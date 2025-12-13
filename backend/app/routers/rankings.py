"""
Rankings API Endpoints for Regional and University Comparisons
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.core.security import get_current_user_token
from app.services.ranking_service import RankingService
from app.database import get_database, Collections

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status")
async def get_ranking_status(
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Get ranking calculation status for the current user
    
    Returns:
        Dictionary with ranking availability and calculation status
    """
    try:
        # Get database connection
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Use RankingService to check ranking status
        ranking_service = RankingService(db)
        rankings = await ranking_service.get_user_rankings(user_id)
        
        regional_ranking = rankings.get("regional_ranking")
        university_ranking = rankings.get("university_ranking")
        
        # First check if user has completed their profile (regardless of data joining)
        profile_doc = await db[Collections.INTERNAL_USERS_PROFILE].find_one({
            "user_id": user_id,
            "profile_completed": True
        })
        
        profile_completed = profile_doc is not None
        
        # Check if user has complete profile data (profile + scan data)
        joined_users = await ranking_service.get_joined_user_data({"user_id": user_id})
        has_complete_profile = len(joined_users) > 0
        
        # Determine ranking status
        if regional_ranking or university_ranking:
            ranking_status = "available"
        elif profile_completed and has_complete_profile:
            ranking_status = "calculating"
        elif profile_completed and not has_complete_profile:
            ranking_status = "pending_scan"
        else:
            ranking_status = "pending_profile"
        
        status_info = {
            "user_id": user_id,
            "profile_completed": profile_completed,
            "has_complete_profile": has_complete_profile,
            "has_regional_ranking": regional_ranking is not None,
            "has_university_ranking": university_ranking is not None,
            "ranking_status": ranking_status
        }
        
        # Add profile info if available
        if has_complete_profile and joined_users:
            user_data = joined_users[0]
            status_info["profile_info"] = {
                "name": user_data.get("name"),
                "university": user_data.get("university_short"),
                "district": user_data.get("district"),
                "overall_score": user_data.get("overall_score")
            }
        elif profile_completed and profile_doc:
            # Show basic profile info even if scan data is missing
            status_info["profile_info"] = {
                "name": profile_doc.get("full_name"),
                "university": profile_doc.get("university_short"),
                "district": profile_doc.get("district"),
                "overall_score": None
            }
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ranking status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ranking status: {str(e)}"
        )


