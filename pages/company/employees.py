import streamlit as st
from sqlalchemy import text
from database.models import EmployeeModel, BranchModel, RoleModel

def manage_employees(engine):
    """Manage employees with role assignment and branch transfers.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Manage Employees</h2>', unsafe_allow_html=True)
    
    company_id = st.session_state.user["id"]
    
    tabs = st.tabs(["Employee List", "Add New Employee", "Update Role", "Transfer Branch"])
    
    with tabs[0]:
        display_employee_list(engine, company_id)
    
    with tabs[1]:
        add_new_employee(engine, company_id)
        
    with tabs[2]:
        update_employee_role(engine, company_id)
        
    with tabs[3]:
        transfer_employee_branch(engine, company_id)
    
    # Handle edit form if an employee is selected
    if hasattr(st.session_state, 'edit_employee'):
        edit_employee(engine, company_id)

def display_employee_list(engine, company_id):
    """Display the list of employees grouped by branch and role.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    # Get all employees for this company
    with engine.connect() as conn:
        employees = EmployeeModel.get_all_employees(conn, company_id)
    
    if not employees:
        st.info("No employees found. Add employees using the 'Add New Employee' tab.")
        return
    
    # Group employees by branch
    employees_by_branch = {}
    for employee in employees:
        branch_name = employee[5]
        if branch_name not in employees_by_branch:
            employees_by_branch[branch_name] = []
        employees_by_branch[branch_name].append(employee)
    
    st.write(f"Total employees: {len(employees)}")
    
    # Display employees by branch
    for branch_name, branch_employees in employees_by_branch.items():
        with st.expander(f"📍 {branch_name} ({len(branch_employees)} employees)", expanded=False):
            # Group branch employees by role
            employees_by_role = {}
            for employee in branch_employees:
                role_name = employee[7]
                if role_name not in employees_by_role:
                    employees_by_role[role_name] = []
                employees_by_role[role_name].append(employee)
            
            # Display employees by role
            for role_name, role_employees in sorted(employees_by_role.items(), 
                                                   key=lambda x: next((e[8] for e in x[1]), 999)):
                st.markdown(f"**{role_name}s:**")
                
                for employee in role_employees:
                    employee_id = employee[0]
                    username = employee[1]
                    full_name = employee[2]
                    profile_pic_url = employee[3]
                    is_active = employee[4]
                    branch_id = employee[9]
                    
                    cols = st.columns([1, 3, 1])
                    with cols[0]:
                        try:
                            st.image(profile_pic_url, width=60)
                        except:
                            st.image("https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y", width=60)
                    
                    with cols[1]:
                        st.write(f"**{full_name}** (@{username})")
                        st.write(f"Role: {role_name} | Status: {'Active' if is_active else 'Inactive'}")
                    
                    with cols[2]:
                        if st.button("Actions", key=f"actions_{employee_id}"):
                            st.session_state.employee_actions = employee_id
                            st.rerun()
                    
                    # Show actions if selected
                    if hasattr(st.session_state, 'employee_actions') and st.session_state.employee_actions == employee_id:
                        action_cols = st.columns(4)
                        
                        with action_cols[0]:
                            if st.button("Edit", key=f"edit_{employee_id}"):
                                st.session_state.edit_employee = {
                                    'id': employee_id,
                                    'username': username,
                                    'full_name': full_name,
                                    'profile_pic_url': profile_pic_url,
                                    'is_active': is_active
                                }
                                st.rerun()
                        
                        with action_cols[1]:
                            if is_active:
                                if st.button("Deactivate", key=f"deactivate_{employee_id}"):
                                    with engine.connect() as conn:
                                        EmployeeModel.update_employee_status(conn, employee_id, False)
                                    st.success(f"Deactivated employee: {full_name}")
                                    st.rerun()
                            else:
                                if st.button("Activate", key=f"activate_{employee_id}"):
                                    with engine.connect() as conn:
                                        EmployeeModel.update_employee_status(conn, employee_id, True)
                                    st.success(f"Activated employee: {full_name}")
                                    st.rerun()
                        
                        with action_cols[2]:
                            if st.button("Reset Password", key=f"reset_{employee_id}"):
                                new_password = "employee123"  # Default reset password
                                with engine.connect() as conn:
                                    EmployeeModel.reset_password(conn, employee_id, new_password)
                                st.success(f"Password reset to '{new_password}' for {full_name}")
                        
                        with action_cols[3]:
                            if st.button("Close", key=f"close_{employee_id}"):
                                del st.session_state.employee_actions
                                st.rerun()

