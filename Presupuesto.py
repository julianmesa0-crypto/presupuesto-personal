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
import json
import os
import time
import requests

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="OptiBudget Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "app_theme" not in st.session_state:
    st.session_state.app_theme = "System"

# ==========================================
# 2. PERSISTENCIA EN ARCHIVOS LOCALES
# ==========================================
USERS_FILE = "users_db.json"
FINANCES_FILE = "finances_db.json"
SMTP_FILE = "smtp_db.json"
AUDIT_FILE = "audit_db.json"
SESSIONS_FILE = "sessions_db.json"
SETTINGS_FILE = "settings_db.json"
CATEGORIES_FILE = "categories_db.json"

def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 100000)
    return key.hex(), salt

def verify_password(stored_hash: str, salt: str, password_attempt: str) -> bool:
    attempt_hash = hashlib.pbkdf2_hmac('sha256', password_attempt.encode('utf-8'), bytes.fromhex(salt), 100000).hex()
    return hmac.compare_digest(stored_hash, attempt_hash)

def load_json_file(filepath, default_val):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_val
    return default_val

def save_json_file(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def get_all_users():
    default_admin_hash, default_admin_salt = hash_password("admin123")
    default_user_hash, default_user_salt = hash_password("Welcome123")
    default_users = {
        "admin@optibudget.com": {
            "name": "Super Administrador",
            "role": "Superusuario",
            "hash": default_admin_hash,
            "salt": default_admin_salt,
            "is_active": True,
            "must_change_password": False,
            "failed_attempts": 0,
            "locked_until": None,
            "created_at": "2026-09-21 00:00"
        },
        "usuario@demo.com": {
            "name": "Usuario Demo",
            "role": "Usuario",
            "hash": default_user_hash,
            "salt": default_user_salt,
            "is_active": True,
            "must_change_password": False,
            "locked_until": None,
            "created_at": "2026-09-21 00:00"
        }
    }
    users = load_json_file(USERS_FILE, None)
    if users is None:
        save_json_file(USERS_FILE, default_users)
        return default_users
    return users

def save_all_users(users_dict):
    save_json_file(USERS_FILE, users_dict)

def get_sessions():
    return load_json_file(SESSIONS_FILE, {})

def save_sessions(sessions_dict):
    save_json_file(SESSIONS_FILE, sessions_dict)

def create_user_session(email):
    token = secrets.token_urlsafe(24)
    sessions = get_sessions()
    sessions[token] = {
        "email": email,
        "last_activity": time.time()
    }
    save_sessions(sessions)
    st.query_params["session_token"] = token
    return token

def update_user_activity(token):
    sessions = get_sessions()
    if token in sessions:
        sessions[token]["last_activity"] = time.time()
        save_sessions(sessions)

def destroy_user_session(token):
    sessions = get_sessions()
    if token in sessions:
        del sessions[token]
        save_sessions(sessions)
    if "session_token" in st.query_params:
        del st.query_params["session_token"]

def get_smtp_config():
    default_smtp = {
        "server": "smtp.gmail.com",
        "port": 587,
        "sender": "",
        "password": "",
        "recipient": "admin@optibudget.com",
        "active": False
    }
    return load_json_file(SMTP_FILE, default_smtp)

def save_smtp_config(smtp_dict):
    save_json_file(SMTP_FILE, smtp_dict)

def get_audit_log():
    return load_json_file(AUDIT_FILE, [])

def append_audit_log(entry):
    logs = get_audit_log()
    logs.append(entry)
    save_json_file(AUDIT_FILE, logs)

@st.cache_data(ttl=3600)
def fetch_live_trm_rates():
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=3)
        data = res.json()
        if data and "rates" in data:
            rates = data["rates"]
            usd_cop = rates.get("COP", 4100.0)
            eur_usd = rates.get("EUR", 0.92)
            eur_cop = usd_cop / eur_usd if eur_usd > 0 else 4450.0
            return float(usd_cop), float(eur_cop)
    except Exception:
        pass
    return 4100.0, 4450.0

def get_user_settings(email):
    all_settings = load_json_file(SETTINGS_FILE, {})
    if email not in all_settings:
        live_usd, live_eur = fetch_live_trm_rates()
        all_settings[email] = {
            "currency": "COP",
            "trm_usd_cop": live_usd,
            "trm_eur_cop": live_eur
        }
        save_json_file(SETTINGS_FILE, all_settings)
    return all_settings[email]

def save_user_settings(email, settings_dict):
    all_settings = load_json_file(SETTINGS_FILE, {})
    all_settings[email] = settings_dict
    save_json_file(SETTINGS_FILE, all_settings)

def get_user_categories(email):
    all_cats = load_json_file(CATEGORIES_FILE, {})
    if email not in all_cats:
        all_cats[email] = {
            "clasificaciones": ["Necesidades", "Deseos", "Ahorros"],
            "gastos_variables": [
                "Mercado y Alimentación", "Transporte / Combustible", "Restaurantes y Salidas",
                "Entretenimiento y Ocio", "Salud y Medicamentos", "Mascotas", "Cuidado Personal",
                "Hogar", "Ropa", "Educación", "Misceláneos"
            ]
        }
        save_json_file(CATEGORIES_FILE, all_cats)
    return all_cats[email]

def save_user_categories(email, cats_dict):
    all_cats = load_json_file(CATEGORIES_FILE, {})
    all_cats[email] = cats_dict
    save_json_file(CATEGORIES_FILE, all_cats)

CHRONO_MONTHS = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def create_initial_example_month():
    return {
        "ingresos": [
            {"Check": False, "Descripción": "Salario / Ingreso Principal", "Actual": 0.0}
        ],
        "facturas": [
            {"Descripción": "Renta / Vivienda", "Monto": 0.0, "Tipo": "Necesidades", "Fecha": "01", "Moneda": "COP", "FechaTransaccion": datetime.now().strftime("%Y-%m-%d")}
        ],
        "gastos_var": [
            {"Categoría": "Mercado / Alimentación", "Monto": 0.0, "Tipo": "Necesidades", "Moneda": "COP", "FechaTransaccion": datetime.now().strftime("%Y-%m-%d")}
        ],
        "ahorros": [
            {"Concepto": "Fondo de Emergencia", "Monto": 0.0, "Notas": "Meta inicial", "Moneda": "COP", "FechaTransaccion": datetime.now().strftime("%Y-%m-%d")}
        ],
        "seguimiento": []
    }

def get_all_finances():
    return load_json_file(FINANCES_FILE, {})

def save_all_finances(finances_dict):
    save_json_file(FINANCES_FILE, finances_dict)

def init_user_finances(email):
    current_year = str(datetime.now().year)
    finances = get_all_finances()
    if email not in finances:
        finances[email] = {
            current_year: {
                "Enero": create_initial_example_month()
            }
        }
        save_all_finances(finances)
    elif current_year not in finances[email]:
        finances[email][current_year] = {
            "Enero": create_initial_example_month()
        }
        save_all_finances(finances)

def clone_structure_from_month(source_month_data):
    return {
        "ingresos": [dict(r, Check=False, Actual=0.0) for r in source_month_data.get("ingresos", [])],
        "facturas": [dict(r, Monto=0.0, Moneda=r.get("Moneda", "COP"), FechaTransaccion=datetime.now().strftime("%Y-%m-%d")) for r in source_month_data.get("facturas", [])],
        "gastos_var": [dict(r, Monto=0.0, Moneda=r.get("Moneda", "COP"), FechaTransaccion=datetime.now().strftime("%Y-%m-%d")) for r in source_month_data.get("gastos_var", [])],
        "ahorros": [dict(r, Monto=0.0, Moneda=r.get("Moneda", "COP"), FechaTransaccion=datetime.now().strftime("%Y-%m-%d")) for r in source_month_data.get("ahorros", [])],
        "seguimiento": []
    }

def send_security_alert(target_email, event_type, details):
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_email": target_email,
        "event_type": event_type,
        "details": details,
        "correo_enviado": "No configurado"
    }
    
    cfg = get_smtp_config()
    if cfg["active"] and cfg["sender"] and cfg["password"] and cfg["recipient"]:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 [NOTIFICACIÓN] {event_type} - OptiBudget Pro"
            msg["From"] = cfg["sender"]
            msg["To"] = cfg["recipient"]
            
            html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #CBD5E1; border-radius: 8px;">
              <h2 style="color: #00385C; margin-top: 0;">💼 OptiBudget Pro - Notificación de Seguridad</h2>
              <p>Se ha registrado el siguiente evento en la plataforma:</p>
              <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr style="background: #F8FAFC;"><td style="padding: 8px; font-weight: bold;">Evento:</td><td style="padding: 8px; color: #00ACA9;">{event_type}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Fecha y Hora:</td><td style="padding: 8px;">{log_entry['timestamp']}</td></tr>
                <tr style="background: #F8FAFC;"><td style="padding: 8px; font-weight: bold;">Cuenta Relacionada:</td><td style="padding: 8px;">{target_email}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Detalles:</td><td style="padding: 8px;">{details}</td></tr>
              </table>
              <hr style="border: 0; border-top: 1px solid #CBD5E1;">
              <p style="font-size: 0.85rem; color: #64748B;">Notificación enviada automáticamente a {cfg['recipient']}.</p>
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
            
    append_audit_log(log_entry)

if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "active_module" not in st.session_state:
    st.session_state.active_module = "📅 Presupuesto Mensual"
if "prev_notif_count" not in st.session_state:
    st.session_state.prev_notif_count = 0

all_users = get_all_users()
token_in_url = st.query_params.get("session_token", None)

if token_in_url:
    sessions = get_sessions()
    if token_in_url in sessions:
        session_info = sessions[token_in_url]
        elapsed = time.time() - session_info.get("last_activity", 0)
        if elapsed > 300:
            destroy_user_session(token_in_url)
            st.session_state.current_user = None
            st.warning("⏱️ Sesión cerrada por inactividad (5 minutos transcurridos sin movimiento). Por favor ingresa de nuevo.")
            st.stop()
        else:
            user_candidate = session_info["email"]
            if user_candidate in all_users and all_users[user_candidate].get("is_active", True):
                st.session_state.current_user = user_candidate
                update_user_activity(token_in_url)
            else:
                destroy_user_session(token_in_url)
                st.session_state.current_user = None
    else:
        st.session_state.current_user = None

