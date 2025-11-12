# pages/analytics_page.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from lib.data_manager import get_dataframes

def show_analytics():
    users, tasks, files, audit, comm = get_dataframes()
    st.title("📊 Analytics Dashboard")

    if tasks is None or tasks.empty:
        st.info("No tasks available for analysis.")
        return

    # --- KPI overview ---
    total = len(tasks)
    completed = len(tasks[tasks["status"] == "Complete"])
    pending = len(tasks[tasks["status"] == "Pending"])
    in_progress = len(tasks[tasks["status"] == "In Progress"])
    blocked = len(tasks[tasks["status"] == "Blocked"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tasks", total)
    c2.metric("Completed", completed)
    c3.metric("Pending", pending)
    c4.metric("In Progress", in_progress)

    st.markdown("---")

    # --- Tasks by Priority ---
    st.subheader("📈 Tasks by Priority")

    by_priority = tasks.groupby("priority").size().reindex(["High", "Medium", "Low"]).fillna(0)
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    bars = ax1.bar(by_priority.index, by_priority.values)
    ax1.set_title("Task Count by Priority", fontsize=12, weight="bold")
    ax1.set_ylabel("Number of Tasks")
    ax1.bar_label(bars, fmt="%d", label_type="edge", padding=3)
    st.pyplot(fig1)

    st.markdown("---")

    # --- Task Status Distribution ---
    st.subheader("🥧 Task Status Distribution")

    status_counts = (
        tasks["status"]
        .value_counts()
        .reindex(["Pending", "In Progress", "Complete", "Blocked"])
        .fillna(0)
    )

    fig2, ax2 = plt.subplots(figsize=(5, 5))
    wedges, texts, autotexts = ax2.pie(
        status_counts,
        labels=status_counts.index,
        autopct=lambda p: f"{p:.1f}%" if p > 0 else "",
        startangle=90,
        pctdistance=0.8,
        labeldistance=1.1,
        wedgeprops={"edgecolor": "white"},
        textprops={"fontsize": 10},
    )
    ax2.set_title("Overall Task Status Distribution", fontsize=12, weight="bold")
    ax2.axis("equal")  # Equal aspect ratio ensures a perfect circle
    st.pyplot(fig2)

    st.markdown("---")

    # --- Completion rate by assignee ---
    st.subheader("📋 Completion Rate by Assignee")

    comp = tasks[tasks["status"] == "Complete"].groupby("assigned_to").size()
    total = tasks.groupby("assigned_to").size()
    rate = (comp / total).fillna(0).sort_values(ascending=False)

    if not rate.empty:
        rate_df = pd.DataFrame(
            {"User": rate.index, "Completion Rate (%)": (rate * 100).round(2)}
        )

        fig3, ax3 = plt.subplots(figsize=(6, 4))
        bars2 = ax3.barh(rate_df["User"], rate_df["Completion Rate (%)"], color="skyblue")
        ax3.bar_label(bars2, fmt="%.1f%%", padding=3)
        ax3.set_xlabel("Completion Rate (%)")
        ax3.set_title("User Completion Rates", fontsize=12, weight="bold")
        ax3.invert_yaxis()
        st.pyplot(fig3)
    else:
        st.info("No completed tasks yet to calculate completion rates.")

    st.markdown("---")
    st.caption("📅 Analytics data auto-generated from your task records.")
