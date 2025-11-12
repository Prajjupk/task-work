
import streamlit as st
import pandas as pd
from lib.data_manager import get_dataframes, quick_save

def show_files():
    users, tasks, files, audit, comm = get_dataframes()
    st.title('📁 File Tracking')
    if files is None or files.empty:
        st.info('No tracked files yet.')
    else:
        st.dataframe(files.head(50))
    st.markdown('---')
    st.subheader('Upload & Track File (stores metadata only)')
    uploaded = st.file_uploader('Choose a file', accept_multiple_files=False)
    if uploaded is not None:
        meta = {
            'filename': uploaded.name,
            'size': uploaded.size,
            'uploaded_by': st.session_state.get('username','guest'),
            'timestamp': pd.Timestamp.now()
        }
        new = pd.DataFrame([meta])
        files = pd.concat([files, new], ignore_index=True) if files is not None and not files.empty else new
        quick_save(files=files)
        st.success('File meta saved.')
