import streamlit as st
import sqlite3
import hashlib
import os
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes_registrados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_local TEXT UNIQUE NOT NULL,
            responsable TEXT,
            telefono TEXT,
            direccion TEXT
        )
    ''')
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remitente TEXT NOT NULL,
            destinatario TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

init_db()

if not os.path.exists("uploads"):
    os.makedirs("uploads")

# =============================================================================
# 2. FUNCIONES DE BASE DE DATOS
# =============================================================================
def agregar_usuario(nombre, correo, password, rol, telefono):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO usuarios(nombre, correo, password, rol, telefono) VALUES (?,?,?,?,?)",
            (nombre, correo, make_hashes(password), rol, telefono)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_usuario(correo, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE correo = ?", (correo,))
    data = c.fetchone()
    conn.close()
    if data and check_hashes(password, data[3]):
        return data
    return None

def agregar_cliente_db(nombre_local, responsable, telefono, direccion):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO clientes_registrados(nombre_local, responsable, telefono, direccion) VALUES (?,?,?,?)",
            (nombre_local, responsable, telefono, direccion)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

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

def guardar_reporte(cliente, tecnico, plaga, tratamiento, estatus, evidencia_path):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO reportes(cliente_nombre, tecnico_nombre, tipo_plaga, tratamiento, estatus, evidencia_path)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (cliente, tecnico, plaga, tratamiento, estatus, evidencia_path))
    conn.commit()
    conn.close()

def obtener_reportes_cliente(nombre_cliente):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM reportes WHERE cliente_nombre LIKE ? ORDER BY fecha DESC", (f"%{nombre_cliente}%",))
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
# 3. ESTILOS Y ANIMACIONES CSS (Optimizados para Móvil y PC)
# =============================================================================
def aplicar_estilos_sidebar():
    st.markdown("""
        <style>
            @keyframes fadeInSlideUp {
                0% { opacity: 0; transform: translateY(18px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            @keyframes sidebarSlideIn {
                0% { opacity: 0; transform: translateX(-25px); }
                100% { opacity: 1; transform: translateX(0); }
            }
            .main .block-container {
                animation: fadeInSlideUp 0.45s ease-out forwards;
                padding-top: 2rem;
            }
            [data-testid="stSidebar"] {
                background-color: #1a1c23;
                animation: sidebarSlideIn 0.40s ease-out forwards;
            }
            /* Animación de los elementos del menú en el Sidebar */
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
                background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
                padding: 16px;
                border-radius: 12px;
                border: 1px solid #4a5568;
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
                background-color: #319795;
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
                color: #a0aec0;
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1.2px;
                margin-bottom: 10px;
                padding-left: 5px;
            }

            /* AJUSTES RESPONSIVOS PARA MÓVILES */
            @media (max-width: 768px) {
                h1 { font-size: 1.8rem !important; line-height: 1.2 !important; }
                h2 { font-size: 1.4rem !important; line-height: 1.2 !important; }
                h3 { font-size: 1.1rem !important; }
                
                .main .block-container {
                    padding-top: 3.5rem !important; 
                    padding-left: 1rem !important;
                    padding-right: 1rem !important;
                }
                
                .profile-card {
                    margin-top: 35px; 
                }
            }
        </style>
    """, unsafe_allow_html=True)

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
        ["Cucaracha americana (Periplaneta americana)", "Próximamente más plagas..."]
    )
    
    if plaga_seleccionada == "Cucaracha americana (Periplaneta americana)":
        st.markdown("---")
        col_img, col_info = st.columns([1, 1])
        
        with col_img:
            if os.path.exists("cucaracha_americana.jpg"):
                st.image("cucaracha_americana.jpg", caption="Infografía Técnica: Cucaracha Americana", use_container_width=True)
            else:
                st.info("💡 Guarda la imagen 'cucaracha_americana.jpg' en la carpeta raíz.")
                uploaded_img = st.file_uploader("O sube la infografía aquí:", type=["jpg", "png", "jpeg"], key="infografia_cucaracha")
                if uploaded_img:
                    with open("cucaracha_americana.jpg", "wb") as f:
                        f.write(uploaded_img.getbuffer())
                    st.rerun()

        with col_info:
            st.header("🪳 Cucaracha americana (*Periplaneta americana*)")
            st.markdown("""
            La **cucaracha americana** (*Periplaneta americana*) es una de las especies de cucarachas más grandes y comunes en zonas urbanas. A pesar de su nombre, no es originaria de América; se cree que proviene de África y llegó al continente hace varios siglos a través del comercio marítimo.
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
            "🔄 Ciclo de Vida", "⚠️ Importancia Sanitaria", "💡 Curiosidades", "🛡️ Prevención y Control"
        ])

        with tab_bio:
            st.subheader("Características")
            st.markdown("""
            * **Tamaño:** Entre 3.5 y 5 cm de longitud.
            * **Color:** Marrón rojizo con una banda amarillenta detrás de la cabeza.
            * **Alas:** Tanto machos como hembras tienen alas completamente desarrolladas y pueden planear o realizar vuelos cortos.
            * **Velocidad:** Puede correr hasta 5.4 km/h, lo que la convierte en una de las cucarachas más rápidas.
            """)

        with tab_hab:
            st.subheader("Hábitat")
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                st.markdown("**Prefiere lugares:**")
                st.markdown("* Cálidos.\n* Húmedos.\n* Oscuros.")
            with col_h2:
                st.markdown("**Es común encontrarlas en:**")
                st.markdown("""
                * Alcantarillas y drenajes.
                * Sótanos y bodegas.
                * Cuartos de máquinas.
                * Cocinas y baños.
                * Basureros.
                """)

        with tab_dieta:
            st.subheader("Alimentación")
            st.markdown("""
            Es **omnívora y carroñera**, por lo que consume prácticamente cualquier materia orgánica.

            **Su dieta incluye:**
            * Restos de comida, pan y cereales.
            * Frutas, verduras y carne.
            * Papel, cartón y pegamento.
            * Cuero.
            * Alimento para mascotas.
            * Materia orgánica en descomposición.
            """)

        with tab_ciclo:
            st.subheader("Ciclo de Vida y Reproducción")
            st.markdown("""
            La cucaracha americana presenta tres etapas de desarrollo:
            """)
            st.markdown("""
            * **Huevo:** La hembra deposita los huevos dentro de una cápsula llamada **ooteca**. Cada ooteca contiene entre **14 y 16 huevos**.
            * **Ninfa:** Al nacer son pequeñas y no tienen alas. Mudan su exoesqueleto entre **10 y 13 veces** antes de convertirse en adultas.
            * **Adulto:** Puede vivir entre **1 y 2 años**, dependiendo de las condiciones ambientales.
            """)
            st.info("""
            **Reproducción:** Una hembra puede producir entre **15 y 90 ootecas** durante su vida. Esto representa la posibilidad de cientos de descendientes si las condiciones son favorables.
            """)

        with tab_salud:
            st.subheader("Importancia Sanitaria")
            st.write("Aunque normalmente no pican a las personas, son consideradas una plaga porque pueden transportar microorganismos en sus patas y cuerpo, contaminando alimentos y superficies.")
            
            st.error("""
            **Pueden contribuir a la dispersión de:**
            * Bacterias como *Salmonella* y *Escherichia coli* (E. coli).
            * Hongos y parásitos.
            """)
            
            st.warning("""
            **Riesgos para la salud:**  
            Sus excrementos, saliva y partes del exoesqueleto pueden provocar **alergias** y **crisis de asma**, especialmente en niños y personas sensibles.
            """)

        with tab_curio:
            st.subheader("Curiosidades")
            st.markdown("""
            * **Resistencia a la inanición:** Puede sobrevivir varias semanas sin alimento si dispone de agua.
            * **Supervivencia sin cabeza:** Puede vivir aproximadamente una semana sin cabeza, ya que respira por pequeños orificios llamados espiráculos distribuidos en el cuerpo. Finalmente muere por deshidratación.
            * **Hábitos nocturnos:** Es principalmente nocturna y evita la luz.
            * **Sensibilidad:** Tiene antenas muy sensibles que le ayudan a detectar obstáculos, alimentos y depredadores.
            * **Resistencia al agua:** Es capaz de soportar breves periodos de inmersión bajo el agua.
            """)

        with tab_prev:
            st.subheader("Prevención y Control")
            st.markdown("""
            Para evitar infestaciones se recomienda:
            
            1. Mantener los alimentos bien almacenados.
            2. Sacar la basura diariamente.
            3. Reparar fugas de agua.
            4. Sellar grietas y rendijas.
            5. Limpiar restos de comida y grasa.
            6. Mantener limpios drenajes y alcantarillas.
            
            👉 *En infestaciones severas, recurrir a un servicio profesional de control de plagas.*
            """)

# =============================================================================
# 5. AUTENTICACIÓN
# =============================================================================
if "user" not in st.session_state:
    st.session_state.user = None

def mostrar_autenticacion():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("tortuga.png"):
            st.image("tortuga.png", width=140)
            
        st.markdown("<h2 style='text-align: center;'>Gestión de Fumigaciones</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Plataforma Integral de Control de Plagas</p>", unsafe_allow_html=True)
        
        tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Crear Cuenta"])
        
        with tab_login:
            with st.form("form_login"):
                correo = st.text_input("Correo electrónico")
                password = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
                
                if submit:
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
                        st.error("Correo o contraseña incorrectos.")

        with tab_registro:
            with st.form("form_registro"):
                nuevo_nombre = st.text_input("Nombre Completo / Empresa")
                nuevo_correo = st.text_input("Correo Electrónico")
                nuevo_telefono = st.text_input("Teléfono")
                nuevo_rol = st.selectbox("Tipo de Usuario", ["Cliente", "Técnico"])
                pass1 = st.text_input("Contraseña", type="password")
                pass2 = st.text_input("Confirmar Contraseña", type="password")
                
                reg_submit = st.form_submit_button("Registrarse", use_container_width=True)
                if reg_submit:
                    if pass1 == pass2 and nuevo_nombre and nuevo_correo:
                        if agregar_usuario(nuevo_nombre, nuevo_correo, pass1, nuevo_rol, nuevo_telefono):
                            st.success("Cuenta creada exitosamente.")
                        else:
                            st.error("El correo ya existe.")

# =============================================================================
# 6. VISTAS PRINCIPALES
# =============================================================================
def vista_tecnico():
    aplicar_estilos_sidebar()
    
    with st.sidebar:
        if os.path.exists("tortuga.png"):
            st.image("tortuga.png", use_container_width=True)
            
        st.markdown(f"""
            <div class="profile-card">
                <div class="profile-name">{st.session_state.user['nombre']}</div>
                <div class="profile-role">Técnico Especialista</div>
            </div>
            <div class="menu-title">MENÚ PRINCIPAL</div>
        """, unsafe_allow_html=True)
    
        opcion = st.sidebar.radio(
            "", 
            [
                "🏠 Inicio / Catálogo",
                "➕ Registrar Servicio", 
                "👥 Gestión Clientes", 
                "📊 Historial & Reportes", 
                "📍 Ubicación Real", 
                "💬 Mensajería"
            ],
            label_visibility="collapsed"
        )

        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            st.session_state.user = None
            st.rerun()
    
    if opcion == "🏠 Inicio / Catálogo":
        mostrar_catalogo_plagas_principal()

    elif opcion == "➕ Registrar Servicio":
        st.subheader("📝 Registrar Servicio de Fumigación")
        lista_clientes = obtener_lista_clientes()
        
        with st.form("registro_fumigacion", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                cliente = st.selectbox("Cliente / Local", options=lista_clientes if lista_clientes else ["Sin clientes"])
                plaga = st.text_input("Tipo de Plaga", placeholder="Ej. Cucaracha, Roedores")
                estatus = st.selectbox("Estatus", ["Completado", "En Proceso", "Seguimiento Requerido"])
            with col2:
                tratamiento = st.text_area("Tratamiento Aplicado")
                evidencia = st.file_uploader("Evidencia Fotográfica", type=["jpg", "png", "jpeg"])
                
            guardar = st.form_submit_button("Guardar Reporte", type="primary")
            if guardar and cliente != "Sin clientes":
                file_path = None
                if evidencia:
                    file_path = os.path.join("uploads", f"{datetime.now().timestamp()}_{evidencia.name}")
                    with open(file_path, "wb") as f:
                        f.write(evidencia.getbuffer())
                guardar_reporte(cliente, st.session_state.user['nombre'], plaga, tratamiento, estatus, file_path)
                st.success("✅ Guardado correctamente.")

    elif opcion == "👥 Gestión Clientes":
        st.subheader("👥 Gestión de Clientes")
        tab1, tab2 = st.tabs(["➕ Agregar Cliente", "📋 Directorio"])
        with tab1:
            with st.form("form_nuevo_cliente", clear_on_submit=True):
                nom_local = st.text_input("Nombre del Local")
                resp = st.text_input("Responsable")
                tel = st.text_input("Teléfono")
                direc = st.text_input("Dirección")
                if st.form_submit_button("Guardar"):
                    if agregar_cliente_db(nom_local, resp, tel, direc):
                        st.success("Cliente registrado.")
        with tab2:
            for c in obtener_todos_clientes_detalle():
                with st.expander(f"🏢 {c[1]}"):
                    st.write(f"**Responsable:** {c[2]}")
                    st.write(f"**Teléfono:** {c[3]}")
                    st.write(f"**Dirección:** {c[4]}")

    elif opcion == "📊 Historial & Reportes":
        st.subheader("📋 Historial de Servicios")
        for r in obtener_todos_reportes():
            with st.expander(f"📌 Servicio #{r[0]} - {r[1]} ({r[6][:10]})"):
                st.write(f"**Técnico:** {r[2]} | **Plaga:** {r[3]}")
                st.write(f"**Tratamiento:** {r[4]}")
                if r[7] and os.path.exists(r[7]):
                    st.image(r[7], width=250)

    elif opcion == "📍 Ubicación Real":
        st.subheader("📍 Control de Ubicación del Técnico")
        
        EXACT_LAT = 17.867755
        EXACT_LON = -92.929815
        EXACT_DIR = "Las Mercedes, 86288 Playas del Rosario, Tabasco"

        params = st.query_params
        if "lat" in params and "lon" in params:
            try:
                st.session_state.mi_lat = float(params["lat"])
                st.session_state.mi_lon = float(params["lon"])
                st.session_state.mi_direccion = "Ubicación detectada por GPS actual"
            except ValueError:
                pass

        if "mi_lat" not in st.session_state:
            st.session_state.mi_lat = EXACT_LAT
            st.session_state.mi_lon = EXACT_LON
            st.session_state.mi_direccion = EXACT_DIR
            st.session_state.mi_estatus = "🟢 En Servicio"
            st.session_state.mi_actividad = "Servicio de Fumigación en Proceso"

        nombre_tecnico = st.session_state.user['nombre']

        col_config, col_mapa = st.columns([1, 1])

        with col_config:
            st.markdown("### ⚙️ Actualizar mi Estado / Dirección")
            
            st.markdown("**1. Detectar ubicación en tiempo real:**")
            html_gps_auto = """
                <button onclick="obtenerGPS()" style="
                    background-color: #319795;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    cursor: pointer;
                    width: 100%;
                    font-size: 1rem;
                ">📡 Capturar mi Posición Exacta (GPS)</button>
                <p id="status_gps" style="color: #a0aec0; font-size: 0.85rem; margin-top: 8px; font-weight: 500;"></p>
                <script>
                function obtenerGPS() {
                    const status = document.getElementById('status_gps');
                    if (navigator.geolocation) {
                        status.innerText = "🔍 Localizando dispositivo con precisión alta...";
                        navigator.geolocation.getCurrentPosition(
                            function(pos) {
                                const lat = pos.coords.latitude;
                                const lon = pos.coords.longitude;
                                status.innerText = "✅ Ubicación obtenida. Recargando mapa...";
                                
                                const topUrl = window.top.location.href.split('?')[0];
                                window.top.location.href = topUrl + '?lat=' + lat + '&lon=' + lon;
                            },
                            function(err) {
                                status.innerText = "⚠️ Error consultando GPS. Revisa los permisos de ubicación de tu navegador.";
                            },
                            { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
                        );
                    } else {
                        status.innerText = "❌ Navegador no compatible con geolocalización.";
                    }
                }
                </script>
            """
            components.html(html_gps_auto, height=100)

            st.markdown("---")
            st.markdown("**2. Modificar información o coordenadas manualmente:**")
            
            with st.form("form_ubicacion_tecnico"):
                nueva_dir = st.text_input("Dirección / Referencia escrita:", value=st.session_state.mi_direccion)
                nuevo_estatus = st.selectbox("Estatus actual:", ["🟢 En Servicio", "🟡 En Trayecto", "🔴 Disponible / Base"], index=0)
                nueva_actividad = st.text_input("Actividad actual:", value=st.session_state.mi_actividad)
                
                c_lat, c_lon = st.columns(2)
                with c_lat:
                    n_lat = st.number_input("Latitud:", value=float(st.session_state.mi_lat), format="%.6f")
                with c_lon:
                    n_lon = st.number_input("Longitud:", value=float(st.session_state.mi_lon), format="%.6f")

                btn_actualizar = st.form_submit_button("💾 Guardar y Centrar Mapa", type="primary")
                if btn_actualizar:
                    st.session_state.mi_direccion = nueva_dir
                    st.session_state.mi_estatus = nuevo_estatus
                    st.session_state.mi_actividad = nueva_actividad
                    st.session_state.mi_lat = n_lat
                    st.session_state.mi_lon = n_lon
                    st.query_params.clear()
                    st.success("✅ Mapa centrado y datos actualizados.")
                    st.rerun()

        with col_mapa:
            st.markdown("### 🗺️ Vista del Mapa al estilo Google Maps")
            
            st.info(f"""
            👤 **Técnico Activo:** {nombre_tecnico}  
            📍 **Dirección:** {st.session_state.mi_direccion}  
            📊 **Estatus:** `{st.session_state.mi_estatus}`  
            🛠️ **Actividad:** {st.session_state.mi_actividad}  
            🌐 **Coordenadas Exactas:** `{st.session_state.mi_lat}, {st.session_state.mi_lon}`
            """)

            tab_gmaps, tab_native = st.tabs(["🗺️ Google Maps Interactivo", "🔴 Vista de Punto Rojo"])

            with tab_gmaps:
                gmaps_iframe = f"""
                    <iframe 
                        width="100%" 
                        height="420" 
                        style="border:0; border-radius:12px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);" 
                        loading="lazy" 
                        allowfullscreen
                        src="https://maps.google.com/maps?q={st.session_state.mi_lat},{st.session_state.mi_lon}&hl=es&z=17&output=embed">
                    </iframe>
                """
                components.html(gmaps_iframe, height=430)

            with tab_native:
                df_mapa = pd.DataFrame([{
                    "lat": float(st.session_state.mi_lat),
                    "lon": float(st.session_state.mi_lon)
                }])
                st.map(df_mapa, zoom=16)

    elif opcion == "💬 Mensajería":
        mostrar_modulo_chat()

def vista_cliente():
    aplicar_estilos_sidebar()
    
    with st.sidebar:
        if os.path.exists("tortuga.png"):
            st.image("tortuga.png", use_container_width=True)
            
        st.markdown(f"""
            <div class="profile-card">
                <div class="profile-name">{st.session_state.user['nombre']}</div>
                <div class="profile-role" style="background-color: #d69e2e;">Cliente VIP</div>
            </div>
            <div class="menu-title">MENÚ PRINCIPAL</div>
        """, unsafe_allow_html=True)
    
        opcion = st.sidebar.radio(
            "", 
            ["🏠 Inicio / Catálogo", "📋 Mis Tratamientos", "💬 Mensajería"],
            label_visibility="collapsed"
        )

        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            st.session_state.user = None
            st.rerun()
    
    if opcion == "🏠 Inicio / Catálogo":
        mostrar_catalogo_plagas_principal()

    elif opcion == "📋 Mis Tratamientos":
        st.subheader("📄 Reportes de Fumigación")
        mis_reportes = obtener_reportes_cliente(st.session_state.user['nombre'])
        for r in mis_reportes:
            st.markdown("---")
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"### Servicio en: **{r[1]}**")
                st.write(f"**Fecha:** {r[6][:10]} | **Plaga:** {r[3]}")
                st.write(f"**Tratamiento:** {r[4]}")
            with col2:
                if r[7] and os.path.exists(r[7]):
                    st.image(r[7], width=200)

    elif opcion == "💬 Mensajería":
        mostrar_modulo_chat()

# =============================================================================
# 7. EJECUCIÓN PRINCIPAL
# =============================================================================
if st.session_state.user is None:
    mostrar_autenticacion()
else:
    st.title("🐢 Gestión de Fumigaciones")
    st.markdown("---")

    if st.session_state.user['rol'] == "Técnico":
        vista_tecnico()
    else:
        vista_cliente()
