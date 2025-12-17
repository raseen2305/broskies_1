"""
Tests for Scan Orchestrator
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scoring.orchestration.scan_orchestrator import ScanOrchestrator
from scoring.config import get_config


class TestScanOrchestrator:
    """Test suite for ScanOrchestrator"""
    
    @pytest.fixture
    def mock_database(self):
        """Create a mock database"""
        db = Mock()
        db.user_profiles = Mock()
        db.repositories = Mock()
        return db
    
    @pytest.fixture
    def orchestrator(self, mock_database):
        """Create orchestrator instance"""
        return ScanOrchestrator(database=mock_database)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data"""
        return {
            'github_id': 'user123',
            'username': 'testuser',
            'name': 'Test User',
            'bio': 'Test bio',
            'avatar_url': 'https://example.com/avatar.jpg',
            'email': 'test@example.com',
            'location': 'Test City',
            'company': 'Test Company',
            'website': 'https://example.com',
            'twitter': 'testuser',
            'followers': 100,
            'following': 50,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    @pytest.fixture
    def sample_repositories(self):
        """Sample repository data"""
        return [
            {
                'github_id': 'repo1',
                'name': 'flagship-repo',
                'full_name': 'testuser/flagship-repo',
                'description': 'A flagship repository',
                'stars': 200,
                'forks': 50,
                'watchers': 100,
                'size': 15000,
                'language': 'Python',
                'topics': ['python', 'api'],
                'updated_at': datetime.utcnow(),
                'has_readme': True,
                'has_license_file': True,
                'has_tests': True,
                'has_ci_cd': True
            },
            {
                'github_id': 'repo2',
                'name': 'significant-repo',
                'full_name': 'testuser/significant-repo',
                'description': 'A significant repository',
                'stars': 50,
                'forks': 10,
                'watchers': 30,
                'size': 5000,
                'language': 'JavaScript',
                'topics': ['javascript'],
                'updated_at': datetime.utcnow(),
                'has_readme': True,
                'has_license_file': False,
                'has_tests': False,
                'has_ci_cd': False
            },
            {
                'github_id': 'repo3',
                'name': 'supporting-repo',
                'full_name': 'testuser/supporting-repo',
                'description': 'A supporting repository',
                'stars': 5,
                'forks': 1,
                'watchers': 3,
                'size': 500,
                'language': 'Python',
                'topics': [],
                'updated_at': datetime.utcnow(),
                'has_readme': False,
                'has_license_file': False,
                'has_tests': False,
                'has_ci_cd': False
            }
        ]
    
    @pytest.mark.asyncio
    async def test_calculate_importance_parallel(
        self,
        orchestrator,
        sample_repositories
    ):
        """Test parallel importance calculation"""
        repos_with_scores = await orchestrator._calculate_importance_parallel(
            sample_repositories
        )
        
        # Check that all repositories have importance scores
        assert len(repos_with_scores) == 3
        for repo in repos_with_scores:
            assert 'importance_score' in repo
            assert 0 <= repo['importance_score'] <= 100
        
        # Check that flagship repo has highest score
        scores = [r['importance_score'] for r in repos_with_scores]
        assert scores[0] > scores[1] > scores[2]
    
    def test_categorize_repositories(self, orchestrator, sample_repositories):
        """Test repository categorization"""
        # Add importance scores
        repos_with_scores = [
            {**sample_repositories[0], 'importance_score': 85.0},
            {**sample_repositories[1], 'importance_score': 60.0},
            {**sample_repositories[2], 'importance_score': 30.0}
        ]
        
        categorized = orchestrator._categorize_repositories(repos_with_scores)
        
        assert len(categorized) == 3
        assert categorized[0]['category'] == 'flagship'
        assert categorized[1]['category'] == 'significant'
        assert categorized[2]['category'] == 'supporting'
    
    def test_generate_summary(self, orchestrator):
        """Test summary generation"""
        repos = [
            {'category': 'flagship'},
            {'category': 'flagship'},
            {'category': 'significant'},
            {'category': 'significant'},
            {'category': 'significant'},
            {'category': 'supporting'},
            {'category': 'supporting'},
            {'category': 'supporting'},
            {'category': 'supporting'}
        ]
        
        summary = orchestrator._generate_summary(repos)
        
        assert summary['total'] == 9
        assert summary['flagship'] == 2
        assert summary['significant'] == 3
        assert summary['supporting'] == 4
    
    def test_get_repositories_by_category(self, orchestrator):
        """Test filtering repositories by category"""
        repos = [
            {'name': 'repo1', 'category': 'flagship'},
            {'name': 'repo2', 'category': 'significant'},
            {'name': 'repo3', 'category': 'flagship'},
            {'name': 'repo4', 'category': 'supporting'}
        ]
        
        flagship = orchestrator.get_repositories_by_category(repos, 'flagship')
        assert len(flagship) == 2
        assert all(r['category'] == 'flagship' for r in flagship)
        
        significant = orchestrator.get_repositories_by_category(repos, 'significant')
        assert len(significant) == 1
        
        supporting = orchestrator.get_repositories_by_category(repos, 'supporting')
        assert len(supporting) == 1
    
    def test_select_repositories_for_analysis(self, orchestrator):
        """Test repository selection for analysis"""
        # Create 20 repositories (10 flagship, 10 significant)
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
        
        selected = orchestrator.select_repositories_for_analysis(repos)
        
        # Should limit to 15 repositories
        config = get_config()
        assert len(selected) <= config.MAX_REPOS_TO_ANALYZE
        
        # Should be sorted by importance score
        scores = [r['importance_score'] for r in selected]
        assert scores == sorted(scores, reverse=True)
        
        # Should only include flagship and significant
        categories = [r['category'] for r in selected]
        assert all(c in ['flagship', 'significant'] for c in categories)
    
    @pytest.mark.asyncio
    async def test_execute_quick_scan_without_storage(self, orchestrator):
        """Test quick scan without database storage"""
        # Mock the GraphQL service
        with patch.object(
            orchestrator.graphql_service,
            'get_user_and_repositories',
            new_callable=AsyncMock
        ) as mock_graphql:
            # Setup mock return value
            mock_user = {
                'username': 'testuser',
                'name': 'Test User',
                'followers': 100
            }
            mock_repos = [
                {
                    'name': 'repo1',
                    'stars': 100,
                    'forks': 20,
                    'size': 10000,
                    'updated_at': datetime.utcnow(),
                    'has_readme': True,
                    'has_license_file': True
                }
            ]
            mock_graphql.return_value = (mock_user, mock_repos)
            
            # Execute scan without storage
            result = await orchestrator.execute_quick_scan(
                username='testuser',
                token='fake_token',
                store_results=False
            )
            
            # Verify results
            assert 'user' in result
            assert 'repositories' in result
            assert 'summary' in result
            assert 'scan_time' in result
            assert result['user']['username'] == 'testuser'
            assert len(result['repositories']) == 1
            assert 'importance_score' in result['repositories'][0]
            assert 'category' in result['repositories'][0]


def run_tests():
    """Run all tests"""
    pytest.main([__file__, '-v'])


if __name__ == '__main__':
    run_tests()
