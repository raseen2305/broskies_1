"""
Base orchestrator interface
All orchestration services should inherit from this
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
import logging
from datetime import datetime


class BaseOrchestrator(ABC):
    """
    Abstract base class for all orchestration services
    
    Orchestrators coordinate multiple services to complete complex workflows
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the orchestrator
        
        Args:
            logger: Optional logger instance. If not provided, creates a new one.
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    @abstractmethod
    async def execute(
        self,
        user_id: str,
        github_token: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute the orchestrated workflow
        
        Args:
            user_id: User identifier
            github_token: GitHub OAuth token
            progress_callback: Optional callback for progress updates
            
        Returns:
            Results dictionary
            
        Raises:
            ValueError: If input is invalid
            RuntimeError: If execution fails
        """
        pass
    
    def start_timer(self) -> None:
        """Start execution timer"""
        self.start_time = datetime.utcnow()
        self.logger.info(f"Starting {self.__class__.__name__}")
    
    def stop_timer(self) -> float:
        """
        Stop execution timer and return duration
        
        Returns:
            Duration in seconds
        """
        self.end_time = datetime.utcnow()
        if self.start_time:
            duration = (self.end_time - self.start_time).total_seconds()
            self.logger.info(
                f"Completed {self.__class__.__name__} in {duration:.2f}s"
            )
            return duration
        return 0.0
    
    async def update_progress(
        self,
        progress_callback: Optional[Callable],
        progress_data: Dict[str, Any]
    ) -> None:
        """
        Update progress via callback
        
        Args:
            progress_callback: Progress callback function
            progress_data: Progress data to send
        """
        if progress_callback:
            try:
                await progress_callback(progress_data)
            except Exception as e:
                self.logger.error(f"Progress callback failed: {e}")
    
    def validate_inputs(self, user_id: str, github_token: str) -> bool:
        """
        Validate orchestrator inputs
        
        Args:
            user_id: User identifier
            github_token: GitHub token
            
        Returns:
            True if valid, False otherwise
        """
        if not user_id or not isinstance(user_id, str):
            self.logger.error("Invalid user_id")
            return False
        
        if not github_token or not isinstance(github_token, str):
            self.logger.error("Invalid github_token")
            return False
        
        return True
