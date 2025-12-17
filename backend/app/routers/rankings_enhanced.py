"""
Enhanced Rankings API with detailed statistics and leaderboards
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.core.security import get_current_user_token
from app.services.enhanced_ranking_service import EnhancedRankingService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check for enhanced rankings API"""
    return {
        "status": "healthy",
        "message": "Enhanced rankings API is operational",
        "version": "2.0"
    }


@router.get("/debug/auth")
async def debug_auth(current_user_token: dict = Depends(get_current_user_token)):
    """Debug endpoint to verify authentication is working"""
    return {
        "authenticated": True,
        "user_id": current_user_token.get("user_id"),
        "token_keys": list(current_user_token.keys()),
        "message": "Authentication is working correctly"
    }


@router.get("/detailed")
async def get_detailed_rankings(
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Get comprehensive ranking information for the current user
    
    Returns:
        Detailed ranking data with statistics and position
    """
    try:
        from app.db_connection import get_database
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Get user's ranking data
        ranking = await db.user_rankings.find_one({"user_id": user_id})
        
        if not ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rankings not available. Please complete a repository scan first."
            )
        
        # Check if rankings have been calculated
        if not ranking.get("regional_rank") and not ranking.get("university_rank"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rankings are being calculated. Please wait a moment and try again."
            )
        
        # Prepare response
        response = {
            "user_info": {
                "github_username": ranking.get("github_username"),
                "name": ranking.get("name"),
                "overall_score": ranking.get("overall_score", 0)
            },
            "regional_ranking": None,
            "university_ranking": None,
            "last_scan_date": ranking.get("last_scan_date"),
            "updated_at": ranking.get("updated_at")
        }
        
        # Add regional ranking if available
        if ranking.get("regional_rank"):
            response["regional_ranking"] = {
                "rank": ranking.get("regional_rank"),
                "total_users": ranking.get("regional_total_users"),
                "percentile": ranking.get("regional_percentile"),  # Top X%
                "percentile_exact": ranking.get("regional_percentile_exact"),  # Exact percentile
                "region": ranking.get("region"),
                "state": ranking.get("state"),
                "avg_score": ranking.get("regional_avg_score"),
                "median_score": ranking.get("regional_median_score"),
                "display_text": f"Top {ranking.get('regional_percentile', 0):.1f}% in {ranking.get('region', 'Unknown')}"
            }
        
        # Add university ranking if available
        if ranking.get("university_rank"):
            response["university_ranking"] = {
                "rank": ranking.get("university_rank"),
                "total_users": ranking.get("university_total_users"),
                "percentile": ranking.get("university_percentile"),  # Top X%
                "percentile_exact": ranking.get("university_percentile_exact"),  # Exact percentile
                "university": ranking.get("university"),
                "university_short": ranking.get("university_short"),
                "avg_score": ranking.get("university_avg_score"),
                "median_score": ranking.get("university_median_score"),
                "display_text": f"Top {ranking.get('university_percentile', 0):.1f}% in {ranking.get('university', 'Unknown')}"
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get detailed rankings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detailed rankings: {str(e)}"
        )


@router.get("/leaderboard")
async def get_leaderboard(
    type: str = Query(..., description="Type: 'regional' or 'university'"),
    limit: int = Query(10, ge=1, le=50, description="Number of top users"),
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Get leaderboard for region or university
    
    Args:
        type: 'regional' or 'university'
        limit: Number of top users to return
    
    Returns:
        Leaderboard with top users and current user's position
    """
    try:
        if type not in ["regional", "university"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Type must be 'regional' or 'university'"
            )
        
        from app.db_connection import get_database
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Get user's profile
        ranking = await db.user_rankings.find_one({"user_id": user_id})
        if not ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Get identifier
        if type == "regional":
            identifier = ranking.get("district")  # Use district for regional leaderboard
            logger.info(f"🔍 Regional leaderboard request - User: {user_id}, District: {identifier}")
            logger.info(f"🔍 User ranking document fields: {list(ranking.keys())}")
            if not identifier:
                logger.warning(f"⚠️ District not set for user {user_id}")
                logger.warning(f"⚠️ Available fields: region={ranking.get('region')}, state={ranking.get('state')}, district={ranking.get('district')}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="District not set in profile"
                )
        else:
            identifier = ranking.get("university_short")
            if not identifier:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="University not set in profile"
                )
        
        # Get leaderboard
        ranking_service = EnhancedRankingService(db)
        leaderboard = await ranking_service.get_leaderboard(
            type, 
            identifier, 
            limit,
            include_user=user_id
        )
        
        # Anonymize and mark current user
        anonymized_leaderboard = []
        current_user_entry = None
        
        for entry in leaderboard:
            is_current = entry["user_id"] == user_id
            
            anonymized_entry = {
                "rank": entry["rank"],
                "score": entry["overall_score"],
                "percentile": entry["percentile"],
                "is_current_user": is_current
            }
            
            # Only show name for current user
            if is_current:
                anonymized_entry["name"] = entry.get("name")
                anonymized_entry["github_username"] = entry.get("github_username")
                current_user_entry = anonymized_entry
            
            anonymized_leaderboard.append(anonymized_entry)
        
        return {
            "type": type,
            "identifier": identifier,
            "leaderboard": anonymized_leaderboard[:limit],  # Top N only
            "current_user": current_user_entry,
            "total_entries": len(anonymized_leaderboard)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get leaderboard: {str(e)}"
        )


@router.get("/statistics")
async def get_ranking_statistics(
    type: str = Query(..., description="Type: 'regional' or 'university'"),
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Get statistical summary for region or university
    
    Args:
        type: 'regional' or 'university'
    
    Returns:
        Statistical summary with distribution
    """
    try:
        if type not in ["regional", "university"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Type must be 'regional' or 'university'"
            )
        
        from app.db_connection import get_database
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Get user's profile
        ranking = await db.user_rankings.find_one({"user_id": user_id})
        if not ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Get identifier
        if type == "regional":
            identifier = ranking.get("region")
        else:
            identifier = ranking.get("university_short")
        
        if not identifier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{type.capitalize()} not set in profile"
            )
        
        # Get statistics
        ranking_service = EnhancedRankingService(db)
        stats = await ranking_service.get_ranking_stats(type, identifier)
        
        return {
            "type": type,
            "identifier": identifier,
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/trigger-update")
async def trigger_ranking_update(
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Manually trigger ranking update for current user's groups
    
    Returns:
        Update results
    """
    try:
        from app.db_connection import get_database
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Trigger update
        ranking_service = EnhancedRankingService(db)
        result = await ranking_service.update_rankings_for_user(user_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to update rankings")
            )
        
        return {
            "success": True,
            "message": "Rankings updated successfully",
            "regional_updated": result.get("regional_updated", False),
            "university_updated": result.get("university_updated", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger ranking update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger ranking update: {str(e)}"
        )


@router.get("/batch-status")
async def get_batch_update_status():
    """
    Get status of last batch ranking update
    
    Returns:
        Batch update status and timing
    """
    try:
        from app.db_connection import get_database
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        # Get latest batch update record (if exists)
        # This would require a batch_update_logs collection
        # For now, return placeholder
        
        return {
            "last_update": None,
            "next_scheduled": None,
            "status": "No batch updates recorded yet"
        }
        
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch status: {str(e)}"
        )
