"""
Page C — Visualization Builder

Build dynamic charts from your cleaned dataset.
Choose chart type, columns, filters, and rendering engine.
"""

import streamlit as sl

from utils.chart_builder import (
    build_histogram, build_box_plot, build_scatter,
    build_line_chart, build_bar_chart, build_heatmap,
    build_histogram_plotly, build_box_plot_plotly, build_scatter_plotly,
    build_line_chart_plotly, build_bar_chart_plotly, build_heatmap_plotly,
    filter_dataframe, fig_to_png_bytes,
)
from utils import ai_assistant


sl.title(":material/bar_chart: Visualization Builder")

# ── State Persistence (Restore) ────────────────
if "app_state_cache" not in sl.session_state:
    sl.session_state["app_state_cache"] = {}
for k, v in sl.session_state["app_state_cache"].items():
    if k.startswith(("viz_", "filt_")) and k not in sl.session_state:
        if k != "viz_download":  # Download buttons cannot be assigned via session_state
            sl.session_state[k] = v
# ─────────────────────────────────────────────

# ── Guard ─────────────────────────────────────
if sl.session_state.get("df_working") is None:
    sl.warning(":material/warning: No dataset loaded. Go to **Upload & Overview** first.")
    sl.stop()

df = sl.session_state.df_working
numeric_cols = df.select_dtypes(include="number").columns.tolist()
categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
all_cols = df.columns.tolist()


# ═══════════════════════════════════════════════
# 🤖 AI Chart Suggestions (Bonus)
# ═══════════════════════════════════════════════
if sl.session_state.get("ai_enabled"):
    if ai_assistant.is_available():
        with sl.expander(":material/robot: AI-Recommended Charts", expanded=False):
            sl.caption(":material/warning: AI suggestions may be imperfect. Review before using.")
            c1, c2, _ = sl.columns([1, 1, 3])
            with c1:
                if sl.button(":material/robot: Get Chart Suggestions", key="ai_chart_btn", use_container_width=True):
                    with sl.status(":material/robot: Analyzing your data...", expanded=True) as status:
                        sl.write("Finding interesting patterns...")
                        suggestions = ai_assistant.get_chart_suggestions(df)
                        
                        if isinstance(suggestions, dict) and "error" in suggestions:
                            status.update(label=":material/error: Failed", state="error")
                            sl.error(f":material/error: AI Error: {suggestions['error']}")
                        elif suggestions:
                            sl.session_state["ai_chart_suggestions"] = suggestions
                            status.update(label=":material/check_circle: Suggestions ready!", state="complete")
                        else:
                            status.update(label=":material/error: Failed", state="error")
                            sl.warning("AI assistant is not available or returned no suggestions.")

            with c2:
                if sl.session_state.get("ai_chart_suggestions"):
                    if sl.button(":material/delete: Clear", key="clear_ai_charts", use_container_width=True):
                        del sl.session_state["ai_chart_suggestions"]
                        sl.rerun()

            if "ai_chart_suggestions" in sl.session_state:
                # Helper for dropdown matching
                CHART_TYPES_LIST = [
                    "Histogram", "Box Plot", "Scatter Plot", 
                    "Line Chart", "Bar Chart (Grouped)", "Heatmap / Correlation"
                ]
                
                for i, sug in enumerate(sl.session_state.ai_chart_suggestions):
                    with sl.container(border=True):
                        col1, col2 = sl.columns([3, 1])
                        with col1:
                            emoji = {
                                "Histogram": ":material/bar_chart_4_bars:", "Box Plot": ":material/line_start:",
                                "Scatter Plot": ":material/scatter_plot:", "Line Chart": ":material/stacked_line_chart:",
                                "Bar Chart": ":material/bar_chart:", "Heatmap": ":material/key_visualizer:",
                            }.get(sug["chart_type"], ":material/add_chart:")

                            cols_text = sug["x_column"]
                            if sug.get("y_column"):
                                cols_text += f" vs {sug['y_column']}"

                            sl.markdown(f"{emoji} **{sug['chart_type']}**: {cols_text}")
                            sl.markdown(f"_{sug['reason']}_")
                            
                        with col2:
                            if sl.button("Use This Chart →", key=f"use_chart_{i}", use_container_width=True):
                                # Determine matching dropdown type
                                match_type = next((t for t in CHART_TYPES_LIST if t.startswith(sug["chart_type"].split()[0])), CHART_TYPES_LIST[0])
                                
                                # Set state to bind to widgets
                                sl.session_state["viz_type"] = match_type
                                
                                # Safe extraction logic picking numeric/categorical independently
                                x_c = sug.get("x_column")
                                y_c = sug.get("y_column")
                                color_c = sug.get("color_column")

                                sug_cols = [c for c in [x_c, y_c, color_c] if c]
                                sug_num_cols = [c for c in sug_cols if c in numeric_cols]
                                sug_cat_cols = [c for c in sug_cols if c in categorical_cols]

                                # Validation Logic dependent on chart type keys
                                if match_type == "Histogram":
                                    if sug_num_cols: sl.session_state["viz_x"] = sug_num_cols[0]
                                    elif x_c in all_cols: sl.session_state["viz_x"] = x_c
                                    if sug_cat_cols: sl.session_state["viz_color_hist"] = sug_cat_cols[0]
                                elif match_type == "Box Plot":
                                    if sug_num_cols: sl.session_state["viz_x_box"] = sug_num_cols[0]
                                    if sug_cat_cols: sl.session_state["viz_color_box"] = sug_cat_cols[0]
                                elif match_type == "Scatter Plot":
                                    if x_c in all_cols: sl.session_state["viz_x_scat"] = x_c
                                    if y_c in numeric_cols: sl.session_state["viz_y_scat"] = y_c
                                    elif len(sug_num_cols) > 1: sl.session_state["viz_y_scat"] = sug_num_cols[1]
                                    if color_c in categorical_cols: sl.session_state["viz_color_scat"] = color_c
                                elif match_type == "Line Chart":
                                    if x_c in all_cols: sl.session_state["viz_x_line"] = x_c
                                    if y_c in numeric_cols: sl.session_state["viz_y_line"] = y_c
                                    if color_c in categorical_cols: sl.session_state["viz_color_line"] = color_c
                                elif match_type == "Bar Chart (Grouped)":
                                    if x_c in all_cols: sl.session_state["viz_x_bar"] = x_c
                                    if y_c in numeric_cols: sl.session_state["viz_y_bar"] = y_c
                                    elif sug_num_cols: sl.session_state["viz_y_bar"] = sug_num_cols[-1]
                                    if color_c in categorical_cols: sl.session_state["viz_color_bar"] = color_c
                                elif match_type == "Heatmap / Correlation":
                                    if sug_num_cols:
                                        sl.session_state["viz_cols_heat"] = list(set(sug_num_cols))
                                        
                                sl.rerun()
    else:
        sl.markdown("---")
        sl.warning(":material/warning: **AI Assistant Unavailable**")
        sl.info("The Gemini API is not configured or is currently unresponsive. Please check your API key in `.streamlit/secrets.toml` or verify your quota.")

