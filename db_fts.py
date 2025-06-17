import sqlite3

def get_conn():
    conn = sqlite3.connect("texto_idx.db")
    conn.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS documentos_fts USING fts5(
        id_documento UNINDEXED,
        texto,
        entidades,
        nombre_archivo,
        content=''
    );
    """)
    return conn

def insertar(id_doc, nombre_archivo, texto, entidades):
    with get_conn() as c:
        c.execute("""
            INSERT INTO documentos_fts (id_documento, texto, entidades, nombre_archivo)
            VALUES (?, ?, ?, ?)
        """, (id_doc, texto, ", ".join(entidades), nombre_archivo))
        c.commit()


def buscar_por_texto(query):
    with get_conn() as c:
        return c.execute(
            "SELECT id_documento, nombre_archivo FROM documentos_fts "
            "WHERE documentos_fts MATCH ?",
            (query,)
        ).fetchall()
