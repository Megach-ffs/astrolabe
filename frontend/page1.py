import streamlit as sl
import pandas as pd

@sl.cache_data
def load_file(upload_file):

    df = pd.read_csv(upload_file)
    sl.session_state["file"] = df
    sl.session_state["filename"] = upload_file.name

def get_overview(df):

    composed_overview = {
        "shape":None,
        "columns":None,
        "summary_stats":{
            "numeric":None,
            "categorical":None
            },
        "missing_values":None,
        "duplicates":None,
        }

    composed_overview["shape"] = df.shape
    composed_overview["columns"] = df.dtypes
    composed_overview["summary_stats"]["numeric"] = df.describe() 
    composed_overview["summary_stats"]["categorical"] = df.describe(include=["object", "category"])
    composed_overview["missing_values"] = [df.isnull().sum(), df.isnull().sum()/len(df)*100]
    composed_overview["duplicates"] = [df[df.duplicated(keep=False)].sort_values(by=list(df.columns)),
                                       df.duplicated().sum()]


    return composed_overview
    

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

    sl.markdown(
        """
        ---
        # Overview
        Here you can see basic overview of the data set:
        - shapes
        - column and datatypes names
        - basic summary statistics
        - missing values by each column
        - duplicates count

        ## Shape
        """
        )

    overview = get_overview(df)
    # sl.write(overview["shape"])
    sl.markdown(
        f"""
        ### Columns: {overview["shape"][0]} --- Rows:    {overview["shape"][1]}
        """
        )

    sl.markdown(
        """
        ## Columns Information
        """
        )
    
    cols_info = pd.DataFrame(overview["columns"])
    cols_info.columns = ["DataType"]

    sl.write(cols_info)

    sl.markdown(
        """
        ## Summary Statistics
        ### Numeric Statistics
        """
        )
    sl.write(overview["summary_stats"]["numeric"])

    sl.markdown("### Categorical Statistics")
    sl.write(overview["summary_stats"]["categorical"])
    
    sl.markdown(
        f"""
        ### Missing Values
        """
        )

    sl.write(overview["missing_values"][0])
    sl.write(overview["missing_values"][1])

    sl.markdown(f"""
        ### Duplicates: {overview["duplicates"][1]}
        """)
    sl.write(overview["duplicates"][0])
    




