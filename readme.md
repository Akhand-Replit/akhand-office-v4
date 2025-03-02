# Employee Management System

A comprehensive employee management system built with Streamlit and PostgreSQL.

## Project Structure

```
employee-management-system/
├── app.py                   # Main application entry point
├── config/                  # Configuration settings
│   └── settings.py          
├── database/                # Database related code
│   ├── connection.py        # Database connection and initialization
│   ├── models.py            # Import aggregator for models
│   └── models/              # Database models
│       ├── branch_model.py
│       ├── company_model.py
│       ├── employee_model.py
│       ├── message_model.py
│       ├── report_model.py
│       ├── role_model.py
│       └── task_model.py
├── pages/                   # Application pages
│   ├── admin/               # Admin pages
│   │   ├── companies.py
│   │   ├── dashboard.py
│   │   ├── employees.py
│   │   ├── messaging.py
│   │   ├── reports.py
│   │   └── tasks.py
│   ├── common/              # Shared components
│   │   └── components.py
│   ├── company/             # Company pages
│   │   ├── branches.py
│   │   ├── dashboard.py
│   │   ├── employees.py
│   │   ├── messages.py
│   │   ├── profile.py
│   │   ├── reports.py
│   │   └── tasks.py
│   ├── employee/            # Employee pages
│   │   ├── dashboard.py
│   │   ├── profile.py
│   │   ├── reports.py
│   │   └── tasks.py
│   └── login/               # Login page
│       └── login_page.py
├── styles/                  # CSS styles
│   └── custom_css.py
└── utils/                   # Utility functions
    ├── auth.py
    ├── helpers.py
    ├── pdf_generator.py
    └── role_permissions.py
```

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.streamlit/secrets.toml` file with the following:
   ```toml
   [postgres]
   url = "postgresql://username:password@localhost:5432/database_name"
   
   admin_username = "admin"
   admin_password = "your_secure_password"
   ```

4. Run the application:
   ```
   streamlit run app.py
   ```

## Features

- **Multi-user system** with different roles (Admin, Company, Employee)
- **Role-based dashboards** with appropriate permissions
- **Company management** with branches and hierarchy
- **Employee management** with role assignment
- **Task assignment and tracking**
- **Daily reporting system**
- **Messaging between admin and companies**
- **Profile management**
- **PDF report generation**

## Access Levels

- **Admin**: Full system access, manages companies
- **Company**: Manages their branches, employees, tasks and reports
- **Employee**: Based on role level (Manager, Asst. Manager, General Employee)
  - Managers: Manage branch employees and tasks
  - Asst. Managers: Manage general employees and tasks
  - General Employees: Submit reports and manage assigned tasks

## Database Structure

The system uses PostgreSQL with the following tables:
- Companies
- Branches (with parent-child relationships)
- Employee Roles
- Employees
- Tasks
- Task Assignments
- Daily Reports
- Messages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