CHART_TYPES = [
    "Histogram",
    "Box Plot",
    "Scatter Plot",
    "Line Chart",
    "Bar Chart (Grouped)",
    "Heatmap / Correlation",
]


# ═══════════════════════════════════════════════
# Config Panel
# ═══════════════════════════════════════════════
config_col, chart_col = sl.columns([1, 3])

with config_col:
    sl.subheader(":material/settings: Settings")

    chart_type = sl.selectbox("Chart Type", CHART_TYPES, key="viz_type")

    # Renderer toggle
    use_plotly = sl.toggle("Use Plotly (interactive)", value=False, key="viz_plotly")

    sl.markdown("---")

    # ── Column selectors (dynamic per chart type) ─
    x_col = None
    y_col = None
    color_col = None
    agg_func = None
    top_n = None
    bins = 30
    heatmap_cols = None

    if chart_type == "Histogram":
        x_col = sl.selectbox("Column", numeric_cols or all_cols, key="viz_x")
        bins = sl.slider("Bins", 5, 100, 30, key="viz_bins")
        color_col = sl.selectbox(
            "Color / Group (optional)",
            [None] + categorical_cols, key="viz_color_hist",
        )

    elif chart_type == "Box Plot":
        x_col = sl.selectbox("Numeric column", numeric_cols, key="viz_x_box")
        color_col = sl.selectbox(
            "Group by (optional)",
            [None] + categorical_cols, key="viz_color_box",
        )

    elif chart_type == "Scatter Plot":
        x_col = sl.selectbox("X column", numeric_cols, key="viz_x_scat")
        y_col = sl.selectbox(
            "Y column",
            [c for c in numeric_cols if c != x_col] or numeric_cols,
            key="viz_y_scat",
        )
        color_col = sl.selectbox(
            "Color (optional)",
            [None] + categorical_cols, key="viz_color_scat",
        )

    elif chart_type == "Line Chart":
        x_col = sl.selectbox("X column (time/order)", all_cols, key="viz_x_line")
        y_col = sl.selectbox(
            "Y column",
            numeric_cols, key="viz_y_line",
        )
        color_col = sl.selectbox(
            "Color / Group (optional)",
            [None] + categorical_cols, key="viz_color_line",
        )

    elif chart_type == "Bar Chart (Grouped)":
        x_col = sl.selectbox(
            "Category (X)", categorical_cols or all_cols, key="viz_x_bar"
        )
        y_col = sl.selectbox("Value (Y)", numeric_cols, key="viz_y_bar")
        agg_func = sl.selectbox(
            "Aggregation", ["mean", "sum", "count", "median"], key="viz_agg"
        )
        color_col = sl.selectbox(
            "Color / Group (optional)",
            [None] + categorical_cols, key="viz_color_bar",
        )
        top_n = sl.slider("Top N categories", 3, 50, 10, key="viz_topn")

    elif chart_type == "Heatmap / Correlation":
        heatmap_cols = sl.multiselect(
            "Columns (leave blank for all numeric)",
            numeric_cols, key="viz_heat_cols",
        )

    # ── Filters ───────────────────────────────
    sl.markdown("---")
    sl.subheader(":material/search: Filters")

    filters = {}
    with sl.expander("Category Filters", expanded=False):
        for col in categorical_cols[:8]:
            unique_vals = df[col].dropna().unique().tolist()
            selected = sl.multiselect(
                f"{col}", unique_vals, default=unique_vals,
                key=f"filt_cat_{col}",
            )
            if len(selected) < len(unique_vals):
                filters[col] = selected

    with sl.expander("Numeric Range Filters", expanded=False):
        for col in numeric_cols[:6]:
            col_min = float(df[col].min())
            col_max = float(df[col].max())
            if col_min < col_max:
                lo, hi = sl.slider(
                    f"{col}", col_min, col_max, (col_min, col_max),
                    key=f"filt_num_{col}",
                )
                if lo > col_min or hi < col_max:
                    filters[col] = (lo, hi)

