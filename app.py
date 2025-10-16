import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import secrets
import string
import requests
import re
import random

st.set_page_config(page_title="Pairx Timesheet", layout="wide", initial_sidebar_state="collapsed")

ADMIN_EMAIL = "srinidhibv.cs23@bmsce.ac.in"
ALLOWED_DOMAINS = ["@persist-ai.com", "@pairx.com","@gmail.com"]
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
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False
if 'otp_sent' not in st.session_state:
    st.session_state.otp_sent = False
if 'generated_otp' not in st.session_state:
    st.session_state.generated_otp = None
if 'otp_email' not in st.session_state:
    st.session_state.otp_email = None
if 'otp_expiry' not in st.session_state:
    st.session_state.otp_expiry = None
if 'signup_data' not in st.session_state:
    st.session_state.signup_data = None

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

def generate_otp():
    """
    Generates a random 6-digit OTP
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_otp_email(email, otp, name):
    """
    Sends OTP to the user's email for verification
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import ssl
        
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        sender_name = st.secrets["email"]["sender_name"]
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Verify Your Email - Pairx Timesheet"
        message["From"] = f"{sender_name} <{sender_email}>"
        message["To"] = email
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
              <h2 style="color: #5FA8D3;">Email Verification - Pairx Timesheet</h2>
              <p>Hello <strong>{name}</strong>,</p>
              <p>Thank you for signing up! Please use the following One-Time Password (OTP) to verify your email address:</p>
              <div style="background: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">
                <h1 style="color: #5FA8D3; font-size: 36px; letter-spacing: 8px; margin: 0;">{otp}</h1>
              </div>
              <p><strong>Important:</strong> This OTP will expire in 10 minutes.</p>
              <p>If you didn't request this verification, please ignore this email.</p>
              <br>
              <p>Best regards,<br><strong>Pairx Team</strong></p>
            </div>
          </body>
        </html>
        """
        
        part = MIMEText(html, "html")
        message.attach(part)
        
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        
        return True, "OTP sent successfully"
    except Exception as e:
        return False, f"Failed to send OTP: {str(e)}"

def generate_next_employee_id():
    """
    Generates the next employee ID by finding the max ID and incrementing it
    """
    try:
        df_emp = pd.read_csv("employees.csv")
        if df_emp.empty:
            return "EMP001"
        
        # Extract numeric part from EmployeeID
        df_emp['ID_Numeric'] = df_emp['EmployeeID'].str.extract(r'(\d+)').astype(int)
        max_id = df_emp['ID_Numeric'].max()
        next_id = max_id + 1
        return f"EMP{next_id:03d}"
    except:
        return "EMP001"

def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def validate_password(password):
    """
    Validates password with requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

def create_firebase_user_signup(email, password):
    """
    Creates a new user in Firebase using REST API for signup
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"content-type": "application/json; charset=UTF-8"},
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "Account created successfully!"
        else:
            error_msg = response.json().get("error", {}).get("message", "Unknown error")
            return False, error_msg.replace("_", " ").lower()
    except Exception as e:
        return False, str(e)

def add_employee_to_database(emp_id, name, email, department, role, manager_id=""):
    """
    Adds employee to the employees.csv database
    """
    try:
        df_emp = pd.read_csv("employees.csv")
    except:
        df_emp = pd.DataFrame(columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
    
    new_row = pd.DataFrame([[emp_id, name, email, department, role, manager_id]], 
                          columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
    out = pd.concat([df_emp, new_row], ignore_index=True)
    out.to_csv("employees.csv", index=False)
    return True

def send_password_email(email, password, name):
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import ssl
        
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        sender_name = st.secrets["email"]["sender_name"]
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your Pairx Timesheet Account Password"
        message["From"] = f"{sender_name} <{sender_email}>"
        message["To"] = email
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
              <h2 style="color: #5FA8D3;">Welcome to Pairx Timesheet Management</h2>
              <p>Hello <strong>{name}</strong>,</p>
              <p>Your account has been created successfully. Below are your login credentials:</p>
              <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Email:</strong> {email}</p>
                <p style="margin: 5px 0;"><strong>Temporary Password:</strong> <code style="background: #e8e8e8; padding: 5px 10px; border-radius: 3px; font-size: 16px;">{password}</code></p>
              </div>
              <p><strong>Important:</strong> Please change your password after your first login for security purposes.</p>
              <br>
              <p>Best regards,<br><strong>Pairx Team</strong></p>
            </div>
          </body>
        </html>
        """
        
        part = MIMEText(html, "html")
        message.attach(part)
        
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        
        return True, "Password email sent successfully"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

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

