import spacy, json
from db_fts import insertar

nlp = spacy.load("es_core_news_md")

def analizar_y_guardar(id_doc, nombre_archivo, texto):
    doc = nlp(texto)
    entidades = [e.text for e in doc.ents if e.label_ in {"ORG", "PERSON", "GPE", "DATE"}]
    insertar(id_doc, nombre_archivo, texto, entidades)
