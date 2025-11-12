# pages/login_page.py
import streamlit as st
from lib.data_manager import get_dataframes
import time

def show_login():
    """
    Render the login form. If the user is already logged in (session state),
    do nothing — this guarantees the sign-in UI is hidden after successful login.
    """
    # If already logged in, don't render the login UI at all.
    if st.session_state.get("logged_in", False):
        return

    users, *_ = get_dataframes()

    st.markdown("<h1 style='color:white;'>Welcome to <span style='color:#2b6ef7;'>Atomm</span></h1>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])

    with col1:
        st.image("https://img.icons8.com/dusk/256/task.png", width=120)

    with col2:
        st.markdown("## Sign in")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if authenticate(username, password, users):
                # set session state values
                st.session_state["logged_in"] = True
                st.session_state["username"] = username

                # set role from users.csv if present, otherwise default to Employee
                try:
                    if users is not None and not users.empty and "role" in users.columns:
                        row = users[users["username"] == username]
                        st.session_state["role"] = row.iloc[0]["role"] if not row.empty else "Employee"
                    else:
                        st.session_state["role"] = "Employee"
                except Exception:
                    st.session_state["role"] = "Employee"

                st.success("✅ Login successful!")
                # allow Streamlit to re-run and render the main UI in the same request:
                # no experimental api calls here; just return so the script continues.
                return
            else:
                st.error("Invalid credentials")


def authenticate(username, password, users_df):
    """Authenticate user from CSV; fallback admin/admin if empty."""
    if not username or not password:
        return False

    if users_df is None or users_df.empty:
        return username == "admin" and password == "admin"

    if "username" not in users_df.columns:
        return username == "admin" and password == "admin"

    row = users_df[users_df["username"] == username]
    if row.empty:
        return False

    stored_pw = str(row.iloc[0].get("password", ""))
    return password == stored_pw