# ═══════════════════════════════════════════════
# Build and Render Chart
# ═══════════════════════════════════════════════
with chart_col:
    # Apply filters
    plot_df = filter_dataframe(df, filters) if filters else df

    if len(plot_df) == 0:
        sl.warning(":material/warning: No data left after filtering. Adjust your filters.")
        sl.stop()

    sl.caption(f"Plotting {len(plot_df):,} rows (filtered from {len(df):,})")

    try:
        fig = None

        if chart_type == "Histogram":
            if use_plotly:
                fig = build_histogram_plotly(plot_df, x_col, bins, color_col)
            else:
                fig = build_histogram(plot_df, x_col, bins, color_col)

        elif chart_type == "Box Plot":
            if not numeric_cols:
                sl.info("No numeric columns available for box plot.")
                sl.stop()
            if use_plotly:
                fig = build_box_plot_plotly(plot_df, x_col, color_col)
            else:
                fig = build_box_plot(plot_df, x_col, color_col)

        elif chart_type == "Scatter Plot":
            if use_plotly:
                fig = build_scatter_plotly(plot_df, x_col, y_col, color_col)
            else:
                fig = build_scatter(plot_df, x_col, y_col, color_col)

        elif chart_type == "Line Chart":
            if use_plotly:
                fig = build_line_chart_plotly(plot_df, x_col, y_col, color_col)
            else:
                fig = build_line_chart(plot_df, x_col, y_col, color_col)

        elif chart_type == "Bar Chart (Grouped)":
            if use_plotly:
                fig = build_bar_chart_plotly(
                    plot_df, x_col, y_col, agg_func, color_col, top_n
                )
            else:
                fig = build_bar_chart(
                    plot_df, x_col, y_col, agg_func, color_col, top_n
                )

        elif chart_type == "Heatmap / Correlation":
            if not numeric_cols:
                sl.info("No numeric columns available for heatmap.")
                sl.stop()
            if use_plotly:
                fig = build_heatmap_plotly(
                    plot_df, heatmap_cols if heatmap_cols else None
                )
            else:
                fig = build_heatmap(
                    plot_df, heatmap_cols if heatmap_cols else None
                )

        # ── Render ─────────────────────────────
        if fig is not None:
            if use_plotly:
                sl.plotly_chart(fig, use_container_width=True)
            else:
                sl.pyplot(fig)

                # Download PNG
                png_bytes = fig_to_png_bytes(fig)
                sl.download_button(
                    ":material/download: Download Chart (PNG)",
                    data=png_bytes,
                    file_name=f"{chart_type.lower().replace(' ', '_')}.png",
                    mime="image/png",
                    key="viz_download",
                )
                import matplotlib.pyplot as plt
                plt.close(fig)

    except Exception as e:
        sl.error(f":material/error: Could not render chart: {e}")

# ── State Persistence (Save) ───────────────────
for k in sl.session_state.keys():
    if k.startswith(("viz_", "filt_")):
        sl.session_state["app_state_cache"][k] = sl.session_state[k]
# ─────────────────────────────────────────────
