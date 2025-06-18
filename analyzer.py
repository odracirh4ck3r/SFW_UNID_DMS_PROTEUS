import spacy, json, unicodedata
from db_fts import insertar


# ── Normalización (sin acentos, minúsculas) ─────────────────────────
def normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text) \
                     .encode("ascii","ignore") \
                     .decode("ascii") \
                     .lower()

# ── Carga del modelo spaCy ──────────────────────────────────────────
nlp = spacy.load("es_core_news_md")

def analizar_y_guardar(id_doc: int, nombre_archivo: str, texto: str):
    """
    1) Extrae entidades spaCy
    2) Normaliza texto y entidades (case‑insensitive, sin tildes)
    3) Inserta todo en SQLite FTS5 con db_fts.insertar()
    """
    # 1) extracción de entidades nombradas
    doc = nlp(texto)
    entidades = [e.text for e in doc.ents if e.label_ in {"ORG", "PERSON", "GPE", "DATE"}]

    # 2) normalización
    texto_norm = normalize(texto)
    entidades_norm = [normalize(e) for e in entidades]

    # 3) único llamado a insertar en FTS5
    insertar(id_doc, nombre_archivo, texto_norm, entidades_norm)



