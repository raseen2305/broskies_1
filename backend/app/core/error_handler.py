"""
Comprehensive error handling system for the GitHub Repository Evaluator API
"""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Union
from enum import Enum

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class ErrorCode(str, Enum):
    """Standardized error codes for the application"""
    
    # Authentication & Authorization
    AUTHENTICATION_FAILED = "AUTH_001"
    INVALID_TOKEN = "AUTH_002"
    TOKEN_EXPIRED = "AUTH_003"
    INSUFFICIENT_PERMISSIONS = "AUTH_004"
    GITHUB_AUTH_FAILED = "AUTH_005"
    GOOGLE_AUTH_FAILED = "AUTH_006"
    
    # Validation Errors
    VALIDATION_ERROR = "VAL_001"
    INVALID_INPUT = "VAL_002"
    MISSING_REQUIRED_FIELD = "VAL_003"
    INVALID_FORMAT = "VAL_004"
    INVALID_GITHUB_URL = "VAL_005"
    INVALID_EMAIL = "VAL_006"
    
    # GitHub Integration
    GITHUB_API_ERROR = "GH_001"
    GITHUB_RATE_LIMIT = "GH_002"
    GITHUB_REPO_NOT_FOUND = "GH_003"
    GITHUB_USER_NOT_FOUND = "GH_004"
    GITHUB_ACCESS_DENIED = "GH_005"
    
    # Database Errors
    DATABASE_ERROR = "DB_001"
    DATABASE_CONNECTION_ERROR = "DB_002"
    RECORD_NOT_FOUND = "DB_003"
    DUPLICATE_RECORD = "DB_004"
    DATABASE_TIMEOUT = "DB_005"
    
    # Scanning & Evaluation
    SCAN_ERROR = "SCAN_001"
    SCAN_IN_PROGRESS = "SCAN_002"
    SCAN_FAILED = "SCAN_003"
    EVALUATION_ERROR = "EVAL_001"
    EVALUATION_TIMEOUT = "EVAL_002"
    
    # Rate Limiting & Security
    RATE_LIMIT_EXCEEDED = "SEC_001"
    REQUEST_TOO_LARGE = "SEC_002"
    MALICIOUS_INPUT_DETECTED = "SEC_003"
    IP_BLOCKED = "SEC_004"
    
    # System Errors
    INTERNAL_SERVER_ERROR = "SYS_001"
    SERVICE_UNAVAILABLE = "SYS_002"
    EXTERNAL_SERVICE_ERROR = "SYS_003"
    CACHE_ERROR = "SYS_004"
    CONFIGURATION_ERROR = "SYS_005"
    
    # User Experience
    RESOURCE_NOT_FOUND = "UX_001"
    OPERATION_NOT_ALLOWED = "UX_002"
    FEATURE_NOT_AVAILABLE = "UX_003"
    MAINTENANCE_MODE = "UX_004"

