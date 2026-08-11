import streamlit as st
import sqlite3
import hashlib
import os
import random
from datetime import datetime
import pandas as pd
import streamlit.components.v1 as components

# =============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y BD
# =============================================================================
FAVICON = "tortuga.png" if os.path.exists("tortuga.png") else "🐢"

st.set_page_config(
    page_title="Gestión de Fumigaciones & Control de Plagas",
    page_icon=FAVICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "fumigaciones.db"

# =============================================================================
# TÉRMINOS Y CONDICIONES DE USO
# =============================================================================
TERMINOS_Y_CONDICIONES = """
**Última actualización:** 30 de julio de 2026

Bienvenido a la plataforma de gestión de fumigaciones de **Los Ángeles Corporativo**. Al acceder, registrarse o utilizar este sitio web y sus servicios, el usuario acepta cumplir los presentes Términos y Condiciones. Si no está de acuerdo con alguno de ellos, deberá abstenerse de utilizar la plataforma.

### 1. Objeto
La plataforma tiene como finalidad facilitar la administración de servicios de control de plagas mediante el registro de clientes, captura de inspecciones, generación de reportes, almacenamiento de evidencias fotográficas, consulta de historial de servicios y demás funciones relacionadas con la operación de fumigaciones.

### 2. Uso de la Plataforma
El usuario se compromete a utilizar la plataforma de manera responsable, ética y conforme a la legislación aplicable.

Queda prohibido:
- Utilizar información falsa o suplantar la identidad de otra persona.
- Intentar acceder sin autorización a cuentas, bases de datos o áreas restringidas.
- Alterar, modificar o eliminar información perteneciente a otros usuarios.
- Introducir virus, software malicioso o cualquier elemento que pueda afectar el funcionamiento del sistema.
- Utilizar la plataforma para fines distintos a la administración de servicios de control de plagas.

### 3. Registro de Usuarios
Algunas funciones requieren la creación de una cuenta. El usuario es responsable de:
- Mantener la confidencialidad de su contraseña.
- Proporcionar información veraz y actualizada.
- Notificar cualquier uso no autorizado de su cuenta.
- Todas las actividades realizadas desde una cuenta serán responsabilidad de su titular.

### 4. Información Registrada
Los datos capturados en la plataforma, incluyendo clientes, direcciones, reportes técnicos, fotografías, evidencias, certificados y documentos, deberán ser verídicos y obtenidos con autorización del cliente cuando así lo exija la legislación aplicable. El usuario garantiza que posee los permisos necesarios para registrar dicha información.

### 5. Propiedad Intelectual
Todo el contenido de la plataforma (diseño, logotipos, base de datos, código fuente, documentación, reportes generados, interfaces y elementos gráficos) es propiedad de **Los Ángeles Corporativo** o cuenta con las autorizaciones correspondientes, encontrándose protegido por la legislación aplicable en materia de propiedad intelectual. Queda prohibida su reproducción, distribución o modificación sin autorización previa y por escrito.

### 6. Disponibilidad del Servicio
Se realizarán esfuerzos razonables para mantener la plataforma disponible de manera continua. No obstante, podrán existir interrupciones ocasionadas por mantenimiento programado, actualizaciones del sistema, fallas técnicas, problemas de conexión a Internet o eventos fuera del control del administrador.

### 7. Protección de Datos
La información proporcionada por los usuarios será utilizada únicamente para la administración de los servicios ofrecidos, la generación de reportes y el cumplimiento de obligaciones legales y administrativas. Los datos serán tratados conforme al Aviso de Privacidad vigente y no serán divulgados a terceros sin autorización, salvo cuando exista obligación legal.

### 8. Responsabilidad
La plataforma constituye una herramienta de apoyo para la administración de servicios de control de plagas. Los Ángeles Corporativo no será responsable por:
- Errores derivados de información incorrecta proporcionada por los usuarios.
- Decisiones tomadas con base en datos incompletos.
- Pérdida de información ocasionada por el uso indebido de las cuentas.
- Daños ocasionados por fallas de Internet o de servicios externos.

### 9. Suspensión o Cancelación de Cuentas
La administración podrá suspender o cancelar, temporal o definitivamente, cualquier cuenta que incumpla estos términos, realice actividades fraudulentas, comprometa la seguridad del sistema o utilice la plataforma con fines ilícitos.

### 10. Modificaciones
Los presentes Términos y Condiciones podrán modificarse en cualquier momento para mejorar el servicio o cumplir nuevas disposiciones legales. Las modificaciones surtirán efecto desde su publicación en la plataforma.

### 11. Legislación Aplicable
Estos Términos y Condiciones se regirán por las leyes vigentes de los Estados Unidos Mexicanos. Cualquier controversia relacionada con la interpretación o cumplimiento de estos términos será sometida a los tribunales competentes del Estado de Tabasco, salvo disposición legal en contrario.

### 12. Contacto
Para cualquier duda relacionada con estos Términos y Condiciones, el usuario podrá comunicarse con **Los Ángeles Corporativo** mediante los medios de contacto publicados dentro de la plataforma.

---
Al utilizar esta plataforma, el usuario declara haber leído, comprendido y aceptado íntegramente los presentes Términos y Condiciones de Uso.
"""

def mostrar_terminos_condiciones():
    with st.expander("📄 Términos y Condiciones de Uso"):
        st.markdown(TERMINOS_Y_CONDICIONES)

        if "terminos_aceptados" not in st.session_state:
            st.session_state.terminos_aceptados = False

        if st.session_state.terminos_aceptados:
            st.success("✅ Has aceptado los Términos y Condiciones de Uso.")
        else:
            if st.button("Sí, acepto", key="btn_aceptar_terminos", type="primary", use_container_width=True):
                st.session_state.terminos_aceptados = True
                st.rerun()

# Alfabeto sin 0/O/1/I/L para evitar confusiones al dictar o leer el código.
_CODIGO_ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

def _generar_codigo_aleatorio(longitud=6):
    return "".join(random.choice(_CODIGO_ALFABETO) for _ in range(longitud))

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            telefono TEXT
        )
    ''')
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN salt TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN codigo_tecnico TEXT")
    except sqlite3.OperationalError:
        pass
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes_registrados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_local TEXT UNIQUE NOT NULL,
            responsable TEXT,
            telefono TEXT,
            direccion TEXT
        )
    ''')
    try:
        c.execute("ALTER TABLE clientes_registrados ADD COLUMN tecnico_asignado TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE clientes_registrados ADD COLUMN tipo_establecimiento TEXT DEFAULT 'Vivienda'")
    except sqlite3.OperationalError:
        pass
    c.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_nombre TEXT NOT NULL,
            tecnico_nombre TEXT NOT NULL,
            tipo_plaga TEXT NOT NULL,
            tratamiento TEXT NOT NULL,
            estatus TEXT DEFAULT 'Completado',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            evidencia_path TEXT
        )
    ''')
    try:
        c.execute("ALTER TABLE reportes ADD COLUMN nivel_infestacion TEXT DEFAULT 'Media'")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE reportes ADD COLUMN cantidad_observada INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    c.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remitente TEXT NOT NULL,
            destinatario TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS rangos_infestacion (
            tipo_establecimiento TEXT NOT NULL,
            nivel TEXT NOT NULL,
            minimo INTEGER NOT NULL,
            maximo INTEGER,
            PRIMARY KEY (tipo_establecimiento, nivel)
        )
    ''')
    # Sembrar rangos por defecto solo si la tabla está vacía (no pisa ajustes ya hechos por el técnico)
    c.execute("SELECT COUNT(*) FROM rangos_infestacion")
    if c.fetchone()[0] == 0:
        rangos_default = [
            # tipo_establecimiento, nivel, minimo, maximo (None = sin tope)
            ("Vivienda",              "Baja", 1, 10), ("Vivienda",              "Media", 11, 50), ("Vivienda",              "Alta", 51, None),
            ("Hotel",                 "Baja", 1, 5),  ("Hotel",                 "Media", 6, 20),  ("Hotel",                 "Alta", 21, None),
            ("Restaurante / Comercio","Baja", 1, 3),  ("Restaurante / Comercio","Media", 4, 15),  ("Restaurante / Comercio","Alta", 16, None),
            ("Industria Alimentaria", "Baja", 1, 2),  ("Industria Alimentaria", "Media", 3, 10),  ("Industria Alimentaria", "Alta", 11, None),
            ("Hospital / Escuela",    "Baja", 1, 5),  ("Hospital / Escuela",    "Media", 6, 20),  ("Hospital / Escuela",    "Alta", 21, None),
            ("Oficina / Bodega",      "Baja", 1, 10), ("Oficina / Bodega",      "Media", 11, 40), ("Oficina / Bodega",      "Alta", 41, None),
        ]
        c.executemany(
            "INSERT INTO rangos_infestacion(tipo_establecimiento, nivel, minimo, maximo) VALUES (?,?,?,?)",
            rangos_default
        )
    conn.commit()
    conn.close()

