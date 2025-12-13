"""
Insights Generator
Identifies strengths and areas for improvement
"""

from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.services.storage import (
    UserStorageService,
    RepositoryStorageService,
    AnalysisStorageService
)

logger = logging.getLogger(__name__)


class InsightsGenerator:
    """
    Generates insights about user's code quality
    
    Identifies:
    - Strengths (test coverage, CI/CD, documentation, code quality)
    - Areas for improvement (missing tests, high complexity, etc.)
    - Priority levels (high, medium, low)
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize insights generator
        
        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.user_storage = UserStorageService(database)
        self.repo_storage = RepositoryStorageService(database)
        self.analysis_storage = AnalysisStorageService(database)
        self.logger = logger
    
    async def generate_insights(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate complete insights for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with strengths and improvements
        """
        self.logger.info(f"Generating insights for user: {user_id}")
        
        # Get repositories
        repos = await self.repo_storage.get_user_repositories(
            user_id,
            analyzed_only=True
        )
        
        if not repos:
            return {
                'strengths': [],
                'improvements': []
            }
        
        # Identify strengths
        strengths = await self._identify_strengths(repos)
        
        # Identify improvements
        improvements = await self._identify_improvements(repos)
        
        return {
            'strengths': strengths,
            'improvements': improvements
        }
    
    async def _identify_strengths(
        self,
        repos: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify user's strengths
        
        Args:
            repos: List of repository objects
            
        Returns:
            List of strength dictionaries
        """
        strengths = []
        
        # Check test coverage
        repos_with_tests = [
            r for r in repos
            if getattr(r, 'has_tests', False) or
            self._has_test_files(r)
        ]
        
        if len(repos_with_tests) / len(repos) >= 0.7:
            strengths.append({
                'title': 'Strong Test Coverage',
                'description': f'{len(repos_with_tests)} out of {len(repos)} repositories have tests',
                'icon': 'test',
                'significance': 'high'
            })
        
        # Check CI/CD
        repos_with_cicd = [
            r for r in repos
            if getattr(r, 'has_ci_cd', False)
        ]
        
        if len(repos_with_cicd) / len(repos) >= 0.6:
            strengths.append({
                'title': 'Active CI/CD Practices',
                'description': f'{len(repos_with_cicd)} repositories use CI/CD pipelines',
                'icon': 'cicd',
                'significance': 'high'
            })
        
        # Check documentation
        repos_with_readme = [
            r for r in repos
            if getattr(r, 'has_readme', False)
        ]
        
        if len(repos_with_readme) / len(repos) >= 0.8:
            strengths.append({
                'title': 'Well-Documented Projects',
                'description': f'{len(repos_with_readme)} repositories have README files',
                'icon': 'documentation',
                'significance': 'medium'
            })
        
        # Check code quality (ACID scores)
        high_quality_repos = []
        for repo in repos:
            if hasattr(repo, 'acid_scores') and repo.acid_scores:
                if isinstance(repo.acid_scores, dict):
                    overall = repo.acid_scores.get('overall', 0.0)
                    if overall >= 80:
                        high_quality_repos.append(repo)
        
        if len(high_quality_repos) / len(repos) >= 0.5:
            strengths.append({
                'title': 'High Code Quality Standards',
                'description': f'{len(high_quality_repos)} repositories have excellent ACID scores (≥80)',
                'icon': 'quality',
                'significance': 'high'
            })
        
        # Check maintainability
        maintainable_repos = []
        for repo in repos:
            if hasattr(repo, 'complexity_metrics') and repo.complexity_metrics:
                if isinstance(repo.complexity_metrics, dict):
                    mi = repo.complexity_metrics.get('maintainability', 0.0)
                    if mi >= 70:
                        maintainable_repos.append(repo)
        
        if len(maintainable_repos) / len(repos) >= 0.6:
            strengths.append({
                'title': 'Maintainable Codebase',
                'description': f'{len(maintainable_repos)} repositories have high maintainability',
                'icon': 'maintainability',
                'significance': 'medium'
            })
        
        # Check licensing
        repos_with_license = [
            r for r in repos
            if getattr(r, 'license', None) is not None
        ]
        
        if len(repos_with_license) / len(repos) >= 0.7:
            strengths.append({
                'title': 'Proper Licensing',
                'description': f'{len(repos_with_license)} repositories have licenses',
                'icon': 'license',
                'significance': 'low'
            })
        
        # Sort by significance
        significance_order = {'high': 0, 'medium': 1, 'low': 2}
        strengths.sort(key=lambda x: significance_order.get(x['significance'], 3))
        
        return strengths
    
    async def _identify_improvements(
        self,
        repos: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify areas for improvement
        
        Args:
            repos: List of repository objects
            
        Returns:
            List of improvement dictionaries
        """
        improvements = []
        
        # Check for missing tests
        repos_without_tests = [
            r for r in repos
            if not getattr(r, 'has_tests', False) and
            not self._has_test_files(r)
        ]
        
        if repos_without_tests:
            improvements.append({
                'title': 'Add Test Coverage',
                'description': f'{len(repos_without_tests)} repositories lack tests',
                'priority': 'high',
                'affected_repos': len(repos_without_tests),
                'icon': 'test'
            })
        
        # Check for missing CI/CD
        repos_without_cicd = [
            r for r in repos
            if not getattr(r, 'has_ci_cd', False)
        ]
        
        if repos_without_cicd:
            improvements.append({
                'title': 'Implement CI/CD Pipelines',
                'description': f'{len(repos_without_cicd)} repositories lack CI/CD',
                'priority': 'high',
                'affected_repos': len(repos_without_cicd),
                'icon': 'cicd'
            })
        
        # Check for high complexity
        complex_repos = []
        for repo in repos:
            if hasattr(repo, 'complexity_metrics') and repo.complexity_metrics:
                if isinstance(repo.complexity_metrics, dict):
                    cyclomatic = repo.complexity_metrics.get('cyclomatic', 0.0)
                    if cyclomatic > 15:
                        complex_repos.append(repo)
        
        if complex_repos:
            improvements.append({
                'title': 'Reduce Code Complexity',
                'description': f'{len(complex_repos)} repositories have high complexity',
                'priority': 'medium',
                'affected_repos': len(complex_repos),
                'icon': 'complexity'
            })
        
        # Check for missing documentation
        repos_without_readme = [
            r for r in repos
            if not getattr(r, 'has_readme', False)
        ]
        
        if repos_without_readme:
            improvements.append({
                'title': 'Improve Documentation',
                'description': f'{len(repos_without_readme)} repositories lack README files',
                'priority': 'medium',
                'affected_repos': len(repos_without_readme),
                'icon': 'documentation'
            })
        
        # Check for low ACID scores
        low_quality_repos = []
        for repo in repos:
            if hasattr(repo, 'acid_scores') and repo.acid_scores:
                if isinstance(repo.acid_scores, dict):
                    overall = repo.acid_scores.get('overall', 0.0)
                    if overall < 60:
                        low_quality_repos.append(repo)
        
        if low_quality_repos:
            improvements.append({
                'title': 'Improve Code Quality',
                'description': f'{len(low_quality_repos)} repositories have low ACID scores (<60)',
                'priority': 'high',
                'affected_repos': len(low_quality_repos),
                'icon': 'quality'
            })
        
        # Check for missing licenses
        repos_without_license = [
            r for r in repos
            if getattr(r, 'license', None) is None
        ]
        
        if repos_without_license:
            improvements.append({
                'title': 'Add Licenses',
                'description': f'{len(repos_without_license)} repositories lack licenses',
                'priority': 'low',
                'affected_repos': len(repos_without_license),
                'icon': 'license'
            })
        
        # Check for low maintainability
        unmaintainable_repos = []
        for repo in repos:
            if hasattr(repo, 'complexity_metrics') and repo.complexity_metrics:
                if isinstance(repo.complexity_metrics, dict):
                    mi = repo.complexity_metrics.get('maintainability', 0.0)
                    if mi < 50:
                        unmaintainable_repos.append(repo)
        
        if unmaintainable_repos:
            improvements.append({
                'title': 'Improve Maintainability',
                'description': f'{len(unmaintainable_repos)} repositories have low maintainability',
                'priority': 'medium',
                'affected_repos': len(unmaintainable_repos),
                'icon': 'maintainability'
            })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        improvements.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return improvements
    
    def _has_test_files(self, repo: Any) -> bool:
        """
        Check if repository has test files
        
        Args:
            repo: Repository object
            
        Returns:
            True if has test files
        """
        # Check if repository name suggests tests
        name = repo.name.lower()
        if 'test' in name or 'spec' in name:
            return True
        
        # Check has_tests attribute
        return getattr(repo, 'has_tests', False)
