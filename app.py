import streamlit as st
import pandas as pd
from PIL import Image
import os
from pandas.errors import EmptyDataError

# Page config
st.set_page_config(page_title="Pairx Timesheet", layout="wide", initial_sidebar_state="expanded")

# Ensure CSV files exist for first run
def check_and_create_csvs():
    files_headers = {
        "employees.csv": "EmployeeID,Name,Department,Role\n",
        "projects.csv": "ProjectID,ProjectName,StartDate,EndDate\n",
        "tasks.csv": "TaskID,ProjectID,AssignedTo,Status\n",
        "timesheets.csv": "TimesheetID,EmployeeID,Date,TaskID,HoursWorked,ApprovalStatus\n",
        "leaves.csv": "LeaveID,EmployeeID,Type,StartDate,EndDate,Status\n"
    }
    for fname, header in files_headers.items():
        if not os.path.exists(fname):
            with open(fname, "w") as f:
                f.write(header)

check_and_create_csvs()

# === DARK MODE THEME COLORS ===
page_bg = "#0f1419"
header_bg = "#1a2332"
card_bg = "#1e2a3a"
card_border = "#2d4057"
title_color = "#FFFFFF"
subtitle_color = "#5FA8D3"
feature_color = "#FF9800"
body_text = "#E8EDF2"
label_text = "#C5CDD6"
input_bg = "#273647"
input_text = "#FFFFFF"
button_bg = "#5FA8D3"
button_text = "#FFFFFF"
shadow = "rgba(0, 0, 0, 0.5)"

# === CUSTOM CSS ===
st.markdown(f"""
<style>
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Page background */
    .stApp {{
        background: {page_bg};
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        color: {body_text};
    }}
    
    /* Remove ALL default padding */
    .block-container {{
        padding: 0 !important;
        max-width: 100% !important;
    }}
    
    /* Dashboard subtitle */
    .dashboard-title {{
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        color: {subtitle_color};
        margin: 1.5rem 2rem 1.2rem 2rem;
        padding: 1rem;
        background: {header_bg};
        border-radius: 10px;
        box-shadow: 0 2px 8px {shadow};
    }}
    
    /* Feature section headers */
    .feature-header {{
        font-size: 1.3rem;
        font-weight: 700;
        color: {feature_color};
        margin: 2rem 2rem 1rem 2rem;
        padding-left: 0.5rem;
        border-left: 4px solid {feature_color};
        letter-spacing: 0.02em;
    }}
    
    /* Card containers */
    .data-card {{
        background: {card_bg};
        padding: 1.2rem;
        border-radius: 12px;
        border: 1px solid {card_border};
        box-shadow: 0 4px 12px {shadow};
        margin: 0 2rem 1.5rem 2rem;
    }}
    
    /* Content padding */
    .content-area {{
        padding: 0 2rem 2rem 2rem;
    }}
    
    /* Labels */
    label {{
        color: {label_text} !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }}
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {{
        background: {input_bg} !important;
        color: {input_text} !important;
        border: 1px solid {card_border} !important;
        border-radius: 8px !important;
        padding: 0.6rem !important;
        font-size: 1rem !important;
    }}
    
    /* Selectbox styling */
    .stSelectbox > div > div {{
        background: {input_bg} !important;
        color: {input_text} !important;
        border: 1px solid {card_border} !important;
        border-radius: 8px !important;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: {button_bg} !important;
        color: {button_text} !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 2px 6px {shadow} !important;
        transition: all 0.3s ease !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px {shadow} !important;
        opacity: 0.9;
    }}
    
    /* Radio buttons */
    .stRadio > label {{
        color: {label_text} !important;
        font-weight: 600 !important;
    }}
    
    .stRadio > div {{
        color: {body_text} !important;
    }}
    
    .stRadio > div label {{
        color: {body_text} !important;
    }}
    
    /* Form submit button */
    .stFormSubmitButton > button {{
        background: {button_bg} !important;
        color: {button_text} !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        background: {card_bg} !important;
        color: {body_text} !important;
        border: 1px solid {card_border} !important;
        border-radius: 8px !important;
    }}
    
    /* Dataframe */
    .dataframe {{
        border-radius: 8px !important;
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: {header_bg};
    }}
    
    [data-testid="stSidebar"] * {{
        color: {label_text} !important;
    }}
    
    /* Success messages */
    .stSuccess {{
        background: #4CAF50 !important;
        color: white !important;
        border-radius: 8px !important;
    }}
</style>
""", unsafe_allow_html=True)

