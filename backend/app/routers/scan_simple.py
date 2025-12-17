"""
Simple scan endpoint for testing without comprehensive analysis
"""

from fastapi import APIRouter, HTTPException, status
import logging
import os
from datetime import datetime

from app.services.github_scanner import GitHubScanner

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/scan-simple/{username}")
async def scan_simple_user(username: str):
    """Simple scan without comprehensive analysis for testing"""
    try:
        logger.info(f"Starting simple scan for user: {username}")
        
        # Get GitHub token
        github_token = os.getenv("GITHUB_TOKEN", "")
        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No GitHub token available"
            )
        
        # Initialize basic scanner
        scanner = GitHubScanner(github_token)
        
        # Get basic user info
        user_info = await scanner.get_user_info(username)
        
        # Get repositories (limited)
        repositories = await scanner.fetch_user_repositories(username, include_forks=False, max_repos=10)
        
        # Simple response
        result = {
            "userId": f"external_{username}",
            "username": username,
            "userInfo": user_info,
            "repositoryCount": len(repositories),
            "repositories": repositories[:5],  # First 5 repos
            "scanDate": datetime.utcnow().isoformat(),
            "scanType": "simple"
        }
        
        logger.info(f"Simple scan completed for {username}")
        return result
        
    except Exception as e:
        logger.error(f"Simple scan failed for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simple scan failed: {str(e)}"
        )