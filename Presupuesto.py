import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import hmac
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import io

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="OptiBudget Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar tema de la app en session_state si no existe
if "app_theme" not in st.session_state:
    st.session_state.app_theme = "System"

# ==========================================
# 2. ESTILOS CSS ADAPTABLES (SYSTEM, LIGHT, DARK)
# ==========================================
if st.session_state.app_theme == "Dark":
    theme_css = """
    :root {
      color-scheme: dark !important;
      --card-bg: #1E293B;
      --card-border: #334155;
      --main-text: #F8FAFC;
      --sub-text: #94A3B8;
      --kpi-title: #38BDF8;
      --banner-bg: linear-gradient(135deg, #0F172A, #1E3A8A);
      --badge-bg: #1E3A5F;
      --badge-border: #38BDF8;
      --badge-text: #E0F2FE;
      --restante-bg: #0F2922;
      --restante-border: #00ACA9;
      --restante-text: #2DD4BF;
    }
    html, body, .stApp, [data-testid="stAppViewContainer"], .main {
      background-color: #0F172A !important;
      color: #F8FAFC !important;
    }
    p, span, label, h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] p {
      color: #F8FAFC !important;
    }
    """
    chart_template = "plotly_dark"
    chart_bg = "#1E293B"
    chart_text = "#F8FAFC"
elif st.session_state.app_theme == "Light":
    theme_css = """
    :root {
      color-scheme: light !important;
      --card-bg: #FFFFFF;
      --card-border: #E2E8F0;
      --main-text: #1E293B;
      --sub-text: #64748B;
      --kpi-title: #00385C;
      --banner-bg: linear-gradient(135deg, #00385C, #0F4F7F);
      --badge-bg: #E5F6FF;
      --badge-border: #00385C;
      --badge-text: #00385C;
      --restante-bg: #F0FDF4;
      --restante-border: #00ACA9;
      --restante-text: #00ACA9;
    }
    html, body, .stApp, [data-testid="stAppViewContainer"], .main {
      background-color: #FFFFFF !important;
      color: #1E293B !important;
    }
    p, span, label, h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] p {
      color: #1E293B !important;
    }
    """
    chart_template = "plotly_white"
    chart_bg = "#FFFFFF"
    chart_text = "#00385C"
else:
    theme_css = """
    :root {
      --card-bg: var(--background-color, #FFFFFF);
      --card-border: rgba(148, 163, 184, 0.3);
      --main-text: var(--text-color, #1E293B);
      --sub-text: #64748B;
      --kpi-title: #00ACA9;
      --banner-bg: linear-gradient(135deg, #00385C, #0F4F7F);
      --badge-bg: rgba(0, 56, 92, 0.1);
      --badge-border: #00385C;
      --badge-text: var(--text-color, #00385C);
      --restante-bg: rgba(0, 172, 169, 0.08);
      --restante-border: #00ACA9;
      --restante-text: #00ACA9;
    }
    """
    chart_template = "none"
    chart_bg = "rgba(0,0,0,0)"
    chart_text = "#00ACA9"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800&display=swap');

{theme_css}

html, body, .stApp {{
  font-family: 'Nunito Sans', sans-serif !important;
}}

/* SIDEBAR ESTILO SAP BYDESIGN COLOR #29AFE2 CON LETRAS BLANCAS */
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
  background-color: #29afe2 !important;
  border-right: 1.5px solid #1e98c7 !important;
}}

[data-testid="stSidebar"] * {{
  color: #FFFFFF !important;
}}

[data-testid="stSidebar"] .stSelectbox label, 
[data-testid="stSidebar"] .stNumberInput label,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {{
  color: #FFFFFF !important;
}}

[data-testid="stSidebar"] div[data-baseweb="select"] > div,
[data-testid="stSidebar"] input {{
  background-color: #FFFFFF !important;
  color: #1E293B !important;
  border-color: #FFFFFF !important;
}}

[data-testid="stSidebar"] div[data-baseweb="select"] * {{
  color: #1E293B !important;
}}

.sap-work-center-header {{
  font-size: 0.74rem;
  font-weight: 800;
  text-transform: uppercase;
  color: #FFFFFF !important;
  letter-spacing: 1.2px;
  padding: 8px 4px 4px 4px;
  margin-top: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.4);
}}

[data-testid="stSidebar"] div.stButton > button {{
  background-color: rgba(255, 255, 255, 0.18) !important;
  color: #FFFFFF !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  text-align: left !important;
  justify-content: flex-start !important;
  padding: 8px 12px !important;
  font-weight: 700 !important;
  font-size: 0.88rem !important;
  border-radius: 6px !important;
  transition: all 0.2s ease-in-out !important;
}}

[data-testid="stSidebar"] div.stButton > button:hover {{
  background-color: #FFFFFF !important;
  color: #00385C !important;
  border-left: 5px solid #00385C !important;
}}

[data-testid="stSidebar"] div.stButton > button:hover * {{
  color: #00385C !important;
}}

.sap-user-card {{
  background-color: rgba(0, 56, 92, 0.25) !important;
  border: 1.5px solid rgba(255, 255, 255, 0.45) !important;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 14px;
}}

/* BANNER DE CABECERA CON TÍTULOS TOTALMENTE CENTRADOS */
.main-header-banner {{
  background: var(--banner-bg) !important;
  color: #FFFFFF !important;
  padding: 1.4rem 2rem;
  border-radius: 12px;
  margin-bottom: 1.2rem;
  text-align: center !important;
  box-shadow: 0 4px 14px rgba(0, 56, 92, 0.12);
}}

.main-header-title {{
  font-size: 1.85rem;
  font-weight: 800;
  margin: 0 auto !important;
  text-align: center !important;
  color: #FFFFFF !important;
}}

.main-header-subtitle {{
  font-size: 0.96rem;
  color: #E2E8F0 !important;
  margin-top: 6px;
  text-align: center !important;
}}

/* Tarjetas KPI y Dinero Restante */
.kpi-card {{
  background: var(--card-bg) !important;
  border: 1.5px solid var(--card-border) !important;
  border-radius: 10px;
  padding: 1rem 0.8rem;
  text-align: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}}

.kpi-card-label {{
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--sub-text) !important;
  letter-spacing: 0.5px;
}}

.kpi-card-value {{
  font-size: 1.55rem;
  font-weight: 800;
  color: var(--kpi-title) !important;
  margin-top: 0.25rem;
}}

.restante-card {{
  background: var(--restante-bg) !important;
  border: 2px solid var(--restante-border) !important;
  border-radius: 10px;
  padding: 1rem 0.8rem;
  text-align: center;
  box-shadow: 0 2px 6px rgba(0, 172, 169, 0.1);
}}

.restante-card-label {{
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--restante-text) !important;
  letter-spacing: 0.5px;
}}

.restante-card-value {{
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--restante-text) !important;
  margin-top: 0.25rem;
}}

.section-badge {{
  background-color: var(--badge-bg) !important;
  color: var(--badge-text) !important;
  font-weight: 800;
  font-size: 0.85rem;
  padding: 6px 12px;
  border-radius: 6px;
  display: inline-block;
  margin-bottom: 0.6rem;
  border-left: 4px solid var(--badge-border) !important;
}}

/* CAMPANA DE NOTIFICACIONES */
.bell-badge {{
  background-color: #D74546;
  color: white !important;
  font-weight: 800;
  border-radius: 50%;
  padding: 2px 7px;
  font-size: 0.75rem;
  margin-left: 4px;
}}

.notif-box {{
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 8px;
  border-left: 4px solid #00ACA9;
}}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SEGURIDAD, ESTADO Y USUARIOS
# ==========================================
def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 100000)
    return key.hex(), salt

def verify_password(stored_hash: str, salt: str, password_attempt: str) -> bool:
    attempt_hash = hashlib.pbkdf2_hmac('sha256', password_attempt.encode('utf-8'), bytes.fromhex(salt), 100000).hex()
    return hmac.compare_digest(stored_hash, attempt_hash)

