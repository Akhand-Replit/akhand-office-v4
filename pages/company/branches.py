import streamlit as st
from sqlalchemy import text
from database.models import BranchModel

def manage_branches(engine):
    """Manage branches including sub-branches.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Manage Branches</h2>', unsafe_allow_html=True)
    
    company_id = st.session_state.user["id"]
    
    tabs = st.tabs(["Branch List", "Add Main Branch", "Add Sub-Branch"])
    
    with tabs[0]:
        display_branch_list(engine, company_id)
    
    with tabs[1]:
        add_main_branch(engine, company_id)
        
    with tabs[2]:
        add_sub_branch(engine, company_id)

def display_branch_list(engine, company_id):
    """Display the list of branches for this company with a hierarchical view.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    # Fetch all branches
    with engine.connect() as conn:
        branches = BranchModel.get_company_branches(conn, company_id)
    
    if not branches:
        st.info("No branches found. Please create a main branch first.")
        return
    
    # Group branches by parent
    main_branches = []
    sub_branches = {}
    
    for branch in branches:
        branch_id = branch[0]
        is_main = branch[5]
        parent_id = branch[6]
        
        if is_main:
            main_branches.append(branch)
        elif parent_id:
            if parent_id not in sub_branches:
                sub_branches[parent_id] = []
            sub_branches[parent_id].append(branch)
    
    # Display branches hierarchically
    st.write(f"Total branches: {len(branches)}")
    
    # Display main branches first
    for main_branch in main_branches:
        display_branch_with_subbranches(engine, main_branch, sub_branches)

