"""
Manual test for Scan Orchestrator
Run this to verify the implementation works
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scoring.orchestration.scan_orchestrator import ScanOrchestrator
from scoring.config import get_config


async def test_importance_calculation():
    """Test importance calculation"""
    print("\n=== Testing Importance Calculation ===")
    
    orchestrator = ScanOrchestrator()
    
    # Sample repositories
    repos = [
        {
            'name': 'flagship-repo',
            'stars': 200,
            'forks': 50,
            'watchers': 100,
            'size': 15000,
            'updated_at': datetime.utcnow(),
            'has_readme': True,
            'has_license_file': True,
            'description': 'A great project',
            'topics': ['python', 'api', 'web']
        },
        {
            'name': 'significant-repo',
            'stars': 50,
            'forks': 10,
            'watchers': 30,
            'size': 5000,
            'updated_at': datetime.utcnow(),
            'has_readme': True,
            'has_license_file': False,
            'description': 'Good project',
            'topics': ['javascript']
        },
        {
            'name': 'supporting-repo',
            'stars': 5,
            'forks': 1,
            'watchers': 3,
            'size': 500,
            'updated_at': datetime.utcnow(),
            'has_readme': False,
            'has_license_file': False,
            'description': '',
            'topics': []
        }
    ]
    
    # Calculate importance scores
    repos_with_scores = await orchestrator._calculate_importance_parallel(repos)
    
    print(f"\nProcessed {len(repos_with_scores)} repositories:")
    for repo in repos_with_scores:
        print(f"  - {repo['name']}: {repo['importance_score']:.1f}")
    
    # Verify scores are in expected order
    assert repos_with_scores[0]['importance_score'] > repos_with_scores[1]['importance_score']
    assert repos_with_scores[1]['importance_score'] > repos_with_scores[2]['importance_score']
    
    print("[OK] Importance calculation working correctly")
    return repos_with_scores


def test_categorization(repos_with_scores):
    """Test repository categorization"""
    print("\n=== Testing Categorization ===")
    
    orchestrator = ScanOrchestrator()
    
    # Categorize repositories
    categorized = orchestrator._categorize_repositories(repos_with_scores)
    
    print(f"\nCategorized {len(categorized)} repositories:")
    for repo in categorized:
        print(f"  - {repo['name']}: {repo['category']} (score: {repo['importance_score']:.1f})")
    
    # Verify categories
    config = get_config()
    for repo in categorized:
        score = repo['importance_score']
        category = repo['category']
        
        if score >= config.FLAGSHIP_THRESHOLD:
            assert category == 'flagship', f"Expected flagship for score {score}"
        elif score >= config.SIGNIFICANT_THRESHOLD:
            assert category == 'significant', f"Expected significant for score {score}"
        else:
            assert category == 'supporting', f"Expected supporting for score {score}"
    
    print("[OK] Categorization working correctly")
    return categorized


def test_summary(categorized_repos):
    """Test summary generation"""
    print("\n=== Testing Summary Generation ===")
    
    orchestrator = ScanOrchestrator()
    
    # Generate summary
    summary = orchestrator._generate_summary(categorized_repos)
    
    print(f"\nSummary:")
    print(f"  Total: {summary['total']}")
    print(f"  Flagship: {summary['flagship']}")
    print(f"  Significant: {summary['significant']}")
    print(f"  Supporting: {summary['supporting']}")
    
    # Verify summary
    assert summary['total'] == len(categorized_repos)
    assert summary['total'] == summary['flagship'] + summary['significant'] + summary['supporting']
    
    print("[OK] Summary generation working correctly")


def test_repository_selection():
    """Test repository selection for analysis"""
    print("\n=== Testing Repository Selection ===")
    
    orchestrator = ScanOrchestrator()
    
    # Create 20 repositories
    repos = []
    for i in range(10):
        repos.append({
            'name': f'flagship{i}',
            'category': 'flagship',
            'importance_score': 90 - i
        })
    for i in range(10):
        repos.append({
            'name': f'significant{i}',
            'category': 'significant',
            'importance_score': 60 - i
        })
    for i in range(5):
        repos.append({
            'name': f'supporting{i}',
            'category': 'supporting',
            'importance_score': 30 - i
        })
    
    # Select repositories for analysis
    selected = orchestrator.select_repositories_for_analysis(repos)
    
    print(f"\nSelected {len(selected)} repositories for analysis:")
    for repo in selected[:5]:  # Show first 5
        print(f"  - {repo['name']}: {repo['category']} (score: {repo['importance_score']:.1f})")
    if len(selected) > 5:
        print(f"  ... and {len(selected) - 5} more")
    
    # Verify selection
    config = get_config()
    assert len(selected) <= config.MAX_REPOS_TO_ANALYZE
    
    # Verify no supporting repos
    categories = [r['category'] for r in selected]
    assert 'supporting' not in categories
    
    # Verify sorted by score
    scores = [r['importance_score'] for r in selected]
    assert scores == sorted(scores, reverse=True)
    
    print("[OK] Repository selection working correctly")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Scan Orchestrator Manual Tests")
    print("=" * 60)
    
    try:
        # Test 1: Importance calculation
        repos_with_scores = await test_importance_calculation()
        
        # Test 2: Categorization
        categorized_repos = test_categorization(repos_with_scores)
        
        # Test 3: Summary generation
        test_summary(categorized_repos)
        
        # Test 4: Repository selection
        test_repository_selection()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[FAILED] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
