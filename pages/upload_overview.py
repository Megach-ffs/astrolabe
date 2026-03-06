"""
Page A — Upload & Overview

Upload a dataset (CSV, Excel, JSON, or Google Sheets) and get
instant profiling: shape, types, missing values, duplicates,
and summary statistics.
"""

import streamlit as sl
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from utils.data_loader import load_uploaded_file, load_google_sheet
from utils.profiler import profile_dataframe
from utils.transform_log import TransformLog


sl.title("📤 Upload & Overview")
sl.markdown("Upload your dataset to get started. The app will automatically profile your data.")


# ──────────────────────────────────────────────
# File Upload Section
# ──────────────────────────────────────────────
upload_tab, sheets_tab = sl.tabs(["📁 File Upload", "📊 Google Sheets"])

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
                sl.success(f"✅ Loaded **{uploaded_file.name}** — {len(df):,} rows × {len(df.columns)} columns")
            except ValueError as e:
                sl.error(f"❌ {e}")
            except Exception as e:
                sl.error(f"❌ Failed to load file: {e}")

with sheets_tab:
    sl.markdown("Connect to a Google Sheet (requires service account credentials in `.streamlit/secrets.toml`).")
    sheet_url = sl.text_input(
        "Google Sheet URL",
        placeholder="https://docs.google.com/spreadsheets/d/...",
    )
    if sl.button("🔗 Load from Google Sheets", disabled=not sheet_url):
        try:
            df = load_google_sheet(sheet_url)
            sl.session_state.df_original = df.copy()
            sl.session_state.df_working = df.copy()
            sl.session_state.file_name = "Google Sheet"
            TransformLog.reset_all(df)
            sl.success(f"✅ Loaded Google Sheet — {len(df):,} rows × {len(df.columns)} columns")
        except ValueError as e:
            sl.error(f"❌ {e}")
        except Exception as e:
            sl.error(f"❌ Failed to load Google Sheet: {e}")


# ──────────────────────────────────────────────
# Data Profiling (only if data is loaded)
# ──────────────────────────────────────────────
if sl.session_state.df_working is not None:
    df = sl.session_state.df_working
    profile = profile_dataframe(df)

    sl.markdown("---")

    # ── Metric Cards ──────────────────────────
    sl.subheader("📊 Dataset Overview")
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
    sl.subheader("📋 Column Information")
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
    sl.subheader("📈 Summary Statistics")
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
    sl.subheader("⚠️ Missing Values")

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
        with sl.expander("📊 Missing Values Details"):
            sl.dataframe(
                missing_df,
                use_container_width=True,
                hide_index=True,
            )
    else:
        sl.success("✅ No missing values found in the dataset!")

    sl.markdown("---")

    # ── Data Preview ──────────────────────────
    sl.subheader("👁️ Data Preview")

    preview_col1, preview_col2 = sl.columns([1, 3])
    with preview_col1:
        preview_mode = sl.radio("View", ["Head", "Tail"], horizontal=True)
        n_rows = sl.slider("Rows to display", min_value=5, max_value=min(100, len(df)), value=10)

    if preview_mode == "Head":
        sl.dataframe(df.head(n_rows), use_container_width=True)
    else:
        sl.dataframe(df.tail(n_rows), use_container_width=True)

else:
    # No data loaded — show instructions
    sl.markdown("---")
    sl.info("👆 Upload a file above or connect to Google Sheets to get started.")

    with sl.expander("📝 Supported Formats"):
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

    with sl.expander("📊 Sample Datasets"):
        sl.markdown(
            """
            Two sample datasets are included in the `sample_data/` directory:
            
            1. **ecommerce_orders.csv** — ~1,500 rows, 10 columns  
               *E-commerce orders with dirty prices, mixed categories, missing values*
            
            2. **weather_stations.xlsx** — ~1,200 rows, 9 columns  
               *Weather data with sentinel outliers, missing values, rare categories*
            """
        )
