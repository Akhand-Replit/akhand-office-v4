import streamlit as st
import time
from database.models.employee_model import EmployeeModel

def edit_my_profile(engine):
    """Edit personal profile information."""
    st.markdown('<h2 class="sub-header">My Profile</h2>', unsafe_allow_html=True)
    
    employee_id = st.session_state.user["id"]
    
    # Fetch current employee data
    with engine.connect() as conn:
        employee_data = EmployeeModel.get_employee_by_id(conn, employee_id)
    
    if not employee_data:
        st.error("Could not retrieve your profile information. Please try again later.")
        return
    
    username, current_full_name, current_pic_url = employee_data
    
    # Display current profile picture
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("<p>Current Profile Picture:</p>", unsafe_allow_html=True)
        try:
            st.image(current_pic_url, width=150, use_container_width=False)
        except:
            st.image("https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y", width=150, use_container_width=False)
    
    with col2:
        st.markdown(f"<p><strong>Username:</strong> {username}</p>", unsafe_allow_html=True)
        st.info("Username cannot be changed as it is used for login purposes.")
    
    # Form for updating profile
    with st.form("update_profile_form"):
        st.subheader("Update Your Information")
        
        # Full name update
        new_full_name = st.text_input("Full Name", value=current_full_name)
        
        # Profile picture URL update
        new_profile_pic_url = st.text_input("Profile Picture URL", value=current_pic_url or "")
        
        # Password update section
        st.subheader("Change Password")
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submitted = st.form_submit_button("Update Profile")
        if submitted:
            updates_made = False
            
            # Check if any changes were made to name or picture URL
            if new_full_name != current_full_name or new_profile_pic_url != current_pic_url:
                with engine.connect() as conn:
                    EmployeeModel.update_profile(conn, employee_id, new_full_name, new_profile_pic_url)
                
                # Update session state with new values
                st.session_state.user["full_name"] = new_full_name
                st.session_state.user["profile_pic_url"] = new_profile_pic_url
                
                updates_made = True
                st.success("Profile information updated successfully.")
            
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
                        is_valid = EmployeeModel.verify_password(conn, employee_id, current_password)
                    
                    if not is_valid:
                        st.error("Current password is incorrect.")
                    else:
                        # Update password - using reset_password instead of update_password
                        with engine.connect() as conn:
                            EmployeeModel.reset_password(conn, employee_id, new_password)
                        
                        updates_made = True
                        st.success("Password updated successfully.")
            
            if updates_made:
                time.sleep(1)  # Give the user time to read the success message
                st.rerun()