def generar_salt():
    return os.urandom(16).hex()

def make_hashes(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()

def check_hashes(password, salt, hashed_text):
    if salt:
        return make_hashes(password, salt) == hashed_text
    return hashlib.sha256(str.encode(password)).hexdigest() == hashed_text

init_db()

if not os.path.exists("uploads"):
    os.makedirs("uploads")

# =============================================================================
# 2. FUNCIONES DE BASE DE DATOS
# =============================================================================
def obtener_tecnico_por_codigo(codigo):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT nombre FROM usuarios WHERE codigo_tecnico = ? AND rol = 'Técnico'",
        (codigo.strip().upper(),)
    )
    fila = c.fetchone()
    conn.close()
    return fila[0] if fila else None

def obtener_codigo_tecnico(correo_tecnico):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT codigo_tecnico FROM usuarios WHERE correo = ?", (correo_tecnico.strip().lower(),))
    fila = c.fetchone()
    conn.close()
    return fila[0] if fila else None

def generar_codigo_tecnico(correo_tecnico):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    while True:
        codigo = _generar_codigo_aleatorio()
        c.execute("SELECT 1 FROM usuarios WHERE codigo_tecnico = ?", (codigo,))
        if not c.fetchone():
            break
    c.execute(
        "UPDATE usuarios SET codigo_tecnico = ? WHERE correo = ?",
        (codigo, correo_tecnico.strip().lower())
    )
    filas_afectadas = c.rowcount
    conn.commit()
    conn.close()
    return codigo if filas_afectadas > 0 else None

