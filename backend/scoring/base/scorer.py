"""
Base scorer interface
All scoring services should inherit from this
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging


class BaseScorer(ABC):
    """
    Abstract base class for all scoring services
    
    Provides common functionality and enforces interface contract
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the scorer
        
        Args:
            logger: Optional logger instance. If not provided, creates a new one.
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def calculate_score(self, data: Dict[str, Any]) -> float:
        """
        Calculate a score based on input data
        
        Args:
            data: Input data for scoring
            
        Returns:
            Score value (typically 0-100)
            
        Raises:
            ValueError: If input data is invalid
        """
        pass
    
    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validate input data before scoring
        
        Args:
            data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def get_score_breakdown(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get detailed breakdown of score components
        
        Args:
            data: Input data for scoring
            
        Returns:
            Dictionary with component scores
        """
        return {}
    
    def log_score(self, score: float, context: str = "") -> None:
        """
        Log a calculated score
        
        Args:
            score: The calculated score
            context: Additional context for logging
        """
        self.logger.info(f"Score calculated: {score:.2f} {context}")
