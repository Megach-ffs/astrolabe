"""
Page B — Cleaning & Preparation Studio

Interactive data cleaning page with 8 feature sections.
Every operation: preview → configure → apply → log → confirm.
"""

import streamlit as sl
import pandas as pd

from utils.transform_log import TransformLog
from utils import cleaning
from utils.validation import ValidationRule, validate_rules, export_violations
from utils import ai_assistant


sl.title(":material/mop: Cleaning & Preparation Studio")

# ── State Persistence (Restore) ────────────────
if "app_state_cache" not in sl.session_state:
    sl.session_state["app_state_cache"] = {}
    
_SAVE_PREFIXES = (
    "mv_", "dup_", "dt_", "std_", "map_", "rare_", "ohe_", "out_", 
    "scale_", "ren_", "drop_", "formula_", "bin_", "val_", "ai_", "create_"
)

for k, v in sl.session_state["app_state_cache"].items():
    if k.startswith(_SAVE_PREFIXES) and k not in sl.session_state:
        # Exclude unassignable Streamlit widgets (Buttons, Downloaders, DataEditors)
        is_btn = k.endswith(("_apply", "_btn", "_add", "_clear", "_run"))
        is_dynamic_btn = "ai_apply_" in k or "ai_skip_" in k
        is_special = "editor" in k or "download" in k
        
        if not (is_btn or is_dynamic_btn or is_special):
            sl.session_state[k] = v
# ─────────────────────────────────────────────

# ── Guard: need data loaded ──────────────────
if sl.session_state.get("df_working") is None:
    sl.warning(":material/warning: No dataset loaded. Go to **Upload & Overview** to upload a file first.")
    sl.stop()

df = sl.session_state.df_working

# Helper columns lists
numeric_cols = df.select_dtypes(include="number").columns.tolist()
categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
all_cols = df.columns.tolist()

sl.markdown(f"Working with **{len(df):,}** rows × **{len(df.columns)}** columns")

# ── Toast Dispatcher (show stored messages after rerun) ──
if "_toast_msg" in sl.session_state:
    sl.success(sl.session_state.pop("_toast_msg"))


def _apply_ai_suggestion(dataframe, suggestion):
    """Map an AI suggestion dict to our existing cleaning functions."""
    op = suggestion["operation"]
    params = suggestion["params"]
    cols = suggestion.get("affected_columns", [])

    if op == "fill_missing":
        strategy = params.get("strategy", "mean")
        target_cols = params.get("columns", cols)
        return cleaning.fill_missing(
            dataframe, target_cols, strategy,
            constant=params.get("constant")
        )
    elif op == "remove_duplicates":
        return cleaning.remove_duplicates(
            dataframe,
            subset=params.get("subset"),
            keep=params.get("keep", "first"),
        )
    elif op == "convert_type":
        target = params.get("target", "numeric")
        target_cols = params.get("columns", cols)
        result = dataframe.copy()
        for col in target_cols:
            if target == "numeric":
                result = cleaning.convert_to_numeric(result, col)
            elif target == "numeric (dirty)":
                result = cleaning.clean_dirty_numeric(result, col)
            elif target == "datetime":
                result = cleaning.convert_to_datetime(result, col)
            elif target == "categorical":
                result = cleaning.convert_to_categorical(result, col)
        return result
    elif op == "standardize_categorical":
        target_cols = params.get("columns", cols)
        ops = params.get("operations", ["trim", "lower"])
        result = dataframe.copy()
        if "trim" in ops:
            result = cleaning.trim_whitespace(result, target_cols)
        for case_op in ["lower", "upper", "title"]:
            if case_op in ops:
                result = cleaning.standardize_case(result, target_cols, case_op)
                break
        return result
    elif op == "outlier_treatment":
        target_cols = params.get("columns", cols)
        method = params.get("method", "IQR")
        action = params.get("action", "Cap")
        result = dataframe.copy()
        for col in target_cols:
            if method == "IQR":
                stats = cleaning.detect_outliers_iqr(result, col)
            else:
                stats = cleaning.detect_outliers_zscore(result, col)
            if "Cap" in action:
                result = cleaning.cap_outliers(
                    result, col, stats["lower"], stats["upper"]
                )
            else:
                result = cleaning.remove_outlier_rows(
                    result, col, stats["mask"]
                )
        return result
    elif op == "scale_columns":
        target_cols = params.get("columns", cols)
        method = params.get("method", "min_max")
        if method == "min_max":
            return cleaning.min_max_scale(dataframe, target_cols)
        else:
            return cleaning.z_score_scale(dataframe, target_cols)
    elif op == "drop_columns":
        target_cols = params.get("columns", cols)
        return cleaning.drop_columns(dataframe, target_cols)
    elif op == "rename_column":
        old = params.get("old", "")
        new = params.get("new", "")
        return cleaning.rename_columns(dataframe, {old: new})
    elif op == "one_hot_encode":
        target_cols = params.get("columns", cols)
        drop_first = params.get("drop_first", False)
        return cleaning.one_hot_encode(dataframe, target_cols, drop_first)
    elif op == "group_rare":
        col = params.get("column", cols[0] if cols else "")
        thresh = params.get("threshold", 5)
        return cleaning.group_rare_categories(dataframe, col, thresh)
    elif op == "map_values":
        col = params.get("column", cols[0] if cols else "")
        mapping = params.get("mapping", {})
        return cleaning.map_values(dataframe, col, mapping)
    else:
        raise ValueError(f"Unknown operation: {op}")


