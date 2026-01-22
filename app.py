import streamlit as st
import time
from datetime import datetime
from database import DatabaseService
from ai_service import AIService
from intern_dashboard import InternDashboard
from admin_dashboard import AdminDashboard

# Initialize services
db = DatabaseService()
ai = AIService()

def landing_page():
    st.set_page_config(
        page_title="InternTrack | Intelligent Intern Development Platform",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
        <style>
        .main-title {
            font-size: 4.5rem;
            font-weight: 900;
            font-style: italic;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0;
            line-height: 1;
        }
        .subtitle {
            font-size: 0.9rem;
            font-weight: 600;
            color: #64748b;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            margin-top: 0.5rem;
            margin-bottom: 2rem;
        }
        .auth-box {
            background: white;
            border-radius: 2rem;
            padding: 3rem;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.15);
            border: 1px solid #f1f5f9;
            position: relative;
            overflow: hidden;
        }
        .auth-box::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)
        
        st.markdown('<h1 class="main-title">InternTrack</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Intelligent Intern Development Platform</p>', unsafe_allow_html=True)
        
        if 'auth_view' not in st.session_state:
            st.session_state.auth_view = 'root'
        
        if st.session_state.auth_view == 'root':
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("Intern Portal\n\nAccess your learning dashboard and track progress", 
                           use_container_width=True,
                           help="Intern login/registration"):
                    st.session_state.auth_view = 'intern'
                    st.rerun()
            
            with col_b:
                if st.button("Admin Hub\n\nManage tracks and monitor cohort performance", 
                           use_container_width=True,
                           help="Company admin login"):
                    st.session_state.auth_view = 'company'
                    st.rerun()
        else:
            if st.button("Back to Selection", type="secondary", use_container_width=True):
                st.session_state.auth_view = 'root'
                st.rerun()
            
            st.markdown('<br>', unsafe_allow_html=True)
            
            if st.session_state.auth_view == 'company':
                company_login_page()
            else:
                intern_auth_page()
        
        st.markdown('</div>', unsafe_allow_html=True)

def company_login_page():
    st.subheader("Admin Authentication")
    st.markdown("Enter your administrative credentials to access the oversight hub.")
    
    with st.form("company_login", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            admin_id = st.text_input("Admin ID", placeholder="Enter admin ID", key="admin_id")
        with col2:
            password = st.text_input("Passcode", type="password", placeholder="Enter passcode", key="admin_pass")
        
        if st.form_submit_button("Authenticate & Enter Hub", type="primary", use_container_width=True):
            if admin_id == "pgt" and password == "123":
                st.session_state.role = "COMPANY"
                st.session_state.auth_view = 'root'
                st.success("Authentication successful! Redirecting...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Authentication failed. Please check your credentials.")

def intern_auth_page():
    if 'is_reg' not in st.session_state:
        st.session_state.is_reg = False
    
    if st.session_state.is_reg:
        st.subheader("Create New Profile")
        st.markdown("Register to start your learning journey with personalized skill tracking.")
    else:
        st.subheader("Intern Authorization")
        st.markdown("Sign in to access your personalized learning dashboard.")
    
    with st.form("intern_auth", clear_on_submit=False):
        if st.session_state.is_reg:
            name = st.text_input("Full Name", placeholder="John Doe", key="reg_name")
        
        email = st.text_input("Email Address", placeholder="john@example.com", key="auth_email")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="auth_pass")
        
        if st.session_state.is_reg:
            st.markdown("### Select Learning Track")
            jobs = db.get_jobs()
            if jobs:
                job_titles = {j['id']: f"{j['title']} ({j['domain']})" for j in jobs}
                selected_job = st.selectbox(
                    "Assigned Track", 
                    options=list(job_titles.keys()),
                    format_func=lambda x: job_titles[x],
                    index=0
                )
                st.caption("This track will define your learning objectives and skill requirements.")
            else:
                st.warning("No learning tracks available. Please contact administrator.")
                selected_job = None
        
        submit_text = "Create Profile & Start" if st.session_state.is_reg else "Authorize & Continue"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.form_submit_button(submit_text, type="primary", use_container_width=True):
                if st.session_state.is_reg:
                    if not name or not email or not password:
                        st.error("Please fill in all required fields.")
                    elif not selected_job:
                        st.error("Please select a learning track.")
                    else:
                        if db.register_intern(name, email, password, selected_job):
                            st.success("Profile created successfully! Please login with your credentials.")
                            st.session_state.is_reg = False
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Email already registered. Please use a different email or login.")
                else:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        user = db.login_intern(email, password)
                        if user:
                            st.session_state.role = "INTERN"
                            st.session_state.current_user = user
                            st.session_state.auth_view = 'root'
                            st.success("Login successful! Loading your dashboard...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Invalid login credentials. Please try again.")
        
        with col2:
            if st.form_submit_button("Clear", use_container_width=True):
                st.rerun()
    
    st.markdown("---")
    switch_text = "Already have an account? Sign in" if st.session_state.is_reg else "New to InternTrack? Create profile"
    if st.button(switch_text, use_container_width=True):
        st.session_state.is_reg = not st.session_state.is_reg
        st.rerun()

def main():
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'auth_view' not in st.session_state:
        st.session_state.auth_view = 'root'
    if 'is_reg' not in st.session_state:
        st.session_state.is_reg = False
    
    st.markdown("""
        <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        .stButton button {
            border-radius: 0.75rem;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        [data-testid="stMetric"] {
            background-color: #f8fafc;
            border-radius: 0.75rem;
            padding: 1rem;
            border: 1px solid #f1f5f9;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 0.75rem 0.75rem 0 0;
            padding: 1rem 2rem;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.role:
        landing_page()
    elif st.session_state.role == "INTERN":
        intern_dashboard = InternDashboard(db, ai)
        intern_dashboard.show()
    else:
        admin_dashboard = AdminDashboard(db)
        admin_dashboard.show()

if __name__ == "__main__":
    main()
