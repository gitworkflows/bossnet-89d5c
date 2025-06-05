#!/usr/bin/env python3
"""
Unit tests for the data processing module.
"""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.data_processing.data_processor import DataProcessor

@pytest.fixture
def sample_student_data():
    """Create sample student data for testing."""
    return pd.DataFrame({
        'student_id': ['S001', 'S002', 'S003'],
        'name': ['Student 1', 'Student 2', 'Student 3'],
        'date_of_birth': ['2000-01-01', '2000-02-01', '2000-03-01'],
        'division': ['dhaka', 'Chittagong', 'khulna'],
        'district': ['dhaka', 'Chittagong', 'khulna'],
        'gpa': [3.5, 4.0, 3.0],
        'days_present': [85, 90, 75],
        'total_school_days': [100, 100, 100]
    })

@pytest.fixture
def data_processor():
    """Create a DataProcessor instance for testing."""
    return DataProcessor()

def test_clean_student_data(data_processor, sample_student_data):
    """Test the data cleaning functionality."""
    cleaned_data = data_processor.clean_student_data(sample_student_data)
    
    # Check if date_of_birth is converted to datetime
    assert pd.api.types.is_datetime64_any_dtype(cleaned_data['date_of_birth'])
    
    # Check if division names are properly capitalized
    assert all(cleaned_data['division'].isin(['Dhaka', 'Chittagong', 'Khulna']))
    
    # Check if district names are properly capitalized
    assert all(cleaned_data['district'].isin(['Dhaka', 'Chittagong', 'Khulna']))
    
    # Check if no duplicate student_ids exist
    assert cleaned_data['student_id'].nunique() == len(cleaned_data)

def test_calculate_performance_metrics(data_processor, sample_student_data):
    """Test the performance metrics calculation."""
    metrics_data = data_processor.calculate_performance_metrics(sample_student_data)
    
    # Check if attendance rate is calculated correctly
    expected_attendance = pd.Series([0.85, 0.90, 0.75], name='attendance_rate')
    pd.testing.assert_series_equal(
        metrics_data['attendance_rate'],
        expected_attendance,
        check_names=False
    )
    
    # Check if performance levels are assigned correctly
    assert metrics_data.loc[metrics_data['gpa'] == 4.0, 'performance_level'].iloc[0] == 'Excellent'
    assert metrics_data.loc[metrics_data['gpa'] == 3.5, 'performance_level'].iloc[0] == 'Very Good'
    assert metrics_data.loc[metrics_data['gpa'] == 3.0, 'performance_level'].iloc[0] == 'Good'

def test_get_performance_level(data_processor):
    """Test the performance level assignment."""
    assert data_processor._get_performance_level(4.0) == 'Excellent'
    assert data_processor._get_performance_level(3.5) == 'Very Good'
    assert data_processor._get_performance_level(3.0) == 'Good'
    assert data_processor._get_performance_level(2.5) == 'Average'
    assert data_processor._get_performance_level(1.5) == 'Needs Improvement'

def test_clean_student_data_with_missing_values(data_processor):
    """Test handling of missing values in student data."""
    data_with_missing = pd.DataFrame({
        'student_id': ['S001', None, 'S003'],
        'name': ['Student 1', 'Student 2', 'Student 3'],
        'date_of_birth': ['2000-01-01', '2000-02-01', '2000-03-01']
    })
    
    cleaned_data = data_processor.clean_student_data(data_with_missing)
    assert len(cleaned_data) == 2  # One row should be removed due to missing student_id
    assert all(cleaned_data['student_id'].notna())  # No null values in student_id

def test_calculate_performance_metrics_edge_cases(data_processor):
    """Test performance metrics calculation with edge cases."""
    edge_case_data = pd.DataFrame({
        'student_id': ['S001', 'S002'],
        'days_present': [100, 0],
        'total_school_days': [100, 100],
        'gpa': [4.0, 1.0]
    })
    
    metrics_data = data_processor.calculate_performance_metrics(edge_case_data)
    
    # Check perfect attendance
    assert metrics_data.loc[0, 'attendance_rate'] == 1.0
    
    # Check zero attendance
    assert metrics_data.loc[1, 'attendance_rate'] == 0.0
    
    # Check performance levels for extreme GPAs
    assert metrics_data.loc[0, 'performance_level'] == 'Excellent'
    assert metrics_data.loc[1, 'performance_level'] == 'Needs Improvement'

if __name__ == '__main__':
    pytest.main([__file__])
