import streamlit as st
import pandas as pd
from PIL import Image
import os
from pandas.errors import EmptyDataError
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import secrets
import string
import requests

st.set_page_config(page_title="Pairx Timesheet", layout="wide", initial_sidebar_state="collapsed")

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
FIREBASE_WEB_API_KEY = st.secrets.get("firebase_web_api_key", "YOUR_WEB_API_KEY")

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
if 'view_as' not in st.session_state:
    st.session_state.view_as = None
if 'show_forgot_password' not in st.session_state:
    st.session_state.show_forgot_password = False

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
    # Centered login container
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="text-align: center; margin-top: 3rem;"><h1 style="color: #1a1a1a; font-weight: 700; font-size: 2.5rem;">Sign In</h1><p style="color: #666; font-size: 1.1rem; margin-top: 0.5rem;">Welcome back to Pairx Timesheet</p></div>', unsafe_allow_html=True)
        
        st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
        
        if st.session_state.show_forgot_password:
            st.markdown('<p style="color: #1a1a1a; font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;">Reset Password</p>', unsafe_allow_html=True)
            reset_email = st.text_input("Email Address", key="reset_email", placeholder="your.email@pairx.com")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Send Reset Link", use_container_width=True, type="primary"):
                    if not reset_email:
                        st.error("Please enter your email")
                    else:
                        success, message = send_password_reset_email(reset_email)
                        if success:
                            st.success(message)
                        else:
                            st.error(f"Error: {message}")
            with col_b:
                if st.button("Back to Login", use_container_width=True):
                    st.session_state.show_forgot_password = False
                    st.rerun()
        else:
            email = st.text_input("Email Address", placeholder="your.email@pairx.com", label_visibility="visible")
            password = st.text_input("Password", type="password", placeholder="Enter your password", label_visibility="visible")
            
            if st.button("Sign In", use_container_width=True, type="primary"):
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

