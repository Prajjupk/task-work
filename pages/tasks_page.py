# pages/tasks_page.py
import streamlit as st
import pandas as pd
from datetime import datetime
from lib.data_manager import get_dataframes, get_next_id, quick_save

def show_tasks():
    """
    Role-aware tasks page:
     - Employee: can view assigned tasks and update status or add a comment
     - Manager: sees team tasks, can reassign, quick-create, bulk-complete
     - Admin: full dataset view with edit/create/delete
    """
    users, tasks, files, audit, comm = get_dataframes()

    # Load session copies first (so changes persist while app runs)
    if 'tasks_df' not in st.session_state:
        st.session_state['tasks_df'] = tasks.copy() if tasks is not None else pd.DataFrame()
    if 'users_df' not in st.session_state:
        st.session_state['users_df'] = users.copy() if users is not None else pd.DataFrame()
    if 'audit_df' not in st.session_state:
        st.session_state['audit_df'] = audit.copy() if audit is not None else pd.DataFrame()

    tasks_df = st.session_state['tasks_df']
    users_df = st.session_state['users_df']
    audit_df = st.session_state['audit_df']

    role = st.session_state.get('role', 'Employee')
    username = st.session_state.get('username', 'guest')

    st.title("Tasks")

    # Role based dataframe
    if role == "Employee":
        df = tasks_df[tasks_df['assigned_to'] == username].copy() if not tasks_df.empty else tasks_df
    elif role == "Manager":
        # get manager team
        team = None
        if not users_df.empty and 'team' in users_df.columns:
            row = users_df[users_df['username'] == username]
            if not row.empty:
                team = row.iloc[0].get('team', None)
        df = tasks_df[tasks_df['team'] == team].copy() if team else tasks_df.iloc[0:0]
    else:  # Admin
        df = tasks_df.copy()

    # Basic table view
    st.subheader("Task List")
    if df.empty:
        st.info("No tasks to display for your role/filters.")
    else:
        st.dataframe(df.sort_values(['priority','due_date'], ascending=[False,True]))

    st.markdown("---")

    # Employee quick update
    if role == "Employee":
        st.subheader("Quick update — change status")
        my_tasks = df
        if my_tasks.empty:
            st.info("No tasks assigned to you.")
        else:
            sel = st.selectbox("Select task", my_tasks['task_id'].astype(str).tolist())
            if sel:
                tid = int(sel)
                task = my_tasks[my_tasks['task_id'] == tid].iloc[0]
                st.write(task['title'])
                new_status = st.selectbox("Status", ["Pending","In Progress","Complete","Blocked"], index=["Pending","In Progress","Complete","Blocked"].index(task['status'] if task['status'] in ["Pending","In Progress","Complete","Blocked"] else "Pending"))
                if st.button("Save status"):
                    idx = st.session_state['tasks_df'][st.session_state['tasks_df']['task_id'] == tid].index
                    if not idx.empty:
                        st.session_state['tasks_df'].loc[idx[0], 'status'] = new_status
                        if new_status == "Complete":
                            st.session_state['tasks_df'].loc[idx[0], 'completion_date'] = pd.to_datetime(datetime.now())
                        else:
                            st.session_state['tasks_df'].loc[idx[0], 'completion_date'] = pd.NaT
                        # log
                        _log_action(audit_df, username, "Status Updated", f"Task {tid} -> {new_status}")
                        quick_save(tasks=st.session_state['tasks_df'], audit=st.session_state['audit_df'])
                        st.success("Saved.")
                    else:
                        st.error("Task index not found.")

    # Manager tools
    elif role == "Manager":
        st.subheader("Manager Controls")
        st.markdown("**Bulk actions**")
        checked = st.multiselect("Select Task IDs", options=df['task_id'].astype(int).tolist())
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Mark selected Complete") and checked:
                updated = 0
                for tid in checked:
                    idx = st.session_state['tasks_df'][st.session_state['tasks_df']['task_id'] == tid].index
                    if not idx.empty:
                        st.session_state['tasks_df'].loc[idx[0], 'status'] = "Complete"
                        st.session_state['tasks_df'].loc[idx[0], 'completion_date'] = pd.to_datetime(datetime.now())
                        updated += 1
                if updated:
                    _log_action(audit_df, username, "Bulk Complete", f"Marked {updated} tasks complete: {checked}")
                    quick_save(tasks=st.session_state['tasks_df'], audit=st.session_state['audit_df'])
                    st.success(f"{updated} tasks updated.")
        with col2:
            if st.button("Reassign selected") and checked:
                members = users_df[users_df['team'] == users_df[users_df['username'] == username]['team'].iloc[0]]['username'].tolist() if not users_df.empty else []
                new_assignee = st.selectbox("New assignee", options=members, key="mgr_reassign")
                if new_assignee:
                    for tid in checked:
                        idx = st.session_state['tasks_df'][st.session_state['tasks_df']['task_id'] == tid].index
                        if not idx.empty:
                            st.session_state['tasks_df'].loc[idx[0], 'assigned_to'] = new_assignee
                    _log_action(audit_df, username, "Bulk Reassign", f"Reassigned {checked} -> {new_assignee}")
                    quick_save(tasks=st.session_state['tasks_df'], audit=st.session_state['audit_df'])
                    st.success("Reassigned.")
        with col3:
            if st.button("Export selected to CSV") and checked:
                out = st.session_state['tasks_df'][st.session_state['tasks_df']['task_id'].isin(checked)]
                st.download_button("Download CSV", out.to_csv(index=False), file_name="selected_tasks.csv")

        st.markdown("---")
        st.subheader("Create task for team member")
        members = []
        if not users_df.empty and 'team' in users_df.columns:
            row = users_df[users_df['username'] == username]
            if not row.empty:
                team = row.iloc[0].get('team', None)
                members = users_df[users_df['team'] == team]['username'].tolist()
        with st.form("mgr_create"):
            title = st.text_input("Title")
            desc = st.text_area("Description")
            assignee = st.selectbox("Assign to", options=members if members else ["None"])
            priority = st.selectbox("Priority", ["High","Medium","Low"], index=1)
            due = st.date_input("Due date")
            submitted = st.form_submit_button("Create task")
            if submitted:
                if not title or not desc or assignee == "None":
                    st.error("Please fill required fields.")
                else:
                    new_id = get_next_id(st.session_state['tasks_df'], 'task_id')
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
                        'created_date': pd.to_datetime(datetime.now()),
                        'completion_date': pd.NaT
                    }
                    st.session_state['tasks_df'] = pd.concat([st.session_state['tasks_df'], pd.DataFrame([new_task])], ignore_index=True)
                    _log_action(audit_df, username, "Task Created (Mgr)", f"Task {new_id} -> {assignee}")
                    quick_save(tasks=st.session_state['tasks_df'], audit=st.session_state['audit_df'])
                    st.success(f"Task {new_id} created.")

    # Admin tools
    else:
        st.subheader("Admin Controls")
        with st.expander("Create new task (admin)"):
            with st.form("admin_create"):
                title = st.text_input("Title")
                desc = st.text_area("Description")
                assignee = st.selectbox("Assign to", options=users_df['username'].tolist() if not users_df.empty else ["admin"])
                priority = st.selectbox("Priority", ["High","Medium","Low"], index=1)
                due = st.date_input("Due date")
                submitted = st.form_submit_button("Create")
                if submitted:
                    new_id = get_next_id(st.session_state['tasks_df'], 'task_id')
                    new_task = {
                        'task_id': new_id,
                        'title': title,
                        'description': desc,
                        'assigned_to': assignee,
                        'assigned_by': username,
                        'due_date': pd.to_datetime(due),
                        'status': 'Pending',
                        'priority': priority,
                        'team': users_df[users_df['username'] == assignee]['team'].iloc[0] if not users_df.empty and 'team' in users_df.columns and not users_df[users_df['username'] == assignee].empty else '',
                        'created_date': pd.to_datetime(datetime.now()),
                        'completion_date': pd.NaT
                    }
                    st.session_state['tasks_df'] = pd.concat([st.session_state['tasks_df'], pd.DataFrame([new_task])], ignore_index=True)
                    _log_action(audit_df, username, "Task Created (Admin)", f"Task {new_id}: {title}")
                    quick_save(tasks=st.session_state['tasks_df'], audit=st.session_state['audit_df'])
                    st.success("Created.")

def _log_action(audit_df, user, action, details):
    """Append to audit_df in session state (creates audit_df if missing)."""
    if 'audit_df' not in st.session_state:
        st.session_state['audit_df'] = audit_df.copy() if audit_df is not None else pd.DataFrame(columns=['log_id','timestamp','user','action','details','category'])
    new_id = get_next_id(st.session_state['audit_df'], 'log_id') if not st.session_state['audit_df'].empty else 1
    new_log = {
        'log_id': new_id,
        'timestamp': pd.Timestamp.now(),
        'user': user,
        'action': action,
        'details': details,
        'category': 'Task Management'
    }
    st.session_state['audit_df'] = pd.concat([st.session_state['audit_df'], pd.DataFrame([new_log])], ignore_index=True)
