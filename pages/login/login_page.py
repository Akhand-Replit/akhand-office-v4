import streamlit as st
from utils.auth import authenticate

def display_login(engine):
    """Display the login page.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-header">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">Employee Management System</h1>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        user = authenticate(engine, username, password)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid username or password")
    
    st.markdown('</div>', unsafe_allow_html=True)
