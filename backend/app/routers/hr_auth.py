"""
HR Authentication Router
Handles Google OAuth authentication for HR users with approval verification
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta, datetime
import logging
import uuid
import os

from app.core.security import create_access_token, create_refresh_token
from app.services.google_oauth_hr import get_google_oauth_hr_service
from app.models.hr_user import (
    HRUser, HRUserCreate, HRUserUpdate, HRUserResponse,
    ApprovedHRUser, ApprovalStatusResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/hr", tags=["hr-authentication"])
security = HTTPBearer()

# Request/Response Models

class GoogleOAuthRequest(BaseModel):
    code: str
    state: Optional[str] = None


class AuthResponse(BaseModel):
    user: HRUserResponse
    access_token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Helper Functions

def convert_objectid_to_string(doc):
    """Convert MongoDB ObjectId to string for Pydantic validation"""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def check_hr_approval(email: str, db) -> bool:
    """Check if HR user email is approved"""
    logger.info(f"[check_hr_approval] Checking email: '{email}' (length: {len(email)})")
    
    if db is None:
        logger.error("[check_hr_approval] Database is None!")
        return False
    
    logger.info(f"[check_hr_approval] Database name: {db.name}")
    
    try:
        # Log collection info
        logger.info(f"[check_hr_approval] Querying collection: {db.name}.approved_hr_users")
        
        # Try exact match first
        approved = await db.approved_hr_users.find_one({"email": email})
        logger.info(f"[check_hr_approval] Exact match result: {approved is not None}")
        logger.info(f"[check_hr_approval] Approved document: {approved}")
        
        if approved:
            logger.info(f"[check_hr_approval] Found approved email: '{approved.get('email')}'")
            return True
        
        # Debug: Show all emails in collection
        try:
            all_emails_cursor = db.approved_hr_users.find({}, {"email": 1})
            all_emails = await all_emails_cursor.to_list(length=20)
            logger.info(f"[check_hr_approval] All approved emails in DB: {[doc.get('email') for doc in all_emails]}")
        except Exception as debug_e:
            logger.error(f"[check_hr_approval] Failed to list emails: {debug_e}")
        
        # Try case-insensitive match as fallback
        approved_ci = await db.approved_hr_users.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})
        logger.info(f"[check_hr_approval] Case-insensitive match result: {approved_ci is not None}")
        
        if approved_ci:
            logger.warning(f"[check_hr_approval] Found with case-insensitive match: '{approved_ci.get('email')}'")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"[check_hr_approval] Error checking approval: {e}")
        import traceback
        logger.error(f"[check_hr_approval] Traceback: {traceback.format_exc()}")
        return False


async def get_or_create_hr_user(google_user_info: dict, db) -> HRUser:
    """Get existing HR user or create new one"""
    email = google_user_info["email"]
    
    # Check if user exists
    existing_user = await db.hr_users.find_one({"email": email})
    
    if existing_user:
        # Update last login
        await db.hr_users.update_one(
            {"_id": existing_user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        return HRUser(**convert_objectid_to_string(existing_user))
    
    # Create new HR user
    hr_user_data = HRUserCreate(
        email=email,
        google_id=google_user_info["google_id"],
        full_name=google_user_info.get("full_name"),
        profile_picture=google_user_info.get("profile_picture"),
        email_verified=google_user_info.get("email_verified", True)
    )
    
    result = await db.hr_users.insert_one(hr_user_data.dict())
    hr_user_doc = await db.hr_users.find_one({"_id": result.inserted_id})
    return HRUser(**convert_objectid_to_string(hr_user_doc))


# Endpoints

@router.get("/google/authorize")
async def hr_google_authorize():
    """
    Get Google OAuth authorization URL for HR users
    
    Returns:
        dict: Contains authorization_url to redirect user to
    """
    try:
        google_oauth = get_google_oauth_hr_service()
        auth_url = google_oauth.get_authorization_url()
        
        logger.info("Generated HR Google OAuth authorization URL")
        return {"authorization_url": auth_url}
        
    except Exception as e:
        logger.error(f"Failed to generate authorization URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )


@router.post("/google/callback", response_model=AuthResponse)
async def hr_google_callback(request: GoogleOAuthRequest):
    """
    Handle Google OAuth callback for HR users
    Verifies email is approved before allowing access
    
    Args:
        request: Contains OAuth code and optional state
        
    Returns:
        AuthResponse: User data and JWT tokens
        
    Raises:
        HTTPException: If email not approved or authentication fails
    """
    from app.db_connection import get_database
    
    try:
        db = await get_database()
        google_oauth = get_google_oauth_hr_service()
        
        # Exchange code for access token
        logger.info("Exchanging OAuth code for access token")
        token_data = await google_oauth.exchange_code_for_token(request.code)
        
        # Get user info from Google
        logger.info("Fetching user info from Google API")
        google_user_info = await google_oauth.get_user_info(token_data["access_token"])
        
        email = google_user_info["email"]
        logger.info(f"Google OAuth successful for email: {email}")
        
        # Check if email is approved
        logger.info(f"Checking approval status for: {email}")
        is_approved = await check_hr_approval(email, db)
        logger.info(f"Approval check result for {email}: {is_approved}")
        
        if not is_approved:
            logger.warning(f"Unapproved HR user attempted login: {email}")
            
            # Debug: Show all approved emails
            try:
                cursor = db.approved_hr_users.find({})
                all_approved = await cursor.to_list(length=10)
                approved_emails = [doc.get('email') for doc in all_approved]
                logger.warning(f"Currently approved emails: {approved_emails}")
            except Exception as debug_e:
                logger.error(f"Failed to fetch approved emails for debugging: {debug_e}")
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your email is not approved for HR dashboard access. Please complete the registration form first."
            )
        
        # Get or create HR user
        hr_user = await get_or_create_hr_user(google_user_info, db)
        
        # Create JWT tokens
        token_payload = {
            "sub": str(hr_user.id),
            "user_type": "hr",
            "email": hr_user.email,
            "email_verified": hr_user.email_verified
        }
        
        access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))  # 24 hours
        access_token = create_access_token(
            data=token_payload,
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data=token_payload)
        
        logger.info(f"HR user authenticated successfully: {email}")
        
        return AuthResponse(
            user=HRUserResponse(
                id=str(hr_user.id),
                email=hr_user.email,
                full_name=hr_user.full_name,
                profile_picture=hr_user.profile_picture,
                company=hr_user.company,
                role=hr_user.role,
                is_approved=hr_user.is_approved,
                created_at=hr_user.created_at,
                last_login=hr_user.last_login
            ),
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HR Google OAuth callback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout")
async def hr_logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout HR user
    Client should remove tokens from storage
    
    Returns:
        dict: Success message
    """
    logger.info("HR user logged out")
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=AuthResponse)
async def hr_refresh_token(request: RefreshTokenRequest):
    """
    Refresh HR user access token using refresh token
    
    Args:
        request: Contains refresh_token
        
    Returns:
        AuthResponse: New tokens and user data
        
    Raises:
        HTTPException: If refresh token invalid or user not found
    """
    from app.db_connection import get_database
    from app.core.security import verify_refresh_token
    
    try:
        db = await get_database()
        
        # Verify refresh token
        payload = verify_refresh_token(request.refresh_token)
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        
        if user_type != "hr":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Get HR user from database
        from bson import ObjectId
        user_doc = await db.hr_users.find_one({"_id": ObjectId(user_id)})
        
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        hr_user = HRUser(**convert_objectid_to_string(user_doc))
        
        # Check if still approved
        is_approved = await check_hr_approval(hr_user.email, db)
        if not is_approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your access has been revoked"
            )
        
        # Create new tokens
        token_payload = {
            "sub": user_id,
            "user_type": "hr",
            "email": hr_user.email,
            "email_verified": hr_user.email_verified
        }
        
        access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))
        access_token = create_access_token(
            data=token_payload,
            expires_delta=access_token_expires
        )
        new_refresh_token = create_refresh_token(data=token_payload)
        
        logger.info(f"Refreshed token for HR user: {hr_user.email}")
        
        return AuthResponse(
            user=HRUserResponse(
                id=str(hr_user.id),
                email=hr_user.email,
                full_name=hr_user.full_name,
                profile_picture=hr_user.profile_picture,
                company=hr_user.company,
                role=hr_user.role,
                is_approved=hr_user.is_approved,
                created_at=hr_user.created_at,
                last_login=hr_user.last_login
            ),
            access_token=access_token,
            refresh_token=new_refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )


