from sqlalchemy import text

class BranchModel:
    """Branch data operations"""
    
    @staticmethod
    def get_all_branches(conn):
        """Get all branches with company information."""
        result = conn.execute(text('''
        SELECT b.id, b.branch_name, b.location, b.branch_head, b.is_active, 
               c.company_name, c.id as company_id, b.is_main_branch,
               p.branch_name as parent_branch_name, p.id as parent_branch_id
        FROM branches b
        JOIN companies c ON b.company_id = c.id
        LEFT JOIN branches p ON b.parent_branch_id = p.id
        ORDER BY c.company_name, b.is_main_branch DESC, b.branch_name
        '''))
        return result.fetchall()
    
    @staticmethod
    def get_company_branches(conn, company_id):
        """Get all branches for a specific company."""
        result = conn.execute(text('''
        SELECT b.id, b.branch_name, b.location, b.branch_head, b.is_active,
               b.is_main_branch, b.parent_branch_id,
               p.branch_name as parent_branch_name
        FROM branches b
        LEFT JOIN branches p ON b.parent_branch_id = p.id
        WHERE b.company_id = :company_id
        ORDER BY b.is_main_branch DESC, b.branch_name
        '''), {'company_id': company_id})
        return result.fetchall()
    
    @staticmethod
    def get_branch_by_id(conn, branch_id):
        """Get branch details by ID."""
        result = conn.execute(text('''
        SELECT b.id, b.branch_name, b.location, b.branch_head, b.is_active,
               b.is_main_branch, b.parent_branch_id, b.company_id,
               p.branch_name as parent_branch_name
        FROM branches b
        LEFT JOIN branches p ON b.parent_branch_id = p.id
        WHERE b.id = :branch_id
        '''), {'branch_id': branch_id})
        return result.fetchone()
    
    @staticmethod
    def get_parent_branches(conn, company_id, exclude_branch_id=None):
        """Get all possible parent branches for a company (for creating sub-branches)."""
        query = '''
        SELECT id, branch_name 
        FROM branches
        WHERE company_id = :company_id AND is_active = TRUE
        '''
        
        params = {'company_id': company_id}
        
        if exclude_branch_id:
            query += ' AND id != :exclude_branch_id'
            params['exclude_branch_id'] = exclude_branch_id
        
        query += ' ORDER BY is_main_branch DESC, branch_name'
        
        result = conn.execute(text(query), params)
        return result.fetchall()
    
    @staticmethod
    def get_active_branches(conn, company_id=None):
        """Get all active branches, optionally filtered by company."""
        query = '''
        SELECT b.id, b.branch_name, c.company_name
        FROM branches b
        JOIN companies c ON b.company_id = c.id
        WHERE b.is_active = TRUE AND c.is_active = TRUE
        '''
        
        params = {}
        if company_id:
            query += ' AND b.company_id = :company_id'
            params = {'company_id': company_id}
        
        query += ' ORDER BY c.company_name, b.is_main_branch DESC, b.branch_name'
        
        result = conn.execute(text(query), params)
        return result.fetchall()
    
    @staticmethod
    def create_main_branch(conn, company_id, branch_name, location, branch_head):
        """Create a main branch for a company."""
        conn.execute(text('''
        INSERT INTO branches (company_id, branch_name, location, branch_head, is_main_branch, parent_branch_id, is_active)
        VALUES (:company_id, :branch_name, :location, :branch_head, TRUE, NULL, TRUE)
        '''), {
            'company_id': company_id,
            'branch_name': branch_name,
            'location': location,
            'branch_head': branch_head
        })
        conn.commit()
    
    @staticmethod
    def create_sub_branch(conn, company_id, parent_branch_id, branch_name, location, branch_head):
        """Create a sub-branch under a parent branch."""
        conn.execute(text('''
        INSERT INTO branches (company_id, parent_branch_id, branch_name, location, branch_head, is_main_branch, is_active)
        VALUES (:company_id, :parent_branch_id, :branch_name, :location, :branch_head, FALSE, TRUE)
        '''), {
            'company_id': company_id,
            'parent_branch_id': parent_branch_id,
            'branch_name': branch_name,
            'location': location,
            'branch_head': branch_head
        })
        conn.commit()
    
    @staticmethod
    def update_branch(conn, branch_id, branch_name, location, branch_head, parent_branch_id=None):
        """Update branch details."""
        query = '''
        UPDATE branches 
        SET branch_name = :branch_name, location = :location, branch_head = :branch_head
        '''
        
        params = {
            'branch_id': branch_id,
            'branch_name': branch_name,
            'location': location,
            'branch_head': branch_head
        }
        
        # Only update parent_branch_id if provided and branch is not a main branch
        if parent_branch_id is not None:
            result = conn.execute(text('SELECT is_main_branch FROM branches WHERE id = :branch_id'), 
                                 {'branch_id': branch_id})
            is_main_branch = result.fetchone()[0]
            
            if not is_main_branch:
                query += ', parent_branch_id = :parent_branch_id'
                params['parent_branch_id'] = parent_branch_id
        
        query += ' WHERE id = :branch_id'
        
        conn.execute(text(query), params)
        conn.commit()
    
    @staticmethod
    def update_branch_status(conn, branch_id, is_active):
        """Update branch active status and update related employees status too."""
        with conn.begin():
            # Update branch status
            conn.execute(text('''
            UPDATE branches 
            SET is_active = :is_active
            WHERE id = :branch_id
            '''), {'branch_id': branch_id, 'is_active': is_active})
            
            # Update employees in this branch
            conn.execute(text('''
            UPDATE employees 
            SET is_active = :is_active
            WHERE branch_id = :branch_id
            '''), {'branch_id': branch_id, 'is_active': is_active})
        
    @staticmethod
    def get_branch_employees(conn, branch_id):
        """Get all employees for a specific branch."""
        result = conn.execute(text('''
        SELECT e.id, e.username, e.full_name, e.profile_pic_url, e.is_active, r.role_name, r.role_level
        FROM employees e
        JOIN employee_roles r ON e.role_id = r.id
        WHERE e.branch_id = :branch_id
        ORDER BY r.role_level, e.full_name
        '''), {'branch_id': branch_id})
        return result.fetchall()
    
    @staticmethod
    def get_employee_count_by_branch(conn, company_id):
        """Get employee count for each branch of a company."""
        result = conn.execute(text('''
        SELECT b.id, b.branch_name, COUNT(e.id) as employee_count
        FROM branches b
        LEFT JOIN employees e ON b.id = e.branch_id AND e.is_active = TRUE
        WHERE b.company_id = :company_id
        GROUP BY b.id, b.branch_name
        ORDER BY b.is_main_branch DESC, b.branch_name
        '''), {'company_id': company_id})
        return result.fetchall()
    
    @staticmethod
    def get_subbranches(conn, parent_branch_id):
        """Get all sub-branches of a branch."""
        result = conn.execute(text('''
        SELECT id, branch_name, is_active
        FROM branches
        WHERE parent_branch_id = :parent_branch_id
        ORDER BY branch_name
        '''), {'parent_branch_id': parent_branch_id})
        return result.fetchall()