import streamlit as st
from database.models import TaskModel
from utils.helpers import format_timestamp

def view_my_tasks(engine):
    """View and manage personal tasks.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">My Tasks</h2>', unsafe_allow_html=True)
    
    employee_id = st.session_state.user["id"]
    
    # Task status filter
    status_options = ["All Tasks", "Pending", "Completed"]
    status_filter = st.selectbox("Show", status_options, key="employee_task_status_filter")
    
    # Determine task completion filter based on selection
    completed_filter = None
    if status_filter == "Pending":
        completed_filter = False
    elif status_filter == "Completed":
        completed_filter = True
    
    # Fetch tasks
    with engine.connect() as conn:
        tasks = TaskModel.get_employee_tasks(conn, employee_id, completed_filter)
    
    # Display tasks
    if not tasks:
        st.info("No tasks found")
    else:
        st.write(f"Found {len(tasks)} tasks")
        
        # Separate into pending and completed for better organization
        pending_tasks = [task for task in tasks if not task[3]]
        completed_tasks = [task for task in tasks if task[3]]
        
        # Display pending tasks first
        if pending_tasks and status_filter != "Completed":
            st.markdown('<h3 class="sub-header">Pending Tasks</h3>', unsafe_allow_html=True)
            
            for task in pending_tasks:
                task_id = task[0]
                task_description = task[1]
                due_date = format_timestamp(task[2])
                created_at = format_timestamp(task[4])
                task_date_str = task[2].strftime('%Y%m%d') if task[2] else 'nodate'
                
                st.markdown(f'''
                <div class="task-item">
                    <strong>Due: {due_date}</strong>
                    <p>{task_description}</p>
                    <div style="text-align: right; color: #777; font-size: 0.8rem;">
                        Created: {created_at}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button(f"Mark as Completed", key=f"employee_complete_{task_id}_{task_date_str}"):
                    with engine.connect() as conn:
                        TaskModel.update_task_status(conn, task_id, True)
                    st.success("Task marked as completed")
                    st.rerun()
        
        # Display completed tasks
        if completed_tasks and status_filter != "Pending":
            st.markdown('<h3 class="sub-header">Completed Tasks</h3>', unsafe_allow_html=True)
            
            for task in completed_tasks:
                task_id = task[0]
                task_description = task[1]
                due_date = format_timestamp(task[2])
                created_at = format_timestamp(task[4])
                
                st.markdown(f'''
                <div class="task-item completed">
                    <strong>Due: {due_date}</strong>
                    <p>{task_description}</p>
                    <div style="text-align: right; color: #777; font-size: 0.8rem;">
                        Created: {created_at}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
