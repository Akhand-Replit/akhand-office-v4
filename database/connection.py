import streamlit as st
from sqlalchemy import create_engine, text

@st.cache_resource
def init_connection():
    """Initialize database connection with caching.
    
    Returns:
        SQLAlchemy engine or None if connection fails
    """
    try:
        return create_engine(st.secrets["postgres"]["url"])
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def init_db(engine):
    """Initialize database tables if they don't exist.
    
    Args:
        engine: SQLAlchemy database engine
    """
    try:
        with engine.connect() as conn:
            # Create tables one by one with proper error handling
            
            # Companies table
            try:
                conn.execute(text('''
                CREATE TABLE IF NOT EXISTS companies (
                    id SERIAL PRIMARY KEY,
                    company_name VARCHAR(100) UNIQUE NOT NULL,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    profile_pic_url TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                '''))
                conn.commit()
            except Exception as e:
                st.error(f"Error creating companies table: {e}")
                raise
            
            # Branches table - Create first without self-referencing foreign key
            try:
                conn.execute(text('''
                CREATE TABLE IF NOT EXISTS branches (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER REFERENCES companies(id),
                    parent_branch_id INTEGER NULL,
                    branch_name VARCHAR(100) NOT NULL,
                    is_main_branch BOOLEAN DEFAULT FALSE,
                    location VARCHAR(255),
                    branch_head VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, branch_name)
                )
                '''))
                conn.commit()
            except Exception as e:
                st.error(f"Error creating branches table: {e}")
                raise
            
            # Now add the self-referencing foreign key to branches table if it doesn't exist
            try:
                # Check if constraint already exists before adding it
                result = conn.execute(text('''
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'branches_parent_branch_id_fkey'
                '''))
                
                # If constraint doesn't exist, add it
                if not result.fetchone():
                    conn.execute(text('''
                    ALTER TABLE branches 
                    ADD CONSTRAINT branches_parent_branch_id_fkey 
                    FOREIGN KEY (parent_branch_id) 
                    REFERENCES branches(id)
                    '''))
                    conn.commit()
            except Exception as e:
                st.warning(f"Note: Could not add parent branch self-reference constraint: {e}")
                # Continue execution - this is not critical
            
            # Employee Roles table
            try:
                conn.execute(text('''
                CREATE TABLE IF NOT EXISTS employee_roles (
                    id SERIAL PRIMARY KEY,
                    role_name VARCHAR(50) NOT NULL,
                    role_level INTEGER NOT NULL,
                    company_id INTEGER REFERENCES companies(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, role_name)
                )
                '''))
                conn.commit()
            except Exception as e:
                st.error(f"Error creating employee_roles table: {e}")
                raise
            
            # Messages table
            try:
                conn.execute(text('''
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    sender_type VARCHAR(20) NOT NULL,
                    sender_id INTEGER NOT NULL,
                    receiver_type VARCHAR(20) NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    message_text TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                '''))
                conn.commit()
            except Exception as e:
                st.error(f"Error creating messages table: {e}")
                raise
            
            # Employees table
            try:
                conn.execute(text('''
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    branch_id INTEGER REFERENCES branches(id),
                    role_id INTEGER REFERENCES employee_roles(id),
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    profile_pic_url TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                '''))
                conn.commit()
            except Exception as e:
                st.error(f"Error creating employees table: {e}")
                raise
            
            # Tasks table
            try:
                conn.execute(text('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER REFERENCES companies(id),
                    branch_id INTEGER REFERENCES branches(id),
                    employee_id INTEGER REFERENCES employees(id),
                    task_description TEXT NOT NULL,
                    due_date DATE,
                    is_completed BOOLEAN DEFAULT FALSE,
                    completed_by_id INTEGER,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                '''))
                conn.commit()
            except Exception as e:
                st.error(f"Error creating tasks table: {e}")
                raise
            
            # Add foreign key for completed_by_id if it doesn't exist
            try:
                # Check if constraint already exists
                result = conn.execute(text('''
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'tasks_completed_by_id_fkey'
                '''))
                
                # If constraint doesn't exist, add it
                if not result.fetchone():
                    conn.execute(text('''
                    ALTER TABLE tasks 
                    ADD CONSTRAINT tasks_completed_by_id_fkey 
                    FOREIGN KEY (completed_by_id) 
                    REFERENCES employees(id)
                    '''))
                    conn.commit()
            except Exception as e:
                st.warning(f"Note: Could not add completed_by_id constraint to tasks: {e}")
                # Continue execution - this is not critical
            
            # Task Assignments table
            try:
                conn.execute(text('''
                CREATE TABLE IF NOT EXISTS task_assignments (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER REFERENCES tasks(id),
                    employee_id INTEGER REFERENCES employees(id),
                    is_completed BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(task_id, employee_id)
                )
                '''))
                conn.commit()
            except Exception as e:
                st.error(f"Error creating task_assignments table: {e}")
                raise
            
            # Daily reports table
            try:
                conn.execute(text('''
                CREATE TABLE IF NOT EXISTS daily_reports (
                    id SERIAL PRIMARY KEY,
                    employee_id INTEGER REFERENCES employees(id),
                    report_date DATE NOT NULL,
                    report_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                '''))
                conn.commit()
            except Exception as e:
                st.error(f"Error creating daily_reports table: {e}")
                raise
            
            # Initialize default roles for each company
            try:
                conn.execute(text('''
                INSERT INTO employee_roles (role_name, role_level, company_id)
                SELECT 'Manager', 1, id FROM companies
                WHERE NOT EXISTS (
                    SELECT 1 FROM employee_roles WHERE role_name = 'Manager' AND company_id = companies.id
                );
                
                INSERT INTO employee_roles (role_name, role_level, company_id)
                SELECT 'Asst. Manager', 2, id FROM companies
                WHERE NOT EXISTS (
                    SELECT 1 FROM employee_roles WHERE role_name = 'Asst. Manager' AND company_id = companies.id
                );
                
                INSERT INTO employee_roles (role_name, role_level, company_id)
                SELECT 'General Employee', 3, id FROM companies
                WHERE NOT EXISTS (
                    SELECT 1 FROM employee_roles WHERE role_name = 'General Employee' AND company_id = companies.id
                );
                '''))
                conn.commit()
            except Exception as e:
                st.error(f"Error inserting default roles: {e}")
                # Don't raise here, as this is not a critical failure
            
            # Set default role for employees without a role
            try:
                conn.execute(text('''
                UPDATE employees e
                SET role_id = r.id
                FROM employee_roles r
                JOIN branches b ON r.company_id = b.company_id
                WHERE e.branch_id = b.id AND r.role_name = 'General Employee' AND e.role_id IS NULL;
                '''))
                conn.commit()
            except Exception as e:
                st.error(f"Error setting default employee roles: {e}")
                # Don't raise here, as this is not a critical failure
            
            st.success("Database initialized successfully")
            
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        # Let the application continue even if there's an error
