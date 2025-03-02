import streamlit as st
from streamlit_option_menu import option_menu

def display_profile_header(user):
    """Display user profile header with image and name.
    
    Args:
        user: User dict with profile information
    """
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown('<div class="profile-container">', unsafe_allow_html=True)
        try:
            st.image(user["profile_pic_url"], width=80, clamp=True, output_format="auto", 
                    channels="RGB", use_container_width=False)
        except:
            st.image("https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y", 
                    width=80, use_container_width=False)
        
        user_type = "Administrator" if user.get("is_admin", False) else "Employee"
        st.markdown(f'''
        <div>
            <h3>{user["full_name"]}</h3>
            <p>{user_type}</p>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def display_stats_card(value, label):
    """Display a statistics card with value and label.
    
    Args:
        value: The statistic value to display
        label: The label for the statistic
    """
    st.markdown('<div class="stat-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-value">{value}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-label">{label}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def display_report_item(date_str, text, author=None):
    """Display a report item with consistent styling.
    
    Args:
        date_str: Formatted date string
        text: Report text content
        author: (Optional) Author name for admin view
    """
    header = f"<strong>{author}</strong> - {date_str}" if author else f"<strong>{date_str}</strong>"
    
    st.markdown(f'''
    <div class="report-item">
        {header}
        <p>{text[:100]}{'...' if len(text) > 100 else ''}</p>
    </div>
    ''', unsafe_allow_html=True)

def display_task_item(description, due_date, is_completed=False, author=None):
    """Display a task item with consistent styling.
    
    Args:
        description: Task description
        due_date: Formatted due date string
        is_completed: Boolean indicating if task is completed
        author: (Optional) Author name for admin view
    """
    status_class = "completed" if is_completed else ""
    header = f"<strong>{author}</strong> - Due: {due_date}" if author else f"<strong>Due: {due_date}</strong>"
    
    st.markdown(f'''
    <div class="task-item {status_class}">
        {header}
        <p>{description[:100]}{'...' if len(description) > 100 else ''}</p>
    </div>
    ''', unsafe_allow_html=True)

def admin_navigation():
    """Create and return the admin navigation menu.
    
    Returns:
        str: Selected menu option
    """
    return option_menu(
        menu_title=None,
        options=["Dashboard", "Employees", "Reports", "Tasks", "Logout"],
        icons=["house", "people", "clipboard-data", "list-task", "box-arrow-right"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#f0f2f6", "border-radius": "10px", "margin-bottom": "20px"},
            "icon": {"color": "#1E88E5", "font-size": "16px"},
            "nav-link": {"font-size": "16px", "text-align": "center", "padding": "10px", "border-radius": "5px"},
            "nav-link-selected": {"background-color": "#1E88E5", "color": "white", "font-weight": "600"},
        }
    )

def employee_navigation():
    """Create and return the employee navigation menu.
    
    Returns:
        str: Selected menu option
    """
    return option_menu(
        menu_title=None,
        options=["Dashboard", "Submit Report", "My Reports", "My Tasks", "My Profile", "Logout"],
        icons=["house", "pencil", "journal-text", "list-check", "person-circle", "box-arrow-right"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#f0f2f6", "border-radius": "10px", "margin-bottom": "20px"},
            "icon": {"color": "#1E88E5", "font-size": "16px"},
            "nav-link": {"font-size": "16px", "text-align": "center", "padding": "10px", "border-radius": "5px"},
            "nav-link-selected": {"background-color": "#1E88E5", "color": "white", "font-weight": "600"},
        }
    )
