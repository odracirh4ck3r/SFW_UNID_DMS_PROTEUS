# gui_main.py
# Versión unificada, organizada y funcional con MySQL (metadatos) y SQLite+FTS5 (búsqueda)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.simpledialog import askstring
import mysql.connector
import sqlite3
import os, time, shutil, json
from ocr_utils import texto_pdf, texto_docx
from analyzer import analizar_y_guardar, normalize

# ——— CONEXIÓN A MySQL (metadatos) ———
conn_mysql = mysql.connector.connect(
    host="localhost", user="root", password="", database="base_documental"
)
cursor_mysql = conn_mysql.cursor()

def get_palabras_clave():
    cursor_mysql.execute("SELECT DISTINCT palabra FROM palabras_clave ORDER BY palabra")
    return [x[0] for x in cursor_mysql.fetchall()]

def folio_existe(folio):
    cursor_mysql.execute("SELECT COUNT(*) FROM documento WHERE numero = %s", (folio,))
    return cursor_mysql.fetchone()[0] > 0

# ——— CONEXIÓN A SQLite (FTS5) ———
def get_conn_fts():
    return sqlite3.connect("texto_idx.db")

def buscar_por_texto(q):
    with get_conn_fts() as c:
        return c.execute("""
            SELECT id_documento, nombre_archivo, entidades FROM documentos_fts
            WHERE documentos_fts MATCH ?
        """, (q,)).fetchall()

# ——— INTERFAZ GRÁFICA ———
root = tk.Tk()
root.title("Gestor Documental Proteus")
frame = ttk.Frame(root, padding=10)
frame.grid()

# --- Datos de referencia ---
def obtener_guardias():
    cursor_mysql.execute("SELECT nombre FROM receptor")
    return [x[0] for x in cursor_mysql.fetchall()]

def obtener_oficiales():
    cursor_mysql.execute("SELECT nombre FROM receptorCuartel")
    return [x[0] for x in cursor_mysql.fetchall()]

# --- Sección superior (Guardia, Oficial, Folio) ---
ttk.Label(frame, text="Guardia:").grid(row=0, column=0)
var_gc = tk.StringVar()
cb_gc = ttk.Combobox(frame, textvariable=var_gc, values=obtener_guardias())
cb_gc.grid(row=0, column=1)

ttk.Label(frame, text="Oficial Cuartel:").grid(row=1, column=0)
var_oc = tk.StringVar()
cb_oc = ttk.Combobox(frame, textvariable=var_oc, values=obtener_oficiales())
cb_oc.grid(row=1, column=1)

ttk.Label(frame, text="Folio:").grid(row=2, column=0)
folio_var = tk.StringVar()
entry_folio = ttk.Entry(frame, textvariable=folio_var)
entry_folio.grid(row=2, column=1)

lbl_estado_folio = ttk.Label(frame, text="")
lbl_estado_folio.grid(row=2, column=2)

def validar_folio(event=None):
    f = folio_var.get().strip()
    if not f.isdigit():
        lbl_estado_folio.config(text="No válido ❌")
    elif folio_existe(f):
        lbl_estado_folio.config(text="Duplicado ❌")
    else:
        lbl_estado_folio.config(text="Disponible ✅")

entry_folio.bind("<KeyRelease>", validar_folio)


def detectar_tipo(texto):
    TIPOS = {
      "radiograma": "Radiograma",
      "memorandum": "Memorándum",
      "oficio": "Oficio",
      # … agrega más
    }
    t = texto.lower()
    for clave, nombre in TIPOS.items():
        if clave in t:
            return nombre
    return None




