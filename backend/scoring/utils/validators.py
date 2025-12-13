"""
Validation utilities for the scoring system
"""

from typing import Dict, Any, List


def validate_repository_data(repo: Dict[str, Any]) -> bool:
    """
    Validate repository data structure
    
    Args:
        repo: Repository data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        'name', 'full_name', 'stars', 'forks',
        'size', 'created_at', 'updated_at'
    ]
    
    if not isinstance(repo, dict):
        return False
    
    for field in required_fields:
        if field not in repo:
            return False
    
    # Validate numeric fields
    if not isinstance(repo.get('stars'), (int, float)):
        return False
    if not isinstance(repo.get('forks'), (int, float)):
        return False
    if not isinstance(repo.get('size'), (int, float)):
        return False
    
    return True


def validate_user_data(user: Dict[str, Any]) -> bool:
    """
    Validate user data structure
    
    Args:
        user: User data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['user_id', 'github_username']
    
    if not isinstance(user, dict):
        return False
    
    for field in required_fields:
        if field not in user:
            return False
        if not isinstance(user[field], str):
            return False
    
    return True


def validate_code_file(file: Dict[str, Any]) -> bool:
    """
    Validate code file structure
    
    Args:
        file: Code file dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['path', 'content']
    
    if not isinstance(file, dict):
        return False
    
    for field in required_fields:
        if field not in file:
            return False
    
    return True


def validate_acid_scores(scores: Dict[str, float]) -> bool:
    """
    Validate ACID scores structure
    
    Args:
        scores: ACID scores dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['atomicity', 'consistency', 'isolation', 'durability']
    
    if not isinstance(scores, dict):
        return False
    
    for field in required_fields:
        if field not in scores:
            return False
        score = scores[field]
        if not isinstance(score, (int, float)):
            return False
        if not 0 <= score <= 100:
            return False
    
    return True
