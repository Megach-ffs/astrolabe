"""Tests for the validation rule engine."""

import pytest
import pandas as pd
import numpy as np
from utils.validation import ValidationRule, validate_rules, export_violations


@pytest.fixture
def sample_df():
    """Test DataFrame with known values."""
    return pd.DataFrame({
        "age": [25, 30, -5, 150, np.nan, 40],
        "status": ["A", "B", "A", "C", "B", np.nan],
        "score": [85, 90, 95, 110, 75, 80],
    })


class TestRangeValidation:
    def test_below_min(self, sample_df):
        rules = [ValidationRule("range", "age", {"min": 0})]
        result = validate_rules(sample_df, rules)
        assert len(result) >= 1
        assert any(result["detail"].str.contains("Below minimum"))

    def test_above_max(self, sample_df):
        rules = [ValidationRule("range", "score", {"max": 100})]
        result = validate_rules(sample_df, rules)
        assert len(result) >= 1
        assert any(result["detail"].str.contains("Above maximum"))

    def test_range_both(self, sample_df):
        rules = [ValidationRule("range", "age", {"min": 0, "max": 120})]
        result = validate_rules(sample_df, rules)
        assert len(result) >= 2  # -5 and 150

    def test_no_violations(self):
        df = pd.DataFrame({"x": [1, 2, 3]})
        rules = [ValidationRule("range", "x", {"min": 0, "max": 10})]
        result = validate_rules(df, rules)
        assert len(result) == 0


class TestAllowedValidation:
    def test_disallowed_values(self, sample_df):
        rules = [ValidationRule("allowed", "status", {"values": ["A", "B"]})]
        result = validate_rules(sample_df, rules)
        assert len(result) >= 1
        assert any(result["value"] == "C")

    def test_all_allowed(self):
        df = pd.DataFrame({"x": ["A", "B", "A"]})
        rules = [ValidationRule("allowed", "x", {"values": ["A", "B"]})]
        result = validate_rules(df, rules)
        assert len(result) == 0


class TestNonNullValidation:
    def test_null_detected(self, sample_df):
        rules = [ValidationRule("non_null", "age")]
        result = validate_rules(sample_df, rules)
        assert len(result) >= 1
        assert all(result["rule_type"] == "non_null")

    def test_no_nulls(self):
        df = pd.DataFrame({"x": [1, 2, 3]})
        rules = [ValidationRule("non_null", "x")]
        result = validate_rules(df, rules)
        assert len(result) == 0


class TestMultipleRules:
    def test_combined_rules(self, sample_df):
        rules = [
            ValidationRule("range", "age", {"min": 0, "max": 120}),
            ValidationRule("non_null", "status"),
            ValidationRule("allowed", "status", {"values": ["A", "B"]}),
        ]
        result = validate_rules(sample_df, rules)
        assert len(result) >= 4  # age violations + null + "C"

    def test_missing_column_ignored(self, sample_df):
        rules = [ValidationRule("range", "nonexistent", {"min": 0})]
        result = validate_rules(sample_df, rules)
        assert len(result) == 0


class TestExport:
    def test_export_csv(self, sample_df):
        rules = [ValidationRule("range", "age", {"min": 0})]
        violations = validate_rules(sample_df, rules)
        csv_bytes = export_violations(violations)
        assert isinstance(csv_bytes, bytes)
        assert b"row_index" in csv_bytes

    def test_export_empty(self):
        df = pd.DataFrame({"x": [1, 2]})
        rules = [ValidationRule("range", "x", {"min": 0})]
        violations = validate_rules(df, rules)
        csv_bytes = export_violations(violations)
        assert isinstance(csv_bytes, bytes)


class TestRuleSerialization:
    def test_to_dict(self):
        rule = ValidationRule("range", "age", {"min": 0, "max": 100})
        d = rule.to_dict()
        assert d["rule_type"] == "range"
        assert d["column"] == "age"
        assert d["params"] == {"min": 0, "max": 100}
