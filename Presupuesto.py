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
    page_title="Presupuesto 50/30/20 Plus",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. ESTILOS CSS PERSONALIZADOS (PALETA ESPECIFICADA)
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700&display=swap');

:root {
  --font-family-base: 'Nunito Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  --color-primary: #00385C;
  --color-primary-soft: #E5F6FF;
  --color-primary-pale: #F5FBFF;
  --color-primary-fore: #032033;
  --color-primary-deep: #0F4F7F;
  --color-primary-inverted: #FFFFFF;

  --color-secondary: #A0DFF7;
  --color-secondary-soft: #E7F6FD;
  --color-secondary-pale: #F5FCFE;
  --color-secondary-fore: #0A405F;
  --color-secondary-deep: #18688D;
  --color-secondary-inverted: #FFFFFF;

  --color-accent: #00ACA9;
  --color-accent-soft: #E5FFFE;
  --color-accent-pale: #F5FFFF;
  --color-accent-fore: #083332;
  --color-accent-deep: #186664;
  --color-accent-inverted: #FFFFFF;

  --color-terciary: #31B4D1;
  --color-terciary-soft: #D5EFF5;
  --color-terciary-pale: #F7FCFD;
  --color-terciary-fore: #0F363E;
  --color-terciary-deep: #227C92;
  --color-terciary-inverted: #FFFFFF;

  --color-neutral-text: #2D3439;
  --color-neutral-lite: #EDEDED;
  --color-surface: #FFFFFF;
  --color-border-subtle: #EBEBEB;

  --color-success: #28A745;
  --color-success-soft: #EAFAEE;
  --color-warning: #F9C039;
  --color-warning-soft: #FDECCE;
  --color-error: #D74546;
  --color-error-soft: #FAEAEA;
}

html, body, [class*="css"] {
  font-family: var(--font-family-base) !important;
  color: var(--color-neutral-text);
  background-color: var(--color-surface);
}

.main-header-banner {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-deep));
  color: var(--color-primary-inverted);
  padding: 1.4rem 2rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 14px rgba(0, 56, 92, 0.12);
}

.main-header-title {
  font-size: 1.8rem;
  font-weight: 700;
  margin: 0;
  color: #FFFFFF;
}

.main-header-subtitle {
  font-size: 0.95rem;
  opacity: 0.88;
  margin-top: 4px;
}

.kpi-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: 10px;
  padding: 1rem 1.2rem;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}

.kpi-card-label {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-secondary-deep);
  letter-spacing: 0.5px;
}

.kpi-card-value {
  font-size: 1.55rem;
  font-weight: 700;
  color: var(--color-primary);
  margin-top: 0.25rem;
}

.restante-card {
  background: linear-gradient(135deg, var(--color-accent-soft), var(--color-accent-pale));
  border: 1.5px solid var(--color-accent);
  border-radius: 10px;
  padding: 1rem 1.2rem;
  text-align: center;
}

.restante-card-label {
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-accent-fore);
}

.restante-card-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--color-accent-deep);
  margin-top: 0.2rem;
}

.section-badge {
  background-color: var(--color-primary-soft);
  color: var(--color-primary-fore);
  font-weight: 700;
  font-size: 0.9rem;
  padding: 6px 14px;
  border-radius: 6px;
  display: inline-block;
  margin-bottom: 0.8rem;
  border-left: 4px solid var(--color-primary);
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SEGURIDAD Y GESTIÓN DE SESIONES
# ==========================================
def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 100000)
    return key.hex(), salt

def verify_password(stored_hash: str, salt: str, password_attempt: str) -> bool:
    attempt_hash = hashlib.pbkdf2_hmac('sha256', password_attempt.encode('utf-8'), bytes.fromhex(salt), 100000).hex()
    return hmac.compare_digest(stored_hash, attempt_hash)

