# pages/home_page.py
import streamlit as st
import pandas as pd
from lib.data_manager import get_dataframes

def show_home():
    """
    Role-aware dashboard:
     - Admin: global KPIs + recent audit
     - Manager: team KPIs, tasks by member, quick create for team
     - Employee: personal tasks summary + quick status update
    """
    users, tasks, files, audit, comm = get_dataframes()

    # Prefer session copies if pages updated state elsewhere
    tasks_df = st.session_state.get("tasks_df", tasks.copy() if tasks is not None else pd.DataFrame())
    users_df = st.session_state.get("users_df", users.copy() if users is not None else pd.DataFrame())

    role = st.session_state.get("role", "Employee")
    username = st.session_state.get("username", "guest")

    st.header("Overview")

    # Shared KPIs
    total_tasks = 0 if tasks_df.empty else len(tasks_df)
    pending = 0 if tasks_df.empty else len(tasks_df[tasks_df['status']=='Pending'])
    complete = 0 if tasks_df.empty else len(tasks_df[tasks_df['status']=='Complete'])

    # Admin dashboard
    if role == "Admin":
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Tasks", total_tasks)
        c2.metric("Pending", pending)
        c3.metric("Completed", complete)

        st.markdown("---")
        st.subheader("Recent Activity (audit)")
        if audit is None or audit.empty:
            st.info("No audit logs yet.")
        else:
            st.dataframe(audit.sort_values("timestamp", ascending=False).head(10)[["timestamp","user","action","details"]])

    # Manager dashboard
    elif role == "Manager":
        st.subheader(f"Team overview — Manager: {username}")

        # detect manager's team from users_df
        team = None
        if not users_df.empty and 'username' in users_df.columns and 'team' in users_df.columns:
            row = users_df[users_df['username'] == username]
            if not row.empty:
                team = row.iloc[0].get('team', None)

        if not team:
            st.warning("No team set for you in users.csv. Set the 'team' column for your user.")
            team_members = []
        else:
            team_members = users_df[users_df['team'] == team]['username'].tolist()

        team_tasks = tasks_df[tasks_df['team'] == team] if team else tasks_df.iloc[0:0]

        t_total = len(team_tasks)
        t_pending = len(team_tasks[team_tasks['status']=='Pending'])
        t_complete = len(team_tasks[team_tasks['status']=='Complete'])

        c1, c2, c3 = st.columns(3)
        c1.metric(f"Team ({team}) Tasks", t_total)
        c2.metric("Pending (team)", t_pending)
        c3.metric("Completed (team)", t_complete)

        st.markdown("---")
        st.subheader("Tasks by member")
        if team_members:
            counts = team_tasks.groupby('assigned_to').size().reindex(team_members).fillna(0).astype(int)
            st.table(counts.rename("task_count").to_frame())
        else:
            st.info("No team members detected.")

        st.markdown("---")
        st.subheader("Quick: Create task for team member")
        with st.form("mgr_quick_create"):
            title = st.text_input("Title")
            desc = st.text_area("Description")
            assignee = st.selectbox("Assign to", options=team_members if team_members else ["None"])
            priority = st.selectbox("Priority", ["High","Medium","Low"], index=1)
            due = st.date_input("Due date")
            submit = st.form_submit_button("Create task")
            if submit:
                if not title or not desc or not assignee or assignee == "None":
                    st.error("Title, description and assignee required.")
                else:
                    # create new task via session state (update tasks_df)
                    new_id = _get_next_task_id(tasks_df)
                    new_task = {
                        'task_id': new_id,
                        'title': title,
                        'description': desc,
                        'assigned_to': assignee,
                        'assigned_by': username,
                        'due_date': pd.to_datetime(due),
                        'status': 'Pending',
                        'priority': priority,
                        'team': team,
                        'created_date': pd.Timestamp.now(),
                        'completion_date': pd.NaT
                    }
                    st.session_state['tasks_df'] = pd.concat([tasks_df, pd.DataFrame([new_task])], ignore_index=True)
                    # persist via lib.data_manager.quick_save if desired (not called automatically here)
                    st.success(f"Created task {new_id} for {assignee}.")

    # Employee dashboard
    else:
        st.subheader(f"Welcome, {username} — Your Tasks")

        my_tasks = tasks_df[tasks_df['assigned_to'] == username] if not tasks_df.empty else tasks_df

        my_total = len(my_tasks)
        my_pending = len(my_tasks[my_tasks['status'] == 'Pending'])
        my_complete = len(my_tasks[my_tasks['status'] == 'Complete'])

        c1, c2, c3 = st.columns(3)
        c1.metric("Your Tasks", my_total)
        c2.metric("Pending", my_pending)
        c3.metric("Completed", my_complete)

        st.markdown("---")
        st.subheader("Your open tasks")
        if my_tasks.empty:
            st.info("No tasks assigned to you.")
        else:
            # Small interactive list: pick a task to update status
            rows = my_tasks.sort_values(['priority','due_date'], ascending=[False,True])
            sel_options = rows.apply(lambda r: f"[{int(r['task_id'])}] {r['title']} — {r['status']}", axis=1).tolist()
            selected = st.selectbox("Select task to update", ["—"] + sel_options)
            if selected != "—":
                tid = int(selected.split("]")[0].lstrip("["))
                task_row = rows[rows['task_id'] == tid].iloc[0]
                st.markdown(f"**{task_row['title']}**")
                st.write(task_row['description'])
                new_status = st.selectbox("Update status", ["Pending","In Progress","Complete","Blocked"], index=["Pending","In Progress","Complete","Blocked"].index(task_row['status'] if task_row['status'] in ["Pending","In Progress","Complete","Blocked"] else "Pending"))
                if st.button("Apply status"):
                    idx = st.session_state.get('tasks_df', tasks_df).index[st.session_state.get('tasks_df', tasks_df)['task_id'] == tid]
                    if not idx.empty:
                        st.session_state['tasks_df'].loc[idx[0], 'status'] = new_status
                        if new_status == "Complete":
                            st.session_state['tasks_df'].loc[idx[0], 'completion_date'] = pd.Timestamp.now()
                        else:
                            st.session_state['tasks_df'].loc[idx[0], 'completion_date'] = pd.NaT
                        st.success("Status updated.")
                    else:
                        st.error("Could not find task index to update.")

def _get_next_task_id(tasks_df):
    """Helper: derive next integer task id from provided DataFrame."""
    try:
        if tasks_df is None or tasks_df.empty or 'task_id' not in tasks_df.columns:
            return 1
        vals = pd.to_numeric(tasks_df['task_id'], errors='coerce').dropna().astype(int)
        return int(vals.max()) + 1 if not vals.empty else 1
    except Exception:
        return 1
