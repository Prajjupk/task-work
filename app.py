# app.py
import streamlit as st
from pages.login_page import show_login
from pages.home_page import show_home
from pages.tasks_page import show_tasks
from pages.files_page import show_files
from pages.audit_page import show_audit
from pages.analytics_page import show_analytics
from pages.comm_page import show_comm
from pages.settings_page import show_settings
from pages.reports_page import show_reports



st.set_page_config(
    page_title="ATOMM",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None,
)

# hide the built-in Streamlit multipage nav so only our custom nav appears
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] { display: none !important; }
    .css-1d391kg .css-1outpf7 { padding-top: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

PAGES = {
    "Home": show_home,
    "Tasks": show_tasks,
    "Files": show_files,
    "Reports": show_reports,
    "Analytics": show_analytics,
    "Settings": show_settings,
    
}

def logout():
    """Clear login-related session state. Streamlit will rerun after the button click."""
    for k in ("logged_in", "username", "role"):
        if k in st.session_state:
            del st.session_state[k]
    # No explicit rerun call — Streamlit re-runs automatically after button click.

def main():
    # ensure login flag exists
    st.session_state.setdefault("logged_in", False)

    # show login UI if not logged in (do not return immediately; let the script continue)
    if not st.session_state["logged_in"]:
        show_login()

    # if still not logged in after show_login(), stop here (login screen remains)
    if not st.session_state.get("logged_in", False):
        return

    # When logged in, render the sidebar and pages
    display_name = st.session_state.get("display_name") or st.session_state.get("username", "user")
    st.sidebar.title(f"TaskPilot — {display_name}")

    if st.sidebar.button("Logout"):
        logout()
        return

    choice = st.sidebar.radio("Navigate", list(PAGES.keys()), index=0)
    page_fn = PAGES.get(choice)
    if page_fn:
        page_fn()
    else:
        st.error("Selected page not found.")

if __name__ == "__main__":
    main()
