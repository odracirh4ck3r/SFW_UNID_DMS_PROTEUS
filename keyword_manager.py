# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 17:27:52 2025

@author: ricar
"""

# keyword_manager.py
import tkinter as tk, tkinter.messagebox as mb
from db import insert_palabra, get_conn

def cargar_banco():
    with get_conn() as c:
        cur = c.cursor()
        cur.execute("SELECT id_keyword, palabra FROM palabras_clave ORDER BY palabra")
        return cur.fetchall()

def agregar_palabra():
    p = entry.get().strip().lower()
    if not p:
        return
    insert_palabra(p)
    refresh()

def refresh():
    lista.delete(0, tk.END)
    for _, palabra in cargar_banco():
        lista.insert(tk.END, palabra)

root = tk.Tk(); root.title("Palabras clave")
entry = tk.Entry(root, width=30); entry.pack(pady=5)
tk.Button(root, text="Agregar", command=agregar_palabra).pack(pady=5)
lista = tk.Listbox(root, width=40, height=15); lista.pack()
refresh(); root.mainloop()
