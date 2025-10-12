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

st.set_page_config(page_title="Pairx Timesheet", layout="wide")

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
                        st.error("Invalid email or user not found. Contact admin.")
                    elif email != ADMIN_EMAIL:
                        if not any(email.endswith(domain) for domain in ALLOWED_DOMAINS):
                            st.error(f"Access denied. Only {', '.join(ALLOWED_DOMAINS)} emails allowed.")
                        else:
                            role, emp_id, name = validate_user(email)
                            if not role:
                                st.error("Email not found in employee database. Contact admin.")
                            else:
                                st.session_state.authenticated = True
                                st.session_state.user_email = email
                                st.session_state.user_role = role
                                st.session_state.employee_id = emp_id
                                st.session_state.user_name = name
                                st.session_state.view_as = role
                                st.success(f"Welcome {name}!")
                                st.rerun()
                    else:
                        role, emp_id, name = validate_user(email)
                        if not role:
                            st.error("Email not found in employee database. Contact admin.")
                        else:
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.session_state.user_role = role
                            st.session_state.employee_id = emp_id
                            st.session_state.user_name = name
                            st.session_state.view_as = role
                            st.success(f"Welcome {name}!")
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
    .user-info {{background: {input_bg}; padding: 0.5rem 1rem; border-radius: 8px; display: inline-block;}}
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

cols = st.columns([3, 3, 2])
with cols[0]:
    st.markdown(f'<div class="user-info" style="margin: 0;">{st.session_state.user_name} ({st.session_state.user_email})</div>', unsafe_allow_html=True)

with cols[1]:
    if st.session_state.user_role == "Admin":
        view_options = ["Admin", "Manager", "Employee"]
        st.session_state.view_as = st.selectbox("View as:", view_options, index=view_options.index(st.session_state.view_as), label_visibility="collapsed")
    else:
        st.markdown(f'<div class="user-info" style="margin: 0;">Role: {st.session_state.user_role}</div>', unsafe_allow_html=True)

with cols[2]:
    if st.button("Logout", use_container_width=True):
        logout()

st.markdown("---")

role = st.session_state.view_as
emp_id = st.session_state.employee_id

if role == "Employee":
    st.header("Employee Dashboard")
    
    st.subheader("Change Password")
    with st.expander("Reset My Password"):
        if st.button("Send Password Reset Email"):
            success, message = send_password_reset_email(st.session_state.user_email)
            if success:
                st.success(message)
                st.info("Check your email for the reset link")
            else:
                st.error(f"Error: {message}")
    
    st.markdown("---")
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
        st.dataframe(filtered_df, use_container_width=True)
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False)
            st.download_button("Download Timesheets", csv, "my_timesheets.csv", "text/csv")
    except:
        st.info("No timesheet history")
    
    st.markdown("---")
    st.subheader("Apply for Leave")
    leave_type = st.selectbox("Leave Type *", ["Sick", "Casual", "Earned"])
    start = st.date_input("Start Date *", key="leave_start")
    end = st.date_input("End Date *", key="leave_end")
    if start and end:
        days = (end - start).days + 1
        st.info(f"Days: {days}")
    leave_reason = st.text_area("Reason *", height=100)
    
    if st.button("Apply for Leave"):
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
            st.success("Leave applied!")
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
        
        if my_leaves.empty:
            st.info("No leave history")
        else:
            st.dataframe(my_leaves, use_container_width=True)
            csv = my_leaves.to_csv(index=False)
            st.download_button("Download Leave History", csv, "my_leaves.csv", "text/csv")
    except:
        st.info("No leave history")

