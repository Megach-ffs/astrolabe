import json
import streamlit as sl

from pydantic import BaseModel, Field
from typing import List, Optional


class CleaningSuggestion(BaseModel):
    """A single cleaning operation suggestion."""
    operation: str = Field(description="Operation name matching our cleaning functions")
    params: dict = Field(description="Parameters for the operation")
    description: str = Field(description="Human-readable explanation of what this does")
    affected_columns: List[str] = Field(description="Column names affected")


class CleaningSuggestionList(BaseModel):
    """List of cleaning suggestions."""
    suggestions: List[CleaningSuggestion]


class ChartSuggestion(BaseModel):
    """A single chart suggestion."""
    chart_type: str = Field(description="One of: Histogram, Box Plot, Scatter Plot, Line Chart, Bar Chart, Heatmap")
    x_column: str = Field(description="Column for X axis")
    y_column: Optional[str] = Field(default=None, description="Column for Y axis (if applicable)")
    color_column: Optional[str] = Field(default=None, description="Column for color/grouping")
    reason: str = Field(description="Why this chart is useful for this data")


class ChartSuggestionList(BaseModel):
    """List of chart suggestions."""
    suggestions: List[ChartSuggestion]


# Client manager

_client = None
MODEL = "gemini-2.5-flash"


def _get_client():
    """
    Lazy-init the Gemini client.
    Returns None if no API key is configured.
    """
    global _client
    if _client is not None:
        return _client

    try:
        api_key = sl.secrets["ai"]["gemini_api_key"]
        if not api_key or api_key.startswith("AIza..."):
            return None
        from google import genai
        _client = genai.Client(api_key=api_key)
        return _client
    except Exception:
        return None


def is_available():
    """Check if the AI assistant is configured and available."""
    return _get_client() is not None


# Data context builder

def _build_data_context(df, max_sample_rows=5):
    """
    Build a compact text summary of the DataFrame for use in prompts.
    Keeps token count low while giving Gemini enough context.
    """
    lines = [
        f"Dataset: {len(df)} rows × {len(df.columns)} columns",
        "",
        "Columns:",
    ]

    for col in df.columns:
        dtype = str(df[col].dtype)
        null_count = int(df[col].isna().sum())
        null_pct = f"{null_count / len(df) * 100:.1f}%" if len(df) > 0 else "0%"
        unique = df[col].nunique()

        line = f"  - {col} (dtype={dtype}, nulls={null_count} [{null_pct}], unique={unique})"

        # adding sample values
        if df[col].dtype == "object" or str(df[col].dtype) == "category":
            top_vals = df[col].dropna().value_counts().head(5).index.tolist()
            line += f" top_values={top_vals}"
        elif df[col].dtype in ("int64", "float64"):
            line += f" range=[{df[col].min()}, {df[col].max()}]"

        lines.append(line)

    # Sample rows
    lines.append("")
    lines.append(f"Sample rows (first {max_sample_rows}):")
    sample = df.head(max_sample_rows).to_string(index=False)
    lines.append(sample)

    return "\n".join(lines)


# System prompts

CLEANING_SYSTEM_PROMPT = """You are a data cleaning assistant embedded in a Streamlit application.

The user has loaded a dataset. Based on the data profile provided and the user's request,
suggest specific cleaning operations from our AVAILABLE OPERATIONS list.

AVAILABLE OPERATIONS (you MUST only suggest these):
- fill_missing: params={strategy: "mean"|"median"|"mode"|"constant"|"ffill"|"bfill", columns: [...]}
- remove_duplicates: params={subset: [...] or null for all, keep: "first"|"last"}
- convert_type: params={target: "numeric"|"datetime"|"categorical"|"numeric (dirty)", columns: [...]}
- standardize_categorical: params={operations: ["trim","lower"|"upper"|"title"], columns: [...]}
- map_values: params={mapping: {"old": "new", ...}, column: "col_name"}
- group_rare: params={threshold: number (percent), column: "col_name"}
- one_hot_encode: params={columns: [...], drop_first: true|false}
- outlier_treatment: params={method: "IQR"|"Z-score", action: "Cap"|"Remove", columns: [...]}
- scale_columns: params={method: "min_max"|"z_score", columns: [...]}
- rename_column: params={old: "old_name", new: "new_name"}
- drop_columns: params={columns: [...]}

Rules:
- Only suggest operations that make sense for the data
- Each suggestion must reference actual column names from the dataset
- Be specific with parameters
- Keep descriptions concise
- Maximum 5 suggestions per request"""


