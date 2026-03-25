"""Tests for the profiler module."""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_df():
    """Create a sample DataFrame with mixed types and quality issues."""
    np.random.seed(42)
    df = pd.DataFrame({
        "id": range(1, 101),
        "name": [f"Item_{i}" for i in range(1, 101)],
        "price": np.random.uniform(10, 1000, 100).round(2),
        "category": np.random.choice(["A", "B", "C", "D"], 100),
        "rating": np.random.uniform(1, 5, 100).round(1),
        "date": pd.date_range("2024-01-01", periods=100, freq="D"),
    })
    # Inject some NaN values
    df.loc[5:10, "price"] = np.nan
    df.loc[20:25, "category"] = np.nan
    df.loc[50:52, "rating"] = np.nan

    # Add duplicate rows
    df = pd.concat([df, df.iloc[:3]], ignore_index=True)
    return df


class TestProfileDataframe:
    """Tests for the profile_dataframe function."""

    def test_returns_dict(self, sample_df):
        from utils.profiler import profile_dataframe
        result = profile_dataframe(sample_df)
        assert isinstance(result, dict)

    def test_shape_correct(self, sample_df):
        from utils.profiler import profile_dataframe
        result = profile_dataframe(sample_df)
        assert result["shape"] == sample_df.shape

    def test_columns_info(self, sample_df):
        from utils.profiler import profile_dataframe
        result = profile_dataframe(sample_df)
        assert len(result["columns"]) == len(sample_df.columns)
        col_names = [c["name"] for c in result["columns"]]
        assert "id" in col_names
        assert "price" in col_names

    def test_missing_detected(self, sample_df):
        from utils.profiler import profile_dataframe
        result = profile_dataframe(sample_df)
        missing_cols = result["missing"]["Column"].tolist()
        assert "price" in missing_cols
        assert "category" in missing_cols

    def test_duplicates_detected(self, sample_df):
        from utils.profiler import profile_dataframe
        result = profile_dataframe(sample_df)
        assert result["duplicates"]["count"] > 0

    def test_numeric_summary_exists(self, sample_df):
        from utils.profiler import profile_dataframe
        result = profile_dataframe(sample_df)
        assert not result["numeric_summary"].empty
        assert "price" in result["numeric_summary"].index

    def test_categorical_summary_exists(self, sample_df):
        from utils.profiler import profile_dataframe
        result = profile_dataframe(sample_df)
        assert not result["categorical_summary"].empty

    def test_empty_dataframe(self):
        from utils.profiler import profile_dataframe
        df = pd.DataFrame()
        result = profile_dataframe(df)
        assert result["shape"] == (0, 0)
        assert result["duplicates"]["count"] == 0
