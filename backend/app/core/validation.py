"""
Comprehensive input validation utilities for the GitHub Repository Evaluator API
"""

import re
import html
import bleach
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from pydantic import BaseModel, validator, Field
from fastapi import HTTPException, status
from datetime import datetime

logger = logging.getLogger(__name__)

class ValidationError(HTTPException):
    """Custom validation error with detailed information"""
    
    def __init__(self, field: str, message: str, value: Any = None):
        detail = {
            "error_type": "validation_error",
            "field": field,
            "message": message,
            "invalid_value": str(value) if value is not None else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

class InputSanitizer:
    """Utility class for sanitizing user inputs"""
    
    # Allowed HTML tags for rich text fields (if any)
    ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    ALLOWED_ATTRIBUTES = {}
    
    # Common patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    GITHUB_USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$')
    # Enhanced GitHub URL patterns supporting multiple formats
    GITHUB_URL_PATTERNS = [
        re.compile(r'^https://github\.com/([a-zA-Z0-9_-]+)/?$'),                    # Basic user profile
        re.compile(r'^https://github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)/?$'), # User with repo
        re.compile(r'^https://github\.com/([a-zA-Z0-9_-]+)\?tab=repositories$'),   # Repositories tab
        re.compile(r'^https://github\.com/([a-zA-Z0-9_-]+)\?tab=overview$'),       # Overview tab
        re.compile(r'^https://github\.com/([a-zA-Z0-9_-]+)\?tab=projects$'),       # Projects tab
        re.compile(r'^https://github\.com/([a-zA-Z0-9_-]+)\?tab=packages$'),       # Packages tab
        re.compile(r'^https://github\.com/([a-zA-Z0-9_-]+)\?tab=stars$'),          # Stars tab
        re.compile(r'^https://github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)\?.*$') # Repository with params
    ]
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000, allow_html: bool = False) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            raise ValidationError("input", "Value must be a string", value)
        
        # Remove null bytes and control characters
        value = value.replace('\x00', '').strip()
        
        # Check length
        if len(value) > max_length:
            raise ValidationError("input", f"String too long (max {max_length} characters)", len(value))
        
        if allow_html:
            # Clean HTML but allow safe tags
            value = bleach.clean(value, tags=InputSanitizer.ALLOWED_TAGS, 
                               attributes=InputSanitizer.ALLOWED_ATTRIBUTES, strip=True)
        else:
            # Escape HTML entities
            value = html.escape(value)
        
        return value
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email address"""
        email = InputSanitizer.sanitize_string(email, max_length=254).lower()
        
        if not InputSanitizer.EMAIL_PATTERN.match(email):
            raise ValidationError("email", "Invalid email format", email)
        
        return email
    
    @staticmethod
    def validate_github_username(username: str) -> str:
        """Validate GitHub username"""
        username = InputSanitizer.sanitize_string(username, max_length=39)
        
        if not InputSanitizer.GITHUB_USERNAME_PATTERN.match(username):
            raise ValidationError("github_username", "Invalid GitHub username format", username)
        
        return username
    
    @staticmethod
    def validate_github_url(url: str) -> Dict[str, Optional[str]]:
        """Validate and parse GitHub URL with enhanced pattern support"""
        url = InputSanitizer.sanitize_string(url, max_length=500)
        
        # Parse URL
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError("github_url", "URL must use HTTP or HTTPS protocol", url)
        
        if parsed.netloc != 'github.com':
            raise ValidationError("github_url", "URL must be from github.com", url)
        
        # Try each pattern until one matches
        username = None
        repository = None
        
        for pattern in InputSanitizer.GITHUB_URL_PATTERNS:
            match = pattern.match(url)
            if match:
                groups = match.groups()
                username = groups[0] if len(groups) > 0 else None
                repository = groups[1] if len(groups) > 1 else None
                break
        
        if not username:
            raise ValidationError("github_url", "Invalid GitHub URL format. Supported formats: https://github.com/username, https://github.com/username/repo, https://github.com/username?tab=repositories", url)
        
        return {
            "url": url,
            "username": username,
            "repository": repository
        }
    
    @staticmethod
    def validate_integer(value: Any, min_value: int = None, max_value: int = None, field_name: str = "integer") -> int:
        """Validate integer input"""
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(field_name, "Value must be an integer", value)
        
        if min_value is not None and value < min_value:
            raise ValidationError(field_name, f"Value must be at least {min_value}", value)
        
        if max_value is not None and value > max_value:
            raise ValidationError(field_name, f"Value must be at most {max_value}", value)
        
        return value
    
    @staticmethod
    def validate_float(value: Any, min_value: float = None, max_value: float = None, field_name: str = "float") -> float:
        """Validate float input"""
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(field_name, "Value must be a number", value)
        
        if min_value is not None and value < min_value:
            raise ValidationError(field_name, f"Value must be at least {min_value}", value)
        
        if max_value is not None and value > max_value:
            raise ValidationError(field_name, f"Value must be at most {max_value}", value)
        
        return value
    
    @staticmethod
    def validate_choice(value: str, choices: List[str], field_name: str = "choice") -> str:
        """Validate choice from predefined options"""
        value = InputSanitizer.sanitize_string(value, max_length=100)
        
        if value not in choices:
            raise ValidationError(field_name, f"Value must be one of: {', '.join(choices)}", value)
        
        return value

# Pydantic models for request validation

class GitHubUrlRequest(BaseModel):
    """Validation model for GitHub URL requests"""
    url: str = Field(..., min_length=1, max_length=500, description="GitHub repository or user URL")
    
    @validator('url')
    def validate_github_url(cls, v):
        return InputSanitizer.validate_github_url(v)["url"]

class ScanRequest(BaseModel):
    """Validation model for repository scan requests"""
    github_url: str = Field(..., min_length=1, max_length=500, description="GitHub URL to scan")
    scan_type: str = Field(..., description="Type of scan: 'self' or 'other'")
    
    @validator('github_url')
    def validate_github_url(cls, v):
        return InputSanitizer.validate_github_url(v)["url"]
    
    @validator('scan_type')
    def validate_scan_type(cls, v):
        return InputSanitizer.validate_choice(v, ['self', 'other'], 'scan_type')

class UserProfileUpdate(BaseModel):
    """Validation model for user profile updates"""
    github_username: Optional[str] = Field(None, min_length=1, max_length=39)
    email: Optional[str] = Field(None, min_length=1, max_length=254)
    profile_visibility: Optional[str] = Field(None, description="Profile visibility: 'public' or 'private'")
    
    @validator('github_username')
    def validate_github_username(cls, v):
        if v is not None:
            return InputSanitizer.validate_github_username(v)
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v is not None:
            return InputSanitizer.validate_email(v)
        return v
    
    @validator('profile_visibility')
    def validate_visibility(cls, v):
        if v is not None:
            return InputSanitizer.validate_choice(v, ['public', 'private'], 'profile_visibility')
        return v

class HRRegistrationRequest(BaseModel):
    """Validation model for HR registration"""
    email: str = Field(..., min_length=1, max_length=254, description="HR professional email")
    company: str = Field(..., min_length=1, max_length=200, description="Company name")
    role: str = Field(..., min_length=1, max_length=100, description="Job role/title")
    
    @validator('email')
    def validate_email(cls, v):
        return InputSanitizer.validate_email(v)
    
    @validator('company')
    def validate_company(cls, v):
        return InputSanitizer.sanitize_string(v, max_length=200)
    
    @validator('role')
    def validate_role(cls, v):
        return InputSanitizer.sanitize_string(v, max_length=100)

class PaginationParams(BaseModel):
    """Validation model for pagination parameters"""
    page: int = Field(1, ge=1, le=1000, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field("created_at", max_length=50, description="Sort field")
    order: Optional[str] = Field("desc", description="Sort order: 'asc' or 'desc'")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        if v is not None:
            allowed_fields = ['created_at', 'updated_at', 'name', 'stars', 'forks', 'score']
            return InputSanitizer.validate_choice(v, allowed_fields, 'sort_by')
        return v
    
    @validator('order')
    def validate_order(cls, v):
        if v is not None:
            return InputSanitizer.validate_choice(v, ['asc', 'desc'], 'order')
        return v

class SearchParams(BaseModel):
    """Validation model for search parameters"""
    query: Optional[str] = Field(None, min_length=1, max_length=200, description="Search query")
    language: Optional[str] = Field(None, max_length=50, description="Programming language filter")
    min_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum score filter")
    max_score: Optional[float] = Field(None, ge=0, le=100, description="Maximum score filter")
    
    @validator('query')
    def validate_query(cls, v):
        if v is not None:
            return InputSanitizer.sanitize_string(v, max_length=200)
        return v
    
    @validator('language')
    def validate_language(cls, v):
        if v is not None:
            return InputSanitizer.sanitize_string(v, max_length=50)
        return v

class CommentRequest(BaseModel):
    """Validation model for comments or feedback"""
    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5)")
    
    @validator('content')
    def validate_content(cls, v):
        return InputSanitizer.sanitize_string(v, max_length=2000, allow_html=False)

# SQL Injection prevention patterns
class SQLInjectionDetector:
    """Utility to detect potential SQL injection attempts"""
    
    SUSPICIOUS_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"].*['\"])",
        r"(;|\|\||&&)",
        r"(\bSCRIPT\b|\bJAVASCRIPT\b)",
        r"(<script|</script>|javascript:|vbscript:)",
    ]
    
    @staticmethod
    def detect_injection(value: str) -> bool:
        """Detect potential injection attempts"""
        if not isinstance(value, str):
            return False
        
        value_upper = value.upper()
        
        for pattern in SQLInjectionDetector.SUSPICIOUS_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                logger.warning(f"Potential injection attempt detected: {value[:100]}")
                return True
        
        return False
    
    @staticmethod
    def validate_safe_input(value: str, field_name: str = "input") -> str:
        """Validate input is safe from injection"""
        if SQLInjectionDetector.detect_injection(value):
            raise ValidationError(field_name, "Input contains potentially malicious content", value)
        
        return value

# XSS prevention
class XSSProtection:
    """Utility for XSS prevention"""
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    @staticmethod
    def detect_xss(value: str) -> bool:
        """Detect potential XSS attempts"""
        if not isinstance(value, str):
            return False
        
        for pattern in XSSProtection.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS attempt detected: {value[:100]}")
                return True
        
        return False
    
    @staticmethod
    def sanitize_for_xss(value: str, field_name: str = "input") -> str:
        """Sanitize input to prevent XSS"""
        if XSSProtection.detect_xss(value):
            raise ValidationError(field_name, "Input contains potentially malicious content", value)
        
        # Additional sanitization
        value = html.escape(value)
        return value

# File upload validation
class FileValidator:
    """Utility for file upload validation"""
    
    ALLOWED_EXTENSIONS = {'.txt', '.md', '.json', '.csv', '.log'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_file_extension(filename: str) -> str:
        """Validate file extension"""
        if not filename:
            raise ValidationError("filename", "Filename is required")
        
        filename = InputSanitizer.sanitize_string(filename, max_length=255)
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValidationError("filename", "Invalid filename", filename)
        
        # Check extension
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{extension}' not in FileValidator.ALLOWED_EXTENSIONS:
            raise ValidationError("filename", f"File type not allowed. Allowed: {', '.join(FileValidator.ALLOWED_EXTENSIONS)}")
        
        return filename
    
    @staticmethod
    def validate_file_size(file_size: int) -> int:
        """Validate file size"""
        if file_size > FileValidator.MAX_FILE_SIZE:
            raise ValidationError("file_size", f"File too large. Maximum size: {FileValidator.MAX_FILE_SIZE // (1024*1024)}MB")
        
        return file_size

# Rate limiting validation
class RateLimitValidator:
    """Enhanced rate limiting with different limits for different endpoints"""
    
    RATE_LIMITS = {
        'auth': {'requests': 10, 'window': 300},      # 10 requests per 5 minutes
        'scan': {'requests': 5, 'window': 3600},      # 5 scans per hour
        'api': {'requests': 100, 'window': 3600},     # 100 API calls per hour
        'search': {'requests': 50, 'window': 3600},   # 50 searches per hour
    }
    
    @staticmethod
    def get_rate_limit(endpoint_type: str) -> Dict[str, int]:
        """Get rate limit configuration for endpoint type"""
        return RateLimitValidator.RATE_LIMITS.get(endpoint_type, {'requests': 60, 'window': 3600})

# Validation decorator
def validate_input(validation_model: BaseModel):
    """Decorator to validate request input using Pydantic models"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be used with FastAPI dependency injection
            # The actual validation happens in the endpoint definition
            return await func(*args, **kwargs)
        return wrapper
    return decorator