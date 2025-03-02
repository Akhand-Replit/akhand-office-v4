import streamlit as st
import datetime
from database.models.report_model import ReportModel
from database.models.branch_model import BranchModel
from database.models.role_model import RoleModel
from utils.helpers import get_date_range_from_filter
from utils.pdf_generator import (
    create_employee_report_pdf, 
    create_branch_report_pdf, 
    create_company_report_pdf,
    create_role_report_pdf
)

def manage_reports(engine):
    """View and download reports with various filters.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Reports</h2>', unsafe_allow_html=True)
    
    company_id = st.session_state.user["id"]
    company_name = st.session_state.user["full_name"]
    
    tabs = st.tabs(["All Reports", "Branch Reports", "Role Reports", "Employee Reports"])
    
    with tabs[0]:
        view_company_reports(engine, company_id, company_name)
    
    with tabs[1]:
        view_branch_reports(engine, company_id, company_name)
        
    with tabs[2]:
        view_role_reports(engine, company_id, company_name)
        
    with tabs[3]:
        view_employee_reports(engine, company_id)

def view_company_reports(engine, company_id, company_name):
    """View and download reports for the entire company.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
        company_name: Name of the company for display
    """
    st.markdown("### Company-wide Reports")
    
    # Date range filter
    col1, col2 = st.columns(2)
    
    with col1:
        date_options = [
            "This Week",
            "This Month",
            "This Year",
            "All Reports",
            "Custom Range"
        ]
        date_filter = st.selectbox("Date Range", date_options, key="company_reports_date_filter")
    
    with col2:
        # Custom date range if selected
        if date_filter == "Custom Range":
            today = datetime.date.today()
            start_date = st.date_input("Start Date", today - datetime.timedelta(days=30))
            end_date = st.date_input("End Date", today)
        else:
            # Set default dates based on filter
            start_date, end_date = get_date_range_from_filter(date_filter)
    
    # Fetch reports
    with engine.connect() as conn:
        reports = ReportModel.get_company_reports(conn, company_id, start_date, end_date)
    
    if not reports:
        st.info("No reports found for the selected period.")
        return
    
    # Display report stats
    total_reports = len(reports)
    unique_employees = len(set(r[1] for r in reports))  # Unique employee names
    unique_branches = len(set(r[3] for r in reports))  # Unique branch names
    
    st.write(f"Found {total_reports} reports from {unique_employees} employees across {unique_branches} branches.")
    
    # Download button
    if st.button("Download as PDF", key="download_company_reports"):
        pdf = create_company_report_pdf(reports, company_name)
        
        # Format date range for filename
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        st.download_button(
            label="Download PDF",
            data=pdf,
            file_name=f"{company_name}_reports_{start_str}_to_{end_str}.pdf",
            mime="application/pdf"
        )
    
    # Display reports grouped by branch and employee
    reports_by_branch = {}
    for report in reports:
        branch_name = report[3]
        
        if branch_name not in reports_by_branch:
            reports_by_branch[branch_name] = {}
        
        employee_name = report[1]
        if employee_name not in reports_by_branch[branch_name]:
            reports_by_branch[branch_name][employee_name] = []
        
        reports_by_branch[branch_name][employee_name].append(report)
    
    # Display branches
    for branch_name, employees in reports_by_branch.items():
        with st.expander(f"Branch: {branch_name} ({sum(len(reports) for reports in employees.values())} reports)", expanded=False):
            # Display employees in this branch
            for employee_name, emp_reports in employees.items():
                with st.expander(f"{employee_name} ({len(emp_reports)} reports)", expanded=False):
                    # Group by date
                    emp_reports_by_date = {}
                    for report in emp_reports:
                        date = report[4]
                        if date not in emp_reports_by_date:
                            emp_reports_by_date[date] = report
                    
                    # Display each date
                    for date, report in sorted(emp_reports_by_date.items(), key=lambda x: x[0], reverse=True):
                        report_text = report[5]
                        
                        st.markdown(f'''
                        <div class="report-item">
                            <strong>{date.strftime('%A, %d %b %Y')}</strong>
                            <p>{report_text}</p>
                        </div>
                        ''', unsafe_allow_html=True)

def view_branch_reports(engine, company_id, company_name):
    """View and download reports for a specific branch.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
        company_name: Name of the company for display
    """
    st.markdown("### Branch Reports")
    
    # Get active branches
    with engine.connect() as conn:
        branches = BranchModel.get_active_branches(conn, company_id)
    
    if not branches:
        st.warning("No active branches found.")
        return
    
    # Branch selection
    branch_options = {branch[1]: branch[0] for branch in branches}
    selected_branch = st.selectbox("Select Branch", list(branch_options.keys()))
    branch_id = branch_options[selected_branch]
    
    # Date range filter
    col1, col2 = st.columns(2)
    
    with col1:
        date_options = [
            "This Week",
            "This Month",
            "This Year",
            "All Reports",
            "Custom Range"
        ]
        date_filter = st.selectbox("Date Range", date_options, key="branch_reports_date_filter")
    
    with col2:
        # Custom date range if selected
        if date_filter == "Custom Range":
            today = datetime.date.today()
            start_date = st.date_input("Start Date", today - datetime.timedelta(days=30), key="branch_start_date")
            end_date = st.date_input("End Date", today, key="branch_end_date")
        else:
            # Set default dates based on filter
            start_date, end_date = get_date_range_from_filter(date_filter)
    
    # Fetch reports
    with engine.connect() as conn:
        reports = ReportModel.get_branch_reports(conn, branch_id, start_date, end_date)
    
    if not reports:
        st.info("No reports found for the selected branch and period.")
        return
    
    # Display report stats
    total_reports = len(reports)
    unique_employees = len(set(r[1] for r in reports))  # Unique employee names
    
    st.write(f"Found {total_reports} reports from {unique_employees} employees in {selected_branch}.")
    
    # Download button
    if st.button("Download as PDF", key="download_branch_reports"):
        pdf = create_branch_report_pdf(reports, selected_branch)
        
        # Format date range for filename
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        st.download_button(
            label="Download PDF",
            data=pdf,
            file_name=f"{selected_branch}_reports_{start_str}_to_{end_str}.pdf",
            mime="application/pdf"
        )
    
    # Display reports grouped by employee
    reports_by_employee = {}
    for report in reports:
        employee_name = report[1]
        role_name = report[2]
        key = f"{employee_name} ({role_name})"
        
        if key not in reports_by_employee:
            reports_by_employee[key] = []
        
        reports_by_employee[key].append(report)
    
    # Display employees
    for employee, emp_reports in reports_by_employee.items():
        with st.expander(f"{employee} ({len(emp_reports)} reports)", expanded=False):
            # Display each report
            for report in sorted(emp_reports, key=lambda x: x[3], reverse=True):
                report_date = report[3]
                report_text = report[4]
                
                st.markdown(f'''
                <div class="report-item">
                    <strong>{report_date.strftime('%A, %d %b %Y')}</strong>
                    <p>{report_text}</p>
                </div>
                ''', unsafe_allow_html=True)

def view_role_reports(engine, company_id, company_name):
    """View and download reports for a specific role.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
        company_name: Name of the company for display
    """
    st.markdown("### Role-based Reports")
    
    # Get roles
    with engine.connect() as conn:
        roles = RoleModel.get_all_roles(conn, company_id)
    
    if not roles:
        st.warning("No roles found.")
        return
    
    # Role selection
    role_options = {role[1]: role[0] for role in roles}
    selected_role = st.selectbox("Select Role", list(role_options.keys()))
    role_id = role_options[selected_role]
    
    # Date range filter
    col1, col2 = st.columns(2)
    
    with col1:
        date_options = [
            "This Week",
            "This Month",
            "This Year",
            "All Reports",
            "Custom Range"
        ]
        date_filter = st.selectbox("Date Range", date_options, key="role_reports_date_filter")
    
    with col2:
        # Custom date range if selected
        if date_filter == "Custom Range":
            today = datetime.date.today()
            start_date = st.date_input("Start Date", today - datetime.timedelta(days=30), key="role_start_date")
            end_date = st.date_input("End Date", today, key="role_end_date")
        else:
            # Set default dates based on filter
            start_date, end_date = get_date_range_from_filter(date_filter)
    
    # Fetch reports
    with engine.connect() as conn:
        reports = ReportModel.get_company_reports(conn, company_id, start_date, end_date, role_id=role_id)
    
    if not reports:
        st.info(f"No reports found for {selected_role}s in the selected period.")
        return
    
    # Display report stats
    total_reports = len(reports)
    unique_employees = len(set(r[1] for r in reports))  # Unique employee names
    unique_branches = len(set(r[3] for r in reports))  # Unique branch names
    
    st.write(f"Found {total_reports} reports from {unique_employees} {selected_role}s across {unique_branches} branches.")
    
    # Download button
    if st.button("Download as PDF", key="download_role_reports"):
        pdf = create_role_report_pdf(reports, selected_role, company_name)
        
        # Format date range for filename
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        st.download_button(
            label="Download PDF",
            data=pdf,
            file_name=f"{selected_role}_reports_{start_str}_to_{end_str}.pdf",
            mime="application/pdf"
        )
    
    # Display reports grouped by branch and employee
    reports_by_branch = {}
    for report in reports:
        branch_name = report[3]
        
        if branch_name not in reports_by_branch:
            reports_by_branch[branch_name] = {}
        
        employee_name = report[1]
        if employee_name not in reports_by_branch[branch_name]:
            reports_by_branch[branch_name][employee_name] = []
        
        reports_by_branch[branch_name][employee_name].append(report)
    
    # Display branches
    for branch_name, employees in reports_by_branch.items():
        with st.expander(f"Branch: {branch_name} ({sum(len(reports) for reports in employees.values())} reports)", expanded=False):
            # Display employees in this branch
            for employee_name, emp_reports in employees.items():
                with st.expander(f"{employee_name} ({len(emp_reports)} reports)", expanded=False):
                    # Display each report
                    for report in sorted(emp_reports, key=lambda x: x[4], reverse=True):
                        report_date = report[4]
                        report_text = report[5]
                        
                        st.markdown(f'''
                        <div class="report-item">
                            <strong>{report_date.strftime('%A, %d %b %Y')}</strong>
                            <p>{report_text}</p>
                        </div>
                        ''', unsafe_allow_html=True)

def view_employee_reports(engine, company_id):
    """View and download reports for a specific employee.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    st.markdown("### Individual Employee Reports")
    
    # Get active employees
    with engine.connect() as conn:
        employees = EmployeeModel.get_active_employees(conn, company_id)
    
    if not employees:
        st.warning("No active employees found.")
        return
    
    # Employee selection with branch info
    employee_options = {}
    for emp in employees:
        display_name = f"{emp[1]} ({emp[4]}, {emp[2]})"
        employee_options[display_name] = emp[0]
    
    selected_employee = st.selectbox("Select Employee", list(employee_options.keys()))
    employee_id = employee_options[selected_employee]
    employee_name = selected_employee.split(" (")[0]
    
    # Date range filter
    col1, col2 = st.columns(2)
    
    with col1:
        date_options = [
            "This Week",
            "This Month",
            "This Year",
            "All Reports",
            "Custom Range"
        ]
        date_filter = st.selectbox("Date Range", date_options, key="employee_reports_date_filter")
    
    with col2:
        # Custom date range if selected
        if date_filter == "Custom Range":
            today = datetime.date.today()
            start_date = st.date_input("Start Date", today - datetime.timedelta(days=30), key="emp_start_date")
            end_date = st.date_input("End Date", today, key="emp_end_date")
        else:
            # Set default dates based on filter
            start_date, end_date = get_date_range_from_filter(date_filter)
    
    # Fetch reports
    with engine.connect() as conn:
        reports = ReportModel.get_employee_reports(conn, employee_id, start_date, end_date)
    
    if not reports:
        st.info(f"No reports found for {employee_name} in the selected period.")
        return
    
    # Display report stats
    total_reports = len(reports)
    
    st.write(f"Found {total_reports} reports from {employee_name}.")
    
    # Download button
    if st.button("Download as PDF", key="download_employee_reports"):
        pdf = create_employee_report_pdf(reports, employee_name)
        
        # Format date range for filename
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        st.download_button(
            label="Download PDF",
            data=pdf,
            file_name=f"{employee_name}_reports_{start_str}_to_{end_str}.pdf",
            mime="application/pdf"
        )
    
    # Display reports
    for report in sorted(reports, key=lambda x: x[1], reverse=True):
        report_date = report[1]
        report_text = report[2]
        
        st.markdown(f'''
        <div class="report-item">
            <strong>{report_date.strftime('%A, %d %b %Y')}</strong>
            <p>{report_text}</p>
        </div>
        ''', unsafe_allow_html=True)
