"""
Data Validation Rule Engine.

Lets users define validation rules and checks them against the dataset,
reporting violations in a structured format.
"""

import pandas as pd


class ValidationRule:
    """Single validation rule definition."""

    def __init__(self, rule_type, column, params=None):
        """
        Args:
            rule_type: 'range', 'allowed', or 'non_null'.
            column: Column name to validate.
            params: Dict of rule parameters:
                - range: {'min': float, 'max': float}
                - allowed: {'values': list}
                - non_null: {} (no params needed)
        """
        self.rule_type = rule_type
        self.column = column
        self.params = params or {}

    def to_dict(self):
        """Serialize the rule to a dictionary."""
        return {
            "rule_type": self.rule_type,
            "column": self.column,
            "params": self.params,
        }

    def __repr__(self):
        return f"ValidationRule({self.rule_type}, {self.column}, {self.params})"


def validate_rules(df, rules):
    """
    Validate a DataFrame against a list of rules.

    Args:
        df: Input DataFrame.
        rules: List of ValidationRule objects.

    Returns:
        pd.DataFrame with columns: row_index, column, rule_type, value, detail
    """
    violations = []

    for rule in rules:
        col = rule.column
        if col not in df.columns:
            continue

        if rule.rule_type == "range":
            min_val = rule.params.get("min")
            max_val = rule.params.get("max")
            series = pd.to_numeric(df[col], errors="coerce")

            if min_val is not None:
                mask = series < min_val
                for idx in df.index[mask]:
                    violations.append({
                        "row_index": int(idx),
                        "column": col,
                        "rule_type": "range",
                        "value": str(df.at[idx, col]),
                        "detail": f"Below minimum ({min_val})",
                    })

            if max_val is not None:
                mask = series > max_val
                for idx in df.index[mask]:
                    violations.append({
                        "row_index": int(idx),
                        "column": col,
                        "rule_type": "range",
                        "value": str(df.at[idx, col]),
                        "detail": f"Above maximum ({max_val})",
                    })

        elif rule.rule_type == "allowed":
            allowed = rule.params.get("values", [])
            if allowed:
                mask = ~df[col].isin(allowed) & df[col].notna()
                for idx in df.index[mask]:
                    violations.append({
                        "row_index": int(idx),
                        "column": col,
                        "rule_type": "allowed",
                        "value": str(df.at[idx, col]),
                        "detail": f"Not in allowed values: {allowed}",
                    })

        elif rule.rule_type == "non_null":
            mask = df[col].isna()
            for idx in df.index[mask]:
                violations.append({
                    "row_index": int(idx),
                    "column": col,
                    "rule_type": "non_null",
                    "value": "NaN",
                    "detail": "Null value found",
                })

    if not violations:
        return pd.DataFrame(
            columns=["row_index", "column", "rule_type", "value", "detail"]
        )

    return pd.DataFrame(violations)


def export_violations(violations_df):
    """
    Export violations DataFrame as CSV bytes for download.

    Args:
        violations_df: DataFrame from validate_rules().

    Returns:
        bytes (CSV encoded).
    """
    return violations_df.to_csv(index=False).encode("utf-8")