class ErrorSeverity(str, Enum):
    """Error severity levels for logging and monitoring"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ApplicationError(Exception):
    """Base application error with structured information"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[list] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.severity = severity
        self.user_message = user_message or self._generate_user_message()
        self.recovery_suggestions = recovery_suggestions or []
        self.timestamp = datetime.utcnow()
        
        super().__init__(self.message)
    
    def _generate_user_message(self) -> str:
        """Generate user-friendly error message based on error code"""
        user_messages = {
            ErrorCode.AUTHENTICATION_FAILED: "Authentication failed. Please check your credentials and try again.",
            ErrorCode.INVALID_TOKEN: "Your session has expired. Please log in again.",
            ErrorCode.TOKEN_EXPIRED: "Your session has expired. Please log in again.",
            ErrorCode.INSUFFICIENT_PERMISSIONS: "You don't have permission to access this resource.",
            ErrorCode.GITHUB_AUTH_FAILED: "GitHub authentication failed. Please try logging in again.",
            ErrorCode.GOOGLE_AUTH_FAILED: "Google authentication failed. Please try logging in again.",
            
            ErrorCode.VALIDATION_ERROR: "The information you provided is invalid. Please check and try again.",
            ErrorCode.INVALID_INPUT: "Invalid input provided. Please check your data and try again.",
            ErrorCode.MISSING_REQUIRED_FIELD: "Required information is missing. Please fill in all required fields.",
            ErrorCode.INVALID_FORMAT: "The format of the information provided is incorrect.",
            ErrorCode.INVALID_GITHUB_URL: "The GitHub URL you provided is invalid. Please check the URL and try again.",
            ErrorCode.INVALID_EMAIL: "The email address format is invalid. Please provide a valid email address.",
            
            ErrorCode.GITHUB_API_ERROR: "Unable to connect to GitHub. Please try again later.",
            ErrorCode.GITHUB_RATE_LIMIT: "GitHub rate limit exceeded. Please wait a few minutes and try again.",
            ErrorCode.GITHUB_REPO_NOT_FOUND: "The GitHub repository could not be found. Please check the URL.",
            ErrorCode.GITHUB_USER_NOT_FOUND: "The GitHub user could not be found. Please check the username.",
            ErrorCode.GITHUB_ACCESS_DENIED: "Access to the GitHub repository is denied. Please check permissions.",
            
            ErrorCode.DATABASE_ERROR: "A database error occurred. Please try again later.",
            ErrorCode.DATABASE_CONNECTION_ERROR: "Unable to connect to the database. Please try again later.",
            ErrorCode.RECORD_NOT_FOUND: "The requested information could not be found.",
            ErrorCode.DUPLICATE_RECORD: "This information already exists in the system.",
            ErrorCode.DATABASE_TIMEOUT: "The operation took too long to complete. Please try again.",
            
            ErrorCode.SCAN_ERROR: "An error occurred during repository scanning. Please try again.",
            ErrorCode.SCAN_IN_PROGRESS: "A scan is already in progress. Please wait for it to complete.",
            ErrorCode.SCAN_FAILED: "Repository scanning failed. Please check the repository and try again.",
            ErrorCode.EVALUATION_ERROR: "An error occurred during repository evaluation. Please try again.",
            ErrorCode.EVALUATION_TIMEOUT: "Repository evaluation took too long. Please try again later.",
            
            ErrorCode.RATE_LIMIT_EXCEEDED: "Too many requests. Please wait a moment and try again.",
            ErrorCode.REQUEST_TOO_LARGE: "The request is too large. Please reduce the size and try again.",
            ErrorCode.MALICIOUS_INPUT_DETECTED: "Invalid input detected. Please check your data.",
            ErrorCode.IP_BLOCKED: "Your IP address has been temporarily blocked due to suspicious activity.",
            
            ErrorCode.INTERNAL_SERVER_ERROR: "An internal server error occurred. Please try again later.",
            ErrorCode.SERVICE_UNAVAILABLE: "The service is temporarily unavailable. Please try again later.",
            ErrorCode.EXTERNAL_SERVICE_ERROR: "An external service is unavailable. Please try again later.",
            ErrorCode.CACHE_ERROR: "A caching error occurred. Please try again.",
            ErrorCode.CONFIGURATION_ERROR: "A configuration error occurred. Please contact support.",
            
            ErrorCode.RESOURCE_NOT_FOUND: "The requested resource could not be found.",
            ErrorCode.OPERATION_NOT_ALLOWED: "This operation is not allowed.",
            ErrorCode.FEATURE_NOT_AVAILABLE: "This feature is not currently available.",
            ErrorCode.MAINTENANCE_MODE: "The system is currently under maintenance. Please try again later."
        }
        
        return user_messages.get(self.error_code, "An unexpected error occurred. Please try again.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "user_message": self.user_message,
                "status_code": self.status_code,
                "severity": self.severity,
                "details": self.details,
                "recovery_suggestions": self.recovery_suggestions,
                "timestamp": self.timestamp.isoformat(),
                "request_id": getattr(self, 'request_id', None)
            }
        }

# Specific error classes for different domains

class AuthenticationError(ApplicationError):
    """Authentication related errors"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.AUTHENTICATION_FAILED, **kwargs):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )

class ValidationError(ApplicationError):
    """Validation related errors"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.VALIDATION_ERROR, **kwargs):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            severity=ErrorSeverity.LOW,
            **kwargs
        )

class GitHubError(ApplicationError):
    """GitHub API related errors"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.GITHUB_API_ERROR, **kwargs):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_502_BAD_GATEWAY,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )

class DatabaseError(ApplicationError):
    """Database related errors"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.DATABASE_ERROR, **kwargs):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )

class ScanError(ApplicationError):
    """Repository scanning related errors"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.SCAN_ERROR, **kwargs):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )

class SecurityError(ApplicationError):
    """Security related errors"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.MALICIOUS_INPUT_DETECTED, **kwargs):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_400_BAD_REQUEST,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )

class RateLimitError(ApplicationError):
    """Rate limiting related errors"""
    def __init__(self, message: str, retry_after: int = 60, **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            severity=ErrorSeverity.LOW,
            details={"retry_after": retry_after},
            recovery_suggestions=[f"Please wait {retry_after} seconds before trying again"],
            **kwargs
        )

