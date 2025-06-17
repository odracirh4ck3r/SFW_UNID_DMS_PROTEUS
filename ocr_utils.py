# -*- coding: utf-8 -*-
"""
ocr_utils.py  ·  Funciones de extracción de texto
Autor : Ricardo  ·  2025‑06‑17
"""

import os, subprocess, tempfile, pytesseract, configparser, shutil
from pdf2image import convert_from_path
from docx import Document

# ──────────────────────────────────────────────────────────────
# 1.  Lectura del archivo de configuración
# ──────────────────────────────────────────────────────────────
cfg = configparser.ConfigParser()
cfg.read("config.ini")

pytesseract.pytesseract.tesseract_cmd = cfg["paths"]["pytesseract_cmd"]
OCRMY_PDF_BIN = cfg["paths"].get("ocrmypdf_bin",
                                 shutil.which("ocrmypdf") or "ocrmypdf")

# ──────────────────────────────────────────────────────────────
# 2.  Intentamos importar PyMuPDF (fitz) ─ si falla usamos pdfminer
# ──────────────────────────────────────────────────────────────
try:
    import fitz                                # PyMuPDF
    if not hasattr(fitz, "open"):              # 1.26.x trae el alias pymupdf
        raise ImportError
    HAVE_FITZ = True
except ImportError:
    HAVE_FITZ = False
    from pdfminer.high_level import extract_text as pdfminer_text

# ──────────────────────────────────────────────────────────────
# 3.  Extracción de texto de documentos Word
# ──────────────────────────────────────────────────────────────
def texto_docx(path: str) -> str:
    """Devuelve el texto plano de un archivo .docx"""
    return "\n".join(p.text for p in Document(path).paragraphs)

# ──────────────────────────────────────────────────────────────
# 4.  Extracción de texto de PDFs (3 niveles)
# ──────────────────────────────────────────────────────────────
def texto_pdf(path: str, paginas_max: int = 3) -> str:
    """
    Extrae texto de las primeras `paginas_max` páginas de un PDF.
    Nivel 1 : PyMuPDF      (rápido, para PDFs nativos)
    Nivel 2 : OCRmyPDF     (Tesseract + limpieza, PDFs escaneados)
    Nivel 3 : Tesseract    (fallback sobre imágenes)
    """
    # ── Nivel 1 · PyMuPDF ─────────────────────────────────────
    if HAVE_FITZ:
        try:
            with fitz.open(path) as doc:
                texto = "".join(
                    doc[i].get_text() for i in range(min(paginas_max, doc.page_count))
                )
            if texto.strip():
                return texto
        except Exception as e:
            print(f"[PyMuPDF] {e}")
    else:
        try:
            texto = pdfminer_text(path, maxpages=paginas_max)
            if texto.strip():
                return texto
        except Exception:
            pass

    # ── Nivel 2 · OCRmyPDF ────────────────────────────────────
    tmp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
    cmd = [OCRMY_PDF_BIN, "--tesseract-timeout", "45",
           "--deskew",
           "--pages", f"1-{paginas_max}",
           path, tmp_pdf]

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            print(f"[OCRmyPDF ERROR] Código: {proc.returncode}\n{proc.stderr.decode()}")
            raise RuntimeError("OCRmyPDF falló en procesar el PDF.")

        if HAVE_FITZ:
            with fitz.open(tmp_pdf) as dtmp:
                texto = dtmp[0].get_text()
        else:
            texto = pdfminer_text(tmp_pdf, maxpages=paginas_max)

        if texto.strip():
            os.remove(tmp_pdf)
            return texto
    except subprocess.CalledProcessError as e:
        if e.returncode == 3:
            # El archivo ya contiene texto
            try:
                if HAVE_FITZ:
                    with fitz.open(path) as doc:
                        texto = "".join(
                            doc[i].get_text() for i in range(min(paginas_max, doc.page_count))
                        )
                        if texto.strip():
                            return texto
                else:
                    texto = pdfminer_text(path, maxpages=paginas_max)
                    if texto.strip():
                        return texto
            except Exception:
                pass
        print(f"[OCRmyPDF] {e}")

    # ── Nivel 3 · Tesseract sobre imágenes ────────────────────
    imgs = convert_from_path(path, dpi=200,
                             first_page=1, last_page=paginas_max)

    texto = "\n".join(
        pytesseract.image_to_string(
            im, lang="spa", config="--oem 1 --psm 6"
        ) for im in imgs
    )
    return texto
