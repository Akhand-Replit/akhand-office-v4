import streamlit as st
from sqlalchemy import text

def authenticate(engine, username, password):
    """Authenticate a user based on username and password.
    
    Args:
        engine: SQLAlchemy database engine
        username: User's username
        password: User's password
        
    Returns:
        dict: User information if authentication succeeds, None otherwise
    """
    # Check if admin credentials are properly set in Streamlit secrets
    if "admin_username" not in st.secrets or "admin_password" not in st.secrets:
        st.warning("Admin credentials are not properly configured in Streamlit secrets. Please set admin_username and admin_password in .streamlit/secrets.toml")
        return None
    
    # Check if credentials match admin in Streamlit secrets
    admin_username = st.secrets["admin_username"]
    admin_password = st.secrets["admin_password"]
    
    if username == admin_username and password == admin_password:
        return {
            "id": 0,  # Special ID for admin
            "username": username, 
            "full_name": "Administrator", 
            "user_type": "admin",
            "profile_pic_url": "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"
        }
    
    # If not admin, check company credentials
    with engine.connect() as conn:
        result = conn.execute(text('''
        SELECT id, company_name, username, profile_pic_url
        FROM companies
        WHERE username = :username AND password = :password AND is_active = TRUE
        '''), {'username': username, 'password': password})
        company = result.fetchone()
    
    if company:
        return {
            "id": company[0], 
            "username": company[2], 
            "full_name": company[1], 
            "user_type": "company",
            "profile_pic_url": company[3]
        }
    
    # If not company, check employee credentials with role information
    with engine.connect() as conn:
        result = conn.execute(text('''
        SELECT e.id, e.username, e.full_name, e.profile_pic_url, 
               b.id as branch_id, b.branch_name, c.id as company_id, c.company_name,
               r.id as role_id, r.role_name, r.role_level
        FROM employees e
        JOIN branches b ON e.branch_id = b.id
        JOIN companies c ON b.company_id = c.id
        JOIN employee_roles r ON e.role_id = r.id
        WHERE e.username = :username AND e.password = :password 
          AND e.is_active = TRUE AND b.is_active = TRUE AND c.is_active = TRUE
        '''), {'username': username, 'password': password})
        employee = result.fetchone()
    
    if employee:
        return {
            "id": employee[0], 
            "username": employee[1], 
            "full_name": employee[2],
            "user_type": "employee",
            "profile_pic_url": employee[3],
            "branch_id": employee[4],
            "branch_name": employee[5],
            "company_id": employee[6],
            "company_name": employee[7],
            "role_id": employee[8],
            "role_name": employee[9],
            "role_level": employee[10]
        }
    
    return None

def logout():
    """Log out the current user by clearing session state."""
    st.session_state.pop("user", None)
    st.rerun()