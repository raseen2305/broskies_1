"""
Debug endpoints to list and find users
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
import logging

from app.core.security import get_current_user_token
from app.database import get_database, Collections

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/list-all")
async def list_all_users(
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    List all users in the database (first 20 from each collection)
    """
    try:
        db = await get_database()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        result = {}
        
        # List internal_users
        internal_users = await db[Collections.INTERNAL_USERS].find({}).limit(20).to_list(None)
        result["internal_users"] = {
            "count": await db[Collections.INTERNAL_USERS].count_documents({}),
            "sample": [
                {
                    "user_id": user.get('user_id'),
                    "username": user.get('username'),
                    "github_username": user.get('github_username'),
                    "overall_score": user.get('overall_score')
                }
                for user in internal_users
            ]
        }
        
        # List profile_users
        profile_users = await db[Collections.INTERNAL_USERS_PROFILE].find({}).limit(20).to_list(None)
        result["profile_users"] = {
            "count": await db[Collections.INTERNAL_USERS_PROFILE].count_documents({}),
            "sample": [
                {
                    "user_id": user.get('user_id'),
                    "github_username": user.get('github_username'),
                    "full_name": user.get('full_name'),
                    "profile_completed": user.get('profile_completed')
                }
                for user in profile_users
            ]
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List users endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )

@router.get("/search-raseen")
async def search_raseen_users(
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Search for any users containing 'raseen'
    """
    try:
        db = await get_database()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        result = {}
        
        # Search internal_users for raseen
        raseen_internal = await db[Collections.INTERNAL_USERS].find({
            "$or": [
                {"user_id": {"$regex": "raseen", "$options": "i"}},
                {"username": {"$regex": "raseen", "$options": "i"}},
                {"github_username": {"$regex": "raseen", "$options": "i"}}
            ]
        }).to_list(None)
        
        result["internal_users_with_raseen"] = [
            {
                "_id": str(user.get('_id')),
                "user_id": user.get('user_id'),
                "username": user.get('username'),
                "github_username": user.get('github_username'),
                "overall_score": user.get('overall_score'),
                "updated_at": str(user.get('updated_at'))
            }
            for user in raseen_internal
        ]
        
        # Search profile_users for raseen
        raseen_profile = await db[Collections.INTERNAL_USERS_PROFILE].find({
            "$or": [
                {"user_id": {"$regex": "raseen", "$options": "i"}},
                {"github_username": {"$regex": "raseen", "$options": "i"}},
                {"full_name": {"$regex": "raseen", "$options": "i"}}
            ]
        }).to_list(None)
        
        result["profile_users_with_raseen"] = [
            {
                "_id": str(user.get('_id')),
                "user_id": user.get('user_id'),
                "github_username": user.get('github_username'),
                "full_name": user.get('full_name'),
                "profile_completed": user.get('profile_completed'),
                "university": user.get('university'),
                "district": user.get('district')
            }
            for user in raseen_profile
        ]
        
        # Search rankings for raseen
        raseen_regional = await db[Collections.REGIONAL_RANKINGS].find({
            "$or": [
                {"user_id": {"$regex": "raseen", "$options": "i"}},
                {"github_username": {"$regex": "raseen", "$options": "i"}}
            ]
        }).to_list(None)
        
        result["regional_rankings_with_raseen"] = [
            {
                "_id": str(ranking.get('_id')),
                "user_id": ranking.get('user_id'),
                "github_username": ranking.get('github_username'),
                "rank": ranking.get('rank'),
                "overall_score": ranking.get('overall_score'),
                "district": ranking.get('district')
            }
            for ranking in raseen_regional
        ]
        
        raseen_university = await db[Collections.UNIVERSITY_RANKINGS].find({
            "$or": [
                {"user_id": {"$regex": "raseen", "$options": "i"}},
                {"github_username": {"$regex": "raseen", "$options": "i"}}
            ]
        }).to_list(None)
        
        result["university_rankings_with_raseen"] = [
            {
                "_id": str(ranking.get('_id')),
                "user_id": ranking.get('user_id'),
                "github_username": ranking.get('github_username'),
                "rank": ranking.get('rank'),
                "overall_score": ranking.get('overall_score'),
                "university_short": ranking.get('university_short')
            }
            for ranking in raseen_university
        ]
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search raseen endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search for raseen: {str(e)}"
        )