import streamlit as st
from sqlalchemy import text
import datetime
import time
from datetime import timedelta
from utils.role_permissions import RolePermissions

def employee_dashboard(engine):
    """Role-based employee dashboard.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.title("Employee Dashboard")
    
    # Get employee info with role
    employee_id = st.session_state.user["id"]
    
    with engine.connect() as conn:
        # Fetch employee details including role
        result = conn.execute(text('''
        SELECT e.id, e.full_name, e.username, e.profile_pic_url, 
               b.id as branch_id, b.branch_name, 
               r.id as role_id, r.role_name, r.role_level
        FROM employees e
        JOIN branches b ON e.branch_id = b.id
        JOIN employee_roles r ON e.role_id = r.id
        WHERE e.id = :employee_id
        '''), {'employee_id': employee_id})
        
        employee_details = result.fetchone()
    
    if not employee_details:
        st.error("Could not load employee details. Please log out and try again.")
        if st.button("Logout"):
            logout()
        return
    
    # Extract employee details
    employee_name = employee_details[1]
    branch_id = employee_details[4]
    branch_name = employee_details[5]
    role_name = employee_details[7]
    role_level = employee_details[8]
    
    # Store additional info in session state for use across the app
    st.session_state.user.update({
        "branch_id": branch_id,
        "branch_name": branch_name,
        "role_name": role_name,
        "role_level": role_level
    })
    
    # Display welcome message with role
    st.write(f"Welcome, {employee_name} ({role_name}) - {branch_name} Branch")
    
    # Role-specific navigation
    if role_level == RolePermissions.MANAGER or role_level == RolePermissions.ASST_MANAGER:
        # Manager and Asst. Manager navigation
        tabs = st.tabs(["Dashboard", "Employees", "Tasks", "Reports", "Profile"])
        
        with tabs[0]:
            display_role_dashboard(engine, branch_id, role_level)
        
        with tabs[1]:
            manage_branch_employees(engine, branch_id, role_level)
            
        with tabs[2]:
            manage_tasks(engine, branch_id, role_level)
            
        with tabs[3]:
            view_reports(engine, branch_id, role_level)
            
        with tabs[4]:
            edit_profile(engine, employee_id)
    else:
        # General Employee navigation
        tabs = st.tabs(["Dashboard", "Tasks", "My Reports", "Profile"])
        
        with tabs[0]:
            display_role_dashboard(engine, branch_id, role_level)
            
        with tabs[1]:
            view_employee_tasks(engine, employee_id)
            
        with tabs[2]:
            view_my_reports(engine, employee_id)
            
        with tabs[3]:
            edit_profile(engine, employee_id)
    
    # Logout option
    if st.sidebar.button("Logout"):
        logout()

def display_role_dashboard(engine, branch_id, role_level):
    """Display dashboard overview based on role.
    
    Args:
        engine: SQLAlchemy database engine
        branch_id: Branch ID
        role_level: Employee role level
    """
    st.subheader("Dashboard Overview")
    
    employee_id = st.session_state.user["id"]
    
    # Statistics row
    col1, col2, col3, col4 = st.columns(4)
    
    with engine.connect() as conn:
        # Task stats
        if role_level == RolePermissions.MANAGER:
            # Get all branch tasks
            result = conn.execute(text('''
            SELECT COUNT(*) FROM tasks 
            WHERE branch_id = :branch_id AND is_completed = FALSE
            '''), {'branch_id': branch_id})
            pending_tasks = result.fetchone()[0]
        elif role_level == RolePermissions.ASST_MANAGER:
            # Get tasks for general employees plus own tasks
            result = conn.execute(text('''
            SELECT COUNT(*) FROM tasks 
            WHERE (employee_id IN (
                SELECT id FROM employees WHERE branch_id = :branch_id AND role_id = (
                    SELECT id FROM employee_roles WHERE role_level = 3
                )
            ) OR employee_id = :employee_id) AND is_completed = FALSE
            '''), {'branch_id': branch_id, 'employee_id': employee_id})
            pending_tasks = result.fetchone()[0]
        else:
            # Get own tasks only
            result = conn.execute(text('''
            SELECT COUNT(*) FROM tasks 
            WHERE employee_id = :employee_id AND is_completed = FALSE
            '''), {'employee_id': employee_id})
            pending_tasks = result.fetchone()[0]
        
        # Personal report stats
        today = datetime.date.today()
        result = conn.execute(text('''
        SELECT COUNT(*) FROM daily_reports 
        WHERE employee_id = :employee_id AND report_date = :today
        '''), {'employee_id': employee_id, 'today': today})
        todays_report = result.fetchone()[0] > 0
        
        # Get employee counts for managers/asst. managers
        if role_level <= RolePermissions.ASST_MANAGER:
            if role_level == RolePermissions.MANAGER:
                result = conn.execute(text('''
                SELECT COUNT(*) FROM employees 
                WHERE branch_id = :branch_id AND is_active = TRUE
                '''), {'branch_id': branch_id})
            else:
                result = conn.execute(text('''
                SELECT COUNT(*) FROM employees e
                JOIN employee_roles r ON e.role_id = r.id
                WHERE e.branch_id = :branch_id AND e.is_active = TRUE 
                AND r.role_level = :general_level
                '''), {'branch_id': branch_id, 'general_level': RolePermissions.GENERAL_EMPLOYEE})
            
            employee_count = result.fetchone()[0]
        
        # Get recent activities
        if role_level == RolePermissions.MANAGER:
            # For managers - see all branch activity
            result = conn.execute(text('''
            SELECT e.full_name, r.role_name, dr.report_date, dr.report_text 
            FROM daily_reports dr
            JOIN employees e ON dr.employee_id = e.id
            JOIN employee_roles r ON e.role_id = r.id
            WHERE e.branch_id = :branch_id
            ORDER BY dr.created_at DESC
            LIMIT 3
            '''), {'branch_id': branch_id})
        elif role_level == RolePermissions.ASST_MANAGER:
            # For asst. managers - see own and general employees
            result = conn.execute(text('''
            SELECT e.full_name, r.role_name, dr.report_date, dr.report_text 
            FROM daily_reports dr
            JOIN employees e ON dr.employee_id = e.id
            JOIN employee_roles r ON e.role_id = r.id
            WHERE e.branch_id = :branch_id 
            AND (r.role_level = :general_level OR e.id = :employee_id)
            ORDER BY dr.created_at DESC
            LIMIT 3
            '''), {
                'branch_id': branch_id, 
                'general_level': RolePermissions.GENERAL_EMPLOYEE,
                'employee_id': employee_id
            })
        else:
            # For general employees - see only own
            result = conn.execute(text('''
            SELECT e.full_name, r.role_name, dr.report_date, dr.report_text 
            FROM daily_reports dr
            JOIN employees e ON dr.employee_id = e.id
            JOIN employee_roles r ON e.role_id = r.id
            WHERE e.id = :employee_id
            ORDER BY dr.created_at DESC
            LIMIT 3
            '''), {'employee_id': employee_id})
        
        recent_reports = result.fetchall()
    
    with col1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value">{pending_tasks}</div>
                <div class="stat-label">Pending Tasks</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        report_status = "Submitted" if todays_report else "Not Submitted"
        report_color = "#4CAF50" if todays_report else "#F44336"
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-value" style="color: {report_color};">{report_status}</div>
                <div class="stat-label">Today's Report</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    if role_level <= RolePermissions.ASST_MANAGER:
        with col3:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-value">{employee_count}</div>
                    <div class="stat-label">{'Branch Employees' if role_level == 1 else 'General Employees'}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Quick actions
    st.subheader("Quick Actions")
    
    # Submit report button
    if not todays_report:
        if st.button("Submit Today's Report"):
            st.session_state.submit_report = True
            st.rerun()
    
    # Report submission form if needed
    if hasattr(st.session_state, 'submit_report') and st.session_state.submit_report:
        with st.form("submit_daily_report"):
            st.subheader("Submit Daily Report")
            report_text = st.text_area("What did you work on today?", height=150)
            
            submitted = st.form_submit_button("Submit Report")
            if submitted:
                if not report_text:
                    st.error("Please enter your report")
                else:
                    with engine.connect() as conn:
                        today = datetime.date.today()
                        
                        # Check if report already exists
                        result = conn.execute(text('''
                        SELECT id FROM daily_reports 
                        WHERE employee_id = :employee_id AND report_date = :today
                        '''), {'employee_id': employee_id, 'today': today})
                        
                        existing = result.fetchone()
                        
                        if existing:
                            # Update existing report
                            conn.execute(text('''
                            UPDATE daily_reports 
                            SET report_text = :report_text, created_at = CURRENT_TIMESTAMP
                            WHERE id = :id
                            '''), {'report_text': report_text, 'id': existing[0]})
                        else:
                            # Create new report
                            conn.execute(text('''
                            INSERT INTO daily_reports (employee_id, report_date, report_text)
                            VALUES (:employee_id, :today, :report_text)
                            '''), {
                                'employee_id': employee_id,
                                'today': today,
                                'report_text': report_text
                            })
                        
                        conn.commit()
                    
                    st.success("Report submitted successfully")
                    del st.session_state.submit_report
                    st.rerun()
    
    # Recent activities
    st.subheader("Recent Reports")
    
    if recent_reports:
        for report in recent_reports:
            name = report[0]
            role = report[1]
            date = report[2].strftime('%d %b, %Y') if report[2] else "Unknown"
            text = report[3]
            
            st.markdown(f"""
            <div class="report-item">
                <div><strong>{name}</strong> ({role}) - {date}</div>
                <p>{text[:150]}{'...' if len(text) > 150 else ''}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent reports found")

