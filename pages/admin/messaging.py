import streamlit as st
import datetime
from database.models import MessageModel, CompanyModel

def manage_messages(engine):
    """Admin message management - send and view messages to/from companies.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Company Messages</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["View Messages", "Send New Message"])
    
    with tab1:
        view_messages(engine)
    
    with tab2:
        send_message(engine)

def view_messages(engine):
    """View messages from companies.
    
    Args:
        engine: SQLAlchemy database engine
    """
    # Fetch all messages for admin
    with engine.connect() as conn:
        messages = MessageModel.get_messages_for_admin(conn)
    
    if not messages:
        st.info("No messages found.")
    else:
        st.write(f"Total messages: {len(messages)}")
        
        # Group messages by sender
        messages_by_sender = {}
        for message in messages:
            sender_name = message[6]  # sender_name from query
            if sender_name not in messages_by_sender:
                messages_by_sender[sender_name] = []
            messages_by_sender[sender_name].append(message)
        
        # Display messages by sender
        for sender_name, sender_messages in messages_by_sender.items():
            with st.expander(f"Messages from {sender_name} ({len(sender_messages)})", expanded=False):
                for message in sender_messages:
                    message_id = message[0]
                    message_text = message[3]
                    is_read = message[4]
                    created_at = message[5].strftime('%d %b, %Y - %H:%M') if message[5] else "Unknown"
                    
                    # Style based on read status
                    background_color = "#f0f0f0" if is_read else "#f1fff1"
                    border_color = "#9e9e9e" if is_read else "#4CAF50"
                    
                    st.markdown(f'''
                    <div style="background-color: {background_color}; padding: 1rem; border-radius: 8px; 
                                margin-bottom: 0.5rem; border-left: 4px solid {border_color};">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span style="font-weight: 600;">{sender_name}</span>
                            <span style="color: #777;">{created_at}</span>
                        </div>
                        <p>{message_text}</p>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # Mark as read button (if not already read)
                    if not is_read:
                        if st.button("Mark as Read", key=f"mark_read_{message_id}"):
                            with engine.connect() as conn:
                                MessageModel.mark_as_read(conn, message_id)
                            st.success("Message marked as read")
                            st.rerun()

def send_message(engine):
    """Send a message to a company.
    
    Args:
        engine: SQLAlchemy database engine
    """
    # Get active companies for recipient selection
    with engine.connect() as conn:
        companies = CompanyModel.get_active_companies(conn)
    
    if not companies:
        st.warning("No active companies found. Please add and activate companies first.")
        return
    
    # Create company selection dictionary
    company_options = {company[1]: company[0] for company in companies}
    
    # Message form
    with st.form("send_message_form"):
        st.subheader("New Message")
        
        recipient_name = st.selectbox("Select Company", list(company_options.keys()))
        message_text = st.text_area("Message", height=150)
        
        submitted = st.form_submit_button("Send Message")
        
        if submitted:
            if not message_text:
                st.error("Please enter a message")
            else:
                # Get company ID from selection
                recipient_id = company_options[recipient_name]
                
                try:
                    with engine.connect() as conn:
                        MessageModel.send_message(
                            conn,
                            sender_type="admin",
                            sender_id=0,  # Admin ID is 0
                            receiver_type="company",
                            receiver_id=recipient_id,
                            message_text=message_text
                        )
                    st.success(f"Message sent to {recipient_name}")
                except Exception as e:
                    st.error(f"Error sending message: {e}")
