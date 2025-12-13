from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta
import httpx
import logging
import uuid
from github import Github

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_token, verify_refresh_token, get_current_user_token
from app.database import get_database
from app.models.user import User, UserCreate, HRUser, HRUserCreate
from app.services.github_oauth import GitHubOAuthService
from app.services.google_oauth import GoogleOAuthService

logger = logging.getLogger(__name__)

def convert_objectid_to_string(doc):
    """Convert MongoDB ObjectId to string for Pydantic validation"""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

router = APIRouter()
security = HTTPBearer()

class GitHubLoginRequest(BaseModel):
    github_token: str

class AuthResponse(BaseModel):
    user: dict
    access_token: str
    refresh_token: str

class HRRegistrationRequest(BaseModel):
    email: str
    company: str
    role: str
    hiring_needs: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class GitHubOAuthRequest(BaseModel):
    code: str
    state: Optional[str] = None

class GoogleOAuthRequest(BaseModel):
    code: str
    state: Optional[str] = None

class HRRegistrationData(BaseModel):
    company: str
    role: str
    hiring_needs: Optional[str] = None

class GoogleCompleteRegistrationRequest(BaseModel):
    code: str
    state: Optional[str] = None
    company: str
    role: str
    hiring_needs: Optional[str] = None

@router.get("/github/authorize")
async def github_authorize():
    """Get GitHub OAuth authorization URL"""
    github_oauth = GitHubOAuthService()
    auth_url = github_oauth.get_authorization_url()
    return {"authorization_url": auth_url}

@router.get("/github/callback")
async def github_callback(
    code: str,
    state: Optional[str] = None
):
    """Handle GitHub OAuth callback"""
    logger.info(f"GitHub OAuth callback received - code: {code[:10] if code else 'None'}..., state: {state}")
    
    try:
        # Get database connection
        from app.db_connection import get_database as get_db_connection
        db = await get_db_connection()
        
        github_oauth = GitHubOAuthService()
        
        # Exchange code for access token
        logger.info("Exchanging OAuth code for access token")
        access_token = await github_oauth.exchange_code_for_token(code, state)
        
        # Get user info from GitHub
        logger.info("Fetching user info from GitHub API")
        github_user_info = await github_oauth.get_user_info(access_token)
        
        if not github_user_info.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub account must have a public email address"
            )
        
        # Check if user exists
        existing_user = None
        if db is not None:
            existing_user = await db.users.find_one({"github_username": github_user_info["login"]})
        
        if existing_user:
            user = User(**convert_objectid_to_string(existing_user))
            # Update GitHub token and user info
            if db is not None:
                await db.users.update_one(
                    {"_id": existing_user["_id"]},
                    {"$set": {
                        "github_token": access_token,
                        "email": github_user_info["email"]
                    }}
                )
        else:
            # Create new user
            user_data = UserCreate(
                email=github_user_info["email"],
                github_username=github_user_info["login"],
                github_access_token=access_token,
                user_type="developer"
            )
            
            if db is not None:
                result = await db.users.insert_one(user_data.dict())
                user_doc = await db.users.find_one({"_id": result.inserted_id})
                user = User(**convert_objectid_to_string(user_doc))
            else:
                # For testing without database
                from datetime import datetime
                user = User(
                    id="test_user_id",
                    email=github_user_info["email"],
                    github_username=github_user_info["login"],
                    github_access_token=access_token,
                    user_type="developer",
                    created_at=datetime.utcnow()
                )
        
        # Create access and refresh tokens
        token_data = {"sub": str(user.id), "user_type": "developer", "email": user.email}
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        jwt_access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data=token_data)
        
        # For OAuth callback, create a temporary session and redirect to frontend
        from fastapi.responses import RedirectResponse
        import uuid
        
        # Generate a temporary session ID
        session_id = str(uuid.uuid4())
        
        # Store the auth response temporarily (in production, use Redis)
        # For now, we'll use a simple in-memory store
        if not hasattr(github_callback, '_temp_sessions'):
            github_callback._temp_sessions = {}
        
        github_callback._temp_sessions[session_id] = {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "githubUsername": user.github_username,
                "userType": user.user_type,
                "createdAt": user.created_at.isoformat()
            },
            "access_token": jwt_access_token,
            "refresh_token": refresh_token
        }
        
        # Redirect to frontend with session ID
        frontend_base_url = settings.get_frontend_url()
        frontend_url = f"{frontend_base_url}/developer/auth?session={session_id}"
        
        logger.info(f"Redirecting to frontend: {frontend_url}")
        return RedirectResponse(url=frontend_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub OAuth failed: {str(e)}"
        )

