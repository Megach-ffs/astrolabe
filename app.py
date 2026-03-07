import streamlit as sl

sl.set_page_config(
        layout="wide"
        )

if "file" not in sl.session_state:

    sl.session_state["file"] = None
    sl.session_state["filename"] = None

main_page = sl.Page("frontend/main.py", title="Astrolabe", icon="💫")
page_1 = sl.Page("frontend/page1.py", title="Upload and Overview")
page_2 = sl.Page("frontend/page2.py", title="Cleaning and Preparation")
page_3 = sl.Page("frontend/page3.py", title="Visualization Builder")
page_4 = sl.Page("frontend/page4.py", title="Export and Report")

app = sl.navigation([main_page, page_1, page_2, page_3, page_4])

with sl.sidebar:
    # sl.markdown("## Data Wrangler app")
    # sl.markdown("---")

    sl.markdown(f"working file: {sl.session_state.filename}")
    sl.markdown("something else")


app.run()
