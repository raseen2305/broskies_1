"""
Scores API Router

Endpoints for querying user scores from the scores_comparison database.
These endpoints are optimized for HR to quickly find and sort developer profiles.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging
from datetime import datetime

from app.services.score_storage_service import get_score_storage_service
from app.db_connection import get_scores_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scores", tags=["scores"])


@router.get("/top-users")
async def get_top_users(
    limit: int = Query(100, ge=1, le=500, description="Number of users to return"),
    skip: int = Query(0, ge=0, description="Number of users to skip for pagination")
):
    """
    Get top users sorted by overall score.
    
    This endpoint is optimized for HR to quickly find top developers.
    
    Args:
        limit: Maximum number of users to return (1-500)
        skip: Number of users to skip for pagination
    
    Returns:
        List of users with their scores, sorted by overall_score descending
    """
    try:
        scores_db = await get_scores_database()
        if not scores_db:
            raise HTTPException(status_code=503, detail="Scores database not available")
        
        score_service = await get_score_storage_service(scores_db)
        users = await score_service.get_top_users(limit=limit, skip=skip)
        
        return {
            "total_returned": len(users),
            "limit": limit,
            "skip": skip,
            "users": users
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get top users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve top users: {str(e)}")


@router.get("/user/{username}")
async def get_user_scores(username: str):
    """
    Get detailed scores for a specific user.
    
    Args:
        username: GitHub username
    
    Returns:
        User score document with overall score, flagship repos, and significant repos
    """
    try:
        scores_db = await get_scores_database()
        if not scores_db:
            raise HTTPException(status_code=503, detail="Scores database not available")
        
        score_service = await get_score_storage_service(scores_db)
        user_scores = await score_service.get_user_scores(username)
        
        if not user_scores:
            raise HTTPException(status_code=404, detail=f"No scores found for user: {username}")
        
        return user_scores
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scores for user {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user scores: {str(e)}")


@router.get("/by-score-range")
async def get_users_by_score_range(
    min_score: float = Query(0, ge=0, le=100, description="Minimum overall score"),
    max_score: float = Query(100, ge=0, le=100, description="Maximum overall score"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of users to return")
):
    """
    Get users within a specific score range.
    
    Useful for HR to find developers within a specific skill level.
    
    Args:
        min_score: Minimum overall score (0-100)
        max_score: Maximum overall score (0-100)
        limit: Maximum number of users to return
    
    Returns:
        List of users within the score range, sorted by score descending
    """
    try:
        if min_score > max_score:
            raise HTTPException(status_code=400, detail="min_score cannot be greater than max_score")
        
        scores_db = await get_scores_database()
        if not scores_db:
            raise HTTPException(status_code=503, detail="Scores database not available")
        
        score_service = await get_score_storage_service(scores_db)
        users = await score_service.get_users_by_score_range(
            min_score=min_score,
            max_score=max_score,
            limit=limit
        )
        
        return {
            "min_score": min_score,
            "max_score": max_score,
            "total_returned": len(users),
            "users": users
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get users by score range: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")


@router.get("/by-language/{language}")
async def get_users_by_language(
    language: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of users to return")
):
    """
    Get users who primarily use a specific programming language.
    
    Useful for HR to find developers with specific language expertise.
    
    Args:
        language: Programming language (e.g., "Python", "JavaScript", "TypeScript")
        limit: Maximum number of users to return
    
    Returns:
        List of users who primarily use the specified language, sorted by score descending
    """
    try:
        scores_db = await get_scores_database()
        if not scores_db:
            raise HTTPException(status_code=503, detail="Scores database not available")
        
        score_service = await get_score_storage_service(scores_db)
        users = await score_service.get_users_by_language(
            language=language,
            limit=limit
        )
        
        return {
            "language": language,
            "total_returned": len(users),
            "users": users
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get users by language: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")


@router.get("/statistics")
async def get_score_statistics():
    """
    Get overall statistics about stored scores.
    
    Returns statistics like:
    - Total number of users
    - Average overall score
    - Max/min scores
    - Total repositories analyzed
    
    Returns:
        Dictionary with statistics
    """
    try:
        scores_db = await get_scores_database()
        if not scores_db:
            raise HTTPException(status_code=503, detail="Scores database not available")
        
        score_service = await get_score_storage_service(scores_db)
        stats = await score_service.get_statistics()
        
        return {
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")


@router.delete("/user/{username}")
async def delete_user_scores(username: str):
    """
    Delete scores for a specific user.
    
    Args:
        username: GitHub username
    
    Returns:
        Success message
    """
    try:
        scores_db = await get_scores_database()
        if not scores_db:
            raise HTTPException(status_code=503, detail="Scores database not available")
        
        score_service = await get_score_storage_service(scores_db)
        success = await score_service.delete_user_scores(username)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"No scores found for user: {username}")
        
        return {
            "message": f"Successfully deleted scores for user: {username}",
            "username": username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete scores for user {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user scores: {str(e)}")


@router.get("/health")
async def scores_health_check():
    """Check if the scores database is accessible"""
    try:
        scores_db = await get_scores_database()
        if not scores_db:
            return {
                "healthy": False,
                "message": "Scores database not available"
            }
        
        # Try to get statistics as a health check
        score_service = await get_score_storage_service(scores_db)
        stats = await score_service.get_statistics()
        
        return {
            "healthy": True,
            "message": "Scores database is accessible",
            "total_users": stats.get("total_users", 0)
        }
        
    except Exception as e:
        logger.error(f"Scores health check failed: {e}")
        return {
            "healthy": False,
            "message": f"Health check failed: {str(e)}"
        }
