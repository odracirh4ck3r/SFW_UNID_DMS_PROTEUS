# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 19:30:10 2025

@author: ricar
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 17:28:05 2025

@author: ricar
"""

# gui_main.pyV0
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import os, datetime, shutil
from db import insert_documento, insert_palabra, vincular_palabras, get_conn
from ocr_utils import texto_docx, texto_pdf





def procesar_carpeta():
    carpeta = filedialog.askdirectory(title="Carpeta de documentos")
    if not carpeta: return
    destino = filedialog.askdirectory(title="Carpeta de destino")
    if not destino: return

    for arch in os.listdir(carpeta):
        ruta = os.path.join(carpeta, arch)
        if not os.path.isfile(ruta): continue
        ext = arch.split('.')[-1].lower()

        texto = texto_docx(ruta) if ext == 'docx' else \
                texto_pdf(ruta)  if ext == 'pdf'  else ""
        if not texto: continue

        # === detectar palabras ===
        tokens = set(t.lower() for t in texto.split())
        with get_conn() as c:
            cur = c.cursor()
            cur.execute("SELECT id_keyword, palabra FROM palabras_clave")
            kw_map = {w.lower(): i for i, w in cur.fetchall()}
        matches = [kw_map[t] for t in tokens & kw_map.keys()]

        # === insertar documento ===
        meta = dict(
            numero = "", asunto = arch,
            id_precedencia = None, id_proc = None,
            fecha = datetime.date.today(),
            idea_principal = texto[:500],    # recorte
            clasificacion = "Pendiente",
            ruta_archivo = os.path.abspath(os.path.join(destino, arch)),
            id_metodo = None, id_nivel = None,
            receptor_id_receptor = None
        )
        doc_id = insert_documento(meta)
        if matches:
            vincular_palabras(doc_id, matches)
        
        src = os.path.abspath(ruta)
        dst = os.path.abspath(meta['ruta_archivo'])
        
        # Si es el mismo archivo, saltar la copia
        if src != dst:
            shutil.copy2(src, dst)
        else:
            # opcional: messagebox.showwarning("Aviso", "Origen y destino son la misma ruta, se omite la copia.")
            pass
        
                
        # === Copiar archivo fisicamente ===
        shutil.copy2(ruta, meta['ruta_archivo'])

    messagebox.showinfo("Terminado", "Procesamiento completado.")

def validar_nombre_guardia(nombre):
    import re
    return re.fullmatch(r"[a-zA-Z.áéíóúÁÉÍÓÚñÑ\s]{3,100}", nombre) is not None

def obtener_guardias():
    with get_conn() as c:
        cur = c.cursor()
        cur.execute("SELECT nombre FROM receptor")
        return [r[0] for r in cur.fetchall()]

def obtener_oficiales():
    with get_conn() as c:
        cur = c.cursor()
        cur.execute("SELECT nombre FROM receptorCuartel")
        return [r[0] for r in cur.fetchall()]

def agregar_nuevo_guardia():
    nuevo = simpledialog.askstring("Nuevo Guardia", "Escriba el nombre del nuevo guardia:")
    if not nuevo or not validar_nombre_guardia(nuevo):
        messagebox.showerror("Error", "Nombre inválido. Solo letras y punto.")
        return
    with get_conn() as c:
        cur = c.cursor()
        cur.execute("INSERT IGNORE INTO receptor (nombre) VALUES (%s)", (nuevo,))
        c.commit()
    cargar_guardias()

def agregar_nuevo_oficial():
    nuevo = simpledialog.askstring("Nuevo Oficial de Cuartel", "Nombre del nuevo oficial:")
    if not nuevo or not validar_nombre_guardia(nuevo):
        messagebox.showerror("Error", "Nombre inválido. Solo letras y punto.")
        return
    with get_conn() as c:
        cur = c.cursor()
        cur.execute("INSERT IGNORE INTO receptorCuartel (nombre) VALUES (%s)", (nuevo,))
        c.commit()
    cargar_oficiales()

def cargar_guardias():
    lista = obtener_guardias()
    combo_guardia['values'] = lista + ["Registrar nuevo guardia..."]

def cargar_oficiales():
    lista = obtener_oficiales()
    combo_oficial['values'] = lista + ["Registrar nuevo oficial..."]

def al_seleccionar_guardia(event):
    if combo_guardia.get() == "Registrar nuevo guardia...":
        agregar_nuevo_guardia()

def al_seleccionar_oficial(event):
    if combo_oficial.get() == "Registrar nuevo oficial...":
        agregar_nuevo_oficial()

# ---- GUI ----
root = tk.Tk(); root.title("Gestor documental MySQL")
tk.Button(root, text="Seleccionar y procesar carpeta", command=procesar_carpeta, width=45).pack(pady=20)

root = tk.Tk()
tk.Label(root, text="Guardia de Correo:").pack()
combo_guardia = ttk.Combobox(root, state="readonly")
combo_guardia.pack()
combo_guardia.bind("<<ComboboxSelected>>", al_seleccionar_guardia)

tk.Label(root, text="Oficial de Cuartel:").pack()
combo_oficial = ttk.Combobox(root, state="readonly")
combo_oficial.pack()
combo_oficial.bind("<<ComboboxSelected>>", al_seleccionar_oficial)

cargar_guardias()
cargar_oficiales()
root.mainloop()











=======================================================================

# gestor_gui.py V1
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import os, datetime, shutil
from db import get_conn, insert_documento, vincular_palabras
from ocr_utils import texto_pdf, texto_docx

root = tk.Tk()
root.title("Gestor Documental Naval")
root.geometry("700x500")

# ---------- VALIDADORES ----------
def validar_nombre_guardia(nombre):
    import re
    return re.fullmatch(r"[a-zA-Z.\u00C0-\u017F\s]{3,100}", nombre) is not None

# ---------- GUARDIAS Y OFICIALES ----------
def obtener_guardias():
    with get_conn() as c:
        cur = c.cursor()
        cur.execute("SELECT nombre FROM receptor ORDER BY nombre")
        return [r[0] for r in cur.fetchall()]

def obtener_oficiales():
    with get_conn() as c:
        cur = c.cursor()
        cur.execute("SELECT nombre FROM receptorCuartel ORDER BY nombre")
        return [r[0] for r in cur.fetchall()]

def agregar_o_eliminar(nombre, tabla, combo, cargar_func):
    if nombre in ("Registrar nuevo guardia...", "Registrar nuevo oficial..."):
        nuevo = simpledialog.askstring("Nuevo", "Escriba el nombre:")
        if not nuevo or not validar_nombre_guardia(nuevo):
            messagebox.showerror("Error", "Nombre inválido. Solo letras y punto.")
            return
        with get_conn() as c:
            cur = c.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {tabla} WHERE nombre=%s", (nuevo,))
            if cur.fetchone()[0] > 0:
                messagebox.showwarning("Duplicado", f"Ya existe '{nuevo}' en {tabla}.")
                return
            cur.execute(f"INSERT INTO {tabla} (nombre) VALUES (%s)", (nuevo,))
            c.commit()
        cargar_func()
    elif nombre:
        if messagebox.askyesno("Eliminar", f"¿Eliminar '{nombre}' de {tabla}?"):
            with get_conn() as c:
                cur = c.cursor()
                cur.execute(f"DELETE FROM {tabla} WHERE nombre=%s", (nombre,))
                c.commit()
            cargar_func()

def cargar_guardias():
    items = obtener_guardias()
    combo_guardia['values'] = items + ["Registrar nuevo guardia..."]

def cargar_oficiales():
    items = obtener_oficiales()
    combo_oficial['values'] = items + ["Registrar nuevo oficial..."]

def al_seleccionar_guardia(event):
    agregar_o_eliminar(combo_guardia.get(), 'receptor', combo_guardia, cargar_guardias)

def al_seleccionar_oficial(event):
    agregar_o_eliminar(combo_oficial.get(), 'receptorCuartel', combo_oficial, cargar_oficiales)

# ---------- NUMERACION ----------
def obtener_ultimo_numero():
    with get_conn() as c:
        cur = c.cursor()
        cur.execute("SELECT MAX(numero) FROM documento")
        r = cur.fetchone()[0]
        return int(r or 0)

def definir_numeracion():
    op = numeracion_var.get()
    if op == 'Desde 0':
        return 0
    elif op == 'Manual':
        v = simpledialog.askinteger("Inicio", "Ingrese número inicial:")
        return v if v is not None else 0
    else:
        return obtener_ultimo_numero() + 1

# ---------- BÚSQUEDA MULTIFILTRO ----------
def buscar_documentos():
    palabra = entrada_palabra.get().strip().lower()
    with get_conn() as c:
        cur = c.cursor()
        sql = "SELECT numero, asunto, fecha FROM documento WHERE 1=1"
        params = []
        if palabra:
            sql += " AND LOWER(idea_principal) LIKE %s"
            params.append(f"%{palabra}%")
        cur.execute(sql, params)
        resultados = cur.fetchall()
    tabla_resultados.delete(*tabla_resultados.get_children())
    for r in resultados:
        tabla_resultados.insert('', 'end', values=r)

# ---------- UI ----------
tk.Label(root, text="Guardia de Correo:").pack()
combo_guardia = ttk.Combobox(root, state="readonly")
combo_guardia.pack()
combo_guardia.bind("<<ComboboxSelected>>", al_seleccionar_guardia)

tk.Label(root, text="Oficial de Cuartel:").pack()
combo_oficial = ttk.Combobox(root, state="readonly")
combo_oficial.pack()
combo_oficial.bind("<<ComboboxSelected>>", al_seleccionar_oficial)

cargar_guardias()
cargar_oficiales()

numeracion_var = tk.StringVar(value='Desde 0')
tk.Label(root, text="Tipo de numeración:").pack()
for modo in ["Desde 0", "Manual", "Continuar desde BD"]:
    ttk.Radiobutton(root, text=modo, variable=numeracion_var, value=modo).pack(anchor='w')

btn_buscar = tk.Button(root, text="Buscar Documentos", command=buscar_documentos)
btn_buscar.pack(pady=10)

entrada_palabra = tk.Entry(root, width=30)
entrada_palabra.pack()
entrada_palabra.insert(0, "Buscar por palabra clave")

tabla_resultados = ttk.Treeview(root, columns=("Num", "Asunto", "Fecha"), show='headings')
for col in ("Num", "Asunto", "Fecha"):
    tabla_resultados.heading(col, text=col)
tabla_resultados.pack(expand=True, fill='both', pady=10)

root.mainloop()






# gestor_gui.py V3
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import os, datetime, shutil
from db import get_conn, insert_documento, vincular_palabras
from ocr_utils import texto_pdf, texto_docx

root = tk.Tk()
root.title("Gestor Documental Naval")
root.geometry("850x600")

# ---------- VALIDADORES ----------
def validar_nombre_guardia(nombre):
    import re
    return re.fullmatch(r"[a-zA-Z.áéíóúÁÉÍÓÚñÑ\s]{3,100}", nombre) is not None

# ---------- GUARDIAS Y OFICIALES ----------
def obtener_guardias():
    with get_conn() as c:
        cur = c.cursor()
        cur.execute("SELECT nombre FROM receptor ORDER BY nombre")
        return [r[0] for r in cur.fetchall()]

def obtener_oficiales():
    with get_conn() as c:
        cur = c.cursor()
        cur.execute("SELECT nombre FROM receptorCuartel ORDER BY nombre")
        return [r[0] for r in cur.fetchall()]

def agregar_receptor(tabla, cargar_func):
    nuevo = simpledialog.askstring("Nuevo Registro", f"Escriba el nombre para {tabla}:")
    if not nuevo or not validar_nombre_guardia(nuevo):
        messagebox.showerror("Error", "Nombre inválido. Solo letras y punto.")
        return
    with get_conn() as c:
        cur = c.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {tabla} WHERE nombre=%s", (nuevo,))
        if cur.fetchone()[0] > 0:
            messagebox.showwarning("Duplicado", f"Ya existe '{nuevo}' en {tabla}.")
            return
        cur.execute(f"INSERT INTO {tabla} (nombre) VALUES (%s)", (nuevo,))
        c.commit()
    cargar_func()

def eliminar_receptor(tabla, valor, cargar_func):
    if not valor:
        return
    if messagebox.askyesno("Eliminar", f"¿Eliminar '{valor}' de {tabla}?"):
        with get_conn() as c:
            cur = c.cursor()
            cur.execute(f"DELETE FROM {tabla} WHERE nombre=%s", (valor,))
            c.commit()
        cargar_func()

def cargar_guardias():
    items = obtener_guardias()
    combo_guardia['values'] = items

def cargar_oficiales():
    items = obtener_oficiales()
    combo_oficial['values'] = items

# ---------- NUMERACION ----------
def obtener_ultimo_numero():
    with get_conn() as c:
        cur = c.cursor()
        cur.execute("SELECT MAX(numero) FROM documento")
        r = cur.fetchone()[0]
        return int(r or 0)

def definir_numeracion():
    op = numeracion_var.get()
    if op == 'Desde 0':
        return 0
    elif op == 'Manual':
        return int(entry_manual_num.get()) if entry_manual_num.get().isdigit() else 0
    else:
        return obtener_ultimo_numero() + 1

# ---------- BÚSQUEDA MULTIFILTRO ----------
def buscar_documentos():
    palabra = entrada_palabra.get().strip().lower()
    with get_conn() as c:
        cur = c.cursor()
        sql = "SELECT numero, asunto, fecha FROM documento WHERE 1=1"
        params = []
        if palabra:
            sql += " AND LOWER(idea_principal) LIKE %s"
            params.append(f"%{palabra}%")
        cur.execute(sql, params)
        resultados = cur.fetchall()
    tabla_resultados.delete(*tabla_resultados.get_children())
    for r in resultados:
        tabla_resultados.insert('', 'end', values=r)

# ---------- UI ----------
tk.Label(root, text="Guardia de Correo:").pack()
combo_guardia = ttk.Combobox(root, state="readonly")
combo_guardia.pack()

frame_guardia = tk.Frame(root)
frame_guardia.pack()
tk.Button(frame_guardia, text="Agregar Guardia", command=lambda: agregar_receptor('receptor', cargar_guardias)).pack(side='left', padx=5)
tk.Button(frame_guardia, text="Eliminar Guardia", command=lambda: eliminar_receptor('receptor', combo_guardia.get(), cargar_guardias)).pack(side='left', padx=5)

cargar_guardias()

tk.Label(root, text="Oficial de Cuartel:").pack()
combo_oficial = ttk.Combobox(root, state="readonly")
combo_oficial.pack()

frame_oficial = tk.Frame(root)
frame_oficial.pack()
tk.Button(frame_oficial, text="Agregar Oficial", command=lambda: agregar_receptor('receptorCuartel', cargar_oficiales)).pack(side='left', padx=5)
tk.Button(frame_oficial, text="Eliminar Oficial", command=lambda: eliminar_receptor('receptorCuartel', combo_oficial.get(), cargar_oficiales)).pack(side='left', padx=5)

cargar_oficiales()

numeracion_var = tk.StringVar(value='Desde 0')
tk.Label(root, text="Tipo de numeración:").pack()
for modo in ["Desde 0", "Manual", "Continuar desde BD"]:
    ttk.Radiobutton(root, text=modo, variable=numeracion_var, value=modo).pack(anchor='w')

entry_manual_num = tk.Entry(root, width=20)
entry_manual_num.pack()
entry_manual_num.insert(0, "0")

btn_buscar = tk.Button(root, text="Buscar Documentos", command=buscar_documentos)
btn_buscar.pack(pady=10)

entrada_palabra = tk.Entry(root, width=30)
entrada_palabra.pack()
entrada_palabra.insert(0, "Buscar por palabra clave")

tabla_resultados = ttk.Treeview(root, columns=("Num", "Asunto", "Fecha"), show='headings')
for col in ("Num", "Asunto", "Fecha"):
    tabla_resultados.heading(col, text=col)
tabla_resultados.pack(expand=True, fill='both', pady=10)

root.mainloop()





# gestor_gui_mejorado.py V4, ya estaban los tipos de numero secuencial de 0, continuar o especifico, pero aquí en éste código ya no está, solo se especifica y valida su diponibilidad..
# falta ponerle un botón que sólo sea "continuar"

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
import os
from tkinter.simpledialog import askstring

# --- Configuración de conexión ---
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="base_documental"
)
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
    cursor.execute("SELECT COUNT(*) FROM documento WHERE numero = %s", (numero,))
    return cursor.fetchone()[0] > 0

# --- GUI ---
root = tk.Tk()
root.title("Gestor Documental Proteus")

frame = ttk.Frame(root, padding=10)
frame.grid()

# --- Guardia de Correo ---
ttks = {}
ttks['lbl_gc'] = ttk.Label(frame, text="Guardia de Correo:")
ttks['lbl_gc'].grid(row=0, column=0)

var_gc = tk.StringVar()
ttks['cb_gc'] = ttk.Combobox(frame, textvariable=var_gc)
ttks['cb_gc']["values"] = obtener_guardias()
ttks['cb_gc'].grid(row=0, column=1)

def nuevo_guardia():
    nombre = askstring("Nuevo Guardia", "Nombre del nuevo guardia:")
    if nombre and nombre.replace(" ", "").isalpha():
        if agregar_guardia(nombre):
            ttks['cb_gc']["values"] = obtener_guardias()
        else:
            messagebox.showwarning("Duplicado", "Ya existe ese nombre.")

def eliminar_guardia_cb():
    if var_gc.get():
        eliminar_guardia(var_gc.get())
        ttks['cb_gc']["values"] = obtener_guardias()
        var_gc.set("")

ttk.Button(frame, text="Agregar Guardia", command=nuevo_guardia).grid(row=0, column=2)
ttk.Button(frame, text="Eliminar Guardia", command=eliminar_guardia_cb).grid(row=0, column=3)

# --- Oficial de Cuartel ---
ttks['lbl_oc'] = ttk.Label(frame, text="Oficial de Cuartel:")
ttks['lbl_oc'].grid(row=1, column=0)

var_oc = tk.StringVar()
ttks['cb_oc'] = ttk.Combobox(frame, textvariable=var_oc)
ttks['cb_oc']["values"] = obtener_oficiales()
ttks['cb_oc'].grid(row=1, column=1)

def nuevo_oficial():
    nombre = askstring("Nuevo Oficial", "Nombre del nuevo oficial:")
    if nombre and nombre.replace(" ", "").isalpha():
        if agregar_oficial(nombre):
            ttks['cb_oc']["values"] = obtener_oficiales()
        else:
            messagebox.showwarning("Duplicado", "Ya existe ese nombre.")

def eliminar_oficial_cb():
    if var_oc.get():
        eliminar_oficial(var_oc.get())
        ttks['cb_oc']["values"] = obtener_oficiales()
        var_oc.set("")

ttk.Button(frame, text="Agregar Oficial", command=nuevo_oficial).grid(row=1, column=2)
ttk.Button(frame, text="Eliminar Oficial", command=eliminar_oficial_cb).grid(row=1, column=3)

# --- Folio ---
ttks['lbl_folio'] = ttk.Label(frame, text="Folio:")
ttks['lbl_folio'].grid(row=2, column=0)

folio_var = tk.StringVar()
ttks['entry_folio'] = ttk.Entry(frame, textvariable=folio_var)
ttks['entry_folio'].grid(row=2, column=1)

lbl_estado_folio = ttk.Label(frame, text="")
lbl_estado_folio.grid(row=2, column=2, columnspan=2)

def validar_folio(event=None):
    try:
        f = int(folio_var.get())
        if folio_existe(f):
            lbl_estado_folio["text"] = "Folio duplicado ❌"
        else:
            lbl_estado_folio["text"] = "Folio disponible ✅"
    except:
        lbl_estado_folio["text"] = "No válido ❌"

ttks['entry_folio'].bind("<KeyRelease>", validar_folio)

# --- Botón Seleccionar Carpeta ---
def seleccionar_carpeta():
    carpeta = filedialog.askdirectory()
    messagebox.showinfo("Carpeta seleccionada", carpeta)
    # Aquí se conectará con el procesamiento real (ocr + mysql)

ttk.Button(frame, text="Seleccionar Carpeta", command=seleccionar_carpeta).grid(row=3, column=0, columnspan=2)

# --- Búsqueda ---
ttk.Label(frame, text="Buscar palabra clave:").grid(row=4, column=0)

clave_var = tk.StringVar()
ttk.Entry(frame, textvariable=clave_var).grid(row=4, column=1)

def buscar():
    cursor.execute("""
        SELECT numero, nombre_archivo FROM documento 
        WHERE LOWER(palabras_clave) LIKE %s
    """, ("%" + clave_var.get().lower() + "%",))
    resultados = cursor.fetchall()
    for row in tree.get_children():
        tree.delete(row)
    for r in resultados:
        tree.insert("", "end", values=r)

ttk.Button(frame, text="Buscar", command=buscar).grid(row=4, column=2)

# --- Resultados ---
tree = ttk.Treeview(frame, columns=("Folio", "Archivo"), show="headings")
tree.heading("Folio", text="Folio")
tree.heading("Archivo", text="Archivo")
tree.grid(row=5, column=0, columnspan=4)

root.mainloop()











# === Integración completa === V6
# Este script conserva TODA tu interfaz anterior, y ahora integra procesamiento real con OCR y MySQL
# Se incluye: barra de progreso, conservación de estado de interfaz, y validaciones

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector, os, shutil, datetime
from tkinter.simpledialog import askstring
from ocr_utils import texto_pdf, texto_docx
from db import insert_documento, insert_palabra, vincular_palabras, get_conn

# --- Conexión ---
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
    cursor.execute("SELECT COUNT(*) FROM documento WHERE numero = %s", (numero,))
    return cursor.fetchone()[0] > 0

# --- GUI ---
root = tk.Tk()
root.title("Gestor Documental Proteus")

frame = ttk.Frame(root, padding=10)
frame.grid()
ttks = {}

# --- Guardia ---
ttks['lbl_gc'] = ttk.Label(frame, text="Guardia de Correo:"); ttks['lbl_gc'].grid(row=0, column=0)
var_gc = tk.StringVar()
ttks['cb_gc'] = ttk.Combobox(frame, textvariable=var_gc, values=obtener_guardias()); ttks['cb_gc'].grid(row=0, column=1)

def nuevo_guardia():
    nombre = askstring("Nuevo Guardia", "Nombre del nuevo guardia:")
    if nombre and nombre.replace(" ", "").isalpha():
        if agregar_guardia(nombre): ttks['cb_gc']["values"] = obtener_guardias()
        else: messagebox.showwarning("Duplicado", "Ya existe ese nombre.")

def eliminar_guardia_cb():
    if var_gc.get(): eliminar_guardia(var_gc.get()); ttks['cb_gc']["values"] = obtener_guardias(); var_gc.set("")

# --- Oficial ---
ttk.Button(frame, text="Agregar Guardia", command=nuevo_guardia).grid(row=0, column=2)
ttk.Button(frame, text="Eliminar Guardia", command=eliminar_guardia_cb).grid(row=0, column=3)

ttks['lbl_oc'] = ttk.Label(frame, text="Oficial de Cuartel:"); ttks['lbl_oc'].grid(row=1, column=0)
var_oc = tk.StringVar()
ttks['cb_oc'] = ttk.Combobox(frame, textvariable=var_oc, values=obtener_oficiales()); ttks['cb_oc'].grid(row=1, column=1)

def nuevo_oficial():
    nombre = askstring("Nuevo Oficial", "Nombre del nuevo oficial:")
    if nombre and nombre.replace(" ", "").isalpha():
        if agregar_oficial(nombre): ttks['cb_oc']["values"] = obtener_oficiales()
        else: messagebox.showwarning("Duplicado", "Ya existe ese nombre.")

def eliminar_oficial_cb():
    if var_oc.get(): eliminar_oficial(var_oc.get()); ttks['cb_oc']["values"] = obtener_oficiales(); var_oc.set("")

ttk.Button(frame, text="Agregar Oficial", command=nuevo_oficial).grid(row=1, column=2)
ttk.Button(frame, text="Eliminar Oficial", command=eliminar_oficial_cb).grid(row=1, column=3)

# --- Folio ---
ttks['lbl_folio'] = ttk.Label(frame, text="Folio:"); ttks['lbl_folio'].grid(row=2, column=0)
folio_var = tk.StringVar()
ttks['entry_folio'] = ttk.Entry(frame, textvariable=folio_var); ttks['entry_folio'].grid(row=2, column=1)
lbl_estado_folio = ttk.Label(frame, text=""); lbl_estado_folio.grid(row=2, column=2, columnspan=2)

def validar_folio(event=None):
    try:
        f = int(folio_var.get())
        lbl_estado_folio["text"] = "Folio duplicado ❌" if folio_existe(f) else "Folio disponible ✅"
    except: lbl_estado_folio["text"] = "No válido ❌"

ttks['entry_folio'].bind("<KeyRelease>", validar_folio)

# --- Progreso ---
progreso = ttk.Progressbar(frame, length=300); progreso.grid(row=3, column=0, columnspan=3, pady=5)

# --- Carpeta ---
def seleccionar_carpeta():
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
    progreso_win.title("Procesando archivos")
    tk.Label(progreso_win, text="Procesando documentos...").pack(pady=5)
    barra = ttk.Progressbar(progreso_win, length=400, mode="determinate", maximum=total)
    barra.pack(padx=20, pady=10)

    root.update_idletasks()

    for i, arch in enumerate(archivos, 1):
        ruta = os.path.join(carpeta, arch)
        ext = arch.split('.')[-1].lower()

        texto = texto_docx(ruta) if ext == 'docx' else texto_pdf(ruta)
        if not texto.strip():
            continue
                archivos_procesados += 1
                tiempo_actual = time.time() - start
                prom = tiempo_actual / archivos_procesados
                faltan = total_archivos - archivos_procesados
                estimado = int(faltan * prom)
                barra['value'] = int((archivos_procesados / total_archivos) * 100)
                etiqueta_estado["text"] = f"Procesado {archivos_procesados}/{total_archivos}. Estimado restante: {estimado} s"
                root.update_idletasks()


        tokens = set(t.lower() for t in texto.split())
        cursor.execute("SELECT id_keyword, palabra FROM palabras_clave")
        kw_map = {w.lower(): i for i, w in cursor.fetchall()}
        matches = [kw_map[t] for t in tokens & kw_map.keys()]

        folio = folio_var.get()
        if not folio.isdigit() or folio_existe(folio):
            continue

        cursor.execute("""
            INSERT INTO documento (numero, nombre_archivo, idea_principal, ruta_archivo)
            VALUES (%s, %s, %s, %s)
        """, (folio, arch, texto[:500], os.path.join(destino, arch)))
        conn.commit()

        doc_id = cursor.lastrowid

        for kid in matches:
            cursor.execute("INSERT INTO documento_palabra (id_documento, id_palabra) VALUES (%s, %s)", (doc_id, kid))
        conn.commit()

        shutil.copy2(ruta, os.path.join(destino, arch))

        barra["value"] = i
        progreso_win.update_idletasks()

    progreso_win.destroy()
    messagebox.showinfo("Listo", f"{total} archivos procesados correctamente.")


ttk.Button(frame, text="Seleccionar y procesar carpeta", command=seleccionar_carpeta).grid(row=6, column=0, columnspan=3, pady=10)

# --- Busqueda ---
ttk.Label(frame, text="Buscar palabra clave:").grid(row=7, column=0)
clave_var = tk.StringVar(); ttk.Entry(frame, textvariable=clave_var).grid(row=7, column=1)

def buscar():
    cursor.execute("""
        SELECT numero, nombre_archivo FROM documento 
        WHERE LOWER(palabras_clave) LIKE %s
    """, ("%" + clave_var.get().lower() + "%",))
    resultados = cursor.fetchall(); [tree.delete(r) for r in tree.get_children()]
    for r in resultados: tree.insert("", "end", values=r)

ttk.Button(frame, text="Buscar", command=buscar).grid(row=7, column=2)

tree = ttk.Treeview(frame, columns=("Folio", "Archivo"), show="headings")
tree.heading("Folio", text="Folio"); tree.heading("Archivo", text="Archivo")
tree.grid(row=8, column=0, columnspan=4, pady=10)
barra = ttk.Progressbar(frame, orient='horizontal', length=300, mode='determinate')
barra.grid(row=6, column=0, columnspan=3, pady=10)

etiqueta_estado = ttk.Label(frame, text="")
etiqueta_estado.grid(row=7, column=0, columnspan=4)

root.mainloop()









#V7
# === Integracion completa ===
# Este script conserva TODA tu interfaz anterior, y ahora integra procesamiento real con OCR y MySQL
# Se incluye: barra de progreso, conservaciÃ³n de estado de interfaz, y validaciones

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector, os, shutil, datetime
from tkinter.simpledialog import askstring
from ocr_utils import texto_pdf, texto_docx
from db import insert_documento, insert_palabra, vincular_palabras, get_conn
import json, sqlite3
#from db_fts import buscar as buscar_fts



# --- ConexiÃ³n ---
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

# --- Guardia ---
ttks['lbl_gc'] = ttk.Label(frame, text="Guardia de Correo:"); ttks['lbl_gc'].grid(row=0, column=0)
var_gc = tk.StringVar()
ttks['cb_gc'] = ttk.Combobox(frame, textvariable=var_gc, values=obtener_guardias()); ttks['cb_gc'].grid(row=0, column=1)

def nuevo_guardia():
    nombre = askstring("Nuevo Guardia", "Nombre del nuevo guardia:")
    if nombre and nombre.replace(" ", "").isalpha():
        if agregar_guardia(nombre): ttks['cb_gc']["values"] = obtener_guardias()
        else: messagebox.showwarning("Duplicado", "Ya existe ese nombre.")

def eliminar_guardia_cb():
    if var_gc.get(): eliminar_guardia(var_gc.get()); ttks['cb_gc']["values"] = obtener_guardias(); var_gc.set("")

# --- Oficial ---
ttk.Button(frame, text="Agregar Guardia", command=nuevo_guardia).grid(row=0, column=2)
ttk.Button(frame, text="Eliminar Guardia", command=eliminar_guardia_cb).grid(row=0, column=3)

ttks['lbl_oc'] = ttk.Label(frame, text="Oficial de Cuartel:"); ttks['lbl_oc'].grid(row=1, column=0)
var_oc = tk.StringVar()
ttks['cb_oc'] = ttk.Combobox(frame, textvariable=var_oc, values=obtener_oficiales()); ttks['cb_oc'].grid(row=1, column=1)

def nuevo_oficial():
    nombre = askstring("Nuevo Oficial", "Nombre del nuevo oficial:")
    if nombre and nombre.replace(" ", "").isalpha():
        if agregar_oficial(nombre): ttks['cb_oc']["values"] = obtener_oficiales()
        else: messagebox.showwarning("Duplicado", "Ya existe ese nombre.")

def eliminar_oficial_cb():
    if var_oc.get(): eliminar_oficial(var_oc.get()); ttks['cb_oc']["values"] = obtener_oficiales(); var_oc.set("")

ttk.Button(frame, text="Agregar Oficial", command=nuevo_oficial).grid(row=1, column=2)
ttk.Button(frame, text="Eliminar Oficial", command=eliminar_oficial_cb).grid(row=1, column=3)

# --- Folio ---
ttks['lbl_folio'] = ttk.Label(frame, text="Folio:"); ttks['lbl_folio'].grid(row=2, column=0)
folio_var = tk.StringVar()
ttks['entry_folio'] = ttk.Entry(frame, textvariable=folio_var); ttks['entry_folio'].grid(row=2, column=1)
lbl_estado_folio = ttk.Label(frame, text=""); lbl_estado_folio.grid(row=2, column=2, columnspan=2)

def validar_folio(event=None):
    folio = folio_var.get()
    if folio.isdigit():
        lbl_estado_folio["text"] = "Folio duplicado" if folio_existe(folio) else "Folio disponible"
    else:
        lbl_estado_folio["text"] = "No vÃ¡lido â"

ttks['entry_folio'].bind("<KeyRelease>", validar_folio)

# --- Progreso ---
progreso = ttk.Progressbar(frame, length=300); progreso.grid(row=3, column=0, columnspan=3, pady=5)

# --- Carpeta ---
def seleccionar_carpeta():
    import time
    from analyzer import analizar_y_guardar
    carpeta = filedialog.askdirectory(title="Carpeta de documentos")
    if not carpeta:
        return

    destino = filedialog.askdirectory(title="Carpeta de destino")
    if not destino:
        return

    archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(('.pdf', '.docx'))]
    total_archivos = len(archivos)
    if total_archivos == 0:
        messagebox.showwarning("VacÃ­o", "No se encontraron archivos PDF o DOCX.")
        return

    progreso_win = tk.Toplevel(root)
    progreso_win.title("Procesando archivos")
    tk.Label(progreso_win, text="Procesando documentos...").pack(pady=5)
    barra = ttk.Progressbar(progreso_win, length=400, mode="determinate", maximum=total_archivos)
    barra.pack(padx=20, pady=10)
    etiqueta_estado = ttk.Label(progreso_win, text="")
    etiqueta_estado.pack()

    root.update_idletasks()

    start = time.time()
    archivos_procesados = 0

    for i, arch in enumerate(archivos, 1):
        ruta = os.path.join(carpeta, arch)
        ext = arch.split('.')[-1].lower()

        texto = texto_docx(ruta) if ext == 'docx' else texto_pdf(ruta)
        if not texto.strip():
            continue

        archivos_procesados += 1
        tiempo_actual = time.time() - start
        prom = tiempo_actual / archivos_procesados
        faltan = total_archivos - archivos_procesados
        estimado = int(faltan * prom)
        barra['value'] = archivos_procesados
        etiqueta_estado["text"] = f"Procesado {archivos_procesados}/{total_archivos}. Estimado restante: {estimado} s"
        root.update_idletasks()

        tokens = set(t.lower() for t in texto.split())
        cursor.execute("SELECT id_keyword, palabra FROM palabras_clave")
        kw_map = {w.lower(): i for i, w in cursor.fetchall()}
        matches = [kw_map[t] for t in tokens & kw_map.keys()]

        cursor.execute("SELECT MAX(CAST(numero AS UNSIGNED)) FROM documento")
        ultimo = cursor.fetchone()[0] or 0
        folio = str(ultimo + 1)
        if not folio.isdigit() or folio_existe(folio):
            continue

        cursor.execute("""
            INSERT INTO documento (numero, asunto, idea_principal, ruta_archivo)
            VALUES (%s, %s, %s, %s)
        """, (folio, arch, texto[:500], os.path.join(destino, arch)))
        conn.commit()

        doc_id = cursor.lastrowid                

        analizar_y_guardar(doc_id, arch, texto)  

        for kid in matches:
            cursor.execute(
                "INSERT INTO documento_palabra (id_documento, id_palabra) VALUES (%s, %s)",
                (doc_id, kid))
        conn.commit()

        shutil.copy2(os.path.abspath(ruta), os.path.abspath(os.path.join(destino, arch)))

        progreso_win.update_idletasks()

    progreso_win.destroy()
    messagebox.showinfo("Listo", f"{archivos_procesados} archivos procesados correctamente.")

ttk.Button(frame, text="Seleccionar y procesar carpeta", command=seleccionar_carpeta).grid(row=4, column=0, columnspan=3, pady=10)

# --- Busqueda ---
ttk.Label(frame, text="Buscar palabra clave:").grid(row=7, column=0)
clave_var = tk.StringVar(); ttk.Entry(frame, textvariable=clave_var).grid(row=7, column=1)

tree = ttk.Treeview(frame, columns=("Folio", "Archivo", "Entidades"), show="headings")
tree.heading("Folio", text="Folio")
tree.heading("Archivo", text="Archivo")
tree.heading("Entidades", text="Entidades")
tree.grid(row=8, column=0, columnspan=4, pady=10)

def buscar():
    import sqlite3
    q = clave_var.get().strip()
    if not q:
        return
    with sqlite3.connect("texto_idx.db") as c:
        rows = c.execute(
            "SELECT id_documento, nombre_archivo, entidades FROM documentos_fts WHERE documentos_fts MATCH ?",
            (q,)
        ).fetchall()
    tree.delete(*tree.get_children())
    for doc_id, nombre, entidades in rows:
        tree.insert("", "end", values=(doc_id, nombre, entidades))


ttk.Button(frame, text="Buscar", command=buscar).grid(row=7, column=2)

tree = ttk.Treeview(frame, columns=("Folio", "Archivo"), show="headings")
tree.heading("Folio", text="Folio"); tree.heading("Archivo", text="Archivo")
tree.grid(row=8, column=0, columnspan=4, pady=10)

etiqueta_estado = ttk.Label(frame, text="")
etiqueta_estado.grid(row=9, column=0, columnspan=4)

root.mainloop()

