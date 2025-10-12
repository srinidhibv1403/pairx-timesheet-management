import streamlit as st
import pandas as pd
from PIL import Image
import os
from pandas.errors import EmptyDataError
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

st.set_page_config(page_title="Pairx Timesheet", layout="wide")

# Initialize Firebase Admin SDK
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

ADMIN_EMAIL = "srinidhibv.cs23@bmsce.ac.in"
ALLOWED_DOMAINS = ["@persist-ai.com", "@pairx.com"]

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

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'employee_id' not in st.session_state:
    st.session_state.employee_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

def validate_user(email):
    if email == ADMIN_EMAIL:
        return "Admin", "ADMIN001", "Admin"
    try:
        df_emp = pd.read_csv("employees.csv")
        if "Email" not in df_emp.columns:
            df_emp["Email"] = ""
        employee = df_emp[df_emp["Email"] == email]
        if not employee.empty:
            return employee.iloc[0]["Role"], employee.iloc[0]["EmployeeID"], employee.iloc[0]["Name"]
    except:
        pass
    return None, None, None

def verify_firebase_password(email, password):
    try:
        user = firebase_auth.get_user_by_email(email)
        return True, user
    except:
        return False, None

def firebase_login():
    st.markdown("### Sign In to Pairx Timesheet")
    st.info(f"Allowed: {ADMIN_EMAIL} or emails ending with {', '.join(ALLOWED_DOMAINS)}")
    
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="your.email@pairx.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In")
        
        if submit:
            if not email or not password:
                st.error("Please enter both email and password")
                return
            
            exists, user = verify_firebase_password(email, password)
            
            if not exists:
                st.error("Invalid email or user not found. Contact admin.")
                return
            
            if email != ADMIN_EMAIL:
                if not any(email.endswith(domain) for domain in ALLOWED_DOMAINS):
                    st.error(f"Access denied. Only {', '.join(ALLOWED_DOMAINS)} emails allowed.")
                    return
            
            role, emp_id, name = validate_user(email)
            
            if not role:
                st.error("Email not found in employee database. Contact admin.")
                return
            
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.user_role = role
            st.session_state.employee_id = emp_id
            st.session_state.user_name = name
            st.success(f"Welcome {name}!")
            st.rerun()

def logout():
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_role = None
    st.session_state.employee_id = None
    st.session_state.user_name = None
    st.rerun()

page_bg = "#0f1419"
body_text = "#E8EDF2"
label_text = "#C5CDD6"
input_bg = "#273647"
input_text = "#FFFFFF"
button_bg = "#5FA8D3"
button_text = "#FFFFFF"

st.markdown(f"""
<style>
    #MainMenu, footer, header {{visibility: hidden;}}
    [data-testid="stSidebar"] {{display: none;}}
    .stApp {{background: {page_bg}; font-family: 'Segoe UI', sans-serif; color: {body_text};}}
    .block-container {{padding: 2rem !important; max-width: 100% !important;}}
    label {{color: {label_text} !important; font-weight: 600 !important;}}
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stDateInput > div > div > input,
    .stSelectbox > div > div, .stTextArea > div > div > textarea {{
        background: {input_bg} !important; color: {input_text} !important;
        border: 1px solid #2d4057 !important; border-radius: 8px !important; padding: 0.6rem !important;
    }}
    .stButton > button, .stFormSubmitButton > button {{
        background: {button_bg} !important; color: {button_text} !important;
        border-radius: 8px !important; padding: 0.6rem 2rem !important;
        font-weight: 600 !important; width: 100%;
    }}
    .stats-card {{background: {input_bg}; padding: 1rem; border-radius: 8px; border: 1px solid #2d4057; text-align: center;}}
    .stats-number {{font-size: 2rem; font-weight: bold; color: {button_bg};}}
    .stats-label {{color: {label_text}; font-size: 0.9rem;}}
    .user-info {{background: {input_bg}; padding: 0.5rem 1rem; border-radius: 8px; display: inline-block; margin-bottom: 1rem;}}
</style>
""", unsafe_allow_html=True)

header_html = """
<div style="background: #FFFFFF; padding: 1.2rem 2rem; margin: -2rem -2rem 2rem -2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: flex; align-items: center;">
    <img src="data:image/png;base64,{}" width="70" style="margin-right: 1.5rem;">
    <span style="color: #000000; font-size: 2rem; font-weight: 700;">Pairx Timesheet Management</span>
</div>
"""

try:
    import base64
    with open("logo.jpg", "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(header_html.format(logo_data), unsafe_allow_html=True)
except:
    st.markdown('<div style="background: #FFFFFF; padding: 1.2rem 2rem; margin: -2rem -2rem 2rem -2rem;"><span style="color: #000000; font-size: 2rem; font-weight: 700;">Pairx Timesheet Management</span></div>', unsafe_allow_html=True)

if not st.session_state.authenticated:
    firebase_login()
    st.stop()

col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(f'<div class="user-info">👤 {st.session_state.user_name} ({st.session_state.user_email}) | Role: {st.session_state.user_role}</div>', unsafe_allow_html=True)
with col2:
    if st.button("Logout"):
        logout()

st.markdown("---")

role = st.session_state.user_role
emp_id = st.session_state.employee_id

if role == "Employee":
    st.header("Employee Dashboard")
    st.subheader("Submit Timesheet")
    date = st.date_input("Date *")
    task_id = st.text_input("Task ID *")
    task_desc = st.text_area("Task Description *", height=100)
    hours = st.number_input("Hours Worked *", min_value=0.0, step=0.5)
    
    if st.button("Submit Timesheet"):
        if not task_id or not task_desc or hours <= 0:
            st.error("Please fill all fields")
        else:
            try:
                df = pd.read_csv("timesheets.csv")
            except:
                df = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
            new_id = df["TimesheetID"].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame([[new_id, emp_id, str(date), task_id, task_desc, hours, "Pending", ""]], 
                                  columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
            out = pd.concat([df, new_row], ignore_index=True)
            out.to_csv("timesheets.csv", index=False)
            st.success("Timesheet submitted!")
            st.rerun()

elif role == "Admin":
    st.header("Admin Dashboard")
    st.subheader("Create New User in Firebase")
    with st.form("create_user"):
        new_email = st.text_input("Email *")
        new_password = st.text_input("Password *", type="password")
        new_name = st.text_input("Display Name *")
        create = st.form_submit_button("Create User")
        
        if create:
            if new_email and new_password and new_name:
                try:
                    user = firebase_auth.create_user(email=new_email, password=new_password, display_name=new_name)
                    st.success(f"✅ User created: {user.email}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.markdown("---")
    st.subheader("Add to Employee Database")
    with st.form("add_employee"):
        emp_id_input = st.text_input("Employee ID *")
        emp_name = st.text_input("Name *")
        emp_email = st.text_input("Email *")
        emp_dept = st.text_input("Department *")
        emp_role = st.selectbox("Role *", ["Employee", "Manager", "Admin"])
        add = st.form_submit_button("Add Employee")
        
        if add:
            if emp_id_input and emp_name and emp_email and emp_dept:
                try:
                    df_emp = pd.read_csv("employees.csv")
                except:
                    df_emp = pd.DataFrame(columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
                new_row = pd.DataFrame([[emp_id_input, emp_name, emp_email, emp_dept, emp_role, ""]], 
                                      columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
                out = pd.concat([df_emp, new_row], ignore_index=True)
                out.to_csv("employees.csv", index=False)
                st.success(f"✅ Employee added!")
                st.rerun()
