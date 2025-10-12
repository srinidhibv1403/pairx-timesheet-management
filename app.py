import streamlit as st
import pandas as pd
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import secrets
import string
import requests
from PIL import Image

# ---- Credentials and Constants ----
st.set_page_config(page_title="Pairx Timesheet", layout="wide", initial_sidebar_state="collapsed")

ADMIN_EMAIL = "srinidhibv.cs23@bmsce.ac.in"
ALLOWED_DOMAINS = ["@persist-ai.com", "@pairx.com"]
FIREBASE_WEB_API_KEY = st.secrets.get("firebase_web_api_key", "YOUR_WEB_API_KEY")

# ---- Firebase Initialization ----
if not firebase_admin._apps:
    try:
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        else:
            firebase_config = dict(st.secrets["firebase"])
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase initialization failed: {e}")

# ---- Theme/Settings State ----
for key, value in {
    'dark_mode': True,
    'show_settings': False,
    'authenticated': False,
    'user_email': None,
    'user_role': None,
    'employee_id': None,
    'user_name': None,
    'view_as': None,
    'show_forgot_password': False
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---- Utility Functions ----
def check_and_create_csvs():
    files_headers = {
        "employees.csv": "EmployeeID,Name,Email,Department,Role,ManagerID\n",
        "projects.csv": "ProjectID,ProjectName,StartDate,EndDate\n",
        "tasks.csv": "TaskID,ProjectID,AssignedTo,Status\n",
        "timesheets.csv": "TimesheetID,EmployeeID,Date,TaskID,TaskDescription,HoursWorked,ApprovalStatus,ManagerComment\n",
        "leaves.csv": "LeaveID,EmployeeID,Type,StartDate,EndDate,Reason,Status,ManagerComment\n"
    }
    for fname, header in files_headers.items():
        if not os.path.exists(fname):
            with open(fname, "w") as f:
                f.write(header)
check_and_create_csvs()

def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def send_password_reset_email(email):
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
        payload = {"requestType": "PASSWORD_RESET", "email": email}
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            return True, "Password reset email sent"
        else:
            return False, r.json().get("error", {}).get("message", "Failed to send reset email")
    except Exception as e:
        return False, str(e)

def validate_user(email):
    if email == ADMIN_EMAIL:
        return "Admin", "ADMIN001", "Admin"
    try:
        df_emp = pd.read_csv("employees.csv")
        employee = df_emp[df_emp["Email"] == email]
        if not employee.empty:
            return employee.iloc[0]["Role"], employee.iloc[0]["EmployeeID"], employee.iloc[0]["Name"]
    except:
        pass
    return None, None, None

def get_my_team_employees(manager_id):
    try:
        df_emp = pd.read_csv("employees.csv")
        return df_emp[df_emp["ManagerID"] == manager_id]["EmployeeID"].tolist()
    except:
        return []

def verify_firebase_password(email, password):
    try:
        user = firebase_auth.get_user_by_email(email)
        return True, user
    except:
        return False, None

def logout():
    for k in ["authenticated", "user_email", "user_role", "employee_id", "user_name", "view_as"]:
        st.session_state[k] = None if "name" in k else False
    st.rerun()

# ---- Theme CSS ----
if st.session_state.dark_mode:
    page_bg = "#0f1419"
    body_text = "#E8EDF2"
    label_text = "#C5CDD6"
    input_bg = "#273647"
    input_text = "#FFFFFF"
    button_bg = "#5FA8D3"
    button_text = "#FFFFFF"
    header_bg = "#FFFFFF"
else:
    page_bg = "#FFFFFF"
    body_text = "#1a1a1a"
    label_text = "#4a4a4a"
    input_bg = "#F5F5F5"
    input_text = "#1a1a1a"
    button_bg = "#3b82f6"
    button_text = "#FFFFFF"
    header_bg = "#FFFFFF"

st.markdown(f"""
<style>
    #MainMenu, footer, header {{visibility: hidden;}}
    [data-testid="stSidebar"] {{display: none;}}
    .stApp {{background: {page_bg}; font-family: 'Segoe UI', sans-serif; color: {body_text};}}
    .block-container {{padding: 0.6rem 1.2rem !important; max-width: 100vw !important;}}
    label {{color: {label_text} !important; font-weight: 600 !important; font-size: 0.92rem !important;}}
    .stTextInput > div > div > input, .stNumberInput > div > div > input, 
    .stDateInput > div > div > input, .stSelectbox > div > div, .stTextArea > div > div > textarea {{
        background: {input_bg} !important; color: {input_text} !important;
        border: 1px solid #2d4057 !important; border-radius: 6px !important; padding: 0.5rem 0.9rem !important;
        font-size: 0.94rem !important;
    }}
    .stButton > button, .stFormSubmitButton > button {{
        background: {button_bg} !important; color: {button_text} !important;
        border-radius: 6px !important; padding: 0.45rem 1.1rem !important;
        font-weight: 600 !important; width: 100%;
        font-size: 0.92rem !important;
        transition: all 0.13s;
        border: none !important;
    }}
    .stButton > button:hover, .stFormSubmitButton > button:hover {{
        filter: brightness(1.12) !important;
        transition: all 0.20s;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background-color: transparent;
        margin-bottom: 0.2rem !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {input_bg};
        color: {body_text};
        border-radius: 5px;
        padding: 0.35rem 1.2rem;
        font-weight: 600;
        font-size: 0.92rem;
        border: 1px solid transparent;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: {button_bg}22;
        border-color: {button_bg}44;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {button_bg};
        color: {button_text};
    }}
    h1 {{font-size: 1.6rem !important;margin:0;margin-bottom:0.1rem}}
    hr {{border: none !important; height: 1px !important; background: #2d4057 !important; margin: 0.8rem 0 !important; opacity: 0.18 !important;}}
    .user-info {{
        background: {input_bg}; padding: 0.25rem 0.65rem;
        border-radius: 14px; display: inline-block; font-size: 0.89rem; font-weight:600;
    }}
    .element-container:has(> .stMarkdown:empty) {{display: none;}}
    /* Remove view line under select */
    [data-baseweb="select"]>div>div>div:not(:last-child) {{border-bottom:none}}
</style>
""", unsafe_allow_html=True)

# ---- Settings Page ----
if st.session_state.get('show_settings', False):
    st.markdown("## Settings")
    st.markdown("### Appearance")
    theme_choice = st.radio("Theme", ["Dark Mode", "Light Mode"], index=0 if st.session_state.dark_mode else 1)
    st.session_state.dark_mode = theme_choice == "Dark Mode"
    if st.button("Back to Dashboard"):
        st.session_state.show_settings = False
        st.rerun()
    st.stop()

# ---- Header with settings button ----
header_html = f"""
<div style="background: {header_bg}; padding: 0.65rem 1.2rem; margin: -0.65rem -1.2rem 1rem -1.2rem; 
    box-shadow: 0 2px 8px rgba(0,0,0,0.07); display: flex; align-items: center; justify-content: space-between;">
    <div style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{{}}" width="40" style="margin-right: 0.75rem;">
        <span style="color: #000000; font-size: 1.35rem; font-weight: 700; 
        font-family: 'Segoe UI', sans-serif; white-space: nowrap;display:inline-block;">Pairx Timesheet Management</span>
    </div>
    <button onclick="window.dispatchEvent(new Event('openSettings'))"
     style="background:{input_bg};border:none;font-size:1.34rem;padding:7px 13px;border-radius:6px;cursor:pointer;">⚙️</button>
</div>
<script>
window.addEventListener('openSettings', function(){window.parent.postMessage({isStreamlitMessage:true,type:'streamlit:setComponentValue',component:'settings_btn',value:true}, '*')})
</script>
"""
try:
    import base64
    with open("logo.jpg", "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(header_html.format(logo_data), unsafe_allow_html=True)
except:
    st.markdown(header_html.format(""), unsafe_allow_html=True)
if st.session_state.get('settings_btn', False):
    st.session_state.show_settings = True
    st.session_state['settings_btn'] = False
    st.rerun()
if not st.session_state.authenticated:
    # Login page (no change needed)
    def firebase_login():
        st.markdown("### Sign In to Pairx Timesheet")
        if st.session_state.show_forgot_password:
            st.subheader("Reset Password")
            reset_email = st.text_input("Enter your email address", key="reset_email")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Send Reset Link", use_container_width=True):
                    if not reset_email:
                        st.error("Please enter your email")
                    else:
                        success, message = send_password_reset_email(reset_email)
                        if success:
                            st.success(message)
                            st.info("Check your email for password reset link")
                        else:
                            st.error(f"Error: {message}")
            with col2:
                if st.button("Back to Login", use_container_width=True):
                    st.session_state.show_forgot_password = False
                    st.rerun()
        else:
            email = st.text_input("Email Address", placeholder="your.email@pairx.com")
            password = st.text_input("Password", type="password")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Sign In", use_container_width=True):
                    if not email or not password:
                        st.error("Please enter both email and password")
                    else:
                        exists, user = verify_firebase_password(email, password)
                        if not exists:
                            st.error("Invalid email or user not found")
                        elif email != ADMIN_EMAIL:
                            if not any(email.endswith(domain) for domain in ALLOWED_DOMAINS):
                                st.error(f"Access denied")
                            else:
                                role, emp_id, name = validate_user(email)
                                if not role:
                                    st.error("Email not found in employee database")
                                else:
                                    st.session_state.authenticated = True
                                    st.session_state.user_email = email
                                    st.session_state.user_role = role
                                    st.session_state.employee_id = emp_id
                                    st.session_state.user_name = name
                                    st.session_state.view_as = role
                                    st.rerun()
                        else:
                            role, emp_id, name = validate_user(email)
                            if not role:
                                st.error("Email not found in employee database")
                            else:
                                st.session_state.authenticated = True
                                st.session_state.user_email = email
                                st.session_state.user_role = role
                                st.session_state.employee_id = emp_id
                                st.session_state.user_name = name
                                st.session_state.view_as = role
                                st.rerun()
            with col2:
                if st.button("Forgot Password?", use_container_width=True):
                    st.session_state.show_forgot_password = True
                    st.rerun()
    firebase_login()
    st.stop()

# ---- User Info (and view select) Bar ----
cols = st.columns([3, 3, 2])
with cols[0]:
    st.markdown(
        f'<div class="user-info">{st.session_state.user_name} ({st.session_state.user_email})</div>',
        unsafe_allow_html=True)
with cols[1]:
    current_role = st.session_state.user_role
    # Only admins get all; manager gets only Employee/Manager; employee gets only their role
    if current_role == "Admin":
        view_options = ["Admin", "Manager", "Employee"]
    elif current_role == "Manager":
        view_options = ["Manager", "Employee"]
    else:
        view_options = ["Employee"]
    st.session_state.view_as = st.selectbox("View as:", view_options, index=view_options.index(st.session_state.view_as or current_role), label_visibility="collapsed")
with cols[2]:
    if st.button("Logout", use_container_width=True):
        logout()
st.markdown("---")

role = st.session_state.view_as or st.session_state.user_role
emp_id = st.session_state.employee_id

if st.session_state.user_role == "Employee" and role != "Employee":
    st.warning("Access Denied: Employees can only view their own dashboard.")
    st.stop()
if st.session_state.user_role == "Manager" and role == "Admin":
    st.warning("Access Denied: Managers cannot view Admin dashboards.")
    st.stop()

# -- EMPLOYEE DASHBOARD --
if role == "Employee":
    st.header("Employee Dashboard")
    tab1, tab2 = st.tabs(["Timesheets", "Leaves"])
    # ... rest of the Employee logic (unchanged; keep as in previous completions, but no emojis) ...
    # ... [put your streamlined Timesheets/Leaves UI logic here as described above] ...
# -- MANAGER DASHBOARD --
elif role == "Manager":
    st.header("Manager Dashboard")
    tab1, tab2 = st.tabs(["Timesheets", "Leaves"])
    # ... manager logic here ...
# -- ADMIN DASHBOARD --
elif role == "Admin":
    st.header("Admin Dashboard")
    tab1, tab2, tab3 = st.tabs(["User Management", "Employee Database", "System"])
    # ... admin logic here ...
