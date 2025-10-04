# pairx-timesheet-management
# Timesheet Management System

A professional web-based timesheet and leave management application with role-based dashboards for employees, managers, and administrators.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Features

### Employee Dashboard
- Submit daily timesheets with task tracking
- View timesheet history and approval status
- Apply for sick, casual, or earned leave
- Track leave applications and status

### Manager Dashboard
- Review and approve/reject employee timesheets
- Manage team leave requests
- Access team performance reports
- Monitor pending approvals

### Admin Dashboard
- Add and manage employee records
- View organization-wide reports
- Access comprehensive timesheet data
- Monitor all leave applications across the organization

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Setup Instructions

1. Clone the repository

2. Install required dependencies

3. Add company logo
   - Place your logo file as `logo.jpg` in the project root directory
   - Recommended dimensions: 200x200 pixels

4. Run the application
5. 
5. Access the application
   - Open your browser and navigate to `http://localhost:8501`

## Usage

### Quick Start
1. Select your role from the sidebar (Employee, Manager, or Admin)
2. Follow the interface prompts for your specific dashboard
3. Submit timesheets, manage approvals, or configure settings based on your role

### Employee Workflow
1. Enter Employee ID in the designated field
2. Submit daily timesheets with task details and hours worked
3. Apply for leave by selecting leave type and dates
4. Monitor approval status in history sections

### Manager Workflow
1. Review pending timesheet submissions
2. Approve or reject employee timesheets
3. Process leave applications
4. Generate team reports and analytics

### Admin Workflow
1. Add new employees to the system
2. Monitor organization-wide activity
3. Generate comprehensive reports
4. Manage system-wide configurations

## Project Structure
timesheet-management/
├── app.py # Main application file
├── logo.jpg # Company logo (user-provided)
├── README.md # Project documentation
└── Data Files (auto-generated):
├── employees.csv # Employee records
├── timesheets.csv # Timesheet submissions
├── leaves.csv # Leave applications
├── projects.csv # Project information
└── tasks.csv # Task assignments

## Requirements

### System Requirements
- Operating System: Windows, macOS, or Linux
- Python 3.7+
- 512MB RAM minimum
- 100MB disk space

### Python Dependencies
streamlit>=1.28.0
pandas>=2.0.0
pillow>=10.0.0

## Configuration

### Theme Customization
The application uses a professional dark theme. To modify colors, edit the variables in `app.py`:
page_bg = "#0f1419" # Main background
header_bg = "#1a2332" # Header background
card_bg = "#1e2a3a" # Card background
subtitle_color = "#5FA8D3" # Subtitle color
feature_color = "#FF9800" # Feature highlight color

### Data Storage
- Application uses CSV files for data persistence
- Files are automatically created on first run
- Data is stored in the project root directory

## Deployment

### Local Development
streamlit run app.py --server.port 8501 --server.address localhost

### Production Deployment Options

**Streamlit Cloud**
1. Push code to GitHub repository
2. Connect repository to Streamlit Cloud
3. Deploy with automatic builds

**Heroku**
heroku create your-app-name
git push heroku main

**Docker**
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install streamlit pandas pillow
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

## Security

### Important Security Considerations

This application is designed for internal use and demonstration purposes. For production deployment, implement:

- User authentication and authorization
- Database integration (PostgreSQL, MySQL)
- SSL/TLS encryption
- Input validation and sanitization
- Audit logging
- Regular security updates
- Backup and recovery procedures
- Access control and role-based permissions

## Troubleshooting

### Common Issues

**Logo not displaying**
- Verify `logo.jpg` exists in the project root directory
- Check file permissions (read access required)
- Ensure image format is JPEG

**CSV file errors**
- Confirm write permissions in project directory
- Close any applications that may have CSV files open
- Restart the application if files become corrupted

**Styling issues**
- Clear browser cache and cookies
- Try hard refresh (Ctrl+F5 or Cmd+Shift+R)
- Restart the Streamlit server
- Check console for JavaScript errors

**Performance issues**
- Monitor CSV file sizes (consider database migration for large datasets)
- Restart application periodically
- Check available system memory

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make changes and test thoroughly
4. Commit changes (`git commit -m 'Add new feature'`)
5. Push to branch (`git push origin feature/new-feature`)
6. Create a Pull Request

### Code Standards
- Follow PEP 8 Python style guidelines
- Add comments for complex logic
- Test all functionality before submitting
- Update documentation as needed

---

**Version 1.0.0** | **Built with Streamlit** | **October 2025**






