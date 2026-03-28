"""
AI-Assisted Data Wrangler & Visualizer
Main application entry point.

Uses sl.Page() + sl.navigation() for centralized page management.
Sidebar and session state are defined here and apply to ALL pages.
"""

import streamlit as sl
from utils.transform_log import TransformLog


# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────
sl.set_page_config(
    page_title="Astrolabe",
    page_icon=":material/biotech:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ──────────────────────────────────────────────
# Session State Initialization
# ──────────────────────────────────────────────
def init_session_state():
    """Initialize all session state keys with default values."""
    defaults = {
        "df_original": None,
        "df_working": None,
        "file_name": None,
        "ai_enabled": False,
    }
    for key, value in defaults.items():
        if key not in sl.session_state:
            sl.session_state[key] = value
    TransformLog.init_session()


init_session_state()


# ──────────────────────────────────────────────
# Navigation — sl.Page() API
# ──────────────────────────────────────────────
home_page = sl.Page("pages/home.py", title="Home", icon=":material/home:", default=True)
upload_page = sl.Page("pages/upload_overview.py", title="Upload & Overview", icon=":material/upload:")
cleaning_page = sl.Page("pages/cleaning_studio.py", title="Cleaning Studio", icon=":material/mop:")
viz_page = sl.Page("pages/visualization.py", title="Visualization", icon=":material/area_chart:")
chat_page = sl.Page("pages/ai_chat.py", title="AI Chat", icon=":material/chat:")
export_page = sl.Page("pages/export_report.py", title="Export & Report", icon=":material/file_export:")

pg = sl.navigation([home_page, upload_page, cleaning_page, viz_page, chat_page, export_page])


# ──────────────────────────────────────────────
# Sidebar — Runs on EVERY page automatically
# ──────────────────────────────────────────────
with sl.sidebar:
    # Session info
    if sl.session_state.df_working is not None:
        df = sl.session_state.df_working
        sl.markdown(f":material/document_scanner: **File:** {sl.session_state.file_name}")
        sl.markdown(f":material/table_rows_narrow: **Rows:** {len(df):,}")
        sl.markdown(f":material/view_column_2: **Columns:** {len(df.columns)}")
        sl.markdown(f":material/autorenew: **Transforms:** {len(TransformLog.get_log())}")
        sl.markdown("---")
    else:
        sl.info("No dataset loaded yet. Go to **Upload & Overview** to start.")

    # Reset session button
    if sl.button(":material/refresh: Reset Session", use_container_width=True):
        for key in list(sl.session_state.keys()):
            del sl.session_state[key]
        sl.rerun()

    # AI toggle
    sl.markdown("---")
    sl.session_state.ai_enabled = sl.toggle(
        ":material/robot: Enable AI Assistant",
        value=sl.session_state.get("ai_enabled", False),
    )


# ──────────────────────────────────────────────
# Run the selected page
# ──────────────────────────────────────────────
pg.run()