@router.post("/developer/login", response_model=AuthResponse)
async def developer_login(
    request: GitHubLoginRequest,
    db = Depends(get_database)
):
    """Authenticate developer using GitHub token (legacy endpoint)"""
    try:
        # Verify GitHub token and get user info
        g = Github(request.github_token)
        github_user = g.get_user()
        
        # Check if user exists
        existing_user = None
        if db is not None:
            existing_user = await db.users.find_one({"github_username": github_user.login})
        
        if existing_user:
            user = User(**convert_objectid_to_string(existing_user))
            # Update GitHub token
            if db is not None:
                await db.users.update_one(
                    {"_id": existing_user["_id"]},
                    {"$set": {"github_token": request.github_token}}
                )
        else:
            # Create new user
            user_data = UserCreate(
                email=github_user.email or f"{github_user.login}@github.local",
                github_username=github_user.login,
                github_token=request.github_token,
                user_type="developer"
            )
            
            if db is not None:
                result = await db.users.insert_one(user_data.dict())
                user_doc = await db.users.find_one({"_id": result.inserted_id})
                user = User(**convert_objectid_to_string(user_doc))
            else:
                # For testing without database
                user = User(
                    id="test_user_id",
                    email=github_user.email or f"{github_user.login}@github.local",
                    github_username=github_user.login,
                    github_token=request.github_token,
                    user_type="developer"
                )
        
        # Create access and refresh tokens
        token_data = {"sub": str(user.id), "user_type": "developer", "email": user.email}
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data=token_data)
        
        return AuthResponse(
            user={
                "id": str(user.id),
                "email": user.email,
                "githubUsername": user.github_username,
                "userType": user.user_type,
                "createdAt": user.created_at.isoformat()
            },
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"GitHub authentication failed: {str(e)}"
        )

@router.get("/google/authorize")
async def google_authorize():
    """Get Google OAuth authorization URL for HR users"""
    google_oauth = GoogleOAuthService()
    auth_url = google_oauth.get_authorization_url()
    return {"authorization_url": auth_url}

@router.get("/google/callback")
async def google_callback(
    code: str,
    state: Optional[str] = None
):
    """Handle Google OAuth callback for HR users"""
    logger.info(f"Google OAuth callback received - code: {code[:10] if code else 'None'}..., state: {state}")
    
    # Get database connection
    from app.db_connection import get_database as get_db_connection
    db = await get_db_connection()
    
    try:
        google_oauth = GoogleOAuthService()
        
        # Exchange code for access token
        logger.info("Exchanging OAuth code for access token")
        token_data = await google_oauth.exchange_code_for_token(code, state)
        
        # Get user info from Google
        logger.info("Fetching user info from Google API")
        google_user_info = await google_oauth.get_user_info(token_data["access_token"])
        
        if not google_user_info.get("verified_email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account email must be verified"
            )
        
        # Check if HR user already exists
        existing_hr = None
        if db is not None:
            existing_hr = await db.hr_users.find_one({"email": google_user_info["email"]})
        
        if existing_hr:
            # Existing user - log them in
            hr_user = HRUser(**convert_objectid_to_string(existing_hr))
            
            # Create access and refresh tokens
            jwt_token_data = {"sub": str(hr_user.id), "user_type": "hr", "email": hr_user.email}
            access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
            jwt_access_token = create_access_token(
                data=jwt_token_data,
                expires_delta=access_token_expires
            )
            refresh_token = create_refresh_token(data=jwt_token_data)
            
            # Store in temporary session
            session_id = str(uuid.uuid4())
            
            if not hasattr(google_callback, '_temp_sessions'):
                google_callback._temp_sessions = {}
            
            google_callback._temp_sessions[session_id] = {
                "user": {
                    "id": str(hr_user.id),
                    "email": hr_user.email,
                    "company": hr_user.company,
                    "role": hr_user.role,
                    "userType": "hr",
                    "createdAt": hr_user.created_at.isoformat()
                },
                "access_token": jwt_access_token,
                "refresh_token": refresh_token
            }
            
            # Redirect to HR dashboard
            frontend_base_url = settings.get_frontend_url()
            frontend_url = f"{frontend_base_url}/hr/auth?session={session_id}"
            
            logger.info(f"Redirecting existing HR user to: {frontend_url}")
            return RedirectResponse(url=frontend_url, status_code=302)
        else:
            # New user - redirect to registration form with code
            frontend_base_url = settings.get_frontend_url()
            frontend_url = f"{frontend_base_url}/hr/auth?code={code}&state={state or ''}"
            
            logger.info(f"Redirecting new HR user to registration: {frontend_url}")
            return RedirectResponse(url=frontend_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google OAuth failed: {str(e)}"
        )

