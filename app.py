import streamlit as sl

main_page = sl.Page("frontend/main.py", title="Astrolabe", icon="💫")
page_1 = sl.Page("frontend/page1.py", title="Page 1 for now", icon="👌")
page_2 = sl.Page("frontend/page2.py", title="Page 2 for now")
page_3 = sl.Page("frontend/page3.py", title="Page 3 for now")
page_4 = sl.Page("frontend/page4.py", title="Page 4 for now")

app = sl.navigation([main_page, page_1, page_2, page_3, page_4])

with sl.sidebar:
    sl.markdown("## Data Wrangler app")
    sl.markdown("---")

    sl.markdown("something")
    sl.markdown("something else")


app.run()
