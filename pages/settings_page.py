# pages/settings_page.py
import streamlit as st
from pathlib import Path
import json
from lib.data_manager import get_dataframes, quick_save
import pandas as pd

DATA_DIR = Path(__file__).parents[1] / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"

def _load_settings():
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"theme": "Dark", "display_name": "", "email_notifications": False}

def _save_settings(settings: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")

def show_settings():
    """Settings page with persistence + display name sync"""
    st.title("⚙️ Settings")
    st.markdown("Customize your TaskPilot experience here!")

    # load persisted settings
    saved = _load_settings()

    # Prefill from saved settings or current session
    theme = st.selectbox(
        "Select Theme", 
        ["Dark", "Light", "Auto"], 
        index=["Dark", "Light", "Auto"].index(saved.get("theme", "Dark"))
    )

    # prefill display name: prefer user.csv -> then session -> then saved file
    current_user = st.session_state.get("username", "")
    users, *_ = get_dataframes()

    user_display = ""
    if users is not None and not users.empty and "username" in users.columns:
        row = users[users["username"] == current_user]
        if not row.empty:
            user_display = row.iloc[0].get("display_name", "") or ""
    if not user_display:
        user_display = st.session_state.get("display_name", "") or saved.get("display_name", "")

    display_name = st.text_input("Change Display Name", value=user_display)
    email_notifications = st.checkbox(
        "Enable Email Notifications", 
        value=bool(saved.get("email_notifications", False))
    )

    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    # SAVE BUTTON
    with col1:
        if st.button("Save Settings"):
            new_settings = {
                "theme": theme,
                "display_name": display_name,
                "email_notifications": email_notifications,
            }
            _save_settings(new_settings)
            st.session_state["app_settings"] = new_settings
            st.session_state["display_name"] = display_name

            # Update user table too
            if current_user and users is not None and not users.empty:
                mask = users["username"] == current_user
                if mask.any():
                    users.loc[mask, "display_name"] = display_name
                    quick_save(users=users)
                    st.info(f"Updated display name for {current_user} in users.csv ✅")

            st.success("Settings saved successfully!")

    # RESET BUTTON
    with col2:
        if st.button("Reset to defaults"):
            defaults = {"theme": "Dark", "display_name": "", "email_notifications": False}
            _save_settings(defaults)
            st.session_state["app_settings"] = defaults
            st.session_state["display_name"] = ""
            st.success("Reset to defaults.")
            st.rerun()

    st.markdown("----")
    st.subheader("Current saved settings")
    st.json(_load_settings())
