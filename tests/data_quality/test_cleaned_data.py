"""Tests for cleaned student data quality."""
import pandas as pd


def test_no_nulls_in_critical_columns():
    """Test that there are no nulls in critical columns of cleaned data."""
    # Load a sample of cleaned data
    df = pd.read_csv("processed_data/cleaned/sample_cleaned.csv")
    critical_columns = ["student_id", "enrollment_status"]
    for col in critical_columns:
        assert df[col].isnull().sum() == 0, f"Nulls found in {col}"
