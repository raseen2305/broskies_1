"""
GitHub Rate Limiter
Manages API rate limits and implements retry logic with exponential backoff
"""

import asyncio
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from enum import Enum

from ..config import get_config
from ..utils import get_logger


class APIType(Enum):
    """GitHub API types"""
    GRAPHQL = "graphql"
    REST = "rest"


class GitHubRateLimiter:
    """
    GitHub API rate limiter
    
    Tracks API usage and implements retry logic with exponential backoff
    - GraphQL: 5000 points/hour
    - REST: 5000 requests/hour
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize rate limiter
        
        Args:
            logger: Optional logger instance
        """
        self.config = get_config()
        self.logger = logger or get_logger(__name__)
        
        # Rate limit tracking
        self._graphql_calls = 0
        self._rest_calls = 0
        self._reset_time = datetime.utcnow() + timedelta(hours=1)
        
        # Retry configuration
        self.max_retries = self.config.MAX_RETRY_ATTEMPTS
        self.backoff_base = self.config.RETRY_BACKOFF_BASE
    
    async def execute_with_retry(
        self,
        api_type: APIType,
        func,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute API call with retry logic
        
        Args:
            api_type: Type of API (GraphQL or REST)
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RuntimeError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Check rate limit before call
                await self._check_rate_limit(api_type)
                
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Track successful call
                self._track_call(api_type)
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if it's a rate limit error
                if self._is_rate_limit_error(e):
                    self.logger.warning(f"Rate limit hit, waiting...")
                    await self._wait_for_rate_limit_reset()
                    continue
                
                # Check if it's a retryable error
                if not self._is_retryable_error(e):
                    self.logger.error(f"Non-retryable error: {e}")
                    raise
                
                # Calculate backoff time
                if attempt < self.max_retries - 1:
                    backoff_time = self._calculate_backoff(attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {backoff_time:.2f}s: {e}"
                    )
                    await asyncio.sleep(backoff_time)
        
        # All retries failed
        self.logger.error(f"All {self.max_retries} attempts failed")
        raise RuntimeError(
            f"API call failed after {self.max_retries} attempts: {last_exception}"
        )
    
    async def _check_rate_limit(self, api_type: APIType) -> None:
        """
        Check if rate limit allows another call
        
        Args:
            api_type: Type of API
        """
        # Reset counters if hour has passed
        if datetime.utcnow() >= self._reset_time:
            self._reset_counters()
        
        # Check limits
        if api_type == APIType.GRAPHQL:
            if self._graphql_calls >= 5000:
                self.logger.warning("GraphQL rate limit reached, waiting...")
                await self._wait_for_rate_limit_reset()
        else:
            if self._rest_calls >= 5000:
                self.logger.warning("REST rate limit reached, waiting...")
                await self._wait_for_rate_limit_reset()
    
    def _track_call(self, api_type: APIType) -> None:
        """
        Track an API call
        
        Args:
            api_type: Type of API
        """
        if api_type == APIType.GRAPHQL:
            self._graphql_calls += 1
        else:
            self._rest_calls += 1
        
        self.logger.debug(
            f"API calls - GraphQL: {self._graphql_calls}, REST: {self._rest_calls}"
        )
    
    def _reset_counters(self) -> None:
        """Reset rate limit counters"""
        self._graphql_calls = 0
        self._rest_calls = 0
        self._reset_time = datetime.utcnow() + timedelta(hours=1)
        self.logger.info("Rate limit counters reset")
    
    async def _wait_for_rate_limit_reset(self) -> None:
        """Wait until rate limit resets"""
        now = datetime.utcnow()
        if now < self._reset_time:
            wait_seconds = (self._reset_time - now).total_seconds()
            self.logger.info(f"Waiting {wait_seconds:.0f}s for rate limit reset")
            await asyncio.sleep(wait_seconds)
        
        self._reset_counters()
    
    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff time
        
        Args:
            attempt: Attempt number (0-indexed)
            
        Returns:
            Backoff time in seconds
        """
        return self.backoff_base ** attempt
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """
        Check if error is a rate limit error
        
        Args:
            error: Exception to check
            
        Returns:
            True if rate limit error, False otherwise
        """
        error_str = str(error).lower()
        return any(phrase in error_str for phrase in [
            'rate limit',
            'too many requests',
            '429',
            'api rate limit exceeded'
        ])
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Check if error is retryable
        
        Args:
            error: Exception to check
            
        Returns:
            True if retryable, False otherwise
        """
        # Network errors are retryable
        retryable_types = (
            asyncio.TimeoutError,
            ConnectionError,
            OSError
        )
        
        if isinstance(error, retryable_types):
            return True
        
        # Check error message for retryable conditions
        error_str = str(error).lower()
        retryable_phrases = [
            'timeout',
            'connection',
            'network',
            'temporary',
            '500',
            '502',
            '503',
            '504'
        ]
        
        return any(phrase in error_str for phrase in retryable_phrases)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current rate limit usage statistics
        
        Returns:
            Dictionary with usage stats
        """
        now = datetime.utcnow()
        time_until_reset = (self._reset_time - now).total_seconds()
        
        return {
            'graphql_calls': self._graphql_calls,
            'graphql_remaining': 5000 - self._graphql_calls,
            'rest_calls': self._rest_calls,
            'rest_remaining': 5000 - self._rest_calls,
            'reset_time': self._reset_time.isoformat(),
            'seconds_until_reset': max(0, time_until_reset)
        }
    
    def log_usage(self) -> None:
        """Log current usage statistics"""
        stats = self.get_usage_stats()
        self.logger.info(
            f"Rate limit usage - "
            f"GraphQL: {stats['graphql_calls']}/5000, "
            f"REST: {stats['rest_calls']}/5000, "
            f"Reset in: {stats['seconds_until_reset']:.0f}s"
        )