# ═══════════════════════════════════════════════
# 🤖 AI Cleaning Assistant (Bonus +12)
# ═══════════════════════════════════════════════
if sl.session_state.get("ai_enabled"):
    if ai_assistant.is_available():
        with sl.expander(":material/robot: AI Cleaning Assistant", expanded=True):
            sl.caption(":material/warning: AI suggestions may be imperfect. Always review before applying.")

            if "ai_clean_initial_prompt" in sl.session_state:
                sl.session_state["ai_clean_prompt"] = sl.session_state.pop("ai_clean_initial_prompt")

            user_prompt = sl.text_input(
                "What would you like to clean?",
                placeholder='e.g. "Fill missing prices with median and lowercase all category names"',
                key="ai_clean_prompt",
            )

            c1, c2, _ = sl.columns([1, 1, 3])
            with c1:
                if user_prompt and sl.button(":material/robot: Get Suggestions", key="ai_clean_btn", use_container_width=True):
                    with sl.status(":material/robot: Analyzing your data...", expanded=True) as status:
                        sl.write("Sending data profile to Gemini...")
                        suggestions = ai_assistant.get_cleaning_suggestions(df, user_prompt)
                        
                        if isinstance(suggestions, dict) and "error" in suggestions:
                            status.update(label=":material/error: Failed", state="error")
                            sl.error(f":material/error: AI Error: {suggestions['error']}")
                        elif suggestions:
                            sl.session_state["ai_suggestions"] = suggestions
                            status.update(label=":material/check_circle: Suggestions ready!", state="complete")
                        else:
                            status.update(label=":material/error: Failed", state="error")
                            sl.warning("AI assistant is not available or returned no suggestions.")

            with c2:
                if sl.session_state.get("ai_suggestions"):
                    if sl.button(":material/delete: Clear", key="clear_ai_sug", use_container_width=True):
                        del sl.session_state["ai_suggestions"]
                        sl.rerun()

            # Display suggestions as cards
            if sl.session_state.get("ai_suggestions"):
                for i, sug in enumerate(sl.session_state.ai_suggestions):
                    with sl.container(border=True):
                        sl.markdown(
                            f"**📌 {sug['operation']}** on "
                            f"`{', '.join(sug['affected_columns'])}`"
                        )
                        sl.markdown(f"_{sug['description']}_")
                        sl.code(str(sug["params"]), language="json")

                        act1, act2, _ = sl.columns([1, 1, 3])
                        if act1.button(":material/check_circle: Apply", key=f"ai_apply_{i}"):
                            try:
                                new_df = _apply_ai_suggestion(df, sug)
                                if new_df is not None:
                                    TransformLog.add_step(
                                        sug["operation"],
                                        sug["params"],
                                        sug["affected_columns"],
                                        df,
                                    )
                                    sl.session_state.df_working = new_df
                                    sl.success(f":material/check_circle: Applied: {sug['description']}")
                                    sl.session_state.ai_suggestions.pop(i)
                                    sl.rerun()
                            except Exception as e:
                                sl.error(f":material/error: Failed: {e}")
                        if act2.button(":material/error: Skip", key=f"ai_skip_{i}"):
                            sl.session_state.ai_suggestions.pop(i)
                            sl.rerun()
    else:
        sl.markdown("---")
        sl.warning(":material/warning: **AI Assistant Unavailable**")
        sl.info("The Gemini API is not configured or is currently unresponsive. Please check your API key in `.streamlit/secrets.toml` or verify your quota.")

