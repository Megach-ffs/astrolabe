"""
Page A — Upload & Overview

Upload a dataset (CSV, Excel, JSON, or Google Sheets) and get
instant profiling: shape, types, missing values, duplicates,
and summary statistics.
"""

import streamlit as sl
import pandas as pd
import matplotlib.pyplot as plt
# import numpy as np  # will be used in future phases

from utils.data_loader import load_uploaded_file, load_google_sheet
from utils.profiler import profile_dataframe
from utils.transform_log import TransformLog
from utils import ai_assistant


sl.title(":material/upload: Upload & Overview")
sl.markdown("Upload your dataset to get started. The app will automatically profile your data.")


# ──────────────────────────────────────────────
# File Upload Section
# ──────────────────────────────────────────────
upload_tab, sheets_tab = sl.tabs([":material/create_new_folder: File Upload", ":material/folder_open: Google Sheets"])

with upload_tab:
    uploaded_file = sl.file_uploader(
        "Choose a file",
        type=["csv", "xlsx", "xls", "json"],
        help="Supported formats: CSV, Excel (.xlsx/.xls), JSON",
    )

    if uploaded_file is not None:
        # Only reload if it's a new file
        if sl.session_state.file_name != uploaded_file.name:
            try:
                df = load_uploaded_file(uploaded_file)
                sl.session_state.df_original = df.copy()
                sl.session_state.df_working = df.copy()
                sl.session_state.file_name = uploaded_file.name
                # Reset transform log for new file
                TransformLog.reset_all(df)
                sl.success(f":material/check_circle: Loaded **{uploaded_file.name}** — {len(df):,} rows × {len(df.columns)} columns")
            except ValueError as e:
                sl.error(f":material/error: {e}")
            except Exception as e:
                sl.error(f":material/error: Failed to load file: {e}")

with sheets_tab:
    sl.markdown("Connect to a Google Sheet (requires service account credentials in `.streamlit/secrets.toml`).")
    sheet_url = sl.text_input(
        "Google Sheet URL",
        placeholder="https://docs.google.com/spreadsheets/d/...",
    )
    if sl.button(":material/folder_open: Load from Google Sheets", disabled=not sheet_url):
        try:
            df = load_google_sheet(sheet_url)
            sl.session_state.df_original = df.copy()
            sl.session_state.df_working = df.copy()
            sl.session_state.file_name = "Google Sheet"
            TransformLog.reset_all(df)
            sl.success(f":material/check_circle: Loaded Google Sheet — {len(df):,} rows × {len(df.columns)} columns")
        except ValueError as e:
            sl.error(f":material/error: {e}")
        except Exception as e:
            sl.error(f":material/error: Failed to load Google Sheet: {e}")


