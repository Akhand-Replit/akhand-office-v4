import streamlit as st
import datetime
from database.models import MessageModel

def view_messages(engine):
    """View and send messages between company and admin.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Admin Messages</h2>', unsafe_allow_html=True)
    
    company_id = st.session_state.user["id"]
    
    # Create two columns for the layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display message history
        display_message_history(engine, company_id)
    
    with col2:
        # Form to send a new message
        send_message_form(engine, company_id)

def display_message_history(engine, company_id):
    """Display message history between company and admin.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    st.subheader("Message History")
    
    # Fetch all messages for this company
    with engine.connect() as conn:
        messages = MessageModel.get_messages_for_company(conn, company_id)
    
    if not messages:
        st.info("No messages yet. Send a message to get started.")
    else:
        # Mark unread messages as read
        for message in messages:
            message_id = message[0]
            is_from_admin = message[1] == "admin"
            is_read = message[4]
            
            # Mark admin messages as read when viewed
            if is_from_admin and not is_read:
                with engine.connect() as conn:
                    MessageModel.mark_as_read(conn, message_id)
        
        # Display messages in a chat-like format
        for message in messages:
            message_text = message[3]
            created_at = message[5].strftime('%d %b, %Y - %H:%M') if message[5] else "Unknown"
            sender_name = message[6]  # This will be "Admin" or company name
            is_from_admin = message[1] == "admin"
            
            # Align messages based on sender (left for admin, right for company)
            alignment = "left" if is_from_admin else "right"
            bg_color = "#f1f7fe" if is_from_admin else "#e9ffe9"
            border_color = "#1E88E5" if is_from_admin else "#4CAF50"
            
            st.markdown(f'''
            <div style="display: flex; justify-content: {alignment}; margin-bottom: 10px;">
                <div style="max-width: 80%; background-color: {bg_color}; 
                            padding: 10px; border-radius: 8px; border-left: 4px solid {border_color};">
                    <div style="font-weight: 600;">{sender_name}</div>
                    <p style="margin: 5px 0;">{message_text}</p>
                    <div style="text-align: right; font-size: 0.8rem; color: #777;">{created_at}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

def send_message_form(engine, company_id):
    """Form to send a new message to admin.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the current company
    """
    st.subheader("Send Message")
    
    with st.form("send_message_form"):
        message_text = st.text_area("Message to Admin", height=150)
        
        submitted = st.form_submit_button("Send Message")
        
        if submitted:
            if not message_text:
                st.error("Please enter a message")
            else:
                try:
                    with engine.connect() as conn:
                        MessageModel.send_message(
                            conn,
                            sender_type="company",
                            sender_id=company_id,
                            receiver_type="admin",
                            receiver_id=0,  # Admin ID is 0
                            message_text=message_text
                        )
                    st.success("Message sent to Admin")
                    st.rerun()  # Refresh to show the new message
                except Exception as e:
                    st.error(f"Error sending message: {e}")
