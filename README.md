# Pairx Timesheet Management System

A modern, full-featured web-based timesheet and leave management application built with Streamlit, Firebase Authentication, and automated email notifications. Features role-based dashboards for employees, managers, and administrators with a beautiful dark/light theme toggle.

**Live Demo:** [https://pairx-timesheet-management.streamlit.app/](https://pairx-timesheet-management.streamlit.app/)

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Security](#security)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

### Authentication System
- Firebase Authentication integration
- Secure login with email and password
- Password reset via email
- Domain-restricted access (@persist-ai.com, @pairx.com)
- Automatic session management

### Employee Dashboard
- Submit daily timesheets with task ID and descriptions
- Real-time hours tracking with validation
- View complete timesheet history with approval status
- Apply for sick, casual, or earned leave
- Track leave applications with status updates
- Download personal timesheet and leave records (CSV)
- Rejected leaves excluded from total count

### Manager Dashboard
- Review and approve/reject employee timesheets
- Add comments and feedback on submissions
- Manage team leave requests with detailed reasoning
- View pending approvals in organized tables
- Filter and search through team submissions
- Track managed employees count
- Role-based view switching (Manager/Employee)

### Admin Dashboard
- **User Management:** Create Firebase users with auto-generated passwords
- **Employee Database:** Add, view, edit, and delete employee records
- **Manager Assignment:** Assign managers to employees
- **Email Notifications:** Automated password emails to new users
- **Password Reset:** Send password reset links to users
- **System Reports:** Export all employee data
- **Role-Based Views:** Switch between Admin/Manager/Employee views

### UI/UX Features
- Modern dark mode with light mode toggle
- Mobile-responsive design
- Clean, professional Inter font family
- Smooth animations and transitions
- Compact, space-efficient layout
- Full-width header with centered 1200px content
- Settings page for theme customization
- No weird lines or visual glitches
- Intuitive navigation and workflows

## Tech Stack

**Frontend:**
- Streamlit 1.28.0+
- Custom CSS with responsive design
- Inter font family from Google Fonts

**Backend:**
- Python 3.7+
- Pandas for data management
- Firebase Admin SDK for authentication
- SMTP for email notifications (Gmail/SendGrid)

**Data Storage:**
- CSV files (employees, timesheets, leaves, projects, tasks)
- Firebase for user authentication

**Deployment:**
- Streamlit Cloud
- Compatible with Heroku, Docker, AWS

## Installation

### Prerequisites
- Python 3.7 or higher
- Firebase project with Authentication enabled
- Gmail account with App Password OR SendGrid account
- Git (for cloning repository)

### Quick Setup

1. **Clone the repository**
   git clone https://github.com/yourusername/pairx-timesheet-management.git
   cd pairx-timesheet-management

2. **Install dependencies**
   pip install -r requirements.txt

3. **Add company logo**
   Place your logo as `logo.jpg` in the project root (recommended: 200x200px)

4. **Configure Firebase**
- Create a Firebase project at https://console.firebase.google.com/
- Enable Email/Password authentication
- Download service account key as `serviceAccountKey.json`
- Place it in the project root

5. **Set up Streamlit secrets**
   Create `.streamlit/secrets.toml`:
   firebase_web_api_key = "your-firebase-web-api-key"

   [email]
   smtp_server = "smtp.gmail.com"
   smtp_port = 587
   sender_email = "your-email@gmail.com"
   sender_password = "your-gmail-app-password"
   sender_name = "Pairx Timesheet"
   
   [firebase]
   type = "service_account"
   project_id = "your-project-id"
   private_key_id = "xxxxx"
   private_key = "-----BEGIN PRIVATE KEY-----\nxxxxx\n-----END PRIVATE KEY-----\n"
   client_email = "firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com"
   client_id = "xxxxx"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-    xxxxx%40your-project.iam.gserviceaccount.com"

6. **Run the application**
   streamlit run app.py

7. **Access at** `http://localhost:8501`

## Configuration

### Email Setup (Gmail)

1. Enable 2-Step Verification in your Google Account
2. Go to https://myaccount.google.com/security
3. Scroll to "App passwords"
4. Generate an app password for "Mail"
5. Copy the 16-character password (no spaces)
6. Add to `.streamlit/secrets.toml` under `[email]` section

### Email Setup (SendGrid - Production)

1. Sign up at https://sendgrid.com/ (100 emails/day free)
2. Verify your sender email
3. Create an API key
4. Update secrets:
   [email]
   sendgrid_api_key = "your-api-key"
   sender_email = "verified@yourdomain.com"
   sender_name = "Pairx Timesheet"

### Theme Customization

Edit these variables in `app.py` (lines 240-252):
if st.session_state.dark_mode:
page_bg = "#0f1419" # Main background
body_text = "#E8EDF2" # Text color
input_bg = "#273647" # Input fields
button_bg = "#5FA8D3" # Buttons
else:
page_bg = "#FFFFFF" # Light mode background
body_text = "#1a1a1a" # Light mode text
input_bg = "#F5F5F5" # Light mode inputs
button_bg = "#3b82f6" # Light mode buttons


### Admin Email Configuration

Change the admin email in `app.py` (line 14):
   ADMIN_EMAIL = "your-admin@bmsce.ac.in"

### Allowed Email Domains

Update allowed domains in `app.py` (line 15):ALLOWED_DOMAINS = ["@persist-ai.com", "@pairx.com", "@yourdomain.com"

## Usage

### First Time Setup

1. **Admin Login:** Use your configured admin email
2. **Create Users:** Go to Admin Dashboard > User Management
3. **Add Employees:** Go to Employee Database tab
4. **Assign Managers:** Select manager when adding employees

### Employee Workflow

1. Sign in with your email and password
2. Navigate to Timesheets tab
3. Submit daily timesheets with task details
4. Go to Leaves tab to apply for leave
5. Monitor approval status in history sections
6. Download your records as CSV

### Manager Workflow

1. Sign in and view Manager Dashboard
2. Review pending timesheet submissions
3. Approve/reject with comments
4. Process leave applications
5. Switch to Employee view to submit your own timesheets

### Admin Workflow

1. Access all three dashboards (Admin/Manager/Employee)
2. Create new Firebase users with auto-generated passwords
3. Add employees to database with manager assignments
4. Send password reset links via System tab
5. Export employee data as CSV
6. Monitor organization-wide activity

## Project Structure
   pairx-timesheet-management/
├── app.py # Main application
├── logo.jpg # Company logo
├── serviceAccountKey.json # Firebase credentials (gitignored)
├── requirements.txt # Python dependencies
├── .streamlit/
│ └── secrets.toml # Configuration secrets (gitignored)
├── .gitignore # Git ignore file
├── README.md # Documentation
└── Data Files (auto-generated):
├── employees.csv # Employee records
├── timesheets.csv # Timesheet submissions
├── leaves.csv # Leave applications
├── projects.csv # Project information
└── tasks.csv # Task assignments

## Deployment

### Streamlit Cloud (Recommended)

1. Push code to GitHub repository
2. Go to https://share.streamlit.io/
3. Connect your repository
4. Add secrets in Streamlit Cloud dashboard
5. Deploy with automatic HTTPS

### Docker Deployment
   FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
Build and run:
docker build -t pairx-timesheet .
docker run -p 8501:8501 pairx-timesheet

### Heroku Deployment

1. Create `Procfile`:
   web: sh setup.sh && streamlit run app.py

2. Create `setup.sh`:
   mkdir -p ~/.streamlit/
   echo "[server]
   headless = true
   port = $PORT
   enableCORS = false
   " > ~/.streamlit/config.toml

3. Deploy:
   heroku create your-app-name
   git push heroku main

## Security

### Production Security Checklist

- [ ] Change default admin email
- [ ] Use strong Firebase security rules
- [ ] Enable 2FA for admin accounts
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting on login attempts
- [ ] Regular security audits
- [ ] Keep dependencies updated
- [ ] Use HTTPS in production
- [ ] Implement data backup strategy
- [ ] Add audit logging for sensitive operations
- [ ] Restrict IP access if needed
- [ ] Use SendGrid for production emails (more reliable than Gmail)

### Data Protection

- All passwords are hashed by Firebase
- CSV files should be backed up regularly
- Secrets are gitignored
- Email passwords use App Passwords, not main passwords
- Session management handled by Streamlit

## API Documentation

### Firebase Authentication Endpoints

**Password Reset:**
   POST https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode
   Headers: None
   Body: {"requestType": "PASSWORD_RESET", "email": "user@domain.com"}

### Email Function
   send_password_email(email, password, name)

   Returns: (success: bool, message: str)
   Sends HTML email with credentials to new user

## Troubleshooting

### Firebase API Key Error
**Error:** "API key not valid"
**Solution:** 
1. Get Web API key from Firebase Console > Project Settings
2. Add to secrets.toml as `firebase_web_api_key = "AIzaSy..."`
3. Ensure it's at TOP LEVEL, not inside [firebase] section

### Email Not Sending
**Gmail Error:** "Authentication failed"
**Solution:**
1. Enable 2-Step Verification
2. Generate App Password (not regular password)
3. Remove spaces from app password in secrets.toml

**SendGrid Error:** "Unauthorized"
**Solution:**
1. Verify sender email in SendGrid dashboard
2. Check API key is correct
3. Ensure you haven't exceeded free tier limits

### Logo Not Displaying
**Solution:**
- Verify `logo.jpg` exists in project root
- Check file is JPEG format
- Ensure readable permissions
- Try renaming to exactly `logo.jpg` (lowercase)

### CSV Permission Errors
**Solution:**
- Close Excel/apps that may lock CSV files
- Check write permissions in directory
- Restart Streamlit server
- Delete corrupted CSV and let app recreate

### Mobile Layout Issues
**Solution:**
- Clear browser cache
- Force refresh (Ctrl+F5)
- Check viewport meta tags
- Responsive CSS is built-in (tested 480px+)

### Performance Issues
**Solution:**
- CSV files over 10MB should migrate to database
- Restart app periodically
- Use st.cache for heavy computations
- Monitor Streamlit Cloud resource usage

## Contributing

### Development Setup

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test thoroughly
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open Pull Request

### Code Standards

- Follow PEP 8 style guidelines
- Add docstrings to functions
- Comment complex logic
- Test on both desktop and mobile
- Update README for new features
- No emojis in documentation

### Testing Checklist

- [ ] Login/logout works correctly
- [ ] All three dashboards functional
- [ ] Email notifications send properly
- [ ] CSV downloads work
- [ ] Mobile responsive
- [ ] Dark/light theme toggle works
- [ ] Role-based access control enforced
- [ ] No console errors

## Requirements

### System Requirements
- Operating System: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- Python 3.7 - 3.11 (3.13 has compatibility issues)
- 1GB RAM minimum (2GB recommended)
- 500MB disk space
- Internet connection for Firebase and email

### Python Dependencies
   streamlit>=1.28.0
   pandas>=2.0.0
   pillow>=10.0.0
   firebase-admin>=6.0.0
   requests>=2.31.0

Install all: `pip install -r requirements.txt`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Version 2.0.0** | **Built with Streamlit & Firebase** | **October 2025**

For support, email: support@pairx.com





















