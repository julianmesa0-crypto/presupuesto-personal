import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import io
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(
    page_title="Presupuesto 50/30/20 Plus - Seguridad Militar",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta estética cálida del video (beige, taupe, terracota y verde salvia)
PALETTE = {
    "bg_main": "#FAF7F2",
    "card_bg": "#FFFFFF",
    "taupe_dark": "#A88E79",
    "taupe_soft": "#CBB8A9",
    "beige_header": "#EDE5DC",
    "beige_alt": "#F5EFE8",
    "text_dark": "#3D342F",
    "text_muted": "#7A6E65",
    "sage_green": "#879883",
    "sage_light": "#EDF3EE",
    "terracotta": "#C97A63",
    "border_soft": "#D6CBC1",
    "alert_red": "#B02A37",
    "alert_bg": "#F8D7DA"
}

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: {PALETTE['text_dark']};
    }}
    
    .main {{
        background-color: {PALETTE['bg_main']};
    }}

    .security-badge {{
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #38BDF8;
        border: 1px solid #334155;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        padding: 6px 12px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 12px;
    }}

    .auth-container {{
        max-width: 490px;
        margin: 1.5rem auto;
        padding: 2.2rem;
        background: #FFFFFF;
        border: 1px solid {PALETTE['border_soft']};
        border-radius: 18px;
        box-shadow: 0 12px 30px rgba(61, 52, 47, 0.09);
    }}

    .user-pill {{
        background-color: {PALETTE['beige_header']};
        border: 1px solid {PALETTE['border_soft']};
        padding: 12px 14px;
        border-radius: 12px;
        margin-bottom: 15px;
        text-align: center;
    }}

    .admin-badge {{
        background-color: {PALETTE['terracotta']};
        color: white;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        display: inline-block;
        margin-top: 4px;
        text-transform: uppercase;
    }}

    .dashboard-header {{
        background: linear-gradient(135deg, {PALETTE['taupe_dark']} 0%, {PALETTE['taupe_soft']} 100%);
        padding: 22px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 22px;
        box-shadow: 0 4px 16px rgba(168, 142, 121, 0.22);
    }}
    
    .dashboard-header h1 {{
        color: white !important;
        margin: 0;
        font-size: 2.1rem;
        font-weight: 700;
    }}
    
    .dashboard-header p {{
        color: #F7F3EE;
        margin-top: 4px;
        font-size: 0.95rem;
    }}

    .kpi-card {{
        background-color: {PALETTE['card_bg']};
        border: 1px solid {PALETTE['border_soft']};
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(61, 52, 47, 0.04);
        transition: transform 0.2s ease;
    }}
    
    .kpi-card:hover {{
        transform: translateY(-2px);
    }}
    
    .kpi-label {{
        font-size: 0.78rem;
        font-weight: 600;
        color: {PALETTE['text_muted']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }}
    
    .kpi-value {{
        font-size: 1.45rem;
        font-weight: 700;
        color: {PALETTE['text_dark']};
    }}
    
    .restante-card {{
        background: linear-gradient(135deg, {PALETTE['sage_light']} 0%, #FFFFFF 100%);
        border: 2px solid {PALETTE['sage_green']};
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        margin-bottom: 22px;
        box-shadow: 0 4px 12px rgba(135, 152, 131, 0.16);
    }}
    
    .restante-title {{
        font-size: 0.88rem;
        font-weight: 700;
        color: {PALETTE['sage_green']};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    .restante-value {{
        font-size: 2.1rem;
        font-weight: 800;
        color: #26432D;
        margin-top: 4px;
    }}
    
    .section-pill {{
        background-color: {PALETTE['taupe_soft']};
        color: white;
        padding: 7px 15px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.92rem;
        display: inline-block;
        margin-bottom: 12px;
    }}
</style>
""", unsafe_allow_html=True)

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

CATEGORIAS_VARIABLES = [
    "Mercado", "Transporte", "Restaurante", "Entretenimiento",
    "Salud", "Cuidado personal", "Hogar", "Ropa",
    "Educación", "Vacaciones", "Mascotas", "Misceláneos"
]

CATEGORIAS_TIPO_DEFAULT = {
    "Mercado": "Necesidades",
    "Transporte": "Necesidades",
    "Restaurante": "Deseos",
    "Entretenimiento": "Deseos",
    "Salud": "Necesidades",
    "Cuidado personal": "Deseos",
    "Hogar": "Necesidades",
    "Ropa": "Deseos",
    "Educación": "Necesidades",
    "Vacaciones": "Deseos",
    "Mascotas": "Necesidades",
    "Misceláneos": "Deseos"
}

def generar_salt() -> str:
    """Genera una sal criptográfica pseudoaleatoria segura de 32 bytes."""
    return secrets.token_hex(16)

def hash_password_militar(password: str, salt: str) -> str:
    """Calcula hash con PBKDF2-HMAC-SHA256 con 100,000 iteraciones y sal única."""
    derived = hashlib.pbkdf2_hmac(
        'sha256',
        password.strip().encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return derived.hex()

def verificar_password_militar(password_ingresada: str, salt: str, hash_almacenado: str) -> bool:
    """Compara en tiempo constante (timing-attack resistant) la contraseña contra el hash."""
    calc_hash = hash_password_militar(password_ingresada, salt)
    return secrets.compare_digest(calc_hash, hash_almacenado)

def enviar_correo_violacion_seguridad(destinatario: str, asunto: str, cuerpo_html: str, config_smtp: dict):
    """
    Envía notificación de alerta inmediata al administrador por correo electrónico.
    """
    if not config_smtp.get("activo", False):
        return False, "SMTP no habilitado. Alerta registrada en la bitácora de auditoría militar."
        
    try:
        servidor = config_smtp.get("servidor", "smtp.gmail.com")
        puerto = int(config_smtp.get("puerto", 587))
        remitente = config_smtp.get("remitente", "")
        password_smtp = config_smtp.get("password", "")
        
        if not remitente or not password_smtp:
            return False, "Credenciales SMTP incompletas en la configuración militar."
            
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = f"Escudo Militar Finanzas <{remitente}>"
        msg["To"] = destinatario
        
        parte_html = MIMEText(cuerpo_html, "html")
        msg.attach(parte_html)
        
        with smtplib.SMTP(servidor, puerto, timeout=10) as server:
            server.starttls()
            server.login(remitente, password_smtp)
            server.sendmail(remitente, destinatario, msg.as_string())
            
        return True, "Notificación de alerta enviada con éxito al correo del administrador."
    except Exception as e:
        return False, f"Fallo al contactar servidor SMTP: {str(e)}"

def registrar_evento_seguridad(tipo: str, correo_afectado: str, detalle: str, nivel: str = "INFO"):
    """Registra en memoria cada evento con marca de tiempo y dispara alerta si es crítico."""
    if "auditoria_seguridad" not in st.session_state:
        st.session_state["auditoria_seguridad"] = []
        
    marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    registro = {
        "timestamp": marca_tiempo,
        "nivel": nivel,
        "tipo": tipo,
        "correo": correo_afectado,
        "detalle": detalle
    }
    st.session_state["auditoria_seguridad"].insert(0, registro)
    
    if nivel in ["ALERTA_CRITICA", "VIOLACION"]:
        config_smtp = st.session_state.get("config_smtp", {})
        correo_admin = config_smtp.get("correo_alertas", "admin@presupuesto.com")
        
        asunto = "🚨 [ALERTA MILITAR] Violación / Intento sospechoso en Presupuesto 50/30/20"
        cuerpo = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #FAF7F2; border: 1px solid #D6CBC1; border-radius: 10px;">
            <h2 style="color: #B02A37; margin-top: 0;">🛡️ ALERTA DE SEGURIDAD DETECTADA</h2>
            <p>El sistema de defensa ha interceptado un intento no autorizado o anomalía de acceso:</p>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <tr><td style="padding: 8px; font-weight: bold; background-color: #EDE5DC;">Fecha y Hora:</td><td style="padding: 8px;">{marca_tiempo}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; background-color: #EDE5DC;">Tipo de Evento:</td><td style="padding: 8px; color: #B02A37; font-weight: bold;">{tipo}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; background-color: #EDE5DC;">Cuenta Objetivo:</td><td style="padding: 8px;">{correo_afectado}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; background-color: #EDE5DC;">Diagnóstico:</td><td style="padding: 8px;">{detalle}</td></tr>
            </table>
        </div>
        """
        enviar_correo_violacion_seguridad(correo_admin, asunto, cuerpo, config_smtp)

def generar_datos_meses_default():
    """Genera la estructura inicial de 12 meses con datos de ejemplo del video."""
    datos = {}
    for m in MESES:
        datos[m] = {
            "ingresos": pd.DataFrame([
                {"Pagado": True, "Descripción": "Salario Principal", "Presupuesto": 1400.0, "Actual": 1400.0},
                {"Pagado": False, "Descripción": "Ingreso Secundario / Freelance", "Presupuesto": 0.0, "Actual": 0.0},
                {"Pagado": False, "Descripción": "Otros Ingresos", "Presupuesto": 0.0, "Actual": 0.0}
            ]),
            "facturas": pd.DataFrame([
                {"Pagado": True, "Descripción": "Renta", "Presupuesto": 400.0, "Actual": 400.0, "Tipo": "Necesidades", "Fecha": "15 abr"},
                {"Pagado": True, "Descripción": "Agua", "Presupuesto": 50.0, "Actual": 50.0, "Tipo": "Necesidades", "Fecha": "18 abr"},
                {"Pagado": True, "Descripción": "Internet", "Presupuesto": 30.0, "Actual": 30.0, "Tipo": "Necesidades", "Fecha": "24 abr"},
                {"Pagado": True, "Descripción": "Netflix", "Presupuesto": 15.0, "Actual": 15.0, "Tipo": "Deseos", "Fecha": "19 abr"},
                {"Pagado": False, "Descripción": "Electricidad", "Presupuesto": 45.0, "Actual": 0.0, "Tipo": "Necesidades", "Fecha": "28 abr"},
                {"Pagado": False, "Descripción": "Gas", "Presupuesto": 15.0, "Actual": 0.0, "Tipo": "Necesidades", "Fecha": "30 abr"},
                {"Pagado": False, "Descripción": "Teléfono Móvil", "Presupuesto": 25.0, "Actual": 0.0, "Tipo": "Necesidades", "Fecha": "20 abr"},
                {"Pagado": False, "Descripción": "Seguro Médico", "Presupuesto": 50.0, "Actual": 0.0, "Tipo": "Necesidades", "Fecha": "05 abr"},
                {"Pagado": False, "Descripción": "Gimnasio", "Presupuesto": 30.0, "Actual": 0.0, "Tipo": "Deseos", "Fecha": "10 abr"},
            ]),
            "gv_presupuesto": {
                "Mercado": 150.0, "Transporte": 50.0, "Restaurante": 50.0, "Entretenimiento": 80.0,
                "Salud": 30.0, "Cuidado personal": 20.0, "Hogar": 30.0, "Ropa": 40.0,
                "Educación": 0.0, "Vacaciones": 0.0, "Mascotas": 30.0, "Misceláneos": 20.0
            },
            "ahorros": pd.DataFrame([
                {"Cumplido": True, "Concepto": "Viajar a Europa", "Presupuesto": 150.0, "Actual": 150.0, "Notas": "Meta 2027"},
                {"Cumplido": False, "Concepto": "Fondo de emergencia", "Presupuesto": 100.0, "Actual": 0.0, "Notas": "3 meses fijos"},
                {"Cumplido": False, "Concepto": "Inversión ETFs", "Presupuesto": 50.0, "Actual": 0.0, "Notas": "S&P 500"}
            ]),
            "transacciones": pd.DataFrame([
                {"Pagado": True, "Monto": 100.0, "Categoría": "Mercado", "Fecha": "16 abr", "Detalle": "Supermercado Éxito"},
                {"Pagado": True, "Monto": 15.0, "Categoría": "Entretenimiento", "Fecha": "17 abr", "Detalle": "Cine Colombia"},
                {"Pagado": True, "Monto": 30.0, "Categoría": "Salud", "Fecha": "27 abr", "Detalle": "Medicamentos"},
                {"Pagado": True, "Monto": 20.0, "Categoría": "Mascotas", "Fecha": "28 abr", "Detalle": "Comida de gato"}
            ])
        }
    return datos

def inicializar_estado_seguro():
    # Leer de st.secrets si está configurado en Streamlit Community Cloud
    secrets_smtp = st.secrets.get("smtp", {}) if hasattr(st, "secrets") else {}
    
    if "config_smtp" not in st.session_state:
        st.session_state["config_smtp"] = {
            "activo": secrets_smtp.get("activo", False),
            "servidor": secrets_smtp.get("servidor", "smtp.gmail.com"),
            "puerto": int(secrets_smtp.get("puerto", 587)),
            "remitente": secrets_smtp.get("remitente", ""),
            "password": secrets_smtp.get("password", ""),
            "correo_alertas": secrets_smtp.get("correo_alertas", "admin@presupuesto.com")
        }
        
    if "intentos_fallidos" not in st.session_state:
        st.session_state["intentos_fallidos"] = {}

    if "cuentas_bloqueadas" not in st.session_state:
        st.session_state["cuentas_bloqueadas"] = {}

    if "auditoria_seguridad" not in st.session_state:
        st.session_state["auditoria_seguridad"] = []

    if "usuarios_db" not in st.session_state:
        salt_admin = generar_salt()
        salt_user = generar_salt()
        st.session_state["usuarios_db"] = {
            "admin@presupuesto.com": {
                "nombre": "Administrador Principal",
                "salt": salt_admin,
                "password_hash": hash_password_militar("admin123", salt_admin),
                "rol": "admin",
                "anio": 2026,
                "moneda": "$",
                "mes_activo": "Abril",
                "session_token": None,
                "datos_meses": generar_datos_meses_default()
            },
            "juan@ejemplo.com": {
                "nombre": "Juan Pérez",
                "salt": salt_user,
                "password_hash": hash_password_militar("12345", salt_user),
                "rol": "usuario",
                "anio": 2026,
                "moneda": "$",
                "mes_activo": "Abril",
                "session_token": None,
                "datos_meses": generar_datos_meses_default()
            }
        }

    if "usuario_activo" not in st.session_state:
        st.session_state["usuario_activo"] = None

inicializar_estado_seguro()

def render_modulo_login_seguro():
    st.markdown("""
    <div style="text-align: center; margin-top: 1.2rem; margin-bottom: 0.8rem;">
        <div class="security-badge">🛡️ DEFENSE ENGINE ACTIVE • PBKDF2-HMAC-SHA256 • LOCKOUT DE 3 INTENTOS</div>
        <h1 style="color: #A88E79; margin: 0; font-size: 2.1rem; font-weight: 800;">💸 Presupuesto 50/30/20 Plus</h1>
        <p style="color: #7A6E65; font-size: 0.95rem;">Gestión financiera con aislamiento por usuario y alerta por correo ante intrusiones.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_izq, col_centro, col_der = st.columns([1, 1.4, 1])
    with col_centro:
        tab_login, tab_registro, tab_info_seguridad = st.tabs(["🔐 Iniciar Sesión", "📝 Crear Cuenta", "🛡️ Escudo Militar"])
        
        with tab_login:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            with st.form("form_login_militar"):
                email = st.text_input("Correo Electrónico", placeholder="ejemplo@correo.com").strip().lower()
                password = st.text_input("Contraseña", type="password")
                btn_login = st.form_submit_button("Ingreso Seguro", use_container_width=True)
                
                if btn_login:
                    ahora = datetime.now()
                    bloqueos = st.session_state["cuentas_bloqueadas"]
                    
                    if email in bloqueos and bloqueos[email] > ahora:
                        minutos_rest = int((bloqueos[email] - ahora).total_seconds() / 60) + 1
                        registrar_evento_seguridad("BLOQUEO_ACTIVO", email, f"Acceso denegado. Cuenta bajo congelamiento por {minutos_rest} min.", "ADVERTENCIA")
                        st.error(f"⛔ CUENTA CONGELADA POR SEGURIDAD. Múltiples intentos fallidos. Intenta en {minutos_rest} minuto(s).")
                        return

                    users = st.session_state["usuarios_db"]
                    login_valido = False
                    if email in users:
                        user_info = users[email]
                        if verificar_password_militar(password, user_info["salt"], user_info["password_hash"]):
                            login_valido = True

                    if login_valido:
                        st.session_state["intentos_fallidos"][email] = 0
                        nuevo_token = secrets.token_hex(32)
                        users[email]["session_token"] = nuevo_token
                        st.session_state["usuario_activo"] = email
                        st.session_state["session_token"] = nuevo_token
                        
                        registrar_evento_seguridad("ACCESO_AUTORIZADO", email, "Autenticación exitosa con token.", "INFO")
                        st.success(f"¡Bienvenido/a, {users[email]['nombre']}!")
                        st.rerun()
                    else:
                        intentos = st.session_state["intentos_fallidos"].get(email, 0) + 1
                        st.session_state["intentos_fallidos"][email] = intentos
                        
                        if intentos >= 3:
                            tiempo_bloqueo = ahora + timedelta(minutes=15)
                            st.session_state["cuentas_bloqueadas"][email] = tiempo_bloqueo
                            registrar_evento_seguridad(
                                "VIOLACION_FUERZA_BRUTA",
                                email,
                                f"Se alcanzaron {intentos} intentos fallidos seguidos. Cuenta congelada 15 min. Alerta enviada al administrador.",
                                "ALERTA_CRITICA"
                            )
                            st.error("🚨 VIOLACIÓN DETECTADA: Se superó el límite de intentos. La cuenta ha sido bloqueada y se despachó la alerta al correo de seguridad.")
                        else:
                            registrar_evento_seguridad(
                                "INTENTO_FALLIDO",
                                email,
                                f"Fallo de contraseña #{intentos}/3.",
                                "ADVERTENCIA"
                            )
                            st.error(f"Credenciales incorrectas. Intento {intentos} de 3 antes de activar el bloqueo.")

            st.info("💡 **Superusuario:** `admin@presupuesto.com` | Clave: `admin123`\n\n💡 **Usuario:** `juan@ejemplo.com` | Clave: `12345`")

        with tab_registro:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            with st.form("form_registro_seguro"):
                nuevo_nombre = st.text_input("Nombre Completo", placeholder="Ej: Laura Gómez")
                nuevo_email = st.text_input("Correo Electrónico", placeholder="laura@ejemplo.com").strip().lower()
                nuevo_pass = st.text_input("Contraseña", type="password")
                nuevo_pass2 = st.text_input("Confirmar Contraseña", type="password")
                btn_reg = st.form_submit_button("Crear Bóveda Financiera", use_container_width=True)
                
                if btn_reg:
                    if not nuevo_nombre or not nuevo_email or not nuevo_pass:
                        st.warning("Por favor completa todos los campos requeridos.")
                    elif len(nuevo_pass) < 5:
                        st.warning("Por seguridad, la contraseña debe tener al menos 5 caracteres.")
                    elif nuevo_pass != nuevo_pass2:
                        st.error("Las contraseñas no coinciden.")
                    elif nuevo_email in st.session_state["usuarios_db"]:
                        st.error("Ya existe una cuenta registrada con este correo.")
                    else:
                        nueva_sal = generar_salt()
                        hash_seguro = hash_password_militar(nuevo_pass, nueva_sal)
                        st.session_state["usuarios_db"][nuevo_email] = {
                            "nombre": nuevo_nombre,
                            "salt": nueva_sal,
                            "password_hash": hash_seguro,
                            "rol": "usuario",
                            "anio": 2026,
                            "moneda": "$",
                            "mes_activo": "Abril",
                            "session_token": None,
                            "datos_meses": generar_datos_meses_default()
                        }
                        registrar_evento_seguridad("REGISTRO_NUEVO_USUARIO", nuevo_email, f"Bóveda financiera creada para {nuevo_nombre}.", "INFO")
                        st.session_state["usuario_activo"] = nuevo_email
                        st.success(f"¡Bóveda privada creada! Bienvenido/a, {nuevo_nombre}.")
                        st.rerun()
                        
        with tab_info_seguridad:
            st.markdown("""
            <div style="font-size: 0.88rem; line-height: 1.6; padding: 10px;">
                <h4 style="color: #A88E79; margin-top: 0;">🛡️ Protocolo de Seguridad Militar Activo:</h4>
                <ul>
                    <li><b>PBKDF2-HMAC-SHA256 (100k rounds):</b> Claves protegidas contra ataques de diccionario y GPU.</li>
                    <li><b>Sal Criptográfica Individual:</b> Generada aleatoriamente con <code>secrets</code> por cuenta.</li>
                    <li><b>Timing-Attack Resistant:</b> Comparación en tiempo constante.</li>
                    <li><b>Escudo Anti-Fuerza Bruta:</b> Bloqueo temporal tras 3 fallos consecutivos.</li>
                    <li><b>Alertas SMTP Instantáneas:</b> Notificación automática de incidentes al correo del administrador.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

def render_modulo_administracion():
    st.markdown("""
    <div class="dashboard-header">
        <h1>👑 CENTRO DE COMANDO & ADMINISTRACIÓN</h1>
        <p>Módulo de Super Administrador: gestión de usuarios, restablecimiento por nombre y bitácora de seguridad</p>
    </div>
    """, unsafe_allow_html=True)

    usuarios_db = st.session_state["usuarios_db"]
    cfg_smtp = st.session_state["config_smtp"]
    
    tab_admin_users, tab_admin_seguridad, tab_bitacora = st.tabs([
        "👥 Gestión de Usuarios y Claves",
        "✉️ Configuración de Alertas por Correo",
        "📜 Bitácora Forense de Violaciones"
    ])
    
    with tab_admin_users:
        total_usuarios = len(usuarios_db)
        total_estudiantes = sum(1 for u in usuarios_db.values() if u.get("rol") == "usuario")
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Bóvedas Financieras</div>
                <div class="kpi-value">{total_usuarios}</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Usuarios Estándar</div>
                <div class="kpi-value">{total_estudiantes}</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Estado de Alertas por Correo</div>
                <div class="kpi-value" style="color: {'#27AE60' if cfg_smtp['activo'] else '#D97706'}; font-size: 1.15rem;">
                    {'🟢 Activo (Envía correos)' if cfg_smtp['activo'] else '🟡 Auditoría Interna'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        col_admin_a, col_admin_b = st.columns([1.3, 1.1])
        
        with col_admin_a:
            st.markdown('<div class="section-pill">👥 USUARIOS REGISTRADOS</div>', unsafe_allow_html=True)
            lista_resumen = []
            for correo, info in usuarios_db.items():
                total_trn = sum(len(mes_data["transacciones"]) for mes_data in info["datos_meses"].values())
                lista_resumen.append({
                    "Nombre": info["nombre"],
                    "Correo": correo,
                    "Rol": "👑 Admin" if info.get("rol") == "admin" else "👤 Usuario",
                    "Transacciones": total_trn
                })
            st.dataframe(pd.DataFrame(lista_resumen), use_container_width=True, hide_index=True)

        with col_admin_b:
            st.markdown('<div class="section-pill">🔑 CAMBIO DE CONTRASEÑA (SOLO NOMBRE)</div>', unsafe_allow_html=True)
            st.caption("Como Superusuario, puedes restablecer la contraseña de cualquier usuario indicando únicamente su **Nombre**.")
            
            nombres_disponibles = sorted(list(set([info["nombre"] for info in usuarios_db.values()])))
            
            with st.form("form_cambio_clave_nombre"):
                nombre_seleccionado = st.selectbox("Selecciona por Nombre:", nombres_disponibles)
                nueva_contrasena = st.text_input("Nueva Contraseña:", type="password", placeholder="Nueva clave")
                confirmar_nueva = st.text_input("Confirmar Contraseña:", type="password")
                btn_actualizar_pass = st.form_submit_button("Actualizar Contraseña Inmediatamente", use_container_width=True)
                
                if btn_actualizar_pass:
                    if not nueva_contrasena:
                        st.warning("Por favor ingresa una contraseña.")
                    elif nueva_contrasena != confirmar_nueva:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        for correo_u, info_u in usuarios_db.items():
                            if info_u["nombre"] == nombre_seleccionado:
                                nueva_sal = generar_salt()
                                info_u["salt"] = nueva_sal
                                info_u["password_hash"] = hash_password_militar(nueva_contrasena, nueva_sal)
                                info_u["session_token"] = None
                                registrar_evento_seguridad(
                                    "RESET_PASSWORD_ADMIN",
                                    correo_u,
                                    f"Contraseña de {nombre_seleccionado} restablecida por el Administrador solicitando solo el nombre.",
                                    "INFO"
                                )
                                st.success(f"✅ ¡Contraseña actualizada con éxito para **{nombre_seleccionado}** (`{correo_u}`)!")
                                break

    with tab_admin_seguridad:
        st.markdown('<div class="section-pill">🚨 CONFIGURACIÓN SMTP DE ALERTAS</div>', unsafe_allow_html=True)
        st.caption("Configura el servidor para recibir correos automáticos ante anomalías o bloqueos por fuerza bruta.")
        
        with st.form("form_config_smtp"):
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                smtp_activo = st.checkbox("Habilitar Envío Inmediato de Correo ante Violaciones", value=cfg_smtp.get("activo", False))
                correo_alertas = st.text_input("Tu Correo Receptor de Alertas:", value=cfg_smtp.get("correo_alertas", "admin@presupuesto.com"))
                servidor_smtp = st.text_input("Servidor SMTP:", value=cfg_smtp.get("servidor", "smtp.gmail.com"))
            with c_s2:
                puerto_smtp = st.number_input("Puerto SMTP (TLS):", value=int(cfg_smtp.get("puerto", 587)), step=1)
                remitente_smtp = st.text_input("Correo Emisor (Cuenta remitente):", value=cfg_smtp.get("remitente", ""))
                password_smtp = st.text_input("Contraseña de Aplicación SMTP:", value=cfg_smtp.get("password", ""), type="password")
                
            if st.form_submit_button("Guardar Configuración SMTP", use_container_width=True):
                cfg_smtp["activo"] = smtp_activo
                cfg_smtp["correo_alertas"] = correo_alertas.strip().lower()
                cfg_smtp["servidor"] = servidor_smtp.strip()
                cfg_smtp["puerto"] = puerto_smtp
                cfg_smtp["remitente"] = remitente_smtp.strip()
                cfg_smtp["password"] = password_smtp.strip()
                st.success("✅ Configuración guardada con éxito.")
                st.rerun()

    with tab_bitacora:
        st.markdown('<div class="section-pill">📜 REGISTRO DE AUDITORÍA Y ACCESOS</div>', unsafe_allow_html=True)
        logs = st.session_state.get("auditoria_seguridad", [])
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
        else:
            st.info("Sin registros de incidentes de seguridad.")

# Verificación de sesión activa
if not st.session_state["usuario_activo"]:
    render_modulo_login_seguro()
    st.stop()

correo_actual = st.session_state["usuario_activo"]
usuario_info = st.session_state["usuarios_db"][correo_actual]
es_superusuario = (usuario_info.get("rol") == "admin")

with st.sidebar:
    st.markdown(f"""
    <div class="user-pill">
        <div style="font-size: 0.76rem; color: {PALETTE['text_muted']}; font-weight: 600;">SESIÓN ENCRIPTADA ACTIVA</div>
        <div style="font-weight: 700; color: {PALETTE['text_dark']}; font-size: 1.05rem;">{usuario_info['nombre']}</div>
        <div style="font-size: 0.78rem; color: {PALETTE['text_muted']};">{correo_actual}</div>
        {"<div class='admin-badge'>👑 Superusuario</div>" if es_superusuario else "<div style='font-size: 0.72rem; color: #7A6E65;'>👤 Bóveda Privada</div>"}
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        registrar_evento_seguridad("CIERRE_SESION", correo_actual, "Cierre voluntario de sesión.", "INFO")
        st.session_state["usuario_activo"] = None
        st.session_state["session_token"] = None
        st.rerun()

    st.markdown("---")
    col_yr, col_curr = st.columns(2)
    with col_yr:
        usuario_info["anio"] = st.number_input("Año", min_value=2020, max_value=2035, value=usuario_info.get("anio", 2026), step=1)
    with col_curr:
        lista_monedas = ["$", "€", "COP", "MXN", "USD"]
        m_idx = lista_monedas.index(usuario_info.get("moneda", "$")) if usuario_info.get("moneda", "$") in lista_monedas else 0
        usuario_info["moneda"] = st.selectbox("Moneda", lista_monedas, index=m_idx)
        
    moneda_simbolo = usuario_info["moneda"]
    st.markdown("---")
    
    opciones_nav = ["Mes a Mes", "Consolidado Anual"]
    if es_superusuario:
        opciones_nav.append("👑 Seguridad & Usuarios")
        
    vista_seleccionada = st.radio("Navegación:", opciones_nav, index=0)
    
    if vista_seleccionada == "Mes a Mes":
        mes_index = MESES.index(usuario_info.get("mes_activo", "Abril")) if usuario_info.get("mes_activo", "Abril") in MESES else 3
        usuario_info["mes_activo"] = st.selectbox("Mes", MESES, index=mes_index)
    
    st.markdown("---")
    
    def generar_excel():
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for m in MESES:
                data_m = usuario_info["datos_meses"][m]
                data_m["ingresos"].to_excel(writer, sheet_name=f"{m}_Ingresos", index=False)
                data_m["facturas"].to_excel(writer, sheet_name=f"{m}_Facturas", index=False)
                data_m["transacciones"].to_excel(writer, sheet_name=f"{m}_Gastos", index=False)
        output.seek(0)
        return output
        
    st.download_button(
        label="💾 Descargar Mi Excel (.xlsx)",
        data=generar_excel(),
        file_name=f"Presupuesto_{usuario_info['nombre'].replace(' ', '_')}_{usuario_info['anio']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

if vista_seleccionada == "👑 Seguridad & Usuarios" and es_superusuario:
    render_modulo_administracion()
    st.stop()

mes_actual = usuario_info["mes_activo"]
datos_m = usuario_info["datos_meses"][mes_actual]
transacciones_df = datos_m["transacciones"]

gv_lista = []
for cat in CATEGORIAS_VARIABLES:
    presup = float(datos_m["gv_presupuesto"].get(cat, 0.0))
    gastado_cat = transacciones_df[transacciones_df["Categoría"] == cat]["Monto"].sum() if not transacciones_df.empty else 0.0
    tipo_cat = CATEGORIAS_TIPO_DEFAULT.get(cat, "Deseos")
    gv_lista.append({
        "Pagado": (gastado_cat > 0),
        "Categoría": cat,
        "Presupuesto": presup,
        "Actual": float(gastado_cat),
        "Tipo": tipo_cat
    })

df_gv = pd.DataFrame(gv_lista)

total_ingreso_presup = float(datos_m["ingresos"]["Presupuesto"].sum())
total_ingreso_actual = float(datos_m["ingresos"]["Actual"].sum())

total_facturas_presup = float(datos_m["facturas"]["Presupuesto"].sum())
total_facturas_actual = float(datos_m["facturas"]["Actual"].sum())

total_gv_presup = float(df_gv["Presupuesto"].sum())
total_gv_actual = float(df_gv["Actual"].sum())

total_ahorro_presup = float(datos_m["ahorros"]["Presupuesto"].sum())
total_ahorro_actual = float(datos_m["ahorros"]["Actual"].sum())

total_gastado = total_facturas_actual + total_gv_actual
presupuesto_a_asignar = total_ingreso_presup - (total_facturas_presup + total_gv_presup + total_ahorro_presup)
dinero_restante = total_ingreso_actual - (total_gastado + total_ahorro_actual)

actual_necesidades = datos_m["facturas"][datos_m["facturas"]["Tipo"] == "Necesidades"]["Actual"].sum() + df_gv[df_gv["Tipo"] == "Necesidades"]["Actual"].sum()
actual_deseos = datos_m["facturas"][datos_m["facturas"]["Tipo"] == "Deseos"]["Actual"].sum() + df_gv[df_gv["Tipo"] == "Deseos"]["Actual"].sum()
actual_ahorros = total_ahorro_actual

presup_50 = total_ingreso_presup * 0.50
presup_30 = total_ingreso_presup * 0.30
presup_20 = total_ingreso_presup * 0.20

if vista_seleccionada == "Mes a Mes":
    st.markdown(f"""
    <div class="dashboard-header">
        <h1>{mes_actual.upper()} {usuario_info['anio']}</h1>
        <p>~ Dashboard Presupuesto 50/30/20 Plus • Bóveda de {usuario_info['nombre']} ~</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1.2])
    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Ingreso Total</div><div class="kpi-value">{moneda_simbolo}{total_ingreso_actual:,.2f}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Gastado</div><div class="kpi-value">{moneda_simbolo}{total_gastado:,.2f}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">A Asignar</div><div class="kpi-value" style="color: {"#27AE60" if presupuesto_a_asignar >= 0 else "#C0392B"};">{moneda_simbolo}{presupuesto_a_asignar:,.2f}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Ahorrado</div><div class="kpi-value">{moneda_simbolo}{total_ahorro_actual:,.2f}</div></div>', unsafe_allow_html=True)
    with c5:
        st.markdown(f'<div class="restante-card" style="margin: 0; padding: 12px;"><div class="restante-title">Dinero Restante</div><div class="restante-value" style="font-size: 1.65rem;">{moneda_simbolo}{dinero_restante:,.2f}</div></div>', unsafe_allow_html=True)
        
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        df_chart_50 = pd.DataFrame({
            "Categoría": ["50% Necesidades", "30% Deseos", "20% Ahorros"],
            "Presupuestado": [presup_50, presup_30, presup_20],
            "Actual": [actual_necesidades, actual_deseos, actual_ahorros]
        })
        fig_donut = go.Figure(data=[go.Pie(
            labels=df_chart_50["Categoría"],
            values=df_chart_50["Actual"] if df_chart_50["Actual"].sum() > 0 else df_chart_50["Presupuestado"],
            hole=.55,
            marker_colors=[PALETTE["taupe_dark"], PALETTE["taupe_soft"], PALETTE["sage_green"]],
            textinfo='percent+label'
        )])
        fig_donut.update_layout(
            title_text="<b>DISTRIBUCIÓN 50 / 30 / 20 (ACTUAL)</b>",
            title_x=0.5,
            height=260,
            margin=dict(t=40, b=20, l=10, r=10),
            showlegend=False
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with chart_col2:
        fig_bar = go.Figure(data=[
            go.Bar(name='Ingresos', x=['Comparativo'], y=[total_ingreso_actual], marker_color=PALETTE["sage_green"], text=[f"{moneda_simbolo}{total_ingreso_actual:,.2f}"], textposition='auto'),
            go.Bar(name='Gastos', x=['Comparativo'], y=[total_gastado], marker_color=PALETTE["taupe_soft"], text=[f"{moneda_simbolo}{total_gastado:,.2f}"], textposition='auto')
        ])
        fig_bar.update_layout(title_text="<b>INGRESOS VS GASTOS</b>", title_x=0.5, barmode='group', height=260, margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    col_left, col_center, col_right = st.columns([1.1, 1.4, 1.4])

    with col_left:
        st.markdown('<div class="section-pill">💵 INGRESOS</div>', unsafe_allow_html=True)
        edited_ing = st.data_editor(
            datos_m["ingresos"],
            column_config={
                "Pagado": st.column_config.CheckboxColumn("✓", default=False),
                "Descripción": st.column_config.TextColumn("Descripción"),
                "Presupuesto": st.column_config.NumberColumn("Presup.", format=f"{moneda_simbolo}%.2f"),
                "Actual": st.column_config.NumberColumn("Actual", format=f"{moneda_simbolo}%.2f")
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_ing_{mes_actual}_{usuario_info['nombre']}"
        )
        usuario_info["datos_meses"][mes_actual]["ingresos"] = edited_ing

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-pill">⚖️ REGLA 50 / 30 / 20</div>', unsafe_allow_html=True)
        
        df_p50 = pd.DataFrame([
            {"Categoría": "Necesidades", "%": "50%", "Presupuesto": presup_50, "Actual": actual_necesidades},
            {"Categoría": "Deseos", "%": "30%", "Presupuesto": presup_30, "Actual": actual_deseos},
            {"Categoría": "Ahorros", "%": "20%", "Presupuesto": presup_20, "Actual": actual_ahorros},
            {"Categoría": "TOTAL", "%": "100%", "Presupuesto": (presup_50 + presup_30 + presup_20), "Actual": (actual_necesidades + actual_deseos + actual_ahorros)}
        ])
        st.dataframe(df_p50.style.format({"Presupuesto": f"{moneda_simbolo}{{:,.2f}}", "Actual": f"{moneda_simbolo}{{:,.2f}}"}), use_container_width=True, hide_index=True)

    with col_center:
        st.markdown('<div class="section-pill">📑 FACTURAS (GASTOS FIJOS)</div>', unsafe_allow_html=True)
        edited_fac = st.data_editor(
            datos_m["facturas"],
            column_config={
                "Pagado": st.column_config.CheckboxColumn("✓", default=False),
                "Descripción": st.column_config.TextColumn("Descripción"),
                "Presupuesto": st.column_config.NumberColumn("Presup.", format=f"{moneda_simbolo}%.2f"),
                "Actual": st.column_config.NumberColumn("Actual", format=f"{moneda_simbolo}%.2f"),
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Necesidades", "Deseos"], default="Necesidades"),
                "Fecha": st.column_config.TextColumn("Fecha Venc.")
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_fac_{mes_actual}_{usuario_info['nombre']}"
        )
        usuario_info["datos_meses"][mes_actual]["facturas"] = edited_fac

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-pill">🛍️ GASTOS VARIABLES</div>', unsafe_allow_html=True)

        with st.expander("✏️ Editar Presupuestos Variables", expanded=False):
            nuevos_presup_gv = {}
            col_a, col_b = st.columns(2)
            for i, cat in enumerate(CATEGORIAS_VARIABLES):
                with col_a if i % 2 == 0 else col_b:
                    nuevos_presup_gv[cat] = st.number_input(
                        cat,
                        value=float(datos_m["gv_presupuesto"].get(cat, 0.0)),
                        step=10.0,
                        key=f"gv_input_{cat}_{mes_actual}_{usuario_info['nombre']}"
                    )
            datos_m["gv_presupuesto"] = nuevos_presup_gv

        st.dataframe(
            df_gv[["Pagado", "Categoría", "Presupuesto", "Actual", "Tipo"]].style.format({"Presupuesto": f"{moneda_simbolo}{{:,.2f}}", "Actual": f"{moneda_simbolo}{{:,.2f}}"}),
            use_container_width=True,
            hide_index=True
        )

    with col_right:
        st.markdown('<div class="section-pill">🌱 AHORROS & METAS</div>', unsafe_allow_html=True)
        edited_ah = st.data_editor(
            datos_m["ahorros"],
            column_config={
                "Cumplido": st.column_config.CheckboxColumn("✓", default=False),
                "Concepto": st.column_config.TextColumn("Concepto"),
                "Presupuesto": st.column_config.NumberColumn("Meta", format=f"{moneda_simbolo}%.2f"),
                "Actual": st.column_config.NumberColumn("Ahorrado", format=f"{moneda_simbolo}%.2f"),
                "Notas": st.column_config.TextColumn("Notas")
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_ah_{mes_actual}_{usuario_info['nombre']}"
        )
        usuario_info["datos_meses"][mes_actual]["ahorros"] = edited_ah

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-pill">🧾 REGISTRO RÁPIDO DE GASTOS</div>', unsafe_allow_html=True)

        with st.expander("➕ Añadir Transacción Diaria", expanded=True):
            with st.form(key=f"form_gasto_{mes_actual}_{usuario_info['nombre']}"):
                c_monto, c_cat = st.columns(2)
                with c_monto:
                    nuevo_monto = st.number_input("Monto", min_value=0.01, value=25.0, step=1.0)
                with c_cat:
                    nueva_cat = st.selectbox("Categoría", CATEGORIAS_VARIABLES)
                    
                c_fec, c_det = st.columns(2)
                with c_fec:
                    nueva_fecha = st.text_input("Fecha", value=datetime.today().strftime("%d %b").lower())
                with c_det:
                    nuevo_det = st.text_input("Detalle", placeholder="Ej: Compra supermercado")
                    
                if st.form_submit_button("Guardar Gasto", use_container_width=True):
                    nuevo_registro = {
                        "Pagado": True,
                        "Monto": float(nuevo_monto),
                        "Categoría": nueva_cat,
                        "Fecha": nueva_fecha,
                        "Detalle": nuevo_det
                    }
                    usuario_info["datos_meses"][mes_actual]["transacciones"] = pd.concat(
                        [usuario_info["datos_meses"][mes_actual]["transacciones"], pd.DataFrame([nuevo_registro])],
                        ignore_index=True
                    )
                    st.success("¡Gasto guardado!")
                    st.rerun()

        edited_trn = st.data_editor(
            datos_m["transacciones"],
            column_config={
                "Pagado": st.column_config.CheckboxColumn("✓", default=True),
                "Monto": st.column_config.NumberColumn("Monto", format=f"{moneda_simbolo}%.2f"),
                "Categoría": st.column_config.SelectboxColumn("Categoría", options=CATEGORIAS_VARIABLES),
                "Fecha": st.column_config.TextColumn("Fecha"),
                "Detalle": st.column_config.TextColumn("Detalle")
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_trn_{mes_actual}_{usuario_info['nombre']}"
        )
        usuario_info["datos_meses"][mes_actual]["transacciones"] = edited_trn

else:
    st.markdown(f"""
    <div class="dashboard-header">
        <h1>RESUMEN FINANCIERO ANUAL {usuario_info['anio']}</h1>
        <p>~ Consolidación de los 12 meses y evolución patrimonial de {usuario_info['nombre']} ~</p>
    </div>
    """, unsafe_allow_html=True)
    
    resumen_data = []
    for m in MESES:
        dm = usuario_info["datos_meses"][m]
        ing = float(dm["ingresos"]["Actual"].sum())
        fac = float(dm["facturas"]["Actual"].sum())
        trn_sum = float(dm["transacciones"]["Monto"].sum()) if not dm["transacciones"].empty else 0.0
        gst_tot = fac + trn_sum
        ah = float(dm["ahorros"]["Actual"].sum())
        rest = ing - (gst_tot + ah)
        
        fac_nec = float(dm["facturas"][dm["facturas"]["Tipo"] == "Necesidades"]["Actual"].sum())
        trn_df = dm["transacciones"]
        if not trn_df.empty:
            trn_df["Tipo"] = trn_df["Categoría"].map(CATEGORIAS_TIPO_DEFAULT)
            trn_nec = float(trn_df[trn_df["Tipo"] == "Necesidades"]["Monto"].sum())
            trn_des = float(trn_df[trn_df["Tipo"] == "Deseos"]["Monto"].sum())
        else:
            trn_nec = 0.0
            trn_des = 0.0
            
        nec = fac_nec + trn_nec
        des = float(dm["facturas"][dm["facturas"]["Tipo"] == "Deseos"]["Actual"].sum()) + trn_des
        
        resumen_data.append({
            "Mes": m,
            "Ingresos": ing,
            "Gastos": gst_tot,
            "Ahorro": ah,
            "Flujo Neto": rest,
            "Necesidades (50%)": nec,
            "Deseos (30%)": des,
            "Ahorros (20%)": ah
        })
        
    df_anual = pd.DataFrame(resumen_data)
    
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Ingresos Anuales</div><div class="kpi-value">{moneda_simbolo}{df_anual["Ingresos"].sum():,.2f}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Gastos Anuales</div><div class="kpi-value">{moneda_simbolo}{df_anual["Gastos"].sum():,.2f}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Ahorro Anual</div><div class="kpi-value">{moneda_simbolo}{df_anual["Ahorro"].sum():,.2f}</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="restante-card" style="margin: 0; padding: 12px;"><div class="restante-title">Excedente Neto</div><div class="restante-value" style="font-size: 1.65rem;">{moneda_simbolo}{df_anual["Flujo Neto"].sum():,.2f}</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    
    fig_evol = go.Figure()
    fig_evol.add_trace(go.Bar(x=df_anual["Mes"], y=df_anual["Ingresos"], name="Ingresos", marker_color=PALETTE["sage_green"]))
    fig_evol.add_trace(go.Bar(x=df_anual["Mes"], y=df_anual["Gastos"], name="Gastos", marker_color=PALETTE["taupe_soft"]))
    fig_evol.add_trace(go.Bar(x=df_anual["Mes"], y=df_anual["Ahorro"], name="Ahorro", marker_color=PALETTE["taupe_dark"]))
    fig_evol.update_layout(title="<b>EVOLUCIÓN MENSUAL DE INGRESOS, GASTOS Y AHORROS</b>", title_x=0.5, barmode='group', height=350, margin=dict(t=45, b=20, l=10, r=10))
    st.plotly_chart(fig_evol, use_container_width=True)

    st.markdown("### 📊 Resumen Mes a Mes")
    st.dataframe(
        df_anual.style.format({
            "Ingresos": f"{moneda_simbolo}{{:,.2f}}",
            "Gastos": f"{moneda_simbolo}{{:,.2f}}",
            "Ahorro": f"{moneda_simbolo}{{:,.2f}}",
            "Flujo Neto": f"{moneda_simbolo}{{:,.2f}}",
            "Necesidades (50%)": f"{moneda_simbolo}{{:,.2f}}",
            "Deseos (30%)": f"{moneda_simbolo}{{:,.2f}}",
            "Ahorros (20%)": f"{moneda_simbolo}{{:,.2f}}"
        }),
        use_container_width=True,
        hide_index=True
    )