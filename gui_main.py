# === Integración completa ===
# Este script conserva TODA tu interfaz anterior, ahora con FTS5, spaCy y búsqueda mejorada
# Incluye: validaciones, análisis automático, renombrado de archivo, y sugerencia de palabras clave

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector, os, shutil, datetime, time, json, sqlite3
from tkinter.simpledialog import askstring
from ocr_utils import texto_pdf, texto_docx
from analyzer import analizar_y_guardar
from db_fts import buscar_por_texto, get_conn

# --- Conexión a MySQL ---
conn = mysql.connector.connect(host="localhost", user="root", password="", database="base_documental")
cursor = conn.cursor()

# --- Funciones auxiliares ---
def obtener_guardias():
    cursor.execute("SELECT nombre FROM receptor")
    return [x[0] for x in cursor.fetchall()]

def obtener_oficiales():
    cursor.execute("SELECT nombre FROM receptorCuartel")
    return [x[0] for x in cursor.fetchall()]

def agregar_guardia(nombre):
    cursor.execute("SELECT COUNT(*) FROM receptor WHERE nombre = %s", (nombre,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO receptor (nombre) VALUES (%s)", (nombre,))
        conn.commit()
        return True
    return False

def eliminar_guardia(nombre):
    cursor.execute("DELETE FROM receptor WHERE nombre = %s", (nombre,))
    conn.commit()

def agregar_oficial(nombre):
    cursor.execute("SELECT COUNT(*) FROM receptorCuartel WHERE nombre = %s", (nombre,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO receptorCuartel (nombre) VALUES (%s)", (nombre,))
        conn.commit()
        return True
    return False

def eliminar_oficial(nombre):
    cursor.execute("DELETE FROM receptorCuartel WHERE nombre = %s", (nombre,))
    conn.commit()

def folio_existe(numero):
    try:
        cursor.execute("SELECT COUNT(*) FROM documento WHERE numero = %s", (int(numero),))
        return cursor.fetchone()[0] > 0
    except:
        return False

# --- GUI ---
root = tk.Tk()
root.title("Gestor Documental Proteus")
frame = ttk.Frame(root, padding=10)
frame.grid()
ttks = {}

# --- Guardia y Oficial ---
var_gc, var_oc = tk.StringVar(), tk.StringVar()
ttks['cb_gc'] = ttk.Combobox(frame, textvariable=var_gc, values=obtener_guardias())
ttks['cb_oc'] = ttk.Combobox(frame, textvariable=var_oc, values=obtener_oficiales())

# --- Folio ---
folio_var = tk.StringVar()
def validar_folio(event=None):
    folio = folio_var.get()
    if folio.isdigit():
        lbl_estado_folio["text"] = "Folio duplicado ❌" if folio_existe(folio) else "Folio disponible ✅"
    else:
        lbl_estado_folio["text"] = "No válido ❌"

# --- Widgets GUI ---
ttks['lbl_gc'] = ttk.Label(frame, text="Guardia:"); ttks['lbl_gc'].grid(row=0, column=0)
ttks['cb_gc'].grid(row=0, column=1)
ttks['lbl_oc'] = ttk.Label(frame, text="Oficial Cuartel:"); ttks['lbl_oc'].grid(row=1, column=0)
ttks['cb_oc'].grid(row=1, column=1)
ttks['lbl_folio'] = ttk.Label(frame, text="Folio:"); ttks['lbl_folio'].grid(row=2, column=0)
ttks['entry_folio'] = ttk.Entry(frame, textvariable=folio_var); ttks['entry_folio'].grid(row=2, column=1)
ttks['entry_folio'].bind("<KeyRelease>", validar_folio)
lbl_estado_folio = ttk.Label(frame, text=""); lbl_estado_folio.grid(row=2, column=2, columnspan=2)

# --- Botón Procesar Carpeta ---
def seleccionar_carpeta():
    if not var_gc.get() or not var_oc.get() or not folio_var.get().isdigit():
        messagebox.showerror("Faltan datos", "Debes seleccionar un guardia, oficial y folio válido.")
        return

    carpeta = filedialog.askdirectory(title="Carpeta de documentos")
    if not carpeta:
        return
    destino = filedialog.askdirectory(title="Carpeta de destino")
    if not destino:
        return

    archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(('.pdf', '.docx'))]
    total = len(archivos)
    if total == 0:
        messagebox.showwarning("Vacío", "No se encontraron archivos PDF o DOCX.")
        return

    progreso_win = tk.Toplevel(root)
    barra = ttk.Progressbar(progreso_win, length=400, mode="determinate", maximum=total)
    barra.pack(padx=20, pady=10)
    estado = ttk.Label(progreso_win, text=""); estado.pack()

    start, procesados = time.time(), 0
    folio_base = int(folio_var.get())

    for i, arch in enumerate(archivos, 1):
        ruta = os.path.join(carpeta, arch)
        ext = arch.split('.')[-1].lower()
        texto = texto_docx(ruta) if ext == 'docx' else texto_pdf(ruta)
        if not texto.strip(): continue

        folio = str(folio_base + i)
        nuevo_nombre = f"{folio}_{arch}"
        destino_path = os.path.abspath(os.path.join(destino, nuevo_nombre))

        cursor.execute("""
            INSERT INTO documento (numero, asunto, idea_principal, ruta_archivo)
            VALUES (%s, %s, %s, %s)
        """, (folio, arch, texto[:500], destino_path))
        conn.commit()
        doc_id = cursor.lastrowid

        analizar_y_guardar(doc_id, arch, texto)

        tokens = set(t.lower() for t in texto.split())
        cursor.execute("SELECT id_keyword, palabra FROM palabras_clave")
        kw_map = {w.lower(): i for i, w in cursor.fetchall()}
        matches = [kw_map[t] for t in tokens & kw_map.keys()]

        for kid in matches:
            cursor.execute("INSERT INTO documento_palabra_clave (id_documento, id_keyword) VALUES (%s, %s)", (doc_id, kid))
        conn.commit()

        shutil.copy2(ruta, destino_path)
        procesados += 1
        tiempo = time.time() - start
        estado["text"] = f"{procesados}/{total} archivos - Estimado restante: {int((total-procesados)*(tiempo/max(procesados,1)))}s"
        barra['value'] = procesados
        progreso_win.update_idletasks()

    progreso_win.destroy()
    messagebox.showinfo("Listo", f"Se procesaron {procesados} archivos correctamente.")

ttk.Button(frame, text="Seleccionar y procesar carpeta", command=seleccionar_carpeta).grid(row=3, column=0, columnspan=3, pady=10)

# --- Búsqueda por palabra clave con sugerencias ---
clave_var = tk.StringVar()
ttk.Label(frame, text="Buscar palabra clave:").grid(row=4, column=0)
clave_entry = ttk.Entry(frame, textvariable=clave_var)
clave_entry.grid(row=4, column=1)

sugerencias = tk.Listbox(frame, height=5)
sugerencias.grid(row=5, column=1, columnspan=2)

# Cargar sugerencias desde base MSYQL Osea la de Xampp o nativa
def cargar_sugerencias():
    cursor.execute("SELECT DISTINCT palabra FROM palabras_clave ORDER BY palabra")
    rows = cursor.fetchall()
    sugerencias.delete(0, tk.END)
    for r in rows:
        sugerencias.insert(tk.END, r[0])


sugerencias.bind("<<ListboxSelect>>", lambda e: clave_var.set(sugerencias.get(sugerencias.curselection())))

# --- Buscar en FTS5 ---
def buscar():
    q = clave_var.get().strip()
    with get_conn() as c:
        filas = c.execute("SELECT id_documento, nombre_archivo, entidades FROM documentos_fts WHERE documentos_fts MATCH ?", (q,)).fetchall()
    tree.delete(*tree.get_children())
    for doc_id, archivo, entidades in filas:
        tree.insert("", "end", values=(doc_id, archivo, entidades))

cargar_sugerencias()
ttk.Button(frame, text="Buscar", command=buscar).grid(row=4, column=2)

# --- Resultados ---
tree = ttk.Treeview(frame, columns=("Folio", "Archivo", "Entidades"), show="headings")
tree.heading("Folio", text="Folio"); tree.heading("Archivo", text="Archivo"); tree.heading("Entidades", text="Entidades")
tree.grid(row=6, column=0, columnspan=4, pady=10)

etiqueta_estado = ttk.Label(frame, text=""); etiqueta_estado.grid(row=7, column=0, columnspan=4)

root.mainloop()
