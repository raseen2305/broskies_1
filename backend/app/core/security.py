from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # Refresh tokens last 7 days
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # Check if token is expired
        exp = payload.get("exp")
        if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_refresh_token(token: str) -> Dict[str, Any]:
    """Verify refresh token"""
    payload = verify_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return payload

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

async def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Extract and verify current user token"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return {
            "user_id": user_id,
            "user_type": user_type,
            "token_payload": payload
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_current_user_optional(request) -> Optional[Any]:
    """
    Optional user authentication - returns user if authenticated, None if not
    Used for detecting user type without requiring authentication
    
    Simple header-based approach:
    - X-User-Type: internal = internal user
    - Authorization: Bearer <token> = internal user  
    - No headers = external user
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Debug: Log all headers
        logger.info(f"🔍 Headers received: {dict(request.headers)}")
        
        # Method 1: Check for X-User-Type header (simple override)
        user_type_header = request.headers.get("X-User-Type")
        logger.info(f"🔍 X-User-Type header: {user_type_header}")
        
        if user_type_header and user_type_header.lower() == "internal":
            logger.info("✅ Creating internal user from X-User-Type header")
            # Create a simple mock user for internal type
            mock_user = type('MockUser', (), {
                'id': '507f1f77bcf86cd799439011',
                'email': 'internal@example.com',
                'user_type': 'developer',
                'github_username': 'internal_user',
                'github_token': None  # MockUser doesn't have a real GitHub token
            })()
            return mock_user
        
        # Method 2: Check for Authorization header (JWT-based)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            logger.info("🔍 Processing JWT token")
            token = auth_header.split(" ")[1]
            
            # Verify token
            payload = verify_token(token)
            user_id = payload.get("sub")
            user_type = payload.get("user_type")
            email = payload.get("email")
            
            if user_id and user_type == "developer":
                logger.info("✅ Creating internal user from JWT token")
                # Create mock user for valid JWT
                mock_user = type('MockUser', (), {
                    'id': user_id,
                    'email': email or 'jwt@example.com',
                    'user_type': user_type,
                    'github_username': email.split('@')[0] if email and '@' in email else 'jwt_user',
                    'github_token': None  # MockUser doesn't have a real GitHub token
                })()
                return mock_user
        
        # No authentication found
        logger.info("🌐 No authentication found - external user")
        return None
        
    except Exception as e:
        logger.error(f"❌ Authentication error: {e}")
        # Any error means no authentication
        return None


async def get_current_hr_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get current authenticated HR user
    Verifies JWT token, checks user exists, is active, and is still approved
    
    Raises:
        HTTPException: If authentication fails or user not authorized
        
    Returns:
        dict: HR user document from database
    """
    from app.db_connection import get_database
    from bson import ObjectId
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Verify JWT token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        email = payload.get("email")
        
        # Check user type
        if user_type != "hr":
            logger.warning(f"Non-HR user attempted to access HR endpoint: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. HR credentials required."
            )
        
        # Get database connection
        db = await get_database()
        
        # Get HR user from database
        user_doc = await db.hr_users.find_one({"_id": ObjectId(user_id)})
        
        if not user_doc:
            logger.warning(f"HR user not found in database: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check if user is active
        if not user_doc.get("is_active", True):
            logger.warning(f"Inactive HR user attempted access: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Verify user is still approved
        approved = await db.approved_hr_users.find_one({"email": email})
        
        if not approved:
            logger.warning(f"Unapproved HR user attempted access: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your access has been revoked. Please contact administrator."
            )
        
        logger.info(f"HR user authenticated: {email}")
        return user_doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HR authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )