import streamlit as st
import datetime
from database.models import TaskModel, EmployeeModel
from utils.helpers import format_timestamp

def manage_tasks(engine):
    """View and manage all employee tasks.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Manage Tasks</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["View Tasks", "Assign New Task"])
    
    with tab1:
        view_tasks(engine)
    
    with tab2:
        assign_new_task(engine)

def view_tasks(engine):
    """View and filter tasks.
    
    Args:
        engine: SQLAlchemy database engine
    """
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        # Employee filter
        with engine.connect() as conn:
            employees = EmployeeModel.get_active_employees(conn)
        
        employee_options = ["All Employees"] + [emp[1] for emp in employees]
        employee_filter = st.selectbox("Select Employee", employee_options, key="task_employee_filter")
    
    with col2:
        # Status filter
        status_options = ["All Tasks", "Pending", "Completed"]
        status_filter = st.selectbox("Task Status", status_options, key="admin_task_status_filter")
    
    # Fetch tasks based on filters
    with engine.connect() as conn:
        tasks = TaskModel.get_all_tasks(conn, employee_filter, status_filter)
    
    # Display tasks
    if not tasks:
        st.info("No tasks found for the selected criteria")
    else:
        st.write(f"Found {len(tasks)} tasks")
        
        for task in tasks:
            task_id = task[0]
            employee_name = task[1]
            task_description = task[2]
            due_date = format_timestamp(task[3])
            is_completed = task[4]
            created_at = format_timestamp(task[5])
            
            # Display the task with status-based styling
            status_class = "completed" if is_completed else ""
            st.markdown(f'''
            <div class="task-item {status_class}">
                <strong>{employee_name}</strong> - Due: {due_date}
                <p>{task_description}</p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #777; font-size: 0.8rem;">Created: {created_at}</span>
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
                    if st.button(f"Mark as Completed", key=f"complete_{task_id}"):
                        with engine.connect() as conn:
                            TaskModel.update_task_status(conn, task_id, True)
                        st.success("Task marked as completed")
                        st.rerun()
                else:
                    if st.button(f"Reopen Task", key=f"reopen_{task_id}"):
                        with engine.connect() as conn:
                            TaskModel.update_task_status(conn, task_id, False)
                        st.success("Task reopened")
                        st.rerun()
            
            with col2:
                if st.button(f"Delete Task", key=f"delete_{task_id}"):
                    with engine.connect() as conn:
                        TaskModel.delete_task(conn, task_id)
                    st.success("Task deleted")
                    st.rerun()

def assign_new_task(engine):
    """Form to assign a new task to an employee.
    
    Args:
        engine: SQLAlchemy database engine
    """
    # Form to assign new task
    with st.form("assign_task_form"):
        # Employee selection
        with engine.connect() as conn:
            employees = EmployeeModel.get_active_employees(conn)
        
        employee_map = {emp[1]: emp[0] for emp in employees}
        employee = st.selectbox("Assign to Employee", [emp[1] for emp in employees])
        
        # Task details
        task_description = st.text_area("Task Description")
        due_date = st.date_input("Due Date", datetime.date.today() + datetime.timedelta(days=7))
        
        submitted = st.form_submit_button("Assign Task")
        if submitted:
            if not task_description:
                st.error("Please enter a task description")
            else:
                # Insert new task
                try:
                    with engine.connect() as conn:
                        TaskModel.add_task(conn, employee_map[employee], task_description, due_date)
                    st.success(f"Successfully assigned task to {employee}")
                except Exception as e:
                    st.error(f"Error assigning task: {e}")