def add_new_employee(engine, company_id):
    """Form to add a new employee with role and branch assignment.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    st.markdown("### Add New Employee")
    
    # Get active branches
    with engine.connect() as conn:
        branches = BranchModel.get_active_branches(conn, company_id)
        roles = RoleModel.get_all_roles(conn, company_id)
    
    if not branches:
        st.warning("No active branches found. Please add and activate branches first.")
        return
    
    if not roles:
        st.warning("No roles defined. Please contact your administrator.")
        return
    
    # Convert to dictionaries for selection
    branch_options = {branch[1]: branch[0] for branch in branches}
    role_options = {role[1]: role[0] for role in roles}
    
    with st.form("add_employee_form"):
        st.subheader("Employee Details")
        
        full_name = st.text_input("Full Name", help="Employee's full name")
        username = st.text_input("Username", help="Username for employee login")
        password = st.text_input("Password", type="password", help="Initial password")
        profile_pic_url = st.text_input("Profile Picture URL", help="Link to employee profile picture")
        
        st.subheader("Assignment")
        selected_branch = st.selectbox("Branch", list(branch_options.keys()))
        selected_role = st.selectbox("Role", list(role_options.keys()))
        
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
                        # Get branch and role IDs
                        branch_id = branch_options[selected_branch]
                        role_id = role_options[selected_role]
                        
                        # Insert new employee
                        try:
                            with engine.connect() as conn:
                                EmployeeModel.add_employee(
                                    conn, 
                                    branch_id, 
                                    role_id, 
                                    username, 
                                    password, 
                                    full_name, 
                                    profile_pic_url
                                )
                            st.success(f"Successfully added employee: {full_name}")
                        except Exception as e:
                            st.error(f"Error adding employee: {e}")

def update_employee_role(engine, company_id):
    """Form to update an employee's role.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    st.markdown("### Update Employee Role")
    
    # Get employees and roles
    with engine.connect() as conn:
        employees = EmployeeModel.get_all_employees(conn, company_id)
        roles = RoleModel.get_all_roles(conn, company_id)
    
    if not employees:
        st.warning("No employees found.")
        return
    
    if not roles:
        st.warning("No roles defined. Please contact your administrator.")
        return
    
    # Create employee options
    employee_options = {}
    for emp in employees:
        display_name = f"{emp[2]} ({emp[7]}, {emp[5]})"
        employee_options[display_name] = emp[0]
    
    # Create role options
    role_options = {role[1]: role[0] for role in roles}
    
    with st.form("update_role_form"):
        selected_employee = st.selectbox("Select Employee", list(employee_options.keys()))
        selected_role = st.selectbox("New Role", list(role_options.keys()))
        
        submitted = st.form_submit_button("Update Role")
        if submitted:
            employee_id = employee_options[selected_employee]
            role_id = role_options[selected_role]
            
            # Update the employee's role
            try:
                with engine.connect() as conn:
                    EmployeeModel.update_employee_role(conn, employee_id, role_id)
                st.success(f"Successfully updated role for {selected_employee.split('(')[0].strip()}")
            except Exception as e:
                st.error(f"Error updating role: {e}")

def transfer_employee_branch(engine, company_id):
    """Form to transfer an employee to a different branch.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    st.markdown("### Transfer Employee to Another Branch")
    
    # Get employees and branches
    with engine.connect() as conn:
        employees = EmployeeModel.get_all_employees(conn, company_id)
        branches = BranchModel.get_active_branches(conn, company_id)
    
    if not employees:
        st.warning("No employees found.")
        return
    
    if not branches or len(branches) < 2:
        st.warning("You need at least two active branches to transfer employees.")
        return
    
    # Create employee options
    employee_options = {}
    for emp in employees:
        display_name = f"{emp[2]} ({emp[7]}, {emp[5]})"
        employee_options[display_name] = (emp[0], emp[9])  # (employee_id, current_branch_id)
    
    # Create branch options
    branch_options = {branch[1]: branch[0] for branch in branches}
    
    with st.form("transfer_branch_form"):
        selected_employee = st.selectbox("Select Employee", list(employee_options.keys()))
        
        # Get current branch ID for the selected employee
        current_branch_id = employee_options[selected_employee][1]
        
        # Filter out the current branch from options
        available_branches = {k: v for k, v in branch_options.items() if v != current_branch_id}
        
        if not available_branches:
            st.warning("No other branches available for transfer.")
            st.form_submit_button("Transfer", disabled=True)
        else:
            selected_branch = st.selectbox("Transfer to Branch", list(available_branches.keys()))
            
            submitted = st.form_submit_button("Transfer")
            if submitted:
                employee_id = employee_options[selected_employee][0]
                new_branch_id = available_branches[selected_branch]
                
                # Transfer the employee
                try:
                    with engine.connect() as conn:
                        EmployeeModel.update_employee_branch(conn, employee_id, new_branch_id)
                    st.success(f"Successfully transferred {selected_employee.split('(')[0].strip()} to {selected_branch}")
                except Exception as e:
                    st.error(f"Error transferring employee: {e}")

def edit_employee(engine, company_id):
    """Edit an employee's profile.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    st.markdown('<h3 class="sub-header">Edit Employee</h3>', unsafe_allow_html=True)
    
    with st.form("edit_employee_form"):
        # Display current information
        employee_id = st.session_state.edit_employee['id']
        username = st.session_state.edit_employee['username']
        st.write(f"Username: {username} (cannot be changed)")
        
        # Editable fields
        full_name = st.text_input("Full Name", value=st.session_state.edit_employee['full_name'])
        profile_pic_url = st.text_input("Profile Picture URL", 
                                       value=st.session_state.edit_employee['profile_pic_url'] or "")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Update Profile")
        with col2:
            canceled = st.form_submit_button("Cancel")
        
        if submitted:
            if not full_name:
                st.error("Full name is required")
            else:
                # Update profile
                try:
                    with engine.connect() as conn:
                        EmployeeModel.update_profile(conn, employee_id, full_name, profile_pic_url)
                    st.success(f"Profile updated successfully for {full_name}")
                    del st.session_state.edit_employee
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating profile: {e}")
        
        if canceled:
            del st.session_state.edit_employee
            st.rerun()
