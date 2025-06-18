# -- coding: utf-8 --
# SICAD - Sistema de Clasificación Documental Militar (Versión optimizada)
# Combina OCR híbrido, validación de archivos, clasificación manual mejorada, y estructura depurada.

# === LIBRERÍAS ===
# Interfaz gráfica
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog

# Módulos de sistema y archivos
import os
import json
import shutil
import subprocess
import threading
import re
import unicodedata

# Fechas y tiempo
from datetime import datetime, timedelta

# Procesamiento de documentos
import pandas as pd
from pdf2image import convert_from_path
from docx import Document
from PyPDF2 import PdfReader

# Procesamiento de imágenes y OCR
import pytesseract
from PIL import Image, ImageTk, ImageOps, ImageFilter
import easyocr
import numpy as np

# === ARCHIVOS DE CONFIGURACIÓN ===
ARCHIVO_PALABRAS = 'palabras_clave.json'
ARCHIVO_METADATOS = 'metadatos_clave2.json'
USUARIO_ACTUAL_TXT = 'usuario_actual.txt'
REGISTRO_EXCEL = 'registro_guardia_2025.xlsx'

nombre_receptor = ""
nombre_capitan = ""

# === INICIALIZACIÓN DE EASYOCR ===
reader_easyocr = easyocr.Reader(['es'], gpu=False)

# Cargar el nombre del receptor y del capitán desde un archivo de texto
def cargar_usuario_guardado():
    global nombre_receptor, nombre_capitan
    if os.path.exists(USUARIO_ACTUAL_TXT):
        with open(USUARIO_ACTUAL_TXT, "r", encoding="utf-8") as f:
            lineas = f.readlines()
            if len(lineas) >= 2:
                nombre_receptor = lineas[0].strip()
                nombre_capitan = lineas[1].strip()

# Ejecutamos al inicio para tener cargado al usuario
cargar_usuario_guardado()


# Cargar archivos JSON (banco de palabras o metadatos)
def cargar_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Limpiar nombre de archivo para evitar errores de escritura
def limpiar_nombre_archivo(nombre):
    nombre = unicodedata.normalize('NFKD', nombre).encode('ascii', 'ignore').decode('ascii')
    nombre = re.sub(r'[^\w\s.-]', '', nombre)
    nombre = re.sub(r'\s+', '_', nombre)
    return nombre.strip()


# Aplicar OCR con Tesseract, y si no funciona, usar EasyOCR como respaldo
def ocr_con_respaldo(imagen):
    texto = ""
    try:
        texto = pytesseract.image_to_string(imagen, lang='spa').strip()
        if not texto or len(texto) < 10:
            resultado_easyocr = reader_easyocr.readtext(np.array(imagen), detail=0, paragraph=True)
            texto = "\n".join(resultado_easyocr).strip()
    except:
        try:
            resultado_easyocr = reader_easyocr.readtext(np.array(imagen), detail=0, paragraph=True)
            texto = "\n".join(resultado_easyocr).strip()
        except:
            pass
    return texto

# Extraer texto de PDF: primero intenta con PyPDF2, si falla recurre a OCR con imágenes
def extraer_texto_pdf(ruta):
    texto = ""
    try:
        reader = PdfReader(ruta)
        for page in reader.pages:
            texto += page.extract_text() or ""
    except:
        pass

    if not texto.strip():
        try:
            paginas = convert_from_path(ruta, dpi=150, first_page=1, last_page=3)
            for img in paginas:
                texto += ocr_con_respaldo(img) + "\n"
        except:
            with open("documentos_fallidos.txt", "a", encoding="utf-8") as f:
                f.write(f"{ruta}\n")
    return texto.lower()

# Extraer texto de documentos Word (.docx)
def extraer_texto_docx(ruta):
    try:
        doc = Document(ruta)
        return "\n".join([p.text for p in doc.paragraphs]).lower()
    except:
        return ""