CHRONO_MONTHS = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def create_initial_example_month():
    return {
        "ingresos": pd.DataFrame([
            {"Check": False, "Descripción": "Salario / Ingreso Principal", "Actual": 0.0}
        ]),
        "facturas": pd.DataFrame([
            {"Descripción": "Renta / Vivienda", "Monto": 0.0, "Tipo": "Necesidades", "Fecha": "01"}
        ]),
        "gastos_var": pd.DataFrame([
            {"Categoría": "Mercado / Alimentación", "Monto": 0.0, "Tipo": "Necesidades"}
        ]),
        "ahorros": pd.DataFrame([
            {"Concepto": "Fondo de Emergencia", "Monto": 0.0, "Notas": "Meta inicial de ahorro"}
        ]),
        "seguimiento": pd.DataFrame(columns=["Monto", "Categoría", "Fecha", "Detalle"])
    }

def clone_structure_from_month(source_month_data):
    new_ing = source_month_data["ingresos"].copy()
    if "Presupuesto" in new_ing.columns:
        new_ing = new_ing.drop(columns=["Presupuesto"])
    new_ing["Check"] = False
    new_ing["Actual"] = 0.0
    
    new_fac = source_month_data["facturas"].copy()
    new_fac["Monto"] = 0.0
    
    new_gv = source_month_data["gastos_var"].copy()
    new_gv["Monto"] = 0.0
    
    new_ah = source_month_data["ahorros"].copy()
    new_ah["Monto"] = 0.0
    
    new_seg = pd.DataFrame(columns=["Monto", "Categoría", "Fecha", "Detalle"])
    
    return {
        "ingresos": new_ing,
        "facturas": new_fac,
        "gastos_var": new_gv,
        "ahorros": new_ah,
        "seguimiento": new_seg
    }

DATA_VERSION = "v9_full_workflow_all_users"

