"""
Cleaning utility functions.

Pure functions for data cleaning operations. No Streamlit imports.
Each function takes a DataFrame + parameters and returns a new DataFrame.
"""

import pandas as pd
import numpy as np
import re


# ──────────────────────────────────────────────
# 4.1 Missing Values
# ──────────────────────────────────────────────

def fill_missing(df, columns, strategy, constant=None):
    """
    Fill missing values in specified columns.

    Args:
        df: Input DataFrame.
        columns: List of column names to fill.
        strategy: One of 'mean', 'median', 'mode', 'constant', 'ffill', 'bfill'.
        constant: Value to use when strategy is 'constant'.

    Returns:
        DataFrame with missing values filled.
    """
    df = df.copy()
    for col in columns:
        if strategy == "mean":
            df[col] = df[col].fillna(df[col].mean())
        elif strategy == "median":
            df[col] = df[col].fillna(df[col].median())
        elif strategy == "mode":
            mode_val = df[col].mode()
            if not mode_val.empty:
                df[col] = df[col].fillna(mode_val.iloc[0])
        elif strategy == "constant":
            df[col] = df[col].fillna(constant)
        elif strategy == "ffill":
            df[col] = df[col].ffill()
        elif strategy == "bfill":
            df[col] = df[col].bfill()
    return df


def drop_rows_with_nulls(df, columns):
    """Drop rows where any of the specified columns have null values."""
    return df.dropna(subset=columns).reset_index(drop=True)


def drop_columns_by_threshold(df, threshold_pct):
    """
    Drop columns where missing % exceeds threshold.

    Args:
        df: Input DataFrame.
        threshold_pct: Float 0-100. Columns with missing % above this are dropped.

    Returns:
        DataFrame with high-null columns removed.
    """
    missing_pct = (df.isnull().sum() / len(df)) * 100
    cols_to_drop = missing_pct[missing_pct > threshold_pct].index.tolist()
    return df.drop(columns=cols_to_drop)


# ──────────────────────────────────────────────
# 4.2 Duplicates
# ──────────────────────────────────────────────

def find_duplicates(df, subset=None):
    """
    Find duplicate rows.

    Args:
        df: Input DataFrame.
        subset: List of columns to check, or None for full-row.

    Returns:
        DataFrame containing only the duplicate rows.
    """
    mask = df.duplicated(subset=subset, keep=False)
    return df[mask].copy()


def remove_duplicates(df, subset=None, keep="first"):
    """
    Remove duplicate rows.

    Args:
        df: Input DataFrame.
        subset: Columns to check, or None for full-row.
        keep: 'first' or 'last'.

    Returns:
        DataFrame with duplicates removed.
    """
    return df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)


# ──────────────────────────────────────────────
# 4.3 Data Types & Parsing
# ──────────────────────────────────────────────

def clean_dirty_numeric(df, column):
    """
    Strip currency symbols, commas, whitespace from a column
    and convert to numeric.
    """
    df = df.copy()
    df[column] = (
        df[column]
        .astype(str)
        .str.replace(r"[£$€¥,\s]", "", regex=True)
        .str.strip()
    )
    df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def convert_to_numeric(df, column, errors="coerce"):
    """Convert a column to numeric type."""
    df = df.copy()
    df[column] = pd.to_numeric(df[column], errors=errors)
    return df


def convert_to_datetime(df, column, fmt=None):
    """
    Convert a column to datetime.

    Args:
        df: Input DataFrame.
        column: Column name.
        fmt: Optional strftime format string. If None, pandas infers.
    """
    df = df.copy()
    if fmt:
        df[column] = pd.to_datetime(df[column], format=fmt, errors="coerce")
    else:
        df[column] = pd.to_datetime(df[column], infer_datetime_format=True,
                                    errors="coerce")
    return df


def convert_to_datetime_mixed(df, column):
    """
    Convert a column to datetime, mixed multiple formats.

    Args:
        df: Input DataFrame.
        column: Column name.
    """
    df = df.copy()
    df[column] = pd.to_datetime(df[column], format="mixed", errors="coerce")
    return df


def convert_to_categorical(df, column):
    """Convert a column to categorical type."""
    df = df.copy()
    df[column] = df[column].astype("category")
    return df


# ──────────────────────────────────────────────
# 4.4 Categorical Data Tools
# ──────────────────────────────────────────────

def standardize_case(df, columns, case="lower"):
    """
    Standardize string case for columns.

    Args:
        case: 'lower', 'upper', or 'title'.
    """
    df = df.copy()
    for col in columns:
        if case == "lower":
            df[col] = df[col].astype(str).str.lower()
        elif case == "upper":
            df[col] = df[col].astype(str).str.upper()
        elif case == "title":
            df[col] = df[col].astype(str).str.title()
    return df


def trim_whitespace(df, columns):
    """Trim leading/trailing whitespace from string columns."""
    df = df.copy()
    for col in columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def map_values(df, column, mapping_dict, set_unmatched_to_other=False):
    """
    Apply a value mapping to a column.

    Args:
        mapping_dict: {old_value: new_value} dict.
        set_unmatched_to_other: If True, values not in mapping become "Other".
    """
    df = df.copy()
    if set_unmatched_to_other:
        mapped = df[column].map(mapping_dict)
        df[column] = mapped.fillna("Other")
    else:
        df[column] = df[column].replace(mapping_dict)
    return df


