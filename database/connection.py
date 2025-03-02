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
    with engine.connect() as conn:
        conn.execute(text('''
        -- Companies table
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            company_name VARCHAR(100) UNIQUE NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            profile_pic_url TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Branches table (with parent branch support)
        CREATE TABLE IF NOT EXISTS branches (
            id SERIAL PRIMARY KEY,
            company_id INTEGER REFERENCES companies(id),
            parent_branch_id INTEGER REFERENCES branches(id),
            branch_name VARCHAR(100) NOT NULL,
            is_main_branch BOOLEAN DEFAULT FALSE,
            location VARCHAR(255),
            branch_head VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company_id, branch_name)
        );
        
        -- Employee Roles table
        CREATE TABLE IF NOT EXISTS employee_roles (
            id SERIAL PRIMARY KEY,
            role_name VARCHAR(50) NOT NULL,
            role_level INTEGER NOT NULL,
            company_id INTEGER REFERENCES companies(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company_id, role_name)
        );
        
        -- Messages table
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            sender_type VARCHAR(20) NOT NULL, -- 'admin' or 'company'
            sender_id INTEGER NOT NULL,
            receiver_type VARCHAR(20) NOT NULL, -- 'admin' or 'company'
            receiver_id INTEGER NOT NULL,
            message_text TEXT NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Employees table (now with roles)
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
        );
        
        -- Tasks table (updated for branch assignment)
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            company_id INTEGER REFERENCES companies(id),
            branch_id INTEGER REFERENCES branches(id),
            employee_id INTEGER REFERENCES employees(id),
            task_description TEXT NOT NULL,
            due_date DATE,
            is_completed BOOLEAN DEFAULT FALSE,
            completed_by_id INTEGER REFERENCES employees(id),
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Task Assignments for tracking branch-level task completions
        CREATE TABLE IF NOT EXISTS task_assignments (
            id SERIAL PRIMARY KEY,
            task_id INTEGER REFERENCES tasks(id),
            employee_id INTEGER REFERENCES employees(id),
            is_completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(task_id, employee_id)
        );
        
        -- Daily reports table (unchanged)
        CREATE TABLE IF NOT EXISTS daily_reports (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER REFERENCES employees(id),
            report_date DATE NOT NULL,
            report_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Insert default employee roles if they don't exist
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
        
        -- Set existing employees to General Employee role by default
        UPDATE employees e
        SET role_id = r.id
        FROM employee_roles r
        JOIN branches b ON r.company_id = b.company_id
        WHERE e.branch_id = b.id AND r.role_name = 'General Employee' AND e.role_id IS NULL;
        '''))
        conn.commit()