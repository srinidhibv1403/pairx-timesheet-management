import streamlit as st
import pandas as pd
from PIL import Image
import os
from pandas.errors import EmptyDataError
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="Pairx Timesheet", layout="wide")

# Admin email and allowed domains
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

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'employee_id' not in st.session_state:
    st.session_state.employee_id = None

def validate_email(email):
    """Validate if email is authorized"""
    # Admin is always allowed
    if email == ADMIN_EMAIL:
        return True, "Admin"
    
    # Check if email has allowed domain
    has_valid_domain = any(email.endswith(domain) for domain in ALLOWED_DOMAINS)
    
    if not has_valid_domain:
        return False, None
    
    # Check if email is in employees database
    try:
        df_emp = pd.read_csv("employees.csv")
        if "Email" not in df_emp.columns:
            df_emp["Email"] = ""
        
        employee = df_emp[df_emp["Email"] == email]
        if not employee.empty:
            return True, employee.iloc[0]["Role"]
        else:
            return False, None
    except:
        return False, None

def google_sign_in():
    """Email-based authentication"""
    st.subheader("Sign In")
    
    st.info(f"Allowed domains: {', '.join(ALLOWED_DOMAINS)} and admin email: {ADMIN_EMAIL}")
    
    email = st.text_input("Enter your email address", placeholder="name@pairx.com or name@persist-ai.com")
    
    if st.button("Sign In"):
        if not email:
            st.error("Please enter your email address")
            return
        
        is_valid, role = validate_email(email)
        
        if is_valid:
            st.session_state.authenticated = True
            st.session_state.user_email = email
            
            # Set role and employee ID
            if email == ADMIN_EMAIL:
                st.session_state.user_role = "Admin"
                st.session_state.employee_id = "ADMIN001"
            else:
                try:
                    df_emp = pd.read_csv("employees.csv")
                    if "Email" in df_emp.columns:
                        employee = df_emp[df_emp["Email"] == email]
                        if not employee.empty:
                            st.session_state.user_role = employee.iloc[0]["Role"]
                            st.session_state.employee_id = employee.iloc[0]["EmployeeID"]
                except:
                    st.session_state.user_role = "Employee"
            
            st.success(f"Welcome! Signed in as {email}")
            st.rerun()
        else:
            if email == ADMIN_EMAIL:
                st.error("Admin authentication failed. Please contact support.")
            elif not any(email.endswith(domain) for domain in ALLOWED_DOMAINS):
                st.error(f"Access denied. Only emails from {', '.join(ALLOWED_DOMAINS)} or admin email are allowed.")
            else:
                st.error("Email not found in employee database. Please contact admin to register your account.")

def logout():
    """Logout function"""
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_role = None
    st.session_state.employee_id = None
    st.rerun()

# Theme colors
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
    
    .stApp {{
        background: {page_bg};
        font-family: 'Segoe UI', sans-serif;
        color: {body_text};
    }}
    
    .block-container {{
        padding: 2rem !important;
        max-width: 100% !important;
    }}
    
    label {{
        color: {label_text} !important;
        font-weight: 600 !important;
    }}
    
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {{
        background: {input_bg} !important;
        color: {input_text} !important;
        border: 1px solid #2d4057 !important;
        border-radius: 8px !important;
        padding: 0.6rem !important;
    }}
    
    .stButton > button,
    .stFormSubmitButton > button {{
        background: {button_bg} !important;
        color: {button_text} !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        width: 100%;
    }}
    
    .stButton > button:hover {{
        opacity: 0.9;
    }}
    
    .stRadio > div {{
        color: {body_text} !important;
    }}
    
    h1, h2, h3 {{
        color: {body_text} !important;
    }}
    
    hr {{
        border-color: #2d4057 !important;
    }}
    
    .stats-card {{
        background: {input_bg};
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #2d4057;
        text-align: center;
    }}
    
    .stats-number {{
        font-size: 2rem;
        font-weight: bold;
        color: {button_bg};
    }}
    
    .stats-label {{
        color: {label_text};
        font-size: 0.9rem;
    }}
    
    .user-info {{
        background: {input_bg};
        padding: 0.5rem 1rem;
        border-radius: 8px;
        display: inline-block;
        margin-bottom: 1rem;
    }}
