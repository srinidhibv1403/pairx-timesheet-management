import streamlit as st
import pandas as pd
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import secrets
import string
import requests

st.set_page_config(page_title="Pairx Timesheet", layout="wide", initial_sidebar_state="collapsed")

ADMIN_EMAIL = "srinidhibv.cs23@bmsce.ac.in"
ALLOWED_DOMAINS = ["@persist-ai.com", "@pairx.com"]
FIREBASE_WEB_API_KEY = st.secrets.get("firebase_web_api_key", "YOUR_WEB_API_KEY")

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

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if 'show_settings' not in st.session_state:
    st.session_state.show_settings = False
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
if 'view_as' not in st.session_state:
    st.session_state.view_as = None
if 'show_forgot_password' not in st.session_state:
    st.session_state.show_forgot_password = False

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

def send_password_email(email, password, name):
    try:
        return True, "Email would be sent (email service not configured)"
    except Exception as e:
        return False, str(e)

def send_password_reset_email(email):
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
        payload = {"requestType": "PASSWORD_RESET", "email": email}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return True, "Password reset email sent successfully"
        else:
            error_data = response.json()
            return False, error_data.get("error", {}).get("message", "Failed to send reset email")
    except Exception as e:
        return False, str(e)

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

def get_my_team_employees(manager_id):
    try:
        df_emp = pd.read_csv("employees.csv")
        if "ManagerID" not in df_emp.columns:
            return []
        my_team = df_emp[df_emp["ManagerID"] == manager_id]["EmployeeID"].tolist()
        return my_team
    except:
        return []

def verify_firebase_password(email, password):
    try:
        user = firebase_auth.get_user_by_email(email)
        return True, user
    except:
        return False, None

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

def logout():
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_role = None
    st.session_state.employee_id = None
    st.session_state.user_name = None
    st.session_state.view_as = None
    st.rerun()

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    
    #MainMenu, footer, header {{visibility: hidden;}}
    [data-testid="stSidebar"] {{display: none;}}
    
    .stApp {{
        background: {page_bg};
        color: {body_text};
    }}
    
    .block-container {{
        padding: 1rem 3rem !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
    }}
    
    /* Remove ALL weird lines from selectbox */
    [data-baseweb="select"] {{
        border: none !important;
    }}
    
    [data-baseweb="select"] > div {{
        border: none !important;
        border-bottom: none !important;
        box-shadow: none !important;
    }}
    
    [data-baseweb="select"] > div > div {{
        border-bottom: none !important;
    }}
    
    [data-baseweb="select"] ul {{
        background: {input_bg} !important;
        border: 1px solid #2d4057 !important;
        border-radius: 8px !important;
    }}
    
    [data-baseweb="select"] li {{
        background: {input_bg} !important;
        color: {body_text} !important;
    }}
    
    [data-baseweb="select"] li:hover {{
        background: {button_bg}33 !important;
    }}
    
    /* Fix toggle/checkbox text visibility */
    .stCheckbox label {{
        color: {body_text} !important;
    }}
    
    .stCheckbox label span {{
        color: {body_text} !important;
    }}
    
    /* Labels */
    label {{
        color: {label_text} !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 6px !important;
    }}
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {{
        background: {input_bg} !important;
        color: {input_text} !important;
        border: 1px solid #2d4057 !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        line-height: 1.5 !important;
    }}
    
    /* Buttons */
    .stButton > button,
    .stFormSubmitButton > button,
    .stDownloadButton > button {{
        background: {button_bg} !important;
        color: {button_text} !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        width: 100%;
        transition: all 0.2s;
    }}
    
    .stButton > button:hover,
    .stFormSubmitButton > button:hover {{
        opacity: 0.9;
        transform: translateY(-1px);
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: transparent;
        border-bottom: none !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: {input_bg};
        color: {body_text};
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 14px;
        border: none !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {button_bg};
        color: {button_text};
    }}
    
    /* Headers */
    h1 {{
        font-size: 28px !important;
        font-weight: 700 !important;
        color: {body_text} !important;
        margin: 16px 0 !important;
    }}
    
    h2 {{
        font-size: 20px !important;
        font-weight: 600 !important;
        color: {body_text} !important;
        margin: 16px 0 12px 0 !important;
    }}
    
    h3 {{
        font-size: 16px !important;
        font-weight: 600 !important;
        color: {body_text} !important;
        margin: 12px 0 8px 0 !important;
    }}
    
    /* Dividers */
    hr {{
        border: none !important;
        height: 1px !important;
        background: #2d4057 !important;
        margin: 24px 0 !important;
        opacity: 0.3 !important;
    }}
    
    /* User info badge */
    .user-info {{
        background: {input_bg};
        padding: 8px 16px;
        border-radius: 20px;
        display: inline-block;
        font-size: 14px;
        font-weight: 600;
    }}
    
    /* Dataframes */
    .stDataFrame {{
        font-size: 14px !important;
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background: {input_bg} !important;
        border-radius: 8px !important;
        border: 1px solid #2d4057 !important;
        font-weight: 600 !important;
        color: {body_text} !important;
        padding: 12px !important;
        font-size: 14px !important;
    }}
    
    /* Alerts */
    .stAlert {{
        border-radius: 8px !important;
        padding: 12px !important;
        font-size: 14px !important;
    }}
    
    /* Forms */
    .stForm {{
        border: 1px solid #2d4057;
        border-radius: 12px;
        padding: 20px;
        background: {input_bg}22;
    }}
    
    /* Column spacing */
    [data-testid="column"] {{
        padding: 0 8px !important;
    }}
    
    /* Hide empty */
    .element-container:has(> .stMarkdown:empty) {{
        display: none;
    }}
        
        
    /* Mobile Responsive - Keep desktop look, just adjust spacing */
    @media (max-width: 768px) {{
        .block-container {{
            padding: 1rem 1.5rem !important;
        }}
        
        /* Smaller header padding on mobile */
        .user-info {{
            font-size: 13px !important;
        }}
        
        /* Make dataframes scrollable */
        .stDataFrame {{
            overflow-x: auto !important;
        }}
        
        /* Better column stacking on mobile */
        [data-testid="column"] {{
            min-width: 0 !important;
        }}
    }}
    
    /* Very small mobile devices */
    @media (max-width: 480px) {{
        .block-container {{
            padding: 0.75rem 1rem !important;
        }}
        
        h1 {{
            font-size: 24px !important;
        }}
        
        h2 {{
            font-size: 18px !important;
        }}
        
        .stButton > button {{
            font-size: 13px !important;
            padding: 9px 20px !important;
        }}
        
        .user-info {{
            font-size: 12px !important;
            padding: 6px 12px !important;
        }}
    }}



