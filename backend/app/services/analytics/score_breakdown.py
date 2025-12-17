"""
Score Breakdown Service
Generates detailed breakdowns of scores and metrics
"""

from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.services.storage import (
    UserStorageService,
    RepositoryStorageService,
    AnalysisStorageService
)
from app.services.scoring import OverallScoreCalculator

logger = logging.getLogger(__name__)


class ScoreBreakdownService:
    """
    Generates detailed score breakdowns
    
    Provides:
    - Overall score breakdown with calculation details
    - ACID component breakdown with grades
    - Repository breakdown by category
    - Complexity metrics breakdown
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize score breakdown service
        
        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.user_storage = UserStorageService(database)
        self.repo_storage = RepositoryStorageService(database)
        self.analysis_storage = AnalysisStorageService(database)
        self.overall_calculator = OverallScoreCalculator()
        self.logger = logger
    
    async def generate_complete_breakdown(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate complete score breakdown for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with complete breakdown
        """
        self.logger.info(f"Generating score breakdown for user: {user_id}")
        
        # Get user profile
        user = await self.user_storage.get_user_by_id(user_id)
        
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Generate all breakdowns
        overall_breakdown = await self.generate_overall_breakdown(user_id)
        acid_breakdown = await self.generate_acid_breakdown(user_id)
        repository_breakdown = await self.generate_repository_breakdown(user_id)
        complexity_breakdown = await self.generate_complexity_breakdown(user_id)
        
        return {
            'user_id': user_id,
            'github_username': user.github_username,
            'overall': overall_breakdown,
            'acid': acid_breakdown,
            'repositories': repository_breakdown,
            'complexity': complexity_breakdown
        }
    
    async def generate_overall_breakdown(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate overall score breakdown
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with overall score breakdown
        """
        # Get user profile
        user = await self.user_storage.get_user_by_id(user_id)
        
        if not user or not user.overall_score:
            return {
                'score': 0.0,
                'grade': 'F',
                'description': 'No score available',
                'calculation': None
            }
        
        # Get repositories
        repos = await self.repo_storage.get_user_repositories(
            user_id,
            analyzed_only=True
        )
        
        # Separate by category
        flagship = [r for r in repos if r.category == 'flagship']
        significant = [r for r in repos if r.category == 'significant']
        
        # Calculate averages
        flagship_scores = [r.overall_score for r in flagship if r.overall_score]
        significant_scores = [r.overall_score for r in significant if r.overall_score]
        
        flagship_avg = (
            sum(flagship_scores) / len(flagship_scores)
            if flagship_scores else 0.0
        )
        significant_avg = (
            sum(significant_scores) / len(significant_scores)
            if significant_scores else 0.0
        )
        
        # Get grade and description
        grade = self.overall_calculator.get_score_grade(user.overall_score)
        description = self.overall_calculator.get_score_description(user.overall_score)
        
        return {
            'score': user.overall_score,
            'grade': grade,
            'description': description,
            'calculation': {
                'formula': '(Flagship × 0.60) + (Significant × 0.40)',
                'flagship': {
                    'average': round(flagship_avg, 1),
                    'count': len(flagship),
                    'weight': 0.60,
                    'contribution': round(flagship_avg * 0.60, 1)
                },
                'significant': {
                    'average': round(significant_avg, 1),
                    'count': len(significant),
                    'weight': 0.40,
                    'contribution': round(significant_avg * 0.40, 1)
                }
            }
        }
    
    async def generate_acid_breakdown(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate ACID component breakdown
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with ACID breakdown
        """
        # Get average ACID scores for flagship
        flagship_acid = await self.analysis_storage.get_average_acid_scores(
            user_id,
            category='flagship'
        )
        
        # Get average ACID scores for significant
        significant_acid = await self.analysis_storage.get_average_acid_scores(
            user_id,
            category='significant'
        )
        
        # Get overall average
        overall_acid = await self.analysis_storage.get_average_acid_scores(user_id)
        
        if not overall_acid:
            return {
                'overall': 0.0,
                'grade': 'F',
                'components': {}
            }
        
        # Generate component breakdowns
        components = {}
        
        for component in ['atomicity', 'consistency', 'isolation', 'durability']:
            overall_score = getattr(overall_acid, component, 0.0)
            flagship_score = getattr(flagship_acid, component, 0.0) if flagship_acid else 0.0
            significant_score = getattr(significant_acid, component, 0.0) if significant_acid else 0.0
            
            components[component] = {
                'score': round(overall_score, 1),
                'grade': self._get_acid_grade(overall_score),
                'description': self._get_component_description(component),
                'flagship': round(flagship_score, 1),
                'significant': round(significant_score, 1)
            }
        
        return {
            'overall': round(overall_acid.overall, 1),
            'grade': self._get_acid_grade(overall_acid.overall),
            'components': components
        }
    
    async def generate_repository_breakdown(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate repository breakdown by category
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with repository breakdown
        """
        # Get all repositories
        repos = await self.repo_storage.get_user_repositories(user_id)
        
        # Separate by category
        flagship = [r for r in repos if r.category == 'flagship']
        significant = [r for r in repos if r.category == 'significant']
        supporting = [r for r in repos if r.category == 'supporting']
        
        # Generate breakdown for each category
        return {
            'total': len(repos),
            'flagship': {
                'count': len(flagship),
                'repositories': [
                    self._format_repository(r) for r in
                    sorted(flagship, key=lambda x: x.importance_score or 0, reverse=True)
                ]
            },
            'significant': {
                'count': len(significant),
                'repositories': [
                    self._format_repository(r) for r in
                    sorted(significant, key=lambda x: x.importance_score or 0, reverse=True)
                ]
            },
            'supporting': {
                'count': len(supporting),
                'repositories': [
                    self._format_repository(r) for r in
                    sorted(supporting, key=lambda x: x.importance_score or 0, reverse=True)
                ][:10]  # Limit to top 10
            }
        }
    
    async def generate_complexity_breakdown(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate complexity metrics breakdown
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with complexity breakdown
        """
        # Get all analyzed repositories
        repos = await self.repo_storage.get_user_repositories(
            user_id,
            analyzed_only=True
        )
        
        if not repos:
            return {
                'average_cyclomatic': 0.0,
                'average_cognitive': 0.0,
                'average_maintainability': 0.0,
                'total_lines': 0,
                'total_functions': 0,
                'total_classes': 0
            }
        
        # Aggregate complexity metrics
        total_cyclomatic = 0.0
        total_cognitive = 0.0
        total_maintainability = 0.0
        total_lines = 0
        total_functions = 0
        total_classes = 0
        count = 0
        
        for repo in repos:
            if hasattr(repo, 'complexity_metrics') and repo.complexity_metrics:
                metrics = repo.complexity_metrics
                
                if isinstance(metrics, dict):
                    total_cyclomatic += metrics.get('cyclomatic', 0.0)
                    total_cognitive += metrics.get('cognitive', 0.0)
                    total_maintainability += metrics.get('maintainability', 0.0)
                    total_lines += metrics.get('lines_of_code', 0)
                    total_functions += metrics.get('function_count', 0)
                    total_classes += metrics.get('class_count', 0)
                    count += 1
        
        # Calculate averages
        avg_cyclomatic = total_cyclomatic / count if count > 0 else 0.0
        avg_cognitive = total_cognitive / count if count > 0 else 0.0
        avg_maintainability = total_maintainability / count if count > 0 else 0.0
        
        return {
            'average_cyclomatic': round(avg_cyclomatic, 1),
            'average_cognitive': round(avg_cognitive, 1),
            'average_maintainability': round(avg_maintainability, 1),
            'cyclomatic_grade': self._get_complexity_grade(avg_cyclomatic),
            'maintainability_grade': self._get_maintainability_grade(avg_maintainability),
            'total_lines': total_lines,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'repositories_analyzed': count
        }
    
    def _format_repository(self, repo: Any) -> Dict[str, Any]:
        """
        Format repository for breakdown
        
        Args:
            repo: Repository object
            
        Returns:
            Formatted repository dictionary
        """
        result = {
            'id': str(repo.id),
            'name': repo.name,
            'category': repo.category,
            'importance_score': repo.importance_score,
            'language': repo.language,
            'stars': repo.stars
        }
        
        # Add analysis data if available
        if repo.analyzed:
            result['analyzed'] = True
            result['overall_score'] = repo.overall_score
            
            if hasattr(repo, 'acid_scores') and repo.acid_scores:
                if isinstance(repo.acid_scores, dict):
                    result['acid_score'] = repo.acid_scores.get('overall', 0.0)
        else:
            result['analyzed'] = False
        
        return result
    
    def _get_acid_grade(self, score: float) -> str:
        """Get letter grade for ACID score"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _get_complexity_grade(self, complexity: float) -> str:
        """Get letter grade for complexity"""
        if complexity <= 5:
            return 'A'
        elif complexity <= 10:
            return 'B'
        elif complexity <= 20:
            return 'C'
        elif complexity <= 30:
            return 'D'
        else:
            return 'F'
    
    def _get_maintainability_grade(self, mi: float) -> str:
        """Get letter grade for maintainability index"""
        if mi >= 85:
            return 'A'
        elif mi >= 70:
            return 'B'
        elif mi >= 50:
            return 'C'
        elif mi >= 30:
            return 'D'
        else:
            return 'F'
    
    def _get_component_description(self, component: str) -> str:
        """Get description for ACID component"""
        descriptions = {
            'atomicity': 'Modularity, single responsibility, function size, and cohesion',
            'consistency': 'Naming conventions, code style, and documentation',
            'isolation': 'Dependencies, architecture separation, and coupling',
            'durability': 'Test coverage, documentation, and maintainability'
        }
        return descriptions.get(component, '')
