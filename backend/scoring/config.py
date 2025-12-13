"""
Configuration for the scoring system
Contains all thresholds, weights, and constants
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ScoringConfig:
    """Configuration for scoring thresholds and weights"""
    
    # Importance Score Weights
    IMPORTANCE_COMMUNITY_WEIGHT: float = 0.40
    IMPORTANCE_ACTIVITY_WEIGHT: float = 0.30
    IMPORTANCE_SIZE_WEIGHT: float = 0.20
    IMPORTANCE_QUALITY_WEIGHT: float = 0.10
    
    # Repository Categorization Thresholds
    FLAGSHIP_THRESHOLD: float = 70.0
    SIGNIFICANT_THRESHOLD: float = 50.0
    
    # Overall Score Weights
    FLAGSHIP_WEIGHT: float = 0.60
    SIGNIFICANT_WEIGHT: float = 0.40
    
    # ACID Score Weights
    ACID_ATOMICITY_WEIGHT: float = 0.25
    ACID_CONSISTENCY_WEIGHT: float = 0.25
    ACID_ISOLATION_WEIGHT: float = 0.25
    ACID_DURABILITY_WEIGHT: float = 0.25
    
    # Performance Targets
    STAGE1_TARGET_SECONDS: float = 1.0
    STAGE2_TARGET_SECONDS: float = 35.0
    STAGE2_BATCH_SIZE: int = 3
    
    # Code Analysis Limits
    MAX_FILES_PER_REPO: int = 50
    MAX_REPOS_TO_ANALYZE: int = 15
    
    # Progress Update Interval
    PROGRESS_UPDATE_INTERVAL_SECONDS: int = 2
    
    # GitHub API
    GITHUB_GRAPHQL_ENDPOINT: str = "https://api.github.com/graphql"
    GITHUB_REST_ENDPOINT: str = "https://api.github.com"
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_BACKOFF_BASE: float = 2.0
    
    # Code File Extensions
    CODE_EXTENSIONS: tuple = (
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.go', '.rb', '.php',
        '.cpp', '.c', '.cs', '.swift', '.kt'
    )


# Global configuration instance
config = ScoringConfig()


def get_config() -> ScoringConfig:
    """Get the global configuration instance"""
    return config


def update_config(updates: Dict[str, Any]) -> None:
    """Update configuration values"""
    global config
    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value)
