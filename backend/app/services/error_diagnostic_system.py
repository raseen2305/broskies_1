"""
Comprehensive Error Handling and Diagnostic System
Provides detailed error tracking, retry logic, and diagnostic information for database operations
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from app.db_connection_multi import DatabaseType, multi_db_manager

logger = logging.getLogger(__name__)

class OperationType(Enum):
    """Types of database operations"""
    STORE = "store"
    FETCH = "fetch" 
    MIGRATE = "migrate"
    UPDATE = "update"
    DELETE = "delete"
    CONNECT = "connect"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class DatabaseError:
    """Represents a database operation error"""
    operation_type: OperationType
    database_name: str
    collection_name: Optional[str]
    error_message: str
    error_code: Optional[str]
    timestamp: datetime
    user_id: Optional[str]
    retry_count: int = 0
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        return {
            "operation_type": self.operation_type.value,
            "database_name": self.database_name,
            "collection_name": self.collection_name,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "retry_count": self.retry_count,
            "severity": self.severity.value,
            "context": self.context
        }

class RetryConfig:
    """Configuration for retry logic"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay

class ErrorDiagnosticSystem:
    """Comprehensive error handling and diagnostic system"""
    
    def __init__(self):
        self.error_history: List[DatabaseError] = []
        self.operation_stats: Dict[str, Dict[str, int]] = {}
        self.retry_configs: Dict[OperationType, RetryConfig] = {
            OperationType.STORE: RetryConfig(max_retries=3, base_delay=1.0),
            OperationType.FETCH: RetryConfig(max_retries=2, base_delay=0.5),
            OperationType.MIGRATE: RetryConfig(max_retries=5, base_delay=2.0, max_delay=120.0),
            OperationType.UPDATE: RetryConfig(max_retries=3, base_delay=1.0),
            OperationType.DELETE: RetryConfig(max_retries=2, base_delay=1.0),
            OperationType.CONNECT: RetryConfig(max_retries=3, base_delay=2.0, max_delay=30.0)
        }
    
    def log_error(
        self,
        operation_type: OperationType,
        database_name: str,
        error_message: str,
        collection_name: Optional[str] = None,
        error_code: Optional[str] = None,
        user_id: Optional[str] = None,
        retry_count: int = 0,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None
    ) -> DatabaseError:
        """Log a database error with detailed information"""
        
        db_error = DatabaseError(
            operation_type=operation_type,
            database_name=database_name,
            collection_name=collection_name,
            error_message=error_message,
            error_code=error_code,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            retry_count=retry_count,
            severity=severity,
            context=context or {}
        )
        
        # Add to error history (keep last 1000 errors)
        self.error_history.append(db_error)
        if len(self.error_history) > 1000:
            self.error_history.pop(0)
        
        # Update operation statistics
        op_key = f"{operation_type.value}_{database_name}"
        if op_key not in self.operation_stats:
            self.operation_stats[op_key] = {"success": 0, "failure": 0, "retry": 0}
        
        if retry_count > 0:
            self.operation_stats[op_key]["retry"] += 1
        else:
            self.operation_stats[op_key]["failure"] += 1
        
        # Log with appropriate level based on severity
        log_message = self._format_error_message(db_error)
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        return db_error
    
    def _format_error_message(self, db_error: DatabaseError) -> str:
        """Format error message for logging"""
        base_msg = f"error in {db_error.operation_type.value} to {db_error.database_name}"
        
        if db_error.collection_name:
            base_msg += f".{db_error.collection_name}"
        
        base_msg += f": {db_error.error_message}"
        
        if db_error.retry_count > 0:
            base_msg += f" (retry {db_error.retry_count})"
        
        if db_error.user_id:
            base_msg += f" [user: {db_error.user_id}]"
        
        return base_msg
    
    async def execute_with_retry(
        self,
        operation_type: OperationType,
        database_name: str,
        operation_func: Callable,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        custom_retry_config: Optional[RetryConfig] = None
    ) -> Any:
        """
        Execute database operation with retry logic and error tracking
        
        Args:
            operation_type: Type of operation being performed
            database_name: Name of the database
            operation_func: Async function to execute
            collection_name: Optional collection name
            user_id: Optional user ID for tracking
            context: Optional context information
            custom_retry_config: Optional custom retry configuration
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If operation fails after all retries
        """
        retry_config = custom_retry_config or self.retry_configs.get(
            operation_type, 
            RetryConfig()
        )
        
        last_exception = None
        
        for attempt in range(retry_config.max_retries + 1):
            try:
                # Execute the operation
                start_time = time.time()
                result = await operation_func()
                execution_time = time.time() - start_time
                
                # Log successful operation
                self._log_success(
                    operation_type, database_name, collection_name, 
                    user_id, execution_time, attempt
                )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Determine error severity
                severity = self._determine_error_severity(e, attempt, retry_config.max_retries)
                
                # Log the error
                error_context = {
                    **(context or {}),
                    "attempt": attempt + 1,
                    "max_attempts": retry_config.max_retries + 1,
                    "execution_time": time.time() - start_time if 'start_time' in locals() else 0
                }
                
                self.log_error(
                    operation_type=operation_type,
                    database_name=database_name,
                    collection_name=collection_name,
                    error_message=str(e),
                    error_code=getattr(e, 'code', None),
                    user_id=user_id,
                    retry_count=attempt,
                    severity=severity,
                    context=error_context
                )
                
                # If this was the last attempt, raise the exception
                if attempt >= retry_config.max_retries:
                    break
                
                # Calculate delay and wait before retry
                delay = retry_config.get_delay(attempt)
                logger.info(f"Retrying {operation_type.value} to {database_name} in {delay:.2f}s (attempt {attempt + 2}/{retry_config.max_retries + 1})")
                await asyncio.sleep(delay)
        
        # All retries exhausted, raise the last exception
        raise last_exception
    
    def _log_success(
        self,
        operation_type: OperationType,
        database_name: str,
        collection_name: Optional[str],
        user_id: Optional[str],
        execution_time: float,
        attempt: int
    ):
        """Log successful operation"""
        op_key = f"{operation_type.value}_{database_name}"
        if op_key not in self.operation_stats:
            self.operation_stats[op_key] = {"success": 0, "failure": 0, "retry": 0}
        
        self.operation_stats[op_key]["success"] += 1
        
        # Log success message
        msg = f"✅ {operation_type.value} to {database_name}"
        if collection_name:
            msg += f".{collection_name}"
        msg += f" completed in {execution_time:.3f}s"
        if attempt > 0:
            msg += f" (after {attempt} retries)"
        if user_id:
            msg += f" [user: {user_id}]"
        
        logger.debug(msg)
    
    def _determine_error_severity(self, exception: Exception, attempt: int, max_retries: int) -> ErrorSeverity:
        """Determine error severity based on exception type and retry status"""
        
        # Connection errors are high severity on final attempt
        connection_errors = ['timeout', 'connection', 'network', 'ssl', 'serverselection']
        if any(error_type in str(exception).lower() for error_type in connection_errors):
            return ErrorSeverity.HIGH if attempt >= max_retries else ErrorSeverity.MEDIUM
        
        # Authentication/authorization errors are critical
        auth_errors = ['authentication', 'authorization', 'permission', 'access denied']
        if any(error_type in str(exception).lower() for error_type in auth_errors):
            return ErrorSeverity.CRITICAL
        
        # Data validation errors are medium severity
        validation_errors = ['validation', 'invalid', 'malformed', 'schema']
        if any(error_type in str(exception).lower() for error_type in validation_errors):
            return ErrorSeverity.MEDIUM
        
        # Final attempt failures are high severity
        if attempt >= max_retries:
            return ErrorSeverity.HIGH
        
        return ErrorSeverity.LOW
    
    @asynccontextmanager
    async def operation_context(
        self,
        operation_type: OperationType,
        database_name: str,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for database operations with automatic error handling
        
        Usage:
            async with error_system.operation_context(
                OperationType.STORE, "raseen_main_user", "scan_cache", user_id
            ) as ctx:
                result = await database.collection.insert_one(data)
                ctx.set_result(result)
        """
        
        class OperationContext:
            def __init__(self):
                self.result = None
                self.start_time = time.time()
            
            def set_result(self, result):
                self.result = result
        
        ctx = OperationContext()
        
        try:
            yield ctx
            
            # Log successful operation
            execution_time = time.time() - ctx.start_time
            self._log_success(
                operation_type, database_name, collection_name,
                user_id, execution_time, 0
            )
            
        except Exception as e:
            # Log the error
            execution_time = time.time() - ctx.start_time
            error_context = {
                **(context or {}),
                "execution_time": execution_time
            }
            
            self.log_error(
                operation_type=operation_type,
                database_name=database_name,
                collection_name=collection_name,
                error_message=str(e),
                error_code=getattr(e, 'code', None),
                user_id=user_id,
                severity=self._determine_error_severity(e, 0, 0),
                context=error_context
            )
            
            raise
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the specified time period"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [
            error for error in self.error_history 
            if error.timestamp >= cutoff_time
        ]
        
        # Group errors by database and operation type
        error_breakdown = {}
        severity_counts = {severity.value: 0 for severity in ErrorSeverity}
        
        for error in recent_errors:
            key = f"{error.database_name}_{error.operation_type.value}"
            if key not in error_breakdown:
                error_breakdown[key] = 0
            error_breakdown[key] += 1
            severity_counts[error.severity.value] += 1
        
        return {
            "time_period_hours": hours,
            "total_errors": len(recent_errors),
            "error_breakdown": error_breakdown,
            "severity_counts": severity_counts,
            "operation_stats": self.operation_stats.copy(),
            "most_recent_errors": [
                error.to_dict() for error in recent_errors[-10:]
            ]
        }
    
    def get_database_health_summary(self) -> Dict[str, Any]:
        """Get overall database health summary"""
        
        health_summary = {}
        
        for op_key, stats in self.operation_stats.items():
            total_ops = stats["success"] + stats["failure"]
            if total_ops > 0:
                success_rate = (stats["success"] / total_ops) * 100
                health_summary[op_key] = {
                    "success_rate": round(success_rate, 2),
                    "total_operations": total_ops,
                    "failures": stats["failure"],
                    "retries": stats["retry"]
                }
        
        # Recent error rate (last hour)
        recent_stats = self.get_error_statistics(hours=1)
        
        return {
            "operation_health": health_summary,
            "recent_error_count": recent_stats["total_errors"],
            "critical_errors_last_hour": recent_stats["severity_counts"]["critical"],
            "timestamp": datetime.utcnow().isoformat()
        }

# Global instance
error_diagnostic_system = ErrorDiagnosticSystem()

# Convenience functions
async def execute_db_operation_with_retry(
    operation_type: OperationType,
    database_name: str,
    operation_func: Callable,
    collection_name: Optional[str] = None,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """Convenience function to execute database operation with retry"""
    return await error_diagnostic_system.execute_with_retry(
        operation_type, database_name, operation_func,
        collection_name, user_id, context
    )

def log_database_error(
    operation_type: OperationType,
    database_name: str,
    error_message: str,
    collection_name: Optional[str] = None,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> DatabaseError:
    """Convenience function to log database error"""
    return error_diagnostic_system.log_error(
        operation_type, database_name, error_message,
        collection_name, None, user_id, 0, ErrorSeverity.MEDIUM, context
    )

def get_database_health() -> Dict[str, Any]:
    """Convenience function to get database health summary"""
    return error_diagnostic_system.get_database_health_summary()