"""
Score Calculation Service
Calculates weighted overall developer scores from evaluated repositories.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ScoreCalculationService:
    """
    Service for calculating overall developer scores.
    
    Implements weighted averaging:
    - Flagship repositories: 60% weight
    - Significant repositories: 40% weight
    
    Requirements: 9.1-9.6
    """
    
    def __init__(self):
        """Initialize score calculation service"""
        self.flagship_weight = 0.6
        self.significant_weight = 0.4
    
    def calculate_overall_score(
        self,
        evaluated_repositories: List[Dict[str, Any]]
    ) -> Optional[float]:
        """
        Calculate weighted overall developer score.
        
        Args:
            evaluated_repositories: List of evaluated repository dictionaries
            
        Returns:
            Overall score (0-100) or None if no evaluated repositories
            
        Requirements: 9.2, 9.3, 9.4, 9.5
        """
        if not evaluated_repositories:
            logger.info("No evaluated repositories - returning None for overall score")
            return None
        
        # Separate by category
        flagship_repos = [
            r for r in evaluated_repositories 
            if r.get('category') == 'flagship' and r.get('evaluation')
        ]
        significant_repos = [
            r for r in evaluated_repositories 
            if r.get('category') == 'significant' and r.get('evaluation')
        ]
        
        # Extract scores
        flagship_scores = [
            r['evaluation']['overall_score'] 
            for r in flagship_repos
        ]
        significant_scores = [
            r['evaluation']['overall_score'] 
            for r in significant_repos
        ]
        
        # Handle edge cases
        if not flagship_scores and not significant_scores:
            logger.warning("No valid evaluation scores found")
            return None
        
        # Calculate weighted average
        overall_score = self._calculate_weighted_average(
            flagship_scores,
            significant_scores
        )
        
        logger.info(
            f"Calculated overall score: {overall_score:.1f} "
            f"(flagship: {len(flagship_scores)}, significant: {len(significant_scores)})"
        )
        
        return overall_score
    
    def _calculate_weighted_average(
        self,
        flagship_scores: List[float],
        significant_scores: List[float]
    ) -> float:
        """
        Calculate weighted average of flagship and significant scores.
        
        Args:
            flagship_scores: List of flagship repository scores
            significant_scores: List of significant repository scores
            
        Returns:
            Weighted average score
        """
        if flagship_scores and significant_scores:
            # Both categories present: apply 60/40 weighting
            flagship_avg = sum(flagship_scores) / len(flagship_scores)
            significant_avg = sum(significant_scores) / len(significant_scores)
            
            overall = (flagship_avg * self.flagship_weight) + (significant_avg * self.significant_weight)
            
            logger.debug(
                f"Weighted average: flagship_avg={flagship_avg:.1f} (60%), "
                f"significant_avg={significant_avg:.1f} (40%), overall={overall:.1f}"
            )
            
        elif flagship_scores:
            # Only flagship repositories
            overall = sum(flagship_scores) / len(flagship_scores)
            logger.debug(f"Only flagship repos: avg={overall:.1f}")
            
        else:
            # Only significant repositories
            overall = sum(significant_scores) / len(significant_scores)
            logger.debug(f"Only significant repos: avg={overall:.1f}")
        
        return round(overall, 1)
    
    def generate_score_breakdown(
        self,
        evaluated_repositories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate detailed score breakdown with metadata.
        
        Args:
            evaluated_repositories: List of evaluated repository dictionaries
            
        Returns:
            Dictionary with score breakdown and metadata
            
        Requirements: 9.6
        """
        if not evaluated_repositories:
            return {
                'overall_score': None,
                'flagship_count': 0,
                'significant_count': 0,
                'total_evaluated': 0,
                'flagship_average': None,
                'significant_average': None,
                'score_breakdown': None
            }
        
        # Separate by category
        flagship_repos = [
            r for r in evaluated_repositories 
            if r.get('category') == 'flagship' and r.get('evaluation')
        ]
        significant_repos = [
            r for r in evaluated_repositories 
            if r.get('category') == 'significant' and r.get('evaluation')
        ]
        
        # Extract scores
        flagship_scores = [r['evaluation']['overall_score'] for r in flagship_repos]
        significant_scores = [r['evaluation']['overall_score'] for r in significant_repos]
        
        # Calculate averages
        flagship_avg = sum(flagship_scores) / len(flagship_scores) if flagship_scores else None
        significant_avg = sum(significant_scores) / len(significant_scores) if significant_scores else None
        
        # Calculate overall score
        overall_score = self.calculate_overall_score(evaluated_repositories)
        
        # Generate breakdown
        breakdown = {
            'overall_score': overall_score,
            'flagship_count': len(flagship_repos),
            'significant_count': len(significant_repos),
            'total_evaluated': len(flagship_repos) + len(significant_repos),
            'flagship_average': round(flagship_avg, 1) if flagship_avg else None,
            'significant_average': round(significant_avg, 1) if significant_avg else None,
            'score_breakdown': self._generate_detailed_breakdown(
                flagship_scores,
                significant_scores,
                overall_score
            )
        }
        
        return breakdown
    
    def _generate_detailed_breakdown(
        self,
        flagship_scores: List[float],
        significant_scores: List[float],
        overall_score: Optional[float]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate detailed score breakdown showing contribution of each category.
        
        Args:
            flagship_scores: List of flagship scores
            significant_scores: List of significant scores
            overall_score: Calculated overall score
            
        Returns:
            Detailed breakdown dictionary
        """
        if overall_score is None:
            return None
        
        breakdown = {
            'overall_score': overall_score,
            'components': []
        }
        
        if flagship_scores:
            flagship_avg = sum(flagship_scores) / len(flagship_scores)
            flagship_contribution = flagship_avg * self.flagship_weight
            
            breakdown['components'].append({
                'category': 'flagship',
                'count': len(flagship_scores),
                'average_score': round(flagship_avg, 1),
                'weight': self.flagship_weight,
                'contribution': round(flagship_contribution, 1),
                'percentage': f"{self.flagship_weight * 100:.0f}%"
            })
        
        if significant_scores:
            significant_avg = sum(significant_scores) / len(significant_scores)
            significant_contribution = significant_avg * self.significant_weight
            
            breakdown['components'].append({
                'category': 'significant',
                'count': len(significant_scores),
                'average_score': round(significant_avg, 1),
                'weight': self.significant_weight,
                'contribution': round(significant_contribution, 1),
                'percentage': f"{self.significant_weight * 100:.0f}%"
            })
        
        return breakdown
    
    def validate_score_calculation(
        self,
        evaluated_repositories: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that score calculation can be performed.
        
        Args:
            evaluated_repositories: List of evaluated repositories
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not evaluated_repositories:
            return False, "No evaluated repositories provided"
        
        # Check for valid evaluations
        valid_evals = [
            r for r in evaluated_repositories
            if r.get('evaluation') and 'overall_score' in r.get('evaluation', {})
        ]
        
        if not valid_evals:
            return False, "No repositories with valid evaluation scores"
        
        # Check for valid categories
        categorized = [
            r for r in valid_evals
            if r.get('category') in ['flagship', 'significant']
        ]
        
        if not categorized:
            return False, "No repositories with valid categories (flagship/significant)"
        
        return True, None
    
    def get_score_statistics(
        self,
        evaluated_repositories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistical information about evaluated repository scores.
        
        Args:
            evaluated_repositories: List of evaluated repositories
            
        Returns:
            Dictionary with statistical information
        """
        if not evaluated_repositories:
            return {
                'count': 0,
                'min_score': None,
                'max_score': None,
                'average_score': None,
                'median_score': None
            }
        
        # Extract all scores
        all_scores = [
            r['evaluation']['overall_score']
            for r in evaluated_repositories
            if r.get('evaluation') and 'overall_score' in r.get('evaluation', {})
        ]
        
        if not all_scores:
            return {
                'count': 0,
                'min_score': None,
                'max_score': None,
                'average_score': None,
                'median_score': None
            }
        
        # Calculate statistics
        sorted_scores = sorted(all_scores)
        count = len(sorted_scores)
        
        return {
            'count': count,
            'min_score': round(min(sorted_scores), 1),
            'max_score': round(max(sorted_scores), 1),
            'average_score': round(sum(sorted_scores) / count, 1),
            'median_score': round(
                sorted_scores[count // 2] if count % 2 == 1
                else (sorted_scores[count // 2 - 1] + sorted_scores[count // 2]) / 2,
                1
            )
        }


# Singleton instance
score_calculation_service = ScoreCalculationService()