@router.get("")
async def get_rankings(
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Get both regional and university rankings for the current user
    
    Returns:
        Dictionary with regional and university ranking information including complete profile data
    """
    try:
        # Get database connection
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Use RankingService to get rankings from correct collections
        ranking_service = RankingService(db)
        rankings = await ranking_service.get_user_rankings(user_id)
        
        regional_ranking = rankings.get("regional_ranking")
        university_ranking = rankings.get("university_ranking")
        
        if not regional_ranking and not university_ranking:
            # First check if user has completed their profile (regardless of data joining)
            profile_doc = await db[Collections.INTERNAL_USERS_PROFILE].find_one({
                "user_id": user_id,
                "profile_completed": True
            })
            
            if profile_doc:
                # User has completed profile, check if they have scan data
                joined_users = await ranking_service.get_joined_user_data({"user_id": user_id})
                
                if len(joined_users) > 0:
                    # User has complete profile AND scan data, trigger ranking calculation
                    logger.info(f"User {user_id} has complete data, triggering ranking calculation")
                    
                    # Trigger ranking calculation in the background
                    try:
                        result = await ranking_service.update_all_rankings_for_user(user_id)
                        if result["success"]:
                            logger.info(f"Rankings calculated successfully for user {user_id}")
                            # Re-fetch rankings after calculation
                            updated_rankings = await ranking_service.get_user_rankings(user_id)
                            if updated_rankings.get("regional_ranking") or updated_rankings.get("university_ranking"):
                                # Rankings are now available, redirect to the main rankings logic
                                regional_ranking = updated_rankings.get("regional_ranking")
                                university_ranking = updated_rankings.get("university_ranking")
                                
                                # Construct response with complete profile data
                                response = {
                                    "status": "available",
                                    "message": "Rankings available",
                                    "has_complete_profile": True
                                }
                                
                                if regional_ranking:
                                     response["regional_percentile_text"] = f"Top {regional_ranking.get('percentile', 0):.1f}% in {regional_ranking.get('district', 'your region')}"
                                     response["regional_ranking"] = {
                                         "rank_in_region": regional_ranking.get("rank"),
                                         "total_users_in_region": regional_ranking.get("total_users"),
                                         "percentile_region": regional_ranking.get("percentile"),
                                         "overall_score": regional_ranking.get("overall_score"),
                                         "name": regional_ranking.get("name"),
                                         "district": regional_ranking.get("district"),
                                         "state": regional_ranking.get("state"),
                                         "region": regional_ranking.get("region"),
                                         "avg_score": regional_ranking.get("avg_score"),
                                         "median_score": regional_ranking.get("median_score")
                                     }
                                     
                                if university_ranking:
                                     response["university_percentile_text"] = f"Top {university_ranking.get('percentile', 0):.1f}% in {university_ranking.get('university_short', 'your university')}"
                                     response["university_ranking"] = {
                                         "rank_in_university": university_ranking.get("rank"),
                                         "total_users_in_university": university_ranking.get("total_users"),
                                         "percentile_university": university_ranking.get("percentile"),
                                         "overall_score": university_ranking.get("overall_score"),
                                         "name": university_ranking.get("name"),
                                         "university": university_ranking.get("university"),
                                         "university_short": university_ranking.get("university_short"),
                                         "avg_score": university_ranking.get("avg_score"),
                                         "median_score": university_ranking.get("median_score")
                                     }
                                
                                return response
                        else:
                            logger.warning(f"Failed to calculate rankings for user {user_id}: {result.get('error')}")
                    except Exception as e:
                        logger.error(f"Error calculating rankings for user {user_id}: {e}")
                    
                    # If calculation failed or is still in progress, return calculating status
                    return {
                        "status": "calculating",
                        "message": "Your rankings are being calculated. This may take a few moments.",
                        "has_complete_profile": True,
                        "profile_completed": True,
                        "regional_ranking": None,
                        "university_ranking": None
                    }
                else:
                    # User has completed profile but no scan data or data linking issue
                    return {
                        "status": "pending_scan",
                        "message": "Please complete a repository scan to see your rankings.",
                        "has_complete_profile": True,
                        "profile_completed": True,
                        "regional_ranking": None,
                        "university_ranking": None
                    }
            else:
                # User has not completed profile setup
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Rankings not available. Please complete your profile setup first."
                )
        
        # Construct response with complete profile data
        response = {
            "status": "available",
            "message": "Rankings available",
            "has_complete_profile": True
        }
        
        if regional_ranking:
             response["regional_percentile_text"] = f"Top {regional_ranking.get('percentile', 0):.1f}% in {regional_ranking.get('district', 'your region')}"
             response["regional_ranking"] = {
                 "rank_in_region": regional_ranking.get("rank"),
                 "total_users_in_region": regional_ranking.get("total_users"),
                 "percentile_region": regional_ranking.get("percentile"),
                 "overall_score": regional_ranking.get("overall_score"),
                 "name": regional_ranking.get("name"),
                 "district": regional_ranking.get("district"),
                 "state": regional_ranking.get("state"),
                 "region": regional_ranking.get("region"),
                 "avg_score": regional_ranking.get("avg_score"),
                 "median_score": regional_ranking.get("median_score")
             }
             
        if university_ranking:
             response["university_percentile_text"] = f"Top {university_ranking.get('percentile', 0):.1f}% in {university_ranking.get('university_short', 'your university')}"
             response["university_ranking"] = {
                 "rank_in_university": university_ranking.get("rank"),
                 "total_users_in_university": university_ranking.get("total_users"),
                 "percentile_university": university_ranking.get("percentile"),
                 "overall_score": university_ranking.get("overall_score"),
                 "name": university_ranking.get("name"),
                 "university": university_ranking.get("university"),
                 "university_short": university_ranking.get("university_short"),
                 "avg_score": university_ranking.get("avg_score"),
                 "median_score": university_ranking.get("median_score")
             }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rankings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rankings: {str(e)}"
        )


@router.get("/detailed")
async def get_detailed_rankings(
    type: str = Query(..., description="Type of ranking: 'regional' or 'university'"),
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Get detailed ranking statistics for regional or university comparison
    
    Args:
        type: Type of ranking ('regional' or 'university')
    
    Returns:
        Detailed ranking statistics with trend data
    """
    try:
        # Validate type parameter
        if type not in ["regional", "university"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Type must be 'regional' or 'university'"
            )
        
        # Get database connection
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Get ranking service
        ranking_service = RankingService(db)
        
        # Get ranking based on type
        if type == "regional":
            ranking = await ranking_service.get_regional_ranking(user_id)
            if not ranking:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Regional ranking not found"
                )
            
            comparison_context = ranking["district"]
            total_users = ranking.get("total_users")
            
        else:  # university
            ranking = await ranking_service.get_university_ranking(user_id)
            if not ranking:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="University ranking not found"
                )
            
            comparison_context = ranking["university_short"]
            total_users = ranking.get("total_users")
        
        # Format detailed response with complete profile data
        response = {
            "rank_position": ranking["rank"],
            "total_users": total_users,
            "percentile_score": ranking["percentile"],
            "overall_score": ranking["overall_score"],
            "name": ranking["name"],
            "github_username": ranking["github_username"],
            "comparison_context": comparison_context,
            "avg_score": ranking.get("avg_score"),
            "median_score": ranking.get("median_score"),
            "last_updated": ranking.get("updated_at", datetime.utcnow()).isoformat(),
            "trend_data": []  # TODO: Implement historical trend tracking
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


@router.post("/calculate")
async def calculate_rankings(
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Manually trigger ranking calculations for the current user
    
    Returns:
        Calculation result with updated rankings
    """
    try:
        # Get database connection
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Update rankings using RankingService
        ranking_service = RankingService(db)
        result = await ranking_service.update_all_rankings_for_user(user_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to calculate rankings")
            )
        
        return {
            "success": True,
            "message": "Rankings calculated successfully",
            "regional_updated": result.get("regional_update", {}).get("success", False) if result.get("regional_update") else False,
            "university_updated": result.get("university_update", {}).get("success", False) if result.get("university_update") else False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate rankings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate rankings: {str(e)}"
        )


@router.post("/sync-score")
async def sync_score(
    acid_score: Optional[float] = Query(None, description="Optional ACID score (fetched automatically if not provided)"),
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Sync user's ACID score and trigger ranking updates
    
    Args:
        acid_score: Optional ACID score (if not provided, fetches from user_overall_details)
    
    Returns:
        Sync result with updated rankings
    """
    try:
        # Get database connection
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Validate acid_score if provided
        if acid_score is not None and (acid_score < 0 or acid_score > 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ACID score must be between 0 and 100"
            )
        
        # Update rankings using RankingService
        ranking_service = RankingService(db)
        result = await ranking_service.update_all_rankings_for_user(user_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to update rankings")
            )
        
        return {
            "success": True,
            "message": "Rankings updated successfully",
            "regional_updated": result.get("regional_update", {}).get("success", False) if result.get("regional_update") else False,
            "university_updated": result.get("university_update", {}).get("success", False) if result.get("university_update") else False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync score: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync score: {str(e)}"
        )


@router.get("/leaderboard/regional")
async def get_regional_leaderboard(
    limit: int = Query(10, ge=1, le=50, description="Number of top users to return"),
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Get regional leaderboard showing top users in the same region
    
    Args:
        limit: Number of top users to return (1-50)
    
    Returns:
        List of top users in the region
    """
    try:
        # Get database connection
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Get user's district from joined data using RankingService
        ranking_service = RankingService(db)
        
        # Get user's regional ranking to find their district
        user_regional_ranking = await ranking_service.get_regional_ranking(user_id)
        if not user_regional_ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User regional ranking not found. Please complete profile setup and scan first."
            )
        
        district = user_regional_ranking.get("district")
        if not district:
             raise HTTPException(status_code=400, detail="User district not set")

        # Get leaderboard
        leaderboard = await ranking_service.get_regional_leaderboard(district, limit)
        
        # Anonymize user data (remove user_id, keep only rank and score)
        anonymized_leaderboard = [
            {
                "rank_position": entry["rank"],
                "overall_score": entry["overall_score"],
                "percentile_score": entry["percentile"],
                "is_current_user": entry["user_id"] == user_id
            }
            for entry in leaderboard
        ]
        
        return {
            "district": district,
            "state": user_regional_ranking.get("state"),
            "region": user_regional_ranking.get("region"),
            "leaderboard": anonymized_leaderboard,
            "total_entries": len(anonymized_leaderboard)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get regional leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get regional leaderboard: {str(e)}"
        )


@router.get("/leaderboard/university")
async def get_university_leaderboard(
    limit: int = Query(10, ge=1, le=50, description="Number of top users to return"),
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Get university leaderboard showing top users in the same university
    
    Args:
        limit: Number of top users to return (1-50)
    
    Returns:
        List of top users in the university
    """
    try:
        # Get database connection
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Get user's university from joined data using RankingService
        ranking_service = RankingService(db)
        
        # Get user's university ranking to find their university
        user_university_ranking = await ranking_service.get_university_ranking(user_id)
        if not user_university_ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User university ranking not found. Please complete profile setup and scan first."
            )
        
        university_short = user_university_ranking.get("university_short")
        if not university_short:
             raise HTTPException(status_code=400, detail="User university not set")

        # Get leaderboard
        leaderboard = await ranking_service.get_university_leaderboard(university_short, limit)
        
        # Anonymize user data (remove user_id, keep only rank and score)
        anonymized_leaderboard = [
            {
                "rank_position": entry["rank"],
                "overall_score": entry["overall_score"],
                "percentile_score": entry["percentile"],
                "is_current_user": entry["user_id"] == user_id
            }
            for entry in leaderboard
        ]
        
        return {
            "university_short": university_short,
            "university": user_university_ranking.get("university"),
            "leaderboard": anonymized_leaderboard,
            "total_entries": len(anonymized_leaderboard)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get university leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get university leaderboard: {str(e)}"
        )


@router.get("/stats/regional")
async def get_regional_stats(
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Get regional statistics and insights
    
    Returns:
        Regional statistics including distribution and averages
    """
    try:
        # Get database connection
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Get user's district using RankingService
        ranking_service = RankingService(db)
        user_regional_ranking = await ranking_service.get_regional_ranking(user_id)
        
        if not user_regional_ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Regional ranking not found"
            )
        
        district = user_regional_ranking.get("district")
        
        # Get all scores in district
        regional_scores = await db[Collections.REGIONAL_RANKINGS].find({"district": district}).to_list(None)
        
        if not regional_scores:
            return {
                "district": district,
                "state": user_regional_ranking.get("state"),
                "region": user_regional_ranking.get("region"),
                "total_users": 0,
                "average_score": 0,
                "median_score": 0,
                "min_score": 0,
                "max_score": 0
            }
        
        scores = [s["overall_score"] for s in regional_scores]
        scores.sort()
        
        # Calculate statistics
        total_users = len(scores)
        average_score = sum(scores) / total_users
        median_score = scores[total_users // 2] if total_users > 0 else 0
        min_score = min(scores)
        max_score = max(scores)
        
        return {
            "district": district,
            "state": user_regional_ranking.get("state"),
            "region": user_regional_ranking.get("region"),
            "total_users": total_users,
            "average_score": round(average_score, 2),
            "median_score": round(median_score, 2),
            "min_score": round(min_score, 2),
            "max_score": round(max_score, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get regional stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get regional stats: {str(e)}"
        )


@router.get("/stats/university")
async def get_university_stats(
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Get university statistics and insights
    
    Returns:
        University statistics including distribution and averages
    """
    try:
        # Get database connection
        db = await get_database()
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Get user's university using RankingService
        ranking_service = RankingService(db)
        user_university_ranking = await ranking_service.get_university_ranking(user_id)
        
        if not user_university_ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="University ranking not found"
            )
        
        university_short = user_university_ranking.get("university_short")
        
        # Get all scores in university
        university_scores = await db[Collections.UNIVERSITY_RANKINGS].find(
            {"university_short": university_short}
        ).to_list(None)
        
        if not university_scores:
            return {
                "university_short": university_short,
                "university": user_university_ranking.get("university"),
                "total_users": 0,
                "average_score": 0,
                "median_score": 0,
                "min_score": 0,
                "max_score": 0
            }
        
        scores = [s["overall_score"] for s in university_scores]
        scores.sort()
        
        # Calculate statistics
        total_users = len(scores)
        average_score = sum(scores) / total_users
        median_score = scores[total_users // 2] if total_users > 0 else 0
        min_score = min(scores)
        max_score = max(scores)
        
        return {
            "university_short": university_short,
            "university": user_university_ranking.get("university"),
            "total_users": total_users,
            "average_score": round(average_score, 2),
            "median_score": round(median_score, 2),
            "min_score": round(min_score, 2),
            "max_score": round(max_score, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get university stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get university stats: {str(e)}"
        )


@router.get("/check/{github_username}")
async def check_ranking_availability(
    github_username: str
):
    """
    Check if ranking data is available for a GitHub username (public endpoint for external scans)
    """
    try:
        # Get database connection
        db = await get_database()
        
        if db is None:
            return {
                "has_ranking_data": False,
                "message": "Database connection unavailable"
            }
        
        logger.info(f"Checking ranking availability for GitHub username: {github_username}")
        
        # Search for user by github_username in ranking collections directly
        # since they contain the joined data we need
        
        reg_ranking = await db[Collections.REGIONAL_RANKINGS].find_one(
            {"github_username": {"$regex": f"^{github_username}$", "$options": "i"}}
        )
        uni_ranking = await db[Collections.UNIVERSITY_RANKINGS].find_one(
            {"github_username": {"$regex": f"^{github_username}$", "$options": "i"}}
        )

        has_regional = reg_ranking is not None
        has_university = uni_ranking is not None
        
        if not has_regional and not has_university:
            return {
                "has_ranking_data": False,
                "message": "Rankings are being calculated or user not found."
            }
        
        # Use data from whichever ranking is available for profile info
        profile_source = reg_ranking if has_regional else uni_ranking
        
        response = {
            "has_ranking_data": True,
            "github_username": github_username,
            "profile": {
                "full_name": profile_source.get("name"),
                "university": profile_source.get("university") if has_university else None,
                "university_short": profile_source.get("university_short") if has_university else None,
                "district": profile_source.get("district") if has_regional else None,
                "state": profile_source.get("state"),
                "region": profile_source.get("region") if has_regional else None
            }
        }
        
        if has_regional:
            response["regional_ranking"] = {
                "rank_in_region": reg_ranking.get("rank"),
                "total_users_in_region": reg_ranking.get("total_users"),
                "percentile_region": reg_ranking.get("percentile"),
                "district": reg_ranking.get("district"),
                "state": reg_ranking.get("state"),
                "region": reg_ranking.get("region"),
                "overall_score": reg_ranking.get("overall_score")
            }
            response["regional_percentile_text"] = f"Top {reg_ranking.get('percentile', 0):.1f}% in {reg_ranking.get('district')}"
            
        if has_university:
            response["university_ranking"] = {
                "rank_in_university": uni_ranking.get("rank"),
                "total_users_in_university": uni_ranking.get("total_users"),
                "percentile_university": uni_ranking.get("percentile"),
                "university": uni_ranking.get("university"),
                "university_short": uni_ranking.get("university_short"),
                "overall_score": uni_ranking.get("overall_score")
            }
            response["university_percentile_text"] = f"Top {uni_ranking.get('percentile', 0):.1f}% in {uni_ranking.get('university_short')}"

        return response
        
    except Exception as e:
        logger.error(f"Failed to check ranking availability for {github_username}: {e}")
        return {
            "has_ranking_data": False,
            "message": f"Error checking ranking data: {str(e)}"
        }