</style>
""", unsafe_allow_html=True)

if st.session_state.get('show_settings', False):
    if st.button("← Back to Dashboard", key="back_btn"):
        st.session_state.show_settings = False
        st.rerun()
    
    st.markdown("---")
    st.markdown("## Settings")
    st.markdown("### Appearance")
    
    dark_mode_toggle = st.checkbox("Dark Mode", value=st.session_state.dark_mode, key="theme_toggle")
    st.session_state.dark_mode = dark_mode_toggle
    
    st.markdown("---")
    st.markdown("### Account")
    
    if st.button("Logout", use_container_width=True):
        logout()
    
    st.stop()

header_html = f"""
<div style="background: {header_bg}; padding: 16px; margin: -1rem calc(-50vw + 50%) 24px calc(-50vw + 50%); box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; align-items: center; justify-content: center;">
    <div style="max-width: 1200px; width: 100%; display: flex; align-items: center; gap: 16px; padding: 0 3rem;">
        <img src="data:image/png;base64,{{}}" width="48">
        <span style="color: #000000; font-size: 20px; font-weight: 700; white-space: nowrap;">Pairx Timesheet Management</span>
    </div>
</div>
"""

try:
    import base64
    with open("logo.jpg", "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(header_html.format(logo_data), unsafe_allow_html=True)
except:
    st.markdown(header_html.format(""), unsafe_allow_html=True)

col_settings = st.columns([10, 1])
with col_settings[1]:
    if st.button("⚙️", key="settings_btn"):
        st.session_state.show_settings = True
        st.rerun()

if not st.session_state.authenticated:
    firebase_login()
    st.stop()

cols = st.columns([5, 5])
with cols[0]:
    st.markdown(f'<div class="user-info">{st.session_state.user_name}</div>', unsafe_allow_html=True)

with cols[1]:
    actual_role = st.session_state.user_role
    if actual_role == "Admin":
        view_options = ["Admin", "Manager", "Employee"]
    elif actual_role == "Manager":
        view_options = ["Manager", "Employee"]
    else:
        view_options = ["Employee"]
    
    if len(view_options) > 1:
        st.session_state.view_as = st.selectbox("View as", view_options, index=view_options.index(st.session_state.view_as or actual_role), label_visibility="collapsed")
    else:
        st.markdown(f'<div class="user-info">Role: {actual_role}</div>', unsafe_allow_html=True)

st.markdown("---")

actual_role = st.session_state.user_role
role = st.session_state.view_as or actual_role
emp_id = st.session_state.employee_id

if actual_role == "Employee" and role != "Employee":
    st.error("Access Denied")
    st.stop()

if actual_role == "Manager" and role == "Admin":
    st.error("Access Denied")
    st.stop()

if role == "Employee":
    st.header("Employee Dashboard")
    
    tab1, tab2 = st.tabs(["Timesheets", "Leaves"])
    
    with tab1:
        st.subheader("Submit Timesheet")
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date")
            task_id = st.text_input("Task ID")
        with col2:
            hours = st.number_input("Hours Worked", min_value=0.0, step=0.5)
        
        task_desc = st.text_area("Task Description", height=100)
        
        if st.button("Submit Timesheet"):
            if not task_id or not task_desc or hours <= 0:
                st.error("Please fill all fields")
            else:
                try:
                    df = pd.read_csv("timesheets.csv")
                    if "TaskDescription" not in df.columns:
                        df["TaskDescription"] = ""
                    if "ManagerComment" not in df.columns:
                        df["ManagerComment"] = ""
                except:
                    df = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
                new_id = df["TimesheetID"].max() + 1 if not df.empty else 1
                new_row = pd.DataFrame([[new_id, emp_id, str(date), task_id, task_desc, hours, "Pending", ""]], 
                                      columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
                out = pd.concat([df, new_row], ignore_index=True)
                out.to_csv("timesheets.csv", index=False)
                st.success("Timesheet submitted!")
                st.rerun()
        
        st.markdown("---")
        st.subheader("My Timesheet History")
        try:
            df = pd.read_csv("timesheets.csv")
            if "TaskDescription" not in df.columns:
                df["TaskDescription"] = ""
            if "ManagerComment" not in df.columns:
                df["ManagerComment"] = ""
            filtered_df = df[df["EmployeeID"] == emp_id]
            st.dataframe(filtered_df, use_container_width=True, height=300)
            if not filtered_df.empty:
                csv = filtered_df.to_csv(index=False)
                st.download_button("Download", csv, "timesheets.csv", "text/csv")
        except:
            st.info("No timesheet history")
    
    with tab2:
        st.subheader("Apply for Leave")
        col1, col2, col3 = st.columns(3)
        with col1:
            leave_type = st.selectbox("Leave Type", ["Sick", "Casual", "Earned"])
        with col2:
            start = st.date_input("Start Date", key="leave_start")
        with col3:
            end = st.date_input("End Date", key="leave_end")
        
        if start and end:
            days = (end - start).days + 1
            st.info(f"Duration: {days} days")
        
        leave_reason = st.text_area("Reason", height=100)
        
        if st.button("Submit Leave Request"):
            if start > end or not leave_reason:
                st.error("Invalid input")
            else:
                try:
                    df = pd.read_csv("leaves.csv")
                    if "Reason" not in df.columns:
                        df["Reason"] = ""
                    if "ManagerComment" not in df.columns:
                        df["ManagerComment"] = ""
                except:
                    df = pd.DataFrame(columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Reason", "Status", "ManagerComment"])
                new_id = df["LeaveID"].max() + 1 if not df.empty else 1
                new_row = pd.DataFrame([[new_id, emp_id, leave_type, str(start), str(end), leave_reason, "Pending", ""]], 
                                      columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Reason", "Status", "ManagerComment"])
                out = pd.concat([df, new_row], ignore_index=True)
                out.to_csv("leaves.csv", index=False)
                st.success("Leave request submitted!")
                st.rerun()
        
        st.markdown("---")
        st.subheader("My Leave History")
        try:
            df_lv = pd.read_csv("leaves.csv")
            if "Reason" not in df_lv.columns:
                df_lv["Reason"] = ""
            if "ManagerComment" not in df_lv.columns:
                df_lv["ManagerComment"] = ""
            my_leaves = df_lv[df_lv["EmployeeID"] == emp_id]
            
            approved_pending_leaves = my_leaves[my_leaves["Status"].isin(["Approved", "Pending"])]
            st.info(f"Total Approved/Pending Leaves: {len(approved_pending_leaves)}")
            
            if my_leaves.empty:
                st.info("No leave history")
            else:
                st.dataframe(my_leaves, use_container_width=True, height=300)
                csv = my_leaves.to_csv(index=False)
                st.download_button("Download", csv, "leaves.csv", "text/csv")
        except:
            st.info("No leave history")

elif role == "Manager":
    st.header("Manager Dashboard")
    
    my_team = get_my_team_employees(emp_id)
    if not my_team:
        st.info("No employees assigned")
    else:
        st.info(f"Managing {len(my_team)} employee(s)")
    
    tab1, tab2 = st.tabs(["Timesheets", "Leaves"])
    
    with tab1:
        st.subheader("Pending Timesheets")
        try:
            df_ts = pd.read_csv("timesheets.csv")
            if "TaskDescription" not in df_ts.columns:
                df_ts["TaskDescription"] = ""
            if "ManagerComment" not in df_ts.columns:
                df_ts["ManagerComment"] = ""
        except:
            df_ts = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
        
        pending_ts = df_ts[(df_ts["ApprovalStatus"] == "Pending") & (df_ts["EmployeeID"].isin(my_team))]
        
        if pending_ts.empty:
            st.info("No pending timesheets")
        else:
            st.dataframe(pending_ts, use_container_width=True, height=250)
            for ix, row in pending_ts.iterrows():
                with st.expander(f"Timesheet #{row['TimesheetID']} - Employee: {row['EmployeeID']}"):
                    st.write(f"**Task:** {row['TaskID']} | **Hours:** {row['HoursWorked']} | **Date:** {row['Date']}")
                    st.write(f"**Description:** {row.get('TaskDescription', 'N/A')}")
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        action = st.radio("Decision", ["Pending", "Approve", "Reject"], key=f"ts{row['TimesheetID']}")
                    with col2:
                        comment = st.text_area("Comment", key=f"cmt_ts{row['TimesheetID']}", height=80)
                    
                    if st.button("Update", key=f"btn_ts{row['TimesheetID']}"):
                        if action == "Pending":
                            st.warning("Select Approve or Reject")
                        elif not comment:
                            st.error("Provide comment")
                        else:
                            df_ts.loc[ix, "ApprovalStatus"] = action
                            df_ts.loc[ix, "ManagerComment"] = comment
                            df_ts.to_csv("timesheets.csv", index=False)
                            st.success(f"Updated!")
                            st.rerun()
    
    with tab2:
        st.subheader("Pending Leave Requests")
        try:
            df_lv = pd.read_csv("leaves.csv")
            if "Reason" not in df_lv.columns:
                df_lv["Reason"] = ""
            if "ManagerComment" not in df_lv.columns:
                df_lv["ManagerComment"] = ""
        except:
            df_lv = pd.DataFrame(columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Reason", "Status", "ManagerComment"])
        
        pending_lv = df_lv[(df_lv["Status"] == "Pending") & (df_lv["EmployeeID"].isin(my_team))]
        
        if pending_lv.empty:
            st.info("No pending leave requests")
        else:
            st.dataframe(pending_lv, use_container_width=True, height=250)
            for ix, row in pending_lv.iterrows():
                with st.expander(f"Leave #{row['LeaveID']} - Employee: {row['EmployeeID']}"):
                    st.write(f"**Type:** {row['Type']} | **Duration:** {row['StartDate']} to {row['EndDate']}")
                    st.write(f"**Reason:** {row.get('Reason', 'N/A')}")
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        action = st.radio("Decision", ["Pending", "Approve", "Reject"], key=f"lv{row['LeaveID']}")
                    with col2:
                        comment = st.text_area("Comment", key=f"cmt_lv{row['LeaveID']}", height=80)
                    
                    if st.button("Update", key=f"btn_lv{row['LeaveID']}"):
                        if action == "Pending":
                            st.warning("Select Approve or Reject")
                        elif not comment:
                            st.error("Provide comment")
                        else:
                            df_lv.loc[ix, "Status"] = action
                            df_lv.loc[ix, "ManagerComment"] = comment
                            df_lv.to_csv("leaves.csv", index=False)
                            st.success(f"Updated!")
                            st.rerun()

elif role == "Admin":
    st.header("Admin Dashboard")
    
    tab1, tab2, tab3 = st.tabs(["User Management", "Employee Database", "System"])
    
    with tab1:
        st.subheader("Create Firebase User")
        with st.form("create_user"):
            col1, col2 = st.columns(2)
            with col1:
                new_email = st.text_input("Email", placeholder="user@pairx.com")
            with col2:
                new_name = st.text_input("Display Name", placeholder="John Doe")
            
            send_email = st.checkbox("Send password to user's email", value=True)
            create = st.form_submit_button("Create User")
            
            if create:
                if not new_email or not new_name:
                    st.error("All fields required")
                elif not any(new_email.endswith(domain) for domain in ALLOWED_DOMAINS):
                    st.error(f"Email must end with {' or '.join(ALLOWED_DOMAINS)}")
                else:
                    try:
                        auto_password = generate_password()
                        user = firebase_auth.create_user(email=new_email, password=auto_password, display_name=new_name)
                        st.success(f"User created: {user.email}")
                        if not send_email:
                            st.info(f"Password: {auto_password}")
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    with tab2:
        st.subheader("Add Employee")
        with st.form("add_employee"):
            col1, col2 = st.columns(2)
            with col1:
                emp_id_input = st.text_input("Employee ID", placeholder="EMP001")
                emp_name = st.text_input("Name", placeholder="John Doe")
                emp_email = st.text_input("Email", placeholder="john@pairx.com")
            with col2:
                emp_dept = st.text_input("Department", placeholder="Engineering")
                emp_role_input = st.selectbox("Role", ["Employee", "Manager", "Admin"])
                
                if emp_role_input == "Employee":
                    try:
                        df_emp = pd.read_csv("employees.csv")
                        if "ManagerID" not in df_emp.columns:
                            df_emp["ManagerID"] = ""
                    except:
                        df_emp = pd.DataFrame(columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
                    
                    manager_list = ["None"]
                    if not df_emp.empty:
                        managers = df_emp[df_emp["Role"].isin(["Manager", "Admin"])][["EmployeeID", "Name"]].values
                        manager_list.extend([f"{m[0]} - {m[1]}" for m in managers])
                    selected_manager = st.selectbox("Assign Manager", manager_list)
                else:
                    selected_manager = "None"
            
            add = st.form_submit_button("Add Employee")
            
            if add:
                if not emp_id_input or not emp_name or not emp_email or not emp_dept:
                    st.error("All fields required")
                elif not any(emp_email.endswith(domain) for domain in ALLOWED_DOMAINS):
                    st.error(f"Email must end with {' or '.join(ALLOWED_DOMAINS)}")
                else:
                    try:
                        df_emp = pd.read_csv("employees.csv")
                    except:
                        df_emp = pd.DataFrame(columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
                    
                    if emp_id_input in df_emp["EmployeeID"].astype(str).values:
                        st.error("Employee ID exists")
                    elif emp_email in df_emp["Email"].values:
                        st.error("Email exists")
                    else:
                        manager_id = "" if selected_manager == "None" else selected_manager.split(" - ")[0]
                        new_row = pd.DataFrame([[emp_id_input, emp_name, emp_email, emp_dept, emp_role_input, manager_id]], 
                                              columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
                        out = pd.concat([df_emp, new_row], ignore_index=True)
                        out.to_csv("employees.csv", index=False)
                        st.success(f"Added {emp_name}")
                        st.rerun()
        
        st.markdown("---")
        st.subheader("Employee List")
        try:
            df_emp = pd.read_csv("employees.csv")
            st.dataframe(df_emp, use_container_width=True, height=300)
            csv = df_emp.to_csv(index=False)
            st.download_button("Download", csv, "employees.csv", "text/csv")
            
            st.markdown("### Delete Employee")
            delete_options = [f"{row['EmployeeID']} - {row['Name']} ({row['Email']})" for _, row in df_emp.iterrows()]
            to_delete = st.selectbox("Select employee to delete", ["Select..."] + delete_options, key="delete_selector")
            
            if to_delete != "Select...":
                if st.button("Delete Employee"):
                    emp_id_to_delete = to_delete.split(" - ")[0]
                    df_emp_fresh = pd.read_csv("employees.csv")
                    df_emp_fresh = df_emp_fresh[df_emp_fresh["EmployeeID"].astype(str) != emp_id_to_delete]
                    df_emp_fresh.to_csv("employees.csv", index=False)
                    st.success(f"Deleted {emp_id_to_delete}")
                    st.rerun()
        except:
            st.info("No employees")
    
    with tab3:
        st.subheader("Send Password Reset")
        with st.form("reset_password"):
            reset_email = st.text_input("User Email", placeholder="user@pairx.com")
            send_reset = st.form_submit_button("Send Reset Link")
            
            if send_reset:
                if not reset_email:
                    st.error("Enter email")
                elif not any(reset_email.endswith(domain) for domain in ALLOWED_DOMAINS):
                    st.error(f"Email must end with {' or '.join(ALLOWED_DOMAINS)}")
                else:
                    success, message = send_password_reset_email(reset_email)
                    if success:
                        st.success(message)
                    else:
                        st.error(f"Error: {message}")


