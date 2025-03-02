import streamlit as st
import datetime
from database.models.task_model import TaskModel
from database.models.branch_model import BranchModel
from database.models.employee_model import EmployeeModel
from database.models.role_model import RoleModel

def manage_tasks(engine):
    """Manage tasks with branch-level or direct employee assignment.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Manage Tasks</h2>', unsafe_allow_html=True)
    
    company_id = st.session_state.user["id"]
    
    tabs = st.tabs(["Task List", "Assign New Task", "Task Progress"])
    
    with tabs[0]:
        view_tasks(engine, company_id)
    
    with tabs[1]:
        assign_task(engine, company_id)
        
    with tabs[2]:
        view_task_progress(engine, company_id)

def view_tasks(engine, company_id):
    """View all tasks for the company with filters.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    st.markdown("### All Tasks")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        status_options = ["All Tasks", "Pending", "Completed"]
        status_filter = st.selectbox("Status", status_options, key="task_status_filter")
    
    with col2:
        assignment_options = ["All Assignments", "Branch Tasks", "Employee Tasks"]
        assignment_filter = st.selectbox("Assignment Type", assignment_options, key="assignment_type_filter")
    
    # Fetch tasks based on filters
    status = None if status_filter == "All Tasks" else (status_filter == "Completed")
    
    with engine.connect() as conn:
        tasks = TaskModel.get_tasks_for_company(conn, company_id, status_filter)
    
    if not tasks:
        st.info("No tasks found matching the selected criteria.")
        return
    
    # Filter by assignment type
    if assignment_filter == "Branch Tasks":
        tasks = [t for t in tasks if t[8] == "branch"]
    elif assignment_filter == "Employee Tasks":
        tasks = [t for t in tasks if t[8] == "employee"]
    
    st.write(f"Found {len(tasks)} tasks")
    
    # Display tasks
    for task in tasks:
        task_id = task[0]
        description = task[1]
        due_date = task[2].strftime('%d %b, %Y') if task[2] else "No due date"
        is_completed = task[3]
        completed_at = task[4].strftime('%d %b, %Y %H:%M') if task[4] else None
        assignee_name = task[8]
        assignee_type = task[9]
        completed_by = task[10]
        
        # Create card with appropriate styling
        bg_color = "#f0f0f0" if is_completed else "#f1fff1"
        border_color = "#9e9e9e" if is_completed else "#4CAF50"
        
        st.markdown(f'''
        <div style="background-color: {bg_color}; padding: 1rem; border-radius: 8px; 
                    margin-bottom: 0.5rem; border-left: 4px solid {border_color};">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="font-weight: 600;">{assignee_name} ({assignee_type.capitalize()})</span>
                <span style="color: #777;">Due: {due_date}</span>
            </div>
            <p>{description}</p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #777; font-size: 0.8rem;">
                    {f"Completed by {completed_by} on {completed_at}" if is_completed else "Pending"}
                </span>
                <span style="font-weight: 600; color: {'#9e9e9e' if is_completed else '#4CAF50'};">
                    {"Completed" if is_completed else "Pending"}
                </span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if not is_completed:
                pass  # Companies don't mark tasks as completed directly
            else:
                if st.button(f"Reopen Task", key=f"reopen_{task_id}"):
                    with engine.connect() as conn:
                        TaskModel.reopen_task(conn, task_id)
                    st.success("Task reopened")
                    st.rerun()
        
        with col2:
            if st.button(f"View Progress", key=f"progress_{task_id}"):
                st.session_state.view_task_progress = task_id
                st.rerun()
            
            # For completed tasks, offer delete option
            if is_completed:
                if st.button(f"Delete Task", key=f"delete_{task_id}"):
                    with engine.connect() as conn:
                        TaskModel.delete_task(conn, task_id)
                    st.success("Task deleted")
                    st.rerun()
    
    # Show task progress if selected
    if hasattr(st.session_state, 'view_task_progress'):
        display_task_progress(engine, st.session_state.view_task_progress)

def display_task_progress(engine, task_id):
    """Display progress details for a branch-level task.
    
    Args:
        engine: SQLAlchemy database engine
        task_id: ID of the task
    """
    st.markdown("### Task Progress Details")
    
    with engine.connect() as conn:
        progress = TaskModel.get_branch_task_progress(conn, task_id)
    
    if not progress:
        st.info("This is not a branch-level task or no progress data is available.")
        
        # Close button
        if st.button("Close Progress View"):
            del st.session_state.view_task_progress
            st.rerun()
        
        return
    
    # Display progress stats
    total = progress['total']
    completed = progress['completed']
    completion_percentage = round((completed / total) * 100) if total > 0 else 0
    
    st.write(f"**Completion Rate:** {completed}/{total} employees ({completion_percentage}%)")
    
    # Progress bar
    st.progress(completion_percentage / 100)
    
    # Group statuses by role
    statuses_by_role = {}
    for status in progress['employee_statuses']:
        employee_id = status[0]
        name = status[1]
        is_completed = status[2]
        role = status[3]
        
        if role not in statuses_by_role:
            statuses_by_role[role] = []
        
        statuses_by_role[role].append((name, is_completed))
    
    # Display employee completion status by role
    for role, employees in sorted(statuses_by_role.items()):
        st.markdown(f"**{role}s:**")
        
        for name, is_completed in employees:
            icon = "✅" if is_completed else "⏳"
            st.write(f"{icon} {name}")
    
    # Close button
    if st.button("Close Progress View"):
        del st.session_state.view_task_progress
        st.rerun()

def assign_task(engine, company_id):
    """Form to assign a new task to a branch or employee.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    st.markdown("### Assign New Task")
    
    # Get active branches and employees
    with engine.connect() as conn:
        branches = BranchModel.get_active_branches(conn, company_id)
        roles = RoleModel.get_all_roles(conn, company_id)
    
    if not branches:
        st.warning("No active branches found. Please add and activate branches first.")
        return
    
    # Assignment options
    assignment_options = ["Branch", "Individual Employee"]
    assignment_type = st.radio("Assign To", assignment_options)
    
    with st.form("assign_task_form"):
        # Task details
        task_description = st.text_area("Task Description", height=100)
        due_date = st.date_input("Due Date", value=datetime.date.today() + datetime.timedelta(days=7))
        
        # Assignment based on selected type
        if assignment_type == "Branch":
            # Branch selection
            branch_options = {branch[1]: branch[0] for branch in branches}
            selected_branch = st.selectbox("Select Branch", list(branch_options.keys()))
            branch_id = branch_options[selected_branch] if selected_branch else None
            employee_id = None
        else:
            # Employee selection - first select branch, then employee
            branch_options = {branch[1]: branch[0] for branch in branches}
            selected_branch = st.selectbox("Employee's Branch", list(branch_options.keys()))
            
            if selected_branch:
                branch_id = branch_options[selected_branch]
                
                # Get employees for this branch
                with engine.connect() as conn:
                    branch_employees = EmployeeModel.get_branch_employees(conn, branch_id)
                
                if not branch_employees:
                    st.warning(f"No employees found in {selected_branch}.")
                    employee_id = None
                else:
                    # Group employees by role
                    employees_by_role = {}
                    for emp in branch_employees:
                        role_name = emp[5]
                        if role_name not in employees_by_role:
                            employees_by_role[role_name] = []
                        
                        employees_by_role[role_name].append((emp[0], emp[2]))  # (id, name)
                    
                    # Create a formatted selection list
                    employee_options = {}
                    for role_name, employees in sorted(employees_by_role.items()):
                        for emp_id, emp_name in employees:
                            employee_options[f"{emp_name} ({role_name})"] = emp_id
                    
                    selected_employee = st.selectbox("Select Employee", list(employee_options.keys()))
                    employee_id = employee_options[selected_employee] if selected_employee else None
                    branch_id = None  # Set to None since we're assigning directly to employee
            else:
                employee_id = None
        
        submitted = st.form_submit_button("Assign Task")
        if submitted:
            if not task_description:
                st.error("Please enter a task description")
            elif assignment_type == "Branch" and not branch_id:
                st.error("Please select a branch")
            elif assignment_type == "Individual Employee" and not employee_id:
                st.error("Please select an employee")
            else:
                # Create the task
                try:
                    with engine.connect() as conn:
                        task_id = TaskModel.create_task(
                            conn,
                            company_id, 
                            task_description, 
                            due_date,
                            branch_id,
                            employee_id
                        )
                    
                    if branch_id:
                        st.success(f"Task assigned to branch: {selected_branch}")
                    else:
                        st.success(f"Task assigned to employee: {selected_employee.split('(')[0].strip()}")
                except Exception as e:
                    st.error(f"Error assigning task: {e}")

def view_task_progress(engine, company_id):
    """View progress of branch-level tasks.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    st.markdown("### Branch Task Progress")
    
    # Get all branch-level tasks
    with engine.connect() as conn:
        tasks = TaskModel.get_tasks_for_company(conn, company_id)
    
    # Filter to only branch tasks
    branch_tasks = [t for t in tasks if t[9] == "branch"]
    
    if not branch_tasks:
        st.info("No branch-level tasks found.")
        return
    
    # Group tasks by status
    pending_tasks = [t for t in branch_tasks if not t[3]]
    completed_tasks = [t for t in branch_tasks if t[3]]
    
    # Display pending tasks first
    if pending_tasks:
        st.markdown("#### Pending Branch Tasks")
        
        for task in pending_tasks:
            task_id = task[0]
            description = task[1]
            due_date = task[2].strftime('%d %b, %Y') if task[2] else "No due date"
            branch_name = task[8]
            
            with st.expander(f"{branch_name}: {description[:50]}{'...' if len(description) > 50 else ''}", expanded=False):
                st.write(f"**Due Date:** {due_date}")
                st.write(f"**Description:** {description}")
                
                # Show progress
                with engine.connect() as conn:
                    progress = TaskModel.get_branch_task_progress(conn, task_id)
                
                if progress:
                    total = progress['total']
                    completed = progress['completed']
                    completion_percentage = round((completed / total) * 100) if total > 0 else 0
                    
                    st.write(f"**Completion Rate:** {completed}/{total} employees ({completion_percentage}%)")
                    st.progress(completion_percentage / 100)
                    
                    # Group by role for more compact display
                    completed_by_role = {}
                    total_by_role = {}
                    
                    for status in progress['employee_statuses']:
                        role = status[3]
                        is_completed = status[2]
                        
                        if role not in completed_by_role:
                            completed_by_role[role] = 0
                            total_by_role[role] = 0
                        
                        total_by_role[role] += 1
                        if is_completed:
                            completed_by_role[role] += 1
                    
                    # Display by role
                    for role in total_by_role.keys():
                        role_percentage = round((completed_by_role[role] / total_by_role[role]) * 100)
                        st.write(f"**{role}s:** {completed_by_role[role]}/{total_by_role[role]} ({role_percentage}%)")
    
    # Display completed tasks
    if completed_tasks:
        st.markdown("#### Completed Branch Tasks")
        
        for task in completed_tasks:
            task_id = task[0]
            description = task[1]
            completed_at = task[4].strftime('%d %b, %Y %H:%M') if task[4] else "Unknown"
            branch_name = task[8]
            completed_by = task[10]
            
            st.markdown(f'''
            <div style="background-color: #f0f0f0; padding: 1rem; border-radius: 8px; 
                        margin-bottom: 0.5rem; border-left: 4px solid #9e9e9e;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span style="font-weight: 600;">{branch_name}</span>
                    <span style="color: #777;">Completed: {completed_at}</span>
                </div>
                <p>{description}</p>
                <div style="text-align: right; color: #777; font-size: 0.8rem;">
                    Marked complete by: {completed_by if completed_by else "All employees"}
                </div>
            </div>
            ''', unsafe_allow_html=True)