def agregar_usuario(nombre, correo, password, rol, telefono, codigo_tecnico_ingresado=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        tecnico_asignado = None
        if rol == "Cliente" and codigo_tecnico_ingresado.strip():
            tecnico_asignado = obtener_tecnico_por_codigo(codigo_tecnico_ingresado)
            if not tecnico_asignado:
                return "codigo_invalido"

        salt = generar_salt()
        hashed = make_hashes(password, salt)
        c.execute(
            "INSERT INTO usuarios(nombre, correo, password, rol, telefono, salt) VALUES (?,?,?,?,?,?)",
            (nombre.strip(), correo.strip().lower(), hashed, rol, telefono.strip(), salt)
        )
        conn.commit()

        if tecnico_asignado:
            agregar_cliente_db(nombre.strip(), nombre.strip(), telefono.strip(), "", tecnico_asignado)

        return "ok"
    except sqlite3.IntegrityError:
        return "email_duplicado"
    finally:
        conn.close()

def login_usuario(correo, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE correo = ?", (correo.strip().lower(),))
    data = c.fetchone()
    conn.close()
    if data:
        salt = data[6] if len(data) > 6 else None
        if check_hashes(password, salt, data[3]):
            return data
    return None

TIPOS_ESTABLECIMIENTO = ["Vivienda", "Hotel", "Restaurante / Comercio", "Industria Alimentaria", "Hospital / Escuela", "Oficina / Bodega"]

def agregar_cliente_db(nombre_local, responsable, telefono, direccion, tecnico_asignado=None, tipo_establecimiento="Vivienda"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO clientes_registrados(nombre_local, responsable, telefono, direccion, tecnico_asignado, tipo_establecimiento) VALUES (?,?,?,?,?,?)",
            (nombre_local.strip(), responsable.strip(), telefono.strip(), direccion.strip(), tecnico_asignado, tipo_establecimiento)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def obtener_tipo_establecimiento(nombre_cliente):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT tipo_establecimiento FROM clientes_registrados WHERE nombre_local = ? COLLATE NOCASE",
        (nombre_cliente,)
    )
    fila = c.fetchone()
    conn.close()
    return fila[0] if fila and fila[0] else "Vivienda"

def obtener_lista_clientes():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT nombre_local FROM clientes_registrados")
    locales = [row[0] for row in c.fetchall()]
    c.execute("SELECT nombre FROM usuarios WHERE rol = 'Cliente'")
    usuarios_clientes = [row[0] for row in c.fetchall()]
    conn.close()
    return sorted(list(set(locales + usuarios_clientes)))

def obtener_todos_clientes_detalle():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM clientes_registrados ORDER BY nombre_local ASC")
    datos = c.fetchall()
    conn.close()
    return datos

def obtener_contactos_disponibles(mi_nombre):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT nombre, rol FROM usuarios WHERE nombre != ?", (mi_nombre,))
    contactos = c.fetchall()
    conn.close()
    return contactos

DESCRIPCION_NIVEL = {
    "Baja": ("🟢", "Se observan pocos individuos o evidencia mínima de actividad. No representa una infestación generalizada."),
    "Media": ("🟡", "Presencia frecuente de la plaga en una o varias áreas. Requiere tratamiento correctivo."),
    "Alta": ("🔴", "Presencia numerosa y generalizada de la plaga. Requiere intervención inmediata."),
}

def obtener_rangos_por_tipo(tipo_establecimiento):
    """Devuelve [(nivel, minimo, maximo), ...] ordenados Baja/Media/Alta para ese tipo de establecimiento."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT nivel, minimo, maximo FROM rangos_infestacion WHERE tipo_establecimiento = ?",
        (tipo_establecimiento,)
    )
    filas = {nivel: (minimo, maximo) for nivel, minimo, maximo in c.fetchall()}
    conn.close()
    orden = ["Baja", "Media", "Alta"]
    return [(nivel, filas[nivel][0], filas[nivel][1]) for nivel in orden if nivel in filas]

def actualizar_rango(tipo_establecimiento, nivel, minimo, maximo):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "UPDATE rangos_infestacion SET minimo = ?, maximo = ? WHERE tipo_establecimiento = ? AND nivel = ?",
        (minimo, maximo, tipo_establecimiento, nivel)
    )
    conn.commit()
    conn.close()

def clasificar_nivel_infestacion(cantidad, tipo_establecimiento="Vivienda"):
    """Clasifica la cantidad observada en Baja/Media/Alta según los rangos definidos para ese tipo de establecimiento."""
    rangos = obtener_rangos_por_tipo(tipo_establecimiento)
    if not rangos:
        rangos = obtener_rangos_por_tipo("Vivienda")
    for nivel, minimo, maximo in rangos:
        if cantidad < minimo:
            continue
        if maximo is None or cantidad <= maximo:
            return nivel
    return rangos[-1][0] if rangos else "Baja"

def guardar_reporte(cliente, tecnico, plaga, tratamiento, estatus, evidencia_path, nivel_infestacion="Media", cantidad_observada=0):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO reportes(cliente_nombre, tecnico_nombre, tipo_plaga, tratamiento, estatus, evidencia_path, nivel_infestacion, cantidad_observada)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (cliente, tecnico, plaga, tratamiento, estatus, evidencia_path, nivel_infestacion, cantidad_observada))
    conn.commit()
    conn.close()

def obtener_reportes_cliente(nombre_cliente):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT * FROM reportes WHERE cliente_nombre = ? COLLATE NOCASE ORDER BY fecha DESC",
        (nombre_cliente,)
    )
    datos = c.fetchall()
    conn.close()
    return datos

def obtener_todos_reportes():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM reportes ORDER BY fecha DESC")
    datos = c.fetchall()
    conn.close()
    return datos

def obtener_infestacion_por_mes(anio):
    """Devuelve el conteo de reportes por mes y nivel de infestación (Baja/Media/Alta) para el año indicado."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT strftime('%m', fecha) AS mes, nivel_infestacion, COUNT(*) 
        FROM reportes
        WHERE strftime('%Y', fecha) = ?
        GROUP BY mes, nivel_infestacion
    ''', (str(anio),))
    datos = c.fetchall()
    conn.close()
    return datos

def obtener_anios_disponibles():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT strftime('%Y', fecha) FROM reportes ORDER BY 1 DESC")
    anios = [row[0] for row in c.fetchall() if row[0]]
    conn.close()
    return anios

def enviar_mensaje_db(remitente, destinatario, texto):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO mensajes(remitente, destinatario, mensaje) VALUES (?,?,?)", (remitente, destinatario, texto))
    conn.commit()
    conn.close()

def obtener_conversacion(user1, user2):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT remitente, destinatario, mensaje, fecha 
        FROM mensajes 
        WHERE (remitente = ? AND destinatario = ?) OR (remitente = ? AND destinatario = ?)
        ORDER BY fecha ASC
    ''', (user1, user2, user2, user1))
    msgs = c.fetchall()
    conn.close()
    return msgs

# =============================================================================
# 3. ESTILOS, ANIMACIONES CSS Y BOTONES PROFESIONALES
# =============================================================================
def aplicar_estilos_globales():
    st.markdown("""
        <style>
            @keyframes fadeInSlideUp {
                0% { opacity: 0; transform: translateY(18px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            .main .block-container {
                animation: fadeInSlideUp 0.45s ease-out forwards;
                padding-top: 2rem;
            }
            button[kind="primary"] {
                background-color: #1d4ed8 !important;
                border: 1px solid #2563eb !important;
                color: #ffffff !important;
                transition: background-color 0.3s ease, transform 0.2s ease !important;
            }
            button[kind="primary"]:hover {
                background-color: #2563eb !important;
                border-color: #3b82f6 !important;
                transform: translateY(-1px);
            }
            .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
                color: #3b82f6 !important;
            }
            .stTabs [data-baseweb="tab-highlight"] {
                background-color: #3b82f6 !important;
            }
        </style>
    """, unsafe_allow_html=True)

def aplicar_estilos_sidebar():
    st.markdown("""
        <style>
            @keyframes sidebarFadeIn {
                0% { opacity: 0; }
                100% { opacity: 1; }
            }
            [data-testid="stSidebar"] {
                background-color: #1a1c23;
                animation: sidebarFadeIn 0.40s ease-out;
            }
            [data-testid="stSidebar"] div[role="radiogroup"] label {
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                border-radius: 8px;
                padding: 6px 10px;
            }
            [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
                background-color: rgba(255, 255, 255, 0.08);
                transform: translateX(5px);
            }
            .profile-card {
                background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
                padding: 16px;
                border-radius: 12px;
                border: 1px solid #374151;
                text-align: center;
                margin-top: 10px;
                margin-bottom: 20px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
            }
            .profile-name {
                color: #ffffff;
                font-weight: 700;
                font-size: 1.1rem;
                margin: 5px 0 0 0;
            }
            .profile-role {
                display: inline-block;
                background-color: #10b981;
                color: #ffffff;
                font-size: 0.75rem;
                font-weight: 600;
                padding: 3px 12px;
                border-radius: 15px;
                margin-top: 6px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
            }
            .menu-title {
                color: #9ca3af;
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1.2px;
                margin-bottom: 10px;
                padding-left: 5px;
            }
            @media (max-width: 768px) {
                h1 { font-size: 1.8rem !important; line-height: 1.2 !important; }
                h2 { font-size: 1.4rem !important; line-height: 1.2 !important; }
                h3 { font-size: 1.1rem !important; }
                .main .block-container {
                    padding-top: 3.5rem !important; 
                    padding-left: 1rem !important;
                    padding-right: 1rem !important;
                }
                .profile-card { margin-top: 35px; }
            }
        </style>
    """, unsafe_allow_html=True)

def aplicar_estilos_navegacion():
    st.markdown("""
        <style>
            .st-key-topnav_wrapper {
                display: flex;
                align-items: center;
                gap: 18px;
                padding: 10px 20px;
                margin-bottom: 1.6rem;
                background: linear-gradient(135deg, #1f2937 0%, #161b26 100%);
                border: 1px solid #2d3341;
                border-radius: 14px;
                box-shadow: 0px 4px 14px rgba(0, 0, 0, 0.25);
            }
            .st-key-topnav_wrapper button[kind="secondary"] {
                background-color: transparent !important;
                border: 1px solid transparent !important;
                color: #d1d5db !important;
                font-weight: 500 !important;
                transition: background-color 0.2s ease, color 0.2s ease !important;
            }
            .st-key-topnav_wrapper button[kind="secondary"]:hover {
                background-color: rgba(255, 255, 255, 0.08) !important;
                color: #ffffff !important;
                border-color: transparent !important;
            }
            .st-key-topnav_wrapper button[kind="primary"] {
                border-radius: 8px !important;
            }
            .topnav-user {
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                line-height: 1.25;
                white-space: nowrap;
            }
            .topnav-user-name {
                color: #ffffff;
                font-weight: 700;
                font-size: 0.92rem;
            }
            .topnav-user-role {
                color: #10b981;
                font-size: 0.72rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.6px;
            }
            @media (min-width: 769px) {
                [data-testid="stSidebar"] { display: none !important; }
                [data-testid="stSidebarCollapsedControl"] { display: none !important; }
            }
            @media (max-width: 768px) {
                .st-key-topnav_wrapper { display: none !important; }
            }
        </style>
    """, unsafe_allow_html=True)

def mostrar_navegacion(opciones, session_key, rol_label):
    aplicar_estilos_navegacion()

    if session_key not in st.session_state:
        st.session_state[session_key] = opciones[0]

    if st.session_state[session_key] not in opciones:
        st.session_state[session_key] = opciones[0]

    # Lógica centralizada para obtener el código si el usuario es Técnico
    codigo_html_top = ""
    codigo_html_side = ""
    es_tecnico = st.session_state.user['rol'] == 'Técnico'
    correo_usuario = st.session_state.user['correo']
    codigo_tecnico = None

    if es_tecnico:
        codigo_tecnico = obtener_codigo_tecnico(correo_usuario)
        if codigo_tecnico:
            codigo_html_top = f'<div style="color:#3b82f6; font-size: 0.85rem; font-weight: 700; margin-top: 4px;">Código: {codigo_tecnico}</div>'
            codigo_html_side = f'<div style="color:#3b82f6; font-size: 0.95rem; font-weight: 700; margin-top: 8px;">Código: {codigo_tecnico}</div>'
        else:
            codigo_html_top = f'<div style="color:#f87171; font-size: 0.85rem; font-weight: 700; margin-top: 4px;">Sin código</div>'
            codigo_html_side = f'<div style="color:#f87171; font-size: 0.95rem; font-weight: 700; margin-top: 8px;">Sin código</div>'

    try:
        contenedor_nav_superior = st.container(key="topnav_wrapper")
    except TypeError:
        contenedor_nav_superior = st.container()

    # ==========================================
    # ENTORNO PC (Barra Superior)
    # ==========================================
    with contenedor_nav_superior:
        col_logo, col_menu, col_user = st.columns([0.5, 3.3, 2.2])
        with col_logo:
            if os.path.exists("tortuga.png"):
                st.image("tortuga.png", width=40)
        with col_menu:
            cols_botones = st.columns(len(opciones))
            for idx, op in enumerate(opciones):
                with cols_botones[idx]:
                    es_activo = (op == st.session_state[session_key])
                    if st.button(
                        op, key=f"{session_key}_top_btn_{idx}",
                        use_container_width=True,
                        type="primary" if es_activo else "secondary"
                    ):
                        st.session_state[session_key] = op
                        st.rerun()
        with col_user:
            st.markdown(f"""
                <div class="topnav-user">
                    <span class="topnav-user-name">{st.session_state.user['nombre']}</span>
                    <span class="topnav-user-role">{rol_label}</span>
                    {codigo_html_top}
                </div>
            """, unsafe_allow_html=True)
            
            # Controles en PC
            col_btn_gen, col_btn_out = st.columns(2)
            with col_btn_gen:
                if es_tecnico:
                    texto_btn = "Regenerar" if codigo_tecnico else "Generar Código"
                    if st.button(texto_btn, key=f"{session_key}_gen_top", use_container_width=True, type="secondary"):
                        generar_codigo_tecnico(correo_usuario)
                        st.rerun()
            with col_btn_out:
                if st.button("Salir", key=f"{session_key}_logout_top", use_container_width=True, type="secondary"):
                    st.session_state.user = None
                    st.rerun()

    # ==========================================
    # ENTORNO MÓVIL (Menú Lateral)
    # ==========================================
    with st.sidebar:
        if os.path.exists("tortuga.png"):
            st.image("tortuga.png", width=160)

        st.markdown(f"""
            <div class="profile-card">
                <div class="profile-name">{st.session_state.user['nombre']}</div>
                <div class="profile-role">{rol_label}</div>
                {codigo_html_side}
            </div>
        """, unsafe_allow_html=True)
        
        # Controles en Móvil
        if es_tecnico:
            texto_btn_side = "Regenerar Código" if codigo_tecnico else "Generar Código"
            if st.button(texto_btn_side, key=f"{session_key}_gen_side", use_container_width=True):
                generar_codigo_tecnico(correo_usuario)
                st.rerun()
                
        st.markdown('<div class="menu-title">MENÚ PRINCIPAL</div>', unsafe_allow_html=True)

        st.radio(
            "", opciones, key=session_key,
            label_visibility="collapsed"
        )

        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión", key=f"{session_key}_logout_side", use_container_width=True, type="secondary"):
            st.session_state.user = None
            st.rerun()

    return st.session_state[session_key]

aplicar_estilos_globales()

def mostrar_modulo_chat():
    st.subheader("💬 Mensajería Interna")
    mi_nombre = st.session_state.user['nombre']
    contactos = obtener_contactos_disponibles(mi_nombre)
    
    if not contactos:
        st.info("Aún no hay otros usuarios registrados en la plataforma para chatear.")
        return

    lista_contactos = [f"{nombre} ({rol})" for nombre, rol in contactos]
    contacto_seleccionado = st.selectbox("Selecciona un contacto para conversar:", lista_contactos)
    nombre_destinatario = contacto_seleccionado.split(" (")[0]
    
    st.markdown("---")
    st.markdown(f"**Conversación con:** `{nombre_destinatario}`")
    
    mensajes = obtener_conversacion(mi_nombre, nombre_destinatario)
    
    chat_container = st.container()
    with chat_container:
        if mensajes:
            for msg in mensajes:
                remitente, _, texto, hora = msg
                es_mio = (remitente == mi_nombre)
                with st.chat_message("user" if es_mio else "assistant"):
                    st.write(f"**{remitente}** *({hora[11:16]})*")
                    st.write(texto)
        else:
            st.caption("No hay mensajes previos. ¡Inicia el chat!")

    st.markdown("---")
    nuevo_msg = st.chat_input("Escribe tu mensaje...")
    if nuevo_msg:
        enviar_mensaje_db(mi_nombre, nombre_destinatario, nuevo_msg)
        st.rerun()

# =============================================================================
# 4. CATÁLOGO COMPLETO DE PLAGAS
# =============================================================================
def mostrar_catalogo_plagas_principal():
    st.title("🪳 Enciclopedia Profesional de Plagas")
    st.caption("Base de conocimiento para identificación, biología y control técnico de infestaciones.")
    
    plaga_seleccionada = st.selectbox(
        "🔍 Selecciona una especie para ver su ficha técnica:",
        [
            "Cucaracha americana (Periplaneta americana)", 
            "Cucaracha alemana (Blattella germanica)",
            "Próximamente más plagas..."
        ]
    )
    
    if plaga_seleccionada == "Cucaracha americana (Periplaneta americana)":
        st.markdown("---")
        col_img, col_info = st.columns([1, 1])
        
        with col_img:
            if os.path.exists("cucaracha_americana.jpg"):
                st.image("cucaracha_americana.jpg", caption="Infografía Técnica: Cucaracha Americana", use_container_width=True)
            else:
                st.info("💡 Guarda la imagen 'cucaracha_americana.jpg' en la carpeta raíz.")
                uploaded_img = st.file_uploader("O sube la infografía aquí:", type=["jpg", "png", "jpeg"], key="info_americana")
                if uploaded_img:
                    with open("cucaracha_americana.jpg", "wb") as f:
                        f.write(uploaded_img.getbuffer())
                    st.rerun()

        with col_info:
            st.header("🪳 Cucaracha americana (*Periplaneta americana*)")
            st.markdown("""
            La **cucaracha americana** (*Periplaneta americana*) es una de las especies de cucarachas más grandes y comunes en zonas urbanas.
            """)
            st.info("""
            **Clasificación**  
            • **Nombre científico:** Periplaneta americana  
            • **Orden:** Blattodea  
            • **Familia:** Blattidae
            """)

            m1, m2 = st.columns(2)
            m1.metric("Tamaño Adulto", "3.5 - 5.0 cm")
            m2.metric("Velocidad Máx.", "5.4 km/h")

        st.markdown("---")
        
        tab_bio, tab_hab, tab_dieta, tab_ciclo, tab_salud, tab_curio, tab_prev = st.tabs([
            "📌 Características", "🏠 Hábitat", "🍞 Alimentación",
            "🔄 Ciclo de Vida", "⚠️ Importancia Sanitaria", "💡 Curiosidades", "🛡️ Prevención"
        ])

        with tab_bio:
            st.subheader("Características")
            st.markdown("""
            * **Tamaño:** Entre 3.5 y 5 cm de longitud.
            * **Color:** Marrón rojizo con una banda amarillenta detrás de la cabeza.
            * **Alas:** Machos y hembras poseen alas desarrolladas; pueden planear o realizar vuelos cortos.
            * **Velocidad:** Puede correr hasta 5.4 km/h.
            """)

        with tab_hab:
            st.subheader("Hábitat")
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                st.markdown("**Prefiere lugares:**")
                st.markdown("* Cálidos.\n* Húmedos.\n* Oscuros.")
            with col_h2:
                st.markdown("**Es común encontrarlas en:**")
                st.markdown("* Alcantarillas y drenajes.\n* Sótanos y bodegas.\n* Cuartos de máquinas.\n* Cocinas y baños.")

        with tab_dieta:
            st.subheader("Alimentación")
            st.markdown("Es **omnívora y carroñera**. Su dieta incluye restos de comida, papel, cartón, pegamento, cuero y materia orgánica en descomposición.")

        with tab_ciclo:
            st.subheader("Ciclo de Vida y Reproducción")
            st.markdown("""
            * **Huevo:** Depositados en cápsulas llamadas **ootecas** (14 a 16 huevos por cápsula).
            * **Ninfa:** Mudan su exoesqueleto de 10 a 13 veces.
            * **Adulto:** Longevidad entre 1 y 2 años.
            """)

        with tab_salud:
            st.subheader("Importancia Sanitaria")
            st.error("Transportan patógenos en cuerpo y patas: *Salmonella*, *E. coli*, hongos y parásitos.")
            st.warning("Sus excrementos y mudas pueden desencadenar alergias y episodios asmáticos.")

        with tab_curio:
            st.subheader("Curiosidades")
            st.markdown("""
            * Soporta semanas sin comer si dispone de agua.
            * Puede sobrevivir hasta una semana sin cabeza.
            * Hábitos mayoritariamente nocturnos.
            """)

        with tab_prev:
            st.subheader("Prevención y Control")
            st.markdown("1. Almacenamiento hermético de alimentos.\n2. Eliminación continua de residuos.\n3. Corrección de fugas.\n4. Sellado de grietas.")

    elif plaga_seleccionada == "Cucaracha alemana (Blattella germanica)":
        st.markdown("---")
        col_img, col_info = st.columns([1, 1])
        
        with col_img:
            if os.path.exists("cucaracha_alemana.jpg"):
                st.image("cucaracha_alemana.jpg", caption="Infografía Técnica: Cucaracha Alemana", use_container_width=True)
            else:
                st.info("💡 Guarda la imagen 'cucaracha_alemana.jpg' en la carpeta raíz.")
                uploaded_img = st.file_uploader("O sube la infografía aquí:", type=["jpg", "png", "jpeg"], key="info_alemana")
                if uploaded_img:
                    with open("cucaracha_alemana.jpg", "wb") as f:
                        f.write(uploaded_img.getbuffer())
                    st.rerun()

        with col_info:
            st.header("🪳 Cucaracha alemana (*Blattella germanica*)")
            st.markdown("""
            La cucaracha alemana (*Blattella germanica*) es una de las especies de cucarachas más pequeñas y una de las plagas domésticas más importantes.
            """)
            st.info("""
            **Clasificación**  
            • **Nombre científico:** Blattella germanica  
            • **Orden:** Blattodea  
            • **Familia:** Ectobiidae
            """)

            m1, m2 = st.columns(2)
            m1.metric("Tamaño Adulto", "1.1 - 1.6 cm")
            m2.metric("Velocidad Máx.", "4 - 5 km/h")

        st.markdown("---")
        
        tab_bio, tab_hab, tab_dieta, tab_ciclo, tab_salud, tab_curio, tab_prev, tab_diff = st.tabs([
            "📌 Características", "🏠 Hábitat", "🍞 Alimentación",
            "🔄 Ciclo de Vida", "⚠️ Sanidad", "💡 Curiosidades", "🛡️ Control", "🆚 Alemana vs Americana"
        ])

        with tab_bio:
            st.subheader("Características Físicas")
            st.markdown("""
            * **Tamaño:** Entre 1.1 y 1.6 cm de longitud.
            * **Color:** Marrón claro o amarillo café.
            * **Marcas distintivas:** Presenta **dos líneas negras paralelas** sobre el pronoto.
            """)

        with tab_hab:
            st.subheader("Hábitat y Refugios")
            st.markdown("* Cocinas, restaurantes y despensas.\n* Electrodomésticos y baños.")

        with tab_dieta:
            st.subheader("Alimentación (Omnívora)")
            st.markdown("Restos de comida, azúcares, grasas y cartón.")

        with tab_ciclo:
            st.subheader("Ciclo de Vida")
            st.markdown("Huevo (ooteca de 30-40 huevos), ninfa y adulto.")

        with tab_salud:
            st.subheader("Importancia Sanitaria")
            st.error("Dispersión de *Salmonella*, *E. coli* y alérgenos asmáticos.")

        with tab_curio:
            st.subheader("Curiosidades")
            st.markdown("Se esconde en rendijas de 2 mm y posee gran resistencia a insecticidas.")

        with tab_prev:
            st.subheader("Control")
            st.markdown("Limpieza estricta, sellado de rendijas y contratación profesional.")

        with tab_diff:
            st.subheader("Diferencias")
            st.markdown("La alemana es pequeña (1.1-1.6 cm) y vive dentro de cocinas; la americana mide hasta 5 cm y suele venir de drenajes.")

    elif plaga_seleccionada == "Próximamente más plagas...":
        st.info("Estamos actualizando la enciclopedia técnica con nuevas especies. ¡Vuelve pronto!")

# =============================================================================
# 4B. CLASIFICACIÓN TOXICOLÓGICA (FRANJAS DE COLOR) — NUEVO
# =============================================================================
CLASES_TOXICOLOGICAS = {
    "Verde":    {"orden": 1, "categoria": "Categoría IV",  "descripcion": "Ligeramente tóxico",    "color": "#22c55e", "icono": "🟢"},
    "Azul":     {"orden": 2, "categoria": "Categoría III", "descripcion": "Moderadamente tóxico",  "color": "#3b82f6", "icono": "🔵"},
    "Amarilla": {"orden": 3, "categoria": "Categoría II",  "descripcion": "Altamente tóxico",      "color": "#eab308", "icono": "🟡"},
    "Roja":     {"orden": 4, "categoria": "Categoría I",   "descripcion": "Extremadamente tóxico", "color": "#ef4444", "icono": "🔴"},
}

# 🔧 AQUÍ VAS A ASIGNAR LA FRANJA DE CADA PRODUCTO.
# Usa como clave EXACTAMENTE el texto que aparece en el selectbox de productos.
CLASE_TOXICOLOGICA_PRODUCTOS = {
    "Demand® 2.5 CS (Syngenta)": "Verde",   # <-- ajusta si no es la clase real
    # "Otro producto®": "Amarilla",
    # "Otro producto 2®": "Roja",
}

def mostrar_badge_toxicidad(clase, mostrar_descripcion=True):
    """Insignia visual con el color de la franja toxicológica del producto."""
    datos = CLASES_TOXICOLOGICAS.get(clase)
    if not datos:
        st.caption("⚪ Sin clasificación toxicológica asignada todavía.")
        return
    descripcion_html = (
        f'<div style="font-size:0.8rem; color:#e5e7eb; margin-top:2px;">'
        f'{datos["descripcion"]} · {datos["categoria"]}</div>'
        if mostrar_descripcion else ""
    )
    st.markdown(f"""
        <div style="
            display:inline-flex; align-items:center; gap:10px;
            background: {datos['color']}22;
            border: 1px solid {datos['color']};
            border-radius: 10px;
            padding: 10px 16px;
            margin-bottom: 10px;
        ">
            <span style="font-size:1.4rem;">{datos['icono']}</span>
            <div>
                <div style="color:{datos['color']}; font-weight:800; letter-spacing:0.5px;">
                    FRANJA {clase.upper()}
                </div>
                {descripcion_html}
            </div>
        </div>
    """, unsafe_allow_html=True)

def mostrar_guia_clases_toxicologicas():
    """Tabla de referencia con las 4 franjas de color."""
    with st.expander("📖 Guía de Clasificación Toxicológica (Franjas de Color)"):
        st.caption(
            "Clasificación según la banda de color impresa en la etiqueta del "
            "producto (categorías toxicológicas OMS / NOM-232-SSA1)."
        )
        for clase, datos in CLASES_TOXICOLOGICAS.items():
            st.markdown(f"""
                <div style="
                    display:flex; align-items:center; gap:12px;
                    border-left: 6px solid {datos['color']};
                    background: #111827;
                    border-radius: 8px;
                    padding: 10px 14px;
                    margin-bottom: 8px;
                ">
                    <span style="font-size:1.3rem;">{datos['icono']}</span>
                    <div>
                        <b style="color:{datos['color']};">Franja {clase}</b>
                        — {datos['descripcion']} ({datos['categoria']})
                    </div>
                </div>
            """, unsafe_allow_html=True)

def mostrar_filtro_por_clase_toxicologica():
    """Selector para consultar rápidamente qué productos hay por franja."""
    st.markdown("#### 🔍 Filtrar productos por franja toxicológica")
    clase_filtro = st.selectbox(
        "Selecciona una franja:",
        list(CLASES_TOXICOLOGICAS.keys()),
        key="filtro_clase_toxi"
    )
    productos_en_clase = [
        prod for prod, clase in CLASE_TOXICOLOGICA_PRODUCTOS.items()
        if clase == clase_filtro
    ]
    mostrar_badge_toxicidad(clase_filtro, mostrar_descripcion=True)
    if productos_en_clase:
        for p in productos_en_clase:
            st.markdown(f"- {p}")
    else:
        st.caption("Ningún producto registrado en esta franja todavía.")

# =============================================================================
# 4C. CATÁLOGO DE PRODUCTOS QUÍMICOS
# =============================================================================
def mostrar_catalogo_quimicos_principal():
    st.title("🧪 Catálogo de Productos Químicos")
    st.caption("Fichas técnicas de los productos utilizados en los servicios de control de plagas.")

    mostrar_guia_clases_toxicologicas()
    with st.expander("🔍 Buscar por franja toxicológica"):
        mostrar_filtro_por_clase_toxicologica()

    producto_seleccionado = st.selectbox(
        "🔍 Selecciona un producto para ver su ficha técnica:",
        [
            "Demand® 2.5 CS (Syngenta)",
            "Próximamente más productos..."
        ]
    )

    if producto_seleccionado == "Demand® 2.5 CS (Syngenta)":
        st.markdown("---")
        col_img, col_info = st.columns([1, 1])

        with col_img:
            if os.path.exists("demand_25cs.jpg"):
                st.image("demand_25cs.jpg", caption="Demand® 2.5 CS - Syngenta", use_container_width=True)
            else:
                st.info("💡 Guarda la imagen 'demand_25cs.jpg' en la carpeta raíz.")
                uploaded_img = st.file_uploader("O sube la imagen del producto aquí:", type=["jpg", "png", "jpeg"], key="info_demand25cs")
                if uploaded_img:
                    with open("demand_25cs.jpg", "wb") as f:
                        f.write(uploaded_img.getbuffer())
                    st.rerun()

        with col_info:
            st.header("🧪 Demand® 2.5 CS (*Syngenta*)")
            st.markdown("""
            **Demand® 2.5 CS** es un insecticida profesional para el control de plagas urbanas. Está formulado con **Lambda-cihalotrina al 2.5%** en una suspensión encapsulada (CS) con tecnología **iCAP®**, la cual libera el ingrediente activo de forma gradual para proporcionar un control residual prolongado.
            """)
            st.info("""
            **Información General**  
            • **Nombre comercial:** Demand® 2.5 CS  
            • **Fabricante:** Syngenta  
            • **Ingrediente activo:** Lambda-cihalotrina 2.5% (25 g/L)  
            • **Familia química:** Piretroides tipo II  
            • **Formulación:** Suspensión encapsulada (CS)  
            • **Grupo IRAC:** 3A
            """)

            mostrar_badge_toxicidad(CLASE_TOXICOLOGICA_PRODUCTOS.get(producto_seleccionado))

        st.markdown("---")

        tab_accion, tab_plagas, tab_lugares, tab_ventajas, tab_dosis, tab_epp, tab_precauciones, tab_residual, tab_toxi = st.tabs([
            "⚙️ Modo de Acción", "🐜 Plagas que Controla", "🏢 Lugares de Aplicación",
            "✅ Ventajas", "💧 Dosis", "🦺 EPP", "⚠️ Precauciones", "⏳ Tiempo Residual", "🏷️ Toxicidad"
        ])

        with tab_accion:
            st.subheader("Modo de Acción")
            st.markdown("""
            La lambda-cihalotrina actúa por **contacto e ingestión**, alterando los canales de sodio del sistema nervioso de los insectos. Esto provoca:

            * Hiperactividad inicial.
            * Parálisis.
            * Muerte del insecto.

            Gracias a la microencapsulación, el ingrediente activo permanece protegido y se libera lentamente, aumentando el tiempo de control residual.
            """)

        with tab_plagas:
            st.subheader("Plagas que Controla")
            st.markdown("""
            Está registrado para controlar numerosas plagas urbanas, entre ellas:

            * Cucarachas
            * Hormigas
            * Moscas
            * Mosquitos
            * Pulgas
            * Arañas
            * Alacranes
            * Avispas
            * Escarabajos
            * Grillos
            * Ciempiés
            * Milpiés
            * Pescadito de plata
            * Cochinillas
            * Jejenes
            * Palomillas
            """)

        with tab_lugares:
            st.subheader("Lugares de Aplicación")
            st.markdown("""
            Puede utilizarse en:

            * Viviendas.
            * Restaurantes.
            * Hoteles.
            * Hospitales.
            * Escuelas.
            * Oficinas.
            * Bodegas.
            * Industrias alimentarias.
            * Áreas perimetrales.
            * Interiores y exteriores.
            """)

        with tab_ventajas:
            st.subheader("Ventajas")
            st.markdown("""
            * ✔️ Rápido efecto de derribo.
            * ✔️ Excelente efecto residual.
            * ✔️ Base agua (menor olor que los concentrados emulsionables).
            * ✔️ La microencapsulación reduce la degradación por luz y temperatura.
            * ✔️ Puede aplicarse sobre superficies porosas y no porosas.
            """)

        with tab_dosis:
            st.subheader("Dosis Recomendada")
            st.markdown("La dosis depende de la plaga y del nivel de infestación. Siempre debe seguirse la **etiqueta oficial del producto**. La ficha técnica del fabricante proporciona las concentraciones autorizadas para cada tipo de aplicación.")

        with tab_epp:
            st.subheader("Equipo de Protección Personal")
            st.markdown("""
            Durante la aplicación se recomienda utilizar:

            * Guantes resistentes a químicos.
            * Lentes de seguridad.
            * Mascarilla o respirador adecuado cuando exista riesgo de inhalación.
            * Overol o ropa de manga larga.
            * Botas de trabajo.
            """)

        with tab_precauciones:
            st.subheader("Precauciones")
            st.warning("""
            * Mantener fuera del alcance de niños y mascotas.
            * Evitar contaminar alimentos y utensilios.
            * No aplicar directamente sobre personas o animales.
            * Es altamente tóxico para organismos acuáticos, por lo que no debe desecharse en ríos, lagos o drenajes.
            """)

        with tab_residual:
            st.subheader("Tiempo Residual")
            st.markdown("""
            El efecto residual suele mantenerse **varias semanas**, dependiendo de factores como:

            * Tipo de superficie.
            * Exposición al sol.
            * Lluvia.
            * Frecuencia de limpieza.
            * Nivel de infestación.
            """)

        with tab_toxi:
            st.subheader("Clasificación Toxicológica")
            mostrar_badge_toxicidad(CLASE_TOXICOLOGICA_PRODUCTOS.get(producto_seleccionado))
            st.markdown("""
            La franja de color impresa en la etiqueta del producto indica el nivel de riesgo
            para la salud humana según la vía de exposición (oral, dérmica o inhalación).
            Consulta siempre la etiqueta oficial del fabricante para el dato definitivo.
            """)

    elif producto_seleccionado == "Próximamente más productos...":
        st.info("Estamos actualizando el catálogo con nuevos productos químicos. ¡Vuelve pronto!")

# =============================================================================
# 4D. GRÁFICA DE NIVEL DE INFESTACIÓN MENSUAL (SOLO TÉCNICOS)
# =============================================================================
MESES_ORDEN = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
MESES_NOMBRE = {
    "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr", "05": "May", "06": "Jun",
    "07": "Jul", "08": "Ago", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"
}
NIVELES_ORDEN = ["Baja", "Media", "Alta"]

def mostrar_grafica_infestacion():
    st.subheader("📈 Nivel de Infestación Mensual")
    st.caption("Cantidad de servicios registrados por nivel de infestación (Baja, Media, Alta) a lo largo del año.")

    tipo_ref = st.selectbox("Ver rangos de referencia para:", TIPOS_ESTABLECIMIENTO, key="tipo_ref_grafica")
    with st.expander(f"ℹ️ ¿Cómo se clasifica la infestación en '{tipo_ref}'?"):
        for nivel, minimo, maximo in obtener_rangos_por_tipo(tipo_ref):
            icono, descripcion = DESCRIPCION_NIVEL[nivel]
            rango_texto = f"{minimo} a {maximo}" if maximo else f"Más de {minimo - 1}"
            st.markdown(f"**{icono} {nivel}** ({rango_texto}): {descripcion}")
        st.caption("Cada nivel se asigna automáticamente según el tipo de establecimiento del cliente. Puedes ajustar estos números en '⚙️ Configurar Rangos'.")

    anios_disponibles = obtener_anios_disponibles()
    anio_actual = str(datetime.now().year)
    if anio_actual not in anios_disponibles:
        anios_disponibles = [anio_actual] + anios_disponibles

    anio_sel = st.selectbox("Año a consultar", anios_disponibles, index=0)

    datos = obtener_infestacion_por_mes(anio_sel)

    # Construir matriz mes x nivel, inicializada en 0
    tabla = {mes: {nivel: 0 for nivel in NIVELES_ORDEN} for mes in MESES_ORDEN}
    for mes, nivel, cantidad in datos:
        if mes in tabla and nivel in NIVELES_ORDEN:
            tabla[mes][nivel] = cantidad

    df_infestacion = pd.DataFrame(
        [[MESES_NOMBRE[mes]] + [tabla[mes][nivel] for nivel in NIVELES_ORDEN] for mes in MESES_ORDEN],
        columns=["Mes"] + NIVELES_ORDEN
    ).set_index("Mes")

    total_servicios = int(df_infestacion.values.sum())

    if total_servicios == 0:
        st.info(f"Todavía no hay servicios registrados en {anio_sel} para generar la gráfica.")
        return

    col_a, col_m, col_b = st.columns(3)
    col_a.metric("🟢 Total Baja", int(df_infestacion["Baja"].sum()))
    col_m.metric("🟡 Total Media", int(df_infestacion["Media"].sum()))
    col_b.metric("🔴 Total Alta", int(df_infestacion["Alta"].sum()))

    st.markdown("---")
    st.bar_chart(
        df_infestacion,
        color=["#22c55e", "#eab308", "#ef4444"],
        use_container_width=True
    )

    with st.expander("📋 Ver tabla de datos"):
        st.dataframe(df_infestacion, use_container_width=True)

# =============================================================================
# 4E. CONFIGURAR RANGOS DE INFESTACIÓN POR TIPO DE ESTABLECIMIENTO (SOLO TÉCNICOS)
# =============================================================================
def mostrar_configurar_rangos():
    st.subheader("⚙️ Configurar Rangos de Infestación")
    st.caption("Ajusta a partir de cuántas plagas observadas se considera Baja, Media o Alta, según el tipo de lugar. Estos valores son los que usa el sistema para clasificar automáticamente cada servicio registrado.")

    tipo_edit = st.selectbox("Tipo de Establecimiento", TIPOS_ESTABLECIMIENTO, key="tipo_config_rangos")
    rangos_actuales = obtener_rangos_por_tipo(tipo_edit)

    with st.form(f"form_rangos_{tipo_edit}"):
        nuevos_valores = {}
        for nivel, minimo, maximo in rangos_actuales:
            icono, _ = DESCRIPCION_NIVEL[nivel]
            col1, col2 = st.columns(2)
            with col1:
                nuevo_min = st.number_input(f"{icono} {nivel} — desde", min_value=0, value=int(minimo), step=1, key=f"min_{tipo_edit}_{nivel}")
            with col2:
                if nivel == "Alta":
                    st.text_input(f"{icono} {nivel} — hasta", value="Sin límite", disabled=True, key=f"max_{tipo_edit}_{nivel}")
                    nuevo_max = None
                else:
                    nuevo_max = st.number_input(f"{icono} {nivel} — hasta", min_value=0, value=int(maximo), step=1, key=f"max_{tipo_edit}_{nivel}")
            nuevos_valores[nivel] = (nuevo_min, nuevo_max)

        guardar = st.form_submit_button("💾 Guardar Rangos", type="primary", use_container_width=True)
        if guardar:
            for nivel, (minimo, maximo) in nuevos_valores.items():
                actualizar_rango(tipo_edit, nivel, minimo, maximo)
            st.success(f"✅ Rangos actualizados para '{tipo_edit}'.")
            st.rerun()

# =============================================================================
# 5. AUTENTICACIÓN MEJORADA
# =============================================================================
if "user" not in st.session_state:
    st.session_state.user = None

def mostrar_autenticacion():
    st.markdown("""
        <style>
            .brand-title {
                font-size: 2.8rem;
                font-weight: 800;
                color: #ffffff;
                line-height: 1.2;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            .brand-subtitle {
                font-size: 1.1rem;
                color: #9ca3af;
                margin-bottom: 30px;
            }
            .spacer {
                margin-top: 60px;
            }
            .auth-card-wrapper [data-testid="stForm"] {
                background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
                border: 1px solid #374151;
                border-radius: 14px;
                padding: 28px 26px;
                box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.35);
            }
            .auth-card-wrapper .stTextInput input {
                background-color: #111827 !important;
                border: 1px solid #374151 !important;
            }
            .auth-welcome {
                font-size: 1.4rem;
                font-weight: 700;
                color: #ffffff;
                margin-bottom: 2px;
            }
            .auth-caption {
                color: #9ca3af;
                margin-bottom: 18px;
            }
            @media (max-width: 768px) {
                .spacer { margin-top: 10px; }
                .brand-title { font-size: 2rem; }
            }
        </style>
    """, unsafe_allow_html=True)

    col_brand, col_space, col_auth = st.columns([1.2, 0.2, 1])

    with col_brand:
        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
        if os.path.exists("tortuga.png"):
            st.image("tortuga.png", width=220)
        
        st.markdown('<div class="brand-title">Gestión Profesional<br>de Fumigaciones</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-subtitle">Plataforma integral para el control de plagas, gestión de clientes y seguimiento en tiempo real.</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background-color: #1f2937; padding: 20px; border-radius: 10px; border-left: 5px solid #10b981; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="color: #10b981; margin-top: 0; font-family: sans-serif;">Características del Sistema:</h4>
            <p style="margin-bottom: 8px; color: #f3f4f6; font-family: sans-serif;">🛡️ <b>Seguridad:</b> Datos encriptados y respaldados.</p>
            <p style="margin-bottom: 8px; color: #f3f4f6; font-family: sans-serif;">📍 <b>Geolocalización:</b> Control de servicios en tiempo real.</p>
            <p style="margin-bottom: 0; color: #f3f4f6; font-family: sans-serif;">📊 <b>Trazabilidad:</b> Historial y reportes fotográficos.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_auth:
        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-card-wrapper">', unsafe_allow_html=True)
        
        with st.container():
            tab_login, tab_registro = st.tabs(["🔐 Iniciar Sesión", "📝 Crear Cuenta Nueva"])
            
            with tab_login:
                st.markdown('<div class="auth-welcome">¡Bienvenido de nuevo!</div>', unsafe_allow_html=True)
                st.markdown('<div class="auth-caption">Ingresa tus credenciales para acceder al panel de control.</div>', unsafe_allow_html=True)
                
                with st.form("form_login", clear_on_submit=False):
                    correo = st.text_input("Correo electrónico", placeholder="ejemplo@empresa.com")
                    password = st.text_input("Contraseña", type="password", placeholder="••••••••")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    submit = st.form_submit_button("Ingresar al Sistema", type="primary", use_container_width=True)
                    
                    if submit:
                        if correo and password:
                            user_data = login_usuario(correo, password)
                            if user_data:
                                st.session_state.user = {
                                    "id": user_data[0],
                                    "nombre": user_data[1],
                                    "correo": user_data[2],
                                    "rol": user_data[4],
                                    "telefono": user_data[5]
                                }
                                st.rerun()
                            else:
                                st.error("⚠️ Correo o contraseña incorrectos. Intenta nuevamente.")
                        else:
                            st.warning("Por favor, completa ambos campos.")

            with tab_registro:
                st.markdown('<div class="auth-welcome">Solicitud de Acceso</div>', unsafe_allow_html=True)
                st.markdown('<div class="auth-caption">Registra tus datos para habilitar tu cuenta en la plataforma.</div>', unsafe_allow_html=True)
                
                with st.form("form_registro", clear_on_submit=True):
                    nuevo_nombre = st.text_input("Nombre Completo / Razón Social", placeholder="Ej. Juan Pérez / Empresa S.A.")
                    nuevo_correo = st.text_input("Correo Electrónico", placeholder="contacto@empresa.com")
                    
                    col_t, col_r = st.columns(2)
                    with col_t:
                        nuevo_telefono = st.text_input("Teléfono Móvil", placeholder="10 dígitos")
                    with col_r:
                        nuevo_rol = st.selectbox("Tipo de Usuario", ["Cliente", "Técnico"])

                    nuevo_codigo_tecnico = st.text_input(
                        "Código del técnico (opcional)",
                        placeholder="Ej. AB12CD",
                        help="Solo aplica si te registras como Cliente. Pídeselo a tu técnico."
                    )
                    
                    pass1 = st.text_input("Contraseña", type="password", placeholder="Crea una contraseña segura (mín. 6 caracteres)")
                    pass2 = st.text_input("Confirmar Contraseña", type="password", placeholder="Repite tu contraseña")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    reg_submit = st.form_submit_button("Registrar Cuenta", type="primary", use_container_width=True)
                    
                    if reg_submit:
                        nombre_limpio = nuevo_nombre.strip()
                        correo_limpio = nuevo_correo.strip()
                        telefono_limpio = nuevo_telefono.strip()
                        codigo_limpio = nuevo_codigo_tecnico.strip()

                        if not nombre_limpio or not correo_limpio or not pass1:
                            st.warning("⚠️ Por favor, llena todos los campos obligatorios.")
                        elif "@" not in correo_limpio or "." not in correo_limpio.split("@")[-1]:
                            st.error("⚠️ Ingresa un correo electrónico válido.")
                        elif telefono_limpio and (not telefono_limpio.isdigit() or len(telefono_limpio) != 10):
                            st.error("⚠️ El teléfono debe contener exactamente 10 dígitos numéricos.")
                        elif len(pass1) < 6:
                            st.error("⚠️ La contraseña debe tener al menos 6 caracteres.")
                        elif pass1 != pass2:
                            st.error("⚠️ Las contraseñas no coinciden.")
                        else:
                            resultado = agregar_usuario(nombre_limpio, correo_limpio, pass1, nuevo_rol, telefono_limpio, codigo_limpio)
                            if resultado == "ok":
                                st.success("✅ Cuenta creada exitosamente. Ahora puedes iniciar sesión.")
                            elif resultado == "codigo_invalido":
                                st.error("⚠️ El código de técnico no es válido. Verifícalo o deja el campo vacío.")
                            else:
                                st.error("❌ El correo ingresado ya se encuentra registrado.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    mostrar_terminos_condiciones()

# =============================================================================
# 6. VISTAS PRINCIPALES (TÉCNICO Y CLIENTE)
# =============================================================================
def mostrar_ubicacion_real():
    st.subheader("📍 Geolocalización y Control de Servicios")
    st.info("Tu navegador pedirá permiso para compartir tu ubicación. Acepta el permiso para verla en el mapa.")

    html_geo = """
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <div id="status" style="font-family: sans-serif; color: #9ca3af; margin-bottom: 8px;">
        Solicitando ubicación...
    </div>
    <div id="map" style="height: 560px; border-radius: 12px; overflow: hidden;"></div>
    <script>
        const statusEl = document.getElementById('status');

        function initMap(lat, lon, accuracy) {
            statusEl.innerHTML = "Ubicación obtenida (precisión aprox. " + Math.round(accuracy) + " m)";
            statusEl.style.color = "#10b981";
            const map = L.map('map').setView([lat, lon], 16);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap'
            }).addTo(map);
            L.marker([lat, lon]).addTo(map).bindPopup('Tu ubicación actual').openPopup();
            if (accuracy) {
                L.circle([lat, lon], {
                    radius: accuracy,
                    color: '#3b82f6',
                    fillColor: '#3b82f6',
                    fillOpacity: 0.15
                }).addTo(map);
            }
        }

        function showError(mensaje) {
            statusEl.innerHTML = mensaje;
            statusEl.style.color = "#f87171";
            document.getElementById('map').innerHTML =
                '<div style="height:100%;display:flex;align-items:center;justify-content:center;' +
                'background:#1f2937;color:#9ca3af;font-family:sans-serif;text-align:center;padding:20px;">' +
                'No se pudo mostrar el mapa sin acceso a tu ubicación.</div>';
        }

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => initMap(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy),
                (err) => {
                    let msg = "No se pudo obtener tu ubicación (" + err.message + "). ";
                    msg += "Revisa que hayas concedido permiso de ubicación a este sitio en tu navegador.";
                    showError(msg);
                },
                { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
            );
        } else {
            showError("Este navegador no soporta geolocalización.");
        }
    </script>
    """
    components.html(html_geo, height=620, scrolling=False)

def vista_tecnico():
    aplicar_estilos_sidebar()

    opcion = mostrar_navegacion(
        [
            "🏠 Inicio / Catálogo",
            "🧪 Productos Químicos",
            "➕ Registrar Servicio",
            "👥 Gestión Clientes",
            "📊 Historial & Reportes",
            "⚙️ Configurar Rangos",
            "📍 Ubicación Real",
            "💬 Mensajería"
        ],
        session_key="nav_tecnico",
        rol_label="Técnico Especialista"
    )
    
    if opcion == "🏠 Inicio / Catálogo":
        mostrar_catalogo_plagas_principal()

    elif opcion == "🧪 Productos Químicos":
        mostrar_catalogo_quimicos_principal()

    elif opcion == "⚙️ Configurar Rangos":
        mostrar_configurar_rangos()

    elif opcion == "➕ Registrar Servicio":
        st.subheader("📝 Registrar Servicio de Fumigación")
        lista_clientes = obtener_lista_clientes()

        cliente = st.selectbox("Cliente / Local", options=lista_clientes if lista_clientes else ["Sin clientes"], key="cliente_sel_servicio")
        tipo_cliente = obtener_tipo_establecimiento(cliente) if lista_clientes else "Vivienda"

        with st.expander(f"ℹ️ Rangos de infestación para '{cliente}' (Tipo: {tipo_cliente})", expanded=True):
            for nivel, minimo, maximo in obtener_rangos_por_tipo(tipo_cliente):
                icono, descripcion = DESCRIPCION_NIVEL[nivel]
                rango_texto = f"{minimo} a {maximo}" if maximo else f"Más de {minimo - 1}"
                st.markdown(f"**{icono} {nivel}** ({rango_texto}): {descripcion}")
            st.caption("Cambia el tipo de establecimiento de este cliente desde '👥 Gestión Clientes' → editar, o ajusta los rangos en '⚙️ Configurar Rangos'.")
        
        with st.form("registro_fumigacion", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                plaga = st.text_input("Tipo de Plaga", placeholder="Ej. Cucaracha alemana, Roedores")
                tratamiento = st.text_area("Tratamiento Aplicado / Productos", placeholder="Ej. Aplicación de gel específico y aspersión perimetral.")
                cantidad_observada = st.number_input(
                    "Cantidad de Plagas Observadas",
                    min_value=0, step=1, value=0,
                    help=f"Se clasificará según los rangos de '{tipo_cliente}' mostrados arriba."
                )
            with col2:
                estatus = st.selectbox("Estatus del Servicio", ["Completado", "En Proceso", "Seguimiento Requerido"])
                tecnico = st.text_input("Técnico Responsable", value=st.session_state.user['nombre'])
                evidencia = st.file_uploader("Subir Evidencia Fotográfica", type=["jpg", "png", "jpeg"])
            
            submit_serv = st.form_submit_button("Guardar Reporte de Servicio", type="primary", use_container_width=True)
            
            if submit_serv:
                path_img = ""
                if evidencia:
                    nombre_unico = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{evidencia.name}"
                    path_img = os.path.join("uploads", nombre_unico)
                    with open(path_img, "wb") as f:
                        f.write(evidencia.getbuffer())
                
                nivel_calculado = clasificar_nivel_infestacion(int(cantidad_observada), tipo_cliente)
                guardar_reporte(cliente, tecnico, plaga, tratamiento, estatus, path_img, nivel_calculado, int(cantidad_observada))
                st.success(f"✅ Servicio registrado correctamente. Nivel de infestación asignado: **{nivel_calculado}** ({int(cantidad_observada)} plagas observadas).")

        st.markdown("---")
        mostrar_grafica_infestacion()

    elif opcion == "👥 Gestión Clientes":
        st.subheader("👥 Gestión de Clientes y Locales")

        correo_tecnico_actual = st.session_state.user['correo']
        codigo_tecnico_actual = obtener_codigo_tecnico(correo_tecnico_actual)
        
        with st.container():
            st.markdown("#### 🔑 Tu código para nuevos clientes")
            st.caption(
                "Compártelo con tus clientes nuevos: al crear su cuenta como Cliente "
                "pueden anexarlo y quedan agregados aquí automáticamente."
            )

            texto_boton_codigo = "🔄 Regenerar código" if codigo_tecnico_actual else "✨ Generar mi código"
            
            if st.button(texto_boton_codigo, key="btn_generar_codigo_tecnico"):
                nuevo_codigo = generar_codigo_tecnico(correo_tecnico_actual)
                if nuevo_codigo:
                    codigo_tecnico_actual = nuevo_codigo
                    st.success(f"✅ ¡Código generado con éxito: {nuevo_codigo}!")
                else:
                    st.error(
                        "⚠️ No se pudo generar el código: no se encontró tu cuenta "
                        "por correo. Intenta cerrar sesión y volver a entrar."
                    )

            if codigo_tecnico_actual:
                st.code(codigo_tecnico_actual, language=None)
            else:
                st.info("Todavía no tienes un código generado.")

        st.markdown("---")
        
        with st.expander("➕ Registrar Nuevo Local o Cliente"):
            with st.form("form_nuevo_cliente", clear_on_submit=True):
                nombre_local = st.text_input("Nombre del Local / Empresa")
                responsable = st.text_input("Persona Responsable")
                tel_local = st.text_input("Teléfono de Contacto")
                dir_local = st.text_input("Dirección Completa")
                tipo_local = st.selectbox("Tipo de Establecimiento", TIPOS_ESTABLECIMIENTO, help="Define los rangos de infestación (Baja/Media/Alta) que se usarán para este cliente.")
                
                btn_cli = st.form_submit_button("Guardar Cliente", type="primary")
                if btn_cli:
                    if nombre_local.strip():
                        if agregar_cliente_db(nombre_local, responsable, tel_local, dir_local, tipo_establecimiento=tipo_local):
                            st.success("✅ Cliente registrado con éxito.")
                            st.rerun()
                        else:
                            st.error("⚠️ El nombre del local ya existe.")
                    else:
                        st.warning("El nombre del local es obligatorio.")
        
        st.markdown("### Listado de Clientes Registrados")
        clientes_detalle = obtener_todos_clientes_detalle()
        if clientes_detalle:
            df_clientes = pd.DataFrame(clientes_detalle, columns=["ID", "Local/Empresa", "Responsable", "Teléfono", "Dirección", "Técnico Asignado", "Tipo de Establecimiento"])
            st.dataframe(df_clientes.drop(columns=["ID"]), use_container_width=True)
        else:
            st.info("No hay clientes registrados todavía.")

    elif opcion == "📊 Historial & Reportes":
        st.subheader("📊 Historial General de Reportes")
        reportes = obtener_todos_reportes()
        if reportes:
            df_rep = pd.DataFrame(reportes, columns=["ID", "Cliente", "Técnico", "Plaga", "Tratamiento", "Estatus", "Fecha", "Evidencia", "Nivel Infestación", "Cantidad Observada"])
            st.dataframe(df_rep, use_container_width=True)
        else:
            st.info("No hay servicios registrados en el historial.")

    elif opcion == "📍 Ubicación Real":
        mostrar_ubicacion_real()

    elif opcion == "💬 Mensajería":
        mostrar_modulo_chat()

def vista_cliente():
    aplicar_estilos_sidebar()

    opcion = mostrar_navegacion(
        [
            "🏠 Inicio / Catálogo",
            "🧪 Productos Químicos",
            "📋 Mis Servicios & Reportes",
            "💬 Mensajería"
        ],
        session_key="nav_cliente",
        rol_label="Cliente / Sucursal"
    )
    
    if opcion == "🏠 Inicio / Catálogo":
        mostrar_catalogo_plagas_principal()

    elif opcion == "🧪 Productos Químicos":
        mostrar_catalogo_quimicos_principal()

    elif opcion == "📋 Mis Servicios & Reportes":
        st.subheader("📋 Historial de Servicios en tu Local")
        nombre_usuario = st.session_state.user['nombre']
        reportes = obtener_reportes_cliente(nombre_usuario)
        
        if reportes:
            for rep in reportes:
                _, cliente, tecnico, plaga, tratamiento, estatus, fecha, evidencia, *_resto = rep
                with st.expander(f"Servicio: {plaga} - Fecha: {fecha} [{estatus}]"):
                    st.write(f"**Técnico Asignado:** {tecnico}")
                    st.write(f"**Tratamiento:** {tratamiento}")
                    st.write(f"**Estatus:** {estatus}")
                    if evidencia and os.path.exists(evidencia):
                        st.image(evidencia, width=300, caption="Evidencia del servicio")
        else:
            st.info("Aún no cuentas con reportes de servicio registrados a tu nombre.")

    elif opcion == "💬 Mensajería":
        mostrar_modulo_chat()

# =============================================================================
# 7. CONTROL DE FLUJO PRINCIPAL
# =============================================================================
if st.session_state.user is None:
    mostrar_autenticacion()
else:
    rol_actual = st.session_state.user['rol']
    if rol_actual == "Técnico":
        vista_tecnico()
    elif rol_actual == "Cliente":
        vista_cliente()
    else:
        vista_tecnico()
