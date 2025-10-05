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
                if "TaskDescription" not in df.columns:
                    df["TaskDescription"] = ""
                if "ManagerComment" not in df.columns:
                    df["ManagerComment"] = ""
            except EmptyDataError:
                df = pd.DataFrame(columns=["TimesheetID", "EmployeeID", "Date", "TaskID", "TaskDescription", "HoursWorked", "ApprovalStatus", "ManagerComment