def init_system_state():
    if "users" not in st.session_state:
        admin_hash, admin_salt = hash_password("admin123")
        user_hash, user_salt = hash_password("123456")
        st.session_state.users = {
            "admin@optibudget.com": {
                "name": "Super Administrador",
                "role": "Superusuario",
                "hash": admin_hash,
                "salt": admin_salt,
                "is_active": True,
                "failed_attempts": 0,
                "locked_until": None,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            },
            "usuario@demo.com": {
                "name": "Usuario Demo",
                "role": "Usuario",
                "hash": user_hash,
                "salt": user_salt,
                "is_active": True,
                "failed_attempts": 0,
                "locked_until": None,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
        }
    if "finances" not in st.session_state:
        st.session_state.finances = {}
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "active_module" not in st.session_state:
        st.session_state.active_module = "📅 Presupuesto Mensual"
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []
    if "smtp_config" not in st.session_state:
        st.session_state.smtp_config = {
            "server": "smtp.gmail.com",
            "port": 587,
            "sender": "",
            "password": "",
            "recipient": "admin@optibudget.com",
            "active": False
        }

init_system_state()

def init_user_finances(email):
    current_year = datetime.now().year
    if email not in st.session_state.finances:
        st.session_state.finances[email] = {
            current_year: {
                "Enero": create_initial_example_month()
            }
        }

def send_security_alert(target_email, event_type, details):
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_email": target_email,
        "event_type": event_type,
        "details": details,
        "correo_enviado": "No configurado"
    }
    
    cfg = st.session_state.smtp_config
    if cfg["active"] and cfg["sender"] and cfg["password"] and cfg["recipient"]:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 [NOTIFICACIÓN] {event_type} - OptiBudget Pro"
            msg["From"] = cfg["sender"]
            msg["To"] = cfg["recipient"]
            
            html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #CBD5E1; border-radius: 8px;">
              <h2 style="color: #00385C; margin-top: 0;">💼 OptiBudget Pro - Notificación del Sistema</h2>
              <p>Se ha registrado el siguiente evento en la plataforma:</p>
              <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr style="background: #F8FAFC;"><td style="padding: 8px; font-weight: bold;">Evento:</td><td style="padding: 8px; color: #00ACA9;">{event_type}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Fecha y Hora:</td><td style="padding: 8px;">{log_entry['timestamp']}</td></tr>
                <tr style="background: #F8FAFC;"><td style="padding: 8px; font-weight: bold;">Cuenta Relacionada:</td><td style="padding: 8px;">{target_email}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Detalles:</td><td style="padding: 8px;">{details}</td></tr>
              </table>
              <hr style="border: 0; border-top: 1px solid #CBD5E1;">
              <p style="font-size: 0.85rem; color: #64748B;">Notificación enviada a la dirección administrativa configurada.</p>
            </div>
            """
            msg.attach(MIMEText(html, "html"))
            
            server = smtplib.SMTP(cfg["server"], cfg["port"], timeout=6)
            server.starttls()
            server.login(cfg["sender"], cfg["password"])
            server.sendmail(cfg["sender"], cfg["recipient"], msg.as_string())
            server.quit()
            log_entry["correo_enviado"] = f"Enviado a {cfg['recipient']}"
        except Exception as e:
            log_entry["correo_enviado"] = f"Error: {str(e)}"
            
    st.session_state.audit_log.append(log_entry)

# ==========================================
# 4. PANTALLA DE ACCESO (LOGIN & REGISTRO)
# ==========================================
if st.session_state.current_user is None:
    st.markdown("""
    <div style='text-align: center; padding: 2.5rem 0 1rem 0;'>
      <h1 style='color: #00385C !important; font-size: 2.4rem; font-weight: 800; margin: 0;'>💼 OptiBudget Pro</h1>
      <p style='color: #18688D !important; font-size: 1.05rem; margin-top: 6px;'>Gestión Financiera Multi-Horizonte con Seguridad Avanzada</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        tab_login, tab_reg = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
        
        with tab_login:
            with st.form("form_login"):
                login_email = st.text_input("Correo electrónico").strip().lower()
                login_pass = st.text_input("Contraseña", type="password")
                btn_login = st.form_submit_button("Ingresar a OptiBudget Pro", use_container_width=True)
                
                if btn_login:
                    if login_email in st.session_state.users:
                        u_data = st.session_state.users[login_email]
                        
                        # 1. VALIDACIÓN: USUARIO ACTIVO/APROBADO POR EL ADMIN
                        if not u_data.get("is_active", True):
                            st.warning("⏳ Tu cuenta ha sido registrada pero está pendiente de aprobación por el Administrador. No puedes ingresar hasta que sea validada.")
                        elif u_data["locked_until"] and datetime.now() < u_data["locked_until"]:
                            st.error(f"⛔ Cuenta bloqueada por seguridad hasta {u_data['locked_until'].strftime('%H:%M:%S')}.")
                        else:
                            if verify_password(u_data["hash"], u_data["salt"], login_pass):
                                u_data["failed_attempts"] = 0
                                u_data["locked_until"] = None
                                st.session_state.current_user = login_email
                                init_user_finances(login_email)
                                st.success("Acceso autorizado con éxito.")
                                st.rerun()
                            else:
                                u_data["failed_attempts"] += 1
                                if u_data["failed_attempts"] >= 3:
                                    u_data["locked_until"] = datetime.now() + timedelta(minutes=15)
                                    send_security_alert(login_email, "INTROMISIÓN DETECTADA / BLOQUEO", "3 intentos fallidos consecutivos.")
                                    st.error("⛔ Demasiados intentos fallidos. Cuenta bloqueada por 15 minutos.")
                                else:
                                    send_security_alert(login_email, "INTENTO FALLIDO", f"Intento #{u_data['failed_attempts']}")
                                    st.warning(f"Credenciales incorrectas. Intentos restantes: {3 - u_data['failed_attempts']}.")
                    else:
                        st.error("Credenciales inválidas.")

        with tab_reg:
            with st.form("form_register"):
                reg_name = st.text_input("Nombre Completo")
                reg_email = st.text_input("Correo Electrónico").strip().lower()
                reg_pass = st.text_input("Contraseña", type="password")
                reg_pass_conf = st.text_input("Confirmar Contraseña", type="password")
                btn_reg = st.form_submit_button("Crear Cuenta", use_container_width=True)
                
                if btn_reg:
                    if not reg_name or not reg_email or not reg_pass:
                        st.warning("Por favor completa todos los campos requeridos.")
                    elif reg_pass != reg_pass_conf:
                        st.error("Las contraseñas no coinciden.")
                    elif reg_email in st.session_state.users:
                        st.error("El correo ya se encuentra registrado.")
                    else:
                        phash, psalt = hash_password(reg_pass)
                        st.session_state.users[reg_email] = {
                            "name": reg_name,
                            "role": "Usuario",
                            "hash": phash,
                            "salt": psalt,
                            "is_active": False,
                            "failed_attempts": 0,
                            "locked_until": None,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        init_user_finances(reg_email)
                        
                        send_security_alert(
                            reg_email, 
                            "NUEVO USUARIO PENDIENTE DE APROBACIÓN", 
                            f"El usuario {reg_name} ({reg_email}) se ha registrado. Requiere activación en el panel de administración."
                        )
                        st.success("✅ Cuenta registrada exitosamente. Se ha enviado un correo al Administrador. Podrás ingresar tan pronto active tu cuenta.")
    st.stop()

# ==========================================
# 5. MENÚ LATERAL ESTILO SAP BYDESIGN Y NOTIFICACIONES
# ==========================================
current_email = st.session_state.current_user
user_info = st.session_state.users[current_email]
is_admin = user_info["role"] == "Superusuario"

init_user_finances(current_email)
user_fin = st.session_state.finances[current_email]

# CÁLCULO DE TAREAS Y MENSAJES PENDIENTES PARA LA CAMPANA 🔔
notifications = []
now = datetime.now()
current_sys_year = now.year
current_sys_month = CHRONO_MONTHS[now.month - 1]

if is_admin:
    pending_users = [mail for mail, u in st.session_state.users.items() if not u.get("is_active", False)]
    if pending_users:
        notifications.append(f"👥 Hay **{len(pending_users)}** usuario(s) pendiente(s) de aprobación para ingresar.")

if current_sys_year not in user_fin:
    notifications.append(f"📅 Estamos en el año **{current_sys_year}** y aún no has creado este año fiscal.")
elif current_sys_month not in user_fin[current_sys_year]:
    notifications.append(f"🗓️ Ha comenzado **{current_sys_month} {current_sys_year}** y aún no has creado este mes.")

with st.sidebar:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 4px;'>
      <div style='font-size: 1.35rem;'>💼</div>
      <div>
        <div style='font-size: 1.15rem; font-weight: 800; color: #FFFFFF !important; line-height: 1.1;'>OptiBudget Pro</div>
        <div style='font-size: 0.72rem; color: #FFFFFF !important; text-transform: uppercase; letter-spacing: 0.8px;'>SAP ByDesign Edition</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # SELECTOR DE TEMA: System, Light, Dark (SIN FORZAR FONDO)
    theme_choice = st.selectbox(
        "🎨 Tema Visual",
        ["System", "Light", "Dark"],
        index=["System", "Light", "Dark"].index(st.session_state.app_theme)
    )
    if theme_choice != st.session_state.app_theme:
        st.session_state.app_theme = theme_choice
        st.rerun()

    # CAMPANA DE NOTIFICACIONES (🔔)
    notif_count = len(notifications)
    with st.expander(f"🔔 Notificaciones y Tareas {f'({notif_count})' if notif_count > 0 else ''}"):
        if notifications:
            for n in notifications:
                st.markdown(f"<div class='notif-box'>⚠️ {n}</div>", unsafe_allow_html=True)
        else:
            st.success("✅ No tienes tareas pendientes. ¡Todo al día!")

    # Tarjeta de Usuario Activo
    st.markdown(f"""
    <div class='sap-user-card'>
      <div style='font-size: 0.68rem; color: #FFFFFF !important; font-weight: 800; text-transform: uppercase;'>Usuario Activo</div>
      <div style='font-size: 0.98rem; color: #FFFFFF !important; font-weight: 800;'>{user_info['name']}</div>
      <div style='font-size: 0.78rem; color: #FFFFFF !important;'>{current_email}</div>
      <div style='margin-top: 5px;'><span style='background: #00385C; color: #FFFFFF !important; padding: 2px 7px; border-radius: 4px; font-size: 0.68rem; font-weight: 800;'>{user_info['role']}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # 1. MÓDULOS DE TRABAJO (ARRIBA)
    st.markdown("<div class='sap-work-center-header'>Centro de Trabajo (Módulos)</div>", unsafe_allow_html=True)

    module_list = [
        ("📅 Presupuesto Mensual", "Ejecución y Gestión"),
        ("📊 Resumen Anual", "Consolidado Fiscal"),
        ("📈 Horizontes Financieros", "Proyección 3, 5, 10+ Años")
    ]
    if is_admin:
        admin_notif_tag = f" ({len(pending_users)})" if (is_admin and pending_users) else ""
        module_list.append((f"👑 Panel de Administración{admin_notif_tag}", "Control Superusuario"))

    for mod_tuple in module_list:
        mod_name = mod_tuple[0]
        is_active = (st.session_state.active_module.split(" (")[0] == mod_name.split(" (")[0])
        prefix = "▶ " if is_active else "  "
        if st.button(f"{prefix}{mod_name}", key=f"nav_btn_{mod_name}", use_container_width=True):
            st.session_state.active_module = mod_name
            st.rerun()

    menu_selection = st.session_state.active_module.split(" (")[0]

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 2. GESTIÓN DE AÑOS Y MESES (DEBAJO DE LOS MÓDULOS)
    st.markdown("<div class='sap-work-center-header'>Período Fiscal & Parámetros</div>", unsafe_allow_html=True)

    created_years = sorted(list(user_fin.keys()))
    if "current_sel_year" not in st.session_state or st.session_state.current_sel_year not in created_years:
        st.session_state.current_sel_year = created_years[-1]
    
    sel_year = st.selectbox("Año Fiscal Activo", created_years, index=created_years.index(st.session_state.current_sel_year))
    st.session_state.current_sel_year = sel_year

    with st.expander("➕ Crear Nuevo Año"):
        with st.form("form_create_year"):
            next_suggested_year = max(created_years) + 1 if created_years else current_sys_year
            new_year_input = st.number_input("Año a crear", min_value=2020, max_value=2099, value=next_suggested_year, step=1)
            btn_create_year = st.form_submit_button("Crear Año", use_container_width=True)
            
            if btn_create_year:
                if new_year_input in user_fin:
                    st.warning(f"El año {new_year_input} ya existe.")
                else:
                    user_fin[new_year_input] = {
                        "Enero": create_initial_example_month()
                    }
                    st.session_state.current_sel_year = new_year_input
                    st.success(f"¡Año {new_year_input} creado!")
                    st.rerun()

    months_in_active_year = [m for m in CHRONO_MONTHS if m in user_fin[sel_year]]
    if not months_in_active_year:
        user_fin[sel_year]["Enero"] = create_initial_example_month()
        months_in_active_year = ["Enero"]

    if "current_sel_month" not in st.session_state or st.session_state.current_sel_month not in months_in_active_year:
        st.session_state.current_sel_month = months_in_active_year[-1]

    sel_month = st.selectbox("Mes Activo", months_in_active_year, index=months_in_active_year.index(st.session_state.current_sel_month))
    st.session_state.current_sel_month = sel_month

    uncreated_months = [m for m in CHRONO_MONTHS if m not in months_in_active_year]
    if uncreated_months:
        with st.expander("➕ Crear Nuevo Mes"):
            with st.form("form_create_month"):
                st.caption("Copia la lista de conceptos del mes previo con los valores en 0.0.")
                next_month_to_create = st.selectbox("Mes a crear", uncreated_months, index=0)
                clone_from = st.selectbox("Traer campos de:", months_in_active_year, index=len(months_in_active_year)-1)
                btn_create_month = st.form_submit_button("Crear Mes", use_container_width=True)
                
                if btn_create_month:
                    source_data = user_fin[sel_year][clone_from]
                    user_fin[sel_year][next_month_to_create] = clone_structure_from_month(source_data)
                    st.session_state.current_sel_month = next_month_to_create
                    st.success(f"¡Mes {next_month_to_create} creado!")
                    st.rerun()
    else:
        st.caption("✅ Todos los meses de este año están creados.")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.current_user = None
        st.rerun()

# ==========================================
# 6. VISTA: PRESUPUESTO MENSUAL (REACTIVO EN TIEMPO REAL)
# ==========================================
if menu_selection == "📅 Presupuesto Mensual":
    data_m = user_fin[sel_year][sel_month]
    
    if "Presupuesto" in data_m["ingresos"].columns:
        data_m["ingresos"] = data_m["ingresos"].drop(columns=["Presupuesto"])
    
    # RECALCULO REACTIVO TOTAL
    total_ingreso_act = float(data_m["ingresos"]["Actual"].sum()) if not data_m["ingresos"].empty else 0.0
    total_facturas = float(data_m["facturas"]["Monto"].sum()) if not data_m["facturas"].empty else 0.0
    total_var = float(data_m["gastos_var"]["Monto"].sum()) if not data_m["gastos_var"].empty else 0.0
    total_seg = float(data_m["seguimiento"]["Monto"].sum()) if not data_m["seguimiento"].empty else 0.0
    total_ahorro = float(data_m["ahorros"]["Monto"].sum()) if not data_m["ahorros"].empty else 0.0
    
    total_gastado = total_facturas + total_var + total_seg
    dinero_restante = total_ingreso_act - total_gastado - total_ahorro
    
    fac_nec = data_m["facturas"][data_m["facturas"]["Tipo"] == "Necesidades"]["Monto"].sum() if not data_m["facturas"].empty else 0.0
    var_nec = data_m["gastos_var"][data_m["gastos_var"]["Tipo"] == "Necesidades"]["Monto"].sum() if not data_m["gastos_var"].empty else 0.0
    nec_total = fac_nec + var_nec
    
    fac_des = data_m["facturas"][data_m["facturas"]["Tipo"] == "Deseos"]["Monto"].sum() if not data_m["facturas"].empty else 0.0
    var_des = data_m["gastos_var"][data_m["gastos_var"]["Tipo"] == "Deseos"]["Monto"].sum() if not data_m["gastos_var"].empty else 0.0
    des_total = fac_des + var_des
    
    # TÍTULO DE PÁGINA TOTALMENTE CENTRADO
    st.markdown(f"""
    <div class='main-header-banner'>
      <div class='main-header-title'>OptiBudget Pro — {sel_month.upper()} {sel_year}</div>
      <div class='main-header-subtitle'>Gestión y Ejecución Presupuestaria en Tiempo Real</div>
    </div>
    """, unsafe_allow_html=True)
    
    # TARJETAS DE VALORES KPI
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Ingreso Total Recibido</div>
          <div class='kpi-card-value'>${total_ingreso_act:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Total Gastado (Fijo + Var)</div>
          <div class='kpi-card-value'>${total_gastado:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Total Ahorrado / Invertido</div>
          <div class='kpi-card-value'>${total_ahorro:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class='restante-card'>
          <div class='restante-card-label'>Dinero Restante Disponible</div>
          <div class='restante-card-value'>${dinero_restante:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
    
    # GRÁFICOS REACTIVOS (TÍTULOS CENTRADOS Y TEMPLATE ADAPTABLE)
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        df_pie = pd.DataFrame({
            "Categoría": ["Necesidades (50%)", "Deseos (30%)", "Ahorros (20%)"],
            "Monto": [nec_total, des_total, total_ahorro]
        })
        if df_pie["Monto"].sum() == 0:
            fig_pie = px.pie(df_pie, names="Categoría", values=[1, 1, 1], hole=0.55,
                             color_discrete_sequence=["#94A3B8", "#CBD5E1", "#E2E8F0"])
        else:
            fig_pie = px.pie(df_pie, names="Categoría", values="Monto", hole=0.55,
                             color_discrete_sequence=["#00385C", "#31B4D1", "#00ACA9"])
        fig_pie.update_layout(
            template=chart_template,
            title=dict(text="Distribución 50/30/20 del Mes", x=0.5, xanchor="center", font=dict(color=chart_text, size=14)),
            margin=dict(t=40, b=10, l=10, r=10),
            height=250,
            paper_bgcolor=chart_bg,
            plot_bgcolor=chart_bg
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with g_col2:
        fig_bar = go.Figure(data=[
            go.Bar(name='Ingresos', x=['Mes'], y=[total_ingreso_act], marker_color='#00ACA9'),
            go.Bar(name='Gastos', x=['Mes'], y=[total_gastado], marker_color='#D74546'),
            go.Bar(name='Ahorros', x=['Mes'], y=[total_ahorro], marker_color='#00385C')
        ])
        fig_bar.update_layout(
            template=chart_template,
            barmode='group',
            title=dict(text="Comparativa Flujo de Caja", x=0.5, xanchor="center", font=dict(color=chart_text, size=14)),
            margin=dict(t=40, b=10, l=10, r=10),
            height=250,
            paper_bgcolor=chart_bg,
            plot_bgcolor=chart_bg
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # ==========================================
    # DISTRIBUCIÓN EN 2 COLUMNAS DE LAS TABLAS
    # ==========================================
    col_izq, col_der = st.columns(2)

    with col_izq:
        # 1. INGRESOS (Solo Actual)
        st.markdown("<div class='section-badge'>💵 1. INGRESOS (VALOR RECIBIDO)</div>", unsafe_allow_html=True)
        st.caption("Editable directamente en la tabla. Se recalcula en tiempo real.")
        edited_ing = st.data_editor(
            data_m["ingresos"],
            column_config={
                "Check": st.column_config.CheckboxColumn("✓", default=False),
                "Descripción": st.column_config.TextColumn("Descripción"),
                "Actual": st.column_config.NumberColumn("Actual ($)", format="$%.2f")
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"ing_{sel_year}_{sel_month}"
        )
        if not edited_ing.equals(data_m["ingresos"]):
            data_m["ingresos"] = edited_ing
            st.rerun()

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        # 2. FACTURAS (GASTOS FIJOS)
        st.markdown("<div class='section-badge'>📑 2. FACTURAS (GASTOS FIJOS)</div>", unsafe_allow_html=True)
        st.caption("🔒 Protegida contra edición accidental. Usa los botones inferiores.")
        df_fac_display = data_m["facturas"].copy()
        if not df_fac_display.empty:
            df_fac_display["Monto"] = df_fac_display["Monto"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df_fac_display, use_container_width=True)

        with st.expander("➕ Añadir Concepto de Factura"):
            with st.form(f"form_add_fac_{sel_year}_{sel_month}"):
                new_f_desc = st.text_input("Descripción (ej. Renta, Agua, Luz)")
                new_f_monto = st.number_input("Monto ($)", min_value=0.0, step=10.0, format="%.2f")
                new_f_tipo = st.selectbox("Clasificación 50/30/20", ["Necesidades", "Deseos"])
                new_f_fecha = st.text_input("Día Límite", value="15")
                btn_add_f = st.form_submit_button("Agregar Factura", use_container_width=True)
                
                if btn_add_f:
                    if new_f_desc.strip():
                        new_row = {"Descripción": new_f_desc.strip(), "Monto": new_f_monto, "Tipo": new_f_tipo, "Fecha": new_f_fecha}
                        data_m["facturas"] = pd.concat([data_m["facturas"], pd.DataFrame([new_row])], ignore_index=True)
                        st.success(f"Factura '{new_f_desc}' agregada.")
                        st.rerun()
                    else:
                        st.warning("Escribe una descripción.")

        with st.expander("✏️ Lápiz de Edición: Modificar Factura"):
            if not data_m["facturas"].empty:
                f_options = [f"{idx} - {row['Descripción']}" for idx, row in data_m["facturas"].iterrows()]
                selected_f_idx = st.selectbox("Seleccione factura", options=range(len(f_options)), format_func=lambda x: f_options[x], key=f"sel_f_{sel_year}_{sel_month}")
                
                current_f = data_m["facturas"].iloc[selected_f_idx]
                with st.form(f"form_edit_fac_{sel_year}_{sel_month}"):
                    edit_f_desc = st.text_input("Descripción", value=current_f["Descripción"])
                    edit_f_monto = st.number_input("Monto ($)", min_value=0.0, value=float(current_f["Monto"]), step=10.0, format="%.2f")
                    edit_f_tipo = st.selectbox("Tipo", ["Necesidades", "Deseos"], index=0 if current_f["Tipo"] == "Necesidades" else 1)
                    edit_f_fecha = st.text_input("Fecha", value=str(current_f["Fecha"]))
                    
                    c_save, c_del = st.columns(2)
                    with c_save:
                        btn_save_f = st.form_submit_button("💾 Guardar", use_container_width=True)
                    with c_del:
                        btn_del_f = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
                        
                    if btn_save_f:
                        data_m["facturas"].at[selected_f_idx, "Descripción"] = edit_f_desc
                        data_m["facturas"].at[selected_f_idx, "Monto"] = edit_f_monto
                        data_m["facturas"].at[selected_f_idx, "Tipo"] = edit_f_tipo
                        data_m["facturas"].at[selected_f_idx, "Fecha"] = edit_f_fecha
                        st.success("Factura actualizada.")
                        st.rerun()
                        
                    if btn_del_f:
                        data_m["facturas"] = data_m["facturas"].drop(index=selected_f_idx).reset_index(drop=True)
                        st.success("Factura eliminada.")
                        st.rerun()
            else:
                st.info("Sin facturas para editar.")

    with col_der:
        # 3. GASTOS VARIABLES
        st.markdown("<div class='section-badge'>🛒 3. GASTOS VARIABLES</div>", unsafe_allow_html=True)
        st.caption("🔒 Protegida contra edición accidental. Usa los botones inferiores.")
        df_var_display = data_m["gastos_var"].copy()
        if not df_var_display.empty:
            df_var_display["Monto"] = df_var_display["Monto"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df_var_display, use_container_width=True)

        with st.expander("➕ Añadir Categoría de Gasto Variable"):
            with st.form(f"form_add_gv_{sel_year}_{sel_month}"):
                new_gv_cat = st.text_input("Categoría (ej. Mercado, Gasolina, Ocio)")
                new_gv_monto = st.number_input("Monto ($)", min_value=0.0, step=10.0, format="%.2f")
                new_gv_tipo = st.selectbox("Clasificación", ["Necesidades", "Deseos"], key=f"new_gv_tipo_{sel_year}_{sel_month}")
                btn_add_gv = st.form_submit_button("Agregar Categoría", use_container_width=True)
                
                if btn_add_gv:
                    if new_gv_cat.strip():
                        new_row = {"Categoría": new_gv_cat.strip(), "Monto": new_gv_monto, "Tipo": new_gv_tipo}
                        data_m["gastos_var"] = pd.concat([data_m["gastos_var"], pd.DataFrame([new_row])], ignore_index=True)
                        st.success(f"Categoría '{new_gv_cat}' agregada.")
                        st.rerun()
                    else:
                        st.warning("Escribe una categoría.")

        with st.expander("✏️ Lápiz de Edición: Modificar Gasto Variable"):
            if not data_m["gastos_var"].empty:
                gv_options = [f"{idx} - {row['Categoría']}" for idx, row in data_m["gastos_var"].iterrows()]
                selected_gv_idx = st.selectbox("Seleccione categoría", options=range(len(gv_options)), format_func=lambda x: gv_options[x], key=f"sel_gv_{sel_year}_{sel_month}")
                
                current_gv = data_m["gastos_var"].iloc[selected_gv_idx]
                with st.form(f"form_edit_gv_{sel_year}_{sel_month}"):
                    edit_gv_cat = st.text_input("Categoría", value=current_gv["Categoría"])
                    edit_gv_monto = st.number_input("Monto ($)", min_value=0.0, value=float(current_gv["Monto"]), step=10.0, format="%.2f")
                    edit_gv_tipo = st.selectbox("Tipo", ["Necesidades", "Deseos"], index=0 if current_gv["Tipo"] == "Necesidades" else 1, key=f"ed_gv_tipo_{sel_year}_{sel_month}")
                    
                    c_save, c_del = st.columns(2)
                    with c_save:
                        btn_save_gv = st.form_submit_button("💾 Guardar", use_container_width=True)
                    with c_del:
                        btn_del_gv = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
                        
                    if btn_save_gv:
                        data_m["gastos_var"].at[selected_gv_idx, "Categoría"] = edit_gv_cat
                        data_m["gastos_var"].at[selected_gv_idx, "Monto"] = edit_gv_monto
                        data_m["gastos_var"].at[selected_gv_idx, "Tipo"] = edit_gv_tipo
                        st.success("Categoría actualizada.")
                        st.rerun()
                        
                    if btn_del_gv:
                        data_m["gastos_var"] = data_m["gastos_var"].drop(index=selected_gv_idx).reset_index(drop=True)
                        st.success("Categoría eliminada.")
                        st.rerun()
            else:
                st.info("Sin categorías para editar.")

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        # 4. AHORROS E INVERSIÓN
        st.markdown("<div class='section-badge'>🎯 4. AHORROS E INVERSIÓN (20%)</div>", unsafe_allow_html=True)
        st.caption("🔒 Protegida contra edición accidental. Usa los botones inferiores.")
        df_ah_display = data_m["ahorros"].copy()
        if not df_ah_display.empty:
            df_ah_display["Monto"] = df_ah_display["Monto"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df_ah_display, use_container_width=True)

        with st.expander("➕ Añadir Meta de Ahorro"):
            with st.form(f"form_add_ah_{sel_year}_{sel_month}"):
                new_ah_con = st.text_input("Concepto (ej. Fondo de Emergencia, Inversión)")
                new_ah_monto = st.number_input("Monto ($)", min_value=0.0, step=10.0, format="%.2f")
                new_ah_notas = st.text_input("Notas / Plazo", value="Meta personal")
                btn_add_ah = st.form_submit_button("Agregar Meta", use_container_width=True)
                
                if btn_add_ah:
                    if new_ah_con.strip():
                        new_row = {"Concepto": new_ah_con.strip(), "Monto": new_ah_monto, "Notas": new_ah_notas}
                        data_m["ahorros"] = pd.concat([data_m["ahorros"], pd.DataFrame([new_row])], ignore_index=True)
                        st.success(f"Meta '{new_ah_con}' agregada.")
                        st.rerun()
                    else:
                        st.warning("Escribe un concepto.")

        with st.expander("✏️ Lápiz de Edición: Modificar Meta de Ahorro"):
            if not data_m["ahorros"].empty:
                ah_options = [f"{idx} - {row['Concepto']}" for idx, row in data_m["ahorros"].iterrows()]
                selected_ah_idx = st.selectbox("Seleccione meta", options=range(len(ah_options)), format_func=lambda x: ah_options[x], key=f"sel_ah_{sel_year}_{sel_month}")
                
                current_ah = data_m["ahorros"].iloc[selected_ah_idx]
                with st.form(f"form_edit_ah_{sel_year}_{sel_month}"):
                    edit_ah_con = st.text_input("Concepto", value=current_ah["Concepto"])
                    edit_ah_monto = st.number_input("Monto ($)", min_value=0.0, value=float(current_ah["Monto"]), step=10.0, format="%.2f")
                    edit_ah_notas = st.text_input("Notas", value=str(current_ah["Notas"]))
                    
                    c_save, c_del = st.columns(2)
                    with c_save:
                        btn_save_ah = st.form_submit_button("💾 Guardar", use_container_width=True)
                    with c_del:
                        btn_del_ah = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
                        
                    if btn_save_ah:
                        data_m["ahorros"].at[selected_ah_idx, "Concepto"] = edit_ah_con
                        data_m["ahorros"].at[selected_ah_idx, "Monto"] = edit_ah_monto
                        data_m["ahorros"].at[selected_ah_idx, "Notas"] = edit_ah_notas
                        st.success("Meta actualizada.")
                        st.rerun()
                        
                    if btn_del_ah:
                        data_m["ahorros"] = data_m["ahorros"].drop(index=selected_ah_idx).reset_index(drop=True)
                        st.success("Meta eliminada.")
                        st.rerun()
            else:
                st.info("Sin metas de ahorro registradas.")

    st.markdown("---")

    # ==========================================
    # SECCIÓN 5: SEGUIMIENTO DE TRANSACCIONES (2 COLUMNAS)
    # ==========================================
    st.markdown("<div class='section-badge'>📝 5. SEGUIMIENTO DE GASTOS DIARIOS</div>", unsafe_allow_html=True)
    col_tx_list, col_tx_form = st.columns([1.3, 1])
    
    with col_tx_list:
        if not data_m["seguimiento"].empty:
            df_seg_disp = data_m["seguimiento"].copy()
            df_seg_disp["Monto"] = df_seg_disp["Monto"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(df_seg_disp, use_container_width=True)
        else:
            st.info("Aún no has registrado transacciones diarias este mes.")

    with col_tx_form:
        with st.form(f"form_add_seg_{sel_year}_{sel_month}"):
            st.markdown("**➕ Registrar Nueva Transacción**")
            seg_monto = st.number_input("Monto ($)", min_value=0.0, step=5.0, format="%.2f")
            seg_cat = st.selectbox("Categoría", [
                "Mercado y Alimentación", "Transporte / Combustible", "Restaurantes y Salidas", "Entretenimiento y Ocio",
                "Salud y Medicamentos", "Mascotas", "Cuidado Personal", "Hogar", "Ropa", "Educación", "Misceláneos"
            ])
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                seg_dia = st.text_input("Día", value=datetime.now().strftime("%d"))
            with c_d2:
                seg_det = st.text_input("Detalle", placeholder="Comercio / Nota")
                
            btn_add_seg = st.form_submit_button("Registrar Transacción", use_container_width=True)
            if btn_add_seg:
                if seg_monto > 0:
                    new_tx = {"Monto": seg_monto, "Categoría": seg_cat, "Fecha": seg_dia, "Detalle": seg_det}
                    data_m["seguimiento"] = pd.concat([data_m["seguimiento"], pd.DataFrame([new_tx])], ignore_index=True)
                    st.success("Transacción registrada.")
                    st.rerun()
                else:
                    st.warning("El monto debe ser superior a 0.")

# ==========================================
# 7. VISTA: RESUMEN ANUAL CONSOLIDADO
# ==========================================
elif menu_selection == "📊 Resumen Anual":
    st.markdown(f"""
    <div class='main-header-banner'>
      <div class='main-header-title'>OptiBudget Pro — CONSOLIDADO ANUAL {sel_year}</div>
      <div class='main-header-subtitle'>Rendimiento y Ejecución Financiera Mensualizada ({len(months_in_active_year)} meses registrados)</div>
    </div>
    """, unsafe_allow_html=True)
    
    summary_data = []
    for m in months_in_active_year:
        d = user_fin[sel_year][m]
        ing = d["ingresos"]["Actual"].sum() if not d["ingresos"].empty else 0.0
        fac = d["facturas"]["Monto"].sum() if not d["facturas"].empty else 0.0
        var = d["gastos_var"]["Monto"].sum() if not d["gastos_var"].empty else 0.0
        seg = d["seguimiento"]["Monto"].sum() if not d["seguimiento"].empty else 0.0
        aho = d["ahorros"]["Monto"].sum() if not d["ahorros"].empty else 0.0
        gas = fac + var + seg
        flujo = ing - gas - aho
        
        summary_data.append({
            "Mes": m,
            "Ingresos": ing,
            "Gastos": gas,
            "Ahorros": aho,
            "Flujo Neto": flujo
        })
        
    df_annual = pd.DataFrame(summary_data)
    
    tot_ing = df_annual["Ingresos"].sum() if not df_annual.empty else 0.0
    tot_gas = df_annual["Gastos"].sum() if not df_annual.empty else 0.0
    tot_aho = df_annual["Ahorros"].sum() if not df_annual.empty else 0.0
    tot_flu = df_annual["Flujo Neto"].sum() if not df_annual.empty else 0.0
    
    ca1, ca2, ca3, ca4 = st.columns(4)
    with ca1:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Ingresos Totales {sel_year}</div>
          <div class='kpi-card-value'>${tot_ing:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with ca2:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Gastos Totales {sel_year}</div>
          <div class='kpi-card-value'>${tot_gas:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with ca3:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Ahorro Acumulado {sel_year}</div>
          <div class='kpi-card-value'>${tot_aho:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with ca4:
        st.markdown(f"""
        <div class='restante-card'>
          <div class='restante-card-label'>Superávit Neto Anual</div>
          <div class='restante-card-value'>${tot_flu:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
    
    if not df_annual.empty:
        fig_an = go.Figure()
        fig_an.add_trace(go.Bar(x=df_annual["Mes"], y=df_annual["Ingresos"], name="Ingresos", marker_color="#00ACA9"))
        fig_an.add_trace(go.Bar(x=df_annual["Mes"], y=df_annual["Gastos"], name="Gastos", marker_color="#D74546"))
        fig_an.add_trace(go.Bar(x=df_annual["Mes"], y=df_annual["Ahorros"], name="Ahorros", marker_color="#00385C"))
        fig_an.update_layout(
            template=chart_template,
            title=dict(text=f"Comportamiento Mes a Mes ({sel_year})", x=0.5, xanchor="center", font=dict(color=chart_text, size=14)),
            barmode='group',
            height=340,
            paper_bgcolor=chart_bg,
            plot_bgcolor=chart_bg
        )
        st.plotly_chart(fig_an, use_container_width=True)
        
        df_annual_formatted = df_annual.copy()
        for col in ["Ingresos", "Gastos", "Ahorros", "Flujo Neto"]:
            df_annual_formatted[col] = df_annual_formatted[col].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df_annual_formatted, use_container_width=True)

# ==========================================
# 8. VISTA: HORIZONTES FINANCIEROS (3, 5, 10+ AÑOS)
# ==========================================
elif menu_selection == "📈 Horizontes Financieros":
    st.markdown("""
    <div class='main-header-banner'>
      <div class='main-header-title'>OptiBudget Pro — PLANIFICACIÓN PLURIANUAL</div>
      <div class='main-header-subtitle'>Proyección Estratégica: Corto Plazo (3 años), Mediano Plazo (5 años) y Largo Plazo (10+ años)</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab_cp, tab_mp, tab_lp = st.tabs([
        "⚡ Corto Plazo (3 Años)",
        "🎯 Mediano Plazo (5 Años)",
        "🏔️ Largo Plazo (10 o más Años)"
    ])
    
    curr_aho = sum([user_fin[sel_year][m]["ahorros"]["Monto"].sum() for m in months_in_active_year])
    
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        base_annual_savings = st.number_input("Ahorro / Inversión Anual Base ($)", min_value=0.0, value=float(curr_aho) if curr_aho > 0 else 3000.0, step=500.0)
    with col_sim2:
        annual_growth_rate = st.slider("Tasa de Crecimiento / Rendimiento Anual Estimado (%)", min_value=1.0, max_value=25.0, value=8.0, step=0.5)

    def calculate_projection(years_count, base_savings, rate_pct):
        r = rate_pct / 100.0
        records = []
        cumulative_principal = 0.0
        total_balance = 0.0
        start_year = sel_year
        for i in range(1, years_count + 1):
            year_label = start_year + i - 1
            cumulative_principal += base_savings
            total_balance = (total_balance + base_savings) * (1 + r)
            gains = total_balance - cumulative_principal
            records.append({
                "Año": year_label,
                "Periodo": f"Año {i}",
                "Aporte Acumulado": cumulative_principal,
                "Rendimientos / Interés Compuesto": max(0.0, gains),
                "Patrimonio Total Estimado": total_balance
            })
        return pd.DataFrame(records)

    with tab_cp:
        st.subheader("⚡ Plan de Corto Plazo (Horizonte 3 Años)")
        st.write("Ideal para: Fondo de emergencia de 6 meses, pago total de deudas de alto costo y compras planificadas.")
        df_cp = calculate_projection(3, base_annual_savings, annual_growth_rate)
        
        c_cp1, c_cp2, c_cp3 = st.columns(3)
        with c_cp1:
            st.metric("Aporte Total Estimado (3 Años)", f"${df_cp['Aporte Acumulado'].iloc[-1]:,.2f}")
        with c_cp2:
            st.metric("Rendimiento Proyectado", f"${df_cp['Rendimientos / Interés Compuesto'].iloc[-1]:,.2f}")
        with c_cp3:
            st.metric("Capital Acumulado al Año 3", f"${df_cp['Patrimonio Total Estimado'].iloc[-1]:,.2f}")
            
        fig_cp = px.bar(df_cp, x="Periodo", y=["Aporte Acumulado", "Rendimientos / Interés Compuesto"],
                        color_discrete_sequence=["#00385C", "#00ACA9"])
        fig_cp.update_layout(
            template=chart_template,
            title=dict(text="Evolución Patrimonial - Corto Plazo", x=0.5, xanchor="center", font=dict(color=chart_text, size=14)),
            paper_bgcolor=chart_bg,
            plot_bgcolor=chart_bg
        )
        st.plotly_chart(fig_cp, use_container_width=True)
        st.dataframe(df_cp.style.format({"Aporte Acumulado": "${:,.2f}", "Rendimientos / Interés Compuesto": "${:,.2f}", "Patrimonio Total Estimado": "${:,.2f}"}), use_container_width=True)

    with tab_mp:
        st.subheader("🎯 Plan de Mediano Plazo (Horizonte 5 Años)")
        st.write("Ideal para: Cuota inicial de vivienda, vehículo propio, capitalización de negocios o estudios avanzados.")
        df_mp = calculate_projection(5, base_annual_savings, annual_growth_rate)
        
        c_mp1, c_mp2, c_mp3 = st.columns(3)
        with c_mp1:
            st.metric("Aporte Total Estimado (5 Años)", f"${df_mp['Aporte Acumulado'].iloc[-1]:,.2f}")
        with c_mp2:
            st.metric("Rendimiento Proyectado", f"${df_mp['Rendimientos / Interés Compuesto'].iloc[-1]:,.2f}")
        with c_mp3:
            st.metric("Capital Acumulado al Año 5", f"${df_mp['Patrimonio Total Estimado'].iloc[-1]:,.2f}")
            
        fig_mp = px.area(df_mp, x="Periodo", y="Patrimonio Total Estimado", color_discrete_sequence=["#00ACA9"])
        fig_mp.update_layout(
            template=chart_template,
            title=dict(text="Curva de Crecimiento a 5 Años", x=0.5, xanchor="center", font=dict(color=chart_text, size=14)),
            paper_bgcolor=chart_bg,
            plot_bgcolor=chart_bg
        )
        st.plotly_chart(fig_mp, use_container_width=True)
        st.dataframe(df_mp.style.format({"Aporte Acumulado": "${:,.2f}", "Rendimientos / Interés Compuesto": "${:,.2f}", "Patrimonio Total Estimado": "${:,.2f}"}), use_container_width=True)

    with tab_lp:
        st.subheader("🏔️ Plan de Largo Plazo (Horizonte 10 o más Años)")
        st.write("Ideal para: Libertad financiera, retiro anticipado, portafolios indexados y patrimonio familiar intergeneracional.")
        
        lp_years = st.slider("Seleccionar Horizonte Extendido", min_value=10, max_value=30, value=15, step=1)
        df_lp = calculate_projection(lp_years, base_annual_savings, annual_growth_rate)
        
        c_lp1, c_lp2, c_lp3 = st.columns(3)
        with c_lp1:
            st.metric(f"Aportes Propios ({lp_years} Años)", f"${df_lp['Aporte Acumulado'].iloc[-1]:,.2f}")
        with c_lp2:
            st.metric("Ganancia por Interés Compuesto", f"${df_lp['Rendimientos / Interés Compuesto'].iloc[-1]:,.2f}")
        with c_lp3:
            st.metric("Patrimonio Final Proyectado", f"${df_lp['Patrimonio Total Estimado'].iloc[-1]:,.2f}")
            
        fig_lp = go.Figure()
        fig_lp.add_trace(go.Scatter(x=df_lp["Año"], y=df_lp["Aporte Acumulado"], name="Aporte Acumulado", fill='tozeroy', line=dict(color='#00385C')))
        fig_lp.add_trace(go.Scatter(x=df_lp["Año"], y=df_lp["Patrimonio Total Estimado"], name="Patrimonio Total con Interés Compuesto", fill='tonexty', line=dict(color='#00ACA9')))
        fig_lp.update_layout(
            template=chart_template,
            title=dict(text="Efecto Bola de Nieve a Largo Plazo", x=0.5, xanchor="center", font=dict(color=chart_text, size=14)),
            height=380,
            paper_bgcolor=chart_bg,
            plot_bgcolor=chart_bg
        )
        st.plotly_chart(fig_lp, use_container_width=True)
        st.dataframe(df_lp.style.format({"Aporte Acumulado": "${:,.2f}", "Rendimientos / Interés Compuesto": "${:,.2f}", "Patrimonio Total Estimado": "${:,.2f}"}), use_container_width=True)

# ==========================================
# 9. PANEL DE ADMINISTRACIÓN Y SUPERUSUARIO
# ==========================================
elif menu_selection == "👑 Panel de Administración":
    st.markdown("""
    <div class='main-header-banner'>
      <div class='main-header-title'>OptiBudget Pro — CENTRO DE CONTROL SUPERUSUARIO</div>
      <div class='main-header-subtitle'>Gestión Total de Usuarios, Aprobación, Roles, Notificaciones SMTP y Auditoría Forense</div>
    </div>
    """, unsafe_allow_html=True)
    
    t_list, t_create, t_edit, t_audit = st.tabs([
        "👥 Listado & Aprobación de Usuarios",
        "➕ Crear Nuevo Usuario",
        "✏️ Editar Usuarios Existentes",
        "🛡️ Bitácora de Seguridad & Notificaciones"
    ])
    
    # ------------------------------------------
    # LISTADO Y APROBACIÓN DE TODOS LOS USUARIOS
    # ------------------------------------------
    with t_list:
        st.subheader("Directorio Global de Usuarios Registrados")
        st.info("💡 Como Super Administrador, puedes activar o desactivar el acceso de cualquier usuario marcando la casilla 'Activo'. Los usuarios no aprobados no podrán iniciar sesión.")
        
        all_user_records = []
        for mail, dat in st.session_state.users.items():
            all_user_records.append({
                "Activo": dat.get("is_active", True),
                "Nombre": dat["name"],
                "Correo Electrónico": mail,
                "Rol": dat["role"],
                "Registrado el": dat.get("created_at", "N/A"),
                "Intentos Fallidos": dat["failed_attempts"],
                "Bloqueado": "Sí" if (dat["locked_until"] and datetime.now() < dat["locked_until"]) else "No"
            })
            
        df_users_all = pd.DataFrame(all_user_records)
        
        edited_user_table = st.data_editor(
            df_users_all,
            column_config={
                "Activo": st.column_config.CheckboxColumn("Activo / Aprobado", help="Desmarca para suspender o marca para permitir acceso"),
                "Correo Electrónico": st.column_config.TextColumn("Correo Electrónico", disabled=True),
                "Nombre": st.column_config.TextColumn("Nombre", disabled=True),
                "Rol": st.column_config.TextColumn("Rol", disabled=True),
                "Registrado el": st.column_config.TextColumn("Registrado el", disabled=True),
                "Intentos Fallidos": st.column_config.NumberColumn("Intentos Fallidos", disabled=True),
                "Bloqueado": st.column_config.TextColumn("Bloqueado", disabled=True)
            },
            disabled=["Nombre", "Correo Electrónico", "Rol", "Registrado el", "Intentos Fallidos", "Bloqueado"],
            hide_index=True,
            use_container_width=True,
            key="admin_user_approval_table"
        )
        
        changes_detected = False
        for _, row in edited_user_table.iterrows():
            target_m = row["Correo Electrónico"]
            current_status = st.session_state.users[target_m].get("is_active", True)
            new_status = row["Activo"]
            if current_status != new_status:
                st.session_state.users[target_m]["is_active"] = new_status
                changes_detected = True
                
        if changes_detected:
            st.success("✅ Estado de aprobación actualizado exitosamente.")
            st.rerun()

    # ------------------------------------------
    # CREAR NUEVO USUARIO DESDE EL PANEL
    # ------------------------------------------
    with t_create:
        st.subheader("➕ Dar de Alta un Nuevo Usuario")
        with st.form("form_admin_create_user"):
            new_u_name = st.text_input("Nombre Completo")
            new_u_email = st.text_input("Correo Electrónico").strip().lower()
            new_u_pass = st.text_input("Contraseña Temporal", type="password")
            new_u_role = st.selectbox("Rol Asignado", ["Usuario", "Superusuario"])
            new_u_active = st.checkbox("Activar acceso inmediatamente", value=True)
            btn_create_u = st.form_submit_button("Crear y Registrar Usuario", use_container_width=True)
            
            if btn_create_u:
                if not new_u_name or not new_u_email or not new_u_pass:
                    st.warning("Completa todos los campos obligatorios.")
                elif new_u_email in st.session_state.users:
                    st.error("Este correo ya se encuentra registrado.")
                else:
                    nhash, nsalt = hash_password(new_u_pass)
                    st.session_state.users[new_u_email] = {
                        "name": new_u_name,
                        "role": new_u_role,
                        "hash": nhash,
                        "salt": nsalt,
                        "is_active": new_u_active,
                        "failed_attempts": 0,
                        "locked_until": None,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    init_user_finances(new_u_email)
                    send_security_alert(
                        new_u_email, 
                        "USUARIO REGISTRADO POR ADMIN", 
                        f"Usuario {new_u_name} ({new_u_role}) registrado administrativamente con estado: {'Activo' if new_u_active else 'Inactivo'}."
                    )
                    st.success(f"Usuario {new_u_name} registrado exitosamente.")
                    st.rerun()

    # ------------------------------------------
    # EDITAR USUARIOS EXISTENTES
    # ------------------------------------------
    with t_edit:
        st.subheader("✏️ Modificar o Gestionar Usuario")
        user_emails = list(st.session_state.users.keys())
        sel_u_email = st.selectbox("Seleccione el usuario a editar", user_emails, format_func=lambda x: f"{st.session_state.users[x]['name']} ({x})")
        
        target_u = st.session_state.users[sel_u_email]
        
        with st.form("form_admin_edit_user"):
            st.write(f"Editando cuenta: **{sel_u_email}**")
            ed_u_name = st.text_input("Nombre Completo", value=target_u["name"])
            ed_u_role = st.selectbox("Rol", ["Usuario", "Superusuario"], index=0 if target_u["role"] == "Usuario" else 1)
            ed_u_active = st.checkbox("Cuenta Activa / Permitir Acceso al Sistema", value=target_u.get("is_active", True))
            ed_u_new_pass = st.text_input("Nueva Contraseña (dejar en blanco para no modificarla)", type="password")
            ed_u_unlock = st.checkbox("Restablecer intentos fallidos y desbloquear cuenta", value=True)
            
            c_ed_save, c_ed_del = st.columns(2)
            with c_ed_save:
                btn_save_u = st.form_submit_button("💾 Guardar Modificaciones", use_container_width=True)
            with c_ed_del:
                btn_del_u = st.form_submit_button("🗑️ Eliminar Usuario", use_container_width=True)
                
            if btn_save_u:
                target_u["name"] = ed_u_name
                target_u["role"] = ed_u_role
                target_u["is_active"] = ed_u_active
                if ed_u_unlock:
                    target_u["failed_attempts"] = 0
                    target_u["locked_until"] = None
                if ed_u_new_pass.strip():
                    nhash, nsalt = hash_password(ed_u_new_pass.strip())
                    target_u["hash"] = nhash
                    target_u["salt"] = nsalt
                    send_security_alert(sel_u_email, "CLAVE MODIFICADA POR ADMIN", "Contraseña redefinida administrativamente.")
                    
                st.success(f"Usuario {ed_u_name} actualizado exitosamente.")
                st.rerun()
                
            if btn_del_u:
                if sel_u_email == current_email:
                    st.error("No puedes eliminar la cuenta con la que has iniciado sesión.")
                else:
                    del st.session_state.users[sel_u_email]
                    if sel_u_email in st.session_state.finances:
                        del st.session_state.finances[sel_u_email]
                    send_security_alert(sel_u_email, "USUARIO ELIMINADO", "Cuenta eliminada por el Super Administrador.")
                    st.success("Usuario eliminado del sistema.")
                    st.rerun()

    # ------------------------------------------
    # BITÁCORA Y CONFIGURACIÓN SMTP
    # ------------------------------------------
    with t_audit:
        st.subheader("🛡️ Configuración de Alertas por Correo Electrónico (SMTP)")
        st.info("Configura la cuenta de correo para enviar notificaciones al Administrador cuando ocurran registros de nuevos usuarios, intentos fallidos o incidentes de seguridad.")
        
        cfg = st.session_state.smtp_config
        with st.form("form_smtp_settings"):
            c_sm1, c_sm2 = st.columns(2)
            with c_sm1:
                smtp_server = st.text_input("Servidor SMTP", value=cfg["server"], help="Ej: smtp.gmail.com o smtp.office365.com")
                smtp_sender = st.text_input("Correo Emisor (Remitente)", value=cfg["sender"], placeholder="tu_correo@gmail.com")
                smtp_pass = st.text_input("Contraseña de Aplicación / SMTP", type="password", value=cfg["password"], help="Para Gmail, genera una 'Contraseña de aplicación'")
            with c_sm2:
                smtp_port = st.number_input("Puerto SMTP", value=int(cfg["port"]), step=1)
                smtp_recipient = st.text_input("Correo Notificador (Destinatario)", value=cfg["recipient"], placeholder="admin@tudominio.com")
                smtp_active = st.checkbox("Activar despacho automático de alertas por correo", value=cfg["active"])
                
            c_btn_save, c_btn_test = st.columns(2)
            with c_btn_save:
                btn_save_smtp = st.form_submit_button("💾 Guardar Configuración SMTP", use_container_width=True)
            with c_btn_test:
                btn_test_smtp = st.form_submit_button("✉️ Enviar Correo de Prueba", use_container_width=True)
                
            if btn_save_smtp:
                st.session_state.smtp_config = {
                    "server": smtp_server.strip(),
                    "port": int(smtp_port),
                    "sender": smtp_sender.strip(),
                    "password": smtp_pass.strip(),
                    "recipient": smtp_recipient.strip(),
                    "active": smtp_active
                }
                st.success("Configuración de correo actualizada correctamente.")
                st.rerun()
                
            if btn_test_smtp:
                if not smtp_sender.strip() or not smtp_pass.strip() or not smtp_recipient.strip():
                    st.warning("Completa el remitente, la contraseña y el destinatario antes de enviar una prueba.")
                else:
                    try:
                        test_msg = MIMEMultipart("alternative")
                        test_msg["Subject"] = "✅ [PRUEBA] Notificación de Seguridad OptiBudget Pro"
                        test_msg["From"] = smtp_sender.strip()
                        test_msg["To"] = smtp_recipient.strip()
                        body = "<h3>Prueba de Alerta Exitosa</h3><p>El sistema de notificaciones de OptiBudget Pro está conectado y listo para alertar ante nuevos registros e incidentes.</p>"
                        test_msg.attach(MIMEText(body, "html"))
                        
                        srv = smtplib.SMTP(smtp_server.strip(), int(smtp_port), timeout=8)
                        srv.starttls()
                        srv.login(smtp_sender.strip(), smtp_pass.strip())
                        srv.sendmail(smtp_sender.strip(), smtp_recipient.strip(), test_msg.as_string())
                        srv.quit()
                        st.success(f"¡Correo de prueba enviado con éxito a {smtp_recipient.strip()}!")
                    except Exception as err:
                        st.error(f"Fallo al conectar con el servidor de correo: {err}")

        st.markdown("---")
        st.subheader("📋 Bitácora Forense de Eventos y Notificaciones Despachadas")
        if st.session_state.audit_log:
            df_log = pd.DataFrame(st.session_state.audit_log)
            st.dataframe(df_log, use_container_width=True)
        else:
            st.success("Sin eventos de seguridad registrados.")
