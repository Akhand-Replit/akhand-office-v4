import streamlit as st
from sqlalchemy import text
from pages.common.components import display_profile_header, display_stats_card
from pages.company.branches import manage_branches
from pages.company.employees import manage_employees
from pages.company.tasks import manage_tasks
from pages.company.reports import manage_reports
from pages.company.messages import view_messages
from pages.company.profile import edit_profile
from utils.auth import logout

def company_dashboard(engine):
    """Display the enhanced company dashboard.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h1 class="main-header">Company Dashboard</h1>', unsafe_allow_html=True)
    
    # Display company profile
    display_profile_header(st.session_state.user)
    
    # Navigation - updated with new features
    selected = company_navigation()
    
    if selected == "Dashboard":
        display_company_dashboard_overview(engine)
    elif selected == "Branches":
        manage_branches(engine)
    elif selected == "Employees":
        manage_employees(engine)
    elif selected == "Tasks":
        manage_tasks(engine)
    elif selected == "Reports":
        manage_reports(engine)
    elif selected == "Messages":
        view_messages(engine)
    elif selected == "Profile":
        edit_profile(engine)
    elif selected == "Logout":
        logout()

def company_navigation():
    """Create and return the company navigation menu with enhanced options.
    
    Returns:
        str: Selected menu option
    """
    return st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Branches", "Employees", "Tasks", "Reports", "Messages", "Profile", "Logout"],
        index=0
    )

def display_company_dashboard_overview(engine):
    """Display the company dashboard overview with statistics and summaries.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Company Overview</h2>', unsafe_allow_html=True)
    
    company_id = st.session_state.user["id"]
    
    # Statistics
    with engine.connect() as conn:
        # Total branches
        result = conn.execute(text('''
        SELECT COUNT(*) FROM branches 
        WHERE company_id = :company_id AND is_active = TRUE
        '''), {'company_id': company_id})
        total_branches = result.fetchone()[0]
        
        # Main branches
        result = conn.execute(text('''
        SELECT COUNT(*) FROM branches 
        WHERE company_id = :company_id AND is_active = TRUE AND is_main_branch = TRUE
        '''), {'company_id': company_id})
        main_branches = result.fetchone()[0]
        
        # Sub-branches
        result = conn.execute(text('''
        SELECT COUNT(*) FROM branches 
        WHERE company_id = :company_id AND is_active = TRUE AND is_main_branch = FALSE
        '''), {'company_id': company_id})
        sub_branches = result.fetchone()[0]
        
        # Total employees
        result = conn.execute(text('''
        SELECT COUNT(*) FROM employees e
        JOIN branches b ON e.branch_id = b.id
        WHERE b.company_id = :company_id AND e.is_active = TRUE
        '''), {'company_id': company_id})
        total_employees = result.fetchone()[0]
        
        # Employees by role
        result = conn.execute(text('''
        SELECT r.role_name, COUNT(e.id) 
        FROM employees e
        JOIN branches b ON e.branch_id = b.id
        JOIN employee_roles r ON e.role_id = r.id
        WHERE b.company_id = :company_id AND e.is_active = TRUE
        GROUP BY r.role_name
        ORDER BY r.role_level
        '''), {'company_id': company_id})
        employees_by_role = result.fetchall()
        
        # Unread messages
        result = conn.execute(text('''
        SELECT COUNT(*) FROM messages 
        WHERE receiver_type = 'company' AND receiver_id = :company_id AND is_read = FALSE
        '''), {'company_id': company_id})
        unread_messages = result.fetchone()[0]
        
        # Active tasks
        result = conn.execute(text('''
        SELECT COUNT(*) FROM tasks 
        WHERE company_id = :company_id AND is_completed = FALSE
        '''), {'company_id': company_id})
        active_tasks = result.fetchone()[0]
        
        # Branch tasks completion status
        result = conn.execute(text('''
        SELECT 
            SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) as completed,
            COUNT(*) as total
        FROM tasks
        WHERE company_id = :company_id AND branch_id IS NOT NULL
        '''), {'company_id': company_id})
        task_stats = result.fetchone()
        branch_task_completion = 0
        if task_stats and task_stats[1] > 0:
            branch_task_completion = round((task_stats[0] / task_stats[1]) * 100)
        
        # Recent daily reports
        result = conn.execute(text('''
        SELECT e.full_name, dr.report_date, dr.report_text, b.branch_name 
        FROM daily_reports dr
        JOIN employees e ON dr.employee_id = e.id
        JOIN branches b ON e.branch_id = b.id
        WHERE b.company_id = :company_id
        ORDER BY dr.created_at DESC
        LIMIT 5
        '''), {'company_id': company_id})
        recent_reports = result.fetchall()
    
    # Display branch statistics
    st.subheader("Branch Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_stats_card(total_branches, "Total Branches")
    
    with col2:
        display_stats_card(main_branches, "Main Branches")
    
    with col3:
        display_stats_card(sub_branches, "Sub-Branches")
    
    # Display employee statistics
    st.subheader("Employee Statistics")
    
    # First row: Total employees and by role
    cols = st.columns(min(len(employees_by_role) + 1, 4))  # Limit to 4 columns max
    
    with cols[0]:
        display_stats_card(total_employees, "Total Employees")
    
    # Display employees by role (up to 3 roles in first row)
    for i, role_stat in enumerate(employees_by_role[:3]):
        if i + 1 < len(cols):
            with cols[i + 1]:
                display_stats_card(role_stat[1], f"{role_stat[0]}s")
    
    # If more than 3 roles, add another row
    if len(employees_by_role) > 3:
        remaining_cols = st.columns(min(len(employees_by_role) - 3, 4))
        for i, role_stat in enumerate(employees_by_role[3:]):
            if i < len(remaining_cols):
                with remaining_cols[i]:
                    display_stats_card(role_stat[1], f"{role_stat[0]}s")
    
    # Task and message stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_stats_card(active_tasks, "Active Tasks")
    
    with col2:
        display_stats_card(f"{branch_task_completion}%", "Branch Task Completion")
    
    with col3:
        display_stats_card(unread_messages, "Unread Messages")
    
    # Recent activities
    st.subheader("Recent Activities")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h4 class="sub-header">Recent Reports</h4>', unsafe_allow_html=True)
        if recent_reports:
            for report in recent_reports:
                employee_name = report[0]
                report_date = report[1].strftime('%d %b, %Y') if report[1] else "Unknown"
                report_text = report[2]
                branch_name = report[3]
                
                st.markdown(f'''
                <div class="report-item">
                    <strong>{employee_name}</strong> - {branch_name} - {report_date}
                    <p>{report_text[:100]}{'...' if len(report_text) > 100 else ''}</p>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.info("No recent reports available")
        
        if st.button("View All Reports", key="view_all_reports"):
            st.session_state.selected_tab = "Reports"
            st.rerun()
    
    with col2:
        st.markdown('<h4 class="sub-header">Quick Actions</h4>', unsafe_allow_html=True)
        
        # Quick action buttons
        if st.button("Add New Branch", key="quick_add_branch"):
            st.session_state.selected_tab = "Branches"
            st.rerun()
        
        if st.button("Add New Employee", key="quick_add_employee"):
            st.session_state.selected_tab = "Employees"
            st.rerun()
        
        if st.button("Assign New Task", key="quick_assign_task"):
            st.session_state.selected_tab = "Tasks"
            st.rerun()
        
        if st.button("Check Messages", key="quick_check_messages"):
            st.session_state.selected_tab = "Messages"
            st.rerun()
