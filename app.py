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
# 3. ESTILOS Y ANIMACIONES CSS
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
    
    # ---------------------------------------------------------
    # FICHA: CUCARACHA AMERICANA
    # ---------------------------------------------------------
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
            La **cucaracha americana** (*Periplaneta americana*) es una de las especies de cucarachas más grandes y comunes en zonas urbanas. A pesar de su nombre, proviene de África y llegó al continente a través del comercio marítimo.
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

    # ---------------------------------------------------------
    # FICHA: CUCARACHA ALEMANA
    # ---------------------------------------------------------
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
            La cucaracha alemana (*Blattella germanica*) es una de las especies de cucarachas más pequeñas y, al mismo tiempo, una de las plagas domésticas más importantes del mundo. A pesar de su nombre, no es originaria de Alemania; se cree que proviene del sudeste asiático y se ha distribuido globalmente gracias al comercio y al transporte de mercancías.
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
            * **Marcas distintivas:** Presenta **dos líneas negras paralelas** sobre el pronoto (detrás de la cabeza), una de sus principales características de identificación.
            * **Alas:** Machos y hembras poseen alas, pero rara vez vuelan; normalmente se desplazan corriendo.
            * **Velocidad:** Puede correr aproximadamente 4 a 5 km/h.
            """)

        with tab_hab:
            st.subheader("Hábitat y Refugios")
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                st.markdown("**Prefiere lugares:**")
                st.markdown("* Cálidos.\n* Húmedos.\n* Cercanos a fuentes de alimento.")
            with col_h2:
                st.markdown("**Es común encontrarlas en:**")
                st.markdown("""
                * Cocinas, restaurantes y despensas.
                * Baños.
                * Electrodomésticos (refrigeradores, microondas, cafeteras).
                * Muebles de cocina, hospitales y hoteles.
                """)

        with tab_dieta:
            st.subheader("Alimentación (Omnívora)")
            st.markdown("Es omnívora, con preferencia por alimentos ricos en carbohidratos y grasas.")
            st.markdown("""
            * **Dieta habitual:** Restos de comida, azúcar, pan, cereales, carnes, quesos, grasas, alimento para mascotas, papel, pegamento, jabón y cartón.
            * **Comportamiento extremo:** Cuando el alimento escasea puede practicar canibalismo o alimentarse de excrementos y restos de otras cucarachas.
            """)

        with tab_ciclo:
            st.subheader("Ciclo de Vida y Reproducción")
            st.markdown("""
            La cucaracha alemana pasa por tres etapas:
            1. **Huevo:** La hembra lleva la ooteca adherida al abdomen hasta poco antes de la eclosión. Cada ooteca contiene entre 30 y 40 huevos, una cantidad muy superior a muchas otras especies.
            2. **Ninfa:** Son de color oscuro y carecen de alas. Mudan su exoesqueleto entre 6 y 7 veces antes de alcanzar la etapa adulta.
            3. **Adulto:** Vive aproximadamente 100 a 200 días, dependiendo de la temperatura y disponibilidad de alimento.
            """)
            st.info("⚠️ **Capacidad Reproductiva:** Es considerada una de las cucarachas con mayor capacidad reproductiva. Una sola hembra puede producir entre 4 y 8 ootecas durante su vida (120 a 320 descendientes), lo que explica la rapidez con la que una infestación puede crecer.")

        with tab_salud:
            st.subheader("Importancia Sanitaria")
            st.error("""
            **Riesgo de Salud Pública:** Representa un importante riesgo debido a que puede transportar microorganismos en su cuerpo y patas.
            * Contribuye a la dispersión de *Salmonella*, *Escherichia coli (E. coli)* y *Staphylococcus aureus*.
            * Hongos, virus y parásitos de forma mecánica.
            """)
            st.warning("**Riesgo Alergénico:** Sus excrementos, saliva y fragmentos de su exoesqueleto pueden provocar alergias, dermatitis y crisis asmáticas, especialmente en niños.")

        with tab_curio:
            st.subheader("Curiosidades")
            st.markdown("""
            * Es la especie de cucaracha que más frecuentemente invade viviendas y establecimientos de alimentos.
            * Puede esconderse en grietas de apenas 2 mm de ancho.
            * Es principalmente nocturna.
            * Se reproduce más rápido que la mayoría de las demás especies de cucarachas.
            * Algunas poblaciones han desarrollado resistencia a diversos insecticidas, lo que dificulta su control.
            """)

        with tab_prev:
            st.subheader("Prevención y Control Técnico")
            st.markdown("""
            Para evitar infestaciones se recomienda:
            * Mantener una limpieza constante en cocinas y comedores.
            * Guardar los alimentos en recipientes herméticos.
            * Reparar fugas de agua y vaciar la basura diariamente.
            * Sellar grietas y rendijas, limpiando debajo de muebles y electrodomésticos.
            * Realizar inspecciones periódicas.
            * **Acción recomendada:** En infestaciones importantes, contratar un servicio profesional de control de plagas.
            """)
            
        with tab_diff:
            st.subheader("Diferencia principal con la cucaracha americana")
            st.markdown("""
            | Característica | 🪳 Cucaracha Alemana (*Blattella germanica*) | 🪳 Cucaracha Americana (*Periplaneta americana*) |
            | :--- | :--- | :--- |
            | **Tamaño** | 1.1 – 1.6 cm (Mucho más pequeña) | 3.5 – 5 cm (Más grande) |
            | **Hábitat principal** | Vive principalmente dentro de viviendas y negocios, especialmente en cocinas. | Suele habitar alcantarillas, drenajes y exteriores. |
            | **Reproducción / Control** | Se reproduce mucho más rápido, lo que la convierte en una de las plagas urbanas más difíciles de controlar. | Menor velocidad reproductiva, controlable mediante bloqueos perimetrales. |
            """)

    elif plaga_seleccionada == "Próximamente más plagas...":
        st.info("Estamos actualizando la enciclopedia técnica con nuevas especies (chinches, roedores, mosquitos). ¡Vuelve pronto!")

# =============================================================================
# 5. AUTENTICACIÓN MEJORADA (SPLIT-SCREEN)
# =============================================================================
if "user" not in st.session_state:
    st.session_state.user = None

def mostrar_autenticacion():
    # 1. Inyectar CSS específico para la pantalla de inicio
    st.markdown("""
        <style>
            /* Estilos para los textos de la marca */
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
            /* Separador vertical invisible para alinear */
            .spacer {
                margin-top: 60px;
            }
            @media (max-width: 768px) {
                .spacer { margin-top: 10px; }
                .brand-title { font-size: 2rem; }
            }
        </style>
    """, unsafe_allow_html=True)

    # 2. Layout de dos columnas principales con un pequeño espacio en medio
    col_brand, col_space, col_auth = st.columns([1.2, 0.2, 1])

    # --- COLUMNA IZQUIERDA: BRANDING Y PROPUESTA DE VALOR ---
    with col_brand:
        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
        
        if os.path.exists("tortuga.png"):
            st.image("tortuga.png", width=120)
        
        st.markdown('<div class="brand-title">Gestión Profesional<br>de Fumigaciones</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-subtitle">Plataforma integral para el control de plagas, gestión de clientes y seguimiento en tiempo real.</div>', unsafe_allow_html=True)
        
        # Puntos de confianza (Trust badges) con diseño elegante y responsivo
        st.markdown("""
        <div style="background-color: #1f2937; padding: 20px; border-radius: 10px; border-left: 5px solid #10b981; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="color: #10b981; margin-top: 0; font-family: sans-serif;">Características del Sistema:</h4>
            <p style="margin-bottom: 8px; color: #f3f4f6; font-family: sans-serif;">🛡️ <b>Seguridad:</b> Datos encriptados y respaldados.</p>
            <p style="margin-bottom: 8px; color: #f3f4f6; font-family: sans-serif;">📍 <b>Geolocalización:</b> Control de servicios en tiempo real.</p>
            <p style="margin-bottom: 0; color: #f3f4f6; font-family: sans-serif;">📊 <b>Trazabilidad:</b> Historial y reportes fotográficos.</p>
        </div>
        """, unsafe_allow_html=True)

    # --- COLUMNA DERECHA: FORMULARIOS DE ACCESO ---
    with col_auth:
        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
        
        # Contenedor visual para agrupar el formulario
        with st.container():
            tab_login, tab_registro = st.tabs(["🔐 Iniciar Sesión", "📝 Crear Cuenta Nueva"])
            
            # --- PESTAÑA: LOGIN ---
            with tab_login:
                st.markdown("### ¡Bienvenido de nuevo!")
                st.caption("Ingresa tus credenciales para acceder al panel de control.")
                
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

            # --- PESTAÑA: REGISTRO ---
            with tab_registro:
                st.markdown("### Solicitud de Acceso")
                st.caption("Registra tus datos para habilitar tu cuenta en la plataforma.")
                
                with st.form("form_registro", clear_on_submit=True):
                    nuevo_nombre = st.text_input("Nombre Completo / Razón Social", placeholder="Ej. Juan Pérez / Empresa S.A.")
                    nuevo_correo = st.text_input("Correo Electrónico", placeholder="contacto@empresa.com")
                    
                    col_t, col_r = st.columns(2)
                    with col_t:
                        nuevo_telefono = st.text_input("Teléfono Móvil", placeholder="10 dígitos")
                    with col_r:
                        nuevo_rol = st.selectbox("Tipo de Usuario", ["Cliente", "Técnico"])
                    
                    pass1 = st.text_input("Contraseña", type="password", placeholder="Crea una contraseña segura")
                    pass2 = st.text_input("Confirmar Contraseña", type="password", placeholder="Repite tu contraseña")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    reg_submit = st.form_submit_button("Registrar Cuenta", use_container_width=True)
                    
                    if reg_submit:
                        if not nuevo_nombre or not nuevo_correo or not pass1:
                            st.warning("⚠️ Por favor, llena todos los campos obligatorios.")
                        elif pass1 != pass2:
                            st.error("⚠️ Las contraseñas no coinciden.")
                        else:
                            if agregar_usuario(nuevo_nombre, nuevo_correo, pass1, nuevo_rol, nuevo_telefono):
                                st.success("✅ Cuenta creada exitosamente. Ahora puedes iniciar sesión.")
                            else:
                                st.error("❌ El correo ingresado ya se encuentra registrado.")

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
                    background-color: #10b981;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    cursor: pointer;
                    width: 100%;
                    font-size: 1rem;
                ">📡 Capturar mi Posición Exacta (GPS)</button>
                <p id="status_gps" style="color: #9ca3af; font-size: 0.85rem; margin-top: 8px; font-weight: 500;"></p>
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
        st.subheader("📋 Mis Tratamientos y Servicios Aplicados")
        reportes = obtener_reportes_cliente(st.session_state.user['nombre'])
        
        if reportes:
            for r in reportes:
                with st.expander(f"📌 Servicio #{r[0]} - Fecha: {r[6][:10]}"):
                    st.write(f"**Técnico a cargo:** {r[2]}")
                    st.write(f"**Tipo de Plaga:** {r[3]}")
                    st.write(f"**Tratamiento:** {r[4]}")
                    st.write(f"**Estatus:** `{r[5]}`")
                    if r[7] and os.path.exists(r[7]):
                        st.image(r[7], caption="Evidencia del servicio", width=300)
        else:
            st.info("No se encontraron registros de servicios previos vinculados a tu cuenta.")

    elif opcion == "💬 Mensajería":
        mostrar_modulo_chat()

# =============================================================================
# 7. CONTROLADOR PRINCIPAL DE LA APLICACIÓN
# =============================================================================
def main():
    if st.session_state.user is None:
        mostrar_autenticacion()
    else:
        rol = st.session_state.user.get('rol', 'Cliente')
        if rol == "Técnico":
            vista_tecnico()
        else:
            vista_cliente()

if __name__ == "__main__":
    main()
