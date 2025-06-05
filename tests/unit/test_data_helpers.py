"""Unit tests for data helper functions."""

from utils.data_helpers.cleaning import remove_nulls


def test_remove_nulls_removes_none():
    """Test that remove_nulls removes None values from a list."""
    data = [1, None, 2, None, 3]
    result = remove_nulls(data)
    assert result == [1, 2, 3]
