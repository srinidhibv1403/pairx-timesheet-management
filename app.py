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
ALLOWED_DOMAINS = ["@persist-ai.com", "@pairx.com", "@gmail.com"]
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
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_otp_email(email, otp, name):
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
    try:
        df_emp = pd.read_csv("employees.csv")
        if df_emp.empty:
            return "EMP001"
        
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
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

def create_firebase_user_signup(email, password):
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
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
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
            return True, response.json()
        else:
            error_msg = response.json().get("error", {}).get("message", "")
            return False, error_msg
    except Exception as e:
        return False, str(e)

def signup_page():
    st.markdown("### Create Your Account")
    
    if st.session_state.otp_sent:
        st.info(f"An OTP has been sent to {st.session_state.otp_email}")
        
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
                    data = st.session_state.signup_data
                    new_emp_id = generate_next_employee_id()
                    success, message = create_firebase_user_signup(data['email'], data['password'])
                    
                    if success:
                        add_employee_to_database(new_emp_id, data['name'], data['email'], 
                                                data['department'], data['role'], data['manager_id'])
                        
                        st.success(f"✅ Email verified! Account created successfully!")
                        st.success(f"Your Employee ID is: {new_emp_id}")
                        st.balloons()
                        
                        role, emp_id, name = validate_user(data['email'])
                        if role:
                            st.session_state.authenticated = True
                            st.session_state.user_email = data['email']
                            st.session_state.user_role = role
                            st.session_state.employee_id = emp_id
                            st.session_state.user_name = name
                            st.session_state.view_as = role
                        
                        st.session_state.otp_sent = False
                        st.session_state.generated_otp = None
                        st.session_state.otp_email = None
                        st.session_state.otp_expiry = None
                        st.session_state.signup_data = None
                        st.session_state.show_signup = False
                        
                        st.info("Redirecting to dashboard...")
                        st.rerun()
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
    
    try:
        df_emp = pd.read_csv("employees.csv")
        if "ManagerID" not in df_emp.columns:
            df_emp["ManagerID"] = ""
    except:
        df_emp = pd.DataFrame(columns=["EmployeeID", "Name", "Email", "Department", "Role", "ManagerID"])
    
    manager_list = ["None"]
    if not df_emp.empty:
        managers = df_emp[df_emp["Role"].isin(["Manager", "Admin"])][["EmployeeID", "Name"]].values
        for m in managers:
            manager_list.append(f"{m[0]} - {m[1]}")
    
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
        
        department = st.text_input("Department *", placeholder="Engineering")
        
        st.markdown("**Select Role:**")
        role = st.radio("Role", ["Employee", "Manager"], horizontal=True, label_visibility="collapsed")
        
        selected_manager = "None"
        if role == "Employee":
            st.markdown("**Assign Manager:**")
            selected_manager = st.selectbox("Manager", manager_list, label_visibility="collapsed", index=0, key="manager_select")
            # Display selected manager explicitly
            if selected_manager != "None":
                st.markdown(f"**Selected:** {selected_manager}")
             if selected_manager == "None":
                st.markdown(f"**Selected:None**")
        
        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit_button = st.form_submit_button("Send Verification OTP", use_container_width=True)
        with col_btn2:
            back_button = st.form_submit_button("Back to Login", use_container_width=True)
        
        if back_button:
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
            
            if role == "Employee" and selected_manager == "None":
                errors.append("⚠️ Please select a manager for employee role")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                otp = generate_otp()
                success, msg = send_otp_email(email, otp, name)
                
                if success:
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
                    success, result = verify_firebase_password(email, password)
                    
                    if not success:
                        if "INVALID_PASSWORD" in str(result) or "INVALID_LOGIN_CREDENTIALS" in str(result):
                            st.error("❌ Invalid email or password")
                        elif "EMAIL_NOT_FOUND" in str(result):
                            st.error("❌ Email not found")
                        elif "USER_DISABLED" in str(result):
                            st.error("❌ User account has been disabled")
                        else:
                            st.error(f"❌ Authentication failed: {result}")
                    else:
                        if email != ADMIN_EMAIL:
                            if not any(email.endswith(domain) for domain in ALLOWED_DOMAINS):
                                st.error(f"Access denied. Only {', '.join(ALLOWED_DOMAINS)} domains are allowed")
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
                                    st.success("✅ Login successful!")
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
                                st.success("✅ Login successful!")
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
        color: {input_text} !important;
    }}
    
    /* Fix for selectbox selected value display */
    [data-baseweb="select"] [data-baseweb="input"] {{
        color: {input_text} !important;
    }}
    
    [data-baseweb="select"] [role="button"] {{
        color: {input_text} !important;
    }}
    
    [data-baseweb="select"] > div > div > div {{
        color: {input_text} !important;
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
    
    /* Additional fix for selectbox text visibility */
    .stSelectbox > div > div > div {{
        color: {input_text} !important;
    }}
    
    .stSelectbox [data-baseweb="select"] span {{
        color: {input_text} !important;
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

# Continue with dashboard code (Employee, Manager, Admin sections)...
# [REST OF THE CODE REMAINS THE SAME - EMPLOYEE, MANAGER, ADMIN DASHBOARDS]

