"""
Score synchronization service for keeping rankings up-to-date.
Handles syncing ACID scores from user_overall_details to ranking collections.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class ScoreSyncService:
    """Service for synchronizing user scores with ranking collections"""
    
    def __init__(self, database: AsyncIOMotorDatabase, ranking_service):
        self.db = database
        self.ranking_service = ranking_service
    
    async def sync_user_score(self, user_id: str) -> Dict[str, Any]:
        """
        Sync user's ACID score from user_overall_details to ranking collections
        
        This method:
        1. Fetches latest ACID score from user_overall_details
        2. Updates regional_scores collection
        3. Updates university_scores collection
        4. Triggers batch ranking updates for affected region and university
        5. Validates user has completed profile before syncing
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with sync results
        """
        try:
            logger.info(f"Starting score sync for user: {user_id}")
            
            # Step 1: Check if user has completed profile
            profile = await self.db.user_profiles.find_one({"user_id": user_id})
            
            if not profile:
                logger.warning(f"User {user_id} has no profile - cannot sync score")
                return {
                    "success": False,
                    "user_id": user_id,
                    "error": "User profile not found. Please complete your profile first.",
                    "error_code": "NO_PROFILE"
                }
            
            # Step 2: Fetch latest overall_score from analysis_states collection
            # First try to get from user profile's github_username
            github_username = profile.get("github_username")
            
            if not github_username:
                logger.warning(f"No github_username in profile for user {user_id}")
                return {
                    "success": False,
                    "user_id": user_id,
                    "error": "GitHub username not found in profile",
                    "error_code": "NO_GITHUB_USERNAME"
                }
            
            # Fetch from analysis_states
            analysis = await self.db.analysis_states.find_one({
                "username": github_username,
                "status": "completed"
            })
            
            if not analysis or not analysis.get("results"):
                logger.warning(f"No completed analysis found for user {github_username}")
                return {
                    "success": False,
                    "user_id": user_id,
                    "error": "No scan results found. Please scan your repositories first.",
                    "error_code": "NO_SCAN_RESULTS"
                }
            
            # Get overall_score from analysis results
            results = analysis.get("results", {})
            acid_score = results.get("overall_score", 0.0)
            
            # Fallback: Check for 'acid_score' if overall_score is 0
            if acid_score == 0:
                fallback_score = results.get("acid_score", 0.0)
                if isinstance(fallback_score, dict):
                    acid_score = fallback_score.get("overall", 0.0)
                elif isinstance(fallback_score, (int, float)):
                    acid_score = fallback_score
            
            if not self.ranking_service.validate_score(acid_score):
                logger.error(f"Invalid ACID score {acid_score} for user {user_id}")
                return {
                    "success": False,
                    "user_id": user_id,
                    "error": f"Invalid ACID score: {acid_score}",
                    "error_code": "INVALID_SCORE"
                }
            
            logger.info(f"Found ACID score {acid_score} for user {user_id}")
            
            # Extract profile information
            region = profile.get("region")
            university_short = profile.get("university_short")
            
            results = {
                "success": True,
                "user_id": user_id,
                "acid_score": acid_score,
                "regional_updated": False,
                "university_updated": False,
                "regional_ranking": None,
                "university_ranking": None
            }
            
            # Step 3: Update regional_scores collection
            if region:
                regional_result = await self._update_regional_score(
                    user_id, region, acid_score
                )
                results["regional_updated"] = regional_result["success"]
                
                # Step 4: Calculate rankings using simple ranking service
                from app.services.simple_ranking_service import SimpleRankingService
                simple_ranking = SimpleRankingService(self.db)
                
                ranking_result = await simple_ranking.calculate_rankings_for_user(user_id)
                
                if ranking_result.get("success"):
                    results["regional_updated"] = ranking_result.get("regional_updated", False)
                    results["university_updated"] = ranking_result.get("university_updated", False)
                    results["regional_ranking"] = ranking_result.get("regional_ranking")
                    results["university_ranking"] = ranking_result.get("university_ranking")
                else:
                    logger.warning(f"Ranking calculation failed: {ranking_result.get('error')}")
            
            logger.info(f"Score sync completed for user {user_id}: regional={results['regional_updated']}, university={results['university_updated']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error syncing score for user {user_id}: {e}", exc_info=True)
            return {
                "success": False,
                "user_id": user_id,
                "error": str(e),
                "error_code": "SYNC_ERROR"
            }
    
    async def _update_regional_score(
        self, 
        user_id: str, 
        region: str, 
        acid_score: float
    ) -> Dict[str, Any]:
        """
        Update or insert user's score in regional_scores collection
        
        Args:
            user_id: User identifier
            region: Region identifier
            acid_score: User's ACID score
        
        Returns:
            Dictionary with update result
        """
        try:
            result = await self.db.regional_scores.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "region": region,
                        "acid_score": acid_score,
                        "last_updated": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "user_id": user_id,
                        "rank_position": 0,
                        "total_users_in_region": 0,
                        "percentile_score": 0.0
                    }
                },
                upsert=True
            )
            
            return {
                "success": True,
                "matched": result.matched_count,
                "modified": result.modified_count,
                "upserted": result.upserted_id is not None
            }
            
        except Exception as e:
            logger.error(f"Error updating regional score for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_university_score(
        self, 
        user_id: str, 
        university_short: str, 
        acid_score: float
    ) -> Dict[str, Any]:
        """
        Update or insert user's score in university_scores collection
        
        Args:
            user_id: User identifier
            university_short: University short identifier
            acid_score: User's ACID score
        
        Returns:
            Dictionary with update result
        """
        try:
            result = await self.db.university_scores.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "university_short": university_short,
                        "acid_score": acid_score,
                        "last_updated": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "user_id": user_id,
                        "rank_position": 0,
                        "total_users_in_university": 0,
                        "percentile_score": 0.0
                    }
                },
                upsert=True
            )
            
            return {
                "success": True,
                "matched": result.matched_count,
                "modified": result.modified_count,
                "upserted": result.upserted_id is not None
            }
            
        except Exception as e:
            logger.error(f"Error updating university score for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def batch_sync_scores(self, user_ids: list[str]) -> Dict[str, Any]:
        """
        Sync scores for multiple users
        
        Args:
            user_ids: List of user identifiers
        
        Returns:
            Dictionary with batch sync results
        """
        results = {
            "total": len(user_ids),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for user_id in user_ids:
            sync_result = await self.sync_user_score(user_id)
            
            if sync_result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "user_id": user_id,
                    "error": sync_result.get("error", "Unknown error")
                })
        
        return results
    
    async def sync_all_users(self) -> Dict[str, Any]:
        """
        Sync scores for all users with profiles
        
        This is a maintenance operation that should be run periodically.
        
        Returns:
            Dictionary with sync results
        """
        try:
            logger.info("Starting full score sync for all users")
            
            # Get all user profiles
            profiles = await self.db.user_profiles.find({}).to_list(None)
            user_ids = [p["user_id"] for p in profiles]
            
            logger.info(f"Found {len(user_ids)} users to sync")
            
            # Batch sync
            results = await self.batch_sync_scores(user_ids)
            
            logger.info(f"Full sync completed: {results['successful']} successful, {results['failed']} failed")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in full score sync: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
