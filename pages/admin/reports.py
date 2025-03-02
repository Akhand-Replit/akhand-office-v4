import streamlit as st
import datetime
from database.models import ReportModel, EmployeeModel
from utils.pdf_generator import create_employee_report_pdf
from utils.helpers import get_date_range_from_filter

def view_all_reports(engine):
    """Display and manage all employee reports.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Employee Reports</h2>', unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Employee filter
        with engine.connect() as conn:
            employees = EmployeeModel.get_active_employees(conn)
        
        employee_options = ["All Employees"] + [emp[1] for emp in employees]
        employee_filter = st.selectbox("Select Employee", employee_options, key="reports_employee_filter")
    
    with col2:
        # Date range filter
        date_options = [
            "All Time",
            "Today",
            "This Week",
            "This Month",
            "This Year",
            "Custom Range"
        ]
        date_filter = st.selectbox("Date Range", date_options, key="reports_date_filter")
    
    with col3:
        # Custom date range if selected
        if date_filter == "Custom Range":
            today = datetime.date.today()
            start_date = st.date_input("Start Date", today - datetime.timedelta(days=30))
            end_date = st.date_input("End Date", today)
        else:
            # Set default dates based on filter
            start_date, end_date = get_date_range_from_filter(date_filter)
    
    # Fetch reports based on filters
    with engine.connect() as conn:
        reports = ReportModel.get_all_reports(conn, start_date, end_date, employee_name=employee_filter)
    
    # Display reports
    if not reports:
        st.info("No reports found for the selected criteria")
    else:
        st.write(f"Found {len(reports)} reports")
        
        # Group by employee for export
        employee_reports = {}
        for report in reports:
            if report[0] not in employee_reports:
                employee_reports[report[0]] = []
            employee_reports[report[0]].append(report)
        
        # Export options
        col1, col2 = st.columns([3, 1])
        with col2:
            if employee_filter != "All Employees" and len(employee_reports) == 1:
                if st.button("Export as PDF"):
                    pdf = create_employee_report_pdf(reports, employee_filter)
                    st.download_button(
                        label="Download PDF",
                        data=pdf,
                        file_name=f"{employee_filter}_reports_{start_date}_to_{end_date}.pdf",
                        mime="application/pdf"
                    )
        
        # Display reports
        for employee_name, emp_reports in employee_reports.items():
            with st.expander(f"Reports by {employee_name} ({len(emp_reports)})", expanded=True):
                # Group by month/year for better organization
                reports_by_period = {}
                for report in emp_reports:
                    period = report[1].strftime('%B %Y')
                    if period not in reports_by_period:
                        reports_by_period[period] = []
                    reports_by_period[period].append(report)
                
                for period, period_reports in reports_by_period.items():
                    st.markdown(f"##### {period}")
                    for report in period_reports:
                        st.markdown(f'''
                        <div class="report-item">
                            <span style="color: #777;">{report[1].strftime('%A, %d %b %Y')}</span>
                            <p>{report[2]}</p>
                        </div>
                        ''', unsafe_allow_html=True)