def init_system_state():
    if "users" not in st.session_state:
        admin_hash, admin_salt = hash_password("admin123")
        user_hash, user_salt = hash_password("123456")
        st.session_state.users = {
            "admin@presupuesto.com": {
                "name": "Super Administrador",
                "role": "Superusuario",
                "hash": admin_hash,
                "salt": admin_salt,
                "failed_attempts": 0,
                "locked_until": None
            },
            "usuario@demo.com": {
                "name": "Usuario Demo",
                "role": "Usuario",
                "hash": user_hash,
                "salt": user_salt,
                "failed_attempts": 0,
                "locked_until": None
            }
        }
    if "finances" not in st.session_state:
        st.session_state.finances = {}
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []
    if "smtp_config" not in st.session_state:
        st.session_state.smtp_config = {
            "server": "smtp.gmail.com",
            "port": 587,
            "sender": "alertas.seguridad@midominio.com",
            "password": "",
            "recipient": "admin@presupuesto.com",
            "active": False
        }

init_system_state()

MONTHS = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def init_user_finances(email):
    if email not in st.session_state.finances:
        user_data = {}
        for m in MONTHS:
            user_data[m] = {
                "ingresos": pd.DataFrame([
                    {"Check": True, "Descripción": "Salario Principal", "Presupuesto": 1400.0, "Actual": 1400.0},
                    {"Check": False, "Descripción": "Ingreso Secundario", "Presupuesto": 0.0, "Actual": 0.0},
                    {"Check": False, "Descripción": "Otros Ingresos", "Presupuesto": 0.0, "Actual": 0.0}
                ]),
                "facturas": pd.DataFrame([
                    {"Check": True, "Descripción": "Renta", "Presupuesto": 400.0, "Actual": 400.0, "Tipo": "Necesidades", "Fecha": "15"},
                    {"Check": True, "Descripción": "Agua", "Presupuesto": 50.0, "Actual": 50.0, "Tipo": "Necesidades", "Fecha": "18"},
                    {"Check": True, "Descripción": "Internet", "Presupuesto": 30.0, "Actual": 30.0, "Tipo": "Necesidades", "Fecha": "24"},
                    {"Check": True, "Descripción": "Netflix", "Presupuesto": 15.0, "Actual": 15.0, "Tipo": "Deseos", "Fecha": "19"},
                    {"Check": False, "Descripción": "Electricidad", "Presupuesto": 45.0, "Actual": 0.0, "Tipo": "Necesidades", "Fecha": "28"}
                ]),
                "gastos_var": pd.DataFrame([
                    {"Check": True, "Categoría": "Mercado", "Presupuesto": 150.0, "Actual": 100.0, "Tipo": "Necesidades"},
                    {"Check": False, "Categoría": "Transporte", "Presupuesto": 50.0, "Actual": 0.0, "Tipo": "Necesidades"},
                    {"Check": False, "Categoría": "Restaurante", "Presupuesto": 50.0, "Actual": 0.0, "Tipo": "Deseos"},
                    {"Check": True, "Categoría": "Entretenimiento", "Presupuesto": 80.0, "Actual": 15.0, "Tipo": "Deseos"},
                    {"Check": True, "Categoría": "Salud", "Presupuesto": 30.0, "Actual": 30.0, "Tipo": "Necesidades"},
                    {"Check": True, "Categoría": "Mascotas", "Presupuesto": 30.0, "Actual": 20.0, "Tipo": "Necesidades"}
                ]),
                "ahorros": pd.DataFrame([
                    {"Check": True, "Concepto": "Viajar a Europa", "Presupuesto": 150.0, "Actual": 150.0, "Notas": "Meta anual"},
                    {"Check": False, "Concepto": "Fondo de emergencia", "Presupuesto": 100.0, "Actual": 0.0, "Notas": "3 meses fijos"}
                ]),
                "seguimiento": pd.DataFrame([
                    {"Check": True, "Monto": 100.0, "Categoría": "Mercado", "Fecha": "16", "Detalle": "Supermercado Éxito"},
                    {"Check": True, "Monto": 15.0, "Categoría": "Entretenimiento", "Fecha": "17", "Detalle": "Cine"},
                    {"Check": True, "Monto": 30.0, "Categoría": "Salud", "Fecha": "27", "Detalle": "Farmacia"},
                    {"Check": True, "Monto": 20.0, "Categoría": "Mascotas", "Fecha": "28", "Detalle": "Alimento mascota"}
                ])
            }
        st.session_state.finances[email] = user_data