sl.markdown("---")


# ═══════════════════════════════════════════════
# 4.1 Missing Values (10 pts)
# ═══════════════════════════════════════════════
with sl.expander(":material/warning: 4.1 — Missing Values", expanded=False):
    # Summary
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]

    if missing_cols.empty:
        sl.success(":material/check_circle: No missing values in the dataset!")
    else:
        missing_info = pd.DataFrame({
            "Column": missing_cols.index,
            "Missing": missing_cols.values,
            "% Missing": (missing_cols / len(df) * 100).round(2).values,
        })
        sl.dataframe(missing_info, use_container_width=True, hide_index=True)

        # Controls
        cols_to_fix = sl.multiselect(
            "Select columns to fix",
            missing_cols.index.tolist(),
            key="mv_cols",
        )

        strategy = sl.selectbox(
            "Strategy",
            ["drop_rows", "drop_columns_by_threshold",
             "mean", "median", "mode", "constant", "ffill", "bfill"],
            key="mv_strategy",
        )

        constant_val = None
        threshold_val = 50.0
        if strategy == "constant":
            constant_val = sl.text_input("Constant value", key="mv_const")
        elif strategy == "drop_columns_by_threshold":
            threshold_val = sl.slider(
                "Max missing % threshold", 0, 100, 50, key="mv_thresh"
            )

        if cols_to_fix and sl.button("Apply Missing Value Fix", key="mv_apply"):
            before_nulls = df.isnull().sum().sum()
            before_rows = len(df)

            if strategy == "drop_rows":
                new_df = cleaning.drop_rows_with_nulls(df, cols_to_fix)
            elif strategy == "drop_columns_by_threshold":
                new_df = cleaning.drop_columns_by_threshold(df, threshold_val)
            else:
                new_df = cleaning.fill_missing(
                    df, cols_to_fix, strategy, constant=constant_val
                )

            TransformLog.add_step(
                "fill_missing",
                {"strategy": strategy, "columns": cols_to_fix},
                cols_to_fix,
                df,
            )
            sl.session_state.df_working = new_df

            after_nulls = new_df.isnull().sum().sum()
            c1, c2 = sl.columns(2)
            c1.metric("Before", f"{before_nulls} nulls, {before_rows} rows")
            c2.metric("After", f"{after_nulls} nulls, {len(new_df)} rows")
            sl.session_state["_toast_msg"] = ":material/check_circle: Applied!"
            sl.rerun()


# ═══════════════════════════════════════════════
# 4.2 Duplicates
# ═══════════════════════════════════════════════
with sl.expander(":material/refresh: 4.2 — Duplicates", expanded=False):
    dup_mode = sl.radio(
        "Check for", ["Full-row duplicates", "Duplicates by subset"],
        horizontal=True, key="dup_mode",
    )

    subset = None
    if dup_mode == "Duplicates by subset":
        subset = sl.multiselect("Key columns", all_cols, key="dup_subset")

    dup_df = cleaning.find_duplicates(df, subset=subset if subset else None)
    sl.metric("Duplicate rows found", len(dup_df))

    if not dup_df.empty:
        with sl.container():
            sl.markdown("**Sample duplicate groups:**")
            sl.dataframe(cleaning.get_duplicates_occurence(df, subset=subset if subset else None).head(20), use_container_width=True)

        keep = sl.selectbox("Keep", ["first", "last"], key="dup_keep")

        if sl.button("Remove Duplicates", key="dup_apply"):
            before = len(df)
            new_df = cleaning.remove_duplicates(
                df, subset=subset if subset else None, keep=keep
            )
            TransformLog.add_step(
                "remove_duplicates",
                {"subset": subset, "keep": keep},
                subset or ["all"],
                df,
            )
            sl.session_state.df_working = new_df
            sl.session_state["_toast_msg"] = f":material/check_circle: Removed {before - len(new_df)} duplicate rows."
            sl.rerun()