# ──────────────────────────────────────────────
# Data Profiling (only if data is loaded)
# ──────────────────────────────────────────────
if sl.session_state.df_working is not None:
    df = sl.session_state.df_working
    profile = profile_dataframe(df)

    sl.markdown("---")

    # ── Metric Cards ──────────────────────────
    sl.subheader(":material/analytics: Dataset Overview")
    col1, col2, col3, col4 = sl.columns(4)

    total_missing = int(df.isnull().sum().sum())
    total_cells = int(df.shape[0] * df.shape[1])
    missing_pct = round(total_missing / total_cells * 100, 1) if total_cells > 0 else 0

    with col1:
        sl.metric("Rows", f"{profile['shape'][0]:,}")
    with col2:
        sl.metric("Columns", f"{profile['shape'][1]}")
    with col3:
        sl.metric("Missing Values", f"{total_missing:,}", delta=f"{missing_pct}%", delta_color="inverse")
    with col4:
        sl.metric(
            "Duplicate Rows",
            f"{profile['duplicates']['count']:,}",
            delta=f"{profile['duplicates']['percentage']}%",
            delta_color="inverse",
        )

    sl.markdown("---")

    # ── Column Info Table ─────────────────────
    sl.subheader(":material/info: Column Information")
    col_df = pd.DataFrame(profile["columns"])
    col_df.columns = ["Name", "Type", "Non-Null", "Null Count", "Null %", "Unique"]

    sl.dataframe(
        col_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Null %": sl.column_config.ProgressColumn(
                "Null %",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )

    sl.markdown("---")

    # ── Summary Statistics ────────────────────
    sl.subheader(":material/table_chart: Summary Statistics")
    stat_tab1, stat_tab2 = sl.tabs(["Numeric", "Categorical"])

    with stat_tab1:
        if not profile["numeric_summary"].empty:
            sl.dataframe(
                profile["numeric_summary"].round(3),
                use_container_width=True,
            )
        else:
            sl.info("No numeric columns found.")

    with stat_tab2:
        if not profile["categorical_summary"].empty:
            sl.dataframe(
                profile["categorical_summary"],
                use_container_width=True,
            )
        else:
            sl.info("No categorical columns found.")

    sl.markdown("---")

    # ── Missing Values Visualization ──────────
    sl.subheader(":material/warning: Missing Values")

    missing_df = profile["missing"]
    if not missing_df.empty:
        fig, ax = plt.subplots(figsize=(10, max(3, len(missing_df) * 0.4)))

        # Sort by missing percentage
        missing_sorted = missing_df.sort_values("Missing %", ascending=True)

        # Color-code: green <5%, yellow 5-20%, red >20%
        colors = []
        for pct in missing_sorted["Missing %"]:
            if pct < 5:
                colors.append("#4CAF50")  # green
            elif pct < 20:
                colors.append("#FFC107")  # yellow
            else:
                colors.append("#F44336")  # red

        bars = ax.barh(
            missing_sorted["Column"],
            missing_sorted["Missing %"],
            color=colors,
            edgecolor="white",
            linewidth=0.5,
        )

        # Add value labels on bars
        for bar, count, pct in zip(
            bars,
            missing_sorted["Missing Count"],
            missing_sorted["Missing %"],
        ):
            ax.text(
                bar.get_width() + 0.5,
                bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}% ({int(count)})",
                va="center",
                fontsize=9,
                color="#FAFAFA",
            )

        ax.set_xlabel("Missing %", color="#FAFAFA")
        ax.set_title("Missing Values by Column", color="#FAFAFA", fontsize=14)
        ax.set_facecolor("#0E1117")
        fig.patch.set_facecolor("#0E1117")
        ax.tick_params(colors="#FAFAFA")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color("#333")
        ax.spines["left"].set_color("#333")
        ax.set_xlim(0, max(missing_sorted["Missing %"]) * 1.3)

        sl.pyplot(fig)
        plt.close(fig)

        # Missing values table
        with sl.expander(":material/analytics: Missing Values Details"):
            sl.dataframe(
                missing_df,
                use_container_width=True,
                hide_index=True,
            )
    else:
        sl.success(":material/check_circle: No missing values found in the dataset!")

    sl.markdown("---")

    # ── Data Preview ──────────────────────────
    sl.subheader(":material/visibility: Data Preview")

    preview_col1, preview_col2 = sl.columns([1, 3])
    with preview_col1:
        preview_mode = sl.radio("View", ["Head", "Tail"], horizontal=True)
        n_rows = sl.slider("Rows to display", min_value=5, max_value=min(100, len(df)), value=10)

    if preview_mode == "Head":
        sl.dataframe(df.head(n_rows), use_container_width=True)
    else:
        sl.dataframe(df.tail(n_rows), use_container_width=True)

    # ── AI Data Dictionary (Bonus) ────────────
    if sl.session_state.get("ai_enabled"):
        if ai_assistant.is_available():
            sl.markdown("---")
            sl.subheader(":material/robot: AI Data Dictionary")
            sl.caption("Generate a data dictionary summarizing your columns, inferred types, and potential issues.")
            
            c1, c2, _ = sl.columns([1, 1, 3])
            with c1:
                if sl.button("Generate Dictionary", key="ai_dict_btn", use_container_width=True):
                    with sl.status("🤖 Analyzing data and generating dictionary...", expanded=True) as status:
                        sl.write("Sending data context to Gemini...")
                        dictionary_markdown = ai_assistant.generate_data_dictionary(df)
                        if dictionary_markdown and not dictionary_markdown.startswith("Error"):
                            sl.session_state.ai_data_dict = dictionary_markdown
                            status.update(label=":material/check_circle: Data Dictionary Generated!", state="complete")
                        else:
                            status.update(label=":material/error: Failed", state="error")
                            sl.error(f":material/error: {dictionary_markdown}")
            
            with c2:
                if sl.session_state.get("ai_data_dict"):
                    if sl.button(":material/delete: Clear", key="clear_ai_dict", use_container_width=True):
                        del sl.session_state["ai_data_dict"]
                        sl.rerun()

            if sl.session_state.get("ai_data_dict"):
                with sl.container(border=True):
                    sl.markdown(sl.session_state.ai_data_dict)
                
                # Action buttons
                act1, act2, act3, _ = sl.columns([2, 2, 2, 2])
                with act1:
                    sl.download_button(
                        ":material/download: Download (MD)",
                        data=sl.session_state.ai_data_dict.encode("utf-8"),
                        file_name="data_dictionary.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                with act2:
                    if sl.button(":material/chat: Discuss in AI Chat", use_container_width=True):
                        sl.session_state.ai_chat_initial_prompt = "I just generated a Data Dictionary. Can you help me analyze these findings and suggest next steps?"
                        sl.switch_page("pages/ai_chat.py")
                with act3:
                    if sl.button(":material/cleaning_services: Clean Data", use_container_width=True):
                        sl.session_state.ai_clean_initial_prompt = "Based on the Data Dictionary, fix the most critical data quality issues automatically."
                        sl.switch_page("pages/cleaning_studio.py")
        else:
            sl.markdown("---")
            sl.warning(":material/error: **AI Assistant Unavailable**")
            sl.info("The Gemini API is not configured or is currently unresponsive. Please check your API key in `.streamlit/secrets.toml` or verify your quota.")

else:
    # No data loaded — show instructions
    sl.markdown("---")
    sl.info(":material/arrow_upward: Upload a file above or connect to Google Sheets to get started.")

    with sl.expander(":material/description: Supported Formats"):
        sl.markdown(
            """
            | Format | Extension | Notes |
            |--------|-----------|-------|
            | CSV | `.csv` | Comma-separated values |
            | Excel | `.xlsx`, `.xls` | First sheet is loaded |
            | JSON | `.json` | Array of objects or column-oriented dict |
            | Google Sheets | URL | Requires service account (bonus feature) |
            """
        )

    with sl.expander(":material/dataset: Sample Datasets"):
        sl.markdown(
            """
            Two sample datasets are included in the `sample_data/` directory:

            1. **ecommerce_orders.csv** — ~1,500 rows, 10 columns
               *E-commerce orders with dirty prices, mixed categories, missing values*

            2. **weather_stations.xlsx** — ~1,200 rows, 9 columns
               *Weather data with sentinel outliers, missing values, rare categories*
            """
        )