# Modern Persist-AI inspired styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
    }
    
    .block-container {
        padding: 1.5rem 2rem !important;
        max-width: 1400px !important;
    }
    
    /* Form Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {
        background: #ffffff !important;
        border: 2px solid #e8ecef !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
        color: #1a1a1a !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stDateInput > div > div > input:focus,
    .stSelectbox > div > div:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Labels */
    label {
        color: #1a1a1a !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: 0.3px !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.3px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    /* Cards */
    .stat-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid #e8ecef;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #3b82f6;
        margin-bottom: 0.25rem;
    }
    
    .stat-label {
        color: #6b7280;
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1a1a1a !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }
    
    h1 {
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        font-size: 1.75rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }
    
    h3 {
        font-size: 1.25rem !important;
        margin-top: 1.5rem !important;
    }
    
    /* Dividers */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, #e8ecef, transparent) !important;
        margin: 2rem 0 !important;
    }
    
    /* Dataframes */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #e8ecef !important;
        font-weight: 600 !important;
        color: #1a1a1a !important;
    }
    
    /* Top Navigation */
    .top-nav {
        background: #ffffff;
        padding: 1rem 2rem;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .user-badge {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        padding: 0.5rem 1.25rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.875rem;
        color: #1a1a1a;
        display: inline-block;
    }
    
    /* Info/Warning/Error boxes */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
        padding: 1rem 1.25rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
header_html = """
<div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 1.5rem 2rem; margin: -1.5rem -2rem 2rem -2rem; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);">
    <div style="display: flex; align-items: center;">
        <div style="background: white; padding: 0.5rem; border-radius: 12px; margin-right: 1rem; display: flex; align-items: center; justify-content: center;">
            <img src="data:image/png;base64,{}" width="50" style="display: block;">
        </div>
        <div>
            <h1 style="color: #ffffff !important; font-size: 1.75rem !important; margin: 0 !important; font-weight: 700 !important; letter-spacing: -0.5px;">Pairx</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.875rem; font-weight: 500;">Timesheet Management System</p>
        </div>
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

if not st.session_state.authenticated:
    firebase_login()
    st.stop()

# Top Navigation Bar
st.markdown('<div class="top-nav">', unsafe_allow_html=True)
cols = st.columns([3, 3, 2])
with cols[0]:
    st.markdown(f'<span class="user-badge">{st.session_state.user_name}</span>', unsafe_allow_html=True)

with cols[1]:
    if st.session_state.user_role == "Admin":
        view_options = ["Admin", "Manager", "Employee"]
        st.session_state.view_as = st.selectbox("View as", view_options, index=view_options.index(st.session_state.view_as))
    else:
        st.markdown(f'<span class="user-badge">{st.session_state.user_role}</span>', unsafe_allow_html=True)

with cols[2]:
    if st.button("Logout", use_container_width=True):
        logout()
st.markdown('</div>', unsafe_allow_html=True)

actual_role = st.session_state.user_role
role = st.session_state.view_as
emp_id = st.session_state.employee_id

if actual_role == "Employee" and role != "Employee":
    st.error("Access Denied")
    st.stop()

if actual_role == "Manager" and role == "Admin":
    st.error("Access Denied")
    st.stop()

# Continue with the same dashboard logic but with improved UI...
# The rest of the code remains the same, just with better visual presentation

if role == "Employee":
    st.markdown("## Employee Dashboard")
    
    # Stats cards
    try:
        df_ts = pd.read_csv("timesheets.csv")
        df_lv = pd.read_csv("leaves.csv")
        my_timesheets = df_ts[df_ts["EmployeeID"] == emp_id]
        my_leaves = df_lv[df_lv["EmployeeID"] == emp_id]
        pending_ts = len(my_timesheets[my_timesheets["ApprovalStatus"] == "Pending"])
        pending_lv = len(my_leaves[my_leaves["Status"] == "Pending"])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="stat-card"><div class="stat-number">{len(my_timesheets)}</div><div class="stat-label">Total Timesheets</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stat-card"><div class="stat-number">{pending_ts}</div><div class="stat-label">Pending Timesheets</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="stat-card"><div class="stat-number">{len(my_leaves)}</div><div class="stat-label">Total Leaves</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="stat-card"><div class="stat-number">{pending_lv}</div><div class="stat-label">Pending Leaves</div></div>', unsafe_allow_html=True)
    except:
        pass
    
    st.markdown("###Submit Timesheet")
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date")
        task_id = st.text_input("Task ID")
    with col2:
        hours = st.number_input("Hours Worked", min_value=0.0, step=0.5)
        
    task_desc = st.text_area("Task Description", height=100)
    
    if st.button("Submit Timesheet", type="primary"):
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
            st.success("Timesheet submitted successfully!")
            st.rerun()
    
    st.markdown("---")
    st.markdown("### My Timesheet History")
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
            st.download_button("Download Timesheets", csv, "my_timesheets.csv", type="primary")
    except:
        st.info("No timesheet history")
    
    st.markdown("---")
    st.markdown("### Apply for Leave")
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
    
    leave_reason = st.text_area("Reason for Leave", height=100)
    
    if st.button("Submit Leave Request", type="primary"):
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
    st.markdown("### My Leave History")
    try:
        df_lv = pd.read_csv("leaves.csv")
        if "Reason" not in df_lv.columns:
            df_lv["Reason"] = ""
        if "ManagerComment" not in df_lv.columns:
            df_lv["ManagerComment"] = ""
        my_leaves = df_lv[df_lv["EmployeeID"] == emp_id]
        
        if my_leaves.empty:
            st.info("No leave history")
        else:
            st.dataframe(my_leaves, use_container_width=True, height=300)
            csv = my_leaves.to_csv(index=False)
            st.download_button("Download Leave History", csv, "my_leaves.csv", type="primary")
    except:
        st.info("No leave history")

elif role == "Manager":
    st.markdown("## Manager Dashboard")
    
    my_team = get_my_team_employees(emp_id)
    
    if not my_team:
        st.info("No employees assigned to you")
    else:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{len(my_team)}</div><div class="stat-label">Team Members</div></div>', unsafe_allow_html=True)
    
    st.markdown("### Pending Timesheets")
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
                st.write(f"**Task:** {row['TaskID']}")
                st.write(f"**Description:** {row.get('TaskDescription', 'N/A')}")
                st.write(f"**Hours:** {row['HoursWorked']} | **Date:** {row['Date']}")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    action = st.radio("Decision", ["Pending", "Approve", "Reject"], key=f"ts{row['TimesheetID']}")
                with col2:
                    comment = st.text_area("Comment", key=f"cmt_ts{row['TimesheetID']}", height=80)
                
                if st.button("Update", key=f"btn_ts{row['TimesheetID']}", type="primary"):
                    if action == "Pending":
                        st.warning("Select Approve or Reject")
                    elif not comment:
                        st.error("Provide comment")
                    else:
                        df_ts.loc[ix, "ApprovalStatus"] = action
                        df_ts.loc[ix, "ManagerComment"] = comment
                        df_ts.to_csv("timesheets.csv", index=False)
                        st.success(f"Updated to {action}!")
                        st.rerun()
    
    st.markdown("---")
    st.markdown("### Pending Leave Requests")
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
                
                if st.button("Update", key=f"btn_lv{row['LeaveID']}", type="primary"):
                    if action == "Pending":
                        st.warning("Select Approve or Reject")
                    elif not comment:
                        st.error("Provide comment")
                    else:
                        df_lv.loc[ix, "Status"] = action
                        df_lv.loc[ix, "ManagerComment"] = comment
                        df_lv.to_csv("leaves.csv", index=False)
                        st.success(f"Updated to {action}!")
                        st.rerun()

elif role == "Admin":
    st.markdown("## Admin Dashboard")
    
    tab1, tab2, tab3 = st.tabs(["User Management", "Employee Database", "System"])
    
    with tab1:
        st.markdown("### Create New User")
        with st.form("create_user"):
            col1, col2 = st.columns(2)
            with col1:
                new_email = st.text_input("Email", placeholder="user@pairx.com")
            with col2:
                new_name = st.text_input("Display Name", placeholder="John Doe")
            
            send_email = st.checkbox("Send password to user's email", value=True)
            create = st.form_submit_button("Create User", type="primary")
            
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
        st.markdown("### Add Employee")
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
            
            add = st.form_submit_button("Add Employee", type="primary")
            
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
        st.markdown("### Employee List")
        try:
            df_emp = pd.read_csv("employees.csv")
            st.dataframe(df_emp, use_container_width=True, height=350)
            csv = df_emp.to_csv(index=False)
            st.download_button("Download Employee List", csv, "employees.csv", type="primary")
        except:
            st.info("No employees")
    
    with tab3:
        st.markdown("### Send Password Reset")
        with st.form("reset_password"):
            reset_email = st.text_input("User Email", placeholder="user@pairx.com")
            send_reset = st.form_submit_button("Send Reset Link", type="primary")
            
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
