
import streamlit as st
from lib.data_manager import get_dataframes

def show_audit():
    users, tasks, files, audit, comm = get_dataframes()
    st.title('📝 Audit Logs')
    if audit is None or audit.empty:
        st.info('No audit logs available.')
        return
    st.dataframe(audit.sort_values('timestamp', ascending=False).head(200))
