import streamlit as st
from sqlalchemy import text
from database.models import EmployeeModel

def manage_employees(engine):
    """Manage employees - listing, adding, activating/deactivating.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Manage Employees</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Employee List", "Add New Employee"])
    
    with tab1:
        display_employee_list(engine)
    
    with tab2:
        add_new_employee(engine)

def display_employee_list(engine):
    """Display the list of employees with management options.
    
    Args:
        engine: SQLAlchemy database engine
    """
    # Fetch and display all employees
    with engine.connect() as conn:
        employees = EmployeeModel.get_all_employees(conn)
    
    if not employees:
        st.info("No employees found. Add employees using the 'Add New Employee' tab.")
    else:
        st.write(f"Total employees: {len(employees)}")
        
        for i, employee in enumerate(employees):
            with st.expander(f"{employee[2]} ({employee[1]})", expanded=False):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    try:
                        st.image(employee[3], width=100, use_container_width=False)
                    except:
                        st.image("https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y", width=100)
                
                with col2:
                    st.write(f"**Username:** {employee[1]}")
                    st.write(f"**Full Name:** {employee[2]}")
                    st.write(f"**Status:** {'Active' if employee[4] else 'Inactive'}")
                    
                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if employee[4]:  # If active
                            if st.button(f"Deactivate", key=f"deactivate_{employee[0]}"):
                                with engine.connect() as conn:
                                    EmployeeModel.update_employee_status(conn, employee[0], False)
                                st.success(f"Deactivated employee: {employee[2]}")
                                st.rerun()
                        else:  # If inactive
                            if st.button(f"Activate", key=f"activate_{employee[0]}"):
                                with engine.connect() as conn:
                                    EmployeeModel.update_employee_status(conn, employee[0], True)
                                st.success(f"Activated employee: {employee[2]}")
                                st.rerun()
                    
                    with col2:
                        if st.button(f"Reset Password", key=f"reset_{employee[0]}"):
                            new_password = "password123"  # Default reset password
                            with engine.connect() as conn:
                                EmployeeModel.reset_password(conn, employee[0], new_password)
                            st.success(f"Password reset to '{new_password}' for {employee[2]}")

def add_new_employee(engine):
    """Form to add a new employee.
    
    Args:
        engine: SQLAlchemy database engine
    """
    # Form to add new employee
    with st.form("add_employee_form"):
        username = st.text_input("Username", help="Username for employee login")
        password = st.text_input("Password", type="password", help="Initial password")
        full_name = st.text_input("Full Name")
        profile_pic_url = st.text_input("Profile Picture URL", help="Link to employee profile picture")
        
        submitted = st.form_submit_button("Add Employee")
        if submitted:
            if not username or not password or not full_name:
                st.error("Please fill all required fields")
            else:
                # Check if username already exists
                with engine.connect() as conn:
                    result = conn.execute(text('SELECT COUNT(*) FROM employees WHERE username = :username'), 
                                          {'username': username})
                    count = result.fetchone()[0]
                    
                    if count > 0:
                        st.error(f"Username '{username}' already exists")
                    else:
                        # Insert new employee
                        try:
                            EmployeeModel.add_employee(conn, username, password, full_name, profile_pic_url)
                            st.success(f"Successfully added employee: {full_name}")
                        except Exception as e:
                            st.error(f"Error adding employee: {e}")
