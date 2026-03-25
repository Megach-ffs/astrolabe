"""Tests for the cleaning utility module."""

import pytest
import pandas as pd
import numpy as np
from utils import cleaning


@pytest.fixture
def sample_df():
    """DataFrame with mixed types and quality issues."""
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie", "  Dave ", "eve"],
        "age": [25, np.nan, 35, 40, 28],
        "salary": [50000, 60000, np.nan, 80000, 55000],
        "category": ["A", "B", "A", "C", "B"],
        "price": ["$1,200.50", "800", "$450.00", "1,100", "abc"],
    })


@pytest.fixture
def dup_df():
    """DataFrame with duplicates."""
    return pd.DataFrame({
        "id": [1, 2, 3, 1, 2],
        "val": ["a", "b", "c", "a", "b"],
    })


@pytest.fixture
def numeric_df():
    """DataFrame for numeric operations."""
    np.random.seed(42)
    data = np.random.normal(50, 10, 100)
    data[0] = 200   # outlier
    data[1] = -100   # outlier
    return pd.DataFrame({"value": data, "group": ["A", "B"] * 50})


# ──────────────────────────────────────────────
# 4.1 Missing Values
# ──────────────────────────────────────────────

class TestFillMissing:
    def test_fill_mean(self, sample_df):
        result = cleaning.fill_missing(sample_df, ["age"], "mean")
        assert result["age"].isna().sum() == 0

    def test_fill_median(self, sample_df):
        result = cleaning.fill_missing(sample_df, ["salary"], "median")
        assert result["salary"].isna().sum() == 0

    def test_fill_mode(self, sample_df):
        result = cleaning.fill_missing(sample_df, ["age"], "mode")
        assert result["age"].isna().sum() == 0

    def test_fill_constant(self, sample_df):
        result = cleaning.fill_missing(sample_df, ["age"], "constant", constant=0)
        assert result["age"].isna().sum() == 0
        assert result.loc[1, "age"] == 0

    def test_fill_ffill(self, sample_df):
        result = cleaning.fill_missing(sample_df, ["age"], "ffill")
        assert result["age"].isna().sum() == 0
        assert result.loc[1, "age"] == 25  # forward filled from row 0

    def test_fill_bfill(self, sample_df):
        result = cleaning.fill_missing(sample_df, ["age"], "bfill")
        assert result["age"].isna().sum() == 0
        assert result.loc[1, "age"] == 35  # backward filled from row 2

    def test_does_not_mutate(self, sample_df):
        original_nulls = sample_df["age"].isna().sum()
        cleaning.fill_missing(sample_df, ["age"], "mean")
        assert sample_df["age"].isna().sum() == original_nulls


class TestDropRows:
    def test_drop_rows_with_nulls(self, sample_df):
        result = cleaning.drop_rows_with_nulls(sample_df, ["age"])
        assert result["age"].isna().sum() == 0
        assert len(result) == 4


class TestDropColumnsByThreshold:
    def test_drop_high_null_columns(self):
        df = pd.DataFrame({
            "a": [1, 2, 3, 4, 5],
            "b": [np.nan, np.nan, np.nan, np.nan, 5],  # 80% null
            "c": [1, np.nan, 3, 4, 5],  # 20% null
        })
        result = cleaning.drop_columns_by_threshold(df, 50)
        assert "b" not in result.columns
        assert "a" in result.columns
        assert "c" in result.columns


# ──────────────────────────────────────────────
# 4.2 Duplicates
# ──────────────────────────────────────────────

class TestDuplicates:
    def test_find_full_row_duplicates(self, dup_df):
        result = cleaning.find_duplicates(dup_df)
        assert len(result) == 4  # rows 0,3 and 1,4 are dupes (all shown)

    def test_find_subset_duplicates(self, dup_df):
        result = cleaning.find_duplicates(dup_df, subset=["id"])
        assert len(result) == 4

    def test_remove_duplicates_keep_first(self, dup_df):
        result = cleaning.remove_duplicates(dup_df, keep="first")
        assert len(result) == 3

    def test_remove_duplicates_keep_last(self, dup_df):
        result = cleaning.remove_duplicates(dup_df, keep="last")
        assert len(result) == 3


# ──────────────────────────────────────────────
# 4.3 Data Types & Parsing
# ──────────────────────────────────────────────

class TestDataTypes:
    def test_clean_dirty_numeric(self, sample_df):
        result = cleaning.clean_dirty_numeric(sample_df, "price")
        assert result["price"].dtype in [np.float64, float]
        assert result.loc[0, "price"] == 1200.50
        assert pd.isna(result.loc[4, "price"])  # "abc" → NaN

    def test_convert_to_numeric(self, sample_df):
        df = pd.DataFrame({"x": ["1", "2", "3", "bad"]})
        result = cleaning.convert_to_numeric(df, "x")
        assert result["x"].dtype == np.float64
        assert pd.isna(result.loc[3, "x"])

    def test_convert_to_datetime(self):
        df = pd.DataFrame({"date": ["2024-01-01", "2024-06-15", "bad"]})
        result = cleaning.convert_to_datetime(df, "date")
        assert pd.api.types.is_datetime64_any_dtype(result["date"])

    def test_convert_to_categorical(self, sample_df):
        result = cleaning.convert_to_categorical(sample_df, "category")
        assert result["category"].dtype.name == "category"


# ──────────────────────────────────────────────
# 4.4 Categorical Data Tools
# ──────────────────────────────────────────────

