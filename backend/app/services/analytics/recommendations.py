"""
Recommendations Engine
Generates actionable recommendations for improving scores
"""

from typing import Dict, List, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.services.storage import (
    UserStorageService,
    RepositoryStorageService,
    AnalysisStorageService
)

logger = logging.getLogger(__name__)


class RecommendationsEngine:
    """
    Generates actionable recommendations
    
    Features:
    - Specific actions per repository
    - Estimated score impact
    - Difficulty levels (easy, medium, hard)
    - Prioritized by impact
    - Limited to top 10 recommendations
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize recommendations engine
        
        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.user_storage = UserStorageService(database)
        self.repo_storage = RepositoryStorageService(database)
        self.analysis_storage = AnalysisStorageService(database)
        self.logger = logger
    
    async def generate_recommendations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of recommendations
            
        Returns:
            List of recommendation dictionaries
        """
        self.logger.info(f"Generating recommendations for user: {user_id}")
        
        # Get repositories
        repos = await self.repo_storage.get_user_repositories(
            user_id,
            analyzed_only=True
        )
        
        if not repos:
            return []
        
        # Generate recommendations for each repository
        all_recommendations = []
        
        for repo in repos:
            repo_recommendations = self._generate_repo_recommendations(repo)
            all_recommendations.extend(repo_recommendations)
        
        # Sort by impact (descending)
        all_recommendations.sort(key=lambda x: x['impact'], reverse=True)
        
        # Limit to top N
        return all_recommendations[:limit]
    
    def _generate_repo_recommendations(
        self,
        repo: Any
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for a single repository
        
        Args:
            repo: Repository object
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Check for missing tests
        if not getattr(repo, 'has_tests', False):
            recommendations.append({
                'repository': repo.name,
                'category': repo.category,
                'action': 'Add test coverage',
                'description': f'Implement unit tests for {repo.name}',
                'steps': [
                    'Set up testing framework (pytest, jest, etc.)',
                    'Write tests for core functionality',
                    'Aim for at least 70% code coverage',
                    'Add tests to CI/CD pipeline'
                ],
                'impact': self._calculate_test_impact(repo),
                'difficulty': 'medium',
                'estimated_time': '4-8 hours'
            })
        
        # Check for missing CI/CD
        if not getattr(repo, 'has_ci_cd', False):
            recommendations.append({
                'repository': repo.name,
                'category': repo.category,
                'action': 'Set up CI/CD pipeline',
                'description': f'Add GitHub Actions or similar CI/CD to {repo.name}',
                'steps': [
                    'Create .github/workflows directory',
                    'Add workflow file for automated testing',
                    'Configure build and test steps',
                    'Add status badge to README'
                ],
                'impact': self._calculate_cicd_impact(repo),
                'difficulty': 'easy',
                'estimated_time': '1-2 hours'
            })
        
        # Check for high complexity
        if hasattr(repo, 'complexity_metrics') and repo.complexity_metrics:
            if isinstance(repo.complexity_metrics, dict):
                cyclomatic = repo.complexity_metrics.get('cyclomatic', 0.0)
                
                if cyclomatic > 15:
                    recommendations.append({
                        'repository': repo.name,
                        'category': repo.category,
                        'action': 'Refactor complex functions',
                        'description': f'Reduce cyclomatic complexity in {repo.name}',
                        'steps': [
                            'Identify functions with high complexity',
                            'Break down large functions into smaller ones',
                            'Extract complex logic into separate functions',
                            'Add comments to explain complex sections'
                        ],
                        'impact': self._calculate_complexity_impact(repo, cyclomatic),
                        'difficulty': 'hard',
                        'estimated_time': '8-16 hours'
                    })
        
        # Check for missing README
        if not getattr(repo, 'has_readme', False):
            recommendations.append({
                'repository': repo.name,
                'category': repo.category,
                'action': 'Add README documentation',
                'description': f'Create comprehensive README for {repo.name}',
                'steps': [
                    'Add project description and purpose',
                    'Include installation instructions',
                    'Document usage examples',
                    'Add contributing guidelines'
                ],
                'impact': self._calculate_readme_impact(repo),
                'difficulty': 'easy',
                'estimated_time': '1-2 hours'
            })
        
        # Check for missing license
        if not getattr(repo, 'license', None):
            recommendations.append({
                'repository': repo.name,
                'category': repo.category,
                'action': 'Add license',
                'description': f'Add open source license to {repo.name}',
                'steps': [
                    'Choose appropriate license (MIT, Apache, GPL, etc.)',
                    'Add LICENSE file to repository',
                    'Update README with license information'
                ],
                'impact': self._calculate_license_impact(repo),
                'difficulty': 'easy',
                'estimated_time': '15 minutes'
            })
        
        # Check for low ACID scores
        if hasattr(repo, 'acid_scores') and repo.acid_scores:
            if isinstance(repo.acid_scores, dict):
                # Check atomicity
                atomicity = repo.acid_scores.get('atomicity', 0.0)
                if atomicity < 60:
                    recommendations.append({
                        'repository': repo.name,
                        'category': repo.category,
                        'action': 'Improve modularity',
                        'description': f'Refactor {repo.name} for better modularity',
                        'steps': [
                            'Break down large files into smaller modules',
                            'Ensure single responsibility per function',
                            'Reduce function size (aim for <50 lines)',
                            'Improve class cohesion'
                        ],
                        'impact': self._calculate_atomicity_impact(repo, atomicity),
                        'difficulty': 'hard',
                        'estimated_time': '8-16 hours'
                    })
                
                # Check consistency
                consistency = repo.acid_scores.get('consistency', 0.0)
                if consistency < 60:
                    recommendations.append({
                        'repository': repo.name,
                        'category': repo.category,
                        'action': 'Improve code consistency',
                        'description': f'Standardize code style in {repo.name}',
                        'steps': [
                            'Set up linter (ESLint, Pylint, etc.)',
                            'Define code style guidelines',
                            'Add inline documentation',
                            'Use consistent naming conventions'
                        ],
                        'impact': self._calculate_consistency_impact(repo, consistency),
                        'difficulty': 'medium',
                        'estimated_time': '4-8 hours'
                    })
                
                # Check durability
                durability = repo.acid_scores.get('durability', 0.0)
                if durability < 60:
                    recommendations.append({
                        'repository': repo.name,
                        'category': repo.category,
                        'action': 'Improve maintainability',
                        'description': f'Enhance long-term maintainability of {repo.name}',
                        'steps': [
                            'Add comprehensive documentation',
                            'Implement automated tests',
                            'Set up CI/CD pipeline',
                            'Add code comments for complex logic'
                        ],
                        'impact': self._calculate_durability_impact(repo, durability),
                        'difficulty': 'medium',
                        'estimated_time': '6-12 hours'
                    })
        
        return recommendations
    
    def _calculate_test_impact(self, repo: Any) -> float:
        """Calculate impact of adding tests"""
        # Tests significantly improve durability score
        base_impact = 10.0
        
        # Higher impact for flagship repositories
        if repo.category == 'flagship':
            base_impact *= 1.5
        elif repo.category == 'significant':
            base_impact *= 1.2
        
        return round(base_impact, 1)
    
    def _calculate_cicd_impact(self, repo: Any) -> float:
        """Calculate impact of adding CI/CD"""
        # CI/CD improves durability and consistency
        base_impact = 8.0
        
        # Higher impact for flagship repositories
        if repo.category == 'flagship':
            base_impact *= 1.5
        elif repo.category == 'significant':
            base_impact *= 1.2
        
        return round(base_impact, 1)
    
    def _calculate_complexity_impact(self, repo: Any, complexity: float) -> float:
        """Calculate impact of reducing complexity"""
        # Impact scales with how high the complexity is
        base_impact = min(15.0, (complexity - 10) * 0.5)
        
        # Higher impact for flagship repositories
        if repo.category == 'flagship':
            base_impact *= 1.5
        elif repo.category == 'significant':
            base_impact *= 1.2
        
        return round(base_impact, 1)
    
    def _calculate_readme_impact(self, repo: Any) -> float:
        """Calculate impact of adding README"""
        # README improves consistency and durability
        base_impact = 5.0
        
        # Higher impact for flagship repositories
        if repo.category == 'flagship':
            base_impact *= 1.5
        elif repo.category == 'significant':
            base_impact *= 1.2
        
        return round(base_impact, 1)
    
    def _calculate_license_impact(self, repo: Any) -> float:
        """Calculate impact of adding license"""
        # License has moderate impact on quality score
        base_impact = 3.0
        
        # Higher impact for flagship repositories
        if repo.category == 'flagship':
            base_impact *= 1.5
        elif repo.category == 'significant':
            base_impact *= 1.2
        
        return round(base_impact, 1)
    
    def _calculate_atomicity_impact(self, repo: Any, current_score: float) -> float:
        """Calculate impact of improving atomicity"""
        # Impact based on how much improvement is possible
        potential_gain = 80 - current_score  # Aim for 80
        base_impact = potential_gain * 0.25  # 25% of potential gain
        
        # Higher impact for flagship repositories
        if repo.category == 'flagship':
            base_impact *= 1.5
        elif repo.category == 'significant':
            base_impact *= 1.2
        
        return round(base_impact, 1)
    
    def _calculate_consistency_impact(self, repo: Any, current_score: float) -> float:
        """Calculate impact of improving consistency"""
        # Impact based on how much improvement is possible
        potential_gain = 80 - current_score
        base_impact = potential_gain * 0.25
        
        # Higher impact for flagship repositories
        if repo.category == 'flagship':
            base_impact *= 1.5
        elif repo.category == 'significant':
            base_impact *= 1.2
        
        return round(base_impact, 1)
    
    def _calculate_durability_impact(self, repo: Any, current_score: float) -> float:
        """Calculate impact of improving durability"""
        # Impact based on how much improvement is possible
        potential_gain = 80 - current_score
        base_impact = potential_gain * 0.25
        
        # Higher impact for flagship repositories
        if repo.category == 'flagship':
            base_impact *= 1.5
        elif repo.category == 'significant':
            base_impact *= 1.2
        
        return round(base_impact, 1)
