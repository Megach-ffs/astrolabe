"""Tests for the data_loader module."""

import pytest
import pandas as pd
import json
import os


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def sample_csv_bytes():
    """Create sample CSV data as bytes."""
    csv_content = "name,age,city\nAlice,30,London\nBob,25,Paris\nCharlie,35,Berlin\n"
    return csv_content.encode("utf-8")


@pytest.fixture
def sample_json_list_bytes():
    """Create sample JSON list data as bytes."""
    data = [
        {"name": "Alice", "age": 30, "city": "London"},
        {"name": "Bob", "age": 25, "city": "Paris"},
    ]
    return json.dumps(data).encode("utf-8")


@pytest.fixture
def sample_json_dict_bytes():
    """Create sample JSON dict data as bytes."""
    data = {"name": ["Alice", "Bob"], "age": [30, 25], "city": ["London", "Paris"]}
    return json.dumps(data).encode("utf-8")


@pytest.fixture
def sample_excel_path(tmp_path):
    """Create a sample Excel file and return the path."""
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [30, 25, 35],
        "city": ["London", "Paris", "Berlin"],
    })
    path = tmp_path / "test.xlsx"
    df.to_excel(path, index=False, engine="openpyxl")
    return path


# ──────────────────────────────────────────────
# Tests for individual loaders
# ──────────────────────────────────────────────

class TestLoadCSV:
    """Tests for CSV loading."""

    def test_load_csv_basic(self, sample_csv_bytes):
        from utils.data_loader import load_csv
        df = load_csv(sample_csv_bytes, "test.csv")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["name", "age", "city"]

    def test_load_csv_dtypes(self, sample_csv_bytes):
        from utils.data_loader import load_csv
        df = load_csv(sample_csv_bytes, "test.csv")
        assert df["age"].dtype in ["int64", "int32"]
        assert df["name"].dtype == "object"


class TestLoadJSON:
    """Tests for JSON loading."""

    def test_load_json_list(self, sample_json_list_bytes):
        from utils.data_loader import load_json
        df = load_json(sample_json_list_bytes, "test.json")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_load_json_dict(self, sample_json_dict_bytes):
        from utils.data_loader import load_json
        df = load_json(sample_json_dict_bytes, "test.json")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "name" in df.columns


class TestLoadExcel:
    """Tests for Excel loading."""

    def test_load_excel_basic(self, sample_excel_path):
        from utils.data_loader import load_excel
        with open(sample_excel_path, "rb") as f:
            file_bytes = f.read()
        df = load_excel(file_bytes, "test.xlsx")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "name" in df.columns


# ──────────────────────────────────────────────
# Tests for load_uploaded_file
# ──────────────────────────────────────────────

class TestLoadUploadedFile:
    """Tests for the main upload dispatcher."""

    def test_none_raises_error(self):
        from utils.data_loader import load_uploaded_file
        with pytest.raises(ValueError, match="No file uploaded"):
            load_uploaded_file(None)

    def test_unsupported_format(self):
        from utils.data_loader import load_uploaded_file

        class FakeFile:
            name = "data.xml"
            def getvalue(self):
                return b"<data></data>"

        with pytest.raises(ValueError, match="Unsupported file format"):
            load_uploaded_file(FakeFile())

    def test_csv_dispatch(self, sample_csv_bytes):
        from utils.data_loader import load_uploaded_file

        class FakeFile:
            name = "data.csv"
            def getvalue(self):
                return sample_csv_bytes

        # Need to bind the bytes
        fake = FakeFile()
        fake.getvalue = lambda: sample_csv_bytes
        df = load_uploaded_file(fake)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