@router.post("/google/complete-registration")
async def google_complete_registration(
    request: GoogleCompleteRegistrationRequest
):
    """Complete HR registration after Google OAuth"""
    # Get database connection
    from app.db_connection import get_database as get_db_connection
    db = await get_db_connection()
    
    try:
        google_oauth = GoogleOAuthService()
        
        # Exchange code for access token
        token_data = await google_oauth.exchange_code_for_token(request.code, request.state)
        
        # Get user info from Google
        google_user_info = await google_oauth.get_user_info(token_data["access_token"])
        
        if not google_user_info.get("verified_email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account email must be verified"
            )
        
        # Create new HR user
        hr_user_data = HRUserCreate(
            email=google_user_info["email"],
            company=request.company,
            role=request.role,
            hiring_needs=request.hiring_needs
        )
        
        if db is not None:
            result = await db.hr_users.insert_one(hr_user_data.dict())
            hr_user_doc = await db.hr_users.find_one({"_id": result.inserted_id})
            hr_user = HRUser(**convert_objectid_to_string(hr_user_doc))
        else:
            # For testing without database
            from datetime import datetime
            hr_user = HRUser(
                id="test_hr_id",
                email=google_user_info["email"],
                company=request.company,
                role=request.role,
                hiring_needs=request.hiring_needs,
                created_at=datetime.utcnow()
            )
        
        # Create access and refresh tokens
        jwt_token_data = {"sub": str(hr_user.id), "user_type": "hr", "email": hr_user.email}
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data=jwt_token_data,
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data=jwt_token_data)
        
        return AuthResponse(
            user={
                "id": str(hr_user.id),
                "email": hr_user.email,
                "company": hr_user.company,
                "role": hr_user.role,
                "userType": "hr",
                "createdAt": hr_user.created_at.isoformat()
            },
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google OAuth registration failed: {str(e)}"
        )

@router.get("/google/form")
async def get_google_form():
    """Get Google Form URL for HR registration"""
    # BroskiesHub HR Registration Google Form
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSfpKFvNqca-W4fvPn7sa1zm6NpJpzvZYY948fk4_YbPdDRilA/viewform?usp=dialog"
    return {"form_url": form_url}

