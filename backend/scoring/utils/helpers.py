"""
Helper utilities for the scoring system
"""

from typing import Optional, Union


def round_score(score: float, decimals: int = 1) -> float:
    """
    Round a score to specified decimal places
    
    Args:
        score: Score value
        decimals: Number of decimal places
        
    Returns:
        Rounded score
    """
    return round(score, decimals)


def calculate_percentage(part: Union[int, float], total: Union[int, float]) -> float:
    """
    Calculate percentage safely
    
    Args:
        part: Part value
        total: Total value
        
    Returns:
        Percentage (0-100)
    """
    if total == 0:
        return 0.0
    return (part / total) * 100


def safe_divide(numerator: Union[int, float], denominator: Union[int, float], default: float = 0.0) -> float:
    """
    Safely divide two numbers
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        Result of division or default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    """
    Clamp a value between min and max
    
    Args:
        value: Value to clamp
        min_value: Minimum value
        max_value: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_value, min(value, max_value))


def normalize_score(score: float, min_score: float, max_score: float) -> float:
    """
    Normalize a score to 0-100 range
    
    Args:
        score: Score to normalize
        min_score: Minimum possible score
        max_score: Maximum possible score
        
    Returns:
        Normalized score (0-100)
    """
    if max_score == min_score:
        return 50.0
    
    normalized = ((score - min_score) / (max_score - min_score)) * 100
    return clamp(normalized, 0.0, 100.0)


def weighted_average(values: list, weights: list) -> float:
    """
    Calculate weighted average
    
    Args:
        values: List of values
        weights: List of weights (must sum to 1.0)
        
    Returns:
        Weighted average
        
    Raises:
        ValueError: If lengths don't match or weights don't sum to 1.0
    """
    if len(values) != len(weights):
        raise ValueError("Values and weights must have same length")
    
    if abs(sum(weights) - 1.0) > 0.001:
        raise ValueError("Weights must sum to 1.0")
    
    return sum(v * w for v, w in zip(values, weights))
