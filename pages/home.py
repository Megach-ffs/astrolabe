"""
Home — Landing Page

Welcome page with feature overview and quick-start guide.
"""

import streamlit as sl


sl.title(":material/science: AI-Assisted Data Wrangler & Visualizer")
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
    sl.markdown("### :material/upload: Upload")
    sl.markdown(
        "Upload CSV, Excel, or JSON files. "
        "Get instant data profiling and overview."
    )

with col2:
    sl.markdown("### :material/cleaning_services: Clean")
    sl.markdown(
        "Handle missing values, duplicates, outliers. "
        "Normalize and transform your data."
    )

with col3:
    sl.markdown("### :material/area_chart: Visualize")
    sl.markdown(
        "Build interactive charts — histograms, scatter, "
        "box plots, heatmaps, and more."
    )

with col4:
    sl.markdown("### :material/export_notes: Export")
    sl.markdown(
        "Download cleaned data, transformation reports, "
        "and reproducible recipes."
    )

sl.markdown("---")

# Quick start guide
with sl.expander(":material/rocket_launch: Quick Start Guide", expanded=True):
    sl.markdown(
        """
        1. **Navigate** to **Upload & Overview** in the sidebar
        2. **Upload** your dataset (CSV, Excel, or JSON)
        3. **Review** the data profile — types, missing values, duplicates
        4. **Go to** **Cleaning Studio** to apply transformations
        5. **Build** visualizations in the **Visualization Builder**
        6. **Export** your cleaned data and reports from **Export & Report**

        :material/lightbulb: **Tip:** Enable the **AI Assistant** in the sidebar for
        intelligent suggestions and natural language commands.
        """
    )

# Dataset status
if sl.session_state.df_working is not None:
    sl.success(
        f":material/check_circle: Dataset loaded: **{sl.session_state.file_name}** — "
        f"{len(sl.session_state.df_working):,} rows × "
        f"{len(sl.session_state.df_working.columns)} columns"
    )
else:
    sl.info(":material/arrow_back: Start by uploading a dataset from the **Upload & Overview** page.")
