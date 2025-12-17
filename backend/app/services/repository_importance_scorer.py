"""
Repository Importance Scorer Service
Calculates importance scores for repositories based on size metrics and production indicators.
Categorizes repositories into flagship, significant, and supporting tiers.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class RepositoryImportanceScorer:
    """
    Service for calculating repository importance scores and categorizing repositories.
    
    Scoring breakdown:
    - Lines of code: 30%
    - File count: 30%
    - Production indicators: 40%
    """
    
    def __init__(self):
        """Initialize the repository importance scorer."""
        self.weights = {
            'lines_of_code': 30,
            'file_count': 30,
            'production_indicators': 40
        }
        
        # Thresholds for lines of code scoring (STRICTER)
        self.loc_thresholds = [
            (50000, 30),   # 50k+ lines = full points
            (25000, 25),   # 25k-50k lines
            (10000, 20),   # 10k-25k lines
            (5000, 15),    # 5k-10k lines
            (2000, 10),    # 2k-5k lines
            (500, 5),      # 500-2k lines
            (0, 0)         # <500 lines = 0 points
        ]
        
        # Thresholds for file count scoring (STRICTER)
        self.file_count_thresholds = [
            (200, 30),     # 200+ files = full points
            (100, 25),     # 100-200 files
            (50, 20),      # 50-100 files
            (25, 15),      # 25-50 files
            (15, 10),      # 15-25 files
            (5, 5),        # 5-15 files
            (0, 0)         # <5 files = 0 points
        ]
        
        # Category thresholds (STRICTER)
        self.category_thresholds = {
            'flagship': 80,    # Raised from 70 to 80
            'significant': 60  # Raised from 50 to 60
        }
        
    def calculate_importance_score(self, repo: Dict[str, Any]) -> int:
        """
        Calculate importance score (0-100) for a repository.
        
        Args:
            repo: Repository data dictionary containing size, language, and metadata
            
        Returns:
            Integer score from 0 to 100
        """
        score = 0
        
        # Calculate lines of code score (30 points)
        loc_score = self._calculate_loc_score(repo)
        score += loc_score
        
        # Calculate file count score (30 points)
        file_count_score = self._calculate_file_count_score(repo)
        score += file_count_score
        
        # Calculate production indicators score (40 points)
        production_score = self._calculate_production_score(repo)
        score += production_score
        
        # Ensure score is within bounds
        final_score = min(max(score, 0), 100)
        
        logger.debug(
            f"Repository '{repo.get('name', 'unknown')}' importance score: {final_score} "
            f"(LOC: {loc_score}, Files: {file_count_score}, Production: {production_score})"
        )
        
        return final_score
    
    def _calculate_loc_score(self, repo: Dict[str, Any]) -> int:
        """
        Calculate score based on lines of code (30 points max).
        
        Uses GitHub size field (in KB) and estimates lines using: size_kb * 35
        
        Args:
            repo: Repository data dictionary
            
        Returns:
            Score from 0 to 30
        """
        size_kb = repo.get('size', 0)
        
        # Estimate lines of code: size_kb * 35 (average ~35 lines per KB)
        estimated_lines = size_kb * 35
        
        # Find appropriate score based on thresholds
        for threshold, points in self.loc_thresholds:
            if estimated_lines >= threshold:
                return points
        
        return 5  # Minimum score
    
    def _calculate_file_count_score(self, repo: Dict[str, Any]) -> int:
        """
        Calculate score based on file count (30 points max).
        
        If exact file count is available, use it. Otherwise, estimate from size.
        
        Args:
            repo: Repository data dictionary
            
        Returns:
            Score from 0 to 30
        """
        # Try to get exact file count if available
        file_count = repo.get('file_count')
        
        if file_count is None:
            # Estimate from size: size_kb / 10 (average ~10 KB per file)
            size_kb = repo.get('size', 0)
            file_count = size_kb / 10 if size_kb > 0 else 0
        
        # Find appropriate score based on thresholds
        for threshold, points in self.file_count_thresholds:
            if file_count >= threshold:
                return points
        
        return 5  # Minimum score
    
    def _calculate_production_score(self, repo: Dict[str, Any]) -> int:
        """
        Calculate score based on production indicators (40 points max).
        
        Production indicators include:
        - Has tests (10 points)
        - Has CI/CD configuration (10 points)
        - Recent activity (10 points)
        - Community engagement (stars, forks, watchers) (10 points)
        
        Args:
            repo: Repository data dictionary
            
        Returns:
            Score from 0 to 40
        """
        score = 0
        
        # Check for test indicators (10 points)
        if self._has_tests(repo):
            score += 10
        
        # Check for CI/CD indicators (10 points)
        if self._has_ci_cd(repo):
            score += 10
        
        # Check for recent activity (10 points)
        activity_score = self._calculate_activity_score(repo)
        score += activity_score
        
        # Check for community engagement (10 points)
        engagement_score = self._calculate_engagement_score(repo)
        score += engagement_score
        
        return score
    
    def _has_tests(self, repo: Dict[str, Any]) -> bool:
        """
        Check if repository has test indicators.
        
        Looks for:
        - 'test' in topics
        - has_tests flag
        - Common test directories/files in description
        
        Args:
            repo: Repository data dictionary
            
        Returns:
            True if tests are detected
        """
        # Check topics
        topics = repo.get('topics', [])
        if topics and any('test' in topic.lower() for topic in topics):
            return True
        
        # Check explicit flag
        if repo.get('has_tests', False):
            return True
        
        # Check description for test keywords
        description = repo.get('description', '') or ''
        if description:
            description_lower = description.lower()
            test_keywords = ['test', 'testing', 'pytest', 'jest', 'junit', 'mocha']
            if any(keyword in description_lower for keyword in test_keywords):
                return True
        
        return False
    
    def _has_ci_cd(self, repo: Dict[str, Any]) -> bool:
        """
        Check if repository has CI/CD indicators.
        
        Looks for:
        - 'ci', 'cd', 'github-actions', 'travis', 'jenkins' in topics
        - has_ci_cd flag
        - CI/CD keywords in description
        
        Args:
            repo: Repository data dictionary
            
        Returns:
            True if CI/CD is detected
        """
        # Check topics
        topics = repo.get('topics', [])
        if topics:
            ci_cd_topics = ['ci', 'cd', 'continuous-integration', 'github-actions', 
                            'travis', 'jenkins', 'circleci', 'gitlab-ci']
            if any(topic.lower() in ci_cd_topics for topic in topics):
                return True
        
        # Check explicit flag
        if repo.get('has_ci_cd', False):
            return True
        
        # Check description for CI/CD keywords
        description = repo.get('description', '') or ''
        if description:
            description_lower = description.lower()
            ci_cd_keywords = ['ci/cd', 'github actions', 'travis', 'jenkins', 
                              'circleci', 'gitlab ci', 'continuous integration']
            if any(keyword in description_lower for keyword in ci_cd_keywords):
                return True
        
        return False
    
    def _calculate_activity_score(self, repo: Dict[str, Any]) -> int:
        """
        Calculate score based on recent activity (10 points max).
        
        Considers (STRICTER):
        - Updated within last 7 days: 10 points
        - Updated within last 30 days: 8 points
        - Updated within last 90 days: 5 points
        - Updated within last 180 days: 3 points
        - Updated within last year: 1 point
        - Older: 0 points
        
        Args:
            repo: Repository data dictionary
            
        Returns:
            Score from 0 to 10
        """
        updated_at = repo.get('updated_at')
        if not updated_at:
            return 0
        
        try:
            # Parse the updated_at timestamp
            if isinstance(updated_at, str):
                updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            else:
                updated_date = updated_at
            
            now = datetime.now(updated_date.tzinfo) if updated_date.tzinfo else datetime.now()
            days_since_update = (now - updated_date).days
            
            if days_since_update <= 7:
                return 10
            elif days_since_update <= 30:
                return 8
            elif days_since_update <= 90:
                return 5
            elif days_since_update <= 180:
                return 3
            elif days_since_update <= 365:
                return 1
            else:
                return 0
        except Exception as e:
            logger.warning(f"Error calculating activity score: {e}")
            return 0
    
    def _calculate_engagement_score(self, repo: Dict[str, Any]) -> int:
        """
        Calculate score based on community engagement (10 points max).
        
        Considers stars, forks, and watchers (STRICTER):
        - Exceptional engagement (total >= 500): 10 points
        - High engagement (total >= 200): 8 points
        - Good engagement (total >= 100): 6 points
        - Moderate engagement (total >= 50): 4 points
        - Some engagement (total >= 20): 2 points
        - Low engagement (total >= 5): 1 point
        - No engagement: 0 points
        
        Args:
            repo: Repository data dictionary
            
        Returns:
            Score from 0 to 10
        """
        stars = repo.get('stargazers_count', 0) or repo.get('stars', 0) or 0
        forks = repo.get('forks_count', 0) or repo.get('forks', 0) or 0
        watchers = repo.get('watchers_count', 0) or repo.get('watchers', 0) or 0
        
        # Calculate total engagement score (forks weighted 2x)
        total_engagement = stars + (forks * 2) + watchers
        
        if total_engagement >= 500:
            return 10
        elif total_engagement >= 200:
            return 8
        elif total_engagement >= 100:
            return 6
        elif total_engagement >= 50:
            return 4
        elif total_engagement >= 20:
            return 2
        elif total_engagement >= 5:
            return 1
        else:
            return 0
    
    def categorize_repositories(self, repositories: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize repositories into flagship, significant, and supporting tiers.
        
        Categories:
        - Flagship: importance_score >= 70 (top-tier production projects)
        - Significant: importance_score >= 50 and < 70 (solid development work)
        - Supporting: importance_score < 50 (learning/experimental projects)
        
        Args:
            repositories: List of repository dictionaries with importance_score field
            
        Returns:
            Dictionary with keys 'flagship', 'significant', 'supporting', and 'all'
        """
        flagship = []
        significant = []
        supporting = []
        
        # Sort repositories by importance score (descending)
        sorted_repos = sorted(
            repositories, 
            key=lambda r: r.get('importance_score', 0), 
            reverse=True
        )
        
        for repo in sorted_repos:
            score = repo.get('importance_score', 0)
            
            if score >= self.category_thresholds['flagship']:
                repo['category'] = 'flagship'
                flagship.append(repo)
            elif score >= self.category_thresholds['significant']:
                repo['category'] = 'significant'
                significant.append(repo)
            else:
                repo['category'] = 'supporting'
                supporting.append(repo)
        
        logger.info(
            f"Categorized {len(repositories)} repositories: "
            f"{len(flagship)} flagship, {len(significant)} significant, "
            f"{len(supporting)} supporting"
        )
        
        return {
            'all': sorted_repos,
            'flagship': flagship,
            'significant': significant,
            'supporting': supporting
        }
    
    def select_for_evaluation(
        self, 
        categorized_repos: Dict[str, List[Dict[str, Any]]], 
        max_evaluate: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Select top repositories for deep evaluation.
        
        Selection strategy:
        - Include all flagship repositories
        - Include significant repositories up to max_evaluate limit
        - Prioritize by importance score
        
        Args:
            categorized_repos: Dictionary from categorize_repositories()
            max_evaluate: Maximum number of repositories to evaluate (default: 15)
            
        Returns:
            List of repositories selected for evaluation
        """
        flagship = categorized_repos.get('flagship', [])
        significant = categorized_repos.get('significant', [])
        
        # Start with all flagship repos
        selected = flagship.copy()
        
        # Add significant repos until we reach max_evaluate
        remaining_slots = max_evaluate - len(selected)
        if remaining_slots > 0:
            selected.extend(significant[:remaining_slots])
        
        logger.info(
            f"Selected {len(selected)} repositories for evaluation: "
            f"{len(flagship)} flagship, {len(selected) - len(flagship)} significant"
        )
        
        return selected