# ═══════════════════════════════════════════════
# 4.3 Data Types & Parsing
# ═══════════════════════════════════════════════
with sl.expander(":material/cached: 4.3 — Data Types & Parsing", expanded=False):
    # Show current types
    dtype_info = pd.DataFrame({
        "Column": all_cols,
        "Current Type": [str(df[c].dtype) for c in all_cols],
        "Sample": [str(df[c].iloc[0]) if len(df) > 0 else "" for c in all_cols],
    })
    sl.dataframe(dtype_info, use_container_width=True, hide_index=True)

    col_to_convert = sl.selectbox("Column to convert", all_cols, key="dt_col")
    target_type = sl.selectbox(
        "Target type",
        ["numeric", "numeric (dirty)", "datetime", "datetime (mixed)", "categorical"],
        key="dt_target",
    )

    dt_fmt = None
    if target_type == "datetime":
        dt_fmt = sl.text_input(
            "DateTime format (leave blank for auto)",
            placeholder="%Y-%m-%d",
            key="dt_fmt",
        )

    if sl.button("Convert Type", key="dt_apply"):
        try:
            if target_type == "numeric":
                new_df = cleaning.convert_to_numeric(df, col_to_convert)
            elif target_type == "numeric (dirty)":
                new_df = cleaning.clean_dirty_numeric(df, col_to_convert)
            elif target_type == "datetime":
                new_df = cleaning.convert_to_datetime(
                    df, col_to_convert, fmt=dt_fmt or None
                )
            elif target_type == "datetime (mixed)":
                new_df = cleaning.convert_to_datetime_mixed(
                    df, col_to_convert
                )
            else:
                new_df = cleaning.convert_to_categorical(df, col_to_convert)

            TransformLog.add_step(
                "convert_type",
                {"target": target_type, "format": dt_fmt},
                [col_to_convert],
                df,
            )
            sl.session_state.df_working = new_df
            sl.session_state["_toast_msg"] = f":material/check_circle: Converted `{col_to_convert}` to {target_type}. \nNew type: `{new_df[col_to_convert].dtype}`"
            sl.rerun()
        except Exception as e:
            sl.error(f":material/error: Conversion failed: {e}")


