import streamlit as sl
import pandas as pd

@sl.cache_data
def load_file(upload_file):

    df = pd.read_csv(upload_file)
    sl.session_state["file"] = df
    sl.session_state["filename"] = upload_file.name

    

sl.set_page_config(
        page_title = "Upload and Overview",
        )

sl.markdown(
        """
        # Upload and Overview
        This is the page used to upload or share your data for future analysis
        """)

upload_file = sl.file_uploader(
    "Upload your file"
    )

if upload_file:
    load_file(upload_file)

if sl.session_state.file is not None:
    sl.markdown(
       f"""
        Currently, you are seeing file: {sl.session_state.filename}
        """
        )
    df = sl.session_state.file
    sl.write(df)  