@router.get("/me", response_model=HRUserResponse)
async def get_current_hr_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get current HR user information
    
    Returns:
        HRUserResponse: Current user data
        
    Raises:
        HTTPException: If token invalid or user not found
    """
    from app.db_connection import get_database
    from app.core.security import verify_token
    from bson import ObjectId
    
    try:
        db = await get_database()
        
        # Verify token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        
        if user_type != "hr":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Get HR user
        user_doc = await db.hr_users.find_one({"_id": ObjectId(user_id)})
        
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        hr_user = HRUser(**convert_objectid_to_string(user_doc))
        
        return HRUserResponse(
            id=str(hr_user.id),
            email=hr_user.email,
            full_name=hr_user.full_name,
            profile_picture=hr_user.profile_picture,
            company=hr_user.company,
            role=hr_user.role,
            is_approved=hr_user.is_approved,
            created_at=hr_user.created_at,
            last_login=hr_user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@router.get("/registration-status/{email}", response_model=ApprovalStatusResponse)
async def check_registration_status(email: str):
    """
    Check if email is approved for HR dashboard access
    
    Args:
        email: Email address to check
        
    Returns:
        ApprovalStatusResponse: Approval status and message
    """
    from app.db_connection import get_database
    
    try:
        db = await get_database()
        is_approved = await check_hr_approval(email, db)
        
        if is_approved:
            return ApprovalStatusResponse(
                email=email,
                is_approved=True,
                message="Email is approved for HR dashboard access"
            )
        else:
            return ApprovalStatusResponse(
                email=email,
                is_approved=False,
                message="Email is not approved. Please complete the registration form."
            )
            
    except Exception as e:
        logger.error(f"Failed to check registration status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check registration status"
        )


@router.get("/form-url")
async def get_registration_form_url():
    """
    Get Google Form URL for HR registration
    
    Returns:
        dict: Contains form_url
    """
    form_url = os.getenv(
        "GOOGLE_FORM_URL",
        "https://docs.google.com/forms/d/e/1FAIpQLSfpKFvNqca-W4fvPn7sa1zm6NpJpzvZYY948fk4_YbPdDRilA/viewform"
    )
    
    return {"form_url": form_url}


# Development/Testing Endpoints

class DevLoginRequest(BaseModel):
    email: str
    password: str


@router.post("/dev/login", response_model=AuthResponse)
async def hr_dev_login(request: DevLoginRequest):
    """
    Development login endpoint for testing
    ONLY works when ENABLE_DEV_LOGIN=true in environment
    
    Args:
        request: Contains email and password
        
    Returns:
        AuthResponse: User data and JWT tokens
        
    Raises:
        HTTPException: If dev login disabled or credentials invalid
    """
    from app.db_connection import get_database
    
    # Check if dev login is enabled
    dev_login_enabled = os.getenv("ENABLE_DEV_LOGIN", "false").lower() == "true"
    
    if not dev_login_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development login is not enabled"
        )
    
    # Validate dev credentials
    dev_email = "test.hr@example.com"
    dev_password = "DevTest2024!Secure"
    
    if request.email != dev_email or request.password != dev_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid development credentials"
        )
    
    try:
        db = await get_database()
        
        # Check if dev user exists in database
        dev_user_doc = await db.hr_users.find_one({"email": dev_email})
        
        if not dev_user_doc:
            # Create dev user
            dev_user_data = {
                "email": dev_email,
                "google_id": "dev-google-id-001",
                "full_name": "Test HR Manager",
                "profile_picture": None,
                "company": "Development Testing Inc.",
                "role": "Senior HR Manager",
                "email_verified": True,
                "is_approved": True,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow()
            }
            result = await db.hr_users.insert_one(dev_user_data)
            dev_user_doc = await db.hr_users.find_one({"_id": result.inserted_id})
            
            # Add to approved list
            await db.approved_hr_users.insert_one({
                "email": dev_email,
                "full_name": "Test HR Manager",
                "company": "Development Testing Inc.",
                "approved_at": datetime.utcnow(),
                "approved_by": "system"
            })
        else:
            # Update last login
            await db.hr_users.update_one(
                {"_id": dev_user_doc["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        
        hr_user = HRUser(**convert_objectid_to_string(dev_user_doc))
        
        # Create JWT tokens
        token_payload = {
            "sub": str(hr_user.id),
            "user_type": "hr",
            "email": hr_user.email,
            "email_verified": hr_user.email_verified,
            "dev_mode": True  # Mark as dev token
        }
        
        access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))
        access_token = create_access_token(
            data=token_payload,
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data=token_payload)
        
        logger.info(f"Development login successful: {dev_email}")
        
        return AuthResponse(
            user=HRUserResponse(
                id=str(hr_user.id),
                email=hr_user.email,
                full_name=hr_user.full_name,
                profile_picture=hr_user.profile_picture,
                company=hr_user.company,
                role=hr_user.role,
                is_approved=hr_user.is_approved,
                created_at=hr_user.created_at,
                last_login=hr_user.last_login
            ),
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Development login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Development login failed: {str(e)}"
        )