def send_security_alert(target_email, event_type, details):
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_email": target_email,
        "event_type": event_type,
        "details": details
    }
    st.session_state.audit_log.append(log_entry)
    
    cfg = st.session_state.smtp_config
    if cfg["active"] and cfg["password"]:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 ALERTA DE SEGURIDAD: {event_type}"
            msg["From"] = cfg["sender"]
            msg["To"] = cfg["recipient"]
            
            html = f"""
            <h3>Alerta de Seguridad Militar en Finanzas 50/30/20</h3>
            <p><b>Evento:</b> {event_type}</p>
            <p><b>Fecha y Hora:</b> {log_entry['timestamp']}</p>
            <p><b>Cuenta objetivo:</b> {target_email}</p>
            <p><b>Detalles:</b> {details}</p>
            <hr>
            <p style='color: #00385C;'>Sistema Automatizado de Defensa Criptográfica</p>
            """
            msg.attach(MIMEText(html, "html"))
            
            server = smtplib.SMTP(cfg["server"], cfg["port"], timeout=5)
            server.starttls()
            server.login(cfg["sender"], cfg["password"])
            server.sendmail(cfg["sender"], cfg["recipient"], msg.as_string())
            server.quit()
        except Exception:
            pass

# ==========================================
# 4. PANTALLA DE ACCESO (LOGIN & REGISTRO)
# ==========================================
if st.session_state.current_user is None:
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0 1rem 0;'>
      <h1 style='color: #00385C; margin: 0;'>💼 Presupuesto 50/30/20 Plus</h1>
      <p style='color: #18688D; font-size: 1.05rem;'>Control financiero inteligente con seguridad criptográfica</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        tab_login, tab_reg = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
        
        with tab_login:
            with st.form("form_login"):
                login_email = st.text_input("Correo electrónico").strip().lower()
                login_pass = st.text_input("Contraseña", type="password")
                btn_login = st.form_submit_button("Ingresar al Portal", use_container_width=True)
                
                if btn_login:
                    if login_email in st.session_state.users:
                        u_data = st.session_state.users[login_email]
                        if u_data["locked_until"] and datetime.now() < u_data["locked_until"]:
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
                                    send_security_alert(login_email, "INTROMISIÓN DETECTADA / CUENTA BLOQUEADA", "3 intentos fallidos consecutivos.")
                                    st.error("⛔ Demasiados intentos fallidos. Cuenta bloqueada por 15 minutos y alerta remitida.")
                                else:
                                    st.warning(f"Credenciales incorrectas. Intentos restantes: {3 - u_data['failed_attempts']}.")
                    else:
                        send_security_alert(login_email, "INTENTO NO RECONOCIDO", "Intento de inicio de sesión con correo inexistente.")
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
                            "failed_attempts": 0,
                            "locked_until": None
                        }
                        init_user_finances(reg_email)
                        st.success("Cuenta creada exitosamente. Ya puedes iniciar sesión.")
    st.stop()

# ==========================================
# 5. MENÚ LATERAL Y NAVEGACIÓN
# ==========================================
current_email = st.session_state.current_user
user_info = st.session_state.users[current_email]
is_admin = user_info["role"] == "Superusuario"

