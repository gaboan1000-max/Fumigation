import streamlit as st
import sqlite3
import hashlib
import os
import random
from datetime import datetime
import pandas as pd
import streamlit.components.v1 as components
import urllib.parse

# Driver de PostgreSQL para Railway
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_DISPONIBLE = True
except ImportError:
    PSYCOPG2_DISPONIBLE = False

try:
    from streamlit_drawable_canvas import st_canvas
    CANVAS_DISPONIBLE = True
except ImportError:
    CANVAS_DISPONIBLE = False

try:
    from PIL import Image
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False

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

# Detectar si estamos en Railway con PostgreSQL o en local con SQLite
DATABASE_URL = os.getenv("DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL and PSYCOPG2_DISPONIBLE)
DB_NAME = "fumigaciones.db"

def get_connection():
    """Devuelve la conexión y un flag indicando si es Postgres o SQLite."""
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn, True
    conn = sqlite3.connect(DB_NAME)
    return conn, False

def run_query(query, params=(), fetch=None):
    """
    Ejecutor agnóstico de consultas que traduce sintaxis entre PostgreSQL y SQLite.
    fetch: None, 'one', 'all', 'rowcount'
    """
    conn, is_pg = get_connection()
    c = conn.cursor()
    
    # Adaptar placeholders
    if is_pg:
        query = query.replace("?", "%s")
    
    try:
        c.execute(query, params)
        if fetch == "one":
            res = c.fetchone()
        elif fetch == "all":
            res = c.fetchall()
        elif fetch == "rowcount":
            res = c.rowcount
        else:
            res = None
        conn.commit()
        return res
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        c.close()
        conn.close()

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

_CODIGO_ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

def _generar_codigo_aleatorio(longitud=6):
    return "".join(random.choice(_CODIGO_ALFABETO) for _ in range(longitud))

def init_db():
    pk_def = "SERIAL PRIMARY KEY" if IS_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    run_query(f'''
        CREATE TABLE IF NOT EXISTS usuarios (
            id {pk_def},
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            telefono TEXT,
            salt TEXT,
            codigo_tecnico TEXT
        )
    ''')
    
    # Migración automática si la tabla ya existía sin la columna
    try:
        if IS_POSTGRES:
            run_query("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS codigo_tecnico TEXT")
        else:
            # SQLite no soporta IF NOT EXISTS en ALTER TABLE
            columnas = [col[1] for col in run_query("PRAGMA table_info(usuarios)", fetch="all")]
            if "codigo_tecnico" not in columnas:
                run_query("ALTER TABLE usuarios ADD COLUMN codigo_tecnico TEXT")
    except Exception:
        pass
    
    run_query(f'''
        CREATE TABLE IF NOT EXISTS clientes_registrados (
            id {pk_def},
            nombre_local TEXT UNIQUE NOT NULL,
            responsable TEXT,
            telefono TEXT,
            direccion TEXT,
            tecnico_asignado TEXT,
            tipo_establecimiento TEXT DEFAULT 'Vivienda'
        )
    ''')

    run_query(f'''
        CREATE TABLE IF NOT EXISTS reportes (
            id {pk_def},
            cliente_nombre TEXT NOT NULL,
            tecnico_nombre TEXT NOT NULL,
            tipo_plaga TEXT NOT NULL,
            tratamiento TEXT NOT NULL,
            estatus TEXT DEFAULT 'Completado',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            evidencia_path TEXT,
            nivel_infestacion TEXT DEFAULT 'Media',
            cantidad_observada INTEGER DEFAULT 0,
            encargado_nombre TEXT,
            firma_path TEXT,
            certificado_path TEXT
        )
    ''')

    run_query(f'''
        CREATE TABLE IF NOT EXISTS mensajes (
            id {pk_def},
            remitente TEXT NOT NULL,
            destinatario TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    run_query('''
        CREATE TABLE IF NOT EXISTS rangos_infestacion (
            tipo_establecimiento TEXT NOT NULL,
            nivel TEXT NOT NULL,
            minimo INTEGER NOT NULL,
            maximo INTEGER,
            PRIMARY KEY (tipo_establecimiento, nivel)
        )
    ''')

    # Sembrar rangos por defecto
    total_rangos = run_query("SELECT COUNT(*) FROM rangos_infestacion", fetch="one")[0]
    if total_rangos == 0:
        rangos_default = [
            ("Vivienda",               "Baja", 1, 10), ("Vivienda",               "Media", 11, 50), ("Vivienda",               "Alta", 51, None),
            ("Hotel",                  "Baja", 1, 5),  ("Hotel",                  "Media", 6, 20),  ("Hotel",                  "Alta", 21, None),
            ("Restaurante / Comercio", "Baja", 1, 3),  ("Restaurante / Comercio", "Media", 4, 15),  ("Restaurante / Comercio", "Alta", 16, None),
            ("Industria Alimentaria",  "Baja", 1, 2),  ("Industria Alimentaria",  "Media", 3, 10),  ("Industria Alimentaria",  "Alta", 11, None),
            ("Hospital / Escuela",     "Baja", 1, 5),  ("Hospital / Escuela",     "Media", 6, 20),  ("Hospital / Escuela",     "Alta", 21, None),
            ("Oficina / Bodega",       "Baja", 1, 10), ("Oficina / Bodega",       "Media", 11, 40), ("Oficina / Bodega",       "Alta", 41, None),
        ]
        for r in rangos_default:
            run_query(
                "INSERT INTO rangos_infestacion(tipo_establecimiento, nivel, minimo, maximo) VALUES (?,?,?,?)",
                r
            )

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
    fila = run_query(
        "SELECT nombre FROM usuarios WHERE codigo_tecnico = ? AND rol = 'Técnico'",
        (codigo.strip().upper(),), fetch="one"
    )
    return fila[0] if fila else None

def obtener_codigo_tecnico(correo_tecnico):
    fila = run_query(
        "SELECT codigo_tecnico FROM usuarios WHERE correo = ?",
        (correo_tecnico.strip().lower(),), fetch="one"
    )
    return fila[0] if fila else None

def generar_codigo_tecnico(correo_tecnico):
    while True:
        codigo = _generar_codigo_aleatorio()
        existe = run_query("SELECT 1 FROM usuarios WHERE codigo_tecnico = ?", (codigo,), fetch="one")
        if not existe:
            break
    afectadas = run_query(
        "UPDATE usuarios SET codigo_tecnico = ? WHERE correo = ?",
        (codigo, correo_tecnico.strip().lower()), fetch="rowcount"
    )
    return codigo if afectadas and afectadas > 0 else None

def agregar_usuario(nombre, correo, password, rol, telefono, codigo_tecnico_ingresado=""):
    try:
        tecnico_asignado = None
        if rol == "Cliente" and codigo_tecnico_ingresado.strip():
            tecnico_asignado = obtener_tecnico_por_codigo(codigo_tecnico_ingresado)
            if not tecnico_asignado:
                return "codigo_invalido"

        salt = generar_salt()
        hashed = make_hashes(password, salt)
        run_query(
            "INSERT INTO usuarios(nombre, correo, password, rol, telefono, salt) VALUES (?,?,?,?,?,?)",
            (nombre.strip(), correo.strip().lower(), hashed, rol, telefono.strip(), salt)
        )
        if tecnico_asignado:
            agregar_cliente_db(nombre.strip(), nombre.strip(), telefono.strip(), "", tecnico_asignado)

        return "ok"
    except Exception:
        return "email_duplicado"

def login_usuario(correo, password):
    data = run_query("SELECT * FROM usuarios WHERE correo = ?", (correo.strip().lower(),), fetch="one")
    if data:
        salt = data[6] if len(data) > 6 else None
        if check_hashes(password, salt, data[3]):
            return data
    return None

TIPOS_ESTABLECIMIENTO = ["Vivienda", "Hotel", "Restaurante / Comercio", "Industria Alimentaria", "Hospital / Escuela", "Oficina / Bodega"]

def agregar_cliente_db(nombre_local, responsable, telefono, direccion, tecnico_asignado=None, tipo_establecimiento="Vivienda"):
    try:
        run_query(
            "INSERT INTO clientes_registrados(nombre_local, responsable, telefono, direccion, tecnico_asignado, tipo_establecimiento) VALUES (?,?,?,?,?,?)",
            (nombre_local.strip(), responsable.strip(), telefono.strip(), direccion.strip(), tecnico_asignado, tipo_establecimiento)
        )
        return True
    except Exception:
        return False

def obtener_tipo_establecimiento(nombre_cliente):
    query = "SELECT tipo_establecimiento FROM clientes_registrados WHERE LOWER(nombre_local) = LOWER(?)"
    fila = run_query(query, (nombre_cliente,), fetch="one")
    return fila[0] if fila and fila[0] else "Vivienda"

def obtener_lista_clientes():
    locales = [row[0] for row in run_query("SELECT nombre_local FROM clientes_registrados", fetch="all")]
    usuarios_clientes = [row[0] for row in run_query("SELECT nombre FROM usuarios WHERE rol = 'Cliente'", fetch="all")]
    return sorted(list(set(locales + usuarios_clientes)))

def obtener_todos_clientes_detalle():
    return run_query("SELECT * FROM clientes_registrados ORDER BY nombre_local ASC", fetch="all")

def obtener_contactos_disponibles(mi_nombre):
    return run_query("SELECT nombre, rol FROM usuarios WHERE nombre != ?", (mi_nombre,), fetch="all")

DESCRIPCION_NIVEL = {
    "Baja": ("🟢", "Se observan pocos individuos o evidencia mínima de actividad. No representa una infestación generalizada."),
    "Media": ("🟡", "Presencia frecuente de la plaga en una o varias áreas. Requiere tratamiento correctivo."),
    "Alta": ("🔴", "Presencia numerosa y generalizada de la plaga. Requiere intervención inmediata."),
}

def obtener_rangos_por_tipo(tipo_establecimiento):
    filas_raw = run_query(
        "SELECT nivel, minimo, maximo FROM rangos_infestacion WHERE tipo_establecimiento = ?",
        (tipo_establecimiento,), fetch="all"
    )
    filas = {nivel: (minimo, maximo) for nivel, minimo, maximo in filas_raw}
    orden = ["Baja", "Media", "Alta"]
    return [(nivel, filas[nivel][0], filas[nivel][1]) for nivel in orden if nivel in filas]

def actualizar_rango(tipo_establecimiento, nivel, minimo, maximo):
    run_query(
        "UPDATE rangos_infestacion SET minimo = ?, maximo = ? WHERE tipo_establecimiento = ? AND nivel = ?",
        (minimo, maximo, tipo_establecimiento, nivel)
    )

def clasificar_nivel_infestacion(cantidad, tipo_establecimiento="Vivienda"):
    rangos = obtener_rangos_por_tipo(tipo_establecimiento)
    if not rangos:
        rangos = obtener_rangos_por_tipo("Vivienda")
    for nivel, minimo, maximo in rangos:
        if cantidad < minimo:
            continue
        if maximo is None or cantidad <= maximo:
            return nivel
    return rangos[-1][0] if rangos else "Baja"

def guardar_reporte(cliente, tecnico, plaga, tratamiento, estatus, evidencia_path, nivel_infestacion="Media", cantidad_observada=0, encargado_nombre="", firma_path="", certificado_path=""):
    run_query('''
        INSERT INTO reportes(cliente_nombre, tecnico_nombre, tipo_plaga, tratamiento, estatus, evidencia_path, nivel_infestacion, cantidad_observada, encargado_nombre, firma_path, certificado_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (cliente, tecnico, plaga, tratamiento, estatus, evidencia_path, nivel_infestacion, cantidad_observada, encargado_nombre, firma_path, certificado_path))

def obtener_reportes_cliente(nombre_cliente):
    return run_query(
        "SELECT * FROM reportes WHERE LOWER(cliente_nombre) = LOWER(?) ORDER BY fecha DESC",
        (nombre_cliente,), fetch="all"
    )

def obtener_todos_reportes():
    return run_query("SELECT * FROM reportes ORDER BY fecha DESC", fetch="all")

def obtener_infestacion_por_mes(anio, cliente=None):
    if IS_POSTGRES:
        if cliente:
            q = '''
                SELECT TO_CHAR(fecha, 'MM') AS mes, nivel_infestacion, COUNT(*) 
                FROM reportes
                WHERE TO_CHAR(fecha, 'YYYY') = ? AND LOWER(cliente_nombre) = LOWER(?)
                GROUP BY mes, nivel_infestacion
            '''
            return run_query(q, (str(anio), cliente), fetch="all")
        else:
            q = '''
                SELECT TO_CHAR(fecha, 'MM') AS mes, nivel_infestacion, COUNT(*) 
                FROM reportes
                WHERE TO_CHAR(fecha, 'YYYY') = ?
                GROUP BY mes, nivel_infestacion
            '''
            return run_query(q, (str(anio),), fetch="all")
    else:
        if cliente:
            q = '''
                SELECT strftime('%m', fecha) AS mes, nivel_infestacion, COUNT(*) 
                FROM reportes
                WHERE strftime('%Y', fecha) = ? AND LOWER(cliente_nombre) = LOWER(?)
                GROUP BY mes, nivel_infestacion
            '''
            return run_query(q, (str(anio), cliente), fetch="all")
        else:
            q = '''
                SELECT strftime('%m', fecha) AS mes, nivel_infestacion, COUNT(*) 
                FROM reportes
                WHERE strftime('%Y', fecha) = ?
                GROUP BY mes, nivel_infestacion
            '''
            return run_query(q, (str(anio),), fetch="all")

def obtener_anios_disponibles(cliente=None):
    if IS_POSTGRES:
        if cliente:
            q = "SELECT DISTINCT TO_CHAR(fecha, 'YYYY') FROM reportes WHERE LOWER(cliente_nombre) = LOWER(?) ORDER BY 1 DESC"
            filas = run_query(q, (cliente,), fetch="all")
        else:
            q = "SELECT DISTINCT TO_CHAR(fecha, 'YYYY') FROM reportes ORDER BY 1 DESC"
            filas = run_query(q, fetch="all")
    else:
        if cliente:
            q = "SELECT DISTINCT strftime('%Y', fecha) FROM reportes WHERE LOWER(cliente_nombre) = LOWER(?) ORDER BY 1 DESC"
            filas = run_query(q, (cliente,), fetch="all")
        else:
            q = "SELECT DISTINCT strftime('%Y', fecha) FROM reportes ORDER BY 1 DESC"
            filas = run_query(q, fetch="all")
    return [row[0] for row in filas if row and row[0]]

def enviar_mensaje_db(remitente, destinatario, texto):
    run_query("INSERT INTO mensajes(remitente, destinatario, mensaje) VALUES (?,?,?)", (remitente, destinatario, texto))

def obtener_conversacion(user1, user2):
    return run_query('''
        SELECT remitente, destinatario, mensaje, fecha 
        FROM mensajes 
        WHERE (remitente = ? AND destinatario = ?) OR (remitente = ? AND destinatario = ?)
        ORDER BY fecha ASC
    ''', (user1, user2, user2, user1), fetch="all")

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

    # ENTORNO PC
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

    # ENTORNO MÓVIL
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
                hora_str = str(hora)[11:16] if hora else ""
                es_mio = (remitente == mi_nombre)
                with st.chat_message("user" if es_mio else "assistant"):
                    st.write(f"**{remitente}** *({hora_str})*")
                    st.write(texto)
        else:
            st.caption("No hay mensajes previos. ¡Inicia el chat!")

    st.markdown("---")
    nuevo_msg = st.chat_input("Escribe tu mensaje...")
    if nuevo_msg:
        enviar_mensaje_db(mi_nombre, nombre_destinatario, nuevo_msg)
        st.rerun()

# =============================================================================
# 4. CATÁLOGOS Y MÓDULOS DE VISTA
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

CLASES_TOXICOLOGICAS = {
    "Verde":    {"orden": 1, "categoria": "Categoría IV",  "descripcion": "Ligeramente tóxico",    "color": "#22c55e", "icono": "🟢"},
    "Azul":     {"orden": 2, "categoria": "Categoría III", "descripcion": "Moderadamente tóxico",  "color": "#3b82f6", "icono": "🔵"},
    "Amarilla": {"orden": 3, "categoria": "Categoría II",  "descripcion": "Altamente tóxico",      "color": "#eab308", "icono": "🟡"},
    "Roja":     {"orden": 4, "categoria": "Categoría I",   "descripcion": "Extremadamente tóxico", "color": "#ef4444", "icono": "🔴"},
}

CLASE_TOXICOLOGICA_PRODUCTOS = {
    "Demand® 2.5 CS (Syngenta)": "Verde",
    "Termidor® 25 CE (BASF)": "Verde",
    "DDVP® 500 U (Agroquímica Tridente)": "Roja",
}

def mostrar_badge_toxicidad(clase, mostrar_descripcion=True):
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
            "Termidor® 25 CE (BASF)",
            "DDVP® 500 U (Agroquímica Tridente)",
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
            La lambda-cihalotrina actúa por **contacto e ingestión**, alterando los canales de sodio del sistema nervioso de los insectos.
            """)

        with tab_plagas:
            st.subheader("Plagas que Controla")
            st.markdown("* Cucarachas\n* Hormigas\n* Moscas\n* Mosquitos\n* Pulgas\n* Arañas\n* Alacranes")

        with tab_lugares:
            st.subheader("Lugares de Aplicación")
            st.markdown("* Viviendas\n* Restaurantes\n* Hoteles\n* Hospitales\n* Escuelas\n* Bodegas")

        with tab_ventajas:
            st.subheader("Ventajas")
            st.markdown("* ✔️ Rápido efecto de derribo.\n* ✔️ Excelente efecto residual.\n* ✔️ Base agua.")

        with tab_dosis:
            st.subheader("Dosis Recomendada")
            st.markdown("Seguir siempre la etiqueta oficial del producto.")

        with tab_epp:
            st.subheader("Equipo de Protección Personal")
            st.markdown("* Guantes resistentes a químicos.\n* Lentes de seguridad.\n* Mascarilla adecuada.\n* Overol y botas.")

        with tab_precauciones:
            st.subheader("Precauciones")
            st.warning("* Mantener fuera del alcance de niños y mascotas.\n* Altamente tóxico para organismos acuáticos.")

        with tab_residual:
            st.subheader("Tiempo Residual")
            st.markdown("El efecto residual suele mantenerse varias semanas.")

        with tab_toxi:
            st.subheader("Clasificación Toxicológica")
            mostrar_badge_toxicidad(CLASE_TOXICOLOGICA_PRODUCTOS.get(producto_seleccionado))

    elif producto_seleccionado == "Termidor® 25 CE (BASF)":
        st.markdown("---")
        col_img, col_info = st.columns([1, 1])

        with col_img:
            if os.path.exists("termidor_25ce.jpg"):
                st.image("termidor_25ce.jpg", caption="Termidor® 25 CE - BASF", use_container_width=True)
            else:
                st.info("💡 Guarda la imagen 'termidor_25ce.jpg' en la carpeta raíz.")
                uploaded_img = st.file_uploader("O sube la imagen del producto aquí:", type=["jpg", "png", "jpeg"], key="info_termidor25ce")
                if uploaded_img:
                    with open("termidor_25ce.jpg", "wb") as f:
                        f.write(uploaded_img.getbuffer())
                    st.rerun()

        with col_info:
            st.header("🐜 Termidor® 25 CE (*BASF*)")
            st.markdown("""
            **Termidor® 25 CE** es un insecticida profesional formulado con **Fipronil**, orientado al control de **termitas** y otras plagas urbanas.
            """)
            mostrar_badge_toxicidad(CLASE_TOXICOLOGICA_PRODUCTOS.get(producto_seleccionado))

    elif producto_seleccionado == "DDVP® 500 U (Agroquímica Tridente)":
        st.markdown("---")
        col_img, col_info = st.columns([1, 1])

        with col_img:
            if os.path.exists("ddvp_500u.jpg"):
                st.image("ddvp_500u.jpg", caption="DDVP® 500 U - Agroquímica Tridente", use_container_width=True)
            else:
                st.info("💡 Guarda la imagen 'ddvp_500u.jpg' en la carpeta raíz.")
                uploaded_img = st.file_uploader("O sube la imagen del producto aquí:", type=["jpg", "png", "jpeg"], key="info_ddvp500u")
                if uploaded_img:
                    with open("ddvp_500u.jpg", "wb") as f:
                        f.write(uploaded_img.getbuffer())
                    st.rerun()

        with col_info:
            st.header("🧪 DDVP® 500 U (*Agroquímica Tridente*)")
            st.markdown("""
            **DDVP® 500 U** está formulado con **diclorvos**. Uso exclusivo para aplicadores de plaguicidas.
            """)
            mostrar_badge_toxicidad(CLASE_TOXICOLOGICA_PRODUCTOS.get(producto_seleccionado))

    elif producto_seleccionado == "Próximamente más productos...":
        st.info("Estamos actualizando el catálogo con nuevos productos químicos. ¡Vuelve pronto!")

MESES_ORDEN = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
MESES_NOMBRE = {
    "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr", "05": "May", "06": "Jun",
    "07": "Jul", "08": "Ago", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"
}
NIVELES_ORDEN = ["Baja", "Media", "Alta"]

def mostrar_grafica_infestacion(cliente=None):
    st.subheader("📈 Nivel de Infestación Mensual")
    if cliente:
        st.caption("Cantidad de servicios registrados en tu local por nivel de infestación (Baja, Media, Alta) a lo largo del año.")
        tipo_ref = obtener_tipo_establecimiento(cliente)
    else:
        st.caption("Cantidad de servicios registrados por nivel de infestación (Baja, Media, Alta) a lo largo del año.")
        tipo_ref = st.selectbox("Ver rangos de referencia para:", TIPOS_ESTABLECIMIENTO, key="tipo_ref_grafica")

    with st.expander(f"ℹ️ ¿Cómo se clasifica la infestación en '{tipo_ref}'?"):
        for nivel, minimo, maximo in obtener_rangos_por_tipo(tipo_ref):
            icono, descripcion = DESCRIPCION_NIVEL[nivel]
            rango_texto = f"{minimo} a {maximo}" if maximo else f"Más de {minimo - 1}"
            st.markdown(f"**{icono} {nivel}** ({rango_texto}): {descripcion}")

    anios_disponibles = obtener_anios_disponibles(cliente=cliente)
    anio_actual = str(datetime.now().year)
    if anio_actual not in anios_disponibles:
        anios_disponibles = [anio_actual] + anios_disponibles

    anio_sel = st.selectbox("Año a consultar", anios_disponibles, index=0, key=f"anio_grafica_{'cliente' if cliente else 'tecnico'}")

    datos = obtener_infestacion_por_mes(anio_sel, cliente=cliente)

    tabla = {mes: {nivel: 0 for nivel in NIVELES_ORDEN} for mes in MESES_ORDEN}
    for mes, nivel, cantidad in datos:
        mes_formato = str(mes).zfill(2)
        if mes_formato in tabla and nivel in NIVELES_ORDEN:
            tabla[mes_formato][nivel] = cantidad

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

def mostrar_configurar_rangos():
    st.subheader("⚙️ Configurar Rangos de Infestación")
    st.caption("Ajusta a partir de cuántas plagas observadas se considera Baja, Media o Alta, según el tipo de lugar.")

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
# 5. AUTENTICACIÓN
# =============================================================================import streamlit as st
import sqlite3
import hashlib
import os
import random
from datetime import datetime
import pandas as pd
import streamlit.components.v1 as components
import urllib.parse
from io import BytesIO

# Driver de PostgreSQL para Railway / Producción
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_DISPONIBLE = True
except ImportError:
    PSYCOPG2_DISPONIBLE = False

# Integración con Cloudinary para almacenamiento persistente de imágenes
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_DISPONIBLE = True
except ImportError:
    CLOUDINARY_DISPONIBLE = False

try:
    from streamlit_drawable_canvas import st_canvas
    CANVAS_DISPONIBLE = True
except ImportError:
    CANVAS_DISPONIBLE = False

try:
    from PIL import Image
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False

# =============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y SERVICIOS EXTERNOS
# =============================================================================
FAVICON = "tortuga.png" if os.path.exists("tortuga.png") else "🐢"

st.set_page_config(
    page_title="FUMI-PRO | Gestión Integral de Control de Plagas",
    page_icon=FAVICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

if CLOUDINARY_DISPONIBLE and CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True
    )
    CLOUDINARY_ACTIVO = True
else:
    CLOUDINARY_ACTIVO = False

def subir_a_cloudinary(archivo_buffer, carpeta="evidencias_fumigacion"):
    """
    Sube un archivo a Cloudinary y devuelve la URL segura permanente.
    Si Cloudinary no está configurado, hace un guardado local de respaldo.
    """
    if CLOUDINARY_ACTIVO:
        try:
            resultado = cloudinary.uploader.upload(
                archivo_buffer,
                folder=carpeta,
                resource_type="auto"
            )
            return resultado.get("secure_url")
        except Exception as e:
            st.error(f"Error al subir imagen a Cloudinary: {e}")
            return None
    else:
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
        nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{getattr(archivo_buffer, 'name', 'img.png')}"
        path_local = os.path.join("uploads", nombre_archivo)
        with open(path_local, "wb") as f:
            if hasattr(archivo_buffer, "getbuffer"):
                f.write(archivo_buffer.getbuffer())
            elif isinstance(archivo_buffer, bytes):
                f.write(archivo_buffer)
            else:
                f.write(archivo_buffer.read())
        return path_local

# Conexión agnóstica Postgres (Railway) / SQLite (Local)
DATABASE_URL = os.getenv("DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL and PSYCOPG2_DISPONIBLE)
DB_NAME = "fumigaciones.db"

def get_connection():
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn, True
    conn = sqlite3.connect(DB_NAME)
    return conn, False

def run_query(query, params=(), fetch=None):
    conn, is_pg = get_connection()
    c = conn.cursor()
    if is_pg:
        query = query.replace("?", "%s")
    try:
        c.execute(query, params)
        if fetch == "one":
            res = c.fetchone()
        elif fetch == "all":
            res = c.fetchall()
        elif fetch == "rowcount":
            res = c.rowcount
        else:
            res = None
        conn.commit()
        return res
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        c.close()
        conn.close()

# =============================================================================
# TÉRMINOS Y CONDICIONES DE USO
# =============================================================================
TERMINOS_Y_CONDICIONES = """
**Última actualización:** 2026

Bienvenido a la plataforma de gestión de fumigaciones de **Los Ángeles Corporativo**. Al acceder, registrarse o utilizar este sitio web y sus servicios, el usuario acepta cumplir los presentes Términos y Condiciones. Si no está de acuerdo con alguno de ellos, deberá abstenerse de utilizar la plataforma.

### 1. Objeto
La plataforma tiene como finalidad facilitar la administración de servicios de control de plagas mediante el registro de clientes, captura de inspecciones, generación de reportes, almacenamiento de evidencias fotográficas, consulta de historial de servicios y firma digital.

### 2. Uso de la Plataforma
El usuario se compromete a utilizar la plataforma de manera responsable, ética y conforme a la legislación aplicable.

Queda prohibido:
- Utilizar información falsa o suplantar la identidad de otra persona.
- Intentar acceder sin autorización a cuentas, bases de datos o áreas restringidas.
- Alterar, modificar o eliminar información perteneciente a otros usuarios.
- Introducir software malicioso que afecte la integridad del sistema.

### 3. Registro y Seguridad
El usuario es responsable de mantener la confidencialidad de sus credenciales y de todas las actividades realizadas desde su cuenta.

### 4. Propiedad Intelectual
El código fuente, interfaces y elementos distintivos son propiedad de **Los Ángeles Corporativo** y están protegidos por la legislación aplicable.

### 5. Legislación Aplicable
Estos Términos y Condiciones se rigen por las leyes vigentes de los Estados Unidos Mexicanos y el Estado de Tabasco.
"""

def mostrar_terminos_condiciones():
    with st.expander("📄 Términos y Condiciones de Uso"):
        st.markdown(TERMINOS_Y_CONDICIONES)
        if "terminos_aceptados" not in st.session_state:
            st.session_state.terminos_aceptados = False
        if st.session_state.terminos_aceptados:
            st.success("✅ Has aceptado los Términos y Condiciones de Uso.")
        else:
            if st.button("Sí, acepto los términos", key="btn_aceptar_terminos", type="primary", use_container_width=True):
                st.session_state.terminos_aceptados = True
                st.rerun()

_CODIGO_ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

def _generar_codigo_aleatorio(longitud=6):
    return "".join(random.choice(_CODIGO_ALFABETO) for _ in range(longitud))

def init_db():
    pk_def = "SERIAL PRIMARY KEY" if IS_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    run_query(f'''
        CREATE TABLE IF NOT EXISTS usuarios (
            id {pk_def},
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            telefono TEXT,
            salt TEXT,
            codigo_tecnico TEXT
        )
    ''')

    try:
        if IS_POSTGRES:
            run_query("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS codigo_tecnico TEXT")
        else:
            columnas = [col[1] for col in run_query("PRAGMA table_info(usuarios)", fetch="all")]
            if "codigo_tecnico" not in columnas:
                run_query("ALTER TABLE usuarios ADD COLUMN codigo_tecnico TEXT")
    except Exception:
        pass
    
    run_query(f'''
        CREATE TABLE IF NOT EXISTS clientes_registrados (
            id {pk_def},
            nombre_local TEXT UNIQUE NOT NULL,
            responsable TEXT,
            telefono TEXT,
            direccion TEXT,
            tecnico_asignado TEXT,
            tipo_establecimiento TEXT DEFAULT 'Vivienda'
        )
    ''')

    run_query(f'''
        CREATE TABLE IF NOT EXISTS reportes (
            id {pk_def},
            cliente_nombre TEXT NOT NULL,
            tecnico_nombre TEXT NOT NULL,
            tipo_plaga TEXT NOT NULL,
            tratamiento TEXT NOT NULL,
            estatus TEXT DEFAULT 'Completado',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            evidencia_path TEXT,
            nivel_infestacion TEXT DEFAULT 'Media',
            cantidad_observada INTEGER DEFAULT 0,
            encargado_nombre TEXT,
            firma_path TEXT,
            certificado_path TEXT
        )
    ''')

    run_query(f'''
        CREATE TABLE IF NOT EXISTS mensajes (
            id {pk_def},
            remitente TEXT NOT NULL,
            destinatario TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    run_query('''
        CREATE TABLE IF NOT EXISTS rangos_infestacion (
            tipo_establecimiento TEXT NOT NULL,
            nivel TEXT NOT NULL,
            minimo INTEGER NOT NULL,
            maximo INTEGER,
            PRIMARY KEY (tipo_establecimiento, nivel)
        )
    ''')

    total_rangos = run_query("SELECT COUNT(*) FROM rangos_infestacion", fetch="one")[0]
    if total_rangos == 0:
        rangos_default = [
            ("Vivienda",               "Baja", 1, 10), ("Vivienda",               "Media", 11, 50), ("Vivienda",               "Alta", 51, None),
            ("Hotel",                  "Baja", 1, 5),  ("Hotel",                  "Media", 6, 20),  ("Hotel",                  "Alta", 21, None),
            ("Restaurante / Comercio", "Baja", 1, 3),  ("Restaurante / Comercio", "Media", 4, 15),  ("Restaurante / Comercio", "Alta", 16, None),
            ("Industria Alimentaria",  "Baja", 1, 2),  ("Industria Alimentaria",  "Media", 3, 10),  ("Industria Alimentaria",  "Alta", 11, None),
            ("Hospital / Escuela",     "Baja", 1, 5),  ("Hospital / Escuela",     "Media", 6, 20),  ("Hospital / Escuela",     "Alta", 21, None),
            ("Oficina / Bodega",       "Baja", 1, 10), ("Oficina / Bodega",       "Media", 11, 40), ("Oficina / Bodega",       "Alta", 41, None),
        ]
        for r in rangos_default:
            run_query(
                "INSERT INTO rangos_infestacion(tipo_establecimiento, nivel, minimo, maximo) VALUES (?,?,?,?)",
                r
            )

def generar_salt():
    return os.urandom(16).hex()

def make_hashes(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()

def check_hashes(password, salt, hashed_text):
    if salt:
        return make_hashes(password, salt) == hashed_text
    return hashlib.sha256(str.encode(password)).hexdigest() == hashed_text

init_db()

# =============================================================================
# 2. FUNCIONES DE BASE DE DATOS
# =============================================================================
def obtener_tecnico_por_codigo(codigo):
    fila = run_query(
        "SELECT nombre FROM usuarios WHERE codigo_tecnico = ? AND rol = 'Técnico'",
        (codigo.strip().upper(),), fetch="one"
    )
    return fila[0] if fila else None

def obtener_codigo_tecnico(correo_tecnico):
    fila = run_query(
        "SELECT codigo_tecnico FROM usuarios WHERE correo = ?",
        (correo_tecnico.strip().lower(),), fetch="one"
    )
    return fila[0] if fila else None

def generar_codigo_tecnico(correo_tecnico):
    while True:
        codigo = _generar_codigo_aleatorio()
        existe = run_query("SELECT 1 FROM usuarios WHERE codigo_tecnico = ?", (codigo,), fetch="one")
        if not existe:
            break
    afectadas = run_query(
        "UPDATE usuarios SET codigo_tecnico = ? WHERE correo = ?",
        (codigo, correo_tecnico.strip().lower()), fetch="rowcount"
    )
    return codigo if afectadas and afectadas > 0 else None

def agregar_usuario(nombre, correo, password, rol, telefono, codigo_tecnico_ingresado=""):
    try:
        tecnico_asignado = None
        if rol == "Cliente" and codigo_tecnico_ingresado.strip():
            tecnico_asignado = obtener_tecnico_por_codigo(codigo_tecnico_ingresado)
            if not tecnico_asignado:
                return "codigo_invalido"

        salt = generar_salt()
        hashed = make_hashes(password, salt)
        run_query(
            "INSERT INTO usuarios(nombre, correo, password, rol, telefono, salt) VALUES (?,?,?,?,?,?)",
            (nombre.strip(), correo.strip().lower(), hashed, rol, telefono.strip(), salt)
        )
        if tecnico_asignado:
            agregar_cliente_db(nombre.strip(), nombre.strip(), telefono.strip(), "", tecnico_asignado)

        return "ok"
    except Exception:
        return "email_duplicado"

def login_usuario(correo, password):
    data = run_query("SELECT * FROM usuarios WHERE correo = ?", (correo.strip().lower(),), fetch="one")
    if data:
        salt = data[6] if len(data) > 6 else None
        if check_hashes(password, salt, data[3]):
            return data
    return None

TIPOS_ESTABLECIMIENTO = ["Vivienda", "Hotel", "Restaurante / Comercio", "Industria Alimentaria", "Hospital / Escuela", "Oficina / Bodega"]

def agregar_cliente_db(nombre_local, responsable, telefono, direccion, tecnico_asignado=None, tipo_establecimiento="Vivienda"):
    try:
        run_query(
            "INSERT INTO clientes_registrados(nombre_local, responsable, telefono, direccion, tecnico_asignado, tipo_establecimiento) VALUES (?,?,?,?,?,?)",
            (nombre_local.strip(), responsable.strip(), telefono.strip(), direccion.strip(), tecnico_asignado, tipo_establecimiento)
        )
        return True
    except Exception:
        return False

def obtener_tipo_establecimiento(nombre_cliente):
    query = "SELECT tipo_establecimiento FROM clientes_registrados WHERE LOWER(nombre_local) = LOWER(?)"
    fila = run_query(query, (nombre_cliente,), fetch="one")
    return fila[0] if fila and fila[0] else "Vivienda"

def obtener_lista_clientes():
    locales = [row[0] for row in run_query("SELECT nombre_local FROM clientes_registrados", fetch="all")]
    usuarios_clientes = [row[0] for row in run_query("SELECT nombre FROM usuarios WHERE rol = 'Cliente'", fetch="all")]
    return sorted(list(set(locales + usuarios_clientes)))

def obtener_todos_clientes_detalle():
    return run_query("SELECT * FROM clientes_registrados ORDER BY nombre_local ASC", fetch="all")

def obtener_contactos_disponibles(mi_nombre):
    return run_query("SELECT nombre, rol FROM usuarios WHERE nombre != ?", (mi_nombre,), fetch="all")

def obtener_rangos_por_tipo(tipo_establecimiento):
    filas_raw = run_query(
        "SELECT nivel, minimo, maximo FROM rangos_infestacion WHERE tipo_establecimiento = ?",
        (tipo_establecimiento,), fetch="all"
    )
    filas = {nivel: (minimo, maximo) for nivel, minimo, maximo in filas_raw}
    orden = ["Baja", "Media", "Alta"]
    return [(nivel, filas[nivel][0], filas[nivel][1]) for nivel in orden if nivel in filas]

def actualizar_rango(tipo_establecimiento, nivel, minimo, maximo):
    run_query(
        "UPDATE rangos_infestacion SET minimo = ?, maximo = ? WHERE tipo_establecimiento = ? AND nivel = ?",
        (minimo, maximo, tipo_establecimiento, nivel)
    )

def clasificar_nivel_infestacion(cantidad, tipo_establecimiento="Vivienda"):
    rangos = obtener_rangos_por_tipo(tipo_establecimiento)
    if not rangos:
        rangos = obtener_rangos_por_tipo("Vivienda")
    for nivel, minimo, maximo in rangos:
        if cantidad < minimo:
            continue
        if maximo is None or cantidad <= maximo:
            return nivel
    return rangos[-1][0] if rangos else "Baja"

def guardar_reporte(cliente, tecnico, plaga, tratamiento, estatus, evidencia_path, nivel_infestacion="Media", cantidad_observada=0, encargado_nombre="", firma_path="", certificado_path=""):
    run_query('''
        INSERT INTO reportes(cliente_nombre, tecnico_nombre, tipo_plaga, tratamiento, estatus, evidencia_path, nivel_infestacion, cantidad_observada, encargado_nombre, firma_path, certificado_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (cliente, tecnico, plaga, tratamiento, estatus, evidencia_path, nivel_infestacion, cantidad_observada, encargado_nombre, firma_path, certificado_path))

def obtener_reportes_cliente(nombre_cliente):
    return run_query(
        "SELECT * FROM reportes WHERE LOWER(cliente_nombre) = LOWER(?) ORDER BY fecha DESC",
        (nombre_cliente,), fetch="all"
    )

def obtener_todos_reportes():
    return run_query("SELECT * FROM reportes ORDER BY fecha DESC", fetch="all")

def obtener_infestacion_por_mes(anio, cliente=None):
    if IS_POSTGRES:
        if cliente:
            q = '''
                SELECT TO_CHAR(fecha, 'MM') AS mes, nivel_infestacion, COUNT(*) 
                FROM reportes
                WHERE TO_CHAR(fecha, 'YYYY') = ? AND LOWER(cliente_nombre) = LOWER(?)
                GROUP BY mes, nivel_infestacion
            '''
            return run_query(q, (str(anio), cliente), fetch="all")
        else:
            q = '''
                SELECT TO_CHAR(fecha, 'MM') AS mes, nivel_infestacion, COUNT(*) 
                FROM reportes
                WHERE TO_CHAR(fecha, 'YYYY') = ?
                GROUP BY mes, nivel_infestacion
            '''
            return run_query(q, (str(anio),), fetch="all")
    else:
        if cliente:
            q = '''
                SELECT strftime('%m', fecha) AS mes, nivel_infestacion, COUNT(*) 
                FROM reportes
                WHERE strftime('%Y', fecha) = ? AND LOWER(cliente_nombre) = LOWER(?)
                GROUP BY mes, nivel_infestacion
            '''
            return run_query(q, (str(anio), cliente), fetch="all")
        else:
            q = '''
                SELECT strftime('%m', fecha) AS mes, nivel_infestacion, COUNT(*) 
                FROM reportes
                WHERE strftime('%Y', fecha) = ?
                GROUP BY mes, nivel_infestacion
            '''
            return run_query(q, (str(anio),), fetch="all")

def obtener_anios_disponibles(cliente=None):
    if IS_POSTGRES:
        if cliente:
            q = "SELECT DISTINCT TO_CHAR(fecha, 'YYYY') FROM reportes WHERE LOWER(cliente_nombre) = LOWER(?) ORDER BY 1 DESC"
            filas = run_query(q, (cliente,), fetch="all")
        else:
            q = "SELECT DISTINCT TO_CHAR(fecha, 'YYYY') FROM reportes ORDER BY 1 DESC"
            filas = run_query(q, fetch="all")
    else:
        if cliente:
            q = "SELECT DISTINCT strftime('%Y', fecha) FROM reportes WHERE LOWER(cliente_nombre) = LOWER(?) ORDER BY 1 DESC"
            filas = run_query(q, (cliente,), fetch="all")
        else:
            q = "SELECT DISTINCT strftime('%Y', fecha) FROM reportes ORDER BY 1 DESC"
            filas = run_query(q, fetch="all")
    return [row[0] for row in filas if row and row[0]]

def enviar_mensaje_db(remitente, destinatario, texto):
    run_query("INSERT INTO mensajes(remitente, destinatario, mensaje) VALUES (?,?,?)", (remitente, destinatario, texto))

def obtener_conversacion(user1, user2):
    return run_query('''
        SELECT remitente, destinatario, mensaje, fecha 
        FROM mensajes 
        WHERE (remitente = ? AND destinatario = ?) OR (remitente = ? AND destinatario = ?)
        ORDER BY fecha ASC
    ''', (user1, user2, user2, user1), fetch="all")

# =============================================================================
# 3. ESTILOS Y COMPONENTES VISUALES
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
    aplicar_estilos_sidebar()

    if session_key not in st.session_state:
        st.session_state[session_key] = opciones[0]

    if st.session_state[session_key] not in opciones:
        st.session_state[session_key] = opciones[0]

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

    # Vista Computadora
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

    # Vista Móvil
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

# =============================================================================
# 4. MÓDULO DE MENSAJERÍA INTERNA
# =============================================================================
def mostrar_modulo_chat():
    st.subheader("💬 Mensajería Interna Directa")
    mi_nombre = st.session_state.user['nombre']
    contactos = obtener_contactos_disponibles(mi_nombre)
    
    if not contactos:
        st.info("Aún no hay otros usuarios registrados en el sistema.")
        return

    lista_contactos = [f"{nombre} ({rol})" for nombre, rol in contactos]
    contacto_seleccionado = st.selectbox("Selecciona un usuario para conversar:", lista_contactos)
    nombre_destinatario = contacto_seleccionado.split(" (")[0]
    
    st.markdown("---")
    mensajes = obtener_conversacion(mi_nombre, nombre_destinatario)
    
    contenedor_chat = st.container(height=380)
    with contenedor_chat:
        if not mensajes:
            st.caption("No hay mensajes previos en este canal. Envía el primero.")
        for rem, _, texto, fecha in mensajes:
            es_mio = (rem == mi_nombre)
            with st.chat_message("user" if es_mio else "assistant"):
                st.markdown(f"**{rem}** *({fecha})*")
                st.write(texto)

    with st.form("form_chat_envio", clear_on_submit=True):
        col_txt, col_btn = st.columns([4, 1])
        with col_txt:
            nuevo_mensaje = st.text_input("Mensaje", placeholder="Escribe tu mensaje...", label_visibility="collapsed")
        with col_btn:
            enviar = st.form_submit_button("Enviar", use_container_width=True, type="primary")
        
        if enviar and nuevo_mensaje.strip():
            enviar_mensaje_db(mi_nombre, nombre_destinatario, nuevo_mensaje.strip())
            st.rerun()

# =============================================================================
# 5. VISTAS DE USUARIOS SEGÚN ROL
# =============================================================================

# --- VISTA TÉCNICO ---
def vista_tecnico():
    opciones = ["Nuevo Servicio", "Historial de Servicios", "Directorio Clientes", "Chat Interno"]
    opcion = mostrar_navegacion(opciones, "nav_tecnico", "Técnico Especialista")

    if opcion == "Nuevo Servicio":
        st.header("📝 Registrar Nuevo Servicio / Inspección")
        clientes = obtener_lista_clientes()
        
        if not clientes:
            st.warning("No hay clientes registrados en la base de datos. Da de alta uno primero en 'Directorio Clientes'.")
            return

        cliente = st.selectbox("Seleccionar Cliente / Razón Social", clientes)
        tipo_est = obtener_tipo_establecimiento(cliente)
        st.info(f"Tipo de establecimiento asignado: **{tipo_est}**")

        with st.form("form_nuevo_servicio"):
            col1, col2 = st.columns(2)
            with col1:
                tipo_plaga = st.text_input("Plaga Identificada", placeholder="Ej. Cucaracha germánica, Roedores, Termitas")
                tratamiento = st.text_area("Tratamiento / Producto Químico Aplicado", placeholder="Detalla químicos, dosis y zonas tratadas...")
            with col2:
                cantidad_obs = st.number_input("Cantidad / Conteo de Ejemplares Observados", min_value=0, value=2)
                nivel_sugerido = clasificar_nivel_infestacion(cantidad_obs, tipo_est)
                st.caption(f"Nivel de infestación calculado: **{nivel_sugerido}**")
                encargado = st.text_input("Nombre de la persona que recibe")
                estatus = st.selectbox("Estatus de la Operación", ["Completado", "Pendiente de Refuerzo", "En Proceso"])

            foto = st.file_uploader("Evidencia Fotográfica (Opcional)", type=["png", "jpg", "jpeg"])
            
            st.markdown("#### Firma Digital de Conformidad")
            firma_img_data = None
            if CANVAS_DISPONIBLE:
                canvas_result = st_canvas(
                    stroke_width=2,
                    stroke_color="#000000",
                    background_color="#ffffff",
                    height=150,
                    width=400,
                    drawing_mode="freedraw",
                    key="canvas_firma"
                )
                if canvas_result.image_data is not None:
                    firma_img_data = canvas_result.image_data

            enviar_servicio = st.form_submit_button("Guardar y Certificar Servicio", use_container_width=True, type="primary")
            
            if enviar_servicio:
                if not tipo_plaga.strip() or not tratamiento.strip():
                    st.error("Es obligatorio capturar la plaga y el tratamiento aplicado.")
                else:
                    path_foto = None
                    path_firma = None

                    if foto:
                        with st.spinner("Subiendo evidencia fotográfica..."):
                            path_foto = subir_a_cloudinary(foto, carpeta="evidencias_fumigacion")

                    if PIL_DISPONIBLE and firma_img_data is not None:
                        try:
                            img_pil = Image.fromarray(firma_img_data.astype('uint8'))
                            buf = BytesIO()
                            img_pil.save(buf, format="PNG")
                            buf.seek(0)
                            with st.spinner("Guardando firma digital..."):
                                path_firma = subir_a_cloudinary(buf, carpeta="firmas_servicios")
                        except Exception as ex_firma:
                            st.warning(f"No se pudo procesar la firma: {ex_firma}")

                    guardar_reporte(
                        cliente=cliente,
                        tecnico=st.session_state.user['nombre'],
                        plaga=tipo_plaga,
                        tratamiento=tratamiento,
                        estatus=estatus,
                        evidencia_path=path_foto,
                        nivel_infestacion=nivel_sugerido,
                        cantidad_observada=cantidad_obs,
                        encargado_nombre=encargado,
                        firma_path=path_firma
                    )
                    st.success("✅ ¡Servicio registrado e indexado exitosamente!")

    elif opcion == "Historial de Servicios":
        st.header("📋 Historial Global de Servicios")
        reportes = obtener_todos_reportes()
        if reportes:
            df = pd.DataFrame(reportes, columns=[
                "ID", "Cliente", "Técnico", "Plaga", "Tratamiento", "Estatus",
                "Fecha", "Evidencia", "Nivel", "Cantidad", "Encargado", "Firma", "Certificado"
            ])
            st.dataframe(df[["ID", "Fecha", "Cliente", "Técnico", "Plaga", "Nivel", "Estatus", "Encargado"]], use_container_width=True)
        else:
            st.info("Aún no hay reportes de servicios registrados.")

    elif opcion == "Directorio Clientes":
        st.header("🏢 Directorio de Clientes y Establecimientos")
        with st.expander("➕ Dar de Alta Nuevo Cliente / Local"):
            with st.form("form_reg_cliente"):
                c1, c2 = st.columns(2)
                with c1:
                    nom_local = st.text_input("Nombre del Establecimiento / Cliente")
                    resp = st.text_input("Encargado o Representante")
                    tipo_est = st.selectbox("Giro / Tipo de Establecimiento", TIPOS_ESTABLECIMIENTO)
                with c2:
                    tel = st.text_input("Teléfono Directo")
                    direc = st.text_input("Dirección Completa")
                
                if st.form_submit_button("Guardar Cliente", use_container_width=True, type="primary"):
                    if nom_local.strip():
                        if agregar_cliente_db(nom_local, resp, tel, direc, st.session_state.user['nombre'], tipo_est):
                            st.success(f"Cliente '{nom_local}' registrado con éxito.")
                            st.rerun()
                        else:
                            st.error("Ese nombre ya se encuentra registrado.")
                    else:
                        st.error("El nombre es requerido.")

        detalles = obtener_todos_clientes_detalle()
        if detalles:
            df_cli = pd.DataFrame(detalles, columns=["ID", "Local/Cliente", "Responsable", "Teléfono", "Dirección", "Técnico Asignado", "Tipo"])
            st.dataframe(df_cli, use_container_width=True)

    elif opcion == "Chat Interno":
        mostrar_modulo_chat()

# --- VISTA CLIENTE ---
def vista_cliente():
    opciones = ["Mis Servicios", "Gráficas & Reportes", "Mensajería"]
    opcion = mostrar_navegacion(opciones, "nav_cliente", "Cliente")

    mi_nombre = st.session_state.user['nombre']

    if opcion == "Mis Servicios":
        st.header(f"📦 Servicios Realizados: {mi_nombre}")
        reportes = obtener_reportes_cliente(mi_nombre)
        if reportes:
            for rep in reportes:
                with st.expander(f"📅 {rep[6]} | Plaga: {rep[3]} | Estatus: {rep[5]}"):
                    col_info, col_img = st.columns([2, 1])
                    with col_info:
                        st.write(f"**Técnico Especialista:** {rep[2]}")
                        st.write(f"**Tratamiento Aplicado:** {rep[4]}")
                        st.write(f"**Nivel de Infestación:** {rep[8]} ({rep[9]} observados)")
                        if rep[10]:
                            st.write(f"**Recibió:** {rep[10]}")
                    with col_img:
                        if rep[7]:
                            st.image(rep[7], caption="Evidencia fotográfica", use_container_width=True)
                        if rep[11]:
                            st.image(rep[11], caption="Firma de conformidad", width=200)
        else:
            st.info("No tienes servicios registrados en este momento.")

    elif opcion == "Gráficas & Reportes":
        st.header("📊 Métricas de Control y Eficiencia")
        anios = obtener_anios_disponibles(mi_nombre)
        if anios:
            anio_sel = st.selectbox("Filtrar por Año", anios)
            datos = obtener_infestacion_por_mes(anio_sel, mi_nombre)
            if datos:
                df_graf = pd.DataFrame(datos, columns=["Mes", "Nivel", "Cantidad"])
                st.bar_chart(df_graf.set_index("Mes")["Cantidad"])
            else:
                st.info("No hay datos para el año seleccionado.")
        else:
            st.info("Aún no existen registros históricos disponibles para graficar.")

    elif opcion == "Mensajería":
        mostrar_modulo_chat()

# --- VISTA ADMINISTRADOR ---
def vista_admin():
    opciones = ["Panel de Control", "Configuración de Rangos", "Auditoría de Servicios", "Chat Directo"]
    opcion = mostrar_navegacion(opciones, "nav_admin", "Administrador")

    if opcion == "Panel de Control":
        st.header("⚙️ Indicadores Operativos y Generales")
        col1, col2, col3 = st.columns(3)
        total_rep = run_query("SELECT COUNT(*) FROM reportes", fetch="one")[0]
        total_usr = run_query("SELECT COUNT(*) FROM usuarios", fetch="one")[0]
        total_cli = run_query("SELECT COUNT(*) FROM clientes_registrados", fetch="one")[0]
        
        col1.metric("Servicios Registrados", total_rep)
        col2.metric("Usuarios en Sistema", total_usr)
        col3.metric("Establecimientos", total_cli)

    elif opcion == "Configuración de Rangos":
        st.header("📏 Configuración de Umbrales de Infestación")
        tipo_sel = st.selectbox("Seleccionar Giro Comercial", TIPOS_ESTABLECIMIENTO)
        rangos = obtener_rangos_por_tipo(tipo_sel)
        
        st.write("Configuración de límites:")
        for nivel, mini, maxi in rangos:
            c1, c2 = st.columns(2)
            with c1:
                n_min = st.number_input(f"Mínimo {nivel}", value=mini, key=f"min_{tipo_sel}_{nivel}")
            with c2:
                n_max = st.number_input(f"Máximo {nivel} (0 = Sin límite superior)", value=maxi if maxi is not None else 0, key=f"max_{tipo_sel}_{nivel}")
            
            if st.button(f"Guardar rango {nivel}", key=f"btn_{tipo_sel}_{nivel}"):
                val_max = None if n_max == 0 else n_max
                actualizar_rango(tipo_sel, nivel, n_min, val_max)
                st.success(f"Umbral de {nivel} actualizado correctamente.")

    elif opcion == "Auditoría de Servicios":
        st.header("📋 Auditoría de Todos los Servicios")
        reps = obtener_todos_reportes()
        if reps:
            df = pd.DataFrame(reps, columns=[
                "ID", "Cliente", "Técnico", "Plaga", "Tratamiento", "Estatus",
                "Fecha", "Evidencia", "Nivel", "Cantidad", "Encargado", "Firma", "Certificado"
            ])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Sin registros en la base de datos.")

    elif opcion == "Chat Directo":
        mostrar_modulo_chat()

# =============================================================================
# 6. ENTRADA PRINCIPAL / AUTENTICACIÓN
# =============================================================================
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🛡️ FUMI-PRO | Plataforma de Fumigaciones")
    tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Crear Cuenta"])

    with tab_login:
        with st.form("form_login"):
            correo = st.text_input("Correo Electrónico")
            pwd = st.text_input("Contraseña", type="password")
            submit_login = st.form_submit_button("Entrar a la Plataforma", use_container_width=True, type="primary")

            if submit_login:
                usuario_db = login_usuario(correo, pwd)
                if usuario_db:
                    st.session_state.user = {
                        "id": usuario_db[0],
                        "nombre": usuario_db[1],
                        "correo": usuario_db[2],
                        "rol": usuario_db[4],
                        "telefono": usuario_db[5]
                    }
                    st.success(f"Sesión iniciada. Bienvenido, {usuario_db[1]}.")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifica tus datos de acceso.")

    with tab_registro:
        mostrar_terminos_condiciones()
        with st.form("form_registro"):
            nombre_reg = st.text_input("Nombre Completo o Razón Social")
            correo_reg = st.text_input("Correo Electrónico")
            tel_reg = st.text_input("Teléfono de Contacto")
            pwd_reg = st.text_input("Contraseña", type="password")
            rol_reg = st.selectbox("Rol", ["Cliente", "Técnico", "Administrador"])
            cod_tecnico_input = st.text_input("Código de Técnico Asignado (Opcional, si eres Cliente)")

            submit_reg = st.form_submit_button("Completar Registro", use_container_width=True, type="primary")

            if submit_reg:
                if not st.session_state.get("terminos_aceptados", False):
                    st.error("Debes aceptar los Términos y Condiciones antes de registrarte.")
                elif not nombre_reg.strip() or not correo_reg.strip() or not pwd_reg.strip():
                    st.error("Por favor llena los campos requeridos.")
                else:
                    res = agregar_usuario(nombre_reg, correo_reg, pwd_reg, rol_reg, tel_reg, cod_tecnico_input)
                    if res == "ok":
                        st.success("¡Registro completado! Ahora puedes iniciar sesión en la pestaña correspondiente.")
                    elif res == "codigo_invalido":
                        st.error("El código de técnico proporcionado no es válido.")
                    else:
                        st.error("Este correo ya se encuentra dado de alta.")

else:
    # Despacho de vista según rol
    rol_actual = st.session_state.user['rol']
    if rol_actual == "Técnico":
        vista_tecnico()
    elif rol_actual == "Cliente":
        vista_cliente()
    elif rol_actual == "Administrador":
        vista_admin()