def signup_page():
    """
    Renders the signup page with email verification via OTP
    """
    st.markdown("### Create Your Account")
    
    # OTP Verification Stage
    if st.session_state.otp_sent:
        st.info(f"An OTP has been sent to {st.session_state.otp_email}")
        
        # Check if OTP expired
        if datetime.now() > st.session_state.otp_expiry:
            st.error("OTP has expired. Please request a new one.")
            if st.button("Restart Signup"):
                st.session_state.otp_sent = False
                st.session_state.generated_otp = None
                st.session_state.otp_email = None
                st.session_state.otp_expiry = None
                st.session_state.signup_data = None
                st.rerun()
            return
        
        time_left = (st.session_state.otp_expiry - datetime.now()).seconds // 60
        st.warning(f"OTP expires in {time_left} minutes")
        
        otp_input = st.text_input("Enter 6-digit OTP", max_chars=6, placeholder="000000")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Verify OTP", use_container_width=True):
                if otp_input == st.session_state.generated_otp:
                    # OTP verified, create account
                    data = st.session_state.signup_data
                    
                    # Generate next employee ID
                    new_emp_id = generate_next_employee_id()
                    
                    # Create user in Firebase
                    success, message = create_firebase_user_signup(data['email'], data['password'])
                    
                    if success:
                        # Add employee to database
                        add_employee_to_database(new_emp_id, data['name'], data['email'], 
                                                data['department'], data['role'], data['manager_id'])
                        
                        st.success(f"✅ Email verified! Account created successfully!")
                        st.success(f"Your Employee ID is: {new_emp_id}")
                        st.balloons()
                        st.info("You can now sign in with your credentials.")
                        
                        # Reset session state
                        st.session_state.otp_sent = False
                        st.session_state.generated_otp = None
                        st.session_state.otp_email = None
                        st.session_state.otp_expiry = None
                        st.session_state.signup_data = None
                        st.session_state.show_signup = False
                    else:
                        st.error(f"Account creation failed: {message}")
                else:
                    st.error("❌ Invalid OTP. Please try again.")
        
        with col2:
            if st.button("Resend OTP", use_container_width=True):
                new_otp = generate_otp()
                success, msg = send_otp_email(st.session_state.otp_email, new_otp, 
                                             st.session_state.signup_data['name'])
                if success:
                    st.session_state.generated_otp = new_otp
                    st.session_state.otp_expiry = datetime.now() + timedelta(minutes=10)
                    st.success("New OTP sent!")
                    st.rerun()
                else:
                    st.error(f"Failed to resend OTP: {msg}")
        
        with col3:
            if st.button("Cancel", use_container_width=True):
                st.session_state.otp_sent = False
                st.session_state.generated_otp = None
                st.session_state.otp_email = None
                st.session_state.otp_expiry = None
                st.session_state.signup_data = None
                st.rerun()
        
        return
    
    # Initial Signup Form
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
    
    with st.form("signup_form"):
        st.markdown("#### Account Information")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *", placeholder="John Doe")
            email = st.text_input("Email Address *", placeholder="yourname@persist-ai.com")
        with col2:
            password = st.text_input("Create Password *", type="password", 
                                    help="At least 8 characters, one uppercase letter, and one special character")
            confirm_password = st.text_input("Confirm Password *", type="password")
        
        st.markdown("---")
        st.markdown("#### Employee Details")
        
        col3, col4 = st.columns(2)
        with col3:
            department = st.text_input("Department *", placeholder="Engineering")
            role = st.selectbox("Role *", ["Employee", "Manager"])
        with col4:
            if role == "Employee":
                selected_manager = st.selectbox("Assign Manager", manager_list)
            else:
                selected_manager = "None"
                st.info("Managers don't need to be assigned to another manager")
        
        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit_button = st.form_submit_button("Send Verification OTP", use_container_width=True)
        with col_btn2:
            if st.form_submit_button("Back to Login", use_container_width=True):
                st.session_state.show_signup = False
                st.rerun()
        
        if submit_button:
            errors = []
            
            if not name.strip():
                errors.append("⚠️ Full name is required")
            
            if not email.strip():
                errors.append("⚠️ Email is required")
            elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
                errors.append("⚠️ Invalid email format")
            elif email != ADMIN_EMAIL and not any(email.endswith(domain) for domain in ALLOWED_DOMAINS):
                errors.append(f"⚠️ Only {' or '.join(ALLOWED_DOMAINS)} domain is allowed")
            
            try:
                df_check = pd.read_csv("employees.csv")
                if email in df_check["Email"].values:
                    errors.append("⚠️ Email already registered")
            except:
                pass
            
            if not password.strip():
                errors.append("⚠️ Password is required")
            else:
                is_valid, msg = validate_password(password)
                if not is_valid:
                    errors.append(f"⚠️ {msg}")
            
            if password != confirm_password:
                errors.append("⚠️ Passwords do not match")
            
            if not department.strip():
                errors.append("⚠️ Department is required")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Generate and send OTP
                otp = generate_otp()
                success, msg = send_otp_email(email, otp, name)
                
                if success:
                    # Store signup data and OTP in session state
                    manager_id = "" if selected_manager == "None" else selected_manager.split(" - ")[0]
                    st.session_state.signup_data = {
                        'name': name,
                        'email': email,
                        'password': password,
                        'department': department,
                        'role': role,
                        'manager_id': manager_id
                    }
                    st.session_state.generated_otp = otp
                    st.session_state.otp_email = email
                    st.session_state.otp_expiry = datetime.now() + timedelta(minutes=10)
                    st.session_state.otp_sent = True
                    st.rerun()
                else:
                    st.error(f"Failed to send verification email: {msg}")