def display_branch_with_subbranches(engine, branch, sub_branches):
    """Display a branch and its sub-branches recursively.
    
    Args:
        engine: SQLAlchemy database engine
        branch: Branch data tuple
        sub_branches: Dictionary of sub-branches by parent ID
    """
    branch_id = branch[0]
    branch_name = branch[1]
    location = branch[2] or "No location specified"
    branch_head = branch[3] or "No head assigned"
    is_active = branch[4]
    is_main = branch[5]
    
    # Branch header with indentation based on level
    prefix = "📍 Main Branch: " if is_main else "└─ "
    with st.expander(f"{prefix}{branch_name}", expanded=False):
        st.write(f"**Location:** {location}")
        st.write(f"**Branch Head:** {branch_head}")
        st.write(f"**Status:** {'Active' if is_active else 'Inactive'}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"Edit Branch", key=f"edit_branch_{branch_id}"):
                st.session_state.edit_branch = {
                    'id': branch_id,
                    'name': branch_name,
                    'location': location if location != "No location specified" else "",
                    'head': branch_head if branch_head != "No head assigned" else "",
                    'is_main': is_main
                }
                st.rerun()
        
        with col2:
            if is_active:
                if st.button(f"Deactivate", key=f"deactivate_branch_{branch_id}"):
                    with engine.connect() as conn:
                        BranchModel.update_branch_status(conn, branch_id, False)
                    st.success(f"Deactivated branch: {branch_name}")
                    st.rerun()
            else:
                if st.button(f"Activate", key=f"activate_branch_{branch_id}"):
                    with engine.connect() as conn:
                        BranchModel.update_branch_status(conn, branch_id, True)
                    st.success(f"Activated branch: {branch_name}")
                    st.rerun()
        
        with col3:
            if st.button(f"View Employees", key=f"view_employees_{branch_id}"):
                st.session_state.view_branch_employees = branch_id
                st.session_state.view_branch_name = branch_name
                st.rerun()
        
        # Show employees if requested
        if hasattr(st.session_state, 'view_branch_employees') and st.session_state.view_branch_employees == branch_id:
            display_branch_employees(engine, branch_id, branch_name)
        
        # Display sub-branches if any
        if branch_id in sub_branches:
            st.markdown("#### Sub-branches:")
            for sub_branch in sub_branches[branch_id]:
                with st.container():
                    st.markdown(f"**{sub_branch[1]}**")
                    cols = st.columns(4)
                    with cols[0]:
                        st.write(f"Location: {sub_branch[2] or 'N/A'}")
                    with cols[1]:
                        st.write(f"Head: {sub_branch[3] or 'N/A'}")
                    with cols[2]:
                        st.write(f"Status: {'Active' if sub_branch[4] else 'Inactive'}")
                    with cols[3]:
                        if st.button(f"Details", key=f"detail_sub_{sub_branch[0]}"):
                            # Recursively display sub-branches
                            display_branch_with_subbranches(engine, sub_branch, sub_branches)

def display_branch_employees(engine, branch_id, branch_name):
    """Display employees for a specific branch.
    
    Args:
        engine: SQLAlchemy database engine
        branch_id: ID of the branch
        branch_name: Name of the branch for display
    """
    st.markdown(f"#### Employees in {branch_name}")
    
    # Fetch employees for this branch
    with engine.connect() as conn:
        employees = BranchModel.get_branch_employees(conn, branch_id)
    
    if not employees:
        st.info(f"No employees found in {branch_name}.")
    else:
        # Group employees by role
        employees_by_role = {}
        for employee in employees:
            role_name = employee[5]
            if role_name not in employees_by_role:
                employees_by_role[role_name] = []
            employees_by_role[role_name].append(employee)
        
        # Display employees by role
        for role_name, role_employees in employees_by_role.items():
            st.markdown(f"**{role_name}s ({len(role_employees)})**")
            for employee in role_employees:
                with st.container():
                    cols = st.columns(4)
                    with cols[0]:
                        st.write(f"{employee[2]}")
                    with cols[1]:
                        st.write(f"Status: {'Active' if employee[4] else 'Inactive'}")
    
    # Close button
    if st.button("Close Employee View", key=f"close_employees_{branch_id}"):
        del st.session_state.view_branch_employees
        del st.session_state.view_branch_name
        st.rerun()

def add_main_branch(engine, company_id):
    """Form to add a new main branch.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    st.markdown("### Create Main Branch")
    st.info("Main branches serve as headquarters or primary operational centers.")
    
    with st.form("add_main_branch_form"):
        branch_name = st.text_input("Branch Name", help="Name of the main branch")
        location = st.text_input("Location", help="Physical location of the branch")
        branch_head = st.text_input("Branch Head", help="Name of the person heading the branch")
        
        submitted = st.form_submit_button("Create Main Branch")
        if submitted:
            if not branch_name:
                st.error("Please enter a branch name")
            else:
                # Check if branch name already exists for this company
                with engine.connect() as conn:
                    result = conn.execute(text('''
                    SELECT COUNT(*) FROM branches 
                    WHERE company_id = :company_id AND branch_name = :branch_name
                    '''), {'company_id': company_id, 'branch_name': branch_name})
                    count = result.fetchone()[0]
                
                if count > 0:
                    st.error(f"Branch with name '{branch_name}' already exists")
                else:
                    # Create new main branch
                    try:
                        with engine.connect() as conn:
                            BranchModel.create_main_branch(conn, company_id, branch_name, location, branch_head)
                        st.success(f"Successfully created main branch: {branch_name}")
                    except Exception as e:
                        st.error(f"Error creating branch: {e}")

def add_sub_branch(engine, company_id):
    """Form to add a new sub-branch under a parent branch.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    st.markdown("### Create Sub-Branch")
    st.info("Sub-branches operate under main branches or other sub-branches.")
    
    # Get available parent branches
    with engine.connect() as conn:
        parent_branches = BranchModel.get_parent_branches(conn, company_id)
    
    if not parent_branches:
        st.warning("You need to create a main branch first before adding sub-branches.")
        return
    
    with st.form("add_sub_branch_form"):
        # Convert parent branches to a dict for selection
        parent_options = {branch[1]: branch[0] for branch in parent_branches}
        
        parent_name = st.selectbox("Parent Branch", list(parent_options.keys()), 
                                  help="The branch under which this sub-branch will operate")
        branch_name = st.text_input("Branch Name", help="Name of the sub-branch")
        location = st.text_input("Location", help="Physical location of the branch")
        branch_head = st.text_input("Branch Head", help="Name of the person heading the branch")
        
        submitted = st.form_submit_button("Create Sub-Branch")
        if submitted:
            if not branch_name:
                st.error("Please enter a branch name")
            else:
                # Check if branch name already exists for this company
                with engine.connect() as conn:
                    result = conn.execute(text('''
                    SELECT COUNT(*) FROM branches 
                    WHERE company_id = :company_id AND branch_name = :branch_name
                    '''), {'company_id': company_id, 'branch_name': branch_name})
                    count = result.fetchone()[0]
                
                if count > 0:
                    st.error(f"Branch with name '{branch_name}' already exists")
                else:
                    # Create new sub-branch
                    try:
                        parent_id = parent_options[parent_name]
                        with engine.connect() as conn:
                            BranchModel.create_sub_branch(
                                conn, 
                                company_id, 
                                parent_id, 
                                branch_name, 
                                location, 
                                branch_head
                            )
                        st.success(f"Successfully created sub-branch: {branch_name} under {parent_name}")
                    except Exception as e:
                        st.error(f"Error creating sub-branch: {e}")

# Edit branch form - shown when a branch is selected for editing
def edit_branch(engine):
    """Edit a branch.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h3 class="sub-header">Edit Branch</h3>', unsafe_allow_html=True)
    
    branch_id = st.session_state.edit_branch['id']
    is_main = st.session_state.edit_branch['is_main']
    company_id = st.session_state.user["id"]
    
    with st.form("edit_branch_form"):
        branch_name = st.text_input("Branch Name", value=st.session_state.edit_branch['name'])
        location = st.text_input("Location", value=st.session_state.edit_branch['location'])
        branch_head = st.text_input("Branch Head", value=st.session_state.edit_branch['head'])
        
        # Parent branch selection (only for sub-branches)
        parent_id = None
        if not is_main:
            # Get available parent branches (excluding this branch to prevent circular references)
            with engine.connect() as conn:
                parent_branches = BranchModel.get_parent_branches(conn, company_id, exclude_branch_id=branch_id)
                
                if parent_branches:
                    # Get current parent branch
                    branch_info = BranchModel.get_branch_by_id(conn, branch_id)
                    current_parent_id = branch_info[6] if branch_info else None
                    current_parent_name = branch_info[8] if branch_info else None
                    
                    # Create options dict
                    parent_options = {branch[1]: branch[0] for branch in parent_branches}
                    
                    # Default to current parent if it exists
                    default_idx = 0
                    if current_parent_name and current_parent_name in list(parent_options.keys()):
                        default_idx = list(parent_options.keys()).index(current_parent_name)
                    
                    parent_name = st.selectbox(
                        "Parent Branch", 
                        list(parent_options.keys()),
                        index=default_idx,
                        help="The branch under which this sub-branch operates"
                    )
                    
                    parent_id = parent_options[parent_name]
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Update Branch")
        with col2:
            canceled = st.form_submit_button("Cancel")
        
        if submitted:
            if not branch_name:
                st.error("Branch name is required")
            else:
                # Check if the branch name already exists for another branch
                with engine.connect() as conn:
                    result = conn.execute(text('''
                    SELECT COUNT(*) FROM branches 
                    WHERE company_id = :company_id AND branch_name = :branch_name AND id != :branch_id
                    '''), {
                        'company_id': company_id, 
                        'branch_name': branch_name,
                        'branch_id': branch_id
                    })
                    count = result.fetchone()[0]
                
                if count > 0:
                    st.error(f"Another branch with name '{branch_name}' already exists")
                else:
                    # Update branch details
                    try:
                        with engine.connect() as conn:
                            BranchModel.update_branch(
                                conn, 
                                branch_id, 
                                branch_name, 
                                location, 
                                branch_head,
                                parent_id
                            )
                        st.success(f"Branch updated successfully: {branch_name}")
                        del st.session_state.edit_branch
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating branch: {e}")
        
        if canceled:
            del st.session_state.edit_branch
            st.rerun()
