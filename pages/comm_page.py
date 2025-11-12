
import streamlit as st
from lib.data_manager import get_dataframes, quick_save
from datetime import datetime
import pandas as pd

def show_comm():
    users, tasks, files, audit, comm = get_dataframes()
    st.title('💬 Communication Hub')
    if comm is None:
        comm = pd.DataFrame(columns=['msg_id','timestamp','user','to','message'])
    st.subheader('Send a team message')
    with st.form('msg_form'):
        to = st.text_input('To (username or All)', value='All')
        msg = st.text_area('Message')
        send = st.form_submit_button('Send')
        if send and msg:
            row = {
                'msg_id': (comm['msg_id'].max()+1 if not comm.empty else 1),
                'timestamp': datetime.now(),
                'user': st.session_state.get('username','guest'),
                'to': to,
                'message': msg
            }
            comm = pd.concat([comm, pd.DataFrame([row])], ignore_index=True)
            quick_save(comm=comm)
            st.success('Message sent')
            st.experimental_rerun()
    st.markdown('---')
    st.subheader('Recent messages')
    if not comm.empty:
        st.dataframe(comm.sort_values('timestamp', ascending=False).head(50))
    else:
        st.info('No messages yet.')
