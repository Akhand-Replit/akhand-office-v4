def get_custom_css():
    """Return the custom CSS for better UI styling.
    
    Returns:
        str: CSS styles as a string
    """
    return """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .sub-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 1rem;
    }
    
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .stat-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E88E5;
    }
    
    .stat-label {
        font-size: 1rem;
        color: #777;
    }
    
    .login-container {
        max-width: 400px;
        background-image: url("https://i.ibb.co/s9b3rSvg/3a02fb88ce57.png");
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        margin: 0 auto;
        padding: 2.5rem;
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    .stButton > button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-weight: 600;
        height: 2.5rem;
        border-radius: 5px;
    }
    
    .stTextInput > div > div > input {
        height: 2.5rem;
    }
    
    .report-item {
        background-color: #f1f7fe;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 4px solid #1E88E5;
    }
    
    .task-item {
        background-color: #f1fff1;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 4px solid #4CAF50;
    }
    
    .task-item.completed {
        background-color: #f0f0f0;
        border-left: 4px solid #9e9e9e;
    }
    
    .profile-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .profile-image {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #1E88E5;
    }
</style>
"""
