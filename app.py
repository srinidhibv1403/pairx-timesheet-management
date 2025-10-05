import streamlit as st
import pandas as pd
from PIL import Image
import os
from pandas.errors import EmptyDataError

st.set_page_config(page_title="Pairx Timesheet", layout="wide")

def check_and_create_csvs():
    files_headers = {
        "employees.csv": "EmployeeID,Name,Department,Role\n",
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

# Role selector
role = st.selectbox("Select Your Role", ["Employee", "Manager", "Admin"])
st.markdown("---")

# EMPLOYEE DASHBOARD
if role == "Employee":
    st.header("Employee Dashboard")
    
    st.subheader("Submit Timesheet")
    emp_id = st.text_input("Employee ID *", placeholder="Enter your Employee ID")
    date = st.date_input("Date *")
    task_id = st.text_input("Task ID *", placeholder="Enter Task ID")
    task_desc = st.text_area("Task Description *", placeholder="Describe the task you worked on", height=100)
    hours = st.number_input("Hours Worked *", min_value=0.0, step=0.5)
    
    if st.button("Submit Timesheet"):
        if not emp_id or not emp_id.strip():
            st.error("Please enter Employee ID")
        elif not task_id or not task_id.strip():
            st.error("Please enter Task ID")
        elif not task_desc or not task_desc.strip():
            st.error("Please enter Task Description")
        elif hours <= 0:
            st.error("Please enter hours worked (must be greater than 0)")
        else:
            try:
                df = pd.read_csv("timesheets.csv")
                # Add missing columns if old format
                if "TaskDescription" not in df.columns:
                    df["TaskDescription"] = ""
                if "ManagerComment" not in df.columns:
                    df["ManagerComment"] = ""
            except EmptyDataError:
                df = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
            new_id = df["TimesheetID"].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame([[new_id, emp_id.strip(), str(date), task_id.strip(), task_desc.strip(), hours, "Pending", ""]], columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
            out = pd.concat([df, new_row], ignore_index=True)
            out.to_csv("timesheets.csv", index=False)
            st.success("Timesheet submitted successfully!")
    
    st.markdown("---")
    st.subheader("My Timesheet History")
    if emp_id and emp_id.strip():
        try:
            df = pd.read_csv("timesheets.csv")
            # Add missing columns if old format
            if "TaskDescription" not in df.columns:
                df["TaskDescription"] = ""
            if "ManagerComment" not in df.columns:
                df["ManagerComment"] = ""
        except EmptyDataError:
            df = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
        st.dataframe(df[df["EmployeeID"] == emp_id.strip()], use_container_width=True)
    else:
        st.info("Enter your Employee ID above to view history")
    
    st.markdown("---")
    st.subheader("Apply for Leave")
    leave_type = st.selectbox("Leave Type *", ["Sick", "Casual", "Earned"])
    start = st.date_input("Start Date *", key="leave_start")
    end = st.date_input("End Date *", key="leave_end")
    leave_reason = st.text_area("Reason for Leave *", placeholder="Explain why you need this leave", height=100)
    
    if st.button("Apply for Leave"):
        if not emp_id or not emp_id.strip():
            st.error("Please enter Employee ID first")
        elif start > end:
            st.error("End date must be after or equal to start date")
        elif not leave_reason or not leave_reason.strip():
            st.error("Please enter reason for leave")
        else:
            try:
                df = pd.read_csv("leaves.csv")
                # Add missing columns if old format
                if "Reason" not in df.columns:
                    df["Reason"] = ""
                if "ManagerComment" not in df.columns:
                    df["ManagerComment"] = ""
            except EmptyDataError:
                df = pd.DataFrame(columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Reason", "Status", "ManagerComment"])
            new_id = df["LeaveID"].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame([[new_id, emp_id.strip(), leave_type, str(start), str(end), leave_reason.strip(), "Pending", ""]], columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Reason", "Status", "ManagerComment"])
            out = pd.concat([df, new_row], ignore_index=True)
            out.to_csv("leaves.csv", index=False)
            st.success("Leave request submitted successfully!")
    
    st.markdown("---")
    st.subheader("My Leave History")
    if emp_id and emp_id.strip():
        try:
            df = pd.read_csv("leaves.csv")
            # Add missing columns if old format
            if "Reason" not in df.columns:
                df["Reason"] = ""
            if "ManagerComment" not in df.columns:
                df["ManagerComment"] = ""
        except EmptyDataError:
            df = pd.DataFrame(columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Reason", "Status", "ManagerComment"])
        st.dataframe(df[df["EmployeeID"] == emp_id.strip()], use_container_width=True)
    else:
        st.info("Enter your Employee ID above to view leave history")

# MANAGER DASHBOARD
elif role == "Manager":
    st.header("Manager Dashboard")
    
    st.subheader("Approve Timesheets")
    try:
        df_ts = pd.read_csv("timesheets.csv")
        # Add missing columns if old format
        if "TaskDescription" not in df_ts.columns:
            df_ts["TaskDescription"] = ""
        if "ManagerComment" not in df_ts.columns:
            df_ts["ManagerComment"] = ""
    except EmptyDataError:
        df_ts = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
    
    pending_ts = df_ts[df_ts["ApprovalStatus"] == "Pending"]
    if pending_ts.empty:
        st.info("No pending timesheets")
    else:
        st.dataframe(pending_ts, use_container_width=True)
        for ix, row in pending_ts.iterrows():
            with st.expander(f"Timesheet ID: {row['TimesheetID']} - Employee: {row['EmployeeID']}"):
                st.write(f"**Task ID:** {row['TaskID']}")
                st.write(f"**Task Description:** {row.get('TaskDescription', 'N/A')}")
                st.write(f"**Hours Worked:** {row['HoursWorked']}")
                st.write(f"**Date:** {row['Date']}")
                
                action = st.radio(f"Decision *", ["Pending", "Approve", "Reject"], key=f"ts{row['TimesheetID']}")
                manager_comment = st.text_area(f"Reason for Decision *", placeholder="Enter reason for approval/rejection", key=f"comment_ts{row['TimesheetID']}", height=80)
                
                if st.button(f"Update", key=f"btn_ts{row['TimesheetID']}"):
                    if action == "Pending":
                        st.warning("Please select Approve or Reject")
                    elif not manager_comment or not manager_comment.strip():
                        st.error("Please provide a reason for your decision")
                    else:
                        df_ts.loc[ix, "ApprovalStatus"] = action
                        df_ts.loc[ix, "ManagerComment"] = manager_comment.strip()
                        df_ts.to_csv("timesheets.csv", index=False)
                        st.success(f"Timesheet updated to {action}!")
                        st.rerun()
    
    st.markdown("---")
    st.subheader("Approve Leave Applications")
    try:
        df_lv = pd.read_csv("leaves.csv")
        # Add missing columns if old format
        if "Reason" not in df_lv.columns:
            df_lv["Reason"] = ""
        if "ManagerComment" not in df_lv.columns:
            df_lv["ManagerComment"] = ""
    except EmptyDataError:
        df_lv = pd.DataFrame(columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Reason", "Status", "ManagerComment"])
    
    pending_lv = df_lv[df_lv["Status"] == "Pending"]
    if pending_lv.empty:
        st.info("No pending leave applications")
    else:
        st.dataframe(pending_lv, use_container_width=True)
        for ix, row in pending_lv.iterrows():
            with st.expander(f"Leave ID: {row['LeaveID']} - Employee: {row['EmployeeID']}"):
                st.write(f"**Leave Type:** {row['Type']}")
                st.write(f"**Start Date:** {row['StartDate']}")
                st.write(f"**End Date:** {row['EndDate']}")
                st.write(f"**Employee Reason:** {row.get('Reason', 'N/A')}")
                
                action = st.radio(f"Decision *", ["Pending", "Approve", "Reject"], key=f"lv{row['LeaveID']}")
                manager_comment = st.text_area(f"Reason for Decision *", placeholder="Enter reason for approval/rejection", key=f"comment_lv{row['LeaveID']}", height=80)
                
                if st.button(f"Update", key=f"btn_lv{row['LeaveID']}"):
                    if action == "Pending":
                        st.warning("Please select Approve or Reject")
                    elif not manager_comment or not manager_comment.strip():
                        st.error("Please provide a reason for your decision")
                    else:
                        df_lv.loc[ix, "Status"] = action
                        df_lv.loc[ix, "ManagerComment"] = manager_comment.strip()
                        df_lv.to_csv("leaves.csv", index=False)
                        st.success(f"Leave updated to {action}!")
                        st.rerun()
    
    st.markdown("---")
    st.subheader("Approved Timesheets")
    approved = df_ts[df_ts["ApprovalStatus"] == "Approve"]
    if approved.empty:
        st.info("No approved timesheets yet")
    else:
        st.dataframe(approved, use_container_width=True)

# ADMIN DASHBOARD
elif role == "Admin":
    st.header("Admin Dashboard")
    
    st.subheader("Manage Employees")
    try:
        df_emp = pd.read_csv("employees.csv")
    except EmptyDataError:
        df_emp = pd.DataFrame(columns=["EmployeeID", "Name", "Department", "Role"])
    
    if df_emp.empty:
        st.info("No employees. Add below.")
    else:
        st.dataframe(df_emp, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Add New Employee")
    with st.form("Add Employee"):
        new_id = df_emp["EmployeeID"].max() + 1 if not df_emp.empty else 1
        name = st.text_input("Name *", placeholder="Enter name")
        dept = st.text_input("Department *", placeholder="Enter department")
        role_sel = st.selectbox("Role *", ["Employee", "Manager", "Admin"])
        submitted = st.form_submit_button("Add Employee")
        
        if submitted:
            if not name or not name.strip():
                st.error("Please enter name")
            elif not dept or not dept.strip():
                st.error("Please enter department")
            else:
                new_row = pd.DataFrame([[new_id, name.strip(), dept.strip(), role_sel]], columns=df_emp.columns)
                out = pd.concat([df_emp, new_row], ignore_index=True)
                out.to_csv("employees.csv", index=False)
                st.success(f"Employee {name.strip()} added!")
                st.rerun()
    
    st.markdown("---")
    st.subheader("Global Timesheets")
    try:
        ts = pd.read_csv("timesheets.csv")
        # Add missing columns if old format
        if "TaskDescription" not in ts.columns:
            ts["TaskDescription"] = ""
        if "ManagerComment" not in ts.columns:
            ts["ManagerComment"] = ""
    except EmptyDataError:
        ts = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment"])
    
    if ts.empty:
        st.info("No timesheets submitted")
    else:
        st.dataframe(ts, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Global Leaves")
    try:
        lv = pd.read_csv("leaves.csv")
        # Add missing columns if old format
        if "Reason" not in lv.columns:
            lv["Reason"] = ""
        if "ManagerComment" not in lv.columns:
            lv["ManagerComment"] = ""
    except EmptyDataError:
        lv = pd.DataFrame(columns=["LeaveID", "EmployeeID", "Type", "StartDate", "EndDate", "Reason", "Status", "ManagerComment"])
    
    if lv.empty:
        st.info("No leave applications")
    else:
        st.dataframe(lv, use_container_width=True)