class TestCategorical:
    def test_standardize_lower(self, sample_df):
        result = cleaning.standardize_case(sample_df, ["name"], "lower")
        assert result.loc[0, "name"] == "alice"

    def test_standardize_title(self, sample_df):
        result = cleaning.standardize_case(sample_df, ["name"], "title")
        assert result.loc[4, "name"] == "Eve"

    def test_trim_whitespace(self, sample_df):
        result = cleaning.trim_whitespace(sample_df, ["name"])
        assert result.loc[3, "name"] == "Dave"

    def test_map_values(self, sample_df):
        mapping = {"A": "Alpha", "B": "Beta"}
        result = cleaning.map_values(sample_df, "category", mapping)
        assert result.loc[0, "category"] == "Alpha"
        assert result.loc[3, "category"] == "C"  # unmatched unchanged

    def test_map_values_with_other(self, sample_df):
        mapping = {"A": "Alpha", "B": "Beta"}
        result = cleaning.map_values(
            sample_df, "category", mapping, set_unmatched_to_other=True
        )
        assert result.loc[3, "category"] == "Other"

    def test_group_rare(self):
        df = pd.DataFrame({"cat": ["A"] * 90 + ["B"] * 5 + ["C"] * 3 + ["D"] * 2})
        result = cleaning.group_rare_categories(df, "cat", 5)
        assert "C" not in result["cat"].values
        assert "D" not in result["cat"].values
        assert "Other" in result["cat"].values

    def test_one_hot(self, sample_df):
        result = cleaning.one_hot_encode(sample_df, ["category"])
        assert "category" not in result.columns
        assert any("category_" in c for c in result.columns)


# ──────────────────────────────────────────────
# 4.5 Numeric Cleaning
# ──────────────────────────────────────────────

class TestOutliers:
    def test_iqr_detection(self, numeric_df):
        stats = cleaning.detect_outliers_iqr(numeric_df, "value")
        assert stats["count"] >= 2  # at least our injected outliers
        assert "mask" in stats

    def test_zscore_detection(self, numeric_df):
        stats = cleaning.detect_outliers_zscore(numeric_df, "value")
        assert stats["count"] >= 2
        assert "mask" in stats

    def test_cap_outliers(self, numeric_df):
        result = cleaning.cap_outliers(numeric_df, "value", 0, 100)
        assert result["value"].min() >= 0
        assert result["value"].max() <= 100

    def test_remove_outliers(self, numeric_df):
        stats = cleaning.detect_outliers_iqr(numeric_df, "value")
        result = cleaning.remove_outlier_rows(
            numeric_df, "value", stats["mask"]
        )
        assert len(result) < len(numeric_df)


# ──────────────────────────────────────────────
# 4.6 Scaling
# ──────────────────────────────────────────────

class TestScaling:
    def test_min_max(self):
        df = pd.DataFrame({"x": [10.0, 20.0, 30.0, 40.0, 50.0]})
        result = cleaning.min_max_scale(df, ["x"])
        assert abs(result["x"].min() - 0.0) < 1e-9
        assert abs(result["x"].max() - 1.0) < 1e-9

    def test_z_score(self):
        df = pd.DataFrame({"x": [10.0, 20.0, 30.0, 40.0, 50.0]})
        result = cleaning.z_score_scale(df, ["x"])
        assert abs(result["x"].mean()) < 1e-9
        assert abs(result["x"].std() - 1.0) < 0.2  # approx 1

    def test_scale_constant_column(self):
        df = pd.DataFrame({"x": [5.0, 5.0, 5.0]})
        result = cleaning.min_max_scale(df, ["x"])
        assert (result["x"] == 0.0).all()


# ──────────────────────────────────────────────
# 4.7 Column Operations
# ──────────────────────────────────────────────

class TestColumnOps:
    def test_rename(self, sample_df):
        result = cleaning.rename_columns(sample_df, {"name": "full_name"})
        assert "full_name" in result.columns
        assert "name" not in result.columns

    def test_drop(self, sample_df):
        result = cleaning.drop_columns(sample_df, ["price", "category"])
        assert "price" not in result.columns
        assert "category" not in result.columns

    def test_formula_divide(self):
        df = pd.DataFrame({"a": [10.0, 20.0], "b": [2.0, 5.0]})
        result = cleaning.create_formula_column(df, "ratio", "a / b")
        assert abs(result.loc[0, "ratio"] - 5.0) < 1e-9

    def test_formula_log(self):
        df = pd.DataFrame({"x": [1.0, 10.0, 100.0]})
        result = cleaning.create_formula_column(df, "log_x", "log(x)")
        assert abs(result.loc[0, "log_x"] - 0.0) < 1e-9

    def test_formula_demean(self):
        df = pd.DataFrame({"x": [10.0, 20.0, 30.0]})
        result = cleaning.create_formula_column(df, "x_dm", "x - mean(x)")
        assert abs(result["x_dm"].mean()) < 1e-9

    def test_formula_invalid(self):
        df = pd.DataFrame({"x": [1, 2]})
        with pytest.raises(ValueError):
            cleaning.create_formula_column(df, "bad", "nonexistent / 0")

    def test_bin_equal_width(self):
        df = pd.DataFrame({"x": range(100)})
        result = cleaning.bin_column(df, "x", 4, "equal_width")
        assert "x_binned" in result.columns
        assert result["x_binned"].nunique() == 4

    def test_bin_quantile(self):
        df = pd.DataFrame({"x": range(100)})
        result = cleaning.bin_column(df, "x", 4, "quantile")
        assert "x_binned" in result.columns
