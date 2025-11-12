import streamlit as st
import pandas as pd
from lib.data_manager import get_dataframes

def show_reports():
    """Generate and view summarized task reports."""
    st.title("📑 Reports")
    st.markdown("Overview and exports of your task data.")

    users, tasks, files, audit, comm = get_dataframes()

    if tasks is None or tasks.empty:
        st.info("No task data available to generate reports.")
        return

    # --- Filter options ---
    col1, col2 = st.columns(2)
    selected_user = col1.selectbox("Filter by Assignee", ["All"] + sorted(tasks['assigned_to'].unique().tolist()))
    selected_status = col2.selectbox("Filter by Status", ["All"] + sorted(tasks['status'].unique().tolist()))

    filtered = tasks.copy()
    if selected_user != "All":
        filtered = filtered[filtered["assigned_to"] == selected_user]
    if selected_status != "All":
        filtered = filtered[filtered["status"] == selected_status]

    st.markdown(f"### Showing {len(filtered)} Tasks")

    st.dataframe(filtered, use_container_width=True)

    # --- Simple summary report ---
    st.markdown("---")
    st.subheader("📊 Summary by Priority")
    summary = filtered.groupby("priority").size().reindex(["High", "Medium", "Low"]).fillna(0)
    st.bar_chart(summary)

    # --- Export to CSV ---
    csv_data = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Report as CSV",
        data=csv_data,
        file_name="task_report.csv",
        mime="text/csv"
    )
