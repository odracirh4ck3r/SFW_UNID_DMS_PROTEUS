# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 17:27:09 2025

@author: ricar
"""

# db.py
import mysql.connector
from contextlib import contextmanager
import configparser, os

cfg = configparser.ConfigParser()
cfg.read('config.ini')

@contextmanager
def get_conn():
    conn = mysql.connector.connect(
        host     = cfg['mysql']['host'],
        user     = cfg['mysql']['user'],
        password = cfg['mysql'][''],
        database = cfg['mysql']['base_documental'],
        charset  = 'utf8mb4',
        collation= 'utf8mb4_general_ci'
    )
    try:
        yield conn
    finally:
        conn.close()

def insert_palabra(palabra):
    sql = "INSERT IGNORE INTO palabras_clave (palabra) VALUES (%s)"
    with get_conn() as c:
        cur = c.cursor()
        cur.execute(sql, (palabra.lower(),))
        c.commit()
        return cur.lastrowid or cur.execute("SELECT id_keyword FROM palabras_clave WHERE palabra=%s", (palabra.lower(),))

def insert_documento(meta):
    sql = """INSERT INTO documento
        (numero, asunto, id_precedencia, id_proc, fecha,
         idea_principal, clasificacion, ruta_archivo, id_metodo, id_nivel,
         receptor_id_receptor)
        VALUES (%(numero)s, %(asunto)s, %(id_precedencia)s, %(id_proc)s,
                %(fecha)s, %(idea_principal)s, %(clasificacion)s,
                %(ruta_archivo)s, %(id_metodo)s, %(id_nivel)s,
                %(receptor_id_receptor)s)
    """
    with get_conn() as c:
        cur = c.cursor()
        cur.execute(sql, meta)
        doc_id = cur.lastrowid
        c.commit()
        return doc_id

def vincular_palabras(doc_id, palabras):
    sql = "INSERT IGNORE INTO documento_palabra_clave (id_documento, id_keyword) VALUES (%s, %s)"
    with get_conn() as c:
        cur = c.cursor()
        cur.executemany(sql, [(doc_id, pid) for pid in palabras])
        c.commit()
