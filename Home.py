import pyrebase
import streamlit as st
import firebase_admin
import re
import importlib.util
from firebase_admin import credentials
from pathlib import Path
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

disable_warnings(InsecureRequestWarning)

def _load_local_module(module_filename: str, module_name: str):
    module_path = Path(__file__).resolve().with_name(module_filename)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {module_name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


config_creds = _load_local_module("config_creds.py", "config_creds")
firebaseConfig = config_creds.firebaseConfig
from ml_app_screen import ml_app


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  FIREBASE INITIALIZATION
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _service_account_path():
    for candidate in ("serviceAccountKey.json", "serviceAccountKey.json.json"):
        if Path(candidate).exists():
            return candidate
    return None


@st.cache_resource
def get_firebase_app():
    service_account = _service_account_path()
    if service_account is None:
        raise FileNotFoundError("Missing Firebase service account key.")
    if not firebase_admin._apps:
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
    return pyrebase.initialize_app(firebaseConfig)


def get_firebase():
    # Fresh client handles avoid stale auth state across reruns/sessions.
    firebase = get_firebase_app()
    return firebase.auth(), firebase.database(), firebase.storage()


def _firebase_error_code(exc: Exception) -> str:
    text = str(exc)
    match = re.search(r'"message"\s*:\s*"([^"]+)"', text)
    if match:
        return match.group(1)
    for code in (
        "INVALID_PASSWORD",
        "EMAIL_NOT_FOUND",
        "INVALID_LOGIN_CREDENTIALS",
        "EMAIL_EXISTS",
        "WEAK_PASSWORD",
        "INVALID_EMAIL",
        "TOO_MANY_ATTEMPTS_TRY_LATER",
    ):
        if code in text:
            return code
    return ""


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  SESSION STATE
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def init_session_state():
    defaults = {"user_login": False, "user_email": "", "username": "", "show_auth": False, "auth_tab": "login"}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  AUTH FUNCTIONS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def handle_login(email, password):
    email = (email or "").strip().lower()
    password = (password or "").strip()
    if not email or not password:
        st.warning("Please enter both email and password.", icon="")
        return
    try:
        auth, _, _ = get_firebase()
        auth.sign_in_with_email_and_password(email, password)
        st.session_state["user_login"] = True
        st.session_state["user_email"] = email
        st.session_state["show_auth"]  = False
        st.rerun()
    except Exception as e:
        error_code = _firebase_error_code(e)
        if error_code in ["INVALID_PASSWORD", "EMAIL_NOT_FOUND", "INVALID_LOGIN_CREDENTIALS"]:
            st.error("Invalid email or password.", icon="")
        elif error_code == "TOO_MANY_ATTEMPTS_TRY_LATER":
            st.warning("Too many attempts. Please wait a minute and try again.", icon="âš ï¸")
        else:
            st.error("Login failed. Please try again.", icon="")


def handle_register(email, password, username, confirm_password):
    email = (email or "").strip().lower()
    username = (username or "").strip()
    password = (password or "").strip()
    confirm_password = (confirm_password or "").strip()
    if not all([email, password, username, confirm_password]):
        st.warning("Please fill in all fields.")
        return
    if len(password) < 6:
        st.warning("Password must be at least 6 characters.")
        return
    if password != confirm_password:
        st.error("Passwords do not match.")
        return
    try:
        auth, db, _ = get_firebase()
        auth.create_user_with_email_and_password(email, password)
        user = auth.sign_in_with_email_and_password(email, password)
        local_id = user["localId"]
        db.child(local_id).child("Username").set(username)
        db.child(local_id).child("Email").set(email)
        st.session_state["user_login"] = True
        st.session_state["user_email"] = email
        st.session_state["username"] = username
        st.session_state["show_auth"] = False
        st.rerun()
    except Exception as e:
        error_code = _firebase_error_code(e)
        if error_code == "EMAIL_EXISTS":
            st.error("Email already registered. Please login.")
        elif error_code == "WEAK_PASSWORD":
            st.warning("Password too weak. Use at least 6 characters.")
        elif error_code == "INVALID_EMAIL":
            st.error("Invalid email format.")
        else:
            st.error("Registration failed. Please try again.")


def handle_logout():
    st.session_state["user_login"] = False
    st.session_state["user_email"] = ""
    st.session_state["username"]   = ""
    st.session_state["show_auth"]  = False


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  GLOBAL CSS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

    /* Hide Streamlit default elements */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
    [data-testid="stToolbar"] { display: none; }

    /* Root variables */
    :root {
        --navy:    #05112a;
        --navy2:   #0a1f45;
        --teal:    #00c9b1;
        --teal2:   #00e5cc;
        --cyan:    #38bdf8;
        --white:   #f0f6ff;
        --gray:    #8899bb;
        --card-bg: rgba(10,31,69,0.85);
        --border:  rgba(0,201,177,0.2);
    }

    /* Full page background */
    .stApp {
        background: var(--navy) !important;
        font-family: 'DM Sans', sans-serif;
    }

    /* Remove default padding */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* â”€â”€ NAVBAR â”€â”€ */
    .navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 18px 60px;
        background: rgba(5,17,42,0.95);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border);
        position: sticky; top: 0; z-index: 999;
    }
    .navbar-brand {
        font-family: 'Syne', sans-serif;
        font-size: 22px; font-weight: 800;
        color: var(--white);
        display: flex; align-items: center; gap: 10px;
    }
    .navbar-brand span { color: var(--teal); }
    .navbar-links {
        display: flex; align-items: center; gap: 32px;
    }
    .navbar-links a {
        color: var(--gray); font-size: 14px; font-weight: 500;
        text-decoration: none; transition: color 0.2s;
        letter-spacing: 0.3px;
    }
    .navbar-links a:hover { color: var(--white); }
    .navbar-actions { display: flex; align-items: center; gap: 12px; }
    .btn-nav-outline {
        padding: 8px 20px; border-radius: 6px;
        border: 1.5px solid var(--teal); color: var(--teal);
        font-size: 13px; font-weight: 600; cursor: pointer;
        background: transparent; transition: all 0.2s;
        font-family: 'DM Sans', sans-serif; letter-spacing: 0.5px;
    }
    .btn-nav-outline:hover { background: var(--teal); color: var(--navy); }
    .btn-nav-solid {
        padding: 8px 20px; border-radius: 6px;
        border: none; color: var(--navy);
        background: var(--teal);
        font-size: 13px; font-weight: 700; cursor: pointer;
        transition: all 0.2s; font-family: 'DM Sans', sans-serif;
    }
    .btn-nav-solid:hover { background: var(--teal2); transform: translateY(-1px); }

    /* â”€â”€ HERO â”€â”€ */
    .hero {
        min-height: 88vh;
        background: linear-gradient(135deg, #05112a 0%, #0a1f45 50%, #061830 100%);
        display: flex; align-items: center;
        padding: 80px 60px;
        position: relative; overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute; inset: 0;
        background-image:
            linear-gradient(rgba(0,201,177,0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,201,177,0.04) 1px, transparent 1px);
        background-size: 50px 50px;
    }
    .hero-orb {
        position: absolute; border-radius: 50%; filter: blur(100px);
        animation: orbFloat 10s ease-in-out infinite alternate;
    }
    .hero-orb-1 { width:500px;height:500px; background:rgba(0,201,177,0.08); top:-100px; right:-50px; }
    .hero-orb-2 { width:300px;height:300px; background:rgba(56,189,248,0.06); bottom:-50px; left:30%; animation-delay:-5s; }
    @keyframes orbFloat { to { transform: translate(20px, -20px); } }

    .hero-content { position:relative; z-index:1; max-width: 680px; }
    .hero-badge {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(0,201,177,0.1); border: 1px solid var(--border);
        border-radius: 50px; padding: 6px 16px;
        font-size: 12px; color: var(--teal); font-weight: 600;
        letter-spacing: 1px; text-transform: uppercase;
        margin-bottom: 28px;
    }
    .hero-badge-dot { width:6px;height:6px;border-radius:50%;background:var(--teal);animation:pulse 2s infinite; }
    @keyframes pulse { 0%,100%{box-shadow:0 0 4px var(--teal);} 50%{box-shadow:0 0 14px var(--teal);} }

    .hero-title {
        font-family: 'Syne', sans-serif;
        font-size: clamp(42px, 6vw, 72px);
        font-weight: 800; line-height: 1.08;
        color: var(--white); margin-bottom: 24px;
    }
    .hero-title .accent { color: var(--teal); }
    .hero-title .accent2 { color: var(--cyan); }

    .hero-subtitle {
        font-size: 18px; color: var(--gray);
        line-height: 1.7; margin-bottom: 40px;
        max-width: 520px; font-weight: 300;
    }

    .hero-stats {
        display: flex; gap: 36px; margin-bottom: 44px;
    }
    .hero-stat-num {
        font-family: 'Syne', sans-serif;
        font-size: 26px; font-weight: 800; color: var(--teal);
    }
    .hero-stat-label { font-size: 12px; color: var(--gray); margin-top: 2px; }

    .hero-cta { display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }
    .btn-primary {
        padding: 14px 32px; border-radius: 8px;
        background: var(--teal); color: var(--navy);
        font-family: 'Syne', sans-serif;
        font-size: 15px; font-weight: 700;
        border: none; cursor: pointer;
        transition: all 0.25s;
        box-shadow: 0 4px 24px rgba(0,201,177,0.35);
    }
    .btn-primary:hover { background: var(--teal2); transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,201,177,0.45); }
    .btn-secondary {
        padding: 14px 32px; border-radius: 8px;
        background: transparent; color: var(--white);
        font-family: 'Syne', sans-serif;
        font-size: 15px; font-weight: 700;
        border: 1.5px solid rgba(255,255,255,0.2); cursor: pointer;
        transition: all 0.25s;
    }
    .btn-secondary:hover { border-color: var(--white); background: rgba(255,255,255,0.05); }

    /* â”€â”€ FEATURES STRIP â”€â”€ */
    .features-strip {
        background: var(--navy2);
        border-top: 1px solid var(--border);
        border-bottom: 1px solid var(--border);
        padding: 32px 60px;
        display: flex; justify-content: center; gap: 60px;
        flex-wrap: wrap;
    }
    .feature-item {
        display: flex; align-items: center; gap: 14px;
        color: var(--gray); font-size: 14px; font-weight: 500;
    }
    .feature-icon {
        width: 40px; height: 40px; border-radius: 10px;
        background: rgba(0,201,177,0.1);
        border: 1px solid var(--border);
        display: flex; align-items: center; justify-content: center;
        font-size: 18px;
    }
    .feature-item strong { display:block; color: var(--white); font-size: 15px; }

    /* â”€â”€ AUTH MODAL â”€â”€ */
    .auth-overlay {
        position: fixed; inset: 0; z-index: 1000;
        background: rgba(5,17,42,0.92);
        backdrop-filter: blur(8px);
        display: flex; align-items: center; justify-content: center;
    }
    .auth-card {
        background: #0c1e3d;
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 48px;
        width: 100%; max-width: 440px;
        box-shadow: 0 32px 80px rgba(0,0,0,0.5);
        animation: slideUp 0.35s ease both;
    }
    @keyframes slideUp { from{opacity:0;transform:translateY(24px);} to{opacity:1;transform:translateY(0);} }
    .auth-logo {
        font-family: 'Syne', sans-serif;
        font-size: 20px; font-weight: 800;
        color: var(--white); text-align: center;
        margin-bottom: 6px;
    }
    .auth-logo span { color: var(--teal); }
    .auth-tagline { text-align:center; color:var(--gray); font-size:13px; margin-bottom:28px; }

    /* Streamlit input overrides inside auth */
    .stTextInput input {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        color: var(--white) !important;
        padding: 12px 14px !important;
    }
    .stTextInput input:focus {
        border-color: var(--teal) !important;
        box-shadow: 0 0 0 3px rgba(0,201,177,0.1) !important;
    }
    .stTextInput label { color: var(--gray) !important; font-size: 12px !important; letter-spacing: 0.8px; text-transform: uppercase; }

    /* Primary button override */
    .stButton button[kind="primary"] {
        background: var(--teal) !important;
        color: var(--navy) !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 12px !important;
        font-size: 15px !important;
        box-shadow: 0 4px 20px rgba(0,201,177,0.3) !important;
        transition: all 0.2s !important;
    }
    .stButton button[kind="primary"]:hover {
        background: var(--teal2) !important;
        transform: translateY(-1px) !important;
    }

    /* Secondary button override */
    .stButton button[kind="secondary"] {
        background: transparent !important;
        color: var(--gray) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
    }

    /* Tabs override */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.04) !important;
        border-radius: 10px !important;
        padding: 4px !important;
        gap: 4px !important;
        border: 1px solid var(--border) !important;
        margin-bottom: 24px !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        color: var(--gray) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 8px 20px !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--teal) !important;
        color: var(--navy) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    .stTabs [data-baseweb="tab-border"] { display: none !important; }

    /* User footer bar */
    .user-bar {
        display: flex; align-items: center; justify-content: space-between;
        background: var(--navy2);
        border-top: 1px solid var(--border);
        padding: 14px 60px;
        font-size: 13px; color: var(--gray);
    }
    .user-bar-email { display:flex; align-items:center; gap:8px; }
    .online-dot { width:8px;height:8px;border-radius:50%;background:#00e676;box-shadow:0 0 8px #00e676; }
    </style>
    """, unsafe_allow_html=True)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  PAGE SECTIONS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def show_navbar():
    st.markdown(
        f"""<div class="navbar">
<div class="navbar-brand">Phish<span>Guardian</span></div>
<div class="navbar-links"></div>
<div class="navbar-actions"></div>
</div>""",
        unsafe_allow_html=True,
    )


def show_hero():
    st.markdown("""
    <div class="hero">
        <div class="hero-orb hero-orb-1"></div>
        <div class="hero-orb hero-orb-2"></div>
        <div class="hero-content">
            <div class="hero-badge">
                <div class="hero-badge-dot"></div>
                ML-Powered Security Platform
            </div>
            <h1 class="hero-title">
                Detect.<span class="accent"> Analyze.</span><br>
                Protect your<br>
                <span class="accent2">Network.</span>
            </h1>
            <p class="hero-subtitle">
                PhishGuardian uses advanced machine learning KNN, Random Forest, CNN & SVM
                to detect network intrusions and phishing attacks in real time.
            </p>
            <div class="hero-stats">
                <div>
                    <div class="hero-stat-num">97.6%</div>
                    <div class="hero-stat-label">SVM Accuracy</div>
                </div>
                <div>
                    <div class="hero-stat-num">97.4%</div>
                    <div class="hero-stat-label">Random Forest</div>
                </div>
                <div>
                    <div class="hero-stat-num">3</div>
                    <div class="hero-stat-label">ML Models</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_features_strip():
    st.markdown("""
    <div class="features-strip">
        <div class="feature-item">
            <div class="feature-icon"></div>
            <div><strong>Intrusion Detection</strong>Scan network traffic CSV files</div>
        </div>
        <div class="feature-item">
            <div class="feature-icon"></div>
            <div><strong>4 ML Algorithms</strong>RF,DT SVM</div>
        </div>
        <div class="feature-item">
            <div class="feature-icon"></div>
            <div><strong>Real-time Analysis</strong>Instant attack classification</div>
        </div>
        <div class="feature-item">
            <div class="feature-icon"></div>
            <div><strong>Detailed Reports</strong>Binary & multi-class results</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_auth_section():
    """Show login/register using Streamlit tabs styled as a centered card."""
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("""
            <div style='text-align:center; margin-bottom:6px;'>
                <span style='font-family:Syne,sans-serif;font-size:22px;font-weight:800;color:#f0f6ff;'>
                    ðŸ›¡ï¸ Phish<span style="color:#00c9b1;">Guardian</span>
                </span>
            </div>
            <p style='text-align:center;color:#8899bb;font-size:13px;margin-bottom:24px;'>
                Sign in to access the ML detection dashboard
            </p>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["Login", "Register"])

        with tab_login:
            st.write("")
            login_email    = st.text_input("Email Address", placeholder="you@example.com", key="login_email")
            login_password = st.text_input("Password", placeholder="#####", type="password", key="login_password")
            st.write("")
            if st.button("Login", width="stretch", type="primary", key="btn_login"):
                handle_login(login_email, login_password)
            st.markdown("<p style='text-align:center;font-size:12px;color:#8899bb;margin-top:12px;'>Don't have an account? Use the <b>Register</b> tab.</p>", unsafe_allow_html=True)

        with tab_register:
            st.write("")
            reg_username = st.text_input("Username",         placeholder="Your name",         key="reg_username")
            reg_email    = st.text_input("Email Address",    placeholder="you@example.com",   key="reg_email")
            reg_password = st.text_input("Password",         placeholder="Min. 6 characters", type="password", key="reg_password")
            reg_confirm  = st.text_input("Confirm Password", placeholder="Repeat password",   type="password", key="reg_confirm")
            st.write("")
            if st.button("Create Account ’", width="stretch", type="primary", key="btn_register"):
                handle_register(reg_email, reg_password, reg_username, reg_confirm)
            st.markdown("<p style='text-align:center;font-size:12px;color:#8899bb;margin-top:12px;'>Already have an account? Use the <b>Login</b> tab.</p>", unsafe_allow_html=True)

    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)


def show_user_bar():
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"""
        <div class="user-bar">
            <div class="user-bar-email">
                <div class="online-dot"></div>
                Logged in as <strong style="color:#f0f6ff;">&nbsp;{st.session_state['user_email']}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.write("")
        if st.button("Log Out", type="secondary", width="stretch"):
            handle_logout()
            st.rerun()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  MAIN APP
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main_app():
    st.set_page_config(
        page_title="PhishGuardian Network Intrusion Detection",
        page_icon="",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_styles()
    init_session_state()

    if not st.session_state["user_login"]:
        # Show landing page + auth form
        show_navbar()
        show_hero()
        show_features_strip()
        show_auth_section()
    else:
        # Show app after login
        show_navbar()
        show_user_bar()
        with st.spinner("Loading the ML app..."):
            ml_app()


main_app()



