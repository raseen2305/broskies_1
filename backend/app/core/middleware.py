from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.security import verify_token
from app.core.validation import SQLInjectionDetector, XSSProtection, InputSanitizer
from app.services.performance_service import performance_service
import logging
import time
import json
from typing import Any, Dict

logger = logging.getLogger(__name__)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication for protected routes"""
    
    def __init__(self, app, protected_paths: list = None):
        super().__init__(app)
        self.protected_paths = protected_paths or [
            "/scan/",
            "/evaluation/",
            "/profile/"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public routes
        if not any(request.url.path.startswith(path) for path in self.protected_paths):
            return await call_next(request)
        
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Check for Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization header missing"}
            )
        
        try:
            # Extract token from Bearer header
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
            
            # Verify token
            payload = verify_token(token)
            
            # Add user info to request state
            request.state.user_id = payload.get("sub")
            request.state.user_type = payload.get("user_type")
            request.state.token_payload = payload
            
        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"}
            )
        
        return await call_next(request)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with different limits for different endpoints"""
    
    def __init__(self, app, default_requests_per_minute: int = 60):
        super().__init__(app)
        self.default_requests_per_minute = default_requests_per_minute
        self.request_counts = {}
        
        # Different rate limits for different endpoint types
        self.rate_limits = {
            '/auth/': {'requests': 30, 'window': 60},      # 30 requests per minute (increased for development)
            '/scan/': {'requests': 100, 'window': 3600},    # 100 scans per hour (increased for development)
            '/evaluation/': {'requests': 200, 'window': 3600}, # 200 API calls per hour
            '/performance/': {'requests': 50, 'window': 3600}, # 50 performance calls per hour
            '/security/test-rate-limit': {'requests': 3, 'window': 60}, # 3 requests per minute for testing
        }
    
    def get_rate_limit_for_path(self, path: str) -> dict:
        """Get rate limit configuration for a specific path"""
        for prefix, config in self.rate_limits.items():
            if path.startswith(prefix):
                return config
        
        # Default rate limit
        return {'requests': self.default_requests_per_minute, 'window': 60}
    
    def get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from token if available
        if hasattr(request.state, 'user_id') and request.state.user_id:
            return f"user:{request.state.user_id}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        return f"ip:{request.client.host}"
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client_id = self.get_client_identifier(request)
        
        # Get rate limit config for this path
        rate_config = self.get_rate_limit_for_path(path)
        window_size = rate_config['window']
        max_requests = rate_config['requests']
        
        current_time = int(time.time())
        window_start = current_time - (current_time % window_size)
        
        # Clean old entries (older than 2 windows)
        cutoff_time = window_start - (2 * window_size)
        self.request_counts = {
            key: count for key, count in self.request_counts.items()
            if key[2] >= cutoff_time
        }
        
        # Check rate limit
        key = (client_id, path.split('/')[1], window_start)  # client, endpoint_type, window
        current_requests = self.request_counts.get(key, 0)
        
        if current_requests >= max_requests:
            logger.warning(f"Rate limit exceeded for {client_id} on {path}")
            
            # Get origin for CORS headers
            origin = request.headers.get("origin", "*")
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": max_requests,
                    "window": window_size,
                    "retry_after": window_size - (current_time % window_size)
                },
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
                    "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, X-Request-ID, Cache-Control, Pragma, Expires",
                }
            )
        
        # Increment counter
        self.request_counts[key] = current_requests + 1
        
        return await call_next(request)

class SecurityValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for security validation including XSS and injection prevention"""
    
    def __init__(self, app):
        super().__init__(app)
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            r'eval\s*\(',
            r'expression\s*\(',
        ]
    
    async def validate_request_size(self, request: Request) -> bool:
        """Validate request size"""
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > self.max_request_size:
            return False
        return True
    
    async def validate_headers(self, request: Request) -> bool:
        """Validate request headers for suspicious content"""
        # Standard headers to always check
        standard_headers = ['user-agent', 'referer', 'x-forwarded-for']
        
        # Check all headers for potential threats
        for header_name, header_value in request.headers.items():
            # Skip standard HTTP headers that are safe
            if header_name.lower() in ['host', 'content-length', 'content-type', 'accept', 'accept-encoding', 'connection', 'authorization', 'user-agent', 'cache-control', 'pragma', 'upgrade-insecure-requests']:
                continue
            
            # Only validate custom headers, not standard browser/client headers
            if header_name.lower().startswith('x-') or header_name.lower() in ['referer', 'origin']:
                if header_value:
                    if SQLInjectionDetector.detect_injection(header_value):
                        logger.warning(f"Suspicious content in {header_name} header: {header_value[:100]}")
                        return False
                    
                    if XSSProtection.detect_xss(header_value):
                        logger.warning(f"XSS attempt in {header_name} header: {header_value[:100]}")
                        return False
        
        return True
    
    async def validate_query_params(self, request: Request) -> bool:
        """Validate query parameters"""
        for key, value in request.query_params.items():
            if SQLInjectionDetector.detect_injection(str(value)):
                logger.warning(f"SQL injection attempt in query param {key}: {value}")
                return False
            
            if XSSProtection.detect_xss(str(value)):
                logger.warning(f"XSS attempt in query param {key}: {value}")
                return False
        
        return True
    
    async def validate_json_body(self, body: bytes) -> bool:
        """Validate JSON request body"""
        if not body:
            return True
        
        try:
            # Parse JSON
            data = json.loads(body.decode('utf-8'))
            
            # Recursively validate all string values
            return self.validate_json_values(data)
            
        except (json.JSONDecodeError, UnicodeDecodeError):
            # If it's not valid JSON, let FastAPI handle the error
            return True
    
    def validate_json_values(self, data: Any) -> bool:
        """Recursively validate JSON values"""
        if isinstance(data, dict):
            for key, value in data.items():
                if not self.validate_json_values(value):
                    return False
        elif isinstance(data, list):
            for item in data:
                if not self.validate_json_values(item):
                    return False
        elif isinstance(data, str):
            if SQLInjectionDetector.detect_injection(data):
                logger.warning(f"SQL injection attempt in JSON body: {data[:100]}")
                return False
            
            if XSSProtection.detect_xss(data):
                logger.warning(f"XSS attempt in JSON body: {data[:100]}")
                return False
        
        return True
    
    async def dispatch(self, request: Request, call_next):
        # Skip validation for OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Validate request size
        if not await self.validate_request_size(request):
            logger.warning(f"Request too large from {request.client.host}")
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request entity too large"}
            )
        
        # Validate headers
        if not await self.validate_headers(request):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid request headers"}
            )
        
        # Validate query parameters
        if not await self.validate_query_params(request):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid query parameters"}
            )
        
        # Validate request body for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if not await self.validate_json_body(body):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request body"}
                )
            
            # Recreate request with the body (since we consumed it)
            async def receive():
                return {"type": "http.request", "body": body}
            
            request._receive = receive
        
        return await call_next(request)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses for security monitoring"""
    
    def __init__(self, app):
        super().__init__(app)
        self.sensitive_paths = ['/auth/', '/admin/']
        self.log_body_paths = ['/scan/', '/evaluation/']
    
    def should_log_body(self, path: str) -> bool:
        """Determine if request body should be logged"""
        return any(path.startswith(prefix) for prefix in self.log_body_paths)
    
    def is_sensitive_path(self, path: str) -> bool:
        """Determine if path contains sensitive information"""
        return any(path.startswith(prefix) for prefix in self.sensitive_paths)
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        method = request.method
        client_ip = request.client.host
        
        # Get user agent
        user_agent = request.headers.get('user-agent', 'Unknown')
        
        # Log request
        log_data = {
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "timestamp": time.time()
        }
        
        # Log query parameters (but not for sensitive paths)
        if not self.is_sensitive_path(path) and request.query_params:
            log_data["query_params"] = dict(request.query_params)
        
        # Log request body for specific paths (but not sensitive data)
        if self.should_log_body(path) and method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body and len(body) < 1000:  # Only log small bodies
                    log_data["body_size"] = len(body)
                
                # Recreate request with the body
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
            except Exception:
                pass
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        response_time_ms = round(process_time * 1000, 2)
        log_data["response_time"] = response_time_ms
        log_data["status_code"] = response.status_code
        
        # Record performance metric
        user_id = getattr(request.state, 'user_id', None)
        error = None if response.status_code < 400 else f"HTTP {response.status_code}"
        
        performance_service.record_api_metric(
            endpoint=path,
            method=method,
            response_time_ms=response_time_ms,
            status_code=response.status_code,
            user_id=user_id,
            error=error
        )
        
        # Log based on status code
        if response.status_code >= 400:
            logger.warning(f"HTTP {response.status_code}: {json.dumps(log_data)}")
        elif response.status_code >= 300:
            logger.info(f"HTTP {response.status_code}: {json.dumps(log_data)}")
        else:
            logger.debug(f"HTTP {response.status_code}: {json.dumps(log_data)}")
        
        # Add response time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