# Mostrar vista previa del documento (PDF como imagen, DOCX como texto plano)
def mostrar_vista_previa(ruta_archivo):
    ext = ruta_archivo.lower().split('.')[-1]
    ventana_previa = None
    try:
        if ext == "pdf":
            paginas = convert_from_path(ruta_archivo, dpi=150, first_page=1, last_page=1)
            if paginas:
                img = paginas[0]
                img.thumbnail((600, 800))
                ventana_previa = tk.Toplevel()
                ventana_previa.title(f"Vista previa: {os.path.basename(ruta_archivo)}")
                img_tk = ImageTk.PhotoImage(img)
                etiqueta = tk.Label(ventana_previa, image=img_tk)
                etiqueta.image = img_tk
                etiqueta.pack()
        elif ext == "docx":
            texto = extraer_texto_docx(ruta_archivo)
            resumen = texto[:2000] + "..." if len(texto) > 2000 else texto
            ventana_previa = tk.Toplevel()
            ventana_previa.title(f"Vista previa: {os.path.basename(ruta_archivo)}")
            text_widget = tk.Text(ventana_previa, wrap="word", width=80, height=30)
            text_widget.insert("1.0", resumen)
            text_widget.config(state="disabled")
            text_widget.pack(padx=10, pady=10)
    except:
        return None
    return ventana_previa

# Ventana de clasificación manual donde el usuario elige tipo, área, precedencia, protección y TX/RX
def clasificacion_manual(vista_previa=None):
    ventana = tk.Toplevel()
    ventana.title("Clasificación Manual")
    ventana.geometry("400x400")
    ventana.grab_set()

    resultado = {}

   
    # Campos del formulario
    tk.Label(ventana, text="Tipo de Documento:").pack()
    tipo_var = tk.StringVar()
    ttk.Combobox(ventana, textvariable=tipo_var, values=[
        "OFICIO", "RADIOGRAMA", "MEMORANDUM", "VOLANTE", "ORDEN", "INFORME", "OTRO"
    ]).pack()

    tk.Label(ventana, text="Área de Destino:").pack()
    area_var = tk.StringVar()
    ttk.Combobox(ventana, textvariable=area_var, values=[
        "CIBERESPACIO", "LOGÍSTICA", "VINCULACIÓN", "INTELIGENCIA", "OPERACIONES", "ARMAS", "OTRA"
    ]).pack()

    tk.Label(ventana, text="Precedencia:").pack()
    prec_var = tk.StringVar()
    ttk.Combobox(ventana, textvariable=prec_var, values=[
        "ORDINARIO", "URGENTE", "EXTRA URGENTE", "INSTANTÁNEO"
    ]).pack()

    tk.Label(ventana, text="Protección:").pack()
    prot_var = tk.StringVar()
    ttk.Combobox(ventana, textvariable=prot_var, values=[
        "NP-PUO", "NP-CONF", "NP-SEC", "NP-AS", "NP-REST", "NP-DUP"
    ]).pack()

    tk.Label(ventana, text="¿Guardar en carpeta TX o RX?").pack()
    carpeta_var = tk.StringVar()
    ttk.Combobox(ventana, textvariable=carpeta_var, values=["TX", "RX"]).pack()

# Al confirmar, se validan los campos y se cierra la ventana
    def confirmar():
        if not tipo_var.get() or not area_var.get() or not prec_var.get() or not prot_var.get() or not carpeta_var.get():
            messagebox.showwarning("Campos incompletos", "Por favor, completa todos los campos antes de confirmar.")
            return

        resultado["tipo_documento"] = tipo_var.get()
        resultado["area_destino"] = area_var.get()
        resultado["precedencia"] = prec_var.get()
        resultado["proteccion"] = prot_var.get()
        resultado["carpeta"] = carpeta_var.get()

        if vista_previa:  # ✅ Cierra la vista previa si estaba abierta
            try:
                vista_previa.destroy()
            except:
                pass

        ventana.destroy()

    tk.Button(ventana, text="Confirmar", command=confirmar).pack(pady=20)
    ventana.wait_window()
    return resultado

# Detecta metadatos en el texto utilizando las palabras clave del archivo JSON
def detectar_metadata(texto, metadata):
    resultado = {
        "tipo_documento": "Desconocido",
        "precedencia": "No definida",
        "proteccion": "No clasificada",
        "area_destino": "Sin destino"
    }
    for campo, opciones in metadata.items():
        for clave, palabras in opciones.items():
            if any(palabra in texto for palabra in palabras):
                resultado[campo] = clave
                break
    return resultado

