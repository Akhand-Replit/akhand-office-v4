import streamlit as st
from styles.custom_css import get_custom_css

def setup_page_config():
    """Configure the Streamlit page settings"""
    # Page config
    st.set_page_config(
        page_title="Employee Management System",
        page_icon="👥",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)