def manage_branch_employees(engine, branch_id, role_level):
    """Manage employees in the branch based on role permissions.
    
    Args:
        engine: SQLAlchemy database engine
        branch_id: Branch ID
        role_level: Employee role level
    """
    st.subheader("Manage Branch Employees")
    
    # Different tabs based on role
    if role_level == RolePermissions.MANAGER:
        tabs = st.tabs(["All Employees", "Add Employee"])
    else:  # Asst. Manager
        tabs = st.tabs(["General Employees", "Add Employee"])
    
    with tabs[0]:
        # Fetch employees based on role permissions
        with engine.connect() as conn:
            if role_level == RolePermissions.MANAGER:
                # Managers can see all employees in their branch
                result = conn.execute(text('''
                SELECT e.id, e.username, e.full_name, e.profile_pic_url, e.is_active,
                       r.role_name, r.role_level
                FROM employees e
                JOIN employee_roles r ON e.role_id = r.id
                WHERE e.branch_id = :branch_id
                ORDER BY r.role_level, e.full_name
                '''), {'branch_id': branch_id})
            else:
                # Asst. Managers can only see General Employees
                result = conn.execute(text('''
                SELECT e.id, e.username, e.full_name, e.profile_pic_url, e.is_active,
                       r.role_name, r.role_level
                FROM employees e
                JOIN employee_roles r ON e.role_id = r.id
                WHERE e.branch_id = :branch_id AND r.role_level = :general_level
                ORDER BY e.full_name
                '''), {
                    'branch_id': branch_id,
                    'general_level': RolePermissions.GENERAL_EMPLOYEE
                })
            
            employees = result.fetchall()
        
        if not employees:
            st.info("No employees found")
        else:
            # Group by role if manager
            if role_level == RolePermissions.MANAGER:
                employees_by_role = {}
                for emp in employees:
                    role = emp[5]
                    if role not in employees_by_role:
                        employees_by_role[role] = []
                    employees_by_role[role].append(emp)
                
                # Display by role
                for role, role_employees in employees_by_role.items():
                    st.subheader(f"{role}s")
                    display_employee_list(engine, role_employees, role_level)
            else:
                # Just display the list for asst. manager
                display_employee_list(engine, employees, role_level)
    
    with tabs[1]:
        # Add employee form - both can add only General Employees
        with st.form("add_employee_form"):
            full_name = st.text_input("Full Name")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            profile_pic_url = st.text_input("Profile Picture URL (optional)")
            
            submitted = st.form_submit_button("Add Employee")
            if submitted:
                if not full_name or not username or not password:
                    st.error("Please fill all required fields")
                else:
                    with engine.connect() as conn:
                        # Check if username already exists
                        result = conn.execute(text('''
                        SELECT COUNT(*) FROM employees WHERE username = :username
                        '''), {'username': username})
                        
                        if result.fetchone()[0] > 0:
                            st.error(f"Username '{username}' already exists")
                        else:
                            try:
                                # Get the General Employee role ID
                                result = conn.execute(text('''
                                SELECT id FROM employee_roles 
                                WHERE role_level = :role_level AND company_id = (
                                    SELECT company_id FROM branches WHERE id = :branch_id
                                )
                                '''), {
                                    'role_level': RolePermissions.GENERAL_EMPLOYEE,
                                    'branch_id': branch_id
                                })
                                
                                role_id = result.fetchone()[0]
                                
                                # Add the employee
                                conn.execute(text('''
                                INSERT INTO employees (branch_id, role_id, username, password, full_name, profile_pic_url, is_active)
                                VALUES (:branch_id, :role_id, :username, :password, :full_name, :profile_pic_url, TRUE)
                                '''), {
                                    'branch_id': branch_id,
                                    'role_id': role_id,
                                    'username': username,
                                    'password': password,
                                    'full_name': full_name,
                                    'profile_pic_url': profile_pic_url if profile_pic_url else "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"
                                })
                                
                                conn.commit()
                                st.success(f"Successfully added {full_name} as General Employee")
                            except Exception as e:
                                st.error(f"Error adding employee: {e}")