# Detecta si el documento menciona una fecha próxima de entrega o respuesta
def detectar_fecha_alerta(texto):
    frases_clave = ["favor de responder antes del", "fecha límite", "se solicita respuesta antes de", "entregar a más tardar el", "responder antes del"]
    if any(frase in texto for frase in frases_clave):
        fechas = re.findall(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b', texto)
        for f in fechas:
            try:
                fecha_doc = datetime.strptime(f.replace("-", "/"), "%d/%m/%Y")
                if datetime.now() <= fecha_doc <= datetime.now() + timedelta(days=5):
                    messagebox.showwarning("📅 Alerta de Respuesta", f"Este documento menciona una fecha próxima ({fecha_doc.strftime('%d/%m/%Y')}).")
                    return
            except:
                continue

# Genera y asigna un folio único por tipo de documento (ej. OF-001, RAD-002)
def asignar_folio(tipo):
    tipo = tipo.upper().strip()
    prefijos = {"OFICIO": "OF", "RADIOGRAMA": "RAD", "MEMORANDUM": "MEMO", "VOLANTE": "VOL"}
    prefijo = prefijos.get(tipo, tipo[:3].upper())
    archivo = f"control_folios_{tipo}.xlsx"
    columnas = ["Folio", "Fecha"]

# Abrir o crear archivo de control de folios
    if os.path.exists(archivo):
        try:
            df = pd.read_excel(archivo, engine='openpyxl')
            if list(df.columns) != columnas:
                df = pd.DataFrame(columns=columnas)
        except:
            df = pd.DataFrame(columns=columnas)
    else:
        df = pd.DataFrame(columns=columnas)

# Asignar nuevo número de folio
    if not df.empty:
        try:
            ultimo = df["Folio"].iloc[-1].split("-")[-1]
            nuevo = int(ultimo) + 1
        except:
            nuevo = 1
    else:
        nuevo = 1
        
    folio = f"{prefijo}-{nuevo:03d}"
    df.loc[len(df)] = [folio, datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    df.to_excel(archivo, index=False, engine='openpyxl')
    return folio

# Registrar los datos completos del documento en el archivo de registro principal
def registrar_documento(folio, archivo, meta):
    global nombre_receptor, nombre_capitan
    data = {
        "Folio": folio,
        "Archivo": archivo,
        "Fecha": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "Receptor": nombre_receptor,
        "Capitán de Permanencia": nombre_capitan,
        "Tipo": meta.get("tipo_documento", "Desconocido"),
        "Precedencia": meta.get("precedencia", "No definida"),
        "Protección": meta.get("proteccion", "No clasificada"),
        "Área Destino": meta.get("area_destino", "Sin destino")
    }

    if os.path.exists(REGISTRO_EXCEL):
        df = pd.read_excel(REGISTRO_EXCEL, engine='openpyxl')
    else:
        df = pd.DataFrame(columns=list(data.keys()))

    df.loc[len(df)] = data
    df.to_excel(REGISTRO_EXCEL, index=False)
    
# Cambiar el nombre del usuario actual (receptor y capitán de permanencia)
def cambiar_usuario():
    global nombre_receptor, nombre_capitan
    nombre_receptor = simpledialog.askstring("Usuario", "Nombre de quien recibe:") or "NO DEFINIDO"
    nombre_capitan = simpledialog.askstring("Usuario", "Nombre del Capitán de Permanencia:") or "NO DEFINIDO"
    with open(USUARIO_ACTUAL_TXT, "w", encoding="utf-8") as f:
        f.write(f"{nombre_receptor}\n{nombre_capitan}")

# Abrir el archivo en su aplicación por defecto (Word, PDF Reader, etc.)
def abrir_en_aplicacion_nativa(ruta_archivo):
    try:
        os.startfile(ruta_archivo)
    except Exception as e:
        print(f"No se pudo abrir el archivo: {e}")
        
# Proceso principal de clasificación de archivos en una carpeta
def clasificar_archivos():
    origen = filedialog.askdirectory(title="Seleccionar carpeta de origen")
    destino = filedialog.askdirectory(title="Seleccionar carpeta de destino")
    if not origen or not destino:
        return
 # Carga bancos de palabras y metadatos
    palabras = cargar_json(ARCHIVO_PALABRAS)
    metadatos = cargar_json(ARCHIVO_METADATOS)
    
 # Diccionario para traducir meses a español
    meses_es = {
        'January': 'ENERO', 'February': 'FEBRERO', 'March': 'MARZO', 'April': 'ABRIL',
        'May': 'MAYO', 'June': 'JUNIO', 'July': 'JULIO', 'August': 'AGOSTO',
        'September': 'SEPTIEMBRE', 'October': 'OCTUBRE', 'November': 'NOVIEMBRE', 'December': 'DICIEMBRE'
    }

    hoy = datetime.now()
    mes_es = meses_es[hoy.strftime('%B')]
    dia = hoy.strftime('%d')

    archivos = [f for f in os.listdir(origen) if not f.startswith('._') and not f.startswith('.') and os.path.isfile(os.path.join(origen, f))]

# Configuración de barra de progreso
    barra_progreso["value"] = 0
    barra_progreso["maximum"] = len(archivos)
    status_var.set("Iniciando proceso...")
    ventana.update_idletasks()

    for i, archivo in enumerate(archivos):
        archivo_limpio = limpiar_nombre_archivo(archivo)
        ruta_original = os.path.join(origen, archivo)
        ruta_limpia = os.path.join(origen, archivo_limpio)

# Renombrar archivos con nombres válidos
        if archivo != archivo_limpio:
            try:
                os.rename(ruta_original, ruta_limpia)
                ruta = ruta_limpia
                archivo = archivo_limpio
            except:
                continue
        else:
            ruta = ruta_original

  # Extraer texto según tipo
        ext = archivo.lower().split('.')[-1]
        texto = extraer_texto_docx(ruta) if ext == "docx" else extraer_texto_pdf(ruta) if ext == "pdf" else ""

        detectar_fecha_alerta(texto)
        meta = detectar_metadata(texto, metadatos)

# Si no se detecta el tipo, se hace clasificación manual
        if meta.get("tipo_documento", "").upper() == "DESCONOCIDO":
            vista = mostrar_vista_previa(ruta)
            if abrir_nativamente.get():
                abrir_en_aplicacion_nativa(ruta)
            meta = clasificacion_manual(vista)
        else:
            vista = None

        tipo = meta.get("tipo_documento", "OTRO")
        carpeta_txrx = meta.get("carpeta", "TX")
        folio = asignar_folio(tipo)
        registrar_documento(folio, archivo, meta)
        
# Crear ruta destino por fecha, tipo y TX/RX
        ruta_final = os.path.join(destino, mes_es, f"{dia} {mes_es}", tipo.upper(), carpeta_txrx)
        os.makedirs(ruta_final, exist_ok=True)
        shutil.copy2(ruta, os.path.join(ruta_final, f"{folio} - {archivo}"))

 # Actualizar barra y estado
        barra_progreso["value"] += 1
        status_var.set(f"Procesando {archivo} ({i+1}/{len(archivos)})")
        ventana.update_idletasks()

    messagebox.showinfo("Finalizado", "Clasificación completada.")
    status_var.set("Listo")


# Crear ventana principal
ventana = tk.Tk()
ventana.title("SICAD - Sistema de Clasificación Documental")
ventana.geometry("640x500")

abrir_nativamente = tk.BooleanVar(value=False)

# Encabezado y botones principales
tk.Label(ventana, text="📁 GESTOR DOCUMENTAL MILITAR", font=("Arial", 16, "bold")).pack(pady=10)
tk.Button(ventana, text="🔍 Clasificar Documentos", width=50, command=lambda: threading.Thread(target=clasificar_archivos).start()).pack(pady=5)
tk.Button(ventana, text="📌 Banco de Palabras Clave", width=50, command=lambda: subprocess.Popen(["python", "banco_palabras.py"])).pack(pady=5)
tk.Button(ventana, text="🔎 Búsqueda urgente", width=50, command=lambda: subprocess.Popen(["python", "busqueda_documentos.py"])).pack(pady=5)
tk.Button(ventana, text="👤 Cambiar Usuario", width=50, command=cambiar_usuario).pack(pady=10)
tk.Button(ventana, text="❌ Salir", width=50, command=ventana.destroy).pack(pady=20)

# Checkbox para abrir archivos en apps nativas
tk.Checkbutton(
    ventana,
    text="Abrir archivo en aplicación nativa durante clasificación manual",
    variable=abrir_nativamente
).pack(pady=5)


# Estado y barra de progreso
status_var = tk.StringVar(value="Listo para clasificar")
tk.Label(ventana, textvariable=status_var, fg="blue").pack()
barra_progreso = ttk.Progressbar(ventana, orient="horizontal", length=500, mode="determinate")
barra_progreso.pack(pady=10)

# Ejecutar la app
ventana.mainloop()

