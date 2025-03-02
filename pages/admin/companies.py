import streamlit as st
from sqlalchemy import text
# Import directly from model files instead of from the models module
from database.models.company_model import CompanyModel
from database.models.branch_model import BranchModel

def manage_companies(engine):
    """Manage companies - listing, adding, activating/deactivating.
    
    Args:
        engine: SQLAlchemy database engine
    """
    st.markdown('<h2 class="sub-header">Manage Companies</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Company List", "Add New Company"])
    
    with tab1:
        display_company_list(engine)
    
    with tab2:
        add_new_company(engine)

def display_company_list(engine):
    """Display the list of companies with management options.
    
    Args:
        engine: SQLAlchemy database engine
    """
    # Fetch and display all companies
    with engine.connect() as conn:
        companies = CompanyModel.get_all_companies(conn)
    
    if not companies:
        st.info("No companies found. Add companies using the 'Add New Company' tab.")
    else:
        st.write(f"Total companies: {len(companies)}")
        
        for company in companies:
            company_id = company[0]
            company_name = company[1]
            username = company[2]
            profile_pic_url = company[3]
            is_active = company[4]
            created_at = company[5].strftime('%d %b, %Y') if company[5] else "Unknown"
            
            with st.expander(f"{company_name} (Username: {username})", expanded=False):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    try:
                        st.image(profile_pic_url, width=100, use_container_width=False)
                    except:
                        st.image("https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y", width=100)
                
                with col2:
                    st.write(f"**Company:** {company_name}")
                    st.write(f"**Username:** {username}")
                    st.write(f"**Status:** {'Active' if is_active else 'Inactive'}")
                    st.write(f"**Created:** {created_at}")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if is_active:  # If active
                            if st.button(f"Deactivate", key=f"deactivate_company_{company_id}"):
                                with engine.connect() as conn:
                                    CompanyModel.update_company_status(conn, company_id, False)
                                st.success(f"Deactivated company: {company_name}")
                                st.rerun()
                        else:  # If inactive
                            if st.button(f"Activate", key=f"activate_company_{company_id}"):
                                with engine.connect() as conn:
                                    CompanyModel.update_company_status(conn, company_id, True)
                                st.success(f"Activated company: {company_name}")
                                st.rerun()
                    
                    with col2:
                        if st.button(f"Reset Password", key=f"reset_company_{company_id}"):
                            new_password = "company123"  # Default reset password
                            with engine.connect() as conn:
                                CompanyModel.reset_password(conn, company_id, new_password)
                            st.success(f"Password reset to '{new_password}' for {company_name}")
                    
                    with col3:
                        if st.button(f"View Branches", key=f"view_branches_{company_id}"):
                            st.session_state.view_company_branches = company_id
                            st.session_state.view_company_name = company_name
                            st.rerun()
                            
                # Display branches if requested
                if hasattr(st.session_state, 'view_company_branches') and st.session_state.view_company_branches == company_id:
                    display_company_branches(engine, company_id, st.session_state.view_company_name)

def display_company_branches(engine, company_id, company_name):
    """Display branches for a specific company.
    
    Args:
        engine: SQLAlchemy database engine
        company_id: ID of the company
        company_name: Name of the company for display
    """
    st.markdown(f'<h3 class="sub-header">Branches for {company_name}</h3>', unsafe_allow_html=True)
    
    # Fetch branches for this company
    with engine.connect() as conn:
        branches = BranchModel.get_company_branches(conn, company_id)
    
    if not branches:
        st.info(f"No branches found for {company_name}.")
    else:
        st.write(f"Total branches: {len(branches)}")
        
        for branch in branches:
            branch_id = branch[0]
            branch_name = branch[1]
            location = branch[2] or "N/A"
            branch_head = branch[3] or "N/A"
            is_active = branch[4]
            
            st.markdown(f'''
            <div class="card">
                <h4>{branch_name}</h4>
                <p><strong>Location:</strong> {location}</p>
                <p><strong>Branch Head:</strong> {branch_head}</p>
                <p><strong>Status:</strong> {'Active' if is_active else 'Inactive'}</p>
            </div>
            ''', unsafe_allow_html=True)
    
    # Close button
    if st.button("Close Branches View", key=f"close_branches_{company_id}"):
        del st.session_state.view_company_branches
        del st.session_state.view_company_name
        st.rerun()

def add_new_company(engine):
    """Form to add a new company.
    
    Args:
        engine: SQLAlchemy database engine
    """
    # Form to add new company
    with st.form("add_company_form"):
        company_name = st.text_input("Company Name", help="Name of the company")
        username = st.text_input("Username", help="Username for company login")
        password = st.text_input("Password", type="password", help="Initial password")
        profile_pic_url = st.text_input("Profile Picture URL", help="Link to company logo or profile picture")
        
        submitted = st.form_submit_button("Add Company")
        if submitted:
            if not company_name or not username or not password:
                st.error("Please fill all required fields")
            else:
                # Check if company name or username already exists
                with engine.connect() as conn:
                    # Check company name
                    result = conn.execute(text('SELECT COUNT(*) FROM companies WHERE company_name = :company_name'), 
                                          {'company_name': company_name})
                    name_count = result.fetchone()[0]
                    
                    # Check username
                    result = conn.execute(text('SELECT COUNT(*) FROM companies WHERE username = :username'), 
                                          {'username': username})
                    username_count = result.fetchone()[0]
                    
                    if name_count > 0:
                        st.error(f"Company name '{company_name}' already exists")
                    elif username_count > 0:
                        st.error(f"Username '{username}' already exists")
                    else:
                        # Insert new company
                        try:
                            CompanyModel.add_company(conn, company_name, username, password, profile_pic_url)
                            st.success(f"Successfully added company: {company_name}")
                        except Exception as e:
                            st.error(f"Error adding company: {e}")
