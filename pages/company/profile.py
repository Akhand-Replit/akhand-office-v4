import streamlit as st
import time
from database.models import CompanyModel

def edit_profile(engine):
    """Edit company profile information.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Company Profile</h2>', unsafe_allow_html=True)
    
    company_id = st.session_state.user["id"]
    
    # Fetch current company data
    with engine.connect() as conn:
        company_data = CompanyModel.get_company_by_id(conn, company_id)
    
    if not company_data:
        st.error("Could not retrieve company information. Please try again later.")
        return
    
    company_name, username, profile_pic_url, is_active = company_data
    
    # Display current profile picture
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("<p>Company Logo:</p>", unsafe_allow_html=True)
        try:
            st.image(profile_pic_url, width=150, use_container_width=False)
        except:
            st.image("https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y", width=150, use_container_width=False)
    
    with col2:
        st.markdown(f"<p><strong>Company Name:</strong> {company_name}</p>", unsafe_allow_html=True)
        st.markdown(f"<p><strong>Username:</strong> {username}</p>", unsafe_allow_html=True)
        st.markdown(f"<p><strong>Status:</strong> {'Active' if is_active else 'Inactive'}</p>", unsafe_allow_html=True)
    
    # Form for updating profile
    with st.form("update_company_profile_form"):
        st.subheader("Update Company Information")
        
        # Company name update
        new_company_name = st.text_input("Company Name", value=company_name)
        
        # Profile picture URL update
        new_profile_pic_url = st.text_input("Logo/Profile URL", value=profile_pic_url or "")
        
        # Password update section
        st.subheader("Change Password")
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submitted = st.form_submit_button("Update Profile")
        if submitted:
            updates_made = False
            
            # Check if any changes were made to name or picture URL
            if new_company_name != company_name or new_profile_pic_url != profile_pic_url:
                with engine.connect() as conn:
                    CompanyModel.update_profile(conn, company_id, new_company_name, new_profile_pic_url)
                
                # Update session state with new values
                st.session_state.user["full_name"] = new_company_name
                st.session_state.user["profile_pic_url"] = new_profile_pic_url
                
                updates_made = True
                st.success("Company information updated successfully.")
            
            # Handle password change if attempted
            if current_password or new_password or confirm_password:
                if not current_password:
                    st.error("Please enter your current password to change it.")
                elif not new_password:
                    st.error("Please enter a new password.")
                elif new_password != confirm_password:
                    st.error("New passwords do not match.")
                else:
                    # Verify current password
                    with engine.connect() as conn:
                        is_valid = CompanyModel.verify_password(conn, company_id, current_password)
                    
                    if not is_valid:
                        st.error("Current password is incorrect.")
                    else:
                        # Update password
                        with engine.connect() as conn:
                            CompanyModel.reset_password(conn, company_id, new_password)
                        
                        updates_made = True
                        st.success("Password updated successfully.")
            
            if updates_made:
                time.sleep(1)  # Give the user time to read the success message
                st.rerun()
