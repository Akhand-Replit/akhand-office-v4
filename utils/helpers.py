import datetime

def get_date_range_from_filter(date_filter):
    """Get start and end dates based on a date filter selection.
    
    Args:
        date_filter: String representing the selected date range
        
    Returns:
        tuple: (start_date, end_date)
    """
    today = datetime.date.today()
    
    if date_filter == "Today":
        start_date = today
        end_date = today
    elif date_filter == "This Week":
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = today
    elif date_filter == "This Month":
        start_date = today.replace(day=1)
        end_date = today
    elif date_filter == "This Year":
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:  # All Time/Reports
        start_date = datetime.date(2000, 1, 1)
        end_date = today
    
    return start_date, end_date

def format_timestamp(timestamp, format_str='%d %b, %Y'):
    """Format a timestamp into a readable string.
    
    Args:
        timestamp: Datetime object
        format_str: Format string (default: '%d %b, %Y')
        
    Returns:
        str: Formatted date string or "No date" if None
    """
    if timestamp:
        return timestamp.strftime(format_str)
    return "No due date"

def calculate_completion_rate(total, completed):
    """Calculate the completion rate as a percentage.
    
    Args:
        total: Total number of items
        completed: Number of completed items
        
    Returns:
        int: Completion rate percentage
    """
    if total == 0:
        return 0
    return round((completed / total) * 100)
