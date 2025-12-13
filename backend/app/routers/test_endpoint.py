"""
Test endpoint for debugging
"""

from fastapi import APIRouter, HTTPException
import logging
import os
from github import Github

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"status": "ok", "message": "Test endpoint working"}

@router.get("/test-github-token")
async def test_github_token():
    """Test if GitHub token is available"""
    github_token = os.getenv("GITHUB_TOKEN", "")
    return {
        "token_available": bool(github_token),
        "token_length": len(github_token) if github_token else 0
    }

@router.get("/test-github-api/{username}")
async def test_github_api(username: str):
    """Test basic GitHub API call"""
    try:
        github_token = os.getenv("GITHUB_TOKEN", "")
        if not github_token:
            return {"error": "No GitHub token"}
        
        github = Github(github_token)
        user = github.get_user(username)
        
        return {
            "username": user.login,
            "name": user.name,
            "public_repos": user.public_repos,
            "followers": user.followers
        }
    except Exception as e:
        return {"error": str(e)}