def display_employee_list(engine, employees, viewer_role_level):
    """Display a list of employees with appropriate actions based on viewer role.
    
    Args:
        engine: SQLAlchemy database engine
        employees: List of employee data
        viewer_role_level: Role level of the person viewing the list
    """
    for employee in employees:
        employee_id = employee[0]
        username = employee[1]
        full_name = employee[2]
        profile_pic_url = employee[3] or "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"
        is_active = employee[4]
        role_name = employee[5]
        employee_role_level = employee[6]
        
        # Only show actions if viewer has permission to manage this role
        can_manage = RolePermissions.can_deactivate_role(viewer_role_level, employee_role_level)
        
        cols = st.columns([1, 3, 1] if can_manage else [1, 4])
        
        with cols[0]:
            st.image(profile_pic_url, width=60)
        
        with cols[1]:
            st.write(f"**{full_name}**")
            st.write(f"Username: {username}")
            st.write(f"Status: {'Active' if is_active else 'Inactive'}")
        
        if can_manage:
            with cols[2]:
                if is_active:
                    if st.button("Deactivate", key=f"deactivate_{employee_id}"):
                        with engine.connect() as conn:
                            conn.execute(text('''
                            UPDATE employees SET is_active = FALSE WHERE id = :id
                            '''), {'id': employee_id})
                            conn.commit()
                        st.success(f"Deactivated {full_name}")
                        st.rerun()
                else:
                    if st.button("Activate", key=f"activate_{employee_id}"):
                        with engine.connect() as conn:
                            conn.execute(text('''
                            UPDATE employees SET is_active = TRUE WHERE id = :id
                            '''), {'id': employee_id})
                            conn.commit()
                        st.success(f"Activated {full_name}")
                        st.rerun()
        
        st.markdown("---")

