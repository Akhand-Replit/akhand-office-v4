import streamlit as st
import datetime
from database.models import ReportModel
from utils.helpers import get_date_range_from_filter

def submit_report(engine):
    """Form for employee to submit daily reports.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Submit Daily Report</h2>', unsafe_allow_html=True)
    
    employee_id = st.session_state.user["id"]
    
    with st.form("submit_report_form"):
        report_date = st.date_input("Report Date", datetime.date.today())
        
        # Check if a report already exists for this date
        with engine.connect() as conn:
            existing_report = ReportModel.check_report_exists(conn, employee_id, report_date)
        
        if existing_report:
            st.warning(f"You already have a report for {report_date.strftime('%d %b, %Y')}. Submitting will update your existing report.")
        
        report_text = st.text_area("What did you work on today?", height=200)
        
        submitted = st.form_submit_button("Submit Report")
        if submitted:
            if not report_text:
                st.error("Please enter your report")
            else:
                try:
                    with engine.connect() as conn:
                        if existing_report:
                            # Update existing report
                            ReportModel.update_report(conn, existing_report[0], report_date, report_text)
                            success_message = "Report updated successfully"
                        else:
                            # Insert new report
                            ReportModel.add_report(conn, employee_id, report_date, report_text)
                            success_message = "Report submitted successfully"
                    
                    st.success(success_message)
                except Exception as e:
                    st.error(f"Error submitting report: {e}")

def view_my_reports(engine):
    """View and manage personal reports.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">My Reports</h2>', unsafe_allow_html=True)
    
    employee_id = st.session_state.user["id"]
    
    # Date range filter
    col1, col2 = st.columns(2)
    
    with col1:
        date_options = [
            "All Reports",
            "This Week",
            "This Month",
            "This Year",
            "Custom Range"
        ]
        date_filter = st.selectbox("Date Range", date_options, key="employee_reports_date_filter")
    
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
        reports = ReportModel.get_employee_reports(conn, employee_id, start_date, end_date)
    
    # Display reports
    if not reports:
        st.info("No reports found for the selected period")
    else:
        st.write(f"Found {len(reports)} reports")
        
        # Group by month/year for better organization
        reports_by_period = {}
        for report in reports:
            period = report[1].strftime('%B %Y')
            if period not in reports_by_period:
                reports_by_period[period] = []
            reports_by_period[period].append(report)
        
        for period, period_reports in reports_by_period.items():
            with st.expander(f"{period} ({len(period_reports)} reports)", expanded=True):
                for report in period_reports:
                    report_id = report[0]
                    report_date = report[1]
                    report_text = report[2]
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f'''
                        <div class="report-item">
                            <strong>{report_date.strftime('%A, %d %b %Y')}</strong>
                            <p>{report_text}</p>
                        </div>
                        ''', unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("Edit", key=f"edit_{report_id}"):
                            st.session_state.edit_report = {
                                'id': report_id,
                                'date': report_date,
                                'text': report_text
                            }
                            st.rerun()
        
    # Edit report if selected
    if hasattr(st.session_state, 'edit_report'):
        st.markdown('<h3 class="sub-header">Edit Report</h3>', unsafe_allow_html=True)
        
        with st.form("edit_report_form"):
            report_date = st.date_input("Report Date", st.session_state.edit_report['date'])
            report_text = st.text_area("Report Text", st.session_state.edit_report['text'], height=200)
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Update Report")
            with col2:
                cancel = st.form_submit_button("Cancel")
            
            if submitted:
                if not report_text:
                    st.error("Please enter your report")
                else:
                    try:
                        with engine.connect() as conn:
                            ReportModel.update_report(
                                conn, 
                                st.session_state.edit_report['id'], 
                                report_date, 
                                report_text
                            )
                        st.success("Report updated successfully")
                        del st.session_state.edit_report
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating report: {e}")
            
            if cancel:
                del st.session_state.edit_report
                st.rerun()