def firebase_login():
    if st.session_state.show_signup:
        signup_page()
        return
    
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
        
        st.markdown("---")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("Don't have an account?")
        with col4:
            if st.button("Sign Up", use_container_width=True):
                st.session_state.show_signup = True
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
    
    .stCheckbox label {{
        color: {body_text} !important;
    }}
    
    .stCheckbox label span {{
        color: {body_text} !important;
    }}
    
    label {{
        color: {label_text} !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 6px !important;
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
        padding: 10px 14px !important;
        font-size: 14px !important;
        line-height: 1.5 !important;
    }}
    
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
    
    h4 {{
        font-size: 15px !important;
        font-weight: 600 !important;
        color: {body_text} !important;
        margin: 12px 0 8px 0 !important;
    }}
    
    hr {{
        border: none !important;
        height: 1px !important;
        background: #2d4057 !important;
        margin: 24px 0 !important;
        opacity: 0.3 !important;
    }}
    
    .user-info {{
        background: {input_bg};
        padding: 8px 16px;
        border-radius: 20px;
        display: inline-block;
        font-size: 14px;
        font-weight: 600;
    }}
    
    .stDataFrame {{
        font-size: 14px !important;
    }}
    
    .streamlit-expanderHeader {{
        background: {input_bg} !important;
        border-radius: 8px !important;
        border: 1px solid #2d4057 !important;
        font-weight: 600 !important;
        color: {body_text} !important;
        padding: 12px !important;
        font-size: 14px !important;
    }}
    
    .stAlert {{
        border-radius: 8px !important;
        padding: 12px !important;
        font-size: 14px !important;
    }}
    
    .stForm {{
        border: 1px solid #2d4057;
        border-radius: 12px;
        padding: 20px;
        background: {input_bg}22;
    }}
    
    [data-testid="column"] {{
        padding: 0 8px !important;
    }}
    
    .element-container:has(> .stMarkdown:empty) {{
        display: none;
    }}
    
    @media (max-width: 768px) {{
        .block-container {{
            padding: 1rem 1.5rem !important;
        }}
        
        .user-info {{
            font-size: 13px !important;
        }}
        
        .stDataFrame {{
            overflow-x: auto !important;
        }}
        
        [data-testid="column"] {{
            min-width: 0 !important;
        }}
    }}
    
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
<div style="background: {header_bg}; padding: 12px 16px; margin: -1rem -1.5rem 24px -1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); width: 100vw; position: relative; left: 50%; right: 50%; margin-left: -50vw; margin-right: -50vw;">
    <div style="max-width: 1200px; margin: 0 auto; display: flex; align-items: center; gap: 12px; padding: 0 16px;">
        <img src="data:image/png;base64,{{}}" width="40" style="min-width: 40px; flex-shrink: 0;">
        <span style="color: #000000; font-size: 18px; font-weight: 700;">Pairx Timesheet</span>
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