inactivity_and_sync_js = """
<script>
let idleTime = 0;
const resetTimer = () => { idleTime = 0; };
window.onload = resetTimer;
window.onmousemove = resetTimer;
window.onmousedown = resetTimer;
window.ontouchstart = resetTimer;
window.onclick = resetTimer;
window.onkeypress = resetTimer;
window.addEventListener('scroll', resetTimer, true);

setInterval(() => {
    idleTime += 1;
    if (idleTime >= 300) {
        window.location.reload();
    }
}, 1000);

setTimeout(() => {
    const activeEl = document.activeElement;
    const isTyping = activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA');
    if (!isTyping) {
        window.parent.postMessage({type: 'streamlit:trigger_rerun'}, '*');
    }
}, 8000);
</script>
"""
st.markdown(inactivity_and_sync_js, unsafe_allow_html=True)

# ==========================================
# 4. ESTILOS CSS CON BOTONES ADAPTABLES AL TEMA DEL SISTEMA
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800&display=swap');

html, body, .stApp {
  font-family: 'Nunito Sans', sans-serif !important;
}

[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
  background-color: #29afe2 !important;
  border-right: 1.5px solid #1e98c7 !important;
}

[data-testid="stSidebar"] * {
  color: #FFFFFF !important;
}

[data-testid="stSidebar"] .stSelectbox label, 
[data-testid="stSidebar"] .stNumberInput label,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
  color: #FFFFFF !important;
}

[data-testid="stSidebar"] div[data-baseweb="select"] > div,
[data-testid="stSidebar"] input {
  background-color: #FFFFFF !important;
  color: #00385C !important;
  border-color: #FFFFFF !important;
}

[data-testid="stSidebar"] div[data-baseweb="select"] * {
  color: #00385C !important;
}

.sap-work-center-header {
  font-size: 0.74rem;
  font-weight: 800;
  text-transform: uppercase;
  color: #FFFFFF !important;
  letter-spacing: 1.2px;
  padding: 8px 4px 4px 4px;
  margin-top: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.4);
}

[data-testid="stSidebar"] div.stButton > button {
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
}

[data-testid="stSidebar"] div.stButton > button:hover {
  background-color: #FFFFFF !important;
  color: #00385C !important;
  border-left: 5px solid #00385C !important;
}

[data-testid="stSidebar"] div.stButton > button:hover * {
  color: #00385C !important;
}

.sap-user-card {
  background-color: rgba(0, 56, 92, 0.25) !important;
  border: 1.5px solid rgba(255, 255, 255, 0.45) !important;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 14px;
}

