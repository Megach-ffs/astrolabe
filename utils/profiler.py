"""
Data Profiler utilities.

Generates summary statistics, missing value reports, and duplicate analysis
for uploaded datasets.
"""

import pandas as pd
import streamlit as sl


@sl.cache_data
def get_basic_stats(df_bytes: bytes) -> dict:
    """
    Compute basic profiling stats for a DataFrame.
    Accepts serialized bytes for caching compatibility.
    """
    import pickle
    df = pickle.loads(df_bytes)
    return _compute_stats(df)


@sl.cache_data
def profile_dataframe(df: pd.DataFrame) -> dict:
    """
    Generate a comprehensive profile of the DataFrame.

    Returns a dict with keys:
        - shape: (rows, cols)
        - columns: list of column info dicts
        - dtypes: dtype per column
        - numeric_summary: describe() for numeric cols
        - categorical_summary: describe() for categorical cols
        - missing: missing value info per column
        - duplicates: duplicate row info
    """
    return _compute_stats(df)


def _compute_stats(df: pd.DataFrame) -> dict:
    """Internal function to compute all profiling stats."""
    # Column info
    columns_info = []
    for col in df.columns:
        columns_info.append({
            "name": col,
            "dtype": str(df[col].dtype),
            "non_null_count": int(df[col].notna().sum()),
            "null_count": int(df[col].isna().sum()),
            "null_pct": round(df[col].isna().mean() * 100, 2),
            "unique_count": int(df[col].nunique()),
        })

    # Missing values summary
    missing = df.isnull().sum()
    missing_info = pd.DataFrame({
        "Column": missing.index,
        "Missing Count": missing.values,
        "Missing %": (missing / len(df) * 100).round(2).values,
    })
    missing_info = missing_info[missing_info["Missing Count"] > 0]

    # Numeric summary
    numeric_cols = df.select_dtypes(include="number")
    numeric_summary = numeric_cols.describe().T if not numeric_cols.empty else pd.DataFrame()

    # Categorical summary
    cat_cols = df.select_dtypes(include=["object", "category"])
    cat_summary = cat_cols.describe().T if not cat_cols.empty else pd.DataFrame()

    # Duplicates
    dup_count = int(df.duplicated().sum())

    return {
        "shape": df.shape,
        "columns": columns_info,
        "dtypes": df.dtypes.astype(str).to_dict(),
        "numeric_summary": numeric_summary,
        "categorical_summary": cat_summary,
        "missing": missing_info,
        "duplicates": {
            "count": dup_count,
            "percentage": round(dup_count / len(df) * 100, 2) if len(df) > 0 else 0,
        },
    }