def manage_tasks(engine, branch_id, role_level):
    """Manage tasks based on role permissions.
    
    Args:
        engine: SQLAlchemy database engine
        branch_id: Branch ID
        role_level: Employee role level
    """
    st.subheader("Task Management")
    
    tabs = st.tabs(["Assign Task", "View Tasks"])
    
    with tabs[0]:
        # Task assignment form
        with st.form("assign_task_form"):
            st.subheader("Assign New Task")
            
            # Get assignable employees based on role
            with engine.connect() as conn:
                if role_level == RolePermissions.MANAGER:
                    # Managers can assign to all branch employees
                    result = conn.execute(text('''
                    SELECT e.id, e.full_name, r.role_name
                    FROM employees e
                    JOIN employee_roles r ON e.role_id = r.id
                    WHERE e.branch_id = :branch_id AND e.is_active = TRUE
                      AND e.id != :current_employee  -- Don't include self
                    ORDER BY r.role_level, e.full_name
                    '''), {
                        'branch_id': branch_id,
                        'current_employee': st.session_state.user["id"]
                    })
                else:
                    # Asst. Managers can only assign to General Employees
                    result = conn.execute(text('''
                    SELECT e.id, e.full_name, r.role_name
                    FROM employees e
                    JOIN employee_roles r ON e.role_id = r.id
                    WHERE e.branch_id = :branch_id AND e.is_active = TRUE
                      AND r.role_level = :general_level
                    ORDER BY e.full_name
                    '''), {
                        'branch_id': branch_id,
                        'general_level': RolePermissions.GENERAL_EMPLOYEE
                    })
                
                employees = result.fetchall()
            
            if not employees:
                st.warning("No eligible employees found to assign tasks")
                st.form_submit_button("Assign Task", disabled=True)
            else:
                # Create employee selection
                employee_options = {}
                for emp in employees:
                    employee_options[f"{emp[1]} ({emp[2]})"] = emp[0]
                
                selected_employee = st.selectbox("Assign to", list(employee_options.keys()))
                task_description = st.text_area("Task Description")
                due_date = st.date_input("Due Date", datetime.date.today() + timedelta(days=1))
                
                submitted = st.form_submit_button("Assign Task")
                
                if submitted:
                    if not task_description:
                        st.error("Please enter a task description")
                    else:
                        # Create task
                        try:
                            with engine.connect() as conn:
                                employee_id = employee_options[selected_employee]
                                
                                conn.execute(text('''
                                INSERT INTO tasks (
                                    branch_id, employee_id, task_description, due_date, is_completed
                                ) VALUES (
                                    :branch_id, :employee_id, :task_description, :due_date, FALSE
                                )
                                '''), {
                                    'branch_id': branch_id,
                                    'employee_id': employee_id,
                                    'task_description': task_description,
                                    'due_date': due_date
                                })
                                
                                conn.commit()
                            
                            st.success(f"Task assigned to {selected_employee.split(' (')[0]}")
                        except Exception as e:
                            st.error(f"Error assigning task: {e}")
    
    with tabs[1]:
        # View tasks based on role
        employee_id = st.session_state.user["id"]
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All Tasks", "Pending", "Completed"],
                key="task_status_filter"
            )
        
        # Fetch tasks based on role permissions
        with engine.connect() as conn:
            if role_level == RolePermissions.MANAGER:
                # Managers see all branch tasks
                query = '''
                SELECT t.id, e.full_name, r.role_name, t.task_description, 
                       t.due_date, t.is_completed, t.created_at
                FROM tasks t
                JOIN employees e ON t.employee_id = e.id
                JOIN employee_roles r ON e.role_id = r.id
                WHERE t.branch_id = :branch_id
                '''
                
                params = {'branch_id': branch_id}
                
            elif role_level == RolePermissions.ASST_MANAGER:
                # Asst. Managers see their tasks and General Employee tasks
                query = '''
                SELECT t.id, e.full_name, r.role_name, t.task_description, 
                       t.due_date, t.is_completed, t.created_at
                FROM tasks t
                JOIN employees e ON t.employee_id = e.id
                JOIN employee_roles r ON e.role_id = r.id
                WHERE (t.employee_id = :employee_id OR
                      (e.branch_id = :branch_id AND r.role_level = :general_level))
                '''
                
                params = {
                    'employee_id': employee_id,
                    'branch_id': branch_id,
                    'general_level': RolePermissions.GENERAL_EMPLOYEE
                }
            
            # Add status filter
            if status_filter == "Pending":
                query += ' AND t.is_completed = FALSE'
            elif status_filter == "Completed":
                query += ' AND t.is_completed = TRUE'
            
            # Sort by due date
            query += ' ORDER BY t.due_date ASC, t.created_at DESC'
            
            # Execute query
            result = conn.execute(text(query), params)
            tasks = result.fetchall()
        
        if not tasks:
            st.info("No tasks found")
        else:
            # Display tasks
            for task in tasks:
                task_id = task[0]
                assigned_to = task[1]
                role_name = task[2]
                description = task[3]
                due_date = task[4].strftime('%d %b, %Y') if task[4] else "No due date"
                is_completed = task[5]
                
                # Task card styling
                status_class = "completed" if is_completed else ""
                
                st.markdown(f'''
                <div class="task-item {status_class}">
                    <div style="display: flex; justify-content: space-between;">
                        <span><strong>Assigned to:</strong> {assigned_to} ({role_name})</span>
                        <span><strong>Due:</strong> {due_date}</span>
                    </div>
                    <p>{description}</p>
                    <div style="text-align: right; font-weight: 600; color: {'#9e9e9e' if is_completed else '#4CAF50'};">
                        {"Completed" if is_completed else "Pending"}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                # Actions based on status
                col1, col2 = st.columns(2)
                
                with col1:
                    if not is_completed:
                        if st.button(f"Mark as Completed", key=f"complete_task_{task_id}"):
                            with engine.connect() as conn:
                                conn.execute(text('''
                                UPDATE tasks SET is_completed = TRUE 
                                WHERE id = :id
                                '''), {'id': task_id})
                                conn.commit()
                            st.success("Task marked as completed")
                            st.rerun()
                
                with col2:
                    if is_completed:
                        if st.button(f"Reopen Task", key=f"reopen_task_{task_id}"):
                            with engine.connect() as conn:
                                conn.execute(text('''
                                UPDATE tasks SET is_completed = FALSE 
                                WHERE id = :id
                                '''), {'id': task_id})
                                conn.commit()
                            st.success("Task reopened")
                            st.rerun()

def view_reports(engine, branch_id, role_level):
    """View reports based on role permissions.
    
    Args:
        engine: SQLAlchemy database engine
        branch_id: Branch ID
        role_level: Employee role level
    """
    st.subheader("Reports")
    
    # Current employee ID
    employee_id = st.session_state.user["id"]
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        if role_level == RolePermissions.MANAGER:
            employee_filter_options = ["All Employees", "By Role", "Individual Employee"]
        else:  # Asst. Manager
            employee_filter_options = ["General Employees", "My Reports"]
        
        employee_filter = st.selectbox(
            "View",
            employee_filter_options
        )
    
    with col2:
        date_options = [
            "Today",
            "This Week",
            "This Month", 
            "Last Month",
            "Last 3 Months",
            "Custom Range"
        ]
        
        date_filter = st.selectbox("Date Range", date_options)
    
    # Date range calculation
    today = datetime.date.today()
    
    if date_filter == "Today":
        start_date = end_date = today
    elif date_filter == "This Week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif date_filter == "This Month":
        start_date = today.replace(day=1)
        end_date = today
    elif date_filter == "Last Month":
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1
        start_date = datetime.date(last_month_year, last_month, 1)
        # Calculate last day of last month
        if last_month == 12:
            end_date = datetime.date(last_month_year, last_month, 31)
        else:
            end_date = datetime.date(last_month_year, last_month + 1, 1) - timedelta(days=1)
    elif date_filter == "Last 3 Months":
        start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        start_date = (start_date - timedelta(days=1)).replace(day=1)
        end_date = today
    elif date_filter == "Custom Range":
        cols = st.columns(2)
        with cols[0]:
            start_date = st.date_input("Start Date", today - timedelta(days=30))
        with cols[1]:
            end_date = st.date_input("End Date", today)
    
    # Additional role-specific filters
    selected_role = None
    selected_employee = None
    
    if role_level == RolePermissions.MANAGER and employee_filter == "By Role":
        with engine.connect() as conn:
            result = conn.execute(text('''
            SELECT DISTINCT r.role_name
            FROM employee_roles r
            JOIN employees e ON e.role_id = r.id
            WHERE e.branch_id = :branch_id
            ORDER BY r.role_level
            '''), {'branch_id': branch_id})
            
            roles = [row[0] for row in result.fetchall()]
        
        selected_role = st.selectbox("Select Role", roles)
    
    elif ((role_level == RolePermissions.MANAGER and employee_filter == "Individual Employee") or
          (role_level == RolePermissions.ASST_MANAGER and employee_filter == "General Employees")):
        with engine.connect() as conn:
            if role_level == RolePermissions.MANAGER:
                # Managers can select any employee
                result = conn.execute(text('''
                SELECT e.id, e.full_name, r.role_name
                FROM employees e
                JOIN employee_roles r ON e.role_id = r.id
                WHERE e.branch_id = :branch_id
                ORDER BY r.role_level, e.full_name
                '''), {'branch_id': branch_id})
            else:
                # Asst. Managers can only select General Employees
                result = conn.execute(text('''
                SELECT e.id, e.full_name, r.role_name
                FROM employees e
                JOIN employee_roles r ON e.role_id = r.id
                WHERE e.branch_id = :branch_id AND r.role_level = :general_level
                ORDER BY e.full_name
                '''), {
                    'branch_id': branch_id,
                    'general_level': RolePermissions.GENERAL_EMPLOYEE
                })
            
            employees = result.fetchall()
            
            if not employees:
                st.warning("No employees found")
            else:
                # Create employee options
                employee_options = {f"{emp[1]} ({emp[2]})": emp[0] for emp in employees}
                selected_employee_name = st.selectbox("Select Employee", list(employee_options.keys()))
                selected_employee = employee_options[selected_employee_name]
    
    # Fetch reports based on filters
    with engine.connect() as conn:
        if role_level == RolePermissions.MANAGER:
            if employee_filter == "All Employees":
                # All branch employees
                result = conn.execute(text('''
                SELECT e.full_name, r.role_name, dr.report_date, dr.report_text
                FROM daily_reports dr
                JOIN employees e ON dr.employee_id = e.id
                JOIN employee_roles r ON e.role_id = r.id
                WHERE e.branch_id = :branch_id AND dr.report_date BETWEEN :start_date AND :end_date
                ORDER BY dr.report_date DESC, r.role_level, e.full_name
                '''), {
                    'branch_id': branch_id,
                    'start_date': start_date,
                    'end_date': end_date
                })
            elif employee_filter == "By Role" and selected_role:
                # By role
                result = conn.execute(text('''
                SELECT e.full_name, r.role_name, dr.report_date, dr.report_text
                FROM daily_reports dr
                JOIN employees e ON dr.employee_id = e.id
                JOIN employee_roles r ON e.role_id = r.id
                WHERE e.branch_id = :branch_id AND r.role_name = :role_name 
                  AND dr.report_date BETWEEN :start_date AND :end_date
                ORDER BY dr.report_date DESC, e.full_name
                '''), {
                    'branch_id': branch_id,
                    'role_name': selected_role,
                    'start_date': start_date,
                    'end_date': end_date
                })
            elif employee_filter == "Individual Employee" and selected_employee:
                # Individual employee
                result = conn.execute(text('''
                SELECT e.full_name, r.role_name, dr.report_date, dr.report_text
                FROM daily_reports dr
                JOIN employees e ON dr.employee_id = e.id
                JOIN employee_roles r ON e.role_id = r.id
                WHERE dr.employee_id = :employee_id AND dr.report_date BETWEEN :start_date AND :end_date
                ORDER BY dr.report_date DESC
                '''), {
                    'employee_id': selected_employee,
                    'start_date': start_date,
                    'end_date': end_date
                })
            else:
                result = None
        elif role_level == RolePermissions.ASST_MANAGER:
            if employee_filter == "General Employees" and selected_employee:
                # Individual General Employee
                result = conn.execute(text('''
                SELECT e.full_name, r.role_name, dr.report_date, dr.report_text
                FROM daily_reports dr
                JOIN employees e ON dr.employee_id = e.id
                JOIN employee_roles r ON e.role_id = r.id
                WHERE dr.employee_id = :employee_id AND dr.report_date BETWEEN :start_date AND :end_date
                ORDER BY dr.report_date DESC
                '''), {
                    'employee_id': selected_employee,
                    'start_date': start_date,
                    'end_date': end_date
                })
            elif employee_filter == "My Reports":
                # Own reports
                result = conn.execute(text('''
                SELECT e.full_name, r.role_name, dr.report_date, dr.report_text
                FROM daily_reports dr
                JOIN employees e ON dr.employee_id = e.id
                JOIN employee_roles r ON e.role_id = r.id
                WHERE dr.employee_id = :employee_id AND dr.report_date BETWEEN :start_date AND :end_date
                ORDER BY dr.report_date DESC
                '''), {
                    'employee_id': employee_id,
                    'start_date': start_date,
                    'end_date': end_date
                })
            else:
                # All General Employees (default)
                result = conn.execute(text('''
                SELECT e.full_name, r.role_name, dr.report_date, dr.report_text
                FROM daily_reports dr
                JOIN employees e ON dr.employee_id = e.id
                JOIN employee_roles r ON e.role_id = r.id
                WHERE e.branch_id = :branch_id AND r.role_level = :general_level
                  AND dr.report_date BETWEEN :start_date AND :end_date
                ORDER BY dr.report_date DESC, e.full_name
                '''), {
                    'branch_id': branch_id,
                    'general_level': RolePermissions.GENERAL_EMPLOYEE,
                    'start_date': start_date,
                    'end_date': end_date
                })
        
        reports = result.fetchall() if result else []
    
    if not reports:
        st.info("No reports found for the selected criteria")
    else:
        st.success(f"Found {len(reports)} reports")
        
        # Create PDF download button
        if st.button("Download as PDF"):
            # Create PDF (implementation would be in utils/pdf_generator.py)
            # For now, just show a placeholder message
            st.info("PDF download feature will be implemented")
        
        # Group reports by date
        reports_by_date = {}
        for report in reports:
            date_str = report[2].strftime('%Y-%m-%d')
            if date_str not in reports_by_date:
                reports_by_date[date_str] = []
            reports_by_date[date_str].append(report)
        
        # Display reports by date
        for date_str, date_reports in sorted(reports_by_date.items(), reverse=True):
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            with st.expander(f"{date_obj.strftime('%A, %d %b %Y')} ({len(date_reports)} reports)", expanded=False):
                for report in date_reports:
                    name = report[0]
                    role = report[1]
                    text = report[3]
                    
                    st.markdown(f"""
                    <div class="report-item">
                        <div><strong>{name}</strong> ({role})</div>
                        <p>{text}</p>
                    </div>
                    """, unsafe_allow_html=True)

def view_employee_tasks(engine, employee_id):
    """View and act on tasks assigned to the employee.
    
    Args:
        engine: SQLAlchemy database engine
        employee_id: Employee ID
    """
    st.subheader("My Tasks")
    
    # Filter options
    status_filter = st.selectbox(
        "Status",
        ["All Tasks", "Pending", "Completed"],
        key="my_task_status_filter"
    )
    
    # Fetch tasks
    with engine.connect() as conn:
        query = '''
        SELECT t.id, t.task_description, t.due_date, t.is_completed, t.created_at
        FROM tasks t
        WHERE t.employee_id = :employee_id
        '''
        
        params = {'employee_id': employee_id}
        
        # Add status filter
        if status_filter == "Pending":
            query += ' AND t.is_completed = FALSE'
        elif status_filter == "Completed":
            query += ' AND t.is_completed = TRUE'
        
        # Sort by due date
        query += ' ORDER BY t.due_date ASC, t.created_at DESC'
        
        # Execute query
        result = conn.execute(text(query), params)
        tasks = result.fetchall()
    
    if not tasks:
        st.info("No tasks found")
    else:
        # Display tasks
        for task in tasks:
            task_id = task[0]
            description = task[1]
            due_date = task[2].strftime('%d %b, %Y') if task[2] else "No due date"
            is_completed = task[3]
            
            # Task card styling
            status_class = "completed" if is_completed else ""
            
            st.markdown(f'''
            <div class="task-item {status_class}">
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>Due:</strong> {due_date}</span>
                    <span style="font-weight: 600; color: {'#9e9e9e' if is_completed else '#4CAF50'};">
                        {"Completed" if is_completed else "Pending"}
                    </span>
                </div>
                <p>{description}</p>
            </div>
            ''', unsafe_allow_html=True)
            
            # Actions based on status
            if not is_completed:
                if st.button(f"Mark as Completed", key=f"complete_my_task_{task_id}"):
                    with engine.connect() as conn:
                        conn.execute(text('''
                        UPDATE tasks SET is_completed = TRUE 
                        WHERE id = :id
                        '''), {'id': task_id})
                        conn.commit()
                    st.success("Task marked as completed")
                    st.rerun()

def view_my_reports(engine, employee_id):
    """View personal reports with filtering.
    
    Args:
        engine: SQLAlchemy database engine
        employee_id: Employee ID
    """
    st.subheader("My Reports")
    
    # Filter options
    date_options = [
        "All Reports",
        "This Month",
        "Last Month",
        "Custom Range"
    ]
    
    date_filter = st.selectbox("Date Range", date_options)
    
    # Date range calculation
    today = datetime.date.today()
    
    if date_filter == "This Month":
        start_date = today.replace(day=1)
        end_date = today
    elif date_filter == "Last Month":
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1
        start_date = datetime.date(last_month_year, last_month, 1)
        # Calculate last day of last month
        if last_month == 12:
            end_date = datetime.date(last_month_year, last_month, 31)
        else:
            end_date = datetime.date(last_month_year, last_month + 1, 1) - timedelta(days=1)
    elif date_filter == "Custom Range":
        cols = st.columns(2)
        with cols[0]:
            start_date = st.date_input("Start Date", today - timedelta(days=30))
        with cols[1]:
            end_date = st.date_input("End Date", today)
    else:  # All Reports
        start_date = datetime.date(2000, 1, 1)  # A date far in the past
        end_date = today
    
    # Fetch reports
    with engine.connect() as conn:
        result = conn.execute(text('''
        SELECT dr.id, dr.report_date, dr.report_text
        FROM daily_reports dr
        WHERE dr.employee_id = :employee_id AND dr.report_date BETWEEN :start_date AND :end_date
        ORDER BY dr.report_date DESC
        '''), {
            'employee_id': employee_id,
            'start_date': start_date,
            'end_date': end_date
        })
        
        reports = result.fetchall()
    
    if not reports:
        st.info("No reports found for the selected period")
    else:
        st.success(f"Found {len(reports)} reports")
        
        # Create PDF download button
        if st.button("Download as PDF"):
            # Create PDF (implementation would be in utils/pdf_generator.py)
            # For now, just show a placeholder message
            st.info("PDF download feature will be implemented")
        
        # Display reports
        for report in reports:
            report_id = report[0]
            report_date = report[1]
            report_text = report[2]
            
            st.markdown(f'''
            <div class="report-item">
                <div><strong>{report_date.strftime('%A, %d %b %Y')}</strong></div>
                <p>{report_text}</p>
            </div>
            ''', unsafe_allow_html=True)

def edit_profile(engine, employee_id):
    """Allow employee to edit their profile.
    
    Args:
        engine: SQLAlchemy database engine
        employee_id: Employee ID
    """
    st.subheader("My Profile")
    
    # Fetch current employee data
    with engine.connect() as conn:
        result = conn.execute(text('''
        SELECT e.username, e.full_name, e.profile_pic_url,
               b.branch_name, r.role_name
        FROM employees e
        JOIN branches b ON e.branch_id = b.id
        JOIN employee_roles r ON e.role_id = r.id
        WHERE e.id = :employee_id
        '''), {'employee_id': employee_id})
        
        employee_data = result.fetchone()
    
    if not employee_data:
        st.error("Could not retrieve your profile information. Please try again later.")
        return
    
    username, current_full_name, current_pic_url, branch_name, role_name = employee_data
    
    # Display current info
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("Current Picture:")
        try:
            st.image(current_pic_url, width=150)
        except:
            st.image("https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y", width=150)
    
    with col2:
        st.write(f"**Username:** {username} (cannot be changed)")
        st.write(f"**Branch:** {branch_name}")
        st.write(f"**Role:** {role_name}")
    
    # Form for updating profile
    with st.form("update_profile_form"):
        new_full_name = st.text_input("Full Name", value=current_full_name)
        new_profile_pic_url = st.text_input("Profile Picture URL", value=current_pic_url or "")
        
        # Password change
        st.subheader("Change Password")
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submitted = st.form_submit_button("Update Profile")
        
        if submitted:
            updates_made = False
            
            # Update profile info if changed
            if new_full_name != current_full_name or new_profile_pic_url != current_pic_url:
                with engine.connect() as conn:
                    conn.execute(text('''
                    UPDATE employees
                    SET full_name = :full_name, profile_pic_url = :profile_pic_url
                    WHERE id = :employee_id
                    '''), {
                        'full_name': new_full_name,
                        'profile_pic_url': new_profile_pic_url,
                        'employee_id': employee_id
                    })
                    conn.commit()
                
                # Update session state
                st.session_state.user["full_name"] = new_full_name
                
                updates_made = True
                st.success("Profile information updated successfully")
            
            # Update password if requested
            if current_password or new_password or confirm_password:
                if not current_password:
                    st.error("Please enter your current password to change it")
                elif not new_password:
                    st.error("Please enter a new password")
                elif new_password != confirm_password:
                    st.error("New passwords do not match")
                else:
                    # Verify current password
                    with engine.connect() as conn:
                        result = conn.execute(text('''
                        SELECT COUNT(*) FROM employees
                        WHERE id = :employee_id AND password = :current_password
                        '''), {
                            'employee_id': employee_id,
                            'current_password': current_password
                        })
                        
                        if result.fetchone()[0] == 0:
                            st.error("Current password is incorrect")
                        else:
                            # Update password
                            conn.execute(text('''
                            UPDATE employees
                            SET password = :new_password
                            WHERE id = :employee_id
                            '''), {
                                'new_password': new_password,
                                'employee_id': employee_id
                            })
                            conn.commit()
                            
                            updates_made = True
                            st.success("Password updated successfully")
            
            if updates_made:
                st.info("Refreshing in 3 seconds...")
                time.sleep(3)
                st.rerun()
