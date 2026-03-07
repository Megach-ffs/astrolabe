"""
Page D — Export & Report

Export cleaned data, transformation reports, and reproducible recipes.
"""

import streamlit as sl

from utils.transform_log import TransformLog
from utils.export import (
    to_csv_bytes, to_excel_bytes,
    generate_report, report_to_markdown, report_to_json_bytes,
    generate_json_recipe, generate_python_script,
)


sl.title("📥 Export & Report")

# ── Guard ─────────────────────────────────────
if sl.session_state.get("df_working") is None:
    sl.warning("⚠️ No dataset loaded. Go to **Upload & Overview** first.")
    sl.stop()

df = sl.session_state.df_working
df_original = sl.session_state.get("df_original", df)
log = TransformLog.get_log()
file_name = sl.session_state.get("file_name", "data.csv")


# ═══════════════════════════════════════════════
# 1. Export Cleaned Dataset
# ═══════════════════════════════════════════════
sl.subheader("📤 Export Cleaned Dataset")
sl.markdown(f"**Current dataset:** {len(df):,} rows × {len(df.columns)} columns")

dl_col1, dl_col2, _ = sl.columns([1, 1, 2])

with dl_col1:
    csv_bytes = to_csv_bytes(df)
    sl.download_button(
        "📥 Download CSV",
        data=csv_bytes,
        file_name="cleaned_dataset.csv",
        mime="text/csv",
        key="export_csv",
        use_container_width=True,
    )

with dl_col2:
    excel_bytes = to_excel_bytes(df)
    sl.download_button(
        "📥 Download Excel",
        data=excel_bytes,
        file_name="cleaned_dataset.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="export_excel",
        use_container_width=True,
    )

# Preview
with sl.expander("👁️ Dataset Preview", expanded=False):
    sl.dataframe(df.head(20), use_container_width=True)

sl.markdown("---")


# ═══════════════════════════════════════════════
# 2. Transformation Report
# ═══════════════════════════════════════════════
sl.subheader("📝 Transformation Report")

report = generate_report(log, df_original, df)

# Summary metrics
mc1, mc2, mc3 = sl.columns(3)
mc1.metric("Total Steps", report["total_steps"])
mc2.metric("Before", f"{report['before']['rows']:,} × {report['before']['columns']}")
mc3.metric("After", f"{report['after']['rows']:,} × {report['after']['columns']}")

# Markdown preview
md_report = report_to_markdown(report)
with sl.expander("📄 Report Preview", expanded=True):
    sl.markdown(md_report)

# Download report
rpt_col1, rpt_col2, _ = sl.columns([1, 1, 2])
with rpt_col1:
    json_report = report_to_json_bytes(report)
    sl.download_button(
        "📥 Download Report (JSON)",
        data=json_report,
        file_name="transformation_report.json",
        mime="application/json",
        key="export_report",
        use_container_width=True,
    )

sl.markdown("---")


# ═══════════════════════════════════════════════
# 3. Reproducible Recipe
# ═══════════════════════════════════════════════
sl.subheader("🔁 Reproducible Recipe")

if log:
    recipe_col1, recipe_col2, _ = sl.columns([1, 1, 2])

    # JSON recipe
    with recipe_col1:
        recipe_bytes = generate_json_recipe(log)
        sl.download_button(
            "📥 Download Recipe (JSON)",
            data=recipe_bytes,
            file_name="recipe.json",
            mime="application/json",
            key="export_recipe",
            use_container_width=True,
        )

    # Python script (bonus +3)
    with recipe_col2:
        script = generate_python_script(log, file_name)
        sl.download_button(
            "📥 Download Python Script",
            data=script.encode("utf-8"),
            file_name="pipeline.py",
            mime="text/x-python",
            key="export_script",
            use_container_width=True,
        )

    # Script preview
    with sl.expander("🐍 Python Script Preview", expanded=False):
        sl.code(script, language="python")

    # Recipe preview
    with sl.expander("📋 JSON Recipe Preview", expanded=False):
        sl.code(recipe_bytes.decode("utf-8"), language="json")
else:
    sl.info("No transformations applied yet. Apply some cleaning steps first to generate a recipe.")


# ═══════════════════════════════════════════════
# 4. Full Transformation Log
# ═══════════════════════════════════════════════
sl.markdown("---")
sl.subheader("📋 Transformation Log")

if log:
    for step in log:
        cols = ", ".join(step["columns"]) if step["columns"] else "all"
        sl.markdown(
            f"**Step {step['step_number']}**: `{step['operation']}` "
            f"on [{cols}] — {step['timestamp']}"
        )
else:
    sl.info("No transformations applied.")
