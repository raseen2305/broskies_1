import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.get_google_redirect_uri()
        
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate Google OAuth authorization URL"""
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
            "state": state or ""
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            async with httpx.AsyncClient() as client:
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
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to exchange code for token"
                    )
                
                data = response.json()
                access_token = data.get("access_token")
                id_token = data.get("id_token")
                
                if not access_token:
                    error = data.get("error", "Unknown error")
                    error_description = data.get("error_description", "")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Google OAuth error: {error} - {error_description}"
                    )
                
                return {
                    "access_token": access_token,
                    "id_token": id_token,
                    "token_type": data.get("token_type", "Bearer"),
                    "expires_in": data.get("expires_in", 3600)
                }
                
        except httpx.RequestError as e:
            logger.error(f"Google OAuth request failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to communicate with Google"
            )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to get user information from Google"
                    )
                
                user_data = response.json()
                
                return {
                    "id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "verified_email": user_data.get("verified_email", False),
                    "name": user_data.get("name"),
                    "given_name": user_data.get("given_name"),
                    "family_name": user_data.get("family_name"),
                    "picture": user_data.get("picture"),
                    "locale": user_data.get("locale")
                }
                
        except httpx.RequestError as e:
            logger.error(f"Google API request failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to communicate with Google API"
            )
    
    async def validate_token(self, access_token: str) -> bool:
        """Validate Google access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
                )
                return response.status_code == 200
        except:
            return False
    
    def create_google_form_url(self, form_id: str) -> str:
        """Create Google Form URL for HR registration"""
        return f"https://docs.google.com/forms/d/e/{form_id}/viewform"