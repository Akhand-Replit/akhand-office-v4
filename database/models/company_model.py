from sqlalchemy import text

class CompanyModel:
    """Company data operations"""
    
    @staticmethod
    def get_all_companies(conn):
        """Get all companies from the database."""
        result = conn.execute(text('''
        SELECT id, company_name, username, profile_pic_url, is_active, created_at 
        FROM companies
        ORDER BY company_name
        '''))
        return result.fetchall()
    
    @staticmethod
    def get_active_companies(conn):
        """Get all active companies."""
        result = conn.execute(text('''
        SELECT id, company_name FROM companies 
        WHERE is_active = TRUE
        ORDER BY company_name
        '''))
        return result.fetchall()
    
    @staticmethod
    def get_company_by_id(conn, company_id):
        """Get company data by ID."""
        result = conn.execute(text('''
        SELECT company_name, username, profile_pic_url, is_active
        FROM companies
        WHERE id = :company_id
        '''), {'company_id': company_id})
        return result.fetchone()
    
    @staticmethod
    def add_company(conn, company_name, username, password, profile_pic_url):
        """Add a new company to the database."""
        default_pic = "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"
        
        conn.execute(text('''
        INSERT INTO companies (company_name, username, password, profile_pic_url, is_active)
        VALUES (:company_name, :username, :password, :profile_pic_url, TRUE)
        '''), {
            'company_name': company_name,
            'username': username,
            'password': password,
            'profile_pic_url': profile_pic_url if profile_pic_url else default_pic
        })
        conn.commit()
    
    @staticmethod
    def update_company_status(conn, company_id, is_active):
        """Activate or deactivate a company and all its branches and employees."""
        # Update company status
        conn.execute(text('UPDATE companies SET is_active = :is_active WHERE id = :id'), 
                    {'id': company_id, 'is_active': is_active})
        
        # Update all branches for this company
        conn.execute(text('''
        UPDATE branches 
        SET is_active = :is_active 
        WHERE company_id = :company_id
        '''), {'company_id': company_id, 'is_active': is_active})
        
        # Update all employees in all branches of this company
        conn.execute(text('''
        UPDATE employees 
        SET is_active = :is_active 
        WHERE branch_id IN (SELECT id FROM branches WHERE company_id = :company_id)
        '''), {'company_id': company_id, 'is_active': is_active})
        
        conn.commit()
    
    @staticmethod
    def reset_password(conn, company_id, new_password):
        """Reset a company's password."""
        conn.execute(text('UPDATE companies SET password = :password WHERE id = :id'), 
                    {'id': company_id, 'password': new_password})
        conn.commit()
    
    @staticmethod
    def update_profile(conn, company_id, company_name, profile_pic_url):
        """Update company profile information."""
        conn.execute(text('''
        UPDATE companies
        SET company_name = :company_name, profile_pic_url = :profile_pic_url
        WHERE id = :company_id
        '''), {
            'company_name': company_name,
            'profile_pic_url': profile_pic_url,
            'company_id': company_id
        })
        conn.commit()
    
    @staticmethod
    def verify_password(conn, company_id, current_password):
        """Verify company's current password."""
        result = conn.execute(text('''
        SELECT COUNT(*)
        FROM companies
        WHERE id = :company_id AND password = :current_password
        '''), {'company_id': company_id, 'current_password': current_password})
        return result.fetchone()[0] > 0