def group_rare_categories(df, column, threshold_pct, replacement="Other"):
    """
    Group categories with frequency below threshold into a single value.

    Args:
        threshold_pct: Float 0-100. Categories below this % become replacement.
    """
    df = df.copy()
    freq = df[column].value_counts(normalize=True) * 100
    rare = freq[freq < threshold_pct].index
    df[column] = df[column].replace(rare, replacement)
    return df


def one_hot_encode(df, columns, drop_first=False):
    """
    One-hot encode categorical columns.

    Returns a new DataFrame with dummy columns added
    and original columns removed.
    """
    return pd.get_dummies(df, columns=columns, drop_first=drop_first,
                          dtype=int)


# ──────────────────────────────────────────────
# 4.5 Numeric Cleaning (Outliers)
# ──────────────────────────────────────────────

def detect_outliers_iqr(df, column, factor=1.5):
    """
    Detect outliers using IQR method.

    Returns:
        dict with keys: q1, q3, iqr, lower, upper, count, pct, mask
    """
    series = df[column].dropna()
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    mask = (df[column] < lower) | (df[column] > upper)

    return {
        "q1": round(q1, 4),
        "q3": round(q3, 4),
        "iqr": round(iqr, 4),
        "lower": round(lower, 4),
        "upper": round(upper, 4),
        "count": int(mask.sum()),
        "pct": round(mask.mean() * 100, 2),
        "mask": mask,
    }


def detect_outliers_zscore(df, column, threshold=3.0):
    """
    Detect outliers using z-score method.

    Returns:
        dict with keys: mean, std, threshold, count, pct, mask
    """
    series = df[column].dropna()
    mean = series.mean()
    std = series.std()
    if std == 0:
        mask = pd.Series(False, index=df.index)
    else:
        z_scores = ((df[column] - mean) / std).abs()
        mask = z_scores > threshold

    return {
        "mean": round(mean, 4),
        "std": round(std, 4),
        "threshold": threshold,
        "count": int(mask.sum()),
        "pct": round(mask.mean() * 100, 2),
        "mask": mask,
    }


def cap_outliers(df, column, lower, upper):
    """Cap (winsorize) values outside [lower, upper]."""
    df = df.copy()
    df[column] = df[column].clip(lower=lower, upper=upper)
    return df


def remove_outlier_rows(df, column, mask):
    """Remove rows flagged as outliers."""
    return df[~mask].reset_index(drop=True)


# ──────────────────────────────────────────────
# 4.6 Normalization / Scaling
# ──────────────────────────────────────────────

def min_max_scale(df, columns):
    """Apply min-max scaling to numeric columns → [0, 1]."""
    df = df.copy()
    for col in columns:
        col_min = df[col].min()
        col_max = df[col].max()
        if col_max - col_min != 0:
            df[col] = (df[col] - col_min) / (col_max - col_min)
        else:
            df[col] = 0.0
    return df


def z_score_scale(df, columns):
    """Apply z-score standardization to numeric columns → mean=0, std=1."""
    df = df.copy()
    for col in columns:
        mean = df[col].mean()
        std = df[col].std()
        if std != 0:
            df[col] = (df[col] - mean) / std
        else:
            df[col] = 0.0
    return df


# ──────────────────────────────────────────────
# 4.7 Column Operations
# ──────────────────────────────────────────────

def rename_columns(df, rename_map):
    """
    Rename columns.

    Args:
        rename_map: {old_name: new_name} dict.
    """
    return df.rename(columns=rename_map)


def drop_columns(df, columns):
    """Drop specified columns."""
    return df.drop(columns=columns, errors="ignore")


def create_formula_column(df, new_name, formula_str):
    """
    Create a new column from a formula string.

    Supported patterns:
      - "colA / colB", "colA * colB", "colA + colB", "colA - colB"
      - "log(colA)"
      - "colA - mean(colA)"

    Uses eval() with the DataFrame namespace for safety.
    """
    df = df.copy()
    try:
        # Replace column references with df['col'] syntax
        # Handle log() function
        expr = formula_str.strip()
        if re.match(r"^log\((.+)\)$", expr):
            col_name = re.match(r"^log\((.+)\)$", expr).group(1).strip()
            df[new_name] = np.log(df[col_name].replace(0, np.nan))
        elif re.match(r"^(.+)\s*-\s*mean\((.+)\)$", expr):
            match = re.match(r"^(.+)\s*-\s*mean\((.+)\)$", expr)
            col1 = match.group(1).strip()
            col2 = match.group(2).strip()
            df[new_name] = df[col1] - df[col2].mean()
        else:
            # Simple arithmetic: colA op colB
            df[new_name] = df.eval(expr)
    except Exception as e:
        raise ValueError(f"Could not evaluate formula '{formula_str}': {e}")
    return df


def bin_column(df, column, n_bins, method="equal_width", labels=None):
    """
    Bin a numeric column into categories.

    Args:
        method: 'equal_width' (pd.cut) or 'quantile' (pd.qcut).
        labels: Optional list of bin labels.
    """
    df = df.copy()
    new_col = f"{column}_binned"
    try:
        if method == "equal_width":
            df[new_col] = pd.cut(df[column], bins=n_bins, labels=labels)
        else:
            df[new_col] = pd.qcut(df[column], q=n_bins, labels=labels,
                                  duplicates="drop")
    except Exception as e:
        raise ValueError(f"Binning failed for '{column}': {e}")
    return df