cols = st.columns([4, 4, 1])
with cols[0]:
    st.markdown(f'<div class="user-info">{st.session_state.user_name} ({st.session_state.employee_id})</div>', unsafe_allow_html=True)

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

with cols[2]:
    if st.button("⚙️", key="settings_btn"):
        st.session_state.show_settings = True
        st.rerun()

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
        st.subheader("Create Firebase User & Employee")
        with st.form("create_user"):
            st.markdown("#### Account Information")
            col1, col2 = st.columns(2)
            with col1:
                new_email = st.text_input("Email *", placeholder="user@pairx.com")
                new_name = st.text_input("Full Name *", placeholder="John Doe")
            with col2:
                auto_password = generate_password()
                st.text_input("Auto-Generated Password", value=auto_password, disabled=True)
                send_email_option = st.checkbox("Send password to user's email", value=True)
            
            st.markdown("---")
            st.markdown("#### Employee Details")
            
            col3, col4 = st.columns(2)
            with col3:
                emp_dept = st.text_input("Department *", placeholder="Engineering")
                emp_role_input = st.selectbox("Role *", ["Employee", "Manager", "Admin"])
            with col4:
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
                    st.info("Managers and Admins don't need manager assignment")
            
            create = st.form_submit_button("Create User & Employee")
            
            if create:
                if not new_email or not new_name or not emp_dept:
                    st.error("All required fields must be filled")
                elif not any(new_email.endswith(domain) for domain in ALLOWED_DOMAINS) and new_email != ADMIN_EMAIL:
                    st.error(f"Email must end with {' or '.join(ALLOWED_DOMAINS)}")
                else:
                    try:
                        df_check = pd.read_csv("employees.csv")
                        if new_email in df_check["Email"].values:
                            st.error("Email already exists in employee database")
                        else:
                            proceed = True
                    except:
                        proceed = True
                    
                    if proceed:
                        try:
                            user = firebase_auth.create_user(email=new_email, password=auto_password, display_name=new_name)
                            
                            new_emp_id = generate_next_employee_id()
                            manager_id = "" if selected_manager == "None" else selected_manager.split(" - ")[0]
                            add_employee_to_database(new_emp_id, new_name, new_email, emp_dept, emp_role_input, manager_id)
                            
                            st.success(f"User created: {user.email} | Employee ID: {new_emp_id}")
                            
                            if send_email_option:
                                success, msg = send_password_email(new_email, auto_password, new_name)
                                if success:
                                    st.success("Password sent to user's email")
                                else:
                                    st.warning(f"User created but email failed: {msg}")
                                    st.info(f"Password: {auto_password}")
                            else:
                                st.info(f"Password: {auto_password}")
                            
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
    
    with tab2:
        st.subheader("Employee List")
        try:
            df_emp = pd.read_csv("employees.csv")
            st.dataframe(df_emp, use_container_width=True, height=300)
            csv = df_emp.to_csv(index=False)
            st.download_button("Download", csv, "employees.csv", "text/csv")
            
            st.markdown("---")
            st.markdown("### Update Employee Role")
            update_options = [f"{row['EmployeeID']} - {row['Name']} ({row['Email']}) - Current: {row['Role']}" for _, row in df_emp.iterrows()]
            to_update = st.selectbox("Select employee to update", ["Select..."] + update_options, key="update_selector")
            
            if to_update != "Select...":
                emp_id_to_update = to_update.split(" - ")[0]
                new_role = st.selectbox("New Role", ["Employee", "Manager", "Admin"], key="new_role_select")
                
                if st.button("Update Role"):
                    df_emp_fresh = pd.read_csv("employees.csv")
                    df_emp_fresh.loc[df_emp_fresh["EmployeeID"] == emp_id_to_update, "Role"] = new_role
                    df_emp_fresh.to_csv("employees.csv", index=False)
                    st.success(f"Updated {emp_id_to_update} to {new_role}")
                    st.rerun()
            
            st.markdown("---")
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
                elif not any(reset_email.endswith(domain) for domain in ALLOWED_DOMAINS) and reset_email != ADMIN_EMAIL:
                    st.error(f"Email must end with {' or '.join(ALLOWED_DOMAINS)}")
                else:
                    success, message = send_password_reset_email(reset_email)
                    if success:
                        st.success(message)
                    else:
                        st.error(f"Error: {message}")