# Error handler functions

async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    """Handle custom application errors"""
    
    # Add request ID for tracking
    request_id = getattr(request.state, 'request_id', None)
    exc.request_id = request_id
    
    # Log the error
    log_error(exc, request)
    
    # Return structured error response
    response_data = exc.to_dict()
    
    # Add retry-after header for rate limit errors
    headers = {}
    if exc.error_code == ErrorCode.RATE_LIMIT_EXCEEDED:
        retry_after = exc.details.get('retry_after', 60)
        headers['Retry-After'] = str(retry_after)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=headers
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    
    # Convert to ApplicationError for consistent handling
    error_code_map = {
        400: ErrorCode.INVALID_INPUT,
        401: ErrorCode.AUTHENTICATION_FAILED,
        403: ErrorCode.INSUFFICIENT_PERMISSIONS,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        405: ErrorCode.OPERATION_NOT_ALLOWED,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_SERVER_ERROR,
        502: ErrorCode.EXTERNAL_SERVICE_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE
    }
    
    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)
    
    app_error = ApplicationError(
        message=str(exc.detail),
        error_code=error_code,
        status_code=exc.status_code,
        details=getattr(exc, 'details', None)
    )
    
    return await application_error_handler(request, app_error)

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    
    # Extract validation details
    validation_details = []
    for error in exc.errors():
        validation_details.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    app_error = ValidationError(
        message="Request validation failed",
        error_code=ErrorCode.VALIDATION_ERROR,
        details={"validation_errors": validation_details},
        recovery_suggestions=[
            "Check the format of your request data",
            "Ensure all required fields are provided",
            "Verify data types match the expected format"
        ]
    )
    
    return await application_error_handler(request, app_error)

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    
    # Log the full exception with traceback
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "request_path": request.url.path,
            "request_method": request.method,
            "client_ip": request.client.host,
            "traceback": traceback.format_exc()
        }
    )
    
    # Create generic error response (don't expose internal details)
    app_error = ApplicationError(
        message="An unexpected error occurred",
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        severity=ErrorSeverity.CRITICAL,
        recovery_suggestions=[
            "Please try again later",
            "If the problem persists, contact support"
        ]
    )
    
    return await application_error_handler(request, app_error)

def log_error(error: ApplicationError, request: Request) -> None:
    """Log error with appropriate level and context"""
    
    log_data = {
        "error_code": error.error_code,
        "error_message": error.message,
        "user_message": error.user_message,
        "status_code": error.status_code,
        "severity": error.severity,
        "request_path": request.url.path,
        "request_method": request.method,
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "request_id": getattr(error, 'request_id', None),
        "details": error.details,
        "timestamp": error.timestamp.isoformat()
    }
    
    # Log with appropriate level based on severity
    if error.severity == ErrorSeverity.CRITICAL:
        logger.critical(f"Critical error: {error.error_code}", extra=log_data)
    elif error.severity == ErrorSeverity.HIGH:
        logger.error(f"High severity error: {error.error_code}", extra=log_data)
    elif error.severity == ErrorSeverity.MEDIUM:
        logger.warning(f"Medium severity error: {error.error_code}", extra=log_data)
    else:
        logger.info(f"Low severity error: {error.error_code}", extra=log_data)

# Utility functions for common error scenarios

def raise_authentication_error(message: str = "Authentication failed", **kwargs):
    """Raise authentication error with standard message"""
    raise AuthenticationError(message, **kwargs)

def raise_validation_error(field: str, message: str, **kwargs):
    """Raise validation error for specific field"""
    raise ValidationError(
        message=f"Validation failed for field '{field}': {message}",
        details={"field": field, "validation_message": message},
        **kwargs
    )

def raise_github_error(message: str, github_status: int = None, **kwargs):
    """Raise GitHub API error with context"""
    error_code = ErrorCode.GITHUB_API_ERROR
    if github_status == 404:
        error_code = ErrorCode.GITHUB_REPO_NOT_FOUND
    elif github_status == 403:
        error_code = ErrorCode.GITHUB_RATE_LIMIT
    
    raise GitHubError(
        message=message,
        error_code=error_code,
        details={"github_status": github_status},
        **kwargs
    )

def raise_database_error(message: str, operation: str = None, **kwargs):
    """Raise database error with operation context"""
    raise DatabaseError(
        message=message,
        details={"operation": operation},
        **kwargs
    )

def raise_scan_error(message: str, scan_id: str = None, **kwargs):
    """Raise scanning error with scan context"""
    raise ScanError(
        message=message,
        details={"scan_id": scan_id},
        **kwargs
    )