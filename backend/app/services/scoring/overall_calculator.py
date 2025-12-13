"""
Overall Score Calculator
Calculates weighted overall developer score from repository scores
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class OverallScoreBreakdown:
    """Container for overall score breakdown"""
    overall_score: float
    flagship_average: float
    significant_average: float
    flagship_count: int
    significant_count: int
    flagship_weight: float = 0.60
    significant_weight: float = 0.40


class OverallScoreCalculator:
    """
    Calculates overall developer score
    
    Formula: (Flagship Average × 0.60) + (Significant Average × 0.40)
    
    Handles edge cases:
    - Only flagship repositories
    - Only significant repositories
    - No analyzed repositories
    """
    
    # Weights from requirements
    FLAGSHIP_WEIGHT = 0.60
    SIGNIFICANT_WEIGHT = 0.40
    
    def __init__(self):
        """Initialize overall score calculator"""
        self.logger = logger
    
    def calculate_overall_score(
        self,
        repositories: List[Dict[str, Any]]
    ) -> OverallScoreBreakdown:
        """
        Calculate overall developer score from repositories
        
        Args:
            repositories: List of repository dictionaries with scores
            
        Returns:
            OverallScoreBreakdown object
        """
        # Separate repositories by category
        flagship_repos = [
            r for r in repositories
            if r.get('category') == 'flagship' and r.get('analyzed', False)
        ]
        
        significant_repos = [
            r for r in repositories
            if r.get('category') == 'significant' and r.get('analyzed', False)
        ]
        
        # Calculate averages
        flagship_avg = self._calculate_average_score(flagship_repos)
        significant_avg = self._calculate_average_score(significant_repos)
        
        # Calculate weighted overall score
        overall = self._calculate_weighted_score(
            flagship_avg,
            significant_avg,
            len(flagship_repos),
            len(significant_repos)
        )
        
        self.logger.info(
            f"Calculated overall score: {overall:.1f} "
            f"(flagship: {flagship_avg:.1f}, significant: {significant_avg:.1f})"
        )
        
        return OverallScoreBreakdown(
            overall_score=overall,
            flagship_average=flagship_avg,
            significant_average=significant_avg,
            flagship_count=len(flagship_repos),
            significant_count=len(significant_repos)
        )
    
    def _calculate_average_score(
        self,
        repositories: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate average score for a list of repositories
        
        Args:
            repositories: List of repository dictionaries
            
        Returns:
            Average score (0.0 if no repositories)
        """
        if not repositories:
            return 0.0
        
        # Get overall scores from repositories
        scores = []
        for repo in repositories:
            # Try to get overall_score from different possible locations
            score = repo.get('overall_score')
            
            if score is None and 'acid_scores' in repo:
                # Try to get from acid_scores
                acid_scores = repo['acid_scores']
                if isinstance(acid_scores, dict):
                    score = acid_scores.get('overall')
            
            if score is not None:
                scores.append(float(score))
        
        if not scores:
            return 0.0
        
        average = sum(scores) / len(scores)
        return round(average, 1)
    
    def _calculate_weighted_score(
        self,
        flagship_avg: float,
        significant_avg: float,
        flagship_count: int,
        significant_count: int
    ) -> float:
        """
        Calculate weighted overall score with volume bonus
        
        New formula rewards both quality AND quantity:
        - Base score from quality (weighted average)
        - Volume multiplier based on repository count
        - Flagship repos have higher impact than significant
        
        Args:
            flagship_avg: Average flagship score
            significant_avg: Average significant score
            flagship_count: Number of flagship repositories
            significant_count: Number of significant repositories
            
        Returns:
            Weighted overall score (0-100)
        """
        # Edge case: No analyzed repositories
        if flagship_count == 0 and significant_count == 0:
            return 0.0
        
        # Calculate base quality score (weighted average)
        if flagship_count > 0 and significant_count == 0:
            base_score = flagship_avg
        elif flagship_count == 0 and significant_count > 0:
            base_score = significant_avg
        else:
            # Both categories present - weighted average
            base_score = (
                flagship_avg * self.FLAGSHIP_WEIGHT +
                significant_avg * self.SIGNIFICANT_WEIGHT
            )
        
        # Calculate volume multiplier (rewards having more quality repos)
        # Flagship repos count more than significant (2x weight)
        weighted_repo_count = (flagship_count * 2.0) + (significant_count * 1.0)
        
        # Volume multiplier formula:
        # - 1-2 repos: 0.85x (slight penalty for very small portfolio)
        # - 3-5 repos: 0.95x (small portfolio)
        # - 6-10 repos: 1.00x (baseline)
        # - 11-20 repos: 1.05x (good portfolio size)
        # - 21-30 repos: 1.08x (large portfolio)
        # - 31+ repos: 1.10x (very large portfolio, capped)
        
        if weighted_repo_count <= 2:
            volume_multiplier = 0.85
        elif weighted_repo_count <= 5:
            volume_multiplier = 0.95
        elif weighted_repo_count <= 10:
            volume_multiplier = 1.00
        elif weighted_repo_count <= 20:
            volume_multiplier = 1.05
        elif weighted_repo_count <= 30:
            volume_multiplier = 1.08
        else:
            volume_multiplier = 1.10
        
        # Apply volume multiplier to base score
        final_score = base_score * volume_multiplier
        
        # Cap at 100
        final_score = min(100.0, final_score)
        
        self.logger.info(
            f"Score calculation: base={base_score:.1f}, "
            f"volume_multiplier={volume_multiplier:.2f}x "
            f"(flagship={flagship_count}, significant={significant_count}), "
            f"final={final_score:.1f}"
        )
        
        return round(final_score, 1)
    
    def get_score_grade(self, score: float) -> str:
        """
        Get letter grade for overall score
        
        Args:
            score: Overall score (0-100)
            
        Returns:
            Letter grade (A-F)
        """
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
    
    def get_score_description(self, score: float) -> str:
        """
        Get description for overall score
        
        Args:
            score: Overall score (0-100)
            
        Returns:
            Score description
        """
        if score >= 90:
            return 'Exceptional - Top-tier developer with outstanding code quality'
        elif score >= 80:
            return 'Excellent - Strong developer with high-quality code'
        elif score >= 70:
            return 'Good - Competent developer with solid code practices'
        elif score >= 60:
            return 'Fair - Developing skills with room for improvement'
        elif score >= 50:
            return 'Needs Improvement - Basic skills, significant growth needed'
        else:
            return 'Beginner - Early stage developer, focus on fundamentals'
    
    def calculate_score_from_acid(
        self,
        acid_scores: Dict[str, float],
        complexity_metrics: Dict[str, float],
        quality_metrics: Dict[str, float]
    ) -> float:
        """
        Calculate repository overall score from ACID and other metrics
        
        Args:
            acid_scores: ACID scores dictionary
            complexity_metrics: Complexity metrics dictionary
            quality_metrics: Quality metrics dictionary
            
        Returns:
            Repository overall score (0-100)
        """
        # Primary weight on ACID overall score (70%)
        acid_overall = acid_scores.get('overall', 0.0)
        
        # Secondary weight on maintainability (20%)
        maintainability = complexity_metrics.get('maintainability_index', 0.0)
        
        # Tertiary weight on quality metrics (10%)
        quality_avg = 0.0
        if quality_metrics:
            quality_values = [
                quality_metrics.get('readability', 0.0),
                quality_metrics.get('maintainability', 0.0),
                quality_metrics.get('security', 0.0),
                quality_metrics.get('test_coverage', 0.0),
                quality_metrics.get('documentation', 0.0)
            ]
            quality_avg = sum(quality_values) / len(quality_values)
        
        # Calculate weighted score
        overall = (
            acid_overall * 0.70 +
            maintainability * 0.20 +
            quality_avg * 0.10
        )
        
        return round(overall, 1)
    
    def validate_score(self, score: float) -> bool:
        """
        Validate that a score is within valid range
        
        Args:
            score: Score to validate
            
        Returns:
            True if valid (0-100), False otherwise
        """
        return 0.0 <= score <= 100.0
    
    def get_percentile_description(self, percentile: float) -> str:
        """
        Get description for percentile ranking
        
        Args:
            percentile: Percentile (0-100)
            
        Returns:
            Percentile description
        """
        if percentile >= 95:
            return 'Top 5% - Elite developer'
        elif percentile >= 90:
            return 'Top 10% - Exceptional developer'
        elif percentile >= 75:
            return 'Top 25% - Strong developer'
        elif percentile >= 50:
            return 'Top 50% - Above average developer'
        elif percentile >= 25:
            return 'Top 75% - Average developer'
        else:
            return 'Below average - Room for growth'
    
    def calculate_improvement_potential(
        self,
        current_score: float,
        flagship_avg: float,
        significant_avg: float
    ) -> Dict[str, Any]:
        """
        Calculate potential score improvement
        
        Args:
            current_score: Current overall score
            flagship_avg: Current flagship average
            significant_avg: Current significant average
            
        Returns:
            Dictionary with improvement analysis
        """
        # Calculate potential if flagship improved to 100
        potential_flagship_100 = (
            100.0 * self.FLAGSHIP_WEIGHT +
            significant_avg * self.SIGNIFICANT_WEIGHT
        )
        flagship_potential = potential_flagship_100 - current_score
        
        # Calculate potential if significant improved to 100
        potential_significant_100 = (
            flagship_avg * self.FLAGSHIP_WEIGHT +
            100.0 * self.SIGNIFICANT_WEIGHT
        )
        significant_potential = potential_significant_100 - current_score
        
        # Calculate potential if both improved to 100
        max_potential = 100.0 - current_score
        
        return {
            'current_score': current_score,
            'max_potential': round(max_potential, 1),
            'flagship_improvement_potential': round(flagship_potential, 1),
            'significant_improvement_potential': round(significant_potential, 1),
            'recommendation': (
                'Focus on flagship repositories' if flagship_potential > significant_potential
                else 'Focus on significant repositories'
            )
        }
