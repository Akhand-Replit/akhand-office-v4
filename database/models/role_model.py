from sqlalchemy import text

class RoleModel:
    """Employee role data operations"""
    
    @staticmethod
    def get_all_roles(conn, company_id):
        """Get all roles for a company.
        
        Args:
            conn: Database connection
            company_id: ID of the company
            
        Returns:
            List of roles (id, name, level)
        """
        result = conn.execute(text('''
        SELECT id, role_name, role_level
        FROM employee_roles
        WHERE company_id = :company_id
        ORDER BY role_level
        '''), {'company_id': company_id})
        return result.fetchall()
    
    @staticmethod
    def get_role_by_id(conn, role_id):
        """Get role details by ID.
        
        Args:
            conn: Database connection
            role_id: ID of the role
            
        Returns:
            Role details (id, name, level, company_id)
        """
        result = conn.execute(text('''
        SELECT id, role_name, role_level, company_id
        FROM employee_roles
        WHERE id = :role_id
        '''), {'role_id': role_id})
        return result.fetchone()
    
    @staticmethod
    def create_role(conn, company_id, role_name, role_level):
        """Create a new role.
        
        Args:
            conn: Database connection
            company_id: ID of the company
            role_name: Name of the role
            role_level: Level of the role (lower number = higher rank)
        """
        conn.execute(text('''
        INSERT INTO employee_roles (company_id, role_name, role_level)
        VALUES (:company_id, :role_name, :role_level)
        '''), {
            'company_id': company_id,
            'role_name': role_name,
            'role_level': role_level
        })
        conn.commit()
    
    @staticmethod
    def update_role(conn, role_id, role_name, role_level):
        """Update role details.
        
        Args:
            conn: Database connection
            role_id: ID of the role
            role_name: New name for the role
            role_level: New level for the role
        """
        conn.execute(text('''
        UPDATE employee_roles
        SET role_name = :role_name, role_level = :role_level
        WHERE id = :role_id
        '''), {
            'role_id': role_id,
            'role_name': role_name,
            'role_level': role_level
        })
        conn.commit()
    
    @staticmethod
    def delete_role(conn, role_id, replacement_role_id):
        """Delete a role and reassign employees to another role.
        
        Args:
            conn: Database connection
            role_id: ID of the role to delete
            replacement_role_id: ID of the role to assign employees to
        """
        with conn.begin():
            # First reassign all employees with this role
            conn.execute(text('''
            UPDATE employees
            SET role_id = :replacement_role_id
            WHERE role_id = :role_id
            '''), {
                'role_id': role_id,
                'replacement_role_id': replacement_role_id
            })
            
            # Then delete the role
            conn.execute(text('''
            DELETE FROM employee_roles
            WHERE id = :role_id
            '''), {'role_id': role_id})
    
    @staticmethod
    def get_manager_roles(conn, company_id):
        """Get roles that are considered management (Manager and Asst. Manager).
        
        Args:
            conn: Database connection
            company_id: ID of the company
            
        Returns:
            List of management role IDs
        """
        result = conn.execute(text('''
        SELECT id 
        FROM employee_roles
        WHERE company_id = :company_id AND role_level <= 2
        '''), {'company_id': company_id})
        return [row[0] for row in result.fetchall()]
    
    @staticmethod
    def initialize_default_roles(conn, company_id):
        """Initialize default roles for a new company.
        
        Args:
            conn: Database connection
            company_id: ID of the company
        """
        # Check if roles already exist for this company
        result = conn.execute(text('''
        SELECT COUNT(*) FROM employee_roles WHERE company_id = :company_id
        '''), {'company_id': company_id})
        
        if result.fetchone()[0] == 0:
            # Create default roles
            default_roles = [
                ('Manager', 1),
                ('Asst. Manager', 2),
                ('General Employee', 3)
            ]
            
            for role_name, role_level in default_roles:
                conn.execute(text('''
                INSERT INTO employee_roles (company_id, role_name, role_level)
                VALUES (:company_id, :role_name, :role_level)
                '''), {
                    'company_id': company_id,
                    'role_name': role_name,
                    'role_level': role_level
                })
            
            conn.commit()