# --- Procesar Carpeta ---
def seleccionar_carpeta():
    if not (var_gc.get() and var_oc.get() and folio_var.get().isdigit() and not folio_existe(folio_var.get())):
        messagebox.showwarning("Faltan datos", "Selecciona guardia, oficial y folio válido")
        return
        # Obtener IDs a partir de los nombres seleccionados
    cursor_mysql.execute("SELECT id_receptor FROM receptor WHERE nombre=%s", (var_gc.get(),))
    id_guardia = cursor_mysql.fetchone()[0]
    cursor_mysql.execute("SELECT id_receptor FROM receptorCuartel WHERE nombre=%s", (var_oc.get(),))
    id_oficial = cursor_mysql.fetchone()[0]

    carpeta = filedialog.askdirectory(title="Carpeta de documentos")
    if not carpeta:
        return
    destino = filedialog.askdirectory(title="Destino")
    if not destino:
        return

    archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(('.pdf', '.docx'))]
    total = len(archivos)
    if total == 0:
        messagebox.showinfo("Vacío", "No hay archivos PDF/DOCX")
        return

    progreso = tk.Toplevel(root)
    tk.Label(progreso, text="Procesando...").pack()
    bar = ttk.Progressbar(progreso, length=400, maximum=total)
    bar.pack()
    estado = tk.Label(progreso, text="")
    estado.pack()

    folio = int(folio_var.get())
    for i, arch in enumerate(archivos, 1):
        ruta = os.path.join(carpeta, arch)
        ext = arch.split(".")[-1].lower()
        texto = texto_docx(ruta) if ext == "docx" else texto_pdf(ruta)
        if not texto.strip():
            continue
        
        prefix = f"{folio:05d}"
        nuevo_nombre = f"{prefix}_{arch}"
        ruta_nueva = os.path.join(destino, nuevo_nombre)
        shutil.copy2(ruta, ruta_nueva)

        cursor_mysql.execute("""
            INSERT INTO documento (numero, asunto, idea_principal, ruta_archivo, receptor_id_receptor, receptorCuartel_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (folio, arch, texto[:500], ruta_nueva, id_guardia, id_oficial))
        conn_mysql.commit()
        doc_id = cursor_mysql.lastrowid


        # Aquí colocas la detección automática de tipo_documento
        tipo = detectar_tipo(texto)                    # llamamos a la función de tipo
        if tipo:
            # 1) obtenemos el id en MySQL
            cursor_mysql.execute(
                "SELECT id_tipo FROM tipo_documento WHERE nombre = %s",
                (tipo,),
            )
            row = cursor_mysql.fetchone()
            if row:
                tid = row[0]
                # 2) actualizamos el documento con esa FK
                cursor_mysql.execute(
                    "UPDATE documento SET tipo_id = %s WHERE id_documento = %s",
                    (tid, doc_id),
                )
                conn_mysql.commit()

        
        analizar_y_guardar(doc_id, arch, texto)

        estado.config(text=f"{i}/{total} → {arch}")
        bar["value"] = i
        root.update_idletasks()
        folio += 1

    progreso.destroy()
    messagebox.showinfo("Hecho", f"Se procesaron {total} archivos")

ttk.Button(frame, text="Seleccionar y procesar carpeta", command=seleccionar_carpeta).grid(row=3, column=0, columnspan=3, pady=10)

# --- Búsqueda ---
ttk.Label(frame, text="Buscar palabra clave:").grid(row=4, column=0)
clave_var = tk.StringVar()
txt_clave = ttk.Entry(frame, textvariable=clave_var)
txt_clave.grid(row=4, column=1)

sugerencias = tk.Listbox(frame, height=5)
sugerencias.grid(row=5, column=1)
for palabra in get_palabras_clave():
    sugerencias.insert(tk.END, palabra)


def buscar():
    q = normalize(clave_var.get().strip())  # si usas normalización
    # 1) Llamada a SQLite FTS5
    fts_rows = buscar_por_texto(q)  # [(doc_id, archivo, entidades), ...]
    q = normalize(clave_var.get().strip())
    print("🔍 Búsqueda FTS5 con query:", repr(q))
    fts_rows = buscar_por_texto(q)
    print("   → filas FTS5:", fts_rows)
    
    tree.delete(*tree.get_children())
    for doc_id, nombre_archivo, entidades in fts_rows:
        # 2) Recuperar metadatos de MySQL, con columnas correctas
        cursor_mysql.execute("""
            SELECT
              numero,
              tipo_id,
              id_precedencia,
              id_proc,
              fecha,
              receptor_id_receptor,
              receptorCuartel_id
            FROM documento
            WHERE id_documento = %s
        """, (doc_id,))
        meta = cursor_mysql.fetchone()
        if not meta:
            # No hay registro en MySQL para este doc_id: lo saltamos
            continue
        
        numero, tipo_id, id_pre, id_pro, fecha, guardia_id, oficial_id = meta
        
        # 3) Traducir tipo_id a nombre (si existe)
        tipo = ""
        if tipo_id:
            cursor_mysql.execute(
                "SELECT nombre FROM tipo_documento WHERE id_tipo = %s",
                (tipo_id,)
            )
            r = cursor_mysql.fetchone()
            tipo = r[0] if r else ""
        
        # 4) Insertar fila en el Treeview (ajusta tus columnas según convenga)
        tree.insert("", "end", values=(
            numero,
            nombre_archivo,
            entidades,
            tipo,
            id_pre,
            id_pro,
            fecha,
            guardia_id,
            oficial_id
        ))



def sugerencia_click(event):
    sel = sugerencias.curselection()
    if sel:
        clave_var.set(sugerencias.get(sel[0]))
        buscar()

sugerencias.bind("<Double-1>", sugerencia_click)
ttk.Button(frame, text="Buscar", command=buscar).grid(row=4, column=2)

# Resultados
cols = ("Folio","Archivo","Entidades","Tipo","Precedencia","Procedencia","Fecha","Guardia","Oficial")
tree = ttk.Treeview(frame, columns=cols, show="headings")
for c in cols:
    tree.heading(c, text=c)
tree.grid(row=6, column=0, columnspan=4, pady=10)

root.mainloop()