@router.post("/hr/register", response_model=AuthResponse)
async def hr_register(
    request: HRRegistrationRequest,
    db = Depends(get_database)
):
    """Register HR user (legacy endpoint)"""
    try:
        # Check if HR user already exists
        existing_hr = None
        if db is not None:
            existing_hr = await db.hr_users.find_one({"email": request.email})
        
        if existing_hr:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="HR user with this email already exists"
            )
        
        # Create new HR user
        hr_user_data = HRUserCreate(
            email=request.email,
            company=request.company,
            role=request.role,
            hiring_needs=request.hiring_needs
        )
        
        if db is not None:
            result = await db.hr_users.insert_one(hr_user_data.dict())
            hr_user_doc = await db.hr_users.find_one({"_id": result.inserted_id})
            hr_user = HRUser(**convert_objectid_to_string(hr_user_doc))
        else:
            # For testing without database
            hr_user = HRUser(
                id="test_hr_id",
                email=request.email,
                company=request.company,
                role=request.role,
                hiring_needs=request.hiring_needs
            )
        
        # Create access and refresh tokens
        token_data = {"sub": str(hr_user.id), "user_type": "hr", "email": hr_user.email}
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data=token_data)
        
        return AuthResponse(
            user={
                "id": str(hr_user.id),
                "email": hr_user.email,
                "company": hr_user.company,
                "role": hr_user.role,
                "userType": "hr",
                "createdAt": hr_user.created_at.isoformat()
            },
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"HR registration failed: {str(e)}"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_database)
):
    """Get current authenticated user"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        
        if user_type == "developer":
            user_doc = await db.users.find_one({"_id": user_id})
            if user_doc:
                return User(**convert_objectid_to_string(user_doc))
        elif user_type == "hr":
            user_doc = await db.hr_users.find_one({"_id": user_id})
            if user_doc:
                return HRUser(**convert_objectid_to_string(user_doc))
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

@router.post("/refresh", response_model=AuthResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db = Depends(get_database)
):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = verify_refresh_token(request.refresh_token)
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        
        if not user_id or not user_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user from database
        if user_type == "developer":
            user_doc = await db.users.find_one({"_id": user_id})
            if not user_doc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            user = User(**convert_objectid_to_string(user_doc))
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "githubUsername": user.github_username,
                "userType": user.user_type,
                "createdAt": user.created_at.isoformat()
            }
        elif user_type == "hr":
            user_doc = await db.hr_users.find_one({"_id": user_id})
            if not user_doc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            user = HRUser(**convert_objectid_to_string(user_doc))
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "company": user.company,
                "role": user.role,
                "userType": "hr",
                "createdAt": user.created_at.isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user type"
            )
        
        # Create new tokens
        token_data = {"sub": user_id, "user_type": user_type, "email": payload.get("email")}
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        new_refresh_token = create_refresh_token(data=token_data)
        
        return AuthResponse(
            user=user_data,
            access_token=access_token,
            refresh_token=new_refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get temporary session data for OAuth callback"""
    if hasattr(github_callback, '_temp_sessions') and session_id in github_callback._temp_sessions:
        session_data = github_callback._temp_sessions[session_id]
        # Remove the session after retrieval (single use)
        del github_callback._temp_sessions[session_id]
        return session_data
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )

@router.post("/logout")
async def logout(current_user_token: dict = Depends(get_current_user_token)):
    """Logout user (client should remove tokens)"""
    return {"message": "Successfully logged out"}

@router.get("/me")
async def get_current_user_info(
    current_user_token: dict = Depends(get_current_user_token),
    db = Depends(get_database)
):
    """Get current user information"""
    try:
        user_id = current_user_token["user_id"]
        user_type = current_user_token["user_type"]
        
        if user_type == "developer":
            user_doc = await db.users.find_one({"_id": user_id})
            if not user_doc:
                raise HTTPException(status_code=404, detail="User not found")
            user = User(**convert_objectid_to_string(user_doc))
            return {
                "id": str(user.id),
                "email": user.email,
                "githubUsername": user.github_username,
                "userType": user.user_type,
                "createdAt": user.created_at.isoformat(),
                "lastScan": user.last_scan.isoformat() if user.last_scan else None
            }
        elif user_type == "hr":
            user_doc = await db.hr_users.find_one({"_id": user_id})
            if not user_doc:
                raise HTTPException(status_code=404, detail="User not found")
            user = HRUser(**convert_objectid_to_string(user_doc))
            return {
                "id": str(user.id),
                "email": user.email,
                "company": user.company,
                "role": user.role,
                "userType": "hr",
                "createdAt": user.created_at.isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not get user information"
        )
