import pytest
import pandas as pd
from utils import ai_assistant

def test_build_data_context():
    """Test that data context correctly summarizes a dataframe."""
    df = pd.DataFrame({
        "name": ["Alice", "Bob", None],
        "age": [25, 30, 35],
        "price": [10.5, 20.0, None]
    })
    
    context = ai_assistant._build_data_context(df, max_sample_rows=2)
    
    # Check shape
    assert "3 rows" in context
    assert "3 columns" in context
    
    # Check column info
    assert "age (dtype=int64" in context
    assert "nulls=0" in context
    assert "name (dtype=object" in context
    assert "nulls=1" in context
    
    # Check samples
    assert "Alice" in context
    assert "Bob" in context
    assert "25" in context

def test_ai_unavailable_fallback(monkeypatch):
    """Test that AI features gracefully fallback when API key is not configured."""
    # Force _client to be None
    monkeypatch.setattr(ai_assistant, "_client", None)
    monkeypatch.setattr(ai_assistant, "_get_client", lambda: None)
    
    df = pd.DataFrame({"a": [1, 2]})
    
    # Cleaning fallback
    assert ai_assistant.get_cleaning_suggestions(df, "clean it") is None
    
    # Chart fallback
    assert ai_assistant.get_chart_suggestions(df) is None
    
    # Dictionary fallback
    assert ai_assistant.generate_data_dictionary(df) is None
    
    # Stream fallback
    stream = list(ai_assistant.chat_stream(df, [{"role": "user", "content": "hello"}]))
    assert len(stream) > 0
    assert "⚠️" in stream[0]