CHART_SYSTEM_PROMPT = """You are a data visualization assistant.

Based on the data profile, suggest 3 useful charts that would reveal insights.

Available chart types: Histogram, Box Plot, Scatter Plot, Line Chart, Bar Chart, Heatmap

Rules:
- Only reference actual column names from the dataset
- x_column and y_column must be real column names or null
- For Histogram: x_column is the numeric value. y_column is null. color_column is an optional categorical group.
- For Box Plot: x_column is the NUMERIC value to distribute. y_column is null. color_column is the optional CATEGORICAL group.
- For Scatter Plot: x_column is numeric, y_column is numeric, color_column is optional categorical.
- For Line Chart: x_column is time/order, y_column is numeric, color_column is optional categorical.
- For Bar Chart: x_column is categorical, y_column is numeric, color_column is optional categorical.
- For Heatmap: x_column and y_column are numeric. color_column must be null.
- Each suggestion should reveal different insights
- Keep reasons concise (1 sentence)"""


DATA_DICT_SYSTEM_PROMPT = """You are a data analyst. Generate a data dictionary for the dataset.

For each column, provide:
1. The column name
2. Inferred meaning/description
3. Data type assessment
4. Potential data quality issues

Format the output as a Markdown table with columns:
| Column | Description | Type | Issues |

Be concise. If no issues, write "None"."""


# natural language cleaning

def get_cleaning_suggestions(df, user_prompt):

    client = _get_client()
    if client is None:
        return None

    data_context = _build_data_context(df)
    full_prompt = f"""Data Profile:
{data_context}

User Request: {user_prompt}

Suggest cleaning operations to fulfill this request."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
            config={
                "system_instruction": CLEANING_SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "response_json_schema": CleaningSuggestionList.model_json_schema(),
                "temperature": 0.2,
            },
        )
        result = CleaningSuggestionList.model_validate_json(response.text)
        return [s.model_dump() for s in result.suggestions]
    except Exception as e:
        return {"error": str(e)}


# chart suggestions

def get_chart_suggestions(df):
    """
    Get chart suggestions from Gemini based on the dataset profile.

    Returns:
        list of ChartSuggestion dicts, or None if unavailable.
    """
    client = _get_client()
    if client is None:
        return None

    data_context = _build_data_context(df)
    full_prompt = f"""Data Profile:
{data_context}

Suggest 3 insightful charts for this dataset."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
            config={
                "system_instruction": CHART_SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "response_json_schema": ChartSuggestionList.model_json_schema(),
                "temperature": 0.3,
            },
        )
        result = ChartSuggestionList.model_validate_json(response.text)
        return [s.model_dump() for s in result.suggestions]
    except Exception as e:
        return {"error": str(e)}


# data dictionary generator

def generate_data_dictionary(df):
    """
    Generate a data dictionary for the dataset using Gemini.

    Returns:
        str (Markdown), or None if unavailable.
    """
    client = _get_client()
    if client is None:
        return None

    data_context = _build_data_context(df, max_sample_rows=3)
    full_prompt = f"""Data Profile:
{data_context}

Generate a data dictionary as a Markdown table."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=full_prompt,
            config={
                "system_instruction": DATA_DICT_SYSTEM_PROMPT,
                "temperature": 0.2,
            },
        )
        return response.text
    except Exception as e:
        return f"Error generating data dictionary: {e}"


# general cha

def chat_stream(df, messages):
    """
    Streaming chat with data context.

    Args:
        df: Current DataFrame for context.
        messages: List of {"role": "user"/"assistant", "content": "..."} dicts.

    Yields:
        str chunks for sl.write_stream().
    """
    client = _get_client()
    if client is None:
        yield "⚠️ AI assistant is not configured. Add your Gemini API key to `.streamlit/secrets.toml`."
        return

    data_context = _build_data_context(df, max_sample_rows=3)
    system = f"""You are a helpful data analysis assistant embedded in a Streamlit data wrangling app.
The user has loaded a dataset. Here is its profile:

{data_context}

You can help with:
- Explaining data patterns and issues
- Suggesting cleaning strategies  
- Interpreting chart results
- Writing pandas code snippets

Keep responses concise and actionable. Use markdown formatting."""

    # Build contents for multi-turn convo
    contents = []
    for msg in messages:
        contents.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}],
        })

    try:
        stream = client.models.generate_content_stream(
            model=MODEL,
            contents=contents,
            config={
                "system_instruction": system,
                "temperature": 0.4,
            },
        )
        for chunk in stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"\n\n⚠️ Error: {e}"
