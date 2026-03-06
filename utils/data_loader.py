"""
Data Loader utilities.

Handles file upload parsing for CSV, Excel, JSON, and Google Sheets.
All loading functions use @st.cache_data for performance.
"""

import streamlit as sl
import pandas as pd
import json
from io import BytesIO


@sl.cache_data
def load_csv(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load a CSV file from uploaded bytes."""
    return pd.read_csv(BytesIO(file_bytes))


@sl.cache_data
def load_excel(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load an Excel (.xlsx) file from uploaded bytes."""
    return pd.read_excel(BytesIO(file_bytes), engine="openpyxl")


@sl.cache_data
def load_json(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load a JSON file from uploaded bytes."""
    data = json.loads(file_bytes.decode("utf-8"))
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict):
        # Try common JSON structures
        if any(isinstance(v, list) for v in data.values()):
            return pd.DataFrame(data)
        else:
            return pd.DataFrame([data])
    else:
        raise ValueError("Unsupported JSON structure. Expected a list or dict.")


def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    """
    Parse an uploaded file based on its extension.

    Args:
        uploaded_file: Streamlit UploadedFile object.

    Returns:
        pd.DataFrame

    Raises:
        ValueError: If file format is unsupported.
    """
    if uploaded_file is None:
        raise ValueError("No file uploaded.")

    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    if filename.endswith(".csv"):
        return load_csv(file_bytes, filename)
    elif filename.endswith((".xlsx", ".xls")):
        return load_excel(file_bytes, filename)
    elif filename.endswith(".json"):
        return load_json(file_bytes, filename)
    else:
        raise ValueError(
            f"Unsupported file format: {filename}. "
            "Please upload a CSV, Excel (.xlsx), or JSON file."
        )
