"""Tests for the export utility module."""

import pytest
import pandas as pd
import json
from utils.export import (
    to_csv_bytes, to_excel_bytes,
    generate_report, report_to_markdown, report_to_json_bytes,
    generate_json_recipe, generate_python_script,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, 35],
        "score": [90.5, 85.0, 92.3],
    })


@pytest.fixture
def sample_log():
    return [
        {
            "step_number": 1,
            "operation": "fill_missing",
            "params": {"strategy": "mean", "columns": ["age"]},
            "columns": ["age"],
            "timestamp": "2024-01-01T12:00:00",
        },
        {
            "step_number": 2,
            "operation": "remove_duplicates",
            "params": {"subset": None, "keep": "first"},
            "columns": ["all"],
            "timestamp": "2024-01-01T12:01:00",
        },
    ]


class TestCSVExport:
    def test_csv_bytes(self, sample_df):
        result = to_csv_bytes(sample_df)
        assert isinstance(result, bytes)
        assert b"name" in result
        assert b"Alice" in result

    def test_csv_rows(self, sample_df):
        result = to_csv_bytes(sample_df)
        lines = result.decode("utf-8").strip().split("\n")
        assert len(lines) == 4  # header + 3 rows


class TestExcelExport:
    def test_excel_bytes(self, sample_df):
        result = to_excel_bytes(sample_df)
        assert isinstance(result, bytes)
        assert len(result) > 100  # reasonable Excel size

    def test_excel_readable(self, sample_df):
        import io
        result = to_excel_bytes(sample_df)
        df_read = pd.read_excel(io.BytesIO(result), engine="openpyxl")
        assert len(df_read) == 3
        assert "name" in df_read.columns


class TestReport:
    def test_generate_report(self, sample_df, sample_log):
        report = generate_report(sample_log, sample_df, sample_df)
        assert report["total_steps"] == 2
        assert report["before"]["rows"] == 3
        assert report["after"]["rows"] == 3
        assert len(report["steps"]) == 2

    def test_report_contains_timestamps(self, sample_df, sample_log):
        report = generate_report(sample_log, sample_df, sample_df)
        assert "generated_at" in report

    def test_markdown_report(self, sample_df, sample_log):
        report = generate_report(sample_log, sample_df, sample_df)
        md = report_to_markdown(report)
        assert "# Transformation Report" in md
        assert "fill_missing" in md
        assert "Step 1" in md

    def test_markdown_empty_log(self, sample_df):
        report = generate_report([], sample_df, sample_df)
        md = report_to_markdown(report)
        assert "No transformations" in md

    def test_json_report(self, sample_df, sample_log):
        report = generate_report(sample_log, sample_df, sample_df)
        json_bytes = report_to_json_bytes(report)
        parsed = json.loads(json_bytes)
        assert parsed["total_steps"] == 2


class TestRecipe:
    def test_json_recipe(self, sample_log):
        result = generate_json_recipe(sample_log)
        parsed = json.loads(result)
        assert parsed["version"] == "1.0"
        assert len(parsed["steps"]) == 2
        assert parsed["steps"][0]["operation"] == "fill_missing"

    def test_recipe_empty(self):
        result = generate_json_recipe([])
        parsed = json.loads(result)
        assert len(parsed["steps"]) == 0


class TestPythonScript:
    def test_script_generated(self, sample_log):
        script = generate_python_script(sample_log, "test.csv")
        assert "import pandas" in script
        assert "test.csv" in script
        assert "fill_missing" in script or "fillna" in script

    def test_script_syntax(self, sample_log):
        """Generated script should be valid Python syntax."""
        script = generate_python_script(sample_log, "data.csv")
        compile(script, "<test>", "exec")  # raises SyntaxError if invalid

    def test_script_empty_log(self):
        script = generate_python_script([], "data.csv")
        assert "import pandas" in script
        compile(script, "<test>", "exec")