</style>
""", unsafe_allow_html=True)

# Header with logo
header_html = """
<div style="background: #FFFFFF; padding: 1.2rem 2rem; margin: -2rem -2rem 2rem -2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: flex; align-items: center;">
    <img src="data:image/png;base64,{}" width="70" style="margin-right: 1.5rem;">
    <span style="color: #000000; font-size: 2rem; font-weight: 700; font-family: 'Segoe UI', sans-serif;">Pairx Timesheet Management</span>
</div>
"""

try:
    import base64
    with open("logo.jpg", "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(header_html.format(logo_data), unsafe_allow_html=True)
except:
    st.markdown('<div style="background: #FFFFFF; padding: 1.2rem 2rem; margin: -2rem -2rem 2rem -2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"><span style="color: #000000; font-size: 2rem; font-weight: 700; font-family: \'Segoe UI\', sans-serif;">Pairx Timesheet Management</span></div>', unsafe_allow_html=True)

# Check authentication
if not st.session_state.authenticated:
    google_sign_in()
    st.stop()

# Show user info and logout button
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(f'<div class="user-info">Logged in as: {st.session_state.user_email} | Role: {st.session_state.user_role}</div>', unsafe_allow_html=True)
with col2:
    if st.button("Logout"):
        logout()

st.markdown("---")

# Get role from session
role = st.session_state.user_role

# EMPLOYEE DASHBOARD
if role == "Employee":
    st.header("Employee Dashboard")
    emp_id = st.session_state.employee_id
    
    # Quick Stats
    st.subheader("Quick Stats")
    try:
        df_ts = pd.read_csv("timesheets.csv")
        df_lv = pd.read_csv("leaves.csv")
        
        my_timesheets = df_ts[df_ts["EmployeeID"] == emp_id]
        my_leaves = df_lv[df_lv["EmployeeID"] == emp_id]
        
        pending_ts = len(my_timesheets[my_timesheets["ApprovalStatus"] == "Pending"])
        approved_ts = len(my_timesheets[my_timesheets["ApprovalStatus"] == "Approve"])
        pending_lv = len(my_leaves[my_leaves["Status"] == "Pending"])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="stats-card"><div class="stats-number">{len(my_timesheets)}</div><div class="stats-label">Total Timesheets</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stats-card"><div class="stats-number">{pending_ts}</div><div class="stats-label">Pending Timesheets</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="stats-card"><div class="stats-number">{len(my_leaves)}</div><div class="stats-label">Total Leaves</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="stats-card"><div class="stats-number">{pending_lv}</div><div class="stats-label">Pending Leaves</div></div>', unsafe_allow_html=True)
    except:
        pass
    
    st.markdown("---")
    st.subheader("Submit Timesheet")
    
    date = st.date_input("Date *")
    task_id = st.text_input("Task ID *", placeholder="Enter Task ID")
    task_desc = st.text_area("Task Description *", placeholder="Describe the task you worked on", height=100)
    hours = st.number_input("Hours Worked *", min_value=0.0, step=0.5)
    
    if st.button("Submit Timesheet"):
        if not task_id or not task_id.strip():
            st.error("Please enter Task ID")
        elif not task_desc or not task_desc.strip():
            st.error("Please enter Task Description")
        elif hours <= 0:
            st.error("Please enter hours worked (must be greater than 0)")
        else:
            try:
                df = pd.read_csv("timesheets.csv")
                if "TaskDescription" not in df.columns:
                    df["TaskDescription"] = ""
                if "ManagerComment" not in df.columns:
                    df["ManagerComment"] = ""
            except EmptyDataError:
                df = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
            new_id = df["TimesheetID"].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame([[new_id, emp_id, str(date), task_id.strip(), task_desc.strip(), hours, "Pending", ""]], columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
            out = pd.concat([df, new_row], ignore_index=True)
            out.to_csv("timesheets.csv", index=False)
            st.success("Timesheet submitted successfully!")
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
            st.download_button("Download CSV", csv, "my_timesheets.csv", "text/csv")
    except EmptyDataError:
        st.info("No timesheet history")
    
    st.markdown("---")
    st.subheader("Apply for Leave")
    leave_type = st.selectbox("Leave Type *", ["Sick", "Casual", "Earned"])
    start = st.date_input("Start Date *", key="leave_start")
    end = st.date_input("End Date *", key="leave_end")
    
    if start and end:
        days_count = (end - start).days + 1
        st.info(f"Number of days: {days_count}")
    
    leave_reason = st.text_area("Reason for Leave *", placeholder="Explain why you need this leave", height=100)
    
    if st.button("Apply for Leave"):
        if start > end:
            st.error("End date must be after or equal to start date")
        elif not leave_reason or not leave_reason.strip():
            st.error("Please enter reason for leave")
        else:
            try:
                df = pd.read_csv("leaves.csv")
                if "Reason" not in df.columns:
                    df["Reason"] = ""
                if "ManagerComment" not in df.columns:
                    df["ManagerComment"] = ""
            except EmptyDataError:
                df = pd.DataFrame(columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Reason", "Status", "ManagerComment"])
            new_id = df["LeaveID"].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame([[new_id, emp_id, leave_type, str(start), str(end), leave_reason.strip(), "Pending", ""]], columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Reason", "Status", "ManagerComment"])
            out = pd.concat([df, new_row], ignore_index=True)
            out.to_csv("leaves.csv", index=False)
            st.success("Leave request submitted successfully!")
            st.rerun()
    
    st.markdown("---")
    st.subheader("My Leave History")
    try:
        df = pd.read_csv("leaves.csv")
        if "Reason" not in df.columns:
            df["Reason"] = ""
        if "ManagerComment" not in df.columns:
            df["ManagerComment"] = ""
        my_leaves = df[df["EmployeeID"] == emp_id]
        st.dataframe(my_leaves, use_container_width=True)
    except EmptyDataError:
        st.info("No leave history")

# MANAGER DASHBOARD (continues with previous code)
elif role == "Manager":
    st.header("Manager Dashboard")
    st.info("Manager dashboard - use previous enhanced code")

# ADMIN DASHBOARD
elif role == "Admin":
    st.header("Admin Dashboard")
    
    st.subheader("Add New Employee")
    with st.form("Add Employee"):
        emp_id_input = st.text_input("Employee ID *", placeholder="Enter unique Employee ID")
        name = st.text_input("Name *", placeholder="Enter name")
        email = st.text_input("Email *", placeholder="name@pairx.com or name@persist-ai.com")
        dept = st.text_input("Department *", placeholder="Enter department")
        role_sel = st.selectbox("Role *", ["Employee", "Manager", "Admin"])
        
        try:
            df_emp = pd.read_csv("employees.csv")
            if "Email" not in df_emp.columns:
                df_emp["Email"] = ""
            if "ManagerID" not in df_emp.columns:
                df_emp["ManagerID"] = ""
        except EmptyDataError:
            df_emp = pd.DataFrame(columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
        
        managers_list = ["None"]
        if not df_emp.empty:
            managers = df_emp[df_emp["Role"] == "Manager"]["EmployeeID"].astype(str).tolist()
            managers_list.extend(managers)
        
        manager_id = st.selectbox("Assign Manager ID", managers_list)
        
        submitted = st.form_submit_button("Add Employee")
        
        if submitted:
            if not emp_id_input or not emp_id_input.strip():
                st.error("Please enter Employee ID")
            elif not name or not name.strip():
                st.error("Please enter name")
            elif not email or not email.strip():
                st.error("Please enter email")
            elif not any(email.endswith(domain) for domain in ALLOWED_DOMAINS):
                st.error(f"Email must end with {' or '.join(ALLOWED_DOMAINS)}")
            elif not dept or not dept.strip():
                st.error("Please enter department")
            elif emp_id_input.strip() in df_emp["EmployeeID"].astype(str).values:
                st.error("Employee ID already exists")
            elif email in df_emp["Email"].values:
                st.error("Email already exists")
            else:
                manager_val = "" if manager_id == "None" else manager_id
                new_row = pd.DataFrame([[emp_id_input.strip(), name.strip(), email.strip(), dept.strip(), role_sel, manager_val]], columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
                out = pd.concat([df_emp, new_row], ignore_index=True)
                out.to_csv("employees.csv", index=False)
                st.success(f"Employee {name.strip()} added with email {email}!")
                st.rerun()