elif role == "Manager":
    st.header("Manager Dashboard")
    
    st.subheader("Approve Timesheets")
    try:
        df_ts = pd.read_csv("timesheets.csv")
        if "TaskDescription" not in df_ts.columns:
            df_ts["TaskDescription"] = ""
        if "ManagerComment" not in df_ts.columns:
            df_ts["ManagerComment"] = ""
    except:
        df_ts = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
    
    pending_ts = df_ts[df_ts["ApprovalStatus"] == "Pending"]
    if pending_ts.empty:
        st.info("No pending timesheets")
    else:
        st.dataframe(pending_ts, use_container_width=True)
        for ix, row in pending_ts.iterrows():
            with st.expander(f"Timesheet #{row['TimesheetID']} - Employee: {row['EmployeeID']}"):
                st.write(f"**Task:** {row['TaskID']}")
                st.write(f"**Description:** {row.get('TaskDescription', 'N/A')}")
                st.write(f"**Hours:** {row['HoursWorked']}")
                st.write(f"**Date:** {row['Date']}")
                
                action = st.radio("Decision *", ["Pending", "Approve", "Reject"], key=f"ts{row['TimesheetID']}")
                comment = st.text_area("Reason *", key=f"cmt_ts{row['TimesheetID']}", height=80)
                
                if st.button("Update", key=f"btn_ts{row['TimesheetID']}"):
                    if action == "Pending":
                        st.warning("Select Approve or Reject")
                    elif not comment:
                        st.error("Provide reason")
                    else:
                        df_ts.loc[ix, "ApprovalStatus"] = action
                        df_ts.loc[ix, "ManagerComment"] = comment
                        df_ts.to_csv("timesheets.csv", index=False)
                        st.success(f"Updated to {action}!")
                        st.rerun()
    
    st.markdown("---")
    st.subheader("Approve Leaves")
    try:
        df_lv = pd.read_csv("leaves.csv")
        if "Reason" not in df_lv.columns:
            df_lv["Reason"] = ""
        if "ManagerComment" not in df_lv.columns:
            df_lv["ManagerComment"] = ""
    except:
        df_lv = pd.DataFrame(columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Reason", "Status", "ManagerComment"])
    
    pending_lv = df_lv[df_lv["Status"] == "Pending"]
    if pending_lv.empty:
        st.info("No pending leaves")
    else:
        st.dataframe(pending_lv, use_container_width=True)
        for ix, row in pending_lv.iterrows():
            with st.expander(f"Leave #{row['LeaveID']} - Employee: {row['EmployeeID']}"):
                st.write(f"**Type:** {row['Type']}")
                st.write(f"**Dates:** {row['StartDate']} to {row['EndDate']}")
                st.write(f"**Reason:** {row.get('Reason', 'N/A')}")
                
                action = st.radio("Decision *", ["Pending", "Approve", "Reject"], key=f"lv{row['LeaveID']}")
                comment = st.text_area("Reason *", key=f"cmt_lv{row['LeaveID']}", height=80)
                
                if st.button("Update", key=f"btn_lv{row['LeaveID']}"):
                    if action == "Pending":
                        st.warning("Select Approve or Reject")
                    elif not comment:
                        st.error("Provide reason")
                    else:
                        df_lv.loc[ix, "Status"] = action
                        df_lv.loc[ix, "ManagerComment"] = comment
                        df_lv.to_csv("leaves.csv", index=False)
                        st.success(f"Updated to {action}!")
                        st.rerun()

elif role == "Admin":
    st.header("Admin Dashboard")
    
    st.subheader("Create Firebase User")
    with st.form("create_user"):
        new_email = st.text_input("Email *", placeholder="user@pairx.com")
        new_name = st.text_input("Display Name *", placeholder="John Doe")
        send_email = st.checkbox("Send password to user's email", value=True)
        create = st.form_submit_button("Create User")
        
        if create:
            if not new_email or not new_name:
                st.error("All fields are required")
            elif not any(new_email.endswith(domain) for domain in ALLOWED_DOMAINS):
                st.error(f"Email must end with {' or '.join(ALLOWED_DOMAINS)}")
            else:
                try:
                    auto_password = generate_password()
                    user = firebase_auth.create_user(email=new_email, password=auto_password, display_name=new_name)
                    st.success(f"User created: {user.email}")
                    
                    if send_email:
                        success, message = send_password_email(new_email, auto_password, new_name)
                        if success:
                            st.success("Password sent to user's email")
                        else:
                            st.warning(f"User created but email failed: {message}")
                            st.info(f"Temporary Password: {auto_password}")
                    else:
                        st.info(f"Temporary Password: {auto_password}")
                        st.warning("Share this password with the user")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.markdown("---")
    st.subheader("Send Password Reset Link")
    with st.form("reset_user_password"):
        reset_email = st.text_input("User Email", placeholder="user@pairx.com")
        send_reset = st.form_submit_button("Send Reset Link")
        
        if send_reset:
            if not reset_email:
                st.error("Please enter email")
            elif not any(reset_email.endswith(domain) for domain in ALLOWED_DOMAINS):
                st.error(f"Email must end with {' or '.join(ALLOWED_DOMAINS)}")
            else:
                success, message = send_password_reset_email(reset_email)
                if success:
                    st.success(message)
                else:
                    st.error(f"Error: {message}")
    
    st.markdown("---")
    st.subheader("Add Employee to Database")
    
    try:
        df_emp = pd.read_csv("employees.csv")
        if "ManagerID" not in df_emp.columns:
            df_emp["ManagerID"] = ""
    except:
        df_emp = pd.DataFrame(columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
    
    with st.form("add_employee"):
        emp_id_input = st.text_input("Employee ID *", placeholder="EMP001")
        emp_name = st.text_input("Name *", placeholder="John Doe")
        emp_email = st.text_input("Email *", placeholder="john@pairx.com")
        emp_dept = st.text_input("Department *", placeholder="Engineering")
        emp_role_input = st.selectbox("Role *", ["Employee", "Manager", "Admin"])
        
        selected_manager = "None"
        if emp_role_input == "Employee":
            manager_list = ["None"]
            if not df_emp.empty:
                managers = df_emp[df_emp["Role"].isin(["Manager", "Admin"])][["EmployeeID", "Name"]].values
                manager_list.extend([f"{m[0]} - {m[1]}" for m in managers])
            selected_manager = st.selectbox("Assign Manager", manager_list)
        else:
            st.info("Manager assignment is only for employees")
        
        add = st.form_submit_button("Add to Database")
        
        if add:
            if not emp_id_input or not emp_name or not emp_email or not emp_dept:
                st.error("All fields are required")
            elif not any(emp_email.endswith(domain) for domain in ALLOWED_DOMAINS):
                st.error(f"Email must end with {' or '.join(ALLOWED_DOMAINS)}")
            elif emp_id_input in df_emp["EmployeeID"].astype(str).values:
                st.error("Employee ID already exists")
            elif emp_email in df_emp["Email"].values:
                st.error("Email already exists in database")
            else:
                manager_id = "" if selected_manager == "None" else selected_manager.split(" - ")[0]
                new_row = pd.DataFrame([[emp_id_input, emp_name, emp_email, emp_dept, emp_role_input, manager_id]], 
                                      columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
                out = pd.concat([df_emp, new_row], ignore_index=True)
                out.to_csv("employees.csv", index=False)
                st.success(f"Added {emp_name} to database")
                st.rerun()
    
    st.markdown("---")
    st.subheader("Manage Employees")
    
    try:
        df_emp = pd.read_csv("employees.csv")
        if "ManagerID" not in df_emp.columns:
            df_emp["ManagerID"] = ""
    except:
        df_emp = pd.DataFrame(columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
    
    if df_emp.empty:
        st.info("No employees in database")
    else:
        st.dataframe(df_emp, use_container_width=True)
        csv = df_emp.to_csv(index=False)
        st.download_button("Download Employee List", csv, "employees.csv", "text/csv")
        
        st.markdown("### Delete Employee")
        delete_options = [f"{row['EmployeeID']} - {row['Name']} ({row['Email']})" for _, row in df_emp.iterrows()]
        to_delete = st.selectbox("Select employee to delete", ["Select..."] + delete_options, key="delete_selector")
        
        if to_delete != "Select...":
            if st.button("Delete Employee", key="delete_btn"):
                emp_id_to_delete = to_delete.split(" - ")[0]
                df_emp_fresh = pd.read_csv("employees.csv")
                df_emp_fresh = df_emp_fresh[df_emp_fresh["EmployeeID"].astype(str) != emp_id_to_delete]
                df_emp_fresh.to_csv("employees.csv", index=False)
                st.success(f"Deleted employee {emp_id_to_delete}")
                st.rerun()
            st.warning("This removes from database only. Firebase account remains.")
