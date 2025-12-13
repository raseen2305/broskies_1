"""
Google OAuth Service for HR Dashboard Authentication
Handles OAuth 2.0 flow specifically for HR users with approval verification
"""

import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
import logging
import os

logger = logging.getLogger(__name__)


class GoogleOAuthHRService:
    """Google OAuth service for HR authentication"""
    
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_HR_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_HR_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_HR_REDIRECT_URI", "http://localhost:5173/hr/auth/callback")
        
        # Validate configuration
        if not self.client_id or not self.client_secret:
            logger.error("Google HR OAuth credentials not configured")
            raise ValueError("GOOGLE_HR_CLIENT_ID and GOOGLE_HR_CLIENT_SECRET must be set")
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate Google OAuth authorization URL for HR users
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            str: Complete authorization URL to redirect user to
        """
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "select_account consent",  # Force account selection and consent
        }
        
        if state:
            params["state"] = state
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        authorization_url = f"{base_url}?{query_string}"
        
        logger.info(f"Generated HR OAuth authorization URL with redirect_uri: {self.redirect_uri}")
        return authorization_url
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from Google OAuth callback
            
        Returns:
            dict: Token data including access_token, id_token, expires_in
            
        Raises:
            HTTPException: If token exchange fails
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": self.redirect_uri,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    error = error_data.get("error", "unknown_error")
                    error_description = error_data.get("error_description", "Failed to exchange code")
                    
                    logger.error(f"Google OAuth token exchange failed: {error} - {error_description}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Authentication failed: {error_description}"
                    )
                
                data = response.json()
                access_token = data.get("access_token")
                
                if not access_token:
                    logger.error("No access token in Google OAuth response")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to obtain access token from Google"
                    )
                
                logger.info("Successfully exchanged authorization code for access token")
                return {
                    "access_token": access_token,
                    "id_token": data.get("id_token"),
                    "token_type": data.get("token_type", "Bearer"),
                    "expires_in": data.get("expires_in", 3600),
                    "refresh_token": data.get("refresh_token")
                }
                
        except httpx.RequestError as e:
            logger.error(f"Google OAuth request failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to connect to Google authentication service. Please try again."
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during authentication"
            )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Google API
        
        Args:
            access_token: Google OAuth access token
            
        Returns:
            dict: User information including id, email, name, picture
            
        Raises:
            HTTPException: If user info retrieval fails
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get user info from Google: {response.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to retrieve user information from Google"
                    )
                
                user_data = response.json()
                
                # Validate required fields
                if not user_data.get("email"):
                    logger.error("No email in Google user data")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Unable to retrieve email from Google account"
                    )
                
                if not user_data.get("verified_email", False):
                    logger.warning(f"Unverified email attempted login: {user_data.get('email')}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Please verify your email address with Google before signing in"
                    )
                
                logger.info(f"Successfully retrieved user info for: {user_data.get('email')}")
                return {
                    "google_id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "email_verified": user_data.get("verified_email", False),
                    "full_name": user_data.get("name"),
                    "given_name": user_data.get("given_name"),
                    "family_name": user_data.get("family_name"),
                    "profile_picture": user_data.get("picture"),
                    "locale": user_data.get("locale")
                }
                
        except httpx.RequestError as e:
            logger.error(f"Google API request failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to connect to Google API. Please try again."
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving user info: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while retrieving user information"
            )
    
    async def validate_token(self, access_token: str) -> bool:
        """
        Validate Google access token
        
        Args:
            access_token: Google OAuth access token
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False


# Singleton instance
_google_oauth_hr_service = None


def get_google_oauth_hr_service() -> GoogleOAuthHRService:
    """Get or create GoogleOAuthHRService singleton instance"""
    global _google_oauth_hr_service
    if _google_oauth_hr_service is None:
        _google_oauth_hr_service = GoogleOAuthHRService()
    return _google_oauth_hr_service
