import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.core.config import settings
from app.services.github_api_service import GitHubAPIService
import logging

logger = logging.getLogger(__name__)

class GitHubOAuthService:
    def __init__(self):
        self.client_id = settings.github_client_id
        self.client_secret = settings.github_client_secret
        self.redirect_uri = settings.get_github_redirect_uri()
        
        # Validate OAuth configuration for Vercel
        if not self.client_id or not self.client_secret:
            logger.error("GitHub OAuth credentials not configured")
            raise ValueError("GitHub OAuth credentials missing")
        
        logger.info(f"GitHub OAuth configured with redirect URI: {self.redirect_uri}")
        
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate GitHub OAuth authorization URL"""
        base_url = "https://github.com/login/oauth/authorize"
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email,public_repo,read:user",
            "state": state or ""
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, state: Optional[str] = None) -> str:
        """Exchange authorization code for access token"""
        logger.info(f"Exchanging OAuth code for token (code length: {len(code) if code else 0})")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                }
                
                # Only add state if provided
                if state:
                    payload["state"] = state
                
                logger.debug(f"OAuth token exchange payload: {dict(payload, client_secret='***')}")
                
                response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data=payload,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "BroskiesHub/1.0"
                    }
                )
                
                logger.info(f"GitHub OAuth token response status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"GitHub OAuth token exchange failed: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to exchange code for token (HTTP {response.status_code})"
                    )
                
                data = response.json()
                logger.debug(f"GitHub OAuth response data keys: {list(data.keys())}")
                
                access_token = data.get("access_token")
                
                if not access_token:
                    error = data.get("error", "Unknown error")
                    error_description = data.get("error_description", "No description provided")
                    logger.error(f"GitHub OAuth error: {error} - {error_description}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"GitHub OAuth error: {error} - {error_description}"
                    )
                
                logger.info("Successfully obtained GitHub access token")
                return access_token
                
        except httpx.RequestError as e:
            logger.error(f"GitHub OAuth request failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to communicate with GitHub OAuth service"
            )
        except Exception as e:
            logger.error(f"Unexpected error during OAuth token exchange: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth token exchange failed"
            )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from GitHub API using the optimized API service"""
        try:
            api_service = GitHubAPIService(access_token)
            
            # Get user profile
            user_data = await api_service.get_user_info()
            
            # Get user emails if needed
            primary_email = user_data.get("email")
            if not primary_email:
                try:
                    emails_data = await api_service._make_request("GET", "/user/emails")
                    for email in emails_data:
                        if email.get("primary", False):
                            primary_email = email.get("email")
                            break
                except Exception as e:
                    logger.warning(f"Could not fetch user emails: {e}")
            
            return {
                "id": user_data.get("id"),
                "login": user_data.get("login"),
                "email": primary_email,
                "name": user_data.get("name"),
                "avatar_url": user_data.get("avatar_url"),
                "bio": user_data.get("bio"),
                "company": user_data.get("company"),
                "location": user_data.get("location"),
                "public_repos": user_data.get("public_repos", 0),
                "followers": user_data.get("followers", 0),
                "following": user_data.get("following", 0),
                "created_at": user_data.get("created_at"),
                "updated_at": user_data.get("updated_at")
            }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"GitHub API request failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to communicate with GitHub API"
            )
    
    async def validate_token(self, access_token: str) -> bool:
        """Validate GitHub access token using the optimized API service"""
        try:
            api_service = GitHubAPIService(access_token)
            return await api_service.validate_token()
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False
    
    async def get_token_info(self, access_token: str) -> Dict[str, Any]:
        """Get detailed information about the access token using the optimized API service"""
        try:
            api_service = GitHubAPIService(access_token)
            
            # Validate token and get user info
            user_data = await api_service.get_user_info()
            rate_limit_info = api_service.get_current_rate_limit_info()
            
            return {
                "valid": True,
                "user_id": user_data.get("id"),
                "username": user_data.get("login"),
                "rate_limit_remaining": rate_limit_info.get("remaining"),
                "rate_limit_reset": rate_limit_info.get("reset_timestamp")
            }
        except HTTPException as e:
            return {
                "valid": False,
                "error": f"HTTP {e.status_code}",
                "message": e.detail
            }
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return {
                "valid": False,
                "error": "network_error",
                "message": str(e)
            }
    
    async def get_user_repositories(self, access_token: str, username: str, max_repos: int = 100) -> list:
        """Get user's public repositories using the optimized API service"""
        try:
            api_service = GitHubAPIService(access_token)
            
            # Check rate limit first
            rate_limit_status = await api_service.get_rate_limit_status()
            core_remaining = rate_limit_status.get("resources", {}).get("core", {}).get("remaining", 0)
            
            if core_remaining < 10:
                logger.warning(f"Low GitHub API rate limit: {core_remaining} requests remaining")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="GitHub API rate limit too low to fetch repositories"
                )
            
            # Fetch repositories
            repositories = await api_service.get_user_repositories(username, per_page=min(max_repos, 100))
            
            logger.info(f"Successfully fetched {len(repositories)} repositories for {username}")
            return repositories
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching repositories: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get repositories from GitHub"
            )