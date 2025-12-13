"""
Tests for utility functions
"""

import pytest
from backend.scoring.utils import (
    round_score,
    calculate_percentage,
    safe_divide,
    clamp,
    normalize_score,
    weighted_average,
    validate_repository_data,
    validate_user_data
)


def test_round_score():
    """Test score rounding"""
    assert round_score(85.678) == 85.7
    assert round_score(85.678, decimals=2) == 85.68
    assert round_score(85.0) == 85.0


def test_calculate_percentage():
    """Test percentage calculation"""
    assert calculate_percentage(15, 20) == 75.0
    assert calculate_percentage(10, 100) == 10.0
    assert calculate_percentage(0, 100) == 0.0
    assert calculate_percentage(100, 100) == 100.0


def test_calculate_percentage_zero_total():
    """Test percentage calculation with zero total"""
    assert calculate_percentage(10, 0) == 0.0


def test_safe_divide():
    """Test safe division"""
    assert safe_divide(10, 2) == 5.0
    assert safe_divide(10, 0) == 0.0
    assert safe_divide(10, 0, default=100.0) == 100.0


def test_clamp():
    """Test value clamping"""
    assert clamp(50) == 50
    assert clamp(150) == 100
    assert clamp(-10) == 0
    assert clamp(75, 0, 100) == 75


def test_clamp_custom_range():
    """Test clamping with custom range"""
    assert clamp(50, 10, 90) == 50
    assert clamp(5, 10, 90) == 10
    assert clamp(95, 10, 90) == 90


def test_normalize_score():
    """Test score normalization"""
    # Score in middle of range
    assert normalize_score(50, 0, 100) == 50.0
    
    # Score at boundaries
    assert normalize_score(0, 0, 100) == 0.0
    assert normalize_score(100, 0, 100) == 100.0
    
    # Score outside range gets clamped
    assert normalize_score(150, 0, 100) == 100.0
    assert normalize_score(-50, 0, 100) == 0.0


def test_normalize_score_custom_range():
    """Test normalization with custom range"""
    # 50 in range 0-200 should be 25 in 0-100
    assert normalize_score(50, 0, 200) == 25.0
    
    # 150 in range 100-200 should be 50 in 0-100
    assert normalize_score(150, 100, 200) == 50.0


def test_normalize_score_same_min_max():
    """Test normalization when min equals max"""
    assert normalize_score(50, 50, 50) == 50.0


def test_weighted_average():
    """Test weighted average calculation"""
    values = [80, 90, 70]
    weights = [0.5, 0.3, 0.2]
    
    result = weighted_average(values, weights)
    expected = (80 * 0.5) + (90 * 0.3) + (70 * 0.2)
    
    assert abs(result - expected) < 0.001


def test_weighted_average_equal_weights():
    """Test weighted average with equal weights"""
    values = [80, 90, 70]
    weights = [1/3, 1/3, 1/3]
    
    result = weighted_average(values, weights)
    expected = (80 + 90 + 70) / 3
    
    assert abs(result - expected) < 0.001


def test_weighted_average_invalid_length():
    """Test weighted average with mismatched lengths"""
    values = [80, 90]
    weights = [0.5, 0.3, 0.2]
    
    with pytest.raises(ValueError):
        weighted_average(values, weights)


def test_weighted_average_invalid_weights():
    """Test weighted average with weights not summing to 1"""
    values = [80, 90, 70]
    weights = [0.5, 0.3, 0.3]  # Sum = 1.1
    
    with pytest.raises(ValueError):
        weighted_average(values, weights)


def test_validate_repository_data_valid():
    """Test repository data validation with valid data"""
    repo = {
        'name': 'test-repo',
        'full_name': 'user/test-repo',
        'stars': 100,
        'forks': 25,
        'size': 5000,
        'created_at': '2024-01-01',
        'updated_at': '2024-11-20'
    }
    
    assert validate_repository_data(repo) is True


def test_validate_repository_data_missing_fields():
    """Test repository data validation with missing fields"""
    repo = {
        'name': 'test-repo',
        'stars': 100
    }
    
    assert validate_repository_data(repo) is False


def test_validate_repository_data_invalid_types():
    """Test repository data validation with invalid types"""
    repo = {
        'name': 'test-repo',
        'full_name': 'user/test-repo',
        'stars': 'not a number',  # Should be int/float
        'forks': 25,
        'size': 5000,
        'created_at': '2024-01-01',
        'updated_at': '2024-11-20'
    }
    
    assert validate_repository_data(repo) is False


def test_validate_repository_data_not_dict():
    """Test repository data validation with non-dict"""
    assert validate_repository_data("not a dict") is False
    assert validate_repository_data(None) is False
    assert validate_repository_data([]) is False


def test_validate_user_data_valid():
    """Test user data validation with valid data"""
    user = {
        'user_id': 'user123',
        'github_username': 'testuser'
    }
    
    assert validate_user_data(user) is True


def test_validate_user_data_missing_fields():
    """Test user data validation with missing fields"""
    user = {
        'user_id': 'user123'
    }
    
    assert validate_user_data(user) is False


def test_validate_user_data_invalid_types():
    """Test user data validation with invalid types"""
    user = {
        'user_id': 123,  # Should be string
        'github_username': 'testuser'
    }
    
    assert validate_user_data(user) is False


def test_validate_user_data_not_dict():
    """Test user data validation with non-dict"""
    assert validate_user_data("not a dict") is False
    assert validate_user_data(None) is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
