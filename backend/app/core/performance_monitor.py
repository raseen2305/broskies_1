"""
Performance Monitoring
Tracks and logs performance metrics for optimization
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Monitors and tracks performance metrics
    
    Tracks execution times, identifies bottlenecks, and logs performance data
    """
    
    def __init__(self):
        """Initialize performance monitor"""
        self.metrics: Dict[str, list] = {}
        self.thresholds: Dict[str, float] = {
            'stage1_scan': 1.0,  # Stage 1 target: <1 second
            'stage2_analysis': 35.0,  # Stage 2 target: <35 seconds
            'api_endpoint': 0.5,  # API endpoints: <500ms
            'database_query': 0.1,  # Database queries: <100ms
        }
    
    def record_metric(
        self,
        operation: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a performance metric
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            metadata: Additional metadata
        """
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        metric = {
            'timestamp': datetime.utcnow(),
            'duration': duration,
            'metadata': metadata or {}
        }
        
        self.metrics[operation].append(metric)
        
        # Check against threshold
        threshold = self.thresholds.get(operation)
        if threshold and duration > threshold:
            logger.warning(
                f"Performance threshold exceeded: {operation} took {duration:.2f}s "
                f"(threshold: {threshold}s)"
            )
        else:
            logger.info(f"Performance: {operation} completed in {duration:.2f}s")
    
    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics
        
        Args:
            operation: Optional operation name to filter by
            
        Returns:
            Dictionary of metrics
        """
        if operation:
            if operation not in self.metrics:
                return {}
            
            metrics = self.metrics[operation]
            durations = [m['duration'] for m in metrics]
            
            return {
                'operation': operation,
                'count': len(metrics),
                'avg_duration': sum(durations) / len(durations) if durations else 0,
                'min_duration': min(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0,
                'threshold': self.thresholds.get(operation),
                'recent': metrics[-10:]  # Last 10 metrics
            }
        
        # Return all metrics
        result = {}
        for op in self.metrics.keys():
            result[op] = self.get_metrics(op)
        
        return result
    
    def clear_metrics(self, operation: Optional[str] = None):
        """
        Clear metrics
        
        Args:
            operation: Optional operation name to clear, or None for all
        """
        if operation:
            if operation in self.metrics:
                self.metrics[operation] = []
        else:
            self.metrics = {}
    
    def set_threshold(self, operation: str, threshold: float):
        """
        Set performance threshold for an operation
        
        Args:
            operation: Operation name
            threshold: Threshold in seconds
        """
        self.thresholds[operation] = threshold
        logger.info(f"Set performance threshold for {operation}: {threshold}s")


# Global instance
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get global performance monitor instance
    
    Returns:
        PerformanceMonitor instance
    """
    return _performance_monitor


def monitor_performance(operation: str, threshold: Optional[float] = None):
    """
    Decorator to monitor function performance
    
    Args:
        operation: Operation name
        threshold: Optional custom threshold
        
    Usage:
        @monitor_performance('my_operation', threshold=1.0)
        async def my_function():
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                monitor = get_performance_monitor()
                
                # Set custom threshold if provided
                if threshold is not None:
                    monitor.set_threshold(operation, threshold)
                
                monitor.record_metric(
                    operation,
                    duration,
                    metadata={
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                monitor = get_performance_monitor()
                
                # Set custom threshold if provided
                if threshold is not None:
                    monitor.set_threshold(operation, threshold)
                
                monitor.record_metric(
                    operation,
                    duration,
                    metadata={
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                )
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class PerformanceTimer:
    """
    Context manager for timing code blocks
    
    Usage:
        with PerformanceTimer('my_operation') as timer:
            # code to time
            pass
        print(f"Duration: {timer.duration}s")
    """
    
    def __init__(self, operation: str, log: bool = True):
        """
        Initialize timer
        
        Args:
            operation: Operation name
            log: Whether to log the result
        """
        self.operation = operation
        self.log = log
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        """Start timer"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and record metric"""
        self.duration = time.time() - self.start_time
        
        if self.log:
            monitor = get_performance_monitor()
            monitor.record_metric(self.operation, self.duration)
        
        return False  # Don't suppress exceptions


# Convenience functions
def record_performance(operation: str, duration: float, metadata: Optional[Dict[str, Any]] = None):
    """
    Record a performance metric
    
    Args:
        operation: Operation name
        duration: Duration in seconds
        metadata: Additional metadata
    """
    monitor = get_performance_monitor()
    monitor.record_metric(operation, duration, metadata)


def get_performance_metrics(operation: Optional[str] = None) -> Dict[str, Any]:
    """
    Get performance metrics
    
    Args:
        operation: Optional operation name to filter by
        
    Returns:
        Dictionary of metrics
    """
    monitor = get_performance_monitor()
    return monitor.get_metrics(operation)


def clear_performance_metrics(operation: Optional[str] = None):
    """
    Clear performance metrics
    
    Args:
        operation: Optional operation name to clear, or None for all
    """
    monitor = get_performance_monitor()
    monitor.clear_metrics(operation)
