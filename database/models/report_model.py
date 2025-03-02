from sqlalchemy import text

class ReportModel:
    """Daily report data operations with advanced filtering"""
    
    @staticmethod
    def get_employee_reports(conn, employee_id, start_date, end_date):
        """Get reports for a specific employee within a date range.
        
        Args:
            conn: Database connection
            employee_id: ID of the employee
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            List of reports
        """
        result = conn.execute(text('''
        SELECT id, report_date, report_text
        FROM daily_reports
        WHERE employee_id = :employee_id
        AND report_date BETWEEN :start_date AND :end_date
        ORDER BY report_date DESC
        '''), {'employee_id': employee_id, 'start_date': start_date, 'end_date': end_date})
        return result.fetchall()
    
    @staticmethod
    def get_branch_reports(conn, branch_id, start_date, end_date, role_id=None):
        """Get reports for all employees in a branch within a date range.
        
        Args:
            conn: Database connection
            branch_id: ID of the branch
            start_date: Start date for filtering
            end_date: End date for filtering
            role_id: Optional role ID for filtering
            
        Returns:
            List of reports with employee info
        """
        query = '''
        SELECT dr.id, e.full_name, r.role_name, dr.report_date, dr.report_text, dr.created_at
        FROM daily_reports dr
        JOIN employees e ON dr.employee_id = e.id
        JOIN employee_roles r ON e.role_id = r.id
        WHERE e.branch_id = :branch_id
        AND dr.report_date BETWEEN :start_date AND :end_date
        '''
        
        params = {
            'branch_id': branch_id, 
            'start_date': start_date, 
            'end_date': end_date
        }
        
        if role_id:
            query += ' AND e.role_id = :role_id'
            params['role_id'] = role_id
        
        query += ' ORDER BY dr.report_date DESC, r.role_level, e.full_name'
        
        result = conn.execute(text(query), params)
        return result.fetchall()
    
    @staticmethod
    def get_company_reports(conn, company_id, start_date, end_date, branch_id=None, role_id=None):
        """Get reports for all employees in a company within a date range.
        
        Args:
            conn: Database connection
            company_id: ID of the company
            start_date: Start date for filtering
            end_date: End date for filtering
            branch_id: Optional branch ID for filtering
            role_id: Optional role ID for filtering
            
        Returns:
            List of reports with employee and branch info
        """
        query = '''
        SELECT dr.id, e.full_name, r.role_name, b.branch_name, dr.report_date, dr.report_text, dr.created_at
        FROM daily_reports dr
        JOIN employees e ON dr.employee_id = e.id
        JOIN branches b ON e.branch_id = b.id
        JOIN employee_roles r ON e.role_id = r.id
        WHERE b.company_id = :company_id
        AND dr.report_date BETWEEN :start_date AND :end_date
        '''
        
        params = {
            'company_id': company_id, 
            'start_date': start_date, 
            'end_date': end_date
        }
        
        if branch_id:
            query += ' AND e.branch_id = :branch_id'
            params['branch_id'] = branch_id
        
        if role_id:
            query += ' AND e.role_id = :role_id'
            params['role_id'] = role_id
        
        query += ' ORDER BY dr.report_date DESC, b.branch_name, r.role_level, e.full_name'
        
        result = conn.execute(text(query), params)
        return result.fetchall()
    
    @staticmethod
    def get_all_reports(conn, start_date, end_date, employee_name=None):
        """Get all reports with optional employee filter.
        
        Args:
            conn: Database connection
            start_date: Start date for filtering
            end_date: End date for filtering
            employee_name: Optional employee name filter
            
        Returns:
            List of reports with employee info
        """
        query = '''
        SELECT e.full_name, dr.report_date, dr.report_text, dr.id, e.id as employee_id
        FROM daily_reports dr
        JOIN employees e ON dr.employee_id = e.id
        WHERE dr.report_date BETWEEN :start_date AND :end_date
        '''
        
        params = {'start_date': start_date, 'end_date': end_date}
        
        if employee_name and employee_name != "All Employees":
            query += ' AND e.full_name = :employee_name'
            params['employee_name'] = employee_name
        
        query += ' ORDER BY dr.report_date DESC, e.full_name'
        
        result = conn.execute(text(query), params)
        return result.fetchall()
    
    @staticmethod
    def add_report(conn, employee_id, report_date, report_text):
        """Add a new report.
        
        Args:
            conn: Database connection
            employee_id: ID of the employee
            report_date: Date of the report
            report_text: Content of the report
        """
        conn.execute(text('''
        INSERT INTO daily_reports (employee_id, report_date, report_text)
        VALUES (:employee_id, :report_date, :report_text)
        '''), {
            'employee_id': employee_id,
            'report_date': report_date,
            'report_text': report_text
        })
        conn.commit()
    
    @staticmethod
    def update_report(conn, report_id, report_date, report_text):
        """Update an existing report.
        
        Args:
            conn: Database connection
            report_id: ID of the report
            report_date: New date for the report
            report_text: New content for the report
        """
        conn.execute(text('''
        UPDATE daily_reports 
        SET report_text = :report_text, report_date = :report_date, created_at = CURRENT_TIMESTAMP
        WHERE id = :id
        '''), {
            'report_text': report_text,
            'report_date': report_date,
            'id': report_id
        })
        conn.commit()
    
    @staticmethod
    def check_report_exists(conn, employee_id, report_date):
        """Check if a report already exists for the given date.
        
        Args:
            conn: Database connection
            employee_id: ID of the employee
            report_date: Date to check
            
        Returns:
            Report ID if exists, None otherwise
        """
        result = conn.execute(text('''
        SELECT id FROM daily_reports 
        WHERE employee_id = :employee_id AND report_date = :report_date
        '''), {'employee_id': employee_id, 'report_date': report_date})
        return result.fetchone()
    
    @staticmethod
    def generate_report_pdf(reports, report_type="employee"):
        """Generate PDF content for reports.
        
        Args:
            reports: List of report data
            report_type: Type of report ("employee", "branch", "company")
            
        Returns:
            PDF content as bytes
        """
        # PDF generation would be implemented in the PDF utility module
        # This method is just a placeholder for the interface
        pass