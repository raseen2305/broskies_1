"""
Tests for ImportanceScorer
"""

import pytest
from datetime import datetime, timedelta
from backend.scoring.scoring import ImportanceScorer


@pytest.fixture
def scorer():
    """Create an ImportanceScorer instance"""
    return ImportanceScorer()


@pytest.fixture
def sample_repo():
    """Create a sample repository data"""
    return {
        'name': 'test-repo',
        'stars': 100,
        'forks': 25,
        'watchers': 80,
        'size': 5000,  # KB
        'updated_at': datetime.utcnow().isoformat(),
        'has_readme': True,
        'license': 'MIT',
        'description': 'A test repository',
        'topics': ['python', 'testing']
    }


def test_calculate_score_valid_input(scorer, sample_repo):
    """Test calculating importance score with valid input"""
    score = scorer.calculate_score(sample_repo)
    
    assert isinstance(score, float)
    assert 0 <= score <= 100
    assert score > 0  # Should have some score


def test_calculate_score_high_engagement(scorer):
    """Test that high engagement repos get high scores"""
    high_engagement_repo = {
        'name': 'popular-repo',
        'stars': 1000,
        'forks': 500,
        'watchers': 800,
        'size': 10000,
        'updated_at': datetime.utcnow().isoformat(),
        'has_readme': True,
        'license': 'MIT',
        'description': 'Very popular repository',
        'topics': ['python', 'popular', 'awesome']
    }
    
    score = scorer.calculate_score(high_engagement_repo)
    assert score >= 80  # Should be high


def test_calculate_score_low_engagement(scorer):
    """Test that low engagement repos get lower scores"""
    low_engagement_repo = {
        'name': 'small-repo',
        'stars': 0,
        'forks': 0,
        'watchers': 0,
        'size': 50,
        'updated_at': (datetime.utcnow() - timedelta(days=400)).isoformat(),
        'has_readme': False,
        'license': None,
        'description': '',
        'topics': []
    }
    
    score = scorer.calculate_score(low_engagement_repo)
    assert score < 50  # Should be low


def test_validate_input_valid(scorer, sample_repo):
    """Test input validation with valid data"""
    assert scorer.validate_input(sample_repo) is True


def test_validate_input_missing_fields(scorer):
    """Test input validation with missing fields"""
    invalid_repo = {
        'name': 'test-repo',
        'stars': 100
        # Missing required fields
    }
    
    assert scorer.validate_input(invalid_repo) is False


def test_validate_input_not_dict(scorer):
    """Test input validation with non-dict input"""
    assert scorer.validate_input("not a dict") is False
    assert scorer.validate_input(None) is False
    assert scorer.validate_input([]) is False


def test_get_score_breakdown(scorer, sample_repo):
    """Test getting detailed score breakdown"""
    breakdown = scorer.get_score_breakdown(sample_repo)
    
    assert isinstance(breakdown, dict)
    assert 'community' in breakdown
    assert 'activity' in breakdown
    assert 'size' in breakdown
    assert 'quality' in breakdown
    
    # All scores should be 0-100
    for score in breakdown.values():
        assert 0 <= score <= 100


def test_community_score_calculation(scorer):
    """Test community score calculation"""
    repo = {
        'stars': 100,
        'forks': 50,
        'watchers': 75,
        'size': 1000,
        'updated_at': datetime.utcnow().isoformat()
    }
    
    score = scorer._calculate_community_score(repo)
    assert isinstance(score, float)
    assert 0 <= score <= 100


def test_activity_score_recent(scorer):
    """Test activity score for recently updated repo"""
    repo = {
        'updated_at': datetime.utcnow().isoformat()
    }
    
    score = scorer._calculate_activity_score(repo)
    assert score == 100.0  # Recent update = max score


def test_activity_score_old(scorer):
    """Test activity score for old repo"""
    repo = {
        'updated_at': (datetime.utcnow() - timedelta(days=400)).isoformat()
    }
    
    score = scorer._calculate_activity_score(repo)
    assert score < 60  # Old repo = lower score


def test_size_score_large(scorer):
    """Test size score for large repo"""
    repo = {'size': 15000}  # 15 MB
    score = scorer._calculate_size_score(repo)
    assert score == 100.0


def test_size_score_small(scorer):
    """Test size score for small repo"""
    repo = {'size': 50}  # 50 KB
    score = scorer._calculate_size_score(repo)
    assert score == 50.0


def test_quality_score_full(scorer):
    """Test quality score with all indicators"""
    repo = {
        'has_readme': True,
        'license': 'MIT',
        'description': 'A well-documented repository',
        'topics': ['python', 'testing', 'quality']
    }
    
    score = scorer._calculate_quality_score(repo)
    assert score == 100.0


def test_quality_score_none(scorer):
    """Test quality score with no indicators"""
    repo = {
        'has_readme': False,
        'license': None,
        'description': '',
        'topics': []
    }
    
    score = scorer._calculate_quality_score(repo)
    assert score == 0.0


def test_categorize_flagship(scorer):
    """Test categorization as flagship"""
    category = scorer.categorize(75.0)
    assert category == 'flagship'


def test_categorize_significant(scorer):
    """Test categorization as significant"""
    category = scorer.categorize(60.0)
    assert category == 'significant'


def test_categorize_supporting(scorer):
    """Test categorization as supporting"""
    category = scorer.categorize(40.0)
    assert category == 'supporting'


def test_categorize_boundary_flagship(scorer):
    """Test categorization at flagship boundary"""
    category = scorer.categorize(70.0)
    assert category == 'flagship'


def test_categorize_boundary_significant(scorer):
    """Test categorization at significant boundary"""
    category = scorer.categorize(50.0)
    assert category == 'significant'


def test_get_category_description(scorer):
    """Test getting category descriptions"""
    desc = scorer.get_category_description('flagship')
    assert isinstance(desc, str)
    assert len(desc) > 0
    
    desc = scorer.get_category_description('significant')
    assert isinstance(desc, str)
    
    desc = scorer.get_category_description('supporting')
    assert isinstance(desc, str)


def test_score_consistency(scorer, sample_repo):
    """Test that same input produces same score"""
    score1 = scorer.calculate_score(sample_repo)
    score2 = scorer.calculate_score(sample_repo)
    
    assert score1 == score2


def test_score_range(scorer, sample_repo):
    """Test that scores are always in valid range"""
    # Test with extreme values
    extreme_repo = {
        'name': 'extreme',
        'stars': 999999,
        'forks': 999999,
        'watchers': 999999,
        'size': 999999,
        'updated_at': datetime.utcnow().isoformat(),
        'has_readme': True,
        'license': 'MIT',
        'description': 'Extreme values',
        'topics': ['a'] * 100
    }
    
    score = scorer.calculate_score(extreme_repo)
    assert 0 <= score <= 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
