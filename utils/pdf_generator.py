import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def create_employee_report_pdf(reports, employee_name=None):
    """Generate a PDF report for employee daily reports.
    
    Args:
        reports: List of report data tuples (id, date, text)
        employee_name: Name of the employee (optional)
        
    Returns:
        bytes: PDF content as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,
        spaceAfter=12
    )
    title = f"Work Reports: {employee_name}" if employee_name else "Work Reports"
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))
    
    # Date range
    if reports:
        date_style = ParagraphStyle(
            'DateRange',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.gray
        )
        min_date = min(report[1] for report in reports).strftime('%d %b %Y')
        max_date = max(report[1] for report in reports).strftime('%d %b %Y')
        elements.append(Paragraph(f"Period: {min_date} to {max_date}", date_style))
        elements.append(Spacer(1, 20))
    
    # Group reports by month
    reports_by_month = {}
    for report in reports:
        month_year = report[1].strftime('%B %Y')
        if month_year not in reports_by_month:
            reports_by_month[month_year] = []
        reports_by_month[month_year].append(report)
    
    # Add each month's reports
    for month, month_reports in reports_by_month.items():
        # Month header
        month_style = ParagraphStyle(
            'Month',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        )
        elements.append(Paragraph(month, month_style))
        
        # Reports for the month
        for report in month_reports:
            # Date
            date_style = ParagraphStyle(
                'Date',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.blue
            )
            elements.append(Paragraph(report[1].strftime('%A, %d %b %Y'), date_style))
            
            # Report text
            text_style = ParagraphStyle(
                'ReportText',
                parent=styles['Normal'],
                fontSize=10,
                leftIndent=10
            )
            elements.append(Paragraph(report[2], text_style))
            elements.append(Spacer(1, 12))
        
        elements.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def create_branch_report_pdf(reports, branch_name):
    """Generate a PDF report for all employees in a branch.
    
    Args:
        reports: List of report data tuples (id, employee_name, role, date, text, created_at)
        branch_name: Name of the branch
        
    Returns:
        bytes: PDF content as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,
        spaceAfter=12
    )
    elements.append(Paragraph(f"Branch Reports: {branch_name}", title_style))
    elements.append(Spacer(1, 12))
    
    # Date range
    if reports:
        date_style = ParagraphStyle(
            'DateRange',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.gray
        )
        min_date = min(report[3] for report in reports).strftime('%d %b %Y')
        max_date = max(report[3] for report in reports).strftime('%d %b %Y')
        elements.append(Paragraph(f"Period: {min_date} to {max_date}", date_style))
        elements.append(Spacer(1, 20))
    
    # Group reports by employee and date
    reports_by_employee = {}
    for report in reports:
        employee_name = report[1]
        role_name = report[2]
        
        key = f"{employee_name} ({role_name})"
        if key not in reports_by_employee:
            reports_by_employee[key] = []
        
        reports_by_employee[key].append(report)
    
    # Add each employee's reports
    for employee, emp_reports in reports_by_employee.items():
        # Employee header
        emp_style = ParagraphStyle(
            'Employee',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        )
        elements.append(Paragraph(employee, emp_style))
        
        # Group by date
        for report in emp_reports:
            # Date
            date_style = ParagraphStyle(
                'Date',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.blue
            )
            elements.append(Paragraph(report[3].strftime('%A, %d %b %Y'), date_style))
            
            # Report text
            text_style = ParagraphStyle(
                'ReportText',
                parent=styles['Normal'],
                fontSize=10,
                leftIndent=10
            )
            elements.append(Paragraph(report[4], text_style))
            elements.append(Spacer(1, 12))
        
        elements.append(Spacer(1, 15))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def create_company_report_pdf(reports, company_name):
    """Generate a PDF report for all branches in a company.
    
    Args:
        reports: List of report data tuples (id, employee_name, role, branch_name, date, text, created_at)
        company_name: Name of the company
        
    Returns:
        bytes: PDF content as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,
        spaceAfter=12
    )
    elements.append(Paragraph(f"Company Reports: {company_name}", title_style))
    elements.append(Spacer(1, 12))
    
    # Date range
    if reports:
        date_style = ParagraphStyle(
            'DateRange',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.gray
        )
        min_date = min(report[4] for report in reports).strftime('%d %b %Y')
        max_date = max(report[4] for report in reports).strftime('%d %b %Y')
        elements.append(Paragraph(f"Period: {min_date} to {max_date}", date_style))
        elements.append(Spacer(1, 20))
    
    # Group reports by branch, then by employee
    reports_by_branch = {}
    for report in reports:
        branch_name = report[3]
        
        if branch_name not in reports_by_branch:
            reports_by_branch[branch_name] = {}
        
        employee_name = report[1]
        role_name = report[2]
        key = f"{employee_name} ({role_name})"
        
        if key not in reports_by_branch[branch_name]:
            reports_by_branch[branch_name][key] = []
        
        reports_by_branch[branch_name][key].append(report)
    
    # Add each branch's reports
    for branch_name, employees in reports_by_branch.items():
        # Branch header
        branch_style = ParagraphStyle(
            'Branch',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=10,
            textColor=colors.blue
        )
        elements.append(Paragraph(f"Branch: {branch_name}", branch_style))
        
        # For each employee in the branch
        for employee_name, emp_reports in employees.items():
            # Employee header
            emp_style = ParagraphStyle(
                'Employee',
                parent=styles['Heading3'],
                fontSize=14,
                spaceAfter=8
            )
            elements.append(Paragraph(employee_name, emp_style))
            
            # Group by date
            emp_reports_by_date = {}
            for report in emp_reports:
                date_str = report[4].strftime('%Y-%m-%d')
                if date_str not in emp_reports_by_date:
                    emp_reports_by_date[date_str] = report
            
            # Add each report
            for date_str, report in sorted(emp_reports_by_date.items(), reverse=True):
                # Date
                date_style = ParagraphStyle(
                    'Date',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.darkblue
                )
                elements.append(Paragraph(report[4].strftime('%A, %d %b %Y'), date_style))
                
                # Report text
                text_style = ParagraphStyle(
                    'ReportText',
                    parent=styles['Normal'],
                    fontSize=10,
                    leftIndent=10
                )
                elements.append(Paragraph(report[5], text_style))
                elements.append(Spacer(1, 10))
            
            elements.append(Spacer(1, 10))
        
        elements.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def create_role_report_pdf(reports, role_name, company_name):
    """Generate a PDF report for all employees of a specific role.
    
    Args:
        reports: List of report data tuples with employee and branch info
        role_name: Name of the role
        company_name: Name of the company
        
    Returns:
        bytes: PDF content as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,
        spaceAfter=12
    )
    elements.append(Paragraph(f"{role_name} Reports - {company_name}", title_style))
    elements.append(Spacer(1, 12))
    
    # Date range
    if reports:
        date_style = ParagraphStyle(
            'DateRange',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.gray
        )
        min_date = min(report[4] for report in reports).strftime('%d %b %Y')
        max_date = max(report[4] for report in reports).strftime('%d %b %Y')
        elements.append(Paragraph(f"Period: {min_date} to {max_date}", date_style))
        elements.append(Spacer(1, 20))
    
    # Group reports by employee and branch
    reports_by_employee = {}
    for report in reports:
        employee_name = report[1]
        branch_name = report[3]
        
        key = f"{employee_name} ({branch_name})"
        if key not in reports_by_employee:
            reports_by_employee[key] = []
        
        reports_by_employee[key].append(report)
    
    # Add each employee's reports
    for employee, emp_reports in reports_by_employee.items():
        # Employee header
        emp_style = ParagraphStyle(
            'Employee',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        )
        elements.append(Paragraph(employee, emp_style))
        
        # Group by date
        emp_reports_by_date = {}
        for report in emp_reports:
            date_str = report[4].strftime('%Y-%m-%d')
            if date_str not in emp_reports_by_date:
                emp_reports_by_date[date_str] = report
        
        # Add each report
        for date_str, report in sorted(emp_reports_by_date.items(), reverse=True):
            # Date
            date_style = ParagraphStyle(
                'Date',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.blue
            )
            elements.append(Paragraph(report[4].strftime('%A, %d %b %Y'), date_style))
            
            # Report text
            text_style = ParagraphStyle(
                'ReportText',
                parent=styles['Normal'],
                fontSize=10,
                leftIndent=10
            )
            elements.append(Paragraph(report[5], text_style))
            elements.append(Spacer(1, 10))
        
        elements.append(Spacer(1, 15))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