# ═══════════════════════════════════════════════
# 4.4 Categorical Data Tools (10 pts)
# ═══════════════════════════════════════════════
with sl.expander(":material/label: 4.4 — Categorical Data Tools", expanded=False):
    cat_tab1, cat_tab2, cat_tab3, cat_tab4 = sl.tabs(
        ["Standardize", "Mapping", "Rare Grouping", "One-Hot Encoding"]
    )

    # Tab 1: Standardize
    with cat_tab1:
        std_cols = sl.multiselect(
            "Columns to standardize", categorical_cols, key="std_cols"
        )
        std_ops = sl.multiselect(
            "Operations",
            ["Trim whitespace", "Lowercase", "Uppercase", "Title case"],
            default=["Trim whitespace", "Lowercase"],
            key="std_ops",
        )
        if std_cols and sl.button("Apply Standardization", key="std_apply"):
            new_df = df.copy()
            applied = []
            if "Trim whitespace" in std_ops:
                new_df = cleaning.trim_whitespace(new_df, std_cols)
                applied.append("trim")
            if "Lowercase" in std_ops:
                new_df = cleaning.standardize_case(new_df, std_cols, "lower")
                applied.append("lower")
            elif "Uppercase" in std_ops:
                new_df = cleaning.standardize_case(new_df, std_cols, "upper")
                applied.append("upper")
            elif "Title case" in std_ops:
                new_df = cleaning.standardize_case(new_df, std_cols, "title")
                applied.append("title")

            TransformLog.add_step(
                "standardize_categorical",
                {"operations": applied},
                std_cols,
                df,
            )
            sl.session_state.df_working = new_df
            sl.session_state["_toast_msg"] = ":material/check_circle: Applied!"
            sl.rerun()

    # Tab 2: Mapping
    with cat_tab2:
        if categorical_cols:
            map_col = sl.selectbox(
                "Column", categorical_cols, key="map_col"
            )
            unique_vals = df[map_col].dropna().unique().tolist()[:50]
            sl.markdown(f"**Unique values** ({len(unique_vals)} shown):")

            mapping_data = pd.DataFrame({
                "Original": unique_vals,
                "New Value": unique_vals,
            })
            edited = sl.data_editor(
                mapping_data, num_rows="fixed", key="map_editor",
                use_container_width=True,
            )

            set_other = sl.checkbox(
                "Set unmatched values to 'Other'", key="map_other"
            )

            if sl.button("Apply Mapping", key="map_apply"):
                mapping_dict = dict(
                    zip(edited["Original"], edited["New Value"])
                )
                # Only keep changed values
                mapping_dict = {
                    k: v for k, v in mapping_dict.items() if k != v
                }
                if mapping_dict:
                    new_df = cleaning.map_values(
                        df, map_col, mapping_dict,
                        set_unmatched_to_other=set_other
                    )
                    TransformLog.add_step(
                        "map_values",
                        {"mapping": mapping_dict, "other": set_other},
                        [map_col],
                        df,
                    )
                    sl.session_state.df_working = new_df
                    sl.session_state["_toast_msg"] = ":material/check_circle: Applied!"
                    sl.rerun()
                else:
                    sl.info("No changes detected in mapping.")
        else:
            sl.info("No categorical columns found.")

    # Tab 3: Rare Category Grouping
    with cat_tab3:
        if categorical_cols:
            rare_col = sl.selectbox(
                "Column", categorical_cols, key="rare_col"
            )
            rare_thresh = sl.slider(
                "Frequency threshold (%)", 1, 20, 5, key="rare_thresh"
            )

            freq = df[rare_col].value_counts(normalize=True) * 100
            rare_cats = freq[freq < rare_thresh]

            if not rare_cats.empty:
                sl.markdown(
                    f"**{len(rare_cats)}** categories below {rare_thresh}%:"
                )
                sl.dataframe(
                    rare_cats.reset_index().rename(
                        columns={"index": "Category", rare_col: "Category"}
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                if sl.button("Group Rare → 'Other'", key="rare_apply"):
                    new_df = cleaning.group_rare_categories(
                        df, rare_col, rare_thresh
                    )
                    TransformLog.add_step(
                        "group_rare",
                        {"threshold": rare_thresh},
                        [rare_col],
                        df,
                    )
                    sl.session_state.df_working = new_df
                    sl.session_state["_toast_msg"] = ":material/check_circle: Applied!"
                    sl.rerun()
            else:
                sl.success("No rare categories at this threshold.")
        else:
            sl.info("No categorical columns found.")

    # Tab 4: One-Hot Encoding
    with cat_tab4:
        if categorical_cols:
            ohe_cols = sl.multiselect(
                "Columns to encode", categorical_cols, key="ohe_cols"
            )
            drop_first = sl.checkbox("Drop first column", key="ohe_drop")

            if ohe_cols:
                new_cols_preview = []
                for c in ohe_cols:
                    vals = df[c].dropna().unique()[:10]
                    for v in vals:
                        new_cols_preview.append(f"{c}_{v}")
                sl.markdown(
                    f"**Preview:** Will create ~{len(new_cols_preview)} "
                    f"new columns"
                )

                if sl.button("Apply One-Hot Encoding", key="ohe_apply"):
                    new_df = cleaning.one_hot_encode(df, ohe_cols, drop_first)
                    TransformLog.add_step(
                        "one_hot_encode",
                        {"drop_first": drop_first},
                        ohe_cols,
                        df,
                    )
                    sl.session_state.df_working = new_df
                    sl.session_state["_toast_msg"] = f":material/check_circle: Encoded {len(ohe_cols)} columns → \n{len(new_df.columns)} total columns"
                    sl.rerun()
        else:
            sl.info("No categorical columns found.")


# ═══════════════════════════════════════════════
# 4.5 Numeric Cleaning — Outliers (10 pts)
# ═══════════════════════════════════════════════
with sl.expander(":material/square_foot: 4.5 — Numeric Cleaning (Outliers)", expanded=False):
    if numeric_cols:
        out_col = sl.selectbox(
            "Column", numeric_cols, key="out_col"
        )
        out_method = sl.radio(
            "Detection method", ["IQR", "Z-Score"],
            horizontal=True, key="out_method",
        )

        if out_method == "IQR":
            iqr_factor = sl.slider(
                "IQR factor", 1.0, 3.0, 1.5, 0.1, key="out_iqr"
            )
            stats = cleaning.detect_outliers_iqr(df, out_col, iqr_factor)
            sl.markdown(
                f"**Q1:** {stats['q1']} | **Q3:** {stats['q3']} | "
                f"**IQR:** {stats['iqr']}"
            )
            sl.markdown(
                f"**Range:** [{stats['lower']}, {stats['upper']}]"
            )
        else:
            z_thresh = sl.slider(
                "Z-Score threshold", 2.0, 4.0, 3.0, 0.1, key="out_z"
            )
            stats = cleaning.detect_outliers_zscore(
                df, out_col, z_thresh
            )
            sl.markdown(
                f"**Mean:** {stats['mean']} | **Std:** {stats['std']}"
            )

        sl.metric(
            "Outliers detected",
            f"{stats['count']} ({stats['pct']}%)"
        )

        if stats["count"] > 0:
            action = sl.selectbox(
                "Action",
                ["Cap / Winsorize", "Remove outlier rows", "Do nothing"],
                key="out_action",
            )

            if action != "Do nothing" and sl.button(
                "Apply Outlier Treatment", key="out_apply"
            ):
                if action == "Cap / Winsorize":
                    if out_method == "IQR":
                        new_df = cleaning.cap_outliers(
                            df, out_col, stats["lower"], stats["upper"]
                        )
                        sl.session_state["_toast_msg"] = f":material/check_circle: {action} applied to `{out_col}` capping values at the thresholds {stats['upper']} and {stats['lower']}."
                    else:
                        lower = stats["mean"] - z_thresh * stats["std"]
                        upper = stats["mean"] + z_thresh * stats["std"]
                        new_df = cleaning.cap_outliers(
                            df, out_col, lower, upper
                        )
                        sl.session_state["_toast_msg"] = f":material/check_circle: {action} applied to `{out_col}` capping values at the thresholds {upper} and {lower}."
                    
                else:
                    new_df = cleaning.remove_outlier_rows(
                        df, out_col, stats["mask"]
                    )
                    sl.session_state["_toast_msg"] = f":material/check_circle: {action} applied to `{out_col}` on `{stats['count']}` rows."
                sl.session_state.df_working = new_df


                TransformLog.add_step(
                    "outlier_treatment",
                    {"method": out_method, "action": action,
                     "count": stats["count"]},
                    [out_col],
                    df,
                )
                
                sl.rerun()
                
    else:
        sl.info("No numeric columns found.")


# ═══════════════════════════════════════════════
# 4.6 Normalization / Scaling (10 pts)
# ═══════════════════════════════════════════════
with sl.expander(":material/blur_linear: 4.6 — Normalization / Scaling", expanded=False):
    if numeric_cols:
        scale_cols = sl.multiselect(
            "Columns to scale", numeric_cols, key="scale_cols"
        )
        scale_method = sl.radio(
            "Method", ["Min-Max (→ [0,1])", "Z-Score (→ mean=0, std=1)"],
            horizontal=True, key="scale_method",
        )

        if scale_cols:
            # Show before stats
            before_stats = df[scale_cols].describe().round(3)
            sl.markdown("**Before:**")
            sl.dataframe(before_stats, use_container_width=True)

            # Preview
            if "Min-Max" in scale_method:
                preview = cleaning.min_max_scale(df, scale_cols)
            else:
                preview = cleaning.z_score_scale(df, scale_cols)

            sl.markdown("**After (preview):**")
            sl.dataframe(
                preview[scale_cols].describe().round(3),
                use_container_width=True,
            )

            if sl.button("Apply Scaling", key="scale_apply"):
                method_name = (
                    "min_max" if "Min-Max" in scale_method else "z_score"
                )
                TransformLog.add_step(
                    f"scale_{method_name}",
                    {"method": method_name},
                    scale_cols,
                    df,
                )
                sl.session_state.df_working = preview
                sl.session_state["_toast_msg"] = ":material/check_circle: Scaling applied!"
                sl.rerun()
    else:
        sl.info("No numeric columns found.")


# ═══════════════════════════════════════════════
# 4.7 Column Operations
# ═══════════════════════════════════════════════
with sl.expander(":material/build: 4.7 — Column Operations", expanded=False):
    col_tab1, col_tab2, col_tab3 = sl.tabs(
        ["Rename", "Drop", "Create New"]
    )

    # Tab 1: Rename
    with col_tab1:
        rename_col = sl.selectbox("Column to rename", all_cols, key="ren_col")
        new_name = sl.text_input(
            "New name", value=rename_col, key="ren_name"
        )
        if new_name != rename_col and sl.button("Rename", key="ren_apply"):
            new_df = cleaning.rename_columns(df, {rename_col: new_name})
            TransformLog.add_step(
                "rename_column",
                {"old": rename_col, "new": new_name},
                [rename_col],
                df,
            )
            sl.session_state.df_working = new_df
            sl.session_state["_toast_msg"] = f":material/check_circle: Renamed `{rename_col}` → `{new_name}`"
            sl.rerun()

    # Tab 2: Drop
    with col_tab2:
        drop_cols = sl.multiselect(
            "Columns to drop", all_cols, key="drop_cols"
        )
        if drop_cols and sl.button("Drop Columns", key="drop_apply"):
            new_df = cleaning.drop_columns(df, drop_cols)
            TransformLog.add_step(
                "drop_columns",
                {"columns": drop_cols},
                drop_cols,
                df,
            )
            sl.session_state.df_working = new_df
            sl.session_state["_toast_msg"] = f":material/check_circle: Dropped {len(drop_cols)} columns."
            sl.rerun()

    # Tab 3: Create New
    with col_tab3:
        create_mode = sl.radio(
            "Mode", ["Formula", "Binning"],
            horizontal=True, key="create_mode",
        )

        if create_mode == "Formula":
            sl.markdown(
                "**Formulas:** `colA / colB`, `colA * colB`, "
                "`log(col)`, `col - mean(col)`"
            )
            formula_name = sl.text_input(
                "New column name", key="formula_name"
            )
            formula_str = sl.text_input(
                "Formula", placeholder="price / quantity",
                key="formula_str",
            )
            if formula_name and formula_str and sl.button(
                "Create Column", key="formula_apply"
            ):
                try:
                    new_df = cleaning.create_formula_column(
                        df, formula_name, formula_str
                    )
                    TransformLog.add_step(
                        "create_column",
                        {"name": formula_name, "formula": formula_str},
                        [formula_name],
                        df,
                    )
                    sl.session_state.df_working = new_df
                    sl.session_state["_toast_msg"] = f":material/check_circle: Created `{formula_name}`"
                    sl.rerun()
                except ValueError as e:
                    sl.error(f":material/error: {e}")
        else:
            bin_col = sl.selectbox(
                "Column to bin", numeric_cols, key="bin_col"
            )
            n_bins = sl.slider("Number of bins", 2, 20, 5, key="bin_n")
            bin_method = sl.radio(
                "Method", ["equal_width", "quantile"],
                horizontal=True, key="bin_method",
            )
            if sl.button("Create Binned Column", key="bin_apply"):
                try:
                    new_df = cleaning.bin_column(
                        df, bin_col, n_bins, bin_method
                    )
                    TransformLog.add_step(
                        "bin_column",
                        {"column": bin_col, "bins": n_bins,
                         "method": bin_method},
                        [bin_col],
                        df,
                    )
                    sl.session_state.df_working = new_df
                    sl.session_state["_toast_msg"] = f":material/check_circle: Created `{bin_col}_binned` with {n_bins} bins"
                    sl.rerun()
                except ValueError as e:
                    sl.error(f":material/error: {e}")


# ═══════════════════════════════════════════════
# 4.8 Data Validation Rules
# ═══════════════════════════════════════════════
with sl.expander(":material/rule: 4.8 — Data Validation Rules", expanded=False):
    sl.markdown("Define rules and check your dataset for violations.")

    # Rule builder
    val_col = sl.selectbox("Column", all_cols, key="val_col")
    val_type = sl.selectbox(
        "Rule type",
        ["range", "allowed", "non_null"],
        key="val_type",
    )

    val_params = {}
    if val_type == "range":
        vc1, vc2 = sl.columns(2)
        val_min = vc1.number_input("Min value", value=0.0, key="val_min")
        val_max = vc2.number_input("Max value", value=100.0, key="val_max")
        val_params = {"min": val_min, "max": val_max}
    elif val_type == "allowed":
        allowed_str = sl.text_input(
            "Allowed values (comma-separated)",
            placeholder="A, B, C",
            key="val_allowed",
        )
        if allowed_str:
            val_params = {
                "values": [v.strip() for v in allowed_str.split(",")]
            }

    # Store rules in session
    if "validation_rules" not in sl.session_state:
        sl.session_state.validation_rules = []

    ac1, ac2 = sl.columns(2)
    if ac1.button("Add Rule", key="val_add"):
        rule = ValidationRule(val_type, val_col, val_params)
        sl.session_state.validation_rules.append(rule)
        sl.success(f"Added: {rule}")

    if ac2.button("Clear Rules", key="val_clear"):
        sl.session_state.validation_rules = []
        sl.rerun()

    # Show current rules
    rules = sl.session_state.validation_rules
    if rules:
        sl.markdown(f"**{len(rules)} rule(s) defined:**")
        for i, r in enumerate(rules):
            sl.markdown(f"  {i+1}. `{r.rule_type}` on `{r.column}` — {r.params}")

        if sl.button("Run Validation", key="val_run"):
            violations = validate_rules(df, rules)
            if violations.empty:
                sl.success(":material/check_circle: No violations found!")
            else:
                sl.warning(f":material/warning: {len(violations)} violation(s) found:")
                sl.dataframe(
                    violations, use_container_width=True, hide_index=True
                )
                csv_bytes = export_violations(violations)
                sl.download_button(
                    "📥 Download Violations CSV",
                    data=csv_bytes,
                    file_name="violations.csv",
                    mime="text/csv",
                    key="val_download",
                )


# ═══════════════════════════════════════════════
# Transformation Log Display
# ═══════════════════════════════════════════════
sl.markdown("---")
sl.subheader(":material/description: Transformation Log")

log = TransformLog.get_log()
if log:
    for step in log:
        cols = ", ".join(step["columns"]) if step["columns"] else "all"
        sl.markdown(
            f"**Step {step['step_number']}**: `{step['operation']}` "
            f"on [{cols}] — {step['timestamp']}"
        )

    undo_col, reset_col, _ = sl.columns([1, 1, 3])
    with undo_col:
        if sl.button(":material/undo: Undo Last", key="log_undo", use_container_width=True):
            restored = TransformLog.undo_last()
            if restored is not None:
                sl.session_state.df_working = restored
                sl.rerun()
    with reset_col:
        if sl.button(
            ":material/refresh: Reset All", key="log_reset", use_container_width=True
        ):
            if sl.session_state.df_original is not None:
                sl.session_state.df_working = TransformLog.reset_all(
                    sl.session_state.df_original
                )
                sl.rerun()
else:
    sl.info("No transformations applied yet.")

# ── State Persistence (Save) ───────────────────
for k in sl.session_state.keys():
    if k.startswith(_SAVE_PREFIXES):
        is_btn = k.endswith(("_apply", "_btn", "_add", "_clear", "_run"))
        is_dynamic_btn = "ai_apply_" in k or "ai_skip_" in k
        is_special = "editor" in k or "download" in k
        
        if not (is_btn or is_dynamic_btn or is_special):
            sl.session_state["app_state_cache"][k] = sl.session_state[k]
# ─────────────────────────────────────────────