with st.sidebar:
    st.markdown(f"""
    <div style='background: #E5F6FF; border: 1px solid #A0DFF7; padding: 12px; border-radius: 8px; margin-bottom: 1rem;'>
      <div style='font-size: 0.8rem; color: #0A405F; font-weight: 700;'>SESIÓN ACTIVA</div>
      <div style='font-size: 1.05rem; color: #00385C; font-weight: 700;'>{user_info['name']}</div>
      <div style='font-size: 0.85rem; color: #18688D;'>{current_email}</div>
      <span style='background: #00385C; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;'>{user_info['role']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    nav_options = ["📅 Presupuesto Mensual", "📊 Resumen Anual"]
    if is_admin:
        nav_options.append("👑 Panel de Administración")
        
    menu_selection = st.radio("Secciones", nav_options)
    
    st.markdown("---")
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state.current_user = None
        st.rerun()

init_user_finances(current_email)
user_fin = st.session_state.finances[current_email]

# ==========================================
# 6. VISTA: PRESUPUESTO MENSUAL
# ==========================================
if menu_selection == "📅 Presupuesto Mensual":
    col_m, col_sp = st.columns([1.5, 3])
    with col_m:
        sel_month = st.selectbox("Seleccionar Mes", MONTHS, index=3) # Abril por defecto
        
    data_m = user_fin[sel_month]
    
    # Cálculos
    total_ingreso_act = float(data_m["ingresos"]["Actual"].sum())
    total_ingreso_pre = float(data_m["ingresos"]["Presupuesto"].sum())
    
    total_facturas_act = float(data_m["facturas"]["Actual"].sum())
    total_facturas_pre = float(data_m["facturas"]["Presupuesto"].sum())
    
    total_var_act = float(data_m["seguimiento"]["Monto"].sum())
    total_var_pre = float(data_m["gastos_var"]["Presupuesto"].sum())
    
    total_ahorro_act = float(data_m["ahorros"]["Actual"].sum())
    total_ahorro_pre = float(data_m["ahorros"]["Presupuesto"].sum())
    
    total_gastado = total_facturas_act + total_var_act
    dinero_restante = total_ingreso_act - total_gastado - total_ahorro_act
    presupuesto_asignar = total_ingreso_pre - (total_facturas_pre + total_var_pre + total_ahorro_pre)
    
    # 50/30/20 actual
    fac_nec = data_m["facturas"][data_m["facturas"]["Tipo"] == "Necesidades"]["Actual"].sum()
    var_nec = data_m["gastos_var"][data_m["gastos_var"]["Tipo"] == "Necesidades"]["Actual"].sum()
    nec_act = fac_nec + var_nec
    
    fac_des = data_m["facturas"][data_m["facturas"]["Tipo"] == "Deseos"]["Actual"].sum()
    var_des = data_m["gastos_var"][data_m["gastos_var"]["Tipo"] == "Deseos"]["Actual"].sum()
    des_act = fac_des + var_des
    
    ahorro_act_p = total_ahorro_act
    
    # BANNER SUPERIOR
    st.markdown(f"""
    <div class='main-header-banner'>
      <div class='main-header-title'>{sel_month.upper()} 2026</div>
      <div class='main-header-subtitle'>Panel General de Finanzas Personales 50/30/20</div>
    </div>
    """, unsafe_allow_html=True)
    
    # TARJETAS KPI
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Ingreso Total</div>
          <div class='kpi-card-value'>${total_ingreso_act:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Total Gastado</div>
          <div class='kpi-card-value'>${total_gastado:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>A Asignar</div>
          <div class='kpi-card-value'>${presupuesto_asignar:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class='kpi-card'>
          <div class='kpi-card-label'>Total Ahorrado</div>
          <div class='kpi-card-value'>${total_ahorro_act:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class='restante-card'>
          <div class='restante-card-label'>Dinero Restante</div>
          <div class='restante-card-value'>${dinero_restante:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
    
    # GRÁFICOS
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        # Gráfica Dona 50/30/20
        df_pie = pd.DataFrame({
            "Categoría": ["50% Necesidades", "30% Deseos", "20% Ahorros"],
            "Monto": [nec_act, des_act, ahorro_act_p]
        })
        fig_pie = px.pie(
            df_pie,
            names="Categoría",
            values="Monto",
            hole=0.55,
            title="Distribución Actual 50/30/20",
            color_discrete_sequence=["#00385C", "#31B4D1", "#00ACA9"]
        )
        fig_pie.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=260)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with g_col2:
        # Gráfica Ingresos vs Gastos
        fig_bar = go.Figure(data=[
            go.Bar(name='Ingresos', x=['Total'], y=[total_ingreso_act], marker_color='#00ACA9'),
            go.Bar(name='Gastos', x=['Total'], y=[total_gastado], marker_color='#D74546'),
            go.Bar(name='Ahorros', x=['Total'], y=[total_ahorro_act], marker_color='#00385C')
        ])
        fig_bar.update_layout(
            barmode='group',
            title="Comparativa Flujo de Caja",
            margin=dict(t=40, b=10, l=10, r=10),
            height=260,
            showlegend=True
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # TABLAS INTERACTIVAS
    col_t1, col_t2 = st.columns([1.1, 1.3])
    
    with col_t1:
        st.markdown("<div class='section-badge'>💵 INGRESOS</div>", unsafe_allow_html=True)
        data_m["ingresos"] = st.data_editor(
            data_m["ingresos"],
            column_config={
                "Check": st.column_config.CheckboxColumn("✓", default=False),
                "Presupuesto": st.column_config.NumberColumn(format="$%.2f"),
                "Actual": st.column_config.NumberColumn(format="$%.2f")
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"ing_{sel_month}"
        )
        
        st.markdown("<div class='section-badge'>🎯 AHORROS</div>", unsafe_allow_html=True)
        data_m["ahorros"] = st.data_editor(
            data_m["ahorros"],
            column_config={
                "Check": st.column_config.CheckboxColumn("✓", default=False),
                "Presupuesto": st.column_config.NumberColumn(format="$%.2f"),
                "Actual": st.column_config.NumberColumn(format="$%.2f")
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"aho_{sel_month}"
        )

    with col_t2:
        st.markdown("<div class='section-badge'>📑 FACTURAS (GASTOS FIJOS)</div>", unsafe_allow_html=True)
        data_m["facturas"] = st.data_editor(
            data_m["facturas"],
            column_config={
                "Check": st.column_config.CheckboxColumn("✓", default=False),
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Necesidades", "Deseos"]),
                "Presupuesto": st.column_config.NumberColumn(format="$%.2f"),
                "Actual": st.column_config.NumberColumn(format="$%.2f")
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"fac_{sel_month}"
        )
        
    st.markdown("---")
    col_b1, col_b2 = st.columns([1.2, 1.2])
    
    with col_b1:
        st.markdown("<div class='section-badge'>🛒 GASTOS VARIABLES (PRESUPUESTO)</div>", unsafe_allow_html=True)
        data_m["gastos_var"] = st.data_editor(
            data_m["gastos_var"],
            column_config={
                "Check": st.column_config.CheckboxColumn("✓", default=False),
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Necesidades", "Deseos"]),
                "Presupuesto": st.column_config.NumberColumn(format="$%.2f"),
                "Actual": st.column_config.NumberColumn(format="$%.2f")
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"gvar_{sel_month}"
        )

    with col_b2:
        st.markdown("<div class='section-badge'>📝 SEGUIMIENTO DE GASTOS (TRANSACCIONES)</div>", unsafe_allow_html=True)
        data_m["seguimiento"] = st.data_editor(
            data_m["seguimiento"],
            column_config={
                "Check": st.column_config.CheckboxColumn("✓", default=True),
                "Monto": st.column_config.NumberColumn(format="$%.2f"),
                "Categoría": st.column_config.SelectboxColumn("Categoría", options=[
                    "Mercado", "Transporte", "Restaurante", "Entretenimiento",
                    "Salud", "Cuidado personal", "Hogar", "Ropa", "Educación",
                    "Vacaciones", "Mascotas", "Misceláneos"
                ])
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"seg_{sel_month}"
        )

# ==========================================
# 7. VISTA: RESUMEN ANUAL CONSOLIDADO
# ==========================================
elif menu_selection == "📊 Resumen Anual":
    st.markdown("""
    <div class='main-header-banner'>
      <div class='main-header-title'>CONSOLIDADO ANUAL 2026</div>
      <div class='main-header-subtitle'>Métricas acumuladas mes a mes</div>
    </div>
    """, unsafe_allow_html=True)
    
    summary_data = []
    for m in MONTHS:
        d = user_fin[m]
        ing = d["ingresos"]["Actual"].sum()
        fac = d["facturas"]["Actual"].sum()
        var = d["seguimiento"]["Monto"].sum()
        aho = d["ahorros"]["Actual"].sum()
        gas = fac + var
        flujo = ing - gas - aho
        
        summary_data.append({
            "Mes": m,
            "Ingresos": ing,
            "Gastos": gas,
            "Ahorros": aho,
            "Flujo Neto": flujo
        })
        
    df_annual = pd.DataFrame(summary_data)
    
    # Métricas anuales
    tot_ing = df_annual["Ingresos"].sum()
    tot_gas = df_annual["Gastos"].sum()
    tot_aho = df_annual["Ahorros"].sum()
    tot_flu = df_annual["Flujo Neto"].sum()
    
    ca1, ca2, ca3, ca4 = st.columns(4)
    with ca1:
        st.metric("Total Ingresos Anuales", f"${tot_ing:,.2f}")
    with ca2:
        st.metric("Total Gastos Anuales", f"${tot_gas:,.2f}")
    with ca3:
        st.metric("Total Ahorrado Anual", f"${tot_aho:,.2f}")
    with ca4:
        st.metric("Flujo Neto Acumulado", f"${tot_flu:,.2f}")
        
    # Gráfica Anual
    fig_an = go.Figure()
    fig_an.add_trace(go.Bar(x=df_annual["Mes"], y=df_annual["Ingresos"], name="Ingresos", marker_color="#00ACA9"))
    fig_an.add_trace(go.Bar(x=df_annual["Mes"], y=df_annual["Gastos"], name="Gastos", marker_color="#D74546"))
    fig_an.add_trace(go.Bar(x=df_annual["Mes"], y=df_annual["Ahorros"], name="Ahorros", marker_color="#00385C"))
    fig_an.update_layout(title="Comportamiento Financiero Mes a Mes", barmode='group', height=360)
    st.plotly_chart(fig_an, use_container_width=True)
    
    # Tabla Anual
    st.dataframe(
        df_annual.style.format({
            "Ingresos": "${:,.2f}",
            "Gastos": "${:,.2f}",
            "Ahorros": "${:,.2f}",
            "Flujo Neto": "${:,.2f}"
        }),
        use_container_width=True
    )

# ==========================================
# 8. PANEL DE ADMINISTRACIÓN Y SEGURIDAD (SUPERUSUARIO)
# ==========================================
elif menu_selection == "👑 Panel de Administración" and is_admin:
    st.markdown("""
    <div class='main-header-banner'>
      <div class='main-header-title'>CENTRO DE COMANDO & ADMINISTRACIÓN</div>
      <div class='main-header-subtitle'>Gestión de identidades, restablecimiento y bitácora militar</div>
    </div>
    """, unsafe_allow_html=True)
    
    t_users, t_sec, t_audit = st.tabs(["👥 Usuarios Registrados", "🔑 Restablecer Contraseña por Nombre", "🛡️ Bitácora de Seguridad"])
    
    with t_users:
        user_list = []
        for mail, dat in st.session_state.users.items():
            user_list.append({
                "Nombre": dat["name"],
                "Correo Electrónico": mail,
                "Rol": dat["role"],
                "Intentos Fallidos": dat["failed_attempts"],
                "Bloqueado Hasta": str(dat["locked_until"]) if dat["locked_until"] else "No"
            })
        st.dataframe(pd.DataFrame(user_list), use_container_width=True)
        
    with t_sec:
        st.subheader("Restablecimiento Directo por Nombre")
        st.info("Como Super Administrador puedes redefinir la clave de cualquier cuenta solicitando únicamente su nombre.")
        
        user_names = [d["name"] for d in st.session_state.users.values()]
        selected_name = st.selectbox("Seleccione el Nombre del Usuario", user_names)
        
        # Encontrar el correo asociado al nombre seleccionado
        target_mail = None
        for mail, dat in st.session_state.users.items():
            if dat["name"] == selected_name:
                target_mail = mail
                break
                
        with st.form("form_reset"):
            st.write(f"Cuenta vinculada: **{target_mail}**")
            new_password = st.text_input("Nueva Contraseña", type="password")
            confirm_new_password = st.text_input("Confirmar Nueva Contraseña", type="password")
            btn_reset = st.form_submit_button("Aplicar Nueva Contraseña")
            
            if btn_reset:
                if not new_password:
                    st.warning("Escribe una contraseña válida.")
                elif new_password != confirm_new_password:
                    st.error("Las contraseñas no coinciden.")
                else:
                    new_h, new_s = hash_password(new_password)
                    st.session_state.users[target_mail]["hash"] = new_h
                    st.session_state.users[target_mail]["salt"] = new_s
                    st.session_state.users[target_mail]["failed_attempts"] = 0
                    st.session_state.users[target_mail]["locked_until"] = None
                    send_security_alert(target_mail, "CONTRASEÑA RESTABLECIDA POR ADMIN", f"Clave actualizada para {selected_name}")
                    st.success(f"Contraseña de {selected_name} actualizada exitosamente.")

    with t_audit:
        st.subheader("Bitácora de Incidentes y Auditoría Criptográfica")
        if st.session_state.audit_log:
            df_log = pd.DataFrame(st.session_state.audit_log)
            st.dataframe(df_log, use_container_width=True)
        else:
            st.success("No se han registrado incidentes ni violaciones de seguridad.")
