"""
Importance Scorer
Calculates repository importance without code analysis
Target: <0.01 seconds per repository
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from ..base import BaseScorer
from ..config import get_config
from ..utils import get_logger, clamp, safe_divide


class ImportanceScorer(BaseScorer):
    """
    Repository importance scorer
    
    Calculates importance score (0-100) based on:
    - Community engagement (40%): stars, forks, watchers
    - Activity (30%): last update date
    - Size (20%): repository size
    - Quality (10%): README, license, topics
    
    No code extraction required - uses metadata only
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize importance scorer
        
        Args:
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.config = get_config()
        
        # Weights from configuration
        self.community_weight = self.config.IMPORTANCE_COMMUNITY_WEIGHT
        self.activity_weight = self.config.IMPORTANCE_ACTIVITY_WEIGHT
        self.size_weight = self.config.IMPORTANCE_SIZE_WEIGHT
        self.quality_weight = self.config.IMPORTANCE_QUALITY_WEIGHT
    
    def calculate_score(self, data: Dict[str, Any]) -> float:
        """
        Calculate importance score for a repository
        
        Args:
            data: Repository data dictionary
            
        Returns:
            Importance score (0-100)
            
        Raises:
            ValueError: If input data is invalid
        """
        if not self.validate_input(data):
            raise ValueError("Invalid repository data")
        
        # Calculate component scores
        community_score = self._calculate_community_score(data)
        activity_score = self._calculate_activity_score(data)
        size_score = self._calculate_size_score(data)
        quality_score = self._calculate_quality_score(data)
        
        # Weighted average
        importance_score = (
            community_score * self.community_weight +
            activity_score * self.activity_weight +
            size_score * self.size_weight +
            quality_score * self.quality_weight
        )
        
        # Clamp to 0-100 range
        importance_score = clamp(importance_score, 0.0, 100.0)
        
        self.log_score(
            importance_score,
            f"for {data.get('name', 'unknown')}"
        )
        
        return round(importance_score, 1)
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validate repository data
        
        Args:
            data: Repository data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['stars', 'forks', 'size', 'updated_at']
        
        if not isinstance(data, dict):
            return False
        
        for field in required_fields:
            if field not in data:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        return True
    
    def get_score_breakdown(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get detailed breakdown of importance score
        
        Args:
            data: Repository data
            
        Returns:
            Dictionary with component scores
        """
        return {
            'community': self._calculate_community_score(data),
            'activity': self._calculate_activity_score(data),
            'size': self._calculate_size_score(data),
            'quality': self._calculate_quality_score(data)
        }
    
    def _calculate_community_score(self, repo: Dict[str, Any]) -> float:
        """
        Calculate community engagement score
        
        Based on stars, forks, and watchers
        
        Args:
            repo: Repository data
            
        Returns:
            Community score (0-100)
        """
        stars = repo.get('stars', 0)
        forks = repo.get('forks', 0)
        watchers = repo.get('watchers', 0)
        
        # Weighted formula
        # Stars are most important, then forks, then watchers
        raw_score = (stars * 2) + (forks * 5) + (watchers * 1)
        
        # Normalize to 0-100 scale
        # 100+ stars/forks = 100 score
        # Use logarithmic scale for better distribution
        if raw_score == 0:
            return 0.0
        
        # Logarithmic scaling
        import math
        normalized = min(100, (math.log10(raw_score + 1) / math.log10(101)) * 100)
        
        return clamp(normalized, 0.0, 100.0)
    
    def _calculate_activity_score(self, repo: Dict[str, Any]) -> float:
        """
        Calculate activity score based on last update
        
        Args:
            repo: Repository data
            
        Returns:
            Activity score (0-100)
        """
        updated_at = repo.get('updated_at')
        
        if not updated_at:
            return 50.0  # Default for missing data
        
        # Parse datetime if string
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except Exception:
                return 50.0
        
        # Calculate days since last update
        now = datetime.utcnow()
        if updated_at.tzinfo:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        
        days_old = (now - updated_at).days
        
        # Scoring based on recency
        if days_old < 30:
            return 100.0
        elif days_old < 90:
            return 90.0
        elif days_old < 180:
            return 75.0
        elif days_old < 365:
            return 60.0
        else:
            # Decay after 1 year
            years_old = days_old / 365
            score = max(0, 60 - (years_old - 1) * 10)
            return clamp(score, 0.0, 100.0)
    
    def _calculate_size_score(self, repo: Dict[str, Any]) -> float:
        """
        Calculate size score
        
        Larger repositories generally indicate more work/complexity
        
        Args:
            repo: Repository data
            
        Returns:
            Size score (0-100)
        """
        size = repo.get('size', 0)  # Size in KB
        
        # Scoring based on size
        if size >= 10000:  # 10+ MB
            return 100.0
        elif size >= 5000:  # 5-10 MB
            return 90.0
        elif size >= 1000:  # 1-5 MB
            return 80.0
        elif size >= 500:   # 500KB - 1MB
            return 70.0
        elif size >= 100:   # 100KB - 500KB
            return 60.0
        else:
            # Very small repos get lower scores
            return 50.0
    
    def _calculate_quality_score(self, repo: Dict[str, Any]) -> float:
        """
        Calculate quality indicators score
        
        Based on README, license, description, topics
        
        Args:
            repo: Repository data
            
        Returns:
            Quality score (0-100)
        """
        score = 0.0
        
        # README (25 points)
        if repo.get('has_readme'):
            score += 25.0
        
        # License (25 points)
        if repo.get('license') or repo.get('has_license_file'):
            score += 25.0
        
        # Description (25 points)
        description = repo.get('description', '')
        if description and len(description.strip()) > 10:
            score += 25.0
        
        # Topics (25 points)
        topics = repo.get('topics', [])
        if topics and len(topics) > 0:
            # More topics = better documentation
            topic_score = min(25.0, len(topics) * 5)
            score += topic_score
        
        return clamp(score, 0.0, 100.0)
    
    def categorize(self, importance_score: float) -> str:
        """
        Categorize repository based on importance score
        
        Args:
            importance_score: Importance score (0-100)
            
        Returns:
            Category: 'flagship', 'significant', or 'supporting'
        """
        if importance_score >= self.config.FLAGSHIP_THRESHOLD:
            return 'flagship'
        elif importance_score >= self.config.SIGNIFICANT_THRESHOLD:
            return 'significant'
        else:
            return 'supporting'
    
    def get_category_description(self, category: str) -> str:
        """
        Get description for a category
        
        Args:
            category: Category name
            
        Returns:
            Category description
        """
        descriptions = {
            'flagship': 'High-impact repositories that define your portfolio',
            'significant': 'Important repositories that contribute to your score',
            'supporting': 'Supporting repositories (not included in scoring)'
        }
        return descriptions.get(category, 'Unknown category')
