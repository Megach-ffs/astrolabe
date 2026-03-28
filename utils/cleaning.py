import pandas as pd
import numpy as np
import re


# 4.1 Missing values
def fill_missing(df, columns, strategy, constant=None):
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
    return df.dropna(subset=columns).reset_index(drop=True)


def drop_columns_by_threshold(df, threshold_pct):
    missing_pct = (df.isnull().sum() / len(df)) * 100
    cols_to_drop = missing_pct[missing_pct > threshold_pct].index.tolist()
    return df.drop(columns=cols_to_drop)
# 4.2 Duplicates

def find_duplicates(df, subset=None):
    mask = df.duplicated(subset=subset, keep='first')
    return df[mask].copy()

def get_duplicates_occurence(df, subset=None):
    return find_duplicates(df, subset).drop_duplicates(subset=subset, keep='first')


def remove_duplicates(df, subset=None, keep="first"):
    return df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)


# 4.3 Data types
def clean_dirty_numeric(df, column):
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
    df = df.copy()
    df[column] = pd.to_numeric(df[column], errors=errors)
    return df


def convert_to_datetime(df, column, fmt=None):
    df = df.copy()
    if fmt:
        df[column] = pd.to_datetime(df[column], format=fmt, errors="coerce")
    else:
        df[column] = pd.to_datetime(df[column], infer_datetime_format=True,
                                    errors="coerce")
    return df


def convert_to_datetime_mixed(df, column):
    df = df.copy()
    df[column] = pd.to_datetime(df[column], format="mixed", errors="coerce")
    return df


def convert_to_categorical(df, column):
    df = df.copy()
    df[column] = df[column].astype("category")
    return df


# 4.4 Categorical data tools

def standardize_case(df, columns, case="lower"):

    df = df.copy()
    for col in columns:
        if case == "lower":
            df[col] = df[col].astype(str).str.lower()
        elif case == "upper":
            df[col] = df[col].astype(str).str.upper()
        elif case == "title":
            df[col] = df[col].astype(str).str.title()
        df[col] = df[col].replace(['', 'nan', 'None', 'null'], np.nan)
    return df


def trim_whitespace(df, columns):
    df = df.copy()
    for col in columns: 
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace(['', 'nan', 'None', 'null'], np.nan)
    return df


def map_values(df, column, mapping_dict, set_unmatched_to_other=False):
    df = df.copy()
    if set_unmatched_to_other:
        mapped = df[column].map(mapping_dict)
        df[column] = mapped.fillna("Other")
    else:
        df[column] = df[column].replace(mapping_dict)
    return df


def group_rare_categories(df, column, threshold_pct, replacement="Other"):
    df = df.copy()
    freq = df[column].value_counts(normalize=True) * 100
    rare = freq[freq < threshold_pct].index
    df[column] = df[column].replace(rare, replacement)
    return df


def one_hot_encode(df, columns, drop_first=False):
    return pd.get_dummies(df, columns=columns, drop_first=drop_first,
                          dtype=int)


# 4.5 Numeric cleaning

def detect_outliers_iqr(df, column, factor=1.5):
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
    df = df.copy()
    df[column] = df[column].clip(lower=lower, upper=upper)
    return df


def remove_outlier_rows(df, column, mask):
    return df[~mask].reset_index(drop=True)


# 4.6Normalization

def min_max_scale(df, columns):
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
    df = df.copy()
    for col in columns:
        mean = df[col].mean()
        std = df[col].std()
        if std != 0:
            df[col] = (df[col] - mean) / std
        else:
            df[col] = 0.0
    return df


# 4.7 Column Operations

def rename_columns(df, rename_map):
    return df.rename(columns=rename_map)

def drop_columns(df, columns):
    return df.drop(columns=columns, errors="ignore")


def create_formula_column(df, new_name, formula_str):
    df = df.copy()
    try:
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
            df[new_name] = df.eval(expr)
    except Exception as e:
        raise ValueError(f"Could not evaluate formula '{formula_str}': {e}")
    return df


def bin_column(df, column, n_bins, method="equal_width", labels=None):
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
