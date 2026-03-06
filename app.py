"""
AI-Assisted Data Wrangler & Visualizer
Main application entry point.

A Streamlit application that lets users upload datasets,
interactively clean, transform, and visualize them,
with export of final datasets and transformation reports.
"""

import streamlit as sl
from utils.transform_log import TransformLog


# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────
sl.set_page_config(
    page_title="Data Wrangler & Visualizer",
    page_icon="🔬",
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

    # Initialize transform log
    TransformLog.init_session()


init_session_state()


# ──────────────────────────────────────────────
# Sidebar — Session Info & Controls
# ──────────────────────────────────────────────
with sl.sidebar:
    sl.markdown("## 🔬 Data Wrangler")
    sl.markdown("---")

    # Session info
    if sl.session_state.df_working is not None:
        df = sl.session_state.df_working
        sl.markdown(f"📁 **File:** {sl.session_state.file_name}")
        sl.markdown(f"📊 **Rows:** {len(df):,}")
        sl.markdown(f"📋 **Columns:** {len(df.columns)}")
        sl.markdown(f"🔄 **Transforms:** {len(TransformLog.get_log())}")
        sl.markdown("---")
    else:
        sl.info("No dataset loaded yet. Go to **Upload & Overview** to start.")

    # Reset session button
    if sl.button("🔄 Reset Session", use_container_width=True):
        for key in list(sl.session_state.keys()):
            del sl.session_state[key]
        sl.rerun()

    # AI toggle
    sl.markdown("---")
    sl.session_state.ai_enabled = sl.toggle(
        "🤖 Enable AI Assistant",
        value=sl.session_state.get("ai_enabled", False),
    )


# ──────────────────────────────────────────────
# Main Content — Landing Page
# ──────────────────────────────────────────────
sl.title("🔬 AI-Assisted Data Wrangler & Visualizer")
sl.markdown(
    """
    Welcome to the **Data Wrangler & Visualizer** — your interactive data 
    preparation studio. Upload a dataset and take it through a complete 
    cleaning, transformation, and visualization pipeline.
    """
)

sl.markdown("---")

# Feature cards
col1, col2, col3, col4 = sl.columns(4)

with col1:
    sl.markdown("### 📤 Upload")
    sl.markdown(
        "Upload CSV, Excel, or JSON files. "
        "Get instant data profiling and overview."
    )

with col2:
    sl.markdown("### 🧹 Clean")
    sl.markdown(
        "Handle missing values, duplicates, outliers. "
        "Normalize and transform your data."
    )

with col3:
    sl.markdown("### 📊 Visualize")
    sl.markdown(
        "Build interactive charts — histograms, scatter, "
        "box plots, heatmaps, and more."
    )

with col4:
    sl.markdown("### 📥 Export")
    sl.markdown(
        "Download cleaned data, transformation reports, "
        "and reproducible recipes."
    )

sl.markdown("---")

# Quick start guide
with sl.expander("🚀 Quick Start Guide", expanded=True):
    sl.markdown(
        """
        1. **Navigate** to **Upload & Overview** in the sidebar
        2. **Upload** your dataset (CSV, Excel, or JSON)
        3. **Review** the data profile — types, missing values, duplicates
        4. **Go to** **Cleaning Studio** to apply transformations
        5. **Build** visualizations in the **Visualization Builder**
        6. **Export** your cleaned data and reports from **Export & Report**
        
        💡 **Tip:** Enable the **AI Assistant** in the sidebar for 
        intelligent suggestions and natural language commands.
        """
    )

# Dataset status
if sl.session_state.df_working is not None:
    sl.success(
        f"✅ Dataset loaded: **{sl.session_state.file_name}** — "
        f"{len(sl.session_state.df_working):,} rows × "
        f"{len(sl.session_state.df_working.columns)} columns"
    )
else:
    sl.info("👈 Start by uploading a dataset from the **Upload & Overview** page.")