.main-header-banner {
  background: linear-gradient(135deg, #00385C, #0F4F7F) !important;
  color: #FFFFFF !important;
  padding: 1.4rem 2rem;
  border-radius: 12px;
  margin-bottom: 1.2rem;
  text-align: center !important;
  box-shadow: 0 4px 14px rgba(0, 56, 92, 0.12);
}

.main-header-title {
  font-size: 1.85rem;
  font-weight: 800;
  margin: 0 auto !important;
  text-align: center !important;
  color: #FFFFFF !important;
}

.main-header-subtitle {
  font-size: 0.96rem;
  color: #E2E8F0 !important;
  margin-top: 6px;
  text-align: center !important;
}

.kpi-card {
  border-radius: 10px;
  padding: 1rem 0.8rem;
  text-align: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}

.kpi-card-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.kpi-card-value {
  font-size: 1.55rem;
  font-weight: 800;
  margin-top: 0.25rem;
}

.restante-card {
  border: 2px solid #00ACA9 !important;
  border-radius: 10px;
  padding: 1rem 0.8rem;
  text-align: center;
  box-shadow: 0 2px 6px rgba(0, 172, 169, 0.1);
}

.restante-card-label {
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.restante-card-value {
  font-size: 1.6rem;
  font-weight: 800;
  margin-top: 0.25rem;
}

.section-badge {
  font-weight: 800;
  font-size: 0.85rem;
  padding: 6px 12px;
  border-radius: 6px;
  display: inline-block;
  margin-bottom: 0.6rem;
  border-left: 4px solid #00ACA9 !important;
}

.bell-badge {
  background-color: #D74546;
  color: white !important;
  font-weight: 800;
  border-radius: 50%;
  padding: 2px 7px;
  font-size: 0.75rem;
  margin-left: 4px;
}

.notif-box {
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 8px;
  font-weight: 600;
  border-left: 5px solid #00ACA9;
}

@media (prefers-color-scheme: light) {
  div[data-testid="stForm"] button[kind="secondary"], div[data-testid="stForm"] button[kind="primary"] {
    background-color: #FFFFFF !important;
    color: #00385C !important;
    border: 1.5px solid #29afe2 !important;
    box-shadow: 0 4px 12px rgba(41, 175, 226, 0.35) !important;
    font-weight: 800 !important;
  }
}
@media (prefers-color-scheme: dark) {
  div[data-testid="stForm"] button[kind="secondary"], div[data-testid="stForm"] button[kind="primary"] {
    background-color: #00385C !important;
    color: #FFFFFF !important;
    border: 1.5px solid #FFFFFF !important;
    box-shadow: 0 4px 12px rgba(255, 255, 255, 0.25) !important;
    font-weight: 800 !important;
  }
}
</style>
""", unsafe_allow_html=True)

def trigger_bell_sound():
    st.markdown("""
    <script>
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.6);
        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.6);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.6);
    } catch (e) {
        console.log("Audio alert handled.");
    }
    </script>
    """, unsafe_allow_html=True)

# ==========================================
# 5. PANTALLA DE ACCESO (LOGIN & REGISTRO)
# ==========================================
all_users = get_all_users()

if st.session_state.current_user is None or st.session_state.current_user not in all_users:
    st.markdown("""
    <div style='text-align: center; padding: 2.5rem 0 1rem 0;'>
      <h1 style='font-size: 2.4rem; font-weight: 800; margin: 0;'>💼 OptiBudget Pro</h1>
      <p style='font-size: 1.05rem; margin-top: 6px;'>Gestión Financiera Multi-Horizonte con Seguridad Avanzada</p>
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
                    all_users_fresh = get_all_users()
                    if login_email in all_users_fresh:
                        u_data = all_users_fresh[login_email]
                        
                        if not u_data.get("is_active", True):
                            st.warning("⏳ Tu cuenta ha sido registrada pero está pendiente de aprobación por el Administrador. No puedes ingresar hasta que sea validada.")
                        elif u_data.get("locked_until") and datetime.now() < datetime.strptime(u_data["locked_until"], "%Y-%m-%d %H:%M:%S"):
                            st.error(f"⛔ Cuenta bloqueada por seguridad hasta {u_data['locked_until']}.")
                        else:
                            if verify_password(u_data["hash"], u_data["salt"], login_pass):
                                u_data["failed_attempts"] = 0
                                u_data["locked_until"] = None
                                all_users_fresh[login_email] = u_data
                                save_all_users(all_users_fresh)
                                
                                create_user_session(login_email)
                                st.session_state.current_user = login_email
                                init_user_finances(login_email)
                                st.success("Acceso autorizado con éxito.")
                                st.rerun()
                            else:
                                u_data["failed_attempts"] = u_data.get("failed_attempts", 0) + 1
                                if u_data["failed_attempts"] >= 3:
                                    lock_time = datetime.now() + timedelta(minutes=15)
                                    u_data["locked_until"] = lock_time.strftime("%Y-%m-%d %H:%M:%S")
                                    all_users_fresh[login_email] = u_data
                                    save_all_users(all_users_fresh)
                                    send_security_alert(login_email, "INTROMISIÓN DETECTADA / BLOQUEO", "3 intentos fallidos consecutivos.")
                                    st.error("⛔ Demasiados intentos fallidos. Cuenta bloqueada por 15 minutos.")
                                else:
                                    all_users_fresh[login_email] = u_data
                                    save_all_users(all_users_fresh)
                                    send_security_alert(login_email, "INTENTO FALLIDO", f"Intento #{u_data['failed_attempts']}")
                                    st.warning(f"Credenciales incorrectas. Intentos restantes: {3 - u_data['failed_attempts']}.")
                    else:
                        st.error("Credenciales inválidas. Verifica tu correo.")

        with tab_reg:
            with st.form("form_register"):
                reg_name = st.text_input("Nombre Completo")
                reg_email = st.text_input("Correo Electrónico").strip().lower()
                st.info("🔑 Por política del sistema, tu contraseña inicial asignada será: **Welcome123**. Tras ser activado por el Administrador, se te solicitará cambiarla obligatoriamente en tu primer ingreso.")
                btn_reg = st.form_submit_button("Crear Cuenta", use_container_width=True)
                
                if btn_reg:
                    all_users_fresh = get_all_users()
                    if not reg_name or not reg_email:
                        st.warning("Por favor completa tu nombre y correo electrónico.")
                    elif reg_email in all_users_fresh:
                        st.error("El correo ya se encuentra registrado.")
                    else:
                        phash, psalt = hash_password("Welcome123")
                        all_users_fresh[reg_email] = {
                            "name": reg_name.strip(),
                            "role": "Usuario",
                            "hash": phash,
                            "salt": psalt,
                            "is_active": False,
                            "must_change_password": True,
                            "failed_attempts": 0,
                            "locked_until": None,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        save_all_users(all_users_fresh)
                        init_user_finances(reg_email)
                        
                        send_security_alert(
                            reg_email, 
                            "NUEVO USUARIO PENDIENTE DE APROBACIÓN", 
                            f"El usuario {reg_name} ({reg_email}) se ha registrado. Requiere activación en el panel de administración."
                        )
                        st.success("✅ Cuenta registrada exitosamente. Guardada en el servidor y correo enviado al Administrador. Podrás ingresar con 'Welcome123' tan pronto el Superusuario apruebe tu cuenta.")
    st.stop()

# ==========================================
# 6. OBLIGACIÓN DE CAMBIO DE CONTRASEÑA EN PRIMER INGRESO
# ==========================================
all_users = get_all_users()
current_email = st.session_state.current_user
user_info = all_users[current_email]

if user_info.get("must_change_password", False):
    st.markdown(f"""
    <div class='main-header-banner'>
      <div class='main-header-title'>ACTUALIZACIÓN OBLIGATORIA DE CONTRASEÑA</div>
      <div class='main-header-subtitle'>Hola {user_info['name']}, tu cuenta fue aprobada con la clave provisional. Por seguridad debes definir tu contraseña personal definitiva para continuar.</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_pc1, col_pc2, col_pc3 = st.columns([1, 1.4, 1])
    with col_pc2:
        with st.form("form_force_new_password"):
            new_pass1 = st.text_input("Nueva Contraseña", type="password")
            new_pass2 = st.text_input("Confirmar Nueva Contraseña", type="password")
            btn_save_first_pass = st.form_submit_button("Establecer Contraseña y Acceder", use_container_width=True)
            
            if btn_save_first_pass:
                if not new_pass1 or len(new_pass1) < 6:
                    st.warning("La contraseña debe tener al menos 6 caracteres.")
                elif new_pass1 == "Welcome123":
                    st.error("No puedes reutilizar la contraseña temporal 'Welcome123'.")
                elif new_pass1 != new_pass2:
                    st.error("Las contraseñas no coinciden.")
                else:
                    nhash, nsalt = hash_password(new_pass1)
                    user_info["hash"] = nhash
                    user_info["salt"] = nsalt
                    user_info["must_change_password"] = False
                    all_users[current_email] = user_info
                    save_all_users(all_users)
                    st.success("✅ Contraseña actualizada correctamente. ¡Bienvenido a OptiBudget Pro!")
                    st.rerun()
    st.stop()

# ==========================================
# 7. MENÚ LATERAL ESTILO SAP BYDESIGN & CONFIGURACIÓN
# ==========================================
is_admin = user_info["role"] == "Superusuario"
init_user_finances(current_email)
all_finances = get_all_finances()
user_fin = all_finances.get(current_email, {})
user_sets = get_user_settings(current_email)
user_cats = get_user_categories(current_email)

notifications = []
now = datetime.now()
current_sys_year = str(now.year)
current_sys_month = CHRONO_MONTHS[now.month - 1]

if is_admin:
    pending_users = [mail for mail, u in all_users.items() if not u.get("is_active", False)]
    if pending_users:
        notifications.append({
            "text": f"Hay <b>{len(pending_users)}</b> usuario(s) pendiente(s) de aprobación.",
            "is_approval": True
        })

if current_sys_year not in user_fin:
    notifications.append({
        "text": f"Estamos en el año <b>{current_sys_year}</b> y aún no has creado este año fiscal.",
        "is_approval": False
    })
elif current_sys_month not in user_fin[current_sys_year]:
    notifications.append({
        "text": f"Ha comenzado <b>{current_sys_month} {current_sys_year}</b> y aún no has creado este mes.",
        "is_approval": False
    })

notif_count = len(notifications)
if notif_count > st.session_state.prev_notif_count:
    trigger_bell_sound()
st.session_state.prev_notif_count = notif_count

with st.sidebar:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 4px;'>
      <div style='font-size: 1.35rem;'>💼</div>
      <div>
        <div style='font-size: 1.15rem; font-weight: 800; color: #FFFFFF !important; line-height: 1.1;'>OptiBudget Pro</div>
        <div style='font-size: 0.72rem; color: #FFFFFF !important; text-transform: uppercase; letter-spacing: 0.8px;'>By Soltein Julian Mesa Holguin</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"🔔 Notificaciones y Tareas {f'({notif_count})' if notif_count > 0 else ''}", expanded=(notif_count > 0)):
        if notifications:
            for idx, n in enumerate(notifications):
                st.markdown(f"<div class='notif-box'>⚠️ {n['text']}</div>", unsafe_allow_html=True)
                if n["is_approval"]:
                    if st.button("👉 Ir a Aprobar Usuarios Ahora", key=f"link_aprob_{idx}", use_container_width=True):
                        st.session_state.active_module = "👑 Panel de Administración"
                        st.rerun()
        else:
            st.success("✅ No tienes tareas pendientes. ¡Todo al día!")

    st.markdown(f"""
    <div class='sap-user-card'>
      <div style='font-size: 0.68rem; color: #FFFFFF !important; font-weight: 800; text-transform: uppercase;'>Usuario Activo</div>
      <div style='font-size: 0.98rem; color: #FFFFFF !important; font-weight: 800;'>{user_info['name']}</div>
      <div style='font-size: 0.78rem; color: #FFFFFF !important;'>{current_email}</div>
      <div style='margin-top: 5px;'><span style='background: #00385C; color: #FFFFFF !important; padding: 2px 7px; border-radius: 4px; font-size: 0.68rem; font-weight: 800;'>{user_info['role']}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # CONFIGURACIÓN DE MONEDA Y TRM
    st.markdown("<div class='sap-work-center-header'>Configuración Monetaria & TRM</div>", unsafe_allow_html=True)
    if st.button("🌐 Sincronizar TRM de Internet", use_container_width=True):
        live_u, live_e = fetch_live_trm_rates()
        user_sets["trm_usd_cop"] = live_u
        user_sets["trm_eur_cop"] = live_e
        save_user_settings(current_email, user_sets)
        st.success("¡TRM sincronizada en línea!")
        st.rerun()

    with st.form("form_currency_settings"):
        curr_options = ["COP", "USD", "EUR"]
        selected_curr = st.selectbox("Moneda Principal", curr_options, index=curr_options.index(user_sets.get("currency", "COP")))
        trm_usd = st.number_input("TRM USD a COP", value=float(user_sets.get("trm_usd_cop", 4100.0)), step=10.0)
        trm_eur = st.number_input("TRM EUR a COP", value=float(user_sets.get("trm_eur_cop", 4450.0)), step=10.0)
        
        if st.form_submit_button("Actualizar Divisa", use_container_width=True):
            user_sets["currency"] = selected_curr
            user_sets["trm_usd_cop"] = trm_usd
            user_sets["trm_eur_cop"] = trm_eur
            save_user_settings(current_email, user_sets)
            st.success("Moneda principal actualizada.")
            st.rerun()

    main_curr = user_sets.get("currency", "COP")
    u_val = user_sets.get('trm_usd_cop', 4100)
    e_val = user_sets.get('trm_eur_cop', 4450)
    
    if main_curr == "COP":
        trm_display_html = f"1 USD = ${u_val:,.1f} COP<br>1 EUR = ${e_val:,.1f} COP"
    elif main_curr == "USD":
        eur_vs_usd = (e_val / u_val) if u_val > 0 else 1.08
        cop_vs_usd = (1.0 / u_val) if u_val > 0 else 0.00024
        trm_display_html = f"1 USD = ${u_val:,.1f} COP<br>1 EUR = ${eur_vs_usd:,.2f} USD<br>1 COP = ${cop_vs_usd:,.5f} USD"
    else:
        usd_vs_eur = (u_val / e_val) if e_val > 0 else 0.92
        cop_vs_eur = (1.0 / e_val) if e_val > 0 else 0.00022
        trm_display_html = f"1 EUR = ${e_val:,.1f} COP<br>1 USD = ${usd_vs_eur:,.2f} EUR<br>1 COP = ${cop_vs_eur:,.5f} EUR"

    st.markdown(f"""
    <div style='background: rgba(255,255,255,0.12); padding: 8px; border-radius: 6px; font-size: 0.8rem; margin-top: 6px; text-align: center;'>
      <b>Relación TRM ({main_curr}):</b><br>
      {trm_display_html}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='sap-work-center-header'>Centro de Trabajo (Módulos)</div>", unsafe_allow_html=True)

    module_list = [
        ("📅 Presupuesto Mensual", "Ejecución y Gestión"),
        ("📊 Resumen Anual", "Consolidado Fiscal"),
        ("📈 Horizontes Financieros", "Proyección 3, 5, 10+ Años"),
        ("🏷️ Categorías & Clasificaciones", "Gestión de Etiquetas")
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
    st.markdown("<div class='sap-work-center-header'>Período Fiscal & Parámetros</div>", unsafe_allow_html=True)

    created_years = sorted(list(user_fin.keys()))
    if not created_years:
        created_years = [current_sys_year]
        user_fin[current_sys_year] = {"Enero": create_initial_example_month()}
        all_finances[current_email] = user_fin
        save_all_finances(all_finances)

    if "current_sel_year" not in st.session_state or st.session_state.current_sel_year not in created_years:
        st.session_state.current_sel_year = created_years[-1]
    
    sel_year = st.selectbox("Año Fiscal Activo", created_years, index=created_years.index(st.session_state.current_sel_year))
    st.session_state.current_sel_year = sel_year

    with st.expander("➕ Crear Nuevo Año"):
        with st.form("form_create_year"):
            next_suggested_year = int(max(created_years)) + 1 if created_years else int(current_sys_year)
            new_year_input = st.number_input("Año a crear", min_value=2020, max_value=2099, value=next_suggested_year, step=1)
            btn_create_year = st.form_submit_button("Crear Año", use_container_width=True)
            
            if btn_create_year:
                s_year = str(new_year_input)
                if s_year in user_fin:
                    st.warning(f"El año {s_year} ya existe.")
                else:
                    user_fin[s_year] = {
                        "Enero": create_initial_example_month()
                    }
                    all_finances[current_email] = user_fin
                    save_all_finances(all_finances)
                    st.session_state.current_sel_year = s_year
                    st.success(f"¡Año {s_year} creado!")
                    st.rerun()

    months_in_active_year = [m for m in CHRONO_MONTHS if m in user_fin.get(sel_year, {})]
    if not months_in_active_year:
        user_fin[sel_year] = {"Enero": create_initial_example_month()}
        all_finances[current_email] = user_fin
        save_all_finances(all_finances)
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
                    cloned_data = clone_structure_from_month(source_data)
                    user_fin[sel_year][next_month_to_create] = cloned_data
                    all_finances[current_email] = user_fin
                    save_all_finances(all_finances)
                    st.session_state.current_sel_month = next_month_to_create
                    st.success(f"¡Mes {next_month_to_create} creado!")
                    st.rerun()
    else:
        st.caption("✅ Todos los meses de este año están creados.")

    with st.expander("🗑️ Eliminar Mes"):
        with st.form("form_delete_specific_month"):
            month_to_del = st.selectbox("Seleccione el mes a eliminar", months_in_active_year)
            btn_del_month = st.form_submit_button("Borrar Mes Seleccionado", use_container_width=True)
            if btn_del_month:
                if len(months_in_active_year) <= 1:
                    st.error("No puedes eliminar el único mes restante del año.")
                else:
                    del user_fin[sel_year][month_to_del]
                    all_finances[current_email] = user_fin
                    save_all_finances(all_finances)
                    st.success(f"Mes {month_to_del} eliminado correctamente.")
                    st.rerun()

    with st.expander("🗑️ Eliminar Año"):
        with st.form("form_delete_specific_year"):
            year_to_del = st.selectbox("Seleccione el año a eliminar", created_years)
            btn_del_year = st.form_submit_button("Borrar Año Seleccionado", use_container_width=True)
            if btn_del_year:
                if len(created_years) <= 1:
                    st.error("No puedes eliminar el único año fiscal existente.")
                else:
                    del user_fin[year_to_del]
                    all_finances[current_email] = user_fin
                    save_all_finances(all_finances)
                    st.success(f"Año {year_to_del} eliminado correctamente.")
                    st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        token_active = st.query_params.get("session_token", None)
        if token_active:
            destroy_user_session(token_active)
        st.session_state.current_user = None
        st.rerun()

def convert_to_main_currency(amount, transaction_currency, sets):
    main_curr = sets.get("currency", "COP")
    trm_usd = float(sets.get("trm_usd_cop", 4100.0))
    trm_eur = float(sets.get("trm_eur_cop", 4450.0))
    
    amount_in_cop = amount
    if transaction_currency == "USD":
        amount_in_cop = amount * trm_usd
    elif transaction_currency == "EUR":
        amount_in_cop = amount * trm_eur
    elif transaction_currency == "COP":
        amount_in_cop = amount
        
    if main_curr == "COP":
        return amount_in_cop
    elif main_curr == "USD":
        return amount_in_cop / trm_usd if trm_usd > 0 else amount_in_cop
    elif main_curr == "EUR":
        return amount_in_cop / trm_eur if trm_eur > 0 else amount_in_cop
    return amount_in_cop

def format_money(val, curr_code):
    if curr_code == "COP":
        return f"${int(round(val)):,}"
    elif curr_code == "USD":
        return f"US${val:,.2f}"
    elif curr_code == "EUR":
        return f"€{val:,.2f}"
    return f"${val:,.2f}"

curr_code = user_sets.get("currency", "COP")
curr_symbol = {"COP": "$", "USD": "US$", "EUR": "€"}.get(curr_code, "$")

# ==========================================
# 8. VISTA: PRESUPUESTO MENSUAL
# ==========================================
if menu_selection == "📅 Presupuesto Mensual":
    raw_month = user_fin[sel_year][sel_month]
    
    df_ing = pd.DataFrame(raw_month.get("ingresos", []))
    if "Presupuesto" in df_ing.columns:
        df_ing = df_ing.drop(columns=["Presupuesto"])
    if df_ing.empty:
        df_ing = pd.DataFrame([{"Check": False, "Descripción": "Salario Principal", "Actual": 0.0}])
        
    df_fac = pd.DataFrame(raw_month.get("facturas", []))
    df_var = pd.DataFrame(raw_month.get("gastos_var", []))
    df_ah = pd.DataFrame(raw_month.get("ahorros", []))
    df_seg = pd.DataFrame(raw_month.get("seguimiento", []))
    if df_seg.empty:
        df_seg = pd.DataFrame(columns=["Monto", "Categoría", "Fecha", "Detalle", "Moneda", "FechaTransaccion"])
        
    total_ingreso_act = float(df_ing["Actual"].sum()) if not df_ing.empty and "Actual" in df_ing.columns else 0.0
    total_facturas = float(df_fac["Monto"].sum()) if not df_fac.empty and "Monto" in df_fac.columns else 0.0
    total_var = float(df_var["Monto"].sum()) if not df_var.empty and "Monto" in df_var.columns else 0.0
    total_seg = float(df_seg["Monto"].sum()) if not df_seg.empty and "Monto" in df_seg.columns else 0.0
    total_ahorro = float(df_ah["Monto"].sum()) if not df_ah.empty and "Monto" in df_ah.columns else 0.0
    
    total_gastado = total_facturas + total_var + total_seg
    dinero_restante = total_ingreso_act - total_gastado - total_ahorro
    
    fac_nec = df_fac[df_fac["Tipo"].isin([c for c in user_cats["clasificaciones"]])]["Monto"].sum() if not df_fac.empty else 0.0
    # Usar clasificaciones dinámicas
    class_list = user_cats["clasificaciones"]
    primary_class = class_list[0] if class_list else "Necesidades"
    secondary_class = class_list[1] if len(class_list) > 1 else "Deseos"

    fac_nec = df_fac[df_fac["Tipo"] == primary_class]["Monto"].sum() if not df_fac.empty else 0.0
    var_nec = df_var[df_var["Tipo"] == primary_class]["Monto"].sum() if not df_var.empty else 0.0
    nec_total = fac_nec + var_nec
    
    fac_des = df_fac[df_fac["Tipo"] == secondary_class]["Monto"].sum() if not df_fac.empty else 0.0
    var_des = df_var[df_var["Tipo"] == secondary_class]["Monto"].sum() if not df_var.empty else 0.0
    des_total = fac_des + var_des
    
    st.markdown(f"""
    <div class='main-header-banner'>
      <div class='main-header-title'>OptiBudget Pro — {sel_month.upper()} {sel_year}</div>
      <div class='main-header-subtitle'>Moneda Principal: {curr_code} | Gestión en Tiempo Real</div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Ingreso Total Recibido</div>
          <div class='kpi-card-value'>{format_money(total_ingreso_act, curr_code)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Total Gastado (Fijo + Var)</div>
          <div class='kpi-card-value'>{format_money(total_gastado, curr_code)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Total Ahorrado / Invertido</div>
          <div class='kpi-card-value'>{format_money(total_ahorro, curr_code)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class='restante-card'>
          <div class='restante-card-label'>Dinero Restante Disponible</div>
          <div class='restante-card-value'>{format_money(dinero_restante, curr_code)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
    
    # EXPORTACIÓN
    with st.expander("📥 Exportar Información Financiera (Excel / CSV)"):
        with st.form("form_export_data"):
            exp_scope = st.selectbox("Alcance de Exportación", ["Mes Actual (" + sel_month + " " + sel_year + ")", "Todo el Año (" + sel_year + ")", "Historial Completo"])
            exp_format = st.selectbox("Formato de Archivo", ["Excel (.xlsx)", "CSV (.csv)"])
            btn_export = st.form_submit_button("Generar Archivo de Exportación", use_container_width=True)
            
            if btn_export:
                export_dfs = {}
                if "Mes Actual" in exp_scope:
                    export_dfs["Ingresos"] = df_ing
                    export_dfs["Facturas"] = df_fac
                    export_dfs["Gastos Variables"] = df_var
                    export_dfs["Ahorros"] = df_ah
                    export_dfs["Seguimiento Diario"] = df_seg
                elif "Todo el Año" in exp_scope:
                    combined_ing, combined_fac, combined_var, combined_ah, combined_seg = [], [], [], [], []
                    for m_name in months_in_active_year:
                        m_data = user_fin[sel_year][m_name]
                        if m_data.get("ingresos"):
                            for r in m_data["ingresos"]:
                                combined_ing.append(dict(r, Mes=m_name))
                        if m_data.get("facturas"):
                            for r in m_data["facturas"]:
                                combined_fac.append(dict(r, Mes=m_name))
                        if m_data.get("gastos_var"):
                            for r in m_data["gastos_var"]:
                                combined_var.append(dict(r, Mes=m_name))
                        if m_data.get("ahorros"):
                            for r in m_data["ahorros"]:
                                combined_ah.append(dict(r, Mes=m_name))
                        if m_data.get("seguimiento"):
                            for r in m_data["seguimiento"]:
                                combined_seg.append(dict(r, Mes=m_name))
                    export_dfs["Ingresos Anuales"] = pd.DataFrame(combined_ing)
                    export_dfs["Facturas Anuales"] = pd.DataFrame(combined_fac)
                    export_dfs["Gastos Anuales"] = pd.DataFrame(combined_var)
                    export_dfs["Ahorros Anuales"] = pd.DataFrame(combined_ah)
                    export_dfs["Seguimiento Anual"] = pd.DataFrame(combined_seg)
                else:
                    all_hist = []
                    for y_key, y_val in user_fin.items():
                        for m_key, m_val in y_val.items():
                            if m_val.get("facturas"):
                                for r in m_val["facturas"]:
                                    all_hist.append(dict(r, Año=y_key, Mes=m_key))
                    export_dfs["Historial Completo Facturas"] = pd.DataFrame(all_hist)

                if "Excel" in exp_format:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        for sheet_name, dframe in export_dfs.items():
                            if not dframe.empty:
                                dframe.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                    processed_data = output.getvalue()
                    st.download_button(
                        label="⬇️ Descargar Archivo Excel (.xlsx)",
                        data=processed_data,
                        file_name=f"OptiBudget_Pro_Export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    first_df = list(export_dfs.values())[0] if export_dfs else pd.DataFrame()
                    csv_data = first_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Descargar Archivo CSV (.csv)",
                        data=csv_data,
                        file_name=f"OptiBudget_Pro_Export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )

    g_col1, g_col2 = st.columns(2)
    with g_col1:
        df_pie = pd.DataFrame({
            "Categoría": [f"{primary_class}", f"{secondary_class}", "Ahorros"],
            "Monto": [nec_total, des_total, total_ahorro]
        })
        fig_pie = px.pie(df_pie, names="Categoría", values="Monto" if df_pie["Monto"].sum() > 0 else [1,1,1], hole=0.55,
                         color_discrete_sequence=["#00385C", "#31B4D1", "#00ACA9"])
        fig_pie.update_layout(
            title=dict(text=f"Distribución Presupuestaria ({curr_code})", x=0.5, xanchor="center", font=dict(size=14)),
            margin=dict(t=40, b=10, l=10, r=10),
            height=250
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with g_col2:
        fig_bar = go.Figure(data=[
            go.Bar(name='Ingresos', x=['Mes'], y=[total_ingreso_act], marker_color='#00ACA9'),
            go.Bar(name='Gastos', x=['Mes'], y=[total_gastado], marker_color='#D74546'),
            go.Bar(name='Ahorros', x=['Mes'], y=[total_ahorro], marker_color='#00385C')
        ])
        fig_bar.update_layout(
            barmode='group',
            title=dict(text=f"Comparativa Flujo de Caja ({curr_code})", x=0.5, xanchor="center", font=dict(size=14)),
            margin=dict(t=40, b=10, l=10, r=10),
            height=250
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("<div class='section-badge'>💵 1. INGRESOS (VALOR RECIBIDO)</div>", unsafe_allow_html=True)
        st.caption(f"Valores expresados en su moneda principal ({curr_code}).")
        edited_ing = st.data_editor(
            df_ing,
            column_config={
                "Check": st.column_config.CheckboxColumn("✓", default=False),
                "Descripción": st.column_config.TextColumn("Descripción"),
                "Actual": st.column_config.NumberColumn(f"Actual ({curr_symbol})", format=f"{curr_symbol}%.2f")
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"ing_{sel_year}_{sel_month}"
        )
        if not edited_ing.equals(df_ing):
            raw_month["ingresos"] = edited_ing.to_dict(orient="records")
            user_fin[sel_year][sel_month] = raw_month
            all_finances[current_email] = user_fin
            save_all_finances(all_finances)
            st.rerun()

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        st.markdown("<div class='section-badge'>📑 2. FACTURAS (GASTOS FIJOS)</div>", unsafe_allow_html=True)
        st.caption("🔒 Protegida contra edición accidental. Usa los botones inferiores.")
        df_fac_display = df_fac.copy()
        if not df_fac_display.empty and "Monto" in df_fac_display.columns:
            df_fac_display["Monto"] = df_fac_display["Monto"].apply(lambda x: format_money(x, curr_code))
        st.dataframe(df_fac_display, use_container_width=True)

        with st.expander("➕ Añadir Concepto de Factura (Con TRM y Fecha)"):
            with st.form(f"form_add_fac_{sel_year}_{sel_month}"):
                new_f_desc = st.text_input("Descripción (ej. Renta, Agua, Luz)")
                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    raw_f_monto = st.number_input("Monto en origen", min_value=0.0, step=10.0, format="%.2f")
                with c_m2:
                    tx_curr = st.selectbox("Moneda", ["COP", "USD", "EUR"], key="fac_tx_curr")
                
                new_f_tipo = st.selectbox("Clasificación", user_cats["clasificaciones"])
                trans_date = st.date_input("Fecha de Transacción", value=datetime.now())
                
                btn_add_f = st.form_submit_button("Agregar Factura con TRM", use_container_width=True)
                
                if btn_add_f:
                    if new_f_desc.strip():
                        converted_monto = convert_to_main_currency(raw_f_monto, tx_curr, user_sets)
                        date_str = trans_date.strftime("%Y-%m-%d")
                        new_row = {
                            "Descripción": f"{new_f_desc.strip()} ({raw_f_monto:,.2f} {tx_curr})", 
                            "Monto": converted_monto, 
                            "Tipo": new_f_tipo, 
                            "Fecha": trans_date.strftime("%d"), 
                            "Moneda": tx_curr,
                            "FechaTransaccion": date_str
                        }
                        df_fac = pd.concat([df_fac, pd.DataFrame([new_row])], ignore_index=True)
                        raw_month["facturas"] = df_fac.to_dict(orient="records")
                        user_fin[sel_year][sel_month] = raw_month
                        all_finances[current_email] = user_fin
                        save_all_finances(all_finances)
                        st.success(f"Factura agregada y convertida a {curr_code} ({format_money(converted_monto, curr_code)}).")
                        st.rerun()
                    else:
                        st.warning("Escribe una descripción.")

        with st.expander("✏️ Lápiz de Edición: Modificar Factura"):
            if not df_fac.empty:
                f_options = [f"{idx} - {row['Descripción']}" for idx, row in df_fac.iterrows()]
                selected_f_idx = st.selectbox("Seleccione factura", options=range(len(f_options)), format_func=lambda x: f_options[x], key=f"sel_f_{sel_year}_{sel_month}")
                
                current_f = df_fac.iloc[selected_f_idx]
                with st.form(f"form_edit_fac_{sel_year}_{sel_month}"):
                    edit_f_desc = st.text_input("Descripción", value=current_f["Descripción"])
                    edit_f_monto = st.number_input(f"Monto ({curr_code})", min_value=0.0, value=float(current_f["Monto"]), step=10.0, format="%.2f")
                    edit_f_tipo = st.selectbox("Clasificación", user_cats["clasificaciones"], index=0 if current_f["Tipo"] in user_cats["clasificaciones"] else 0)
                    edit_f_fecha = st.text_input("Fecha", value=str(current_f["Fecha"]))
                    
                    c_save, c_del = st.columns(2)
                    with c_save:
                        btn_save_f = st.form_submit_button("💾 Guardar", use_container_width=True)
                    with c_del:
                        btn_del_f = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
                        
                    if btn_save_f:
                        df_fac.at[selected_f_idx, "Descripción"] = edit_f_desc
                        df_fac.at[selected_f_idx, "Monto"] = edit_f_monto
                        df_fac.at[selected_f_idx, "Tipo"] = edit_f_tipo
                        df_fac.at[selected_f_idx, "Fecha"] = edit_f_fecha
                        raw_month["facturas"] = df_fac.to_dict(orient="records")
                        user_fin[sel_year][sel_month] = raw_month
                        all_finances[current_email] = user_fin
                        save_all_finances(all_finances)
                        st.success("Factura actualizada.")
                        st.rerun()
                        
                    if btn_del_f:
                        df_fac = df_fac.drop(index=selected_f_idx).reset_index(drop=True)
                        raw_month["facturas"] = df_fac.to_dict(orient="records")
                        user_fin[sel_year][sel_month] = raw_month
                        all_finances[current_email] = user_fin
                        save_all_finances(all_finances)
                        st.success("Factura eliminada.")
                        st.rerun()
            else:
                st.info("Sin facturas para editar.")

    with col_der:
        st.markdown("<div class='section-badge'>🛒 3. GASTOS VARIABLES</div>", unsafe_allow_html=True)
        st.caption("🔒 Protegida contra edición accidental. Usa los botones inferiores.")
        df_var_display = df_var.copy()
        if not df_var_display.empty and "Monto" in df_var_display.columns:
            df_var_display["Monto"] = df_var_display["Monto"].apply(lambda x: format_money(x, curr_code))
        st.dataframe(df_var_display, use_container_width=True)

        with st.expander("➕ Añadir Categoría de Gasto Variable (Con TRM y Fecha)"):
            with st.form(f"form_add_gv_{sel_year}_{sel_month}"):
                new_gv_cat = st.selectbox("Categoría de Gasto", user_cats["gastos_variables"])
                c_v1, c_v2 = st.columns(2)
                with c_v1:
                    raw_v_monto = st.number_input("Monto en origen", min_value=0.0, step=10.0, format="%.2f", key="gv_raw_monto")
                with c_v2:
                    tx_curr_v = st.selectbox("Moneda", ["COP", "USD", "EUR"], key="gv_tx_curr")
                
                new_gv_tipo = st.selectbox("Clasificación", user_cats["clasificaciones"], key=f"new_gv_tipo_{sel_year}_{sel_month}")
                trans_date_v = st.date_input("Fecha de Transacción", value=datetime.now(), key="gv_date")
                
                btn_add_gv = st.form_submit_button("Agregar Categoría con TRM", use_container_width=True)
                
                if btn_add_gv:
                    if new_gv_cat.strip():
                        converted_v = convert_to_main_currency(raw_v_monto, tx_curr_v, user_sets)
                        date_str_v = trans_date_v.strftime("%Y-%m-%d")
                        new_row = {
                            "Categoría": f"{new_gv_cat.strip()} ({raw_v_monto:,.2f} {tx_curr_v})", 
                            "Monto": converted_v, 
                            "Tipo": new_gv_tipo, 
                            "Moneda": tx_curr_v,
                            "FechaTransaccion": date_str_v
                        }
                        df_var = pd.concat([df_var, pd.DataFrame([new_row])], ignore_index=True)
                        raw_month["gastos_var"] = df_var.to_dict(orient="records")
                        user_fin[sel_year][sel_month] = raw_month
                        all_finances[current_email] = user_fin
                        save_all_finances(all_finances)
                        st.success(f"Gasto variable agregado y convertido a {curr_code} ({format_money(converted_v, curr_code)}).")
                        st.rerun()
                    else:
                        st.warning("Selecciona una categoría.")

        with st.expander("✏️ Lápiz de Edición: Modificar Gasto Variable"):
            if not df_var.empty:
                gv_options = [f"{idx} - {row['Categoría']}" for idx, row in df_var.iterrows()]
                selected_gv_idx = st.selectbox("Seleccione categoría", options=range(len(gv_options)), format_func=lambda x: gv_options[x], key=f"sel_gv_{sel_year}_{sel_month}")
                
                current_gv = df_var.iloc[selected_gv_idx]
                with st.form(f"form_edit_gv_{sel_year}_{sel_month}"):
                    edit_gv_cat = st.text_input("Categoría", value=current_gv["Categoría"])
                    edit_gv_monto = st.number_input(f"Monto ({curr_code})", min_value=0.0, value=float(current_gv["Monto"]), step=10.0, format="%.2f")
                    edit_gv_tipo = st.selectbox("Clasificación", user_cats["clasificaciones"], index=0 if current_gv["Tipo"] in user_cats["clasificaciones"] else 0, key=f"ed_gv_tipo_{sel_year}_{sel_month}")
                    
                    c_save, c_del = st.columns(2)
                    with c_save:
                        btn_save_gv = st.form_submit_button("💾 Guardar", use_container_width=True)
                    with c_del:
                        btn_del_gv = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
                        
                    if btn_save_gv:
                        df_var.at[selected_gv_idx, "Categoría"] = edit_gv_cat
                        df_var.at[selected_gv_idx, "Monto"] = edit_gv_monto
                        df_var.at[selected_gv_idx, "Tipo"] = edit_gv_tipo
                        raw_month["gastos_var"] = df_var.to_dict(orient="records")
                        user_fin[sel_year][sel_month] = raw_month
                        all_finances[current_email] = user_fin
                        save_all_finances(all_finances)
                        st.success("Categoría actualizada.")
                        st.rerun()
                        
                    if btn_del_gv:
                        df_var = df_var.drop(index=selected_gv_idx).reset_index(drop=True)
                        raw_month["gastos_var"] = df_var.to_dict(orient="records")
                        user_fin[sel_year][sel_month] = raw_month
                        all_finances[current_email] = user_fin
                        save_all_finances(all_finances)
                        st.success("Categoría eliminada.")
                        st.rerun()
            else:
                st.info("Sin categorías para editar.")

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        st.markdown("<div class='section-badge'>🎯 4. AHORROS E INVERSIÓN (20%)</div>", unsafe_allow_html=True)
        st.caption("🔒 Protegida contra edición accidental. Usa los botones inferiores.")
        df_ah_display = df_ah.copy()
        if not df_ah_display.empty and "Monto" in df_ah_display.columns:
            df_ah_display["Monto"] = df_ah_display["Monto"].apply(lambda x: format_money(x, curr_code))
        st.dataframe(df_ah_display, use_container_width=True)

        with st.expander("➕ Añadir Meta de Ahorro (Con TRM)"):
            with st.form(f"form_add_ah_{sel_year}_{sel_month}"):
                new_ah_con = st.text_input("Concepto (ej. Fondo de Emergencia, Inversión)")
                c_a1, c_a2 = st.columns(2)
                with c_a1:
                    raw_a_monto = st.number_input("Monto origen", min_value=0.0, step=10.0, format="%.2f", key="ah_raw_monto")
                with c_a2:
                    tx_curr_a = st.selectbox("Moneda", ["COP", "USD", "EUR"], key="ah_tx_curr")
                
                new_ah_notas = st.text_input("Notas / Plazo", value="Meta personal")
                trans_date_a = st.date_input("Fecha", value=datetime.now(), key="ah_date")
                
                btn_add_ah = st.form_submit_button("Agregar Meta con TRM", use_container_width=True)
                
                if btn_add_ah:
                    if new_ah_con.strip():
                        converted_a = convert_to_main_currency(raw_a_monto, tx_curr_a, user_sets)
                        date_str_a = trans_date_a.strftime("%Y-%m-%d")
                        new_row = {
                            "Concepto": f"{new_ah_con.strip()} ({raw_a_monto:,.2f} {tx_curr_a})", 
                            "Monto": converted_a, 
                            "Notas": new_ah_notas, 
                            "Moneda": tx_curr_a,
                            "FechaTransaccion": date_str_a
                        }
                        df_ah = pd.concat([df_ah, pd.DataFrame([new_row])], ignore_index=True)
                        raw_month["ahorros"] = df_ah.to_dict(orient="records")
                        user_fin[sel_year][sel_month] = raw_month
                        all_finances[current_email] = user_fin
                        save_all_finances(all_finances)
                        st.success(f"Meta agregada con fecha {date_str_a} y convertida a {curr_code} ({format_money(converted_a, curr_code)}).")
                        st.rerun()
                    else:
                        st.warning("Escribe un concepto.")

        with st.expander("✏️ Lápiz de Edición: Modificar Meta de Ahorro"):
            if not df_ah.empty:
                ah_options = [f"{idx} - {row['Concepto']}" for idx, row in df_ah.iterrows()]
                selected_ah_idx = st.selectbox("Seleccione meta", options=range(len(ah_options)), format_func=lambda x: ah_options[x], key=f"sel_ah_{sel_year}_{sel_month}")
                
                current_ah = df_ah.iloc[selected_ah_idx]
                with st.form(f"form_edit_ah_{sel_year}_{sel_month}"):
                    edit_ah_con = st.text_input("Concepto", value=current_ah["Concepto"])
                    edit_ah_monto = st.number_input(f"Monto ({curr_code})", min_value=0.0, value=float(current_ah["Monto"]), step=10.0, format="%.2f")
                    edit_ah_notas = st.text_input("Notas", value=str(current_ah["Notas"]))
                    
                    c_save, c_del = st.columns(2)
                    with c_save:
                        btn_save_ah = st.form_submit_button("💾 Guardar", use_container_width=True)
                    with c_del:
                        btn_del_ah = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
                        
                    if btn_save_ah:
                        df_ah.at[selected_ah_idx, "Concepto"] = edit_ah_con
                        df_ah.at[selected_ah_idx, "Monto"] = edit_ah_monto
                        df_ah.at[selected_ah_idx, "Notas"] = edit_ah_notas
                        raw_month["ahorros"] = df_ah.to_dict(orient="records")
                        user_fin[sel_year][sel_month] = raw_month
                        all_finances[current_email] = user_fin
                        save_all_finances(all_finances)
                        st.success("Meta actualizada.")
                        st.rerun()
                        
                    if btn_del_ah:
                        df_ah = df_ah.drop(index=selected_ah_idx).reset_index(drop=True)
                        raw_month["ahorros"] = df_ah.to_dict(orient="records")
                        user_fin[sel_year][sel_month] = raw_month
                        all_finances[current_email] = user_fin
                        save_all_finances(all_finances)
                        st.success("Meta eliminada.")
                        st.rerun()
            else:
                st.info("Sin metas de ahorro registradas.")

    st.markdown("---")

    # ==========================================
    # SECCIÓN 5: SEGUIMIENTO DE TRANSACCIONES (2 COLUMNAS + LÁPIZ EDICIÓN/ELIMINACIÓN)
    # ==========================================
    st.markdown("<div class='section-badge'>📝 5. SEGUIMIENTO DE GASTOS DIARIOS</div>", unsafe_allow_html=True)
    col_tx_list, col_tx_form = st.columns([1.3, 1])
    
    with col_tx_list:
        if not df_seg.empty and "Monto" in df_seg.columns:
            df_seg_disp = df_seg.copy()
            df_seg_disp["Monto"] = df_seg_disp["Monto"].apply(lambda x: format_money(x, curr_code))
            st.dataframe(df_seg_disp, use_container_width=True)
        else:
            st.info("Aún no has registrado transacciones diarias este mes.")

        # Lápiz de edición y eliminación para Seguimiento de Gastos Diarios
        with st.expander("✏️ Lápiz de Edición / Eliminación: Gasto Diario"):
            if not df_seg.empty:
                seg_options = [f"{idx} - [{row.get('FechaTransaccion', 'N/A')}] {row['Categoría']}: {format_money(row['Monto'], curr_code)}" for idx, row in df_seg.iterrows()]
                selected_seg_idx = st.selectbox("Seleccione transacción", options=range(len(seg_options)), format_func=lambda x: seg_options[x], key=f"sel_seg_{sel_year}_{sel_month}")
                
                current_seg = df_seg.iloc[selected_seg_idx]
                with st.form(f"form_edit_seg_{sel_year}_{sel_month}"):
                    edit_seg_monto = st.number_input(f"Monto ({curr_code})", min_value=0.0, value=float(current_seg["Monto"]), step=5.0, format="%.2f")
                    edit_seg_cat = st.selectbox("Categoría", user_cats["gastos_variables"], index=0 if current_seg["Categoría"] in user_cats["gastos_variables"] else 0)
                    edit_seg_det = st.text_input("Detalle", value=str(current_seg.get("Detalle", "")))
                    
                    c_s_save, c_s_del = st.columns(2)
                    with c_s_save:
                        btn_save_seg = st.form_submit_button("💾 Guardar", use_container_width=True)
                    with c_s_del:
                        btn_del_seg = st.form_submit_button("🗑️ Eliminar Gasto", use_container_width=True)
                        
                    if btn_save_seg:
                        df_seg.at[selected_seg_idx, "Monto"] = edit_seg_monto
                        df_seg.at[selected_seg_idx, "Categoría"] = edit_seg_cat
                        df_seg.at[selected_seg_idx, "Detalle"] = edit_seg_det
                        raw_month["seguimiento"] = df_seg.to_dict(orient="records")
                        user_fin[sel_year][sel_month] = raw_month
                        all_finances[current_email] = user_fin
                        save_all_finances(all_finances)
                        st.success("Gasto diario actualizado.")
                        st.rerun()
                        
                    if btn_del_seg:
                        df_seg = df_seg.drop(index=selected_seg_idx).reset_index(drop=True)
                        raw_month["seguimiento"] = df_seg.to_dict(orient="records")
                        user_fin[sel_year][sel_month] = raw_month
                        all_finances[current_email] = user_fin
                        save_all_finances(all_finances)
                        st.success("Gasto diario eliminado.")
                        st.rerun()
            else:
                st.info("Sin transacciones para editar.")

    with col_tx_form:
        with st.form(f"form_add_seg_{sel_year}_{sel_month}"):
            st.markdown("**➕ Registrar Transacción (Con TRM y Fecha)**")
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                raw_seg_monto = st.number_input("Monto origen", min_value=0.0, step=5.0, format="%.2f", key="seg_raw_monto")
            with c_s2:
                tx_curr_s = st.selectbox("Moneda", ["COP", "USD", "EUR"], key="seg_tx_curr")
                
            seg_cat = st.selectbox("Categoría", user_cats["gastos_variables"])
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                trans_date_s = st.date_input("Fecha", value=datetime.now(), key="seg_date")
            with c_d2:
                seg_det = st.text_input("Detalle", placeholder="Comercio / Nota")
                
            btn_add_seg = st.form_submit_button("Registrar con TRM", use_container_width=True)
            if btn_add_seg:
                if raw_seg_monto > 0:
                    converted_seg = convert_to_main_currency(raw_seg_monto, tx_curr_s, user_sets)
                    date_str_s = trans_date_s.strftime("%Y-%m-%d")
                    new_tx = {
                        "Monto": converted_seg, 
                        "Categoría": seg_cat, 
                        "Fecha": trans_date_s.strftime("%d"), 
                        "Detalle": f"{seg_det} ({raw_seg_monto:,.2f} {tx_curr_s})" if seg_det else f"({raw_seg_monto:,.2f} {tx_curr_s})",
                        "Moneda": tx_curr_s,
                        "FechaTransaccion": date_str_s
                    }
                    df_seg = pd.concat([df_seg, pd.DataFrame([new_tx])], ignore_index=True)
                    raw_month["seguimiento"] = df_seg.to_dict(orient="records")
                    user_fin[sel_year][sel_month] = raw_month
                    all_finances[current_email] = user_fin
                    save_all_finances(all_finances)
                    st.success(f"Transacción registrada con fecha {date_str_s} y convertida a {curr_code} ({format_money(converted_seg, curr_code)}).")
                    st.rerun()
                else:
                    st.warning("El monto debe ser superior al valor 0.")

# ==========================================
# 9. VISTA: RESUMEN ANUAL CONSOLIDADO
# ==========================================
elif menu_selection == "📊 Resumen Anual":
    st.markdown(f"""
    <div class='main-header-banner'>
      <div class='main-header-title'>OptiBudget Pro — CONSOLIDADO ANUAL {sel_year}</div>
      <div class='main-header-subtitle'>Rendimiento y Ejecución Financiera ({curr_code})</div>
    </div>
    """, unsafe_allow_html=True)
    
    summary_data = []
    for m in months_in_active_year:
        d = user_fin[sel_year][m]
        d_ing = pd.DataFrame(d.get("ingresos", []))
        d_fac = pd.DataFrame(d.get("facturas", []))
        d_var = pd.DataFrame(d.get("gastos_var", []))
        d_seg = pd.DataFrame(d.get("seguimiento", []))
        d_aho = pd.DataFrame(d.get("ahorros", []))
        
        ing = float(d_ing["Actual"].sum()) if not d_ing.empty and "Actual" in d_ing.columns else 0.0
        fac = float(d_fac["Monto"].sum()) if not d_fac.empty and "Monto" in d_fac.columns else 0.0
        var = float(d_var["Monto"].sum()) if not d_var.empty and "Monto" in d_var.columns else 0.0
        seg = float(d_seg["Monto"].sum()) if not d_seg.empty and "Monto" in d_seg.columns else 0.0
        aho = float(d_aho["Monto"].sum()) if not d_aho.empty and "Monto" in d_aho.columns else 0.0
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
          <div class='kpi-card-value'>{format_money(tot_ing, curr_code)}</div>
        </div>
        """, unsafe_allow_html=True)
    with ca2:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Gastos Totales {sel_year}</div>
          <div class='kpi-card-value'>{format_money(tot_gas, curr_code)}</div>
        </div>
        """, unsafe_allow_html=True)
    with ca3:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Ahorro Acumulado {sel_year}</div>
          <div class='kpi-card-value'>{format_money(tot_aho, curr_code)}</div>
        </div>
        """, unsafe_allow_html=True)
    with ca4:
        st.markdown(f"""
        <div class='restante-card'>
          <div class='restante-card-label'>Superávit Neto Anual</div>
          <div class='restante-card-value'>{format_money(tot_flu, curr_code)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
    
    if not df_annual.empty:
        fig_an = go.Figure()
        fig_an.add_trace(go.Bar(x=df_annual["Mes"], y=df_annual["Ingresos"], name="Ingresos", marker_color="#00ACA9"))
        fig_an.add_trace(go.Bar(x=df_annual["Mes"], y=df_annual["Gastos"], name="Gastos", marker_color="#D74546"))
        fig_an.add_trace(go.Bar(x=df_annual["Mes"], y=df_annual["Ahorros"], name="Ahorros", marker_color="#00385C"))
        fig_an.update_layout(
            barmode='group',
            title=dict(text=f"Comportamiento Mes a Mes ({sel_year})", x=0.5, xanchor="center", font=dict(size=14)),
            height=340
        )
        st.plotly_chart(fig_an, use_container_width=True)
        
        df_annual_formatted = df_annual.copy()
        for col in ["Ingresos", "Gastos", "Ahorros", "Flujo Neto"]:
            df_annual_formatted[col] = df_annual_formatted[col].apply(lambda x: format_money(x, curr_code))
        st.dataframe(df_annual_formatted, use_container_width=True)

# ==========================================
# 10. VISTA: HORIZONTES FINANCIEROS
# ==========================================
elif menu_selection == "📈 Horizontes Financieros":
    st.markdown("""
    <div class='main-header-banner'>
      <div class='main-header-title'>OptiBudget Pro — PLANIFICACIÓN PLURIANUAL</div>
      <div class='main-header-subtitle'>Proyección Estratégica en Moneda Principal</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab_cp, tab_mp, tab_lp = st.tabs([
        "⚡ Corto Plazo (3 Años)",
        "🎯 Mediano Plazo (5 Años)",
        "🏔️ Largo Plazo (10 o más Años)"
    ])
    
    curr_aho = sum([float(pd.DataFrame(user_fin[sel_year][m].get("ahorros", [])).get("Monto", pd.Series([0.0])).sum()) for m in months_in_active_year])
    
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        base_annual_savings = st.number_input(f"Ahorro / Inversión Anual Base ({curr_symbol})", min_value=0.0, value=float(curr_aho) if curr_aho > 0 else 3000.0, step=500.0)
    with col_sim2:
        annual_growth_rate = st.slider("Tasa de Crecimiento / Rendimiento Anual Estimado (%)", min_value=1.0, max_value=25.0, value=8.0, step=0.5)

    def calculate_projection(years_count, base_savings, rate_pct):
        r = rate_pct / 100.0
        records = []
        cumulative_principal = 0.0
        total_balance = 0.0
        start_year = int(sel_year)
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
        df_cp = calculate_projection(3, base_annual_savings, annual_growth_rate)
        
        c_cp1, c_cp2, c_cp3 = st.columns(3)
        with c_cp1:
            st.metric("Aporte Total", format_money(df_cp['Aporte Acumulado'].iloc[-1], curr_code))
        with c_cp2:
            st.metric("Rendimiento", format_money(df_cp['Rendimientos / Interés Compuesto'].iloc[-1], curr_code))
        with c_cp3:
            st.metric("Capital Total", format_money(df_cp['Patrimonio Total Estimado'].iloc[-1], curr_code))
            
        fig_cp = px.bar(df_cp, x="Periodo", y=["Aporte Acumulado", "Rendimientos / Interés Compuesto"], color_discrete_sequence=["#00385C", "#00ACA9"])
        fig_cp.update_layout(title=dict(text="Evolución - Corto Plazo", x=0.5, xanchor="center", font=dict(size=14)))
        st.plotly_chart(fig_cp, use_container_width=True)
        st.dataframe(df_cp.style.format({"Aporte Acumulado": lambda x: format_money(x, curr_code), "Rendimientos / Interés Compuesto": lambda x: format_money(x, curr_code), "Patrimonio Total Estimado": lambda x: format_money(x, curr_code)}), use_container_width=True)

    with tab_mp:
        st.subheader("🎯 Plan de Mediano Plazo (Horizonte 5 Años)")
        df_mp = calculate_projection(5, base_annual_savings, annual_growth_rate)
        
        c_mp1, c_mp2, c_mp3 = st.columns(3)
        with c_mp1:
            st.metric("Aporte Total", format_money(df_mp['Aporte Acumulado'].iloc[-1], curr_code))
        with c_mp2:
            st.metric("Rendimiento", format_money(df_mp['Rendimientos / Interés Compuesto'].iloc[-1], curr_code))
        with c_mp3:
            st.metric("Capital Total", format_money(df_mp['Patrimonio Total Estimado'].iloc[-1], curr_code))
            
        fig_mp = px.area(df_mp, x="Periodo", y="Patrimonio Total Estimado", color_discrete_sequence=["#00ACA9"])
        fig_mp.update_layout(title=dict(text="Curva - Mediano Plazo", x=0.5, xanchor="center", font=dict(size=14)))
        st.plotly_chart(fig_mp, use_container_width=True)
        st.dataframe(df_mp.style.format({"Aporte Acumulado": lambda x: format_money(x, curr_code), "Rendimientos / Interés Compuesto": lambda x: format_money(x, curr_code), "Patrimonio Total Estimado": lambda x: format_money(x, curr_code)}), use_container_width=True)

    with tab_lp:
        st.subheader("🏔️ Plan de Largo Plazo (Horizonte 10 o más Años)")
        lp_years = st.slider("Seleccionar Horizonte Extendido", min_value=10, max_value=30, value=15, step=1)
        df_lp = calculate_projection(lp_years, base_annual_savings, annual_growth_rate)
        
        c_lp1, c_lp2, c_lp3 = st.columns(3)
        with c_lp1:
            st.metric("Aportes Propios", format_money(df_lp['Aporte Acumulado'].iloc[-1], curr_code))
        with c_lp2:
            st.metric("Ganancia Compuesta", format_money(df_lp['Rendimientos / Interés Compuesto'].iloc[-1], curr_code))
        with c_lp3:
            st.metric("Patrimonio Final", format_money(df_lp['Patrimonio Total Estimado'].iloc[-1], curr_code))
            
        fig_lp = go.Figure()
        fig_lp.add_trace(go.Scatter(x=df_lp["Año"], y=df_lp["Aporte Acumulado"], name="Aporte Acumulado", fill='tozeroy', line=dict(color='#00385C')))
        fig_lp.add_trace(go.Scatter(x=df_lp["Año"], y=df_lp["Patrimonio Total Estimado"], name="Patrimonio Total", fill='tonexty', line=dict(color='#00ACA9')))
        fig_lp.update_layout(title=dict(text="Efecto Bola de Nieve", x=0.5, xanchor="center", font=dict(size=14)), height=380)
        st.plotly_chart(fig_lp, use_container_width=True)
        st.dataframe(df_lp.style.format({"Aporte Acumulado": lambda x: format_money(x, curr_code), "Rendimientos / Interés Compuesto": lambda x: format_money(x, curr_code), "Patrimonio Total Estimado": lambda x: format_money(x, curr_code)}), use_container_width=True)

# ==========================================
# 11. NUEVO MÓDULO: CATEGORÍAS & CLASIFICACIONES
# ==========================================
elif menu_selection == "🏷️ Categorías & Clasificaciones":
    st.markdown("""
    <div class='main-header-banner'>
      <div class='main-header-title'>OptiBudget Pro — GESTIÓN DE ETIQUETAS Y CATEGORÍAS</div>
      <div class='main-header-subtitle'>Personaliza las clasificaciones (ej. Necesidades) y los tipos de gastos variables de tu presupuesto</div>
    </div>
    """, unsafe_allow_html=True)
    
    t_class, t_vars = st.tabs(["🏷️ Gestionar Clasificaciones (50/30/20)", "🛒 Gestionar Gastos Variables"])
    
    with t_class:
        st.subheader("Clasificaciones Presupuestarias Activas")
        st.info("Puedes agregar nuevas etiquetas de clasificación para tus gastos y facturas (ej. Necesidades, Deseos, Inversión, etc.).")
        
        current_classes = user_cats.get("clasificaciones", ["Necesidades", "Deseos", "Ahorros"])
        df_class = pd.DataFrame({"Clasificación": current_classes})
        
        edited_class = st.data_editor(
            df_class,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_clasificaciones"
        )
        
        if st.button("💾 Guardar Cambios en Clasificaciones", use_container_width=True):
            new_list = [c.strip() for c in edited_class["Clasificación"].tolist() if str(c).strip()]
            if new_list:
                user_cats["clasificaciones"] = new_list
                save_user_categories(current_email, user_cats)
                st.success("¡Clasificaciones actualizadas con éxito!")
                st.rerun()
            else:
                st.warning("Debe existir al menos una clasificación.")

    with t_vars:
        st.subheader("Listado de Categorías de Gastos Variables")
        st.info("Personaliza las categorías que aparecen al registrar tus gastos variables y transacciones diarias.")
        
        current_vars = user_cats.get("gastos_variables", [])
        df_vars = pd.DataFrame({"Categoría": current_vars})
        
        edited_vars = st.data_editor(
            df_vars,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_gastos_variables"
        )
        
        if st.button("💾 Guardar Cambios en Gastos Variables", use_container_width=True):
            new_v_list = [v.strip() for v in edited_vars["Categoría"].tolist() if str(v).strip()]
            if new_v_list:
                user_cats["gastos_variables"] = new_v_list
                save_user_categories(current_email, user_cats)
                st.success("¡Categorías de gastos variables actualizadas con éxito!")
                st.rerun()
            else:
                st.warning("Debe existir al menos una categoría.")

# ==========================================
# 12. PANEL DE ADMINISTRACIÓN
# ==========================================
elif menu_selection == "👑 Panel de Administración":
    st.markdown("""
    <div class='main-header-banner'>
      <div class='main-header-title'>OptiBudget Pro — CENTRO DE CONTROL SUPERUSUARIO</div>
      <div class='main-header-subtitle'>Gestión de Usuarios, Aprobación y Seguridad SMTP</div>
    </div>
    """, unsafe_allow_html=True)
    
    t_list, t_create, t_edit, t_audit = st.tabs([
        "👥 Listado & Aprobación de Usuarios",
        "➕ Crear Nuevo Usuario",
        "✏️ Editar Usuarios Existentes",
        "🛡️ Bitácora de Seguridad & Notificaciones"
    ])
    
    with t_list:
        st.subheader("Directorio Global de Usuarios Registrados")
        all_users_fresh = get_all_users()
        all_user_records = []
        for mail, dat in all_users_fresh.items():
            all_user_records.append({
                "Activo": dat.get("is_active", True),
                "Nombre": dat["name"],
                "Correo Electrónico": mail,
                "Rol": dat["role"],
                "Registrado el": dat.get("created_at", "N/A")
            })
            
        df_users_all = pd.DataFrame(all_user_records)
        edited_user_table = st.data_editor(
            df_users_all,
            column_config={
                "Activo": st.column_config.CheckboxColumn("Activo / Aprobado"),
                "Correo Electrónico": st.column_config.TextColumn("Correo", disabled=True),
                "Nombre": st.column_config.TextColumn("Nombre", disabled=True),
                "Rol": st.column_config.TextColumn("Rol", disabled=True),
                "Registrado el": st.column_config.TextColumn("Fecha", disabled=True)
            },
            disabled=["Nombre", "Correo Electrónico", "Rol", "Registrado el"],
            hide_index=True,
            use_container_width=True,
            key="admin_user_approval_table"
        )
        
        changes_detected = False
        for _, row in edited_user_table.iterrows():
            target_m = row["Correo Electrónico"]
            current_status = all_users_fresh[target_m].get("is_active", True)
            new_status = row["Activo"]
            if current_status != new_status:
                all_users_fresh[target_m]["is_active"] = new_status
                changes_detected = True
                
        if changes_detected:
            save_all_users(all_users_fresh)
            st.success("✅ Estado de aprobación actualizado.")
            st.rerun()

    with t_create:
        st.subheader("➕ Dar de Alta un Nuevo Usuario")
        with st.form("form_admin_create_user"):
            new_u_name = st.text_input("Nombre Completo")
            new_u_email = st.text_input("Correo Electrónico").strip().lower()
            new_u_role = st.selectbox("Rol Asignado", ["Usuario", "Superusuario"])
            new_u_active = st.checkbox("Activar acceso inmediatamente", value=True)
            btn_create_u = st.form_submit_button("Crear Usuario", use_container_width=True)
            
            if btn_create_u:
                all_users_fresh = get_all_users()
                if not new_u_name or not new_u_email:
                    st.warning("Completa los campos obligatorios.")
                elif new_u_email in all_users_fresh:
                    st.error("Este correo ya existe.")
                else:
                    nhash, nsalt = hash_password("Welcome123")
                    all_users_fresh[new_u_email] = {
                        "name": new_u_name.strip(),
                        "role": new_u_role,
                        "hash": nhash,
                        "salt": nsalt,
                        "is_active": new_u_active,
                        "must_change_password": True,
                        "failed_attempts": 0,
                        "locked_until": None,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    save_all_users(all_users_fresh)
                    init_user_finances(new_u_email)
                    st.success(f"Usuario {new_u_name} creado con contraseña 'Welcome123'.")
                    st.rerun()

    with t_edit:
        st.subheader("✏️ Modificar Usuario")
        all_users_fresh = get_all_users()
        user_emails = list(all_users_fresh.keys())
        if "last_selected_edit_user" not in st.session_state:
            st.session_state.last_selected_edit_user = user_emails[0] if user_emails else ""
            
        sel_u_email = st.selectbox("Seleccione usuario", user_emails, format_func=lambda x: f"{all_users_fresh[x]['name']} ({x})", key="sel_user_edit")
        if sel_u_email != st.session_state.last_selected_edit_user:
            st.session_state.last_selected_edit_user = sel_u_email
            st.rerun()
            
        target_u = all_users_fresh[sel_u_email]
        with st.form(f"form_edit_{sel_u_email}"):
            ed_u_name = st.text_input("Nombre", value=target_u["name"], key=f"name_{sel_u_email}")
            ed_u_active = st.checkbox("Activo", value=target_u.get("is_active", True), key=f"active_{sel_u_email}")
            ed_u_pass = st.text_input("Nueva Contraseña (opcional)", type="password", key=f"pass_{sel_u_email}")
            
            if st.form_submit_button("💾 Guardar", use_container_width=True):
                target_u["name"] = ed_u_name.strip()
                target_u["is_active"] = ed_u_active
                if ed_u_pass.strip():
                    nhash, nsalt = hash_password(ed_u_pass.strip())
                    target_u["hash"] = nhash
                    target_u["salt"] = nsalt
                all_users_fresh[sel_u_email] = target_u
                save_all_users(all_users_fresh)
                st.success("Modificaciones guardadas.")
                st.rerun()

    with t_audit:
        st.subheader("🛡️ Configuración SMTP & Bitácora")
        cfg = get_smtp_config()
        with st.form("form_smtp"):
            smtp_server = st.text_input("Servidor SMTP", value=cfg["server"])
            smtp_sender = st.text_input("Remitente", value=cfg["sender"])
            smtp_pass = st.text_input("Contraseña", type="password", value=cfg["password"])
            smtp_port = st.number_input("Puerto", value=int(cfg["port"]))
            smtp_recip = st.text_input("Destinatario", value=cfg["recipient"])
            smtp_act = st.checkbox("Activar", value=cfg["active"])
            if st.form_submit_button("Guardar SMTP", use_container_width=True):
                save_smtp_config({"server": smtp_server, "port": int(smtp_port), "sender": smtp_sender, "password": smtp_pass, "recipient": smtp_recip, "active": smtp_act})
                st.success("SMTP guardado.")
                st.rerun()