# === WHITE HEADER WITH LOGO - PROPERLY ALIGNED ===
header_html = """
<div style="background: #FFFFFF; padding: 1.2rem 2rem; margin-bottom: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: flex; align-items: center;">
    <img src="data:image/png;base64,{}" width="70" style="margin-right: 1.5rem;">
    <h1 style="color: #1C3F5E; font-size: 2rem; margin: 0; font-weight: 700;">Pairx Timesheet Management</h1>
</div>
"""

try:
    import base64
    with open("logo.jpg", "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(header_html.format(logo_data), unsafe_allow_html=True)
except:
    st.markdown("""
    <div style="background: #FFFFFF; padding: 1.2rem 2rem; margin-bottom: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color: #1C3F5E; font-size: 2rem; margin: 0; font-weight: 700;">Pairx Timesheet Management</h1>
    </div>
    """, unsafe_allow_html=True)

# === CONTENT AREA ===
st.markdown('<div class="content-area">', unsafe_allow_html=True)

# === ROLE SELECTOR ===
role = st.sidebar.selectbox("Select Role", ["Employee", "Manager", "Admin"])

# ========== EMPLOYEE DASHBOARD ==========
if role == "Employee":
    st.markdown('<div class="dashboard-title">Employee Dashboard</div>', unsafe_allow_html=True)

    # Submit Timesheet
    st.markdown('<div class="feature-header">Submit Timesheet</div>', unsafe_allow_html=True)
    emp_id = st.text_input("Employee ID", key="emp_id_ts")
    date = st.date_input("Date")
    task_id = st.text_input("Task ID")
    hours = st.number_input("Hours Worked", min_value=0.0, step=0.5)
    
    if st.button("Submit Timesheet"):
        try:
            df = pd.read_csv("timesheets.csv")
        except EmptyDataError:
            df = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "HoursWorked", "ApprovalStatus"])
        new_id = df["TimesheetID"].max() + 1 if not df.empty else 1
        new_row = pd.DataFrame([[new_id, emp_id, str(date), task_id, hours, "Pending"]], columns=df.columns)
        out = pd.concat([df, new_row], ignore_index=True)
        out.to_csv("timesheets.csv", index=False)
        st.success("Timesheet submitted successfully!")

    # Timesheet History
    st.markdown('<div class="feature-header">My Timesheet History</div>', unsafe_allow_html=True)
    st.markdown('<div class="data-card">', unsafe_allow_html=True)
    if emp_id:
        try:
            df = pd.read_csv("timesheets.csv")
        except EmptyDataError:
            df = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "HoursWorked", "ApprovalStatus"])
        st.dataframe(df[df["EmployeeID"] == emp_id], use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Apply for Leave
    st.markdown('<div class="feature-header">Apply for Leave</div>', unsafe_allow_html=True)
    leave_type = st.selectbox("Leave Type", ["Sick", "Casual", "Earned"])
    start = st.date_input("Start Date", key="leave_start")
    end = st.date_input("End Date", key="leave_end")
    
    if st.button("Apply for Leave"):
        try:
            df = pd.read_csv("leaves.csv")
        except EmptyDataError:
            df = pd.DataFrame(columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Status"])
        new_id = df["LeaveID"].max() + 1 if not df.empty else 1
        new_row = pd.DataFrame([[new_id, emp_id, leave_type, str(start), str(end), "Pending"]], columns=df.columns)
        out = pd.concat([df, new_row], ignore_index=True)
        out.to_csv("leaves.csv", index=False)
        st.success("Leave request submitted successfully!")

    # Leave History
    st.markdown('<div class="feature-header">My Leave History</div>', unsafe_allow_html=True)
    st.markdown('<div class="data-card">', unsafe_allow_html=True)
    if emp_id:
        try:
            df = pd.read_csv("leaves.csv")
        except EmptyDataError:
            df = pd.DataFrame(columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Status"])
        st.dataframe(df[df["EmployeeID"] == emp_id], use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ========== MANAGER DASHBOARD ==========
elif role == "Manager":
    st.markdown('<div class="dashboard-title">Manager Dashboard</div>', unsafe_allow_html=True)

    # Approve Timesheets
    st.markdown('<div class="feature-header">Approve Timesheets</div>', unsafe_allow_html=True)
    try:
        df_ts = pd.read_csv("timesheets.csv")
    except EmptyDataError:
        df_ts = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "HoursWorked", "ApprovalStatus"])
    
    pending_ts = df_ts[df_ts["ApprovalStatus"] == "Pending"]
    st.markdown('<div class="data-card">', unsafe_allow_html=True)
    st.dataframe(pending_ts, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    for ix, row in pending_ts.iterrows():
        with st.expander(f"Timesheet ID: {row['TimesheetID']} - Employee: {row['EmployeeID']}"):
            action = st.radio(
                f"Decision for Timesheet {row['TimesheetID']}",
                ["Pending", "Approve", "Reject"],
                key=f"ts{row['TimesheetID']}"
            )
            if st.button(f"Update Timesheet {row['TimesheetID']}", key=f"btn_ts{row['TimesheetID']}"):
                df_ts.loc[ix, "ApprovalStatus"] = action
                df_ts.to_csv("timesheets.csv", index=False)
                st.success(f"Timesheet {row['TimesheetID']} updated to {action}!")

    # Approve Leaves
    st.markdown('<div class="feature-header">Approve Leave Applications</div>', unsafe_allow_html=True)
    try:
        df_lv = pd.read_csv("leaves.csv")
    except EmptyDataError:
        df_lv = pd.DataFrame(columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Status"])
    
    pending_lv = df_lv[df_lv["Status"] == "Pending"]
    st.markdown('<div class="data-card">', unsafe_allow_html=True)
    st.dataframe(pending_lv, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    for ix, row in pending_lv.iterrows():
        with st.expander(f"Leave ID: {row['LeaveID']} - Employee: {row['EmployeeID']}"):
            action = st.radio(
                f"Decision for Leave {row['LeaveID']}",
                ["Pending", "Approve", "Reject"],
                key=f"lv{row['LeaveID']}"
            )
            if st.button(f"Update Leave {row['LeaveID']}", key=f"btn_lv{row['LeaveID']}"):
                df_lv.loc[ix, "Status"] = action
                df_lv.to_csv("leaves.csv", index=False)
                st.success(f"Leave {row['LeaveID']} updated to {action}!")

    # Manager Reports
    st.markdown('<div class="feature-header">Manager Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="data-card">', unsafe_allow_html=True)
    approved = df_ts[df_ts["ApprovalStatus"] == "Approve"]
    st.dataframe(approved, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ========== ADMIN DASHBOARD ==========
elif role == "Admin":
    st.markdown('<div class="dashboard-title">Admin Dashboard</div>', unsafe_allow_html=True)

    # Manage Employees
    st.markdown('<div class="feature-header">Manage Employees</div>', unsafe_allow_html=True)
    try:
        df_emp = pd.read_csv("employees.csv")
    except EmptyDataError:
        df_emp = pd.DataFrame(columns=["EmployeeID", "Name", "Department", "Role"])
    
    st.markdown('<div class="data-card">', unsafe_allow_html=True)
    st.dataframe(df_emp, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Add New Employee
    st.markdown('<div class="feature-header">Add New Employee</div>', unsafe_allow_html=True)
    with st.form("Add Employee"):
        new_id = df_emp["EmployeeID"].max() + 1 if not df_emp.empty else 1
        name = st.text_input("Name")
        dept = st.text_input("Department")
        role_sel = st.selectbox("Role", ["Employee", "Manager", "Admin"])
        submitted = st.form_submit_button("Add Employee")
        
        if submitted and name:
            new_row = pd.DataFrame([[new_id, name, dept, role_sel]], columns=df_emp.columns)
            out = pd.concat([df_emp, new_row], ignore_index=True)
            out.to_csv("employees.csv", index=False)
            st.success(f"Employee {name} added successfully!")

    # Global Timesheets
    st.markdown('<div class="feature-header">Global Timesheets Report</div>', unsafe_allow_html=True)
    try:
        ts = pd.read_csv("timesheets.csv")
    except EmptyDataError:
        ts = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "HoursWorked", "ApprovalStatus"])
    
    st.markdown('<div class="data-card">', unsafe_allow_html=True)
    st.dataframe(ts, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Global Leaves
    st.markdown('<div class="feature-header">Global Leave Report</div>', unsafe_allow_html=True)
    try:
        lv = pd.read_csv("leaves.csv")
    except EmptyDataError:
        lv = pd.DataFrame(columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Status"])
    
    st.markdown('<div class="data-card">', unsafe_allow_html=True)
    st.dataframe(lv, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
