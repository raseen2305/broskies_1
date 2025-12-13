"""
User-Friendly Error Messages
Maps technical errors to user-friendly messages with actionable guidance
"""

from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ErrorMessageMapper:
    """
    Maps technical errors to user-friendly messages
    
    Provides actionable guidance without exposing sensitive information
    """
    
    # Error code to user message mapping
    ERROR_MESSAGES: Dict[str, Tuple[str, str]] = {
        # Authentication errors
        'AUTH_TOKEN_MISSING': (
            "GitHub authentication required",
            "Please connect your GitHub account to continue. Click 'Connect GitHub' to authorize access."
        ),
        'AUTH_TOKEN_INVALID': (
            "GitHub authentication expired",
            "Your GitHub connection has expired. Please reconnect your GitHub account."
        ),
        'AUTH_TOKEN_REVOKED': (
            "GitHub access revoked",
            "GitHub access has been revoked. Please reconnect your GitHub account with the required permissions."
        ),
        
        # GitHub API errors
        'GITHUB_RATE_LIMIT': (
            "GitHub API rate limit exceeded",
            "We've reached GitHub's API limit. Please try again in a few minutes. Consider upgrading your GitHub plan for higher limits."
        ),
        'GITHUB_USER_NOT_FOUND': (
            "GitHub user not found",
            "The specified GitHub username doesn't exist. Please check the username and try again."
        ),
        'GITHUB_REPO_NOT_FOUND': (
            "Repository not found",
            "The specified repository doesn't exist or is private. Please check the repository name and your access permissions."
        ),
        'GITHUB_API_ERROR': (
            "GitHub service temporarily unavailable",
            "We're having trouble connecting to GitHub. Please try again in a few moments."
        ),
        
        # Scan errors
        'SCAN_NO_REPOSITORIES': (
            "No repositories found",
            "No public repositories were found for this account. Make sure you have public repositories to analyze."
        ),
        'SCAN_ALREADY_IN_PROGRESS': (
            "Scan already in progress",
            "A scan is already running for this account. Please wait for it to complete before starting a new one."
        ),
        'SCAN_FAILED': (
            "Scan failed",
            "The repository scan encountered an error. Please try again. If the problem persists, contact support."
        ),
        
        # Analysis errors
        'ANALYSIS_NO_SCAN': (
            "Scan required first",
            "Please complete a quick scan before running deep analysis. Click 'Quick Scan' to get started."
        ),
        'ANALYSIS_NO_REPOSITORIES': (
            "No repositories to analyze",
            "No flagship or significant repositories were found. Complete a quick scan first to categorize your repositories."
        ),
        'ANALYSIS_IN_PROGRESS': (
            "Analysis already in progress",
            "An analysis is already running. Please wait for it to complete before starting a new one."
        ),
        'ANALYSIS_FAILED': (
            "Analysis failed",
            "The code analysis encountered an error. Please try again. If the problem persists, contact support."
        ),
        
        # Database errors
        'DATABASE_CONNECTION_ERROR': (
            "Service temporarily unavailable",
            "We're experiencing technical difficulties. Please try again in a few moments."
        ),
        'DATABASE_QUERY_ERROR': (
            "Data retrieval error",
            "We couldn't retrieve your data. Please refresh the page and try again."
        ),
        
        # Validation errors
        'VALIDATION_INVALID_INPUT': (
            "Invalid input",
            "The provided information is invalid. Please check your input and try again."
        ),
        'VALIDATION_MISSING_FIELD': (
            "Required information missing",
            "Please provide all required information to continue."
        ),
        
        # Permission errors
        'PERMISSION_DENIED': (
            "Access denied",
            "You don't have permission to access this resource. Please check your account permissions."
        ),
        'PERMISSION_INSUFFICIENT': (
            "Insufficient permissions",
            "Your account doesn't have the required permissions. Please contact an administrator."
        ),
        
        # Resource errors
        'RESOURCE_NOT_FOUND': (
            "Resource not found",
            "The requested resource doesn't exist. It may have been deleted or moved."
        ),
        'RESOURCE_ALREADY_EXISTS': (
            "Resource already exists",
            "This resource already exists. Please use a different name or update the existing resource."
        ),
        
        # Generic errors
        'INTERNAL_ERROR': (
            "Something went wrong",
            "We encountered an unexpected error. Please try again. If the problem persists, contact support."
        ),
        'TIMEOUT_ERROR': (
            "Request timeout",
            "The operation took too long to complete. Please try again with a smaller dataset or contact support."
        ),
        'NETWORK_ERROR': (
            "Network error",
            "We couldn't connect to the service. Please check your internet connection and try again."
        )
    }
    
    @classmethod
    def get_user_message(
        cls,
        error_code: str,
        technical_details: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get user-friendly error message
        
        Args:
            error_code: Error code
            technical_details: Optional technical details (not shown to user)
            
        Returns:
            Dictionary with title, message, and error_code
        """
        if error_code in cls.ERROR_MESSAGES:
            title, message = cls.ERROR_MESSAGES[error_code]
        else:
            # Default fallback message
            title, message = cls.ERROR_MESSAGES['INTERNAL_ERROR']
            logger.warning(f"Unknown error code: {error_code}")
        
        # Log technical details for debugging (never expose to user)
        if technical_details:
            logger.error(f"Error {error_code}: {technical_details}")
        
        return {
            'title': title,
            'message': message,
            'error_code': error_code
        }
    
    @classmethod
    def map_exception_to_code(cls, exception: Exception) -> str:
        """
        Map exception to error code
        
        Args:
            exception: Exception instance
            
        Returns:
            Error code string
        """
        exception_str = str(exception).lower()
        exception_type = type(exception).__name__
        
        # Authentication errors
        if 'token' in exception_str and ('missing' in exception_str or 'not found' in exception_str):
            return 'AUTH_TOKEN_MISSING'
        if 'token' in exception_str and ('invalid' in exception_str or 'expired' in exception_str):
            return 'AUTH_TOKEN_INVALID'
        if 'revoked' in exception_str or 'unauthorized' in exception_str:
            return 'AUTH_TOKEN_REVOKED'
        
        # GitHub API errors
        if 'rate limit' in exception_str:
            return 'GITHUB_RATE_LIMIT'
        if 'user' in exception_str and 'not found' in exception_str:
            return 'GITHUB_USER_NOT_FOUND'
        if 'repository' in exception_str and 'not found' in exception_str:
            return 'GITHUB_REPO_NOT_FOUND'
        if 'github' in exception_str and ('api' in exception_str or 'graphql' in exception_str):
            return 'GITHUB_API_ERROR'
        
        # Scan errors
        if 'no repositories' in exception_str:
            return 'SCAN_NO_REPOSITORIES'
        if 'scan' in exception_str and 'in progress' in exception_str:
            return 'SCAN_ALREADY_IN_PROGRESS'
        if 'scan' in exception_str and 'failed' in exception_str:
            return 'SCAN_FAILED'
        
        # Analysis errors
        if 'scan required' in exception_str or 'complete quick scan' in exception_str:
            return 'ANALYSIS_NO_SCAN'
        if 'analysis' in exception_str and 'no repositories' in exception_str:
            return 'ANALYSIS_NO_REPOSITORIES'
        if 'analysis' in exception_str and 'in progress' in exception_str:
            return 'ANALYSIS_IN_PROGRESS'
        if 'analysis' in exception_str and 'failed' in exception_str:
            return 'ANALYSIS_FAILED'
        
        # Database errors
        if 'database' in exception_str and 'connection' in exception_str:
            return 'DATABASE_CONNECTION_ERROR'
        if 'database' in exception_str or 'query' in exception_str:
            return 'DATABASE_QUERY_ERROR'
        
        # Validation errors
        if exception_type == 'ValidationError' or 'validation' in exception_str:
            return 'VALIDATION_INVALID_INPUT'
        if 'required' in exception_str or 'missing' in exception_str:
            return 'VALIDATION_MISSING_FIELD'
        
        # Permission errors
        if 'permission' in exception_str or 'access denied' in exception_str:
            return 'PERMISSION_DENIED'
        if 'forbidden' in exception_str or exception_type == 'PermissionError':
            return 'PERMISSION_INSUFFICIENT'
        
        # Resource errors
        if 'not found' in exception_str and exception_type != 'FileNotFoundError':
            return 'RESOURCE_NOT_FOUND'
        if 'already exists' in exception_str:
            return 'RESOURCE_ALREADY_EXISTS'
        
        # Timeout and network errors
        if exception_type == 'TimeoutError' or 'timeout' in exception_str:
            return 'TIMEOUT_ERROR'
        if exception_type in ['ConnectionError', 'NetworkError'] or 'network' in exception_str:
            return 'NETWORK_ERROR'
        
        # Default to internal error
        return 'INTERNAL_ERROR'
    
    @classmethod
    def format_error_response(
        cls,
        exception: Exception,
        include_technical_details: bool = False
    ) -> Dict[str, str]:
        """
        Format exception as user-friendly error response
        
        Args:
            exception: Exception instance
            include_technical_details: Whether to include technical details (for debugging)
            
        Returns:
            Formatted error response
        """
        error_code = cls.map_exception_to_code(exception)
        response = cls.get_user_message(error_code, str(exception))
        
        # Only include technical details in development/debug mode
        if include_technical_details:
            response['technical_details'] = str(exception)
            response['exception_type'] = type(exception).__name__
        
        return response


# Convenience function for use in routers
def get_user_friendly_error(exception: Exception, debug: bool = False) -> Dict[str, str]:
    """
    Get user-friendly error message from exception
    
    Args:
        exception: Exception instance
        debug: Whether to include technical details
        
    Returns:
        User-friendly error response
    """
    return ErrorMessageMapper.format_error_response(exception, debug)
