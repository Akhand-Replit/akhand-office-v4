from sqlalchemy import text

class EmployeeModel:
    """Employee data operations"""
    
    @staticmethod
    def get_all_employees(conn, company_id=None):
        """Get all employees with optional company filter.
        
        Args:
            conn: Database connection
            company_id: Optional company ID filter
            
        Returns:
            List of employees with branch and role info
        """
        query = '''
        SELECT e.id, e.username, e.full_name, e.profile_pic_url, e.is_active,
               b.branch_name, c.company_name, r.role_name, r.role_level, b.id as branch_id
        FROM employees e
        JOIN branches b ON e.branch_id = b.id
        JOIN companies c ON b.company_id = c.id
        JOIN employee_roles r ON e.role_id = r.id
        '''
        
        params = {}
        if company_id:
            query += ' WHERE b.company_id = :company_id'
            params = {'company_id': company_id}
        
        query += ' ORDER BY c.company_name, b.branch_name, r.role_level, e.full_name'
        
        result = conn.execute(text(query), params)
        return result.fetchall()
    
    @staticmethod
    def get_branch_employees(conn, branch_id):
        """Get all employees for a specific branch.
        
        Args:
            conn: Database connection
            branch_id: ID of the branch
            
        Returns:
            List of employees with role info
        """
        result = conn.execute(text('''
        SELECT e.id, e.username, e.full_name, e.profile_pic_url, e.is_active, 
               r.role_name, r.role_level, r.id as role_id
        FROM employees e
        JOIN employee_roles r ON e.role_id = r.id
        WHERE e.branch_id = :branch_id
        ORDER BY r.role_level, e.full_name
        '''), {'branch_id': branch_id})
        return result.fetchall()
    
    @staticmethod
    def get_active_employees(conn, company_id=None, branch_id=None, role_level=None):
        """Get active employees with optional filters.
        
        Args:
            conn: Database connection
            company_id: Optional company ID filter
            branch_id: Optional branch ID filter
            role_level: Optional role level filter
            
        Returns:
            List of active employees
        """
        query = '''
        SELECT e.id, e.full_name, b.branch_name, c.company_name, r.role_name
        FROM employees e
        JOIN branches b ON e.branch_id = b.id
        JOIN companies c ON b.company_id = c.id
        JOIN employee_roles r ON e.role_id = r.id
        WHERE e.is_active = TRUE 
          AND b.is_active = TRUE
          AND c.is_active = TRUE
        '''
        
        params = {}
        
        if company_id:
            query += ' AND c.id = :company_id'
            params['company_id'] = company_id
        
        if branch_id:
            query += ' AND b.id = :branch_id'
            params['branch_id'] = branch_id
        
        if role_level:
            query += ' AND r.role_level = :role_level'
            params['role_level'] = role_level
        
        query += ' ORDER BY b.branch_name, r.role_level, e.full_name'
        
        result = conn.execute(text(query), params)
        return result.fetchall()
    
    @staticmethod
    def get_employee_by_id(conn, employee_id):
        """Get detailed employee data by ID.
        
        Args:
            conn: Database connection
            employee_id: ID of the employee
            
        Returns:
            Employee details including branch and role info
        """
        result = conn.execute(text('''
        SELECT e.id, e.username, e.full_name, e.profile_pic_url, e.is_active,
               b.id as branch_id, b.branch_name, r.id as role_id, r.role_name, 
               c.id as company_id
        FROM employees e
        JOIN branches b ON e.branch_id = b.id
        JOIN employee_roles r ON e.role_id = r.id
        JOIN companies c ON b.company_id = c.id
        WHERE e.id = :employee_id
        '''), {'employee_id': employee_id})
        return result.fetchone()
    
    @staticmethod
    def add_employee(conn, branch_id, role_id, username, password, full_name, profile_pic_url):
        """Add a new employee.
        
        Args:
            conn: Database connection
            branch_id: ID of the branch
            role_id: ID of the role
            username: Username for login
            password: Password for login
            full_name: Full name of employee
            profile_pic_url: URL to profile picture
        """
        default_pic = "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"
        
        conn.execute(text('''
        INSERT INTO employees (branch_id, role_id, username, password, full_name, profile_pic_url, is_active)
        VALUES (:branch_id, :role_id, :username, :password, :full_name, :profile_pic_url, TRUE)
        '''), {
            'branch_id': branch_id,
            'role_id': role_id,
            'username': username,
            'password': password,
            'full_name': full_name,
            'profile_pic_url': profile_pic_url if profile_pic_url else default_pic
        })
        conn.commit()
    
    @staticmethod
    def update_employee_status(conn, employee_id, is_active):
        """Activate or deactivate an employee.
        
        Args:
            conn: Database connection
            employee_id: ID of the employee
            is_active: New active status
        """
        conn.execute(text('UPDATE employees SET is_active = :is_active WHERE id = :id'), 
                    {'id': employee_id, 'is_active': is_active})
        conn.commit()
    
    @staticmethod
    def update_employee_role(conn, employee_id, role_id):
        """Update employee's role.
        
        Args:
            conn: Database connection
            employee_id: ID of the employee
            role_id: New role ID
        """
        conn.execute(text('''
        UPDATE employees
        SET role_id = :role_id
        WHERE id = :employee_id
        '''), {
            'employee_id': employee_id,
            'role_id': role_id
        })
        conn.commit()
    
    @staticmethod
    def update_employee_branch(conn, employee_id, branch_id):
        """Transfer employee to different branch.
        
        Args:
            conn: Database connection
            employee_id: ID of the employee
            branch_id: New branch ID
        """
        conn.execute(text('''
        UPDATE employees
        SET branch_id = :branch_id
        WHERE id = :employee_id
        '''), {
            'employee_id': employee_id,
            'branch_id': branch_id
        })
        conn.commit()
    
    @staticmethod
    def reset_password(conn, employee_id, new_password):
        """Reset an employee's password.
        
        Args:
            conn: Database connection
            employee_id: ID of the employee
            new_password: New password
        """
        conn.execute(text('UPDATE employees SET password = :password WHERE id = :id'), 
                    {'id': employee_id, 'password': new_password})
        conn.commit()
    
    @staticmethod
    def update_profile(conn, employee_id, full_name, profile_pic_url):
        """Update employee profile information.
        
        Args:
            conn: Database connection
            employee_id: ID of the employee
            full_name: New full name
            profile_pic_url: New profile picture URL
        """
        conn.execute(text('''
        UPDATE employees
        SET full_name = :full_name, profile_pic_url = :profile_pic_url
        WHERE id = :employee_id
        '''), {
            'full_name': full_name,
            'profile_pic_url': profile_pic_url,
            'employee_id': employee_id
        })
        conn.commit()
    
    @staticmethod
    def verify_password(conn, employee_id, current_password):
        """Verify employee's current password.
        
        Args:
            conn: Database connection
            employee_id: ID of the employee
            current_password: Password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        result = conn.execute(text('''
        SELECT COUNT(*)
        FROM employees
        WHERE id = :employee_id AND password = :current_password
        '''), {'employee_id': employee_id, 'current_password': current_password})
        return result.fetchone()[0] > 0