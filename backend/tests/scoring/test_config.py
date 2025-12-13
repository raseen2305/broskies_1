"""
Tests for scoring configuration
"""

import pytest
from backend.scoring.config import ScoringConfig, get_config, update_config


def test_config_defaults():
    """Test that configuration has correct default values"""
    config = ScoringConfig()
    
    # Test importance weights
    assert config.IMPORTANCE_COMMUNITY_WEIGHT == 0.40
    assert config.IMPORTANCE_ACTIVITY_WEIGHT == 0.30
    assert config.IMPORTANCE_SIZE_WEIGHT == 0.20
    assert config.IMPORTANCE_QUALITY_WEIGHT == 0.10
    
    # Test thresholds
    assert config.FLAGSHIP_THRESHOLD == 70.0
    assert config.SIGNIFICANT_THRESHOLD == 50.0
    
    # Test overall score weights
    assert config.FLAGSHIP_WEIGHT == 0.60
    assert config.SIGNIFICANT_WEIGHT == 0.40
    
    # Test performance targets
    assert config.STAGE1_TARGET_SECONDS == 1.0
    assert config.STAGE2_TARGET_SECONDS == 35.0
    assert config.STAGE2_BATCH_SIZE == 3
    
    # Test limits
    assert config.MAX_FILES_PER_REPO == 50
    assert config.MAX_REPOS_TO_ANALYZE == 15


def test_weights_sum_to_one():
    """Test that importance weights sum to 1.0"""
    config = ScoringConfig()
    
    total = (
        config.IMPORTANCE_COMMUNITY_WEIGHT +
        config.IMPORTANCE_ACTIVITY_WEIGHT +
        config.IMPORTANCE_SIZE_WEIGHT +
        config.IMPORTANCE_QUALITY_WEIGHT
    )
    
    assert abs(total - 1.0) < 0.001


def test_get_config():
    """Test getting global config instance"""
    config = get_config()
    assert isinstance(config, ScoringConfig)
    assert config.FLAGSHIP_THRESHOLD == 70.0


def test_update_config():
    """Test updating configuration values"""
    original_threshold = get_config().FLAGSHIP_THRESHOLD
    
    # Update config
    update_config({'FLAGSHIP_THRESHOLD': 75.0})
    
    # Verify update
    assert get_config().FLAGSHIP_THRESHOLD == 75.0
    
    # Restore original
    update_config({'FLAGSHIP_THRESHOLD': original_threshold})


def test_code_extensions():
    """Test that code extensions are defined"""
    config = ScoringConfig()
    
    assert '.py' in config.CODE_EXTENSIONS
    assert '.js' in config.CODE_EXTENSIONS
    assert '.ts' in config.CODE_EXTENSIONS
    assert '.java' in config.CODE_EXTENSIONS
    assert len(config.CODE_EXTENSIONS) > 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
