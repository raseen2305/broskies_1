"""
Manual test script to verify scoring system components
Run this to quickly test if everything is working
"""

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from scoring.config import get_config
from scoring.scoring import ImportanceScorer
from scoring.utils import (
    round_score,
    calculate_percentage,
    safe_divide,
    validate_repository_data
)


def test_config():
    """Test configuration"""
    print("\n" + "="*70)
    print("Testing Configuration")
    print("="*70)
    
    config = get_config()
    print(f"✓ Config loaded successfully")
    print(f"  - Flagship threshold: {config.FLAGSHIP_THRESHOLD}")
    print(f"  - Significant threshold: {config.SIGNIFICANT_THRESHOLD}")
    print(f"  - Stage 1 target: {config.STAGE1_TARGET_SECONDS}s")
    print(f"  - Stage 2 target: {config.STAGE2_TARGET_SECONDS}s")
    print(f"  - Max files per repo: {config.MAX_FILES_PER_REPO}")
    
    return True


def test_utils():
    """Test utility functions"""
    print("\n" + "="*70)
    print("Testing Utility Functions")
    print("="*70)
    
    # Test rounding
    score = round_score(85.678)
    print(f"✓ round_score(85.678) = {score}")
    assert score == 85.7
    
    # Test percentage
    pct = calculate_percentage(15, 20)
    print(f"✓ calculate_percentage(15, 20) = {pct}%")
    assert pct == 75.0
    
    # Test safe divide
    result = safe_divide(10, 0, default=0.0)
    print(f"✓ safe_divide(10, 0) = {result}")
    assert result == 0.0
    
    # Test validation
    repo = {
        'name': 'test',
        'full_name': 'user/test',
        'stars': 100,
        'forks': 25,
        'size': 5000,
        'created_at': '2024-01-01',
        'updated_at': '2024-11-20'
    }
    valid = validate_repository_data(repo)
    print(f"✓ validate_repository_data() = {valid}")
    assert valid is True
    
    return True


def test_importance_scorer():
    """Test importance scorer"""
    print("\n" + "="*70)
    print("Testing Importance Scorer")
    print("="*70)
    
    scorer = ImportanceScorer()
    print(f"✓ ImportanceScorer created")
    
    # Test with sample repository
    sample_repo = {
        'name': 'awesome-project',
        'stars': 150,
        'forks': 45,
        'watchers': 120,
        'size': 8500,
        'updated_at': datetime.utcnow().isoformat(),
        'has_readme': True,
        'license': 'MIT',
        'description': 'A production-ready REST API',
        'topics': ['python', 'api', 'rest']
    }
    
    # Calculate score
    score = scorer.calculate_score(sample_repo)
    print(f"✓ Importance score calculated: {score}")
    assert 0 <= score <= 100
    
    # Get breakdown
    breakdown = scorer.get_score_breakdown(sample_repo)
    print(f"  Score breakdown:")
    print(f"    - Community: {breakdown['community']:.1f}")
    print(f"    - Activity: {breakdown['activity']:.1f}")
    print(f"    - Size: {breakdown['size']:.1f}")
    print(f"    - Quality: {breakdown['quality']:.1f}")
    
    # Categorize
    category = scorer.categorize(score)
    print(f"✓ Category: {category}")
    print(f"  {scorer.get_category_description(category)}")
    
    return True


def test_different_repos():
    """Test scorer with different repository types"""
    print("\n" + "="*70)
    print("Testing Different Repository Types")
    print("="*70)
    
    scorer = ImportanceScorer()
    
    # High-engagement repo
    high_repo = {
        'name': 'popular-project',
        'stars': 1000,
        'forks': 500,
        'watchers': 800,
        'size': 15000,
        'updated_at': datetime.utcnow().isoformat(),
        'has_readme': True,
        'license': 'MIT',
        'description': 'Very popular open source project',
        'topics': ['python', 'popular', 'awesome', 'production']
    }
    
    high_score = scorer.calculate_score(high_repo)
    high_category = scorer.categorize(high_score)
    print(f"✓ High-engagement repo: {high_score:.1f} ({high_category})")
    
    # Medium-engagement repo
    medium_repo = {
        'name': 'decent-project',
        'stars': 50,
        'forks': 10,
        'watchers': 30,
        'size': 2000,
        'updated_at': datetime.utcnow().isoformat(),
        'has_readme': True,
        'license': 'MIT',
        'description': 'A decent project',
        'topics': ['python']
    }
    
    medium_score = scorer.calculate_score(medium_repo)
    medium_category = scorer.categorize(medium_score)
    print(f"✓ Medium-engagement repo: {medium_score:.1f} ({medium_category})")
    
    # Low-engagement repo
    low_repo = {
        'name': 'small-project',
        'stars': 0,
        'forks': 0,
        'watchers': 0,
        'size': 100,
        'updated_at': '2023-01-01T00:00:00Z',
        'has_readme': False,
        'license': None,
        'description': '',
        'topics': []
    }
    
    low_score = scorer.calculate_score(low_repo)
    low_category = scorer.categorize(low_score)
    print(f"✓ Low-engagement repo: {low_score:.1f} ({low_category})")
    
    # Verify score ordering
    assert high_score > medium_score > low_score
    print(f"\n✓ Score ordering correct: {high_score:.1f} > {medium_score:.1f} > {low_score:.1f}")
    
    return True


def main():
    """Run all manual tests"""
    print("\n" + "="*70)
    print("SCORING SYSTEM MANUAL TEST")
    print("="*70)
    
    tests = [
        ("Configuration", test_config),
        ("Utility Functions", test_utils),
        ("Importance Scorer", test_importance_scorer),
        ("Different Repository Types", test_different_repos),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {name} FAILED: {e}")
            failed += 1
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✅ All manual tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
