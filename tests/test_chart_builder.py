"""Tests for the chart builder utility module."""

import pytest
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from utils import chart_builder

matplotlib.use("Agg")


@pytest.fixture
def sample_df():
    """DataFrame with mixed types for charting."""
    np.random.seed(42)
    return pd.DataFrame({
        "x_num": np.random.normal(50, 10, 100),
        "y_num": np.random.normal(100, 20, 100),
        "category": np.random.choice(["A", "B", "C"], 100),
        "date": pd.date_range("2024-01-01", periods=100, freq="D"),
    })


# ──────────────────────────────────────────────
# Filter tests
# ──────────────────────────────────────────────

class TestFilter:
    def test_category_filter(self, sample_df):
        result = chart_builder.filter_dataframe(
            sample_df, {"category": ["A", "B"]}
        )
        assert result["category"].isin(["A", "B"]).all()
        assert len(result) < len(sample_df)

    def test_numeric_range_filter(self, sample_df):
        result = chart_builder.filter_dataframe(
            sample_df, {"x_num": (40, 60)}
        )
        assert result["x_num"].min() >= 40
        assert result["x_num"].max() <= 60

    def test_combined_filter(self, sample_df):
        result = chart_builder.filter_dataframe(
            sample_df, {
                "category": ["A"],
                "x_num": (30, 70),
            }
        )
        assert result["category"].eq("A").all()
        assert result["x_num"].min() >= 30

    def test_missing_column_ignored(self, sample_df):
        result = chart_builder.filter_dataframe(
            sample_df, {"nonexistent": ["val"]}
        )
        assert len(result) == len(sample_df)


# ──────────────────────────────────────────────
# Matplotlib chart tests
# ──────────────────────────────────────────────

class TestHistogram:
    def test_basic(self, sample_df):
        fig = chart_builder.build_histogram(sample_df, "x_num")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_with_color(self, sample_df):
        fig = chart_builder.build_histogram(
            sample_df, "x_num", color_col="category"
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestBoxPlot:
    def test_basic(self, sample_df):
        fig = chart_builder.build_box_plot(sample_df, "x_num")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_grouped(self, sample_df):
        fig = chart_builder.build_box_plot(
            sample_df, "x_num", group_col="category"
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestScatter:
    def test_basic(self, sample_df):
        fig = chart_builder.build_scatter(sample_df, "x_num", "y_num")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_with_color(self, sample_df):
        fig = chart_builder.build_scatter(
            sample_df, "x_num", "y_num", color_col="category"
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestLineChart:
    def test_basic(self, sample_df):
        fig = chart_builder.build_line_chart(
            sample_df, "date", "y_num"
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_with_color(self, sample_df):
        fig = chart_builder.build_line_chart(
            sample_df, "date", "y_num", color_col="category"
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestBarChart:
    def test_basic(self, sample_df):
        fig = chart_builder.build_bar_chart(
            sample_df, "category", "x_num", agg="mean"
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_top_n(self, sample_df):
        fig = chart_builder.build_bar_chart(
            sample_df, "category", "x_num", agg="sum", top_n=2
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_count(self, sample_df):
        fig = chart_builder.build_bar_chart(
            sample_df, "category", "x_num", agg="count"
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestHeatmap:
    def test_basic(self, sample_df):
        fig = chart_builder.build_heatmap(sample_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_selected_columns(self, sample_df):
        fig = chart_builder.build_heatmap(
            sample_df, columns=["x_num", "y_num"]
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


# ──────────────────────────────────────────────
# PNG export test
# ──────────────────────────────────────────────

class TestExport:
    def test_fig_to_png(self, sample_df):
        fig = chart_builder.build_histogram(sample_df, "x_num")
        png_bytes = chart_builder.fig_to_png_bytes(fig)
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 1000  # reasonable PNG size
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"  # PNG header
        plt.close(fig)
