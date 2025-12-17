"""
Simplified Ranking Service - Uses single user_rankings collection
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SimpleRankingService:
    """Simplified service for calculating rankings using single collection"""
    
    def __init__(self, database):
        self.db = database
    
    async def calculate_rankings_for_user(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate both regional and university rankings for a user
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with success status and ranking info
        """
        try:
            # Get user's ranking document
            user_ranking = await self.db.user_rankings.find_one({"user_id": user_id})
            
            if not user_ranking:
                return {
                    "success": False,
                    "error": "User ranking document not found",
                    "error_code": "NO_RANKING_DOC"
                }
            
            region = user_ranking.get("region")
            university_short = user_ranking.get("university_short")
            user_score = user_ranking.get("overall_score", 0)
            
            results = {
                "success": True,
                "user_id": user_id,
                "regional_updated": False,
                "university_updated": False
            }
            
            # Calculate regional ranking
            if region:
                regional_result = await self._calculate_regional_ranking(user_id, region, user_score)
                results["regional_updated"] = regional_result["success"]
                results["regional_ranking"] = regional_result.get("ranking")
            
            # Calculate university ranking
            if university_short:
                university_result = await self._calculate_university_ranking(user_id, university_short, user_score)
                results["university_updated"] = university_result["success"]
                results["university_ranking"] = university_result.get("ranking")
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating rankings for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "CALCULATION_ERROR"
            }
    
    async def _calculate_regional_ranking(self, user_id: str, region: str, user_score: float) -> Dict[str, Any]:
        """Calculate regional ranking for a user"""
        try:
            # Get all users in the same region, sorted by score descending
            users_in_region = await self.db.user_rankings.find(
                {"region": region, "overall_score": {"$ne": None}}
            ).sort("overall_score", -1).to_list(None)
            
            if not users_in_region:
                return {"success": False, "error": "No users in region"}
            
            total_users = len(users_in_region)
            
            # Find user's rank
            rank = None
            for idx, user in enumerate(users_in_region):
                if user["user_id"] == user_id:
                    rank = idx + 1
                    break
            
            if rank is None:
                return {"success": False, "error": "User not found in region"}
            
            # Calculate percentile (higher is better)
            percentile = ((total_users - rank) / total_users) * 100
            
            # Update user's regional ranking in the same document
            await self.db.user_rankings.update_one(
                {"user_id": user_id},
                {"$set": {
                    "regional_rank": rank,
                    "regional_total_users": total_users,
                    "regional_percentile": round(percentile, 1),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            logger.info(f"Updated regional ranking for user {user_id}: rank {rank}/{total_users}, percentile {percentile:.1f}%")
            
            return {
                "success": True,
                "ranking": {
                    "rank": rank,
                    "total_users": total_users,
                    "percentile": round(percentile, 1),
                    "region": region
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating regional ranking: {e}")
            return {"success": False, "error": str(e)}
    
    async def _calculate_university_ranking(self, user_id: str, university_short: str, user_score: float) -> Dict[str, Any]:
        """Calculate university ranking for a user"""
        try:
            # Get all users in the same university, sorted by score descending
            users_in_university = await self.db.user_rankings.find(
                {"university_short": university_short, "overall_score": {"$ne": None}}
            ).sort("overall_score", -1).to_list(None)
            
            if not users_in_university:
                return {"success": False, "error": "No users in university"}
            
            total_users = len(users_in_university)
            
            # Find user's rank
            rank = None
            for idx, user in enumerate(users_in_university):
                if user["user_id"] == user_id:
                    rank = idx + 1
                    break
            
            if rank is None:
                return {"success": False, "error": "User not found in university"}
            
            # Calculate percentile (higher is better)
            percentile = ((total_users - rank) / total_users) * 100
            
            # Update user's university ranking in the same document
            await self.db.user_rankings.update_one(
                {"user_id": user_id},
                {"$set": {
                    "university_rank": rank,
                    "university_total_users": total_users,
                    "university_percentile": round(percentile, 1),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            logger.info(f"Updated university ranking for user {user_id}: rank {rank}/{total_users}, percentile {percentile:.1f}%")
            
            return {
                "success": True,
                "ranking": {
                    "rank": rank,
                    "total_users": total_users,
                    "percentile": round(percentile, 1),
                    "university": university_short
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating university ranking: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_rankings(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's rankings from user_rankings collection
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with ranking information
        """
        try:
            ranking = await self.db.user_rankings.find_one({"user_id": user_id})
            
            if not ranking:
                return {
                    "success": False,
                    "error": "No ranking data found",
                    "error_code": "NO_RANKING_DATA"
                }
            
            return {
                "success": True,
                "overall_score": ranking.get("overall_score"),
                "regional": {
                    "rank": ranking.get("regional_rank"),
                    "total_users": ranking.get("regional_total_users"),
                    "percentile": ranking.get("regional_percentile"),
                    "region": ranking.get("region")
                } if ranking.get("regional_rank") else None,
                "university": {
                    "rank": ranking.get("university_rank"),
                    "total_users": ranking.get("university_total_users"),
                    "percentile": ranking.get("university_percentile"),
                    "university": ranking.get("university")
                } if ranking.get("university_rank") else None
            }
            
        except Exception as e:
            logger.error(f"Error getting rankings for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "GET_ERROR"
            }
