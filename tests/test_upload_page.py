"""Tests for the Upload & Overview page integration."""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def ecommerce_df():
    """Load the ecommerce sample dataset."""
    return pd.read_csv("sample_data/ecommerce_orders.csv")


@pytest.fixture
def weather_df():
    """Load the weather sample dataset."""
    return pd.read_excel("sample_data/weather_stations.xlsx")


class TestProfileIntegration:
    """Test profiling works correctly with sample datasets."""

    def test_csv_profiling(self, ecommerce_df):
        from utils.profiler import profile_dataframe
        profile = profile_dataframe(ecommerce_df)

        assert profile["shape"][0] >= 1000
        assert profile["shape"][1] >= 8
        assert len(profile["columns"]) == profile["shape"][1]
        assert profile["duplicates"]["count"] > 0

    def test_excel_profiling(self, weather_df):
        from utils.profiler import profile_dataframe
        profile = profile_dataframe(weather_df)

        assert profile["shape"][0] >= 1000
        assert profile["shape"][1] >= 8

    def test_missing_values_detected(self, ecommerce_df):
        from utils.profiler import profile_dataframe
        profile = profile_dataframe(ecommerce_df)

        missing = profile["missing"]
        assert not missing.empty, "Should detect missing values in ecommerce data"
        assert "Missing Count" in missing.columns
        assert "Missing %" in missing.columns

    def test_numeric_summary(self, ecommerce_df):
        from utils.profiler import profile_dataframe
        profile = profile_dataframe(ecommerce_df)

        assert not profile["numeric_summary"].empty

    def test_categorical_summary(self, ecommerce_df):
        from utils.profiler import profile_dataframe
        profile = profile_dataframe(ecommerce_df)

        assert not profile["categorical_summary"].empty

    def test_column_info_completeness(self, weather_df):
        from utils.profiler import profile_dataframe
        profile = profile_dataframe(weather_df)

        for col_info in profile["columns"]:
            assert "name" in col_info
            assert "dtype" in col_info
            assert "null_count" in col_info
            assert "null_pct" in col_info
            assert "unique_count" in col_info


class TestDataLoaderEdgeCases:
    """Test edge cases in data loading."""

    def test_empty_csv(self, tmp_path):
        from utils.data_loader import load_csv
        csv_bytes = b"col1,col2\n"
        df = load_csv(csv_bytes, "empty.csv")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_single_row_csv(self, tmp_path):
        from utils.data_loader import load_csv
        csv_bytes = b"name,age\nAlice,30\n"
        df = load_csv(csv_bytes, "single.csv")
        assert len(df) == 1

    def test_all_null_column(self):
        """Profile should handle a column that is entirely null."""
        from utils.profiler import profile_dataframe
        df = pd.DataFrame({
            "a": [1, 2, 3],
            "b": [np.nan, np.nan, np.nan],
        })
        profile = profile_dataframe(df)
        # Find column b info
        b_info = [c for c in profile["columns"] if c["name"] == "b"][0]
        assert b_info["null_pct"] == 100.0

    def test_google_sheet_missing_credentials(self):
        """Google Sheets should raise ValueError with invalid credentials."""
        from utils.data_loader import load_google_sheet
        with pytest.raises((ValueError, Exception)):
            load_google_sheet("https://docs.google.com/spreadsheets/d/fake")
