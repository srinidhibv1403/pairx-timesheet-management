import streamlit as st
import pandas as pd
from PIL import Image
import os
from pandas.errors import EmptyDataError

# Page config - changed initial_sidebar_state for mobile
st.set_page_config(
    page_title="Pairx Timesheet", 
    layout="wide", 
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Timesheet Management System v1.0"
    }
)

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

# === CUSTOM CSS WITH MOBILE IMPROVEMENTS ===
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
    
    /* Mobile: Make sidebar toggle more visible */
    @media (max-width: 768px) {{
        [data-testid="stSidebarNav"] {{
            background: {header_bg};
            padding-top: 2rem;
        }}
        
        /* Ensure sidebar button is visible */
        button[kind="header"] {{
            background-color: {button_bg} !important;
            color: white !important;
        }}
    }}
    
    /* Dashboard subtitle */
    .dashboard-title {{
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        color: {subtitle_color};
        margin: 1.5rem 0 1.2rem 0;
        padding: 1rem;
        background: {header_bg};
        border-radius: 10px;
        box-shadow: 0 2px 8px {shadow};
    }}
    
    /* Mobile responsive title */
    @media (max-width: 768px) {{
        .dashboard-title {{
            font-size: 1.5rem;
            padding: 0.8rem;
        }}
    }}
    
    /* Feature section headers */
    .feature-header {{
        font-size: 1.3rem;
        font-weight: 700;
        color: {feature_color};
        margin: 2rem 0 1rem 0;
        padding-left: 0.5rem;
        border-left: 4px solid {feature_color};
        letter-spacing: 0.02em;
    }}
    
    /* Mobile responsive feature header */
    @media (max-width: 768px) {{
        .feature-header {{
            font-size: 1.1rem;
            margin: 1.5rem 0 0.8rem 0;
        }}
    }}
    
    /* Card containers */
    .data-card {{
        background: {card_bg};
        padding
