"""
Comprehensive logging configuration for the GitHub Repository Evaluator
"""

import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Base log data
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from the record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info', 'message'
            ]:
                extra_fields[key] = value
        
        if extra_fields:
            log_data["extra"] = extra_fields
        
        return json.dumps(log_data, default=str, ensure_ascii=False)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']
        
        # Create colored level name
        colored_level = f"{level_color}{record.levelname}{reset_color}"
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format message
        message = record.getMessage()
        
        # Add extra context if available
        extra_info = ""
        if hasattr(record, 'request_path'):
            extra_info += f" [{record.request_path}]"
        if hasattr(record, 'user_id'):
            extra_info += f" [user:{record.user_id}]"
        if hasattr(record, 'error_code'):
            extra_info += f" [{record.error_code}]"
        
        # Format final message
        formatted_message = f"{timestamp} | {colored_level:8} | {record.name:20} | {message}{extra_info}"
        
        # Add exception info if present
        if record.exc_info:
            formatted_message += f"\n{self.formatException(record.exc_info)}"
        
        return formatted_message

def setup_logging(
    log_level: str = "INFO",
    log_file: str = None,
    enable_json_logging: bool = False,
    enable_console_logging: bool = True
) -> None:
    """Setup comprehensive logging configuration"""
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Base logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "colored": {
                "()": ColoredFormatter,
            },
            "standard": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {},
        "loggers": {
            # Application loggers
            "app": {
                "level": log_level,
                "handlers": [],
                "propagate": True
            },
            "app.core": {
                "level": log_level,
                "handlers": [],
                "propagate": True
            },
            "app.routers": {
                "level": log_level,
                "handlers": [],
                "propagate": True
            },
            "app.services": {
                "level": log_level,
                "handlers": [],
                "propagate": True
            },
            "app.tasks": {
                "level": log_level,
                "handlers": [],
                "propagate": True
            },
            # Third-party loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": [],
                "propagate": True
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": [],
                "propagate": True
            },
            "uvicorn.error": {
                "level": "ERROR",  # Suppress WebSocket warnings
                "handlers": [],
                "propagate": True
            },
            "fastapi": {
                "level": "INFO",
                "handlers": [],
                "propagate": True
            },
            "httpx": {
                "level": "WARNING",
                "handlers": [],
                "propagate": True
            },
            "celery": {
                "level": "INFO",
                "handlers": [],
                "propagate": True
            }
        },
        "root": {
            "level": log_level,
            "handlers": []
        }
    }
    
    # Console handler
    if enable_console_logging:
        config["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "colored",
            "level": log_level
        }
        
        # Add console handler ONLY to root logger (centralized logging)
        # All other loggers propagate to root
        config["root"]["handlers"].append("console")
    
    # File handler
    if log_file:
        formatter = "json" if enable_json_logging else "standard"
        
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": formatter,
            "level": log_level,
            "encoding": "utf-8"
        }
        
        # Add file handler ONLY to root logger
        config["root"]["handlers"].append("file")
    
    # Error file handler (separate file for errors)
    if log_file:
        error_file = str(Path(log_file).with_suffix('.error.log'))
        formatter = "json" if enable_json_logging else "standard"
        
        config["handlers"]["error_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": error_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": formatter,
            "level": "ERROR",
            "encoding": "utf-8"
        }
        
        # Add error file handler ONLY to root logger
        config["root"]["handlers"].append("error_file")
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log configuration success
    logger = logging.getLogger("app.core.logging")
    logger.info(
        "Logging configuration applied",
        extra={
            "log_level": log_level,
            "log_file": log_file,
            "json_logging": enable_json_logging,
            "console_logging": enable_console_logging
        }
    )

class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def log_info(self, message: str, **kwargs):
        """Log info message with extra context"""
        self.logger.info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with extra context"""
        self.logger.warning(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message with extra context"""
        self.logger.error(message, extra=kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with extra context"""
        self.logger.debug(message, extra=kwargs)

def get_logger(name: str) -> logging.Logger:
    """Get logger with specified name"""
    return logging.getLogger(name)

def log_request(request_data: Dict[str, Any]) -> None:
    """Log HTTP request with structured data"""
    logger = get_logger("app.requests")
    logger.info("HTTP Request", extra=request_data)

def log_response(response_data: Dict[str, Any]) -> None:
    """Log HTTP response with structured data"""
    logger = get_logger("app.responses")
    logger.info("HTTP Response", extra=response_data)

def log_security_event(event_type: str, details: Dict[str, Any]) -> None:
    """Log security event with structured data"""
    logger = get_logger("app.security")
    logger.warning(
        f"Security Event: {event_type}",
        extra={
            "event_type": event_type,
            "security_details": details,
            "severity": "security"
        }
    )

def log_performance_metric(metric_name: str, value: float, unit: str = "ms", **context) -> None:
    """Log performance metric"""
    logger = get_logger("app.performance")
    logger.info(
        f"Performance Metric: {metric_name}",
        extra={
            "metric_name": metric_name,
            "metric_value": value,
            "metric_unit": unit,
            "metric_context": context
        }
    )

def log_business_event(event_type: str, details: Dict[str, Any]) -> None:
    """Log business event (user actions, system events)"""
    logger = get_logger("app.business")
    logger.info(
        f"Business Event: {event_type}",
        extra={
            "event_type": event_type,
            "business_details": details
        }
    )

# Context managers for logging

class LogExecutionTime:
    """Context manager to log execution time of operations"""
    
    def __init__(self, operation_name: str, logger_name: str = "app.performance"):
        self.operation_name = operation_name
        self.logger = get_logger(logger_name)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds() * 1000  # milliseconds
        
        if exc_type is None:
            self.logger.info(
                f"Operation completed: {self.operation_name}",
                extra={
                    "operation": self.operation_name,
                    "duration_ms": duration,
                    "status": "success"
                }
            )
        else:
            self.logger.error(
                f"Operation failed: {self.operation_name}",
                extra={
                    "operation": self.operation_name,
                    "duration_ms": duration,
                    "status": "failed",
                    "error_type": exc_type.__name__,
                    "error_message": str(exc_val)
                }
            )

class LogUserAction:
    """Context manager to log user actions"""
    
    def __init__(self, action: str, user_id: str = None, **context):
        self.action = action
        self.user_id = user_id
        self.context = context
        self.logger = get_logger("app.user_actions")
    
    def __enter__(self):
        self.logger.info(
            f"User action started: {self.action}",
            extra={
                "action": self.action,
                "user_id": self.user_id,
                "action_context": self.context,
                "status": "started"
            }
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.info(
                f"User action completed: {self.action}",
                extra={
                    "action": self.action,
                    "user_id": self.user_id,
                    "action_context": self.context,
                    "status": "completed"
                }
            )
        else:
            self.logger.error(
                f"User action failed: {self.action}",
                extra={
                    "action": self.action,
                    "user_id": self.user_id,
                    "action_context": self.context,
                    "status": "failed",
                    "error_type": exc_type.__name__,
                    "error_message": str(exc_val)
                }
            )