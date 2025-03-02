import streamlit as st
from sqlalchemy import text
from pages.common.components import (
    display_profile_header, display_stats_card, 
    display_report_item, display_task_item
)
from pages.admin.companies import manage_companies
from pages.admin.messaging import manage_messages
from pages.admin.employees import manage_employees
from pages.admin.reports import view_all_reports
from pages.admin.tasks import manage_tasks
from utils.auth import logout
from utils.helpers import calculate_completion_rate

def admin_dashboard(engine):
    """Display the admin dashboard.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h1 class="main-header">Admin Dashboard</h1>', unsafe_allow_html=True)
    
    # Display admin profile
    display_profile_header(st.session_state.user)
    
    # Navigation - Updated with Companies and Messages
    selected = admin_navigation()
    
    if selected == "Dashboard":
        display_admin_dashboard_overview(engine)
    elif selected == "Companies":
        manage_companies(engine)
    elif selected == "Messages":
        manage_messages(engine)
    elif selected == "Employees":
        manage_employees(engine)
    elif selected == "Reports":
        view_all_reports(engine)
    elif selected == "Tasks":
        manage_tasks(engine)
    elif selected == "Logout":
        logout()

def admin_navigation():
    """Create and return the admin navigation menu with new options.
    
    Returns:
        str: Selected menu option
    """
    return st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Companies", "Messages", "Employees", "Reports", "Tasks", "Logout"],
        index=0
    )

def display_admin_dashboard_overview(engine):
    """Display the admin dashboard overview with statistics and recent activities.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Overview</h2>', unsafe_allow_html=True)
    
    # Statistics
    with engine.connect() as conn:
        # Total companies
        result = conn.execute(text('SELECT COUNT(*) FROM companies WHERE is_active = TRUE'))
        total_companies = result.fetchone()[0]
        
        # Total branches
        result = conn.execute(text('SELECT COUNT(*) FROM branches WHERE is_active = TRUE'))
        total_branches = result.fetchone()[0]
        
        # Total employees
        result = conn.execute(text('SELECT COUNT(*) FROM employees WHERE is_active = TRUE'))
        total_employees = result.fetchone()[0]
        
        # Total reports
        result = conn.execute(text('SELECT COUNT(*) FROM daily_reports'))
        total_reports = result.fetchone()[0]
        
        # Total tasks
        result = conn.execute(text('SELECT COUNT(*) FROM tasks'))
        total_tasks = result.fetchone()[0]
        
        # Completed tasks
        result = conn.execute(text('SELECT COUNT(*) FROM tasks WHERE is_completed = TRUE'))
        completed_tasks = result.fetchone()[0]
        
        # Unread messages
        result = conn.execute(text('''
        SELECT COUNT(*) FROM messages 
        WHERE receiver_type = 'admin' AND is_read = FALSE
        '''))
        unread_messages = result.fetchone()[0]
        
        # Recent company additions
        result = conn.execute(text('''
        SELECT company_name, created_at 
        FROM companies 
        ORDER BY created_at DESC 
        LIMIT 5
        '''))
        recent_companies = result.fetchall()
        
        # Recent messages
        result = conn.execute(text('''
        SELECT m.message_text, m.created_at, 
               CASE WHEN m.sender_type = 'company' THEN c.company_name ELSE 'Admin' END as sender_name
        FROM messages m
        LEFT JOIN companies c ON m.sender_type = 'company' AND m.sender_id = c.id
        WHERE m.receiver_type = 'admin'
        ORDER BY m.created_at DESC 
        LIMIT 5
        '''))
        recent_messages = result.fetchall()
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        display_stats_card(total_companies, "Active Companies")
    
    with col2:
        display_stats_card(total_branches, "Active Branches")
    
    with col3:
        display_stats_card(total_employees, "Active Employees")
    
    with col4:
        display_stats_card(unread_messages, "Unread Messages")
    
    # Second row of stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        display_stats_card(total_reports, "Total Reports")
    
    with col2:
        display_stats_card(total_tasks, "Total Tasks")
    
    with col3:
        completion_rate = calculate_completion_rate(total_tasks, completed_tasks)
        display_stats_card(f"{completion_rate}%", "Task Completion")
    
    # Recent activities
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h3 class="sub-header">Recent Companies</h3>', unsafe_allow_html=True)
        if recent_companies:
            for company in recent_companies:
                company_name = company[0]
                created_at = company[1].strftime('%d %b, %Y') if company[1] else "Unknown"
                
                st.markdown(f'''
                <div class="card">
                    <strong>{company_name}</strong>
                    <p style="color: #777; font-size: 0.8rem;">Added on {created_at}</p>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.info("No companies added yet")
    
    with col2:
        st.markdown('<h3 class="sub-header">Recent Messages</h3>', unsafe_allow_html=True)
        if recent_messages:
            for message in recent_messages:
                message_text = message[0]
                created_at = message[1].strftime('%d %b, %Y') if message[1] else "Unknown"
                sender_name = message[2]
                
                st.markdown(f'''
                <div class="report-item">
                    <span style="font-weight: 600;">{sender_name}</span> - <span style="color: #777;">{created_at}</span>
                    <p>{message_text[:100]}{'...' if len(message_text) > 100 else ''}</p>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.info("No messages available")
