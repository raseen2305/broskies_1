"""
Enhanced Evaluation Service
Provides batch evaluation capabilities and production indicator detection
for the intelligent repository scoring system.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedEvaluationService:
    """
    Enhanced evaluation service for batch repository evaluation.
    
    Provides:
    - Batch evaluation of multiple repositories
    - Production indicator detection
    - Strength and weakness identification
    - Simplified evaluation for repositories without full code analysis
    
    Requirements: 5.1-5.7
    """
    
    def __init__(self, github_scanner=None):
        """
        Initialize enhanced evaluation service.
        
        Args:
            github_scanner: Optional GitHub scanner for fetching repository data
        """
        self.github_scanner = github_scanner
        
    async def evaluate_repository_batch(
        self,
        repositories: List[Dict[str, Any]],
        github_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple repositories in batch.
        
        Args:
            repositories: List of repository dictionaries
            github_token: Optional GitHub token for API access
            
        Returns:
            List of repositories with evaluation data added
        """
        evaluated_repos = []
        
        for repo in repositories:
            try:
                evaluation = await self.evaluate_repository_simple(repo, github_token)
                repo['evaluation'] = evaluation
                repo['evaluated'] = True
                evaluated_repos.append(repo)
                
            except Exception as e:
                logger.error(f"Failed to evaluate {repo.get('name')}: {e}")
                repo['evaluated'] = False
                repo['evaluation'] = None
        
        return evaluated_repos
    
    async def evaluate_repository_simple(
        self,
        repo: Dict[str, Any],
        github_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simplified repository evaluation without full code analysis.
        
        Uses repository metadata and production indicators to generate
        evaluation scores and insights.
        
        Args:
            repo: Repository dictionary with metadata
            github_token: Optional GitHub token
            
        Returns:
            Evaluation dictionary with scores and insights
        """
        # Detect production indicators
        production_indicators = self.detect_production_indicators(repo)
        
        # Calculate base scores from metadata
        acid_scores = self._calculate_acid_scores_from_metadata(repo, production_indicators)
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics_from_metadata(repo, production_indicators)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(acid_scores, quality_metrics)
        
        # Identify strengths and weaknesses
        strengths = self._identify_strengths(repo, production_indicators, acid_scores)
        improvements = self._identify_improvements(repo, production_indicators, acid_scores)
        
        return {
            'overall_score': overall_score,
            'acid_scores': acid_scores,
            'quality_metrics': quality_metrics,
            'production_indicators': production_indicators,
            'strengths': strengths,
            'improvements': improvements,
            'evaluated_at': datetime.utcnow().isoformat(),
            'evaluation_type': 'metadata_based'
        }
    
    def detect_production_indicators(self, repo: Dict[str, Any]) -> Dict[str, bool]:
        """
        Detect production indicators from repository metadata.
        
        Indicators:
        - has_tests: Test files or testing frameworks detected
        - has_ci_cd: CI/CD configuration files detected
        - has_docker: Docker configuration detected
        - has_monitoring: Monitoring/logging tools detected
        
        Args:
            repo: Repository dictionary
            
        Returns:
            Dictionary of production indicators
        """
        indicators = {
            'has_tests': False,
            'has_ci_cd': False,
            'has_docker': False,
            'has_monitoring': False
        }
        
        # Check for tests
        indicators['has_tests'] = self._detect_tests(repo)
        
        # Check for CI/CD
        indicators['has_ci_cd'] = self._detect_ci_cd(repo)
        
        # Check for Docker
        indicators['has_docker'] = self._detect_docker(repo)
        
        # Check for monitoring
        indicators['has_monitoring'] = self._detect_monitoring(repo)
        
        return indicators
    
    def _detect_tests(self, repo: Dict[str, Any]) -> bool:
        """Detect if repository has tests"""
        # Check topics
        topics = repo.get('topics', []) or []
        test_topics = ['testing', 'test', 'unit-testing', 'integration-testing', 
                       'pytest', 'jest', 'mocha', 'junit']
        if any(topic in test_topics for topic in topics):
            return True
        
        # Check description
        description = (repo.get('description') or '').lower()
        test_keywords = ['test', 'testing', 'pytest', 'jest', 'junit', 'mocha', 'spec']
        if any(keyword in description for keyword in test_keywords):
            return True
        
        # Check explicit flag
        if repo.get('has_tests'):
            return True
        
        return False
    
    def _detect_ci_cd(self, repo: Dict[str, Any]) -> bool:
        """Detect if repository has CI/CD"""
        # Check topics
        topics = repo.get('topics', []) or []
        ci_cd_topics = ['ci', 'cd', 'continuous-integration', 'continuous-deployment',
                        'github-actions', 'travis', 'jenkins', 'circleci', 'gitlab-ci']
        if any(topic in ci_cd_topics for topic in topics):
            return True
        
        # Check description
        description = (repo.get('description') or '').lower()
        ci_cd_keywords = ['ci/cd', 'github actions', 'travis', 'jenkins', 
                          'circleci', 'continuous integration', 'pipeline']
        if any(keyword in description for keyword in ci_cd_keywords):
            return True
        
        # Check explicit flag
        if repo.get('has_ci_cd'):
            return True
        
        return False
    
    def _detect_docker(self, repo: Dict[str, Any]) -> bool:
        """Detect if repository uses Docker"""
        # Check topics
        topics = repo.get('topics', []) or []
        docker_topics = ['docker', 'dockerfile', 'docker-compose', 'containerization']
        if any(topic in docker_topics for topic in topics):
            return True
        
        # Check description
        description = (repo.get('description') or '').lower()
        docker_keywords = ['docker', 'container', 'dockerfile']
        if any(keyword in description for keyword in docker_keywords):
            return True
        
        return False
    
    def _detect_monitoring(self, repo: Dict[str, Any]) -> bool:
        """Detect if repository has monitoring/logging"""
        # Check topics
        topics = repo.get('topics', []) or []
        monitoring_topics = ['monitoring', 'logging', 'observability', 'prometheus',
                            'grafana', 'elk', 'datadog', 'sentry']
        if any(topic in monitoring_topics for topic in topics):
            return True
        
        # Check description
        description = (repo.get('description') or '').lower()
        monitoring_keywords = ['monitoring', 'logging', 'observability', 'metrics']
        if any(keyword in description for keyword in monitoring_keywords):
            return True
        
        return False
    
    def _calculate_acid_scores_from_metadata(
        self,
        repo: Dict[str, Any],
        production_indicators: Dict[str, bool]
    ) -> Dict[str, float]:
        """
        Calculate ACID scores from repository metadata.
        
        Args:
            repo: Repository dictionary
            production_indicators: Production indicators
            
        Returns:
            Dictionary of ACID scores
        """
        # Base scores from repository characteristics
        size = repo.get('size', 0)
        stars = repo.get('stargazers_count', 0) or repo.get('stars', 0) or 0
        forks = repo.get('forks_count', 0) or repo.get('forks', 0) or 0
        
        # Architecture score (based on size and structure)
        architecture_score = min(70 + (size / 1000), 95)
        if production_indicators['has_docker']:
            architecture_score += 5
        
        # Code quality score (based on production indicators)
        code_quality_score = 70
        if production_indicators['has_tests']:
            code_quality_score += 10
        if production_indicators['has_ci_cd']:
            code_quality_score += 10
        
        # Innovation score (based on community engagement)
        innovation_score = 65
        if stars > 50:
            innovation_score += 15
        elif stars > 20:
            innovation_score += 10
        elif stars > 10:
            innovation_score += 5
        
        # Documentation score (based on description and size)
        documentation_score = 70
        if repo.get('description'):
            documentation_score += 10
        if repo.get('homepage'):
            documentation_score += 5
        
        return {
            'architecture': min(architecture_score, 100),
            'code_quality': min(code_quality_score, 100),
            'innovation': min(innovation_score, 100),
            'documentation': min(documentation_score, 100)
        }
    
    def _calculate_quality_metrics_from_metadata(
        self,
        repo: Dict[str, Any],
        production_indicators: Dict[str, bool]
    ) -> Dict[str, float]:
        """Calculate quality metrics from metadata"""
        # Base quality score
        base_quality = 70
        
        # Adjust based on production indicators
        if production_indicators['has_tests']:
            base_quality += 8
        if production_indicators['has_ci_cd']:
            base_quality += 8
        if production_indicators['has_docker']:
            base_quality += 7
        if production_indicators['has_monitoring']:
            base_quality += 7
        
        return {
            'code_quality': min(base_quality, 100),
            'technical_excellence': min(base_quality + 5, 100),
            'production_readiness': min(base_quality + 3, 100),
            'innovation_score': min(base_quality - 5, 100)
        }
    
    def _calculate_overall_score(
        self,
        acid_scores: Dict[str, float],
        quality_metrics: Dict[str, float]
    ) -> float:
        """Calculate overall score from ACID scores and quality metrics"""
        # Weight ACID scores
        acid_avg = sum(acid_scores.values()) / len(acid_scores)
        
        # Weight quality metrics
        quality_avg = sum(quality_metrics.values()) / len(quality_metrics)
        
        # Combined score (60% ACID, 40% quality)
        overall = (acid_avg * 0.6) + (quality_avg * 0.4)
        
        return round(overall, 1)
    
    def _identify_strengths(
        self,
        repo: Dict[str, Any],
        production_indicators: Dict[str, bool],
        acid_scores: Dict[str, float]
    ) -> List[str]:
        """Identify repository strengths"""
        strengths = []
        
        # Check production indicators
        if production_indicators['has_tests']:
            strengths.append('Comprehensive test coverage')
        
        if production_indicators['has_ci_cd']:
            strengths.append('Automated CI/CD pipeline')
        
        if production_indicators['has_docker']:
            strengths.append('Containerized deployment')
        
        if production_indicators['has_monitoring']:
            strengths.append('Production monitoring and observability')
        
        # Check ACID scores
        if acid_scores['architecture'] >= 85:
            strengths.append('Well-structured architecture')
        
        if acid_scores['code_quality'] >= 85:
            strengths.append('High code quality standards')
        
        if acid_scores['documentation'] >= 85:
            strengths.append('Excellent documentation')
        
        # Check community engagement
        stars = repo.get('stargazers_count', 0) or repo.get('stars', 0) or 0
        if stars > 50:
            strengths.append('Strong community engagement')
        
        # Check repository size
        size = repo.get('size', 0)
        if size > 5000:
            strengths.append('Substantial codebase demonstrating experience')
        
        # Ensure at least some strengths
        if not strengths:
            strengths.append('Active development')
        
        return strengths[:5]  # Limit to top 5
    
    def _identify_improvements(
        self,
        repo: Dict[str, Any],
        production_indicators: Dict[str, bool],
        acid_scores: Dict[str, float]
    ) -> List[str]:
        """Identify areas for improvement"""
        improvements = []
        
        # Check missing production indicators
        if not production_indicators['has_tests']:
            improvements.append('Add comprehensive unit and integration tests')
        
        if not production_indicators['has_ci_cd']:
            improvements.append('Implement CI/CD pipeline for automated testing and deployment')
        
        if not production_indicators['has_docker']:
            improvements.append('Add Docker containerization for consistent deployments')
        
        if not production_indicators['has_monitoring']:
            improvements.append('Implement monitoring and logging for production observability')
        
        # Check ACID scores
        if acid_scores['documentation'] < 75:
            improvements.append('Improve documentation with README, API docs, and code comments')
        
        if acid_scores['code_quality'] < 75:
            improvements.append('Enhance code quality with linting and code reviews')
        
        # Check description
        if not repo.get('description'):
            improvements.append('Add a clear project description')
        
        # Limit to top 5 most important
        return improvements[:5]


# Singleton instance
enhanced_evaluation_service = EnhancedEvaluationService()
