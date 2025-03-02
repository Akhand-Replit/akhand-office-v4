from sqlalchemy import text
import datetime

class TaskModel:
    """Task data operations with branch and employee assignment support"""
    
    @staticmethod
    def create_task(conn, company_id, task_description, due_date, branch_id=None, employee_id=None):
        """Create a new task with branch or employee assignment.
        
        Args:
            conn: Database connection
            company_id: ID of the company creating the task
            task_description: Description of the task
            due_date: Due date for the task
            branch_id: Optional branch ID for branch-level assignment
            employee_id: Optional employee ID for direct assignment
            
        Returns:
            int: ID of the created task
        """
        with conn.begin():
            # Insert task record
            result = conn.execute(text('''
            INSERT INTO tasks (company_id, branch_id, employee_id, task_description, due_date, is_completed)
            VALUES (:company_id, :branch_id, :employee_id, :task_description, :due_date, FALSE)
            RETURNING id
            '''), {
                'company_id': company_id,
                'branch_id': branch_id,
                'employee_id': employee_id,
                'task_description': task_description,
                'due_date': due_date
            })
            
            task_id = result.fetchone()[0]
            
            # If assigned to a branch, create assignments for all branch employees
            if branch_id and not employee_id:
                # Get all active employees in the branch
                employees = conn.execute(text('''
                SELECT id FROM employees
                WHERE branch_id = :branch_id AND is_active = TRUE
                '''), {'branch_id': branch_id}).fetchall()
                
                # Create task assignments for each employee
                for emp in employees:
                    conn.execute(text('''
                    INSERT INTO task_assignments (task_id, employee_id, is_completed)
                    VALUES (:task_id, :employee_id, FALSE)
                    '''), {
                        'task_id': task_id,
                        'employee_id': emp[0]
                    })
            
            return task_id
    
    @staticmethod
    def get_tasks_for_company(conn, company_id, status_filter=None):
        """Get all tasks for a company with optional status filter.
        
        Args:
            conn: Database connection
            company_id: ID of the company
            status_filter: Optional status filter ('All', 'Pending', 'Completed')
            
        Returns:
            List of tasks with branch and employee info
        """
        query = '''
        SELECT t.id, t.task_description, t.due_date, t.is_completed, 
               t.completed_at, t.created_at, t.branch_id, t.employee_id,
               CASE 
                   WHEN t.branch_id IS NOT NULL THEN b.branch_name 
                   WHEN t.employee_id IS NOT NULL THEN e.full_name
                   ELSE 'Unassigned'
               END as assignee_name,
               CASE
                   WHEN t.branch_id IS NOT NULL THEN 'branch'
                   WHEN t.employee_id IS NOT NULL THEN 'employee'
                   ELSE 'unassigned'
               END as assignee_type,
               ce.full_name as completed_by_name
        FROM tasks t
        LEFT JOIN branches b ON t.branch_id = b.id
        LEFT JOIN employees e ON t.employee_id = e.id
        LEFT JOIN employees ce ON t.completed_by_id = ce.id
        WHERE t.company_id = :company_id
        '''
        
        params = {'company_id': company_id}
        
        if status_filter == "Pending":
            query += ' AND t.is_completed = FALSE'
        elif status_filter == "Completed":
            query += ' AND t.is_completed = TRUE'
        
        query += ' ORDER BY t.due_date ASC NULLS LAST, t.created_at DESC'
        
        result = conn.execute(text(query), params)
        return result.fetchall()
    
    @staticmethod
    def get_branch_task_progress(conn, task_id):
        """Get progress of a branch-level task.
        
        Args:
            conn: Database connection
            task_id: ID of the task
            
        Returns:
            Dict with total, completed counts and employee completion status
        """
        # Get task information
        task_info = conn.execute(text('''
        SELECT branch_id FROM tasks WHERE id = :task_id
        '''), {'task_id': task_id}).fetchone()
        
        if not task_info or not task_info[0]:
            return None  # Not a branch task
        
        # Get completion counts
        counts = conn.execute(text('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) as completed
        FROM task_assignments
        WHERE task_id = :task_id
        '''), {'task_id': task_id}).fetchone()
        
        # Get individual employee statuses
        employee_statuses = conn.execute(text('''
        SELECT ta.employee_id, e.full_name, ta.is_completed, r.role_name, r.role_level,
               ta.completed_at
        FROM task_assignments ta
        JOIN employees e ON ta.employee_id = e.id
        JOIN employee_roles r ON e.role_id = r.id
        WHERE ta.task_id = :task_id
        ORDER BY r.role_level, e.full_name
        '''), {'task_id': task_id}).fetchall()
        
        return {
            'total': counts[0],
            'completed': counts[1],
            'employee_statuses': employee_statuses
        }
    
    @staticmethod
    def mark_task_completed(conn, task_id, employee_id):
        """Mark a task as completed by an employee.
        
        For branch tasks, this marks the employee's assignment as completed.
        For individual tasks, this marks the entire task as completed.
        
        Args:
            conn: Database connection
            task_id: ID of the task
            employee_id: ID of the employee completing the task
            
        Returns:
            bool: True if entire task is now complete, False otherwise
        """
        now = datetime.datetime.now()
        
        with conn.begin():
            # Get task information
            task = conn.execute(text('''
            SELECT branch_id, employee_id, is_completed 
            FROM tasks 
            WHERE id = :task_id
            '''), {'task_id': task_id}).fetchone()
            
            if not task:
                return False
            
            # If already completed, do nothing
            if task[2]:
                return True
            
            # If branch task, update the employee's assignment
            if task[0]:  # branch_id is not None
                # Update the assignment
                conn.execute(text('''
                UPDATE task_assignments
                SET is_completed = TRUE, completed_at = :now
                WHERE task_id = :task_id AND employee_id = :employee_id
                '''), {
                    'task_id': task_id,
                    'employee_id': employee_id,
                    'now': now
                })
                
                # Check employee role level
                employee_role = conn.execute(text('''
                SELECT r.role_level 
                FROM employees e
                JOIN employee_roles r ON e.role_id = r.id
                WHERE e.id = :employee_id
                '''), {'employee_id': employee_id}).fetchone()
                
                is_manager = employee_role and employee_role[0] <= 2  # Manager or Asst. Manager
                
                # If employee is a manager or assistant manager, complete the entire task
                if is_manager:
                    conn.execute(text('''
                    UPDATE tasks
                    SET is_completed = TRUE, completed_at = :now, completed_by_id = :employee_id
                    WHERE id = :task_id
                    '''), {
                        'task_id': task_id,
                        'employee_id': employee_id,
                        'now': now
                    })
                    return True
                
                # Otherwise, check if all assignments are complete
                all_complete = conn.execute(text('''
                SELECT COUNT(*) = 0
                FROM task_assignments
                WHERE task_id = :task_id AND is_completed = FALSE
                '''), {'task_id': task_id}).fetchone()[0]
                
                if all_complete:
                    conn.execute(text('''
                    UPDATE tasks
                    SET is_completed = TRUE, completed_at = :now, completed_by_id = :employee_id
                    WHERE id = :task_id
                    '''), {
                        'task_id': task_id,
                        'employee_id': employee_id,
                        'now': now
                    })
                    return True
                
                return False
                
            # If direct employee task, complete it
            elif task[1] == employee_id:  # task assigned directly to this employee
                conn.execute(text('''
                UPDATE tasks
                SET is_completed = TRUE, completed_at = :now, completed_by_id = :employee_id
                WHERE id = :task_id
                '''), {
                    'task_id': task_id,
                    'employee_id': employee_id,
                    'now': now
                })
                return True
            
            return False
    
    @staticmethod
    def get_tasks_for_employee(conn, employee_id, status_filter=None):
        """Get tasks assigned to an employee.
        
        Includes both direct tasks and branch-level tasks.
        
        Args:
            conn: Database connection
            employee_id: ID of the employee
            status_filter: Optional status filter ('All', 'Pending', 'Completed')
            
        Returns:
            List of tasks with type and completion status
        """
        # Get employee's branch
        emp_info = conn.execute(text('''
        SELECT branch_id FROM employees WHERE id = :employee_id
        '''), {'employee_id': employee_id}).fetchone()
        
        if not emp_info:
            return []
        
        branch_id = emp_info[0]
        
        # Get directly assigned tasks
        direct_query = '''
        SELECT t.id, t.task_description, t.due_date, t.is_completed, 
               t.completed_at, t.created_at, 'direct' as task_type,
               NULL as assignment_id, t.is_completed as assignment_completed
        FROM tasks t
        WHERE t.employee_id = :employee_id
        '''
        
        if status_filter == "Pending":
            direct_query += ' AND t.is_completed = FALSE'
        elif status_filter == "Completed":
            direct_query += ' AND t.is_completed = TRUE'
        
        # Get branch-level tasks
        branch_query = '''
        SELECT t.id, t.task_description, t.due_date, t.is_completed, 
               t.completed_at, t.created_at, 'branch' as task_type,
               ta.id as assignment_id, ta.is_completed as assignment_completed
        FROM tasks t
        JOIN task_assignments ta ON t.id = ta.task_id
        WHERE t.branch_id = :branch_id AND ta.employee_id = :employee_id
        '''
        
        if status_filter == "Pending":
            branch_query += ' AND ta.is_completed = FALSE'
        elif status_filter == "Completed":
            branch_query += ' AND ta.is_completed = TRUE'
        
        # Combine queries
        query = f'''
        {direct_query}
        UNION ALL
        {branch_query}
        ORDER BY due_date ASC NULLS LAST, created_at DESC
        '''
        
        result = conn.execute(text(query), {
            'employee_id': employee_id,
            'branch_id': branch_id
        })
        
        return result.fetchall()
    
    @staticmethod
    def reopen_task(conn, task_id):
        """Reopen a completed task.
        
        Args:
            conn: Database connection
            task_id: ID of the task
        """
        with conn.begin():
            # First reopen the main task
            conn.execute(text('''
            UPDATE tasks
            SET is_completed = FALSE, completed_at = NULL, completed_by_id = NULL
            WHERE id = :task_id
            '''), {'task_id': task_id})
            
            # Then reopen all assignments
            conn.execute(text('''
            UPDATE task_assignments
            SET is_completed = FALSE, completed_at = NULL
            WHERE task_id = :task_id
            '''), {'task_id': task_id})
    
    @staticmethod
    def delete_task(conn, task_id):
        """Delete a task and all its assignments.
        
        Args:
            conn: Database connection
            task_id: ID of the task
        """
        with conn.begin():
            # First delete all assignments
            conn.execute(text('''
            DELETE FROM task_assignments
            WHERE task_id = :task_id
            '''), {'task_id': task_id})
            
            # Then delete the task
            conn.execute(text('''
            DELETE FROM tasks
            WHERE id = :task_id
            '''), {'task_id': task_id})
            
    @staticmethod
    def add_task(conn, employee_id, task_description, due_date):
        """Add a new task directly assigned to an employee.
        
        This method is kept for backward compatibility.
        
        Args:
            conn: Database connection
            employee_id: ID of the employee
            task_description: Description of the task
            due_date: Due date for the task
        """
        conn.execute(text('''
        INSERT INTO tasks (employee_id, task_description, due_date, is_completed)
        VALUES (:employee_id, :task_description, :due_date, FALSE)
        '''), {
            'employee_id': employee_id,
            'task_description': task_description,
            'due_date': due_date
        })
        conn.commit()
    
    @staticmethod
    def update_task_status(conn, task_id, is_completed):
        """Update task completion status.
        
        This method is kept for backward compatibility.
        
        Args:
            conn: Database connection
            task_id: ID of the task
            is_completed: New completion status
        """
        conn.execute(text('UPDATE tasks SET is_completed = :is_completed WHERE id = :id'), 
                    {'id': task_id, 'is_completed': is_completed})
        conn.commit()
    
    @staticmethod
    def get_all_tasks(conn, employee_name=None, status_filter=None):
        """Get all tasks with optional employee and status filters.
        
        This method is kept for backward compatibility.
        
        Args:
            conn: Database connection
            employee_name: Optional employee name filter
            status_filter: Optional status filter ('Pending', 'Completed')
            
        Returns:
            List of tasks with employee info
        """
        query = '''
        SELECT t.id, e.full_name, t.task_description, t.due_date, t.is_completed, t.created_at, e.id as employee_id
        FROM tasks t
        JOIN employees e ON t.employee_id = e.id
        WHERE 1=1
        '''
        
        params = {}
        
        if employee_name and employee_name != "All Employees":
            query += ' AND e.full_name = :employee_name'
            params['employee_name'] = employee_name
        
        if status_filter == "Pending":
            query += ' AND t.is_completed = FALSE'
        elif status_filter == "Completed":
            query += ' AND t.is_completed = TRUE'
        
        query += ' ORDER BY t.due_date ASC NULLS LAST, t.created_at DESC'
        
        result = conn.execute(text(query), params)
        return result.fetchall()