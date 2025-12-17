"""
User Rankings Sync Service
Connects user_profiles and analysis_states collections to populate user_rankings
with all necessary data for ranking widget and ranking tab.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class UserRankingsSyncService:
    """
    Service to sync data from user_profiles and analysis_states into user_rankings.
    
    Matches records based on:
    - analysis_states.username == user_profiles.github_username
    
    Populates user_rankings with:
    - Profile data (name, university, region, etc.)
    - Analysis data (overall_score, repositories, category counts)
    - Ranking placeholders (to be calculated by ranking service)
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize the sync service.
        
        Args:
            database: MongoDB database instance
        """
        self.db = database
        
    async def sync_single_user(self, username: str) -> Dict[str, Any]:
        """
        Sync a single user's data from user_profiles and analysis_states to user_rankings.
        
        Args:
            username: GitHub username to sync
            
        Returns:
            Dictionary with sync result and status
        """
        try:
            logger.info(f"🔄 Starting sync for user: {username}")
            
            # Step 1: Find user profile by github_username
            profile = await self.db.user_profiles.find_one({"github_username": username})
            
            if not profile:
                logger.warning(f"⚠️  No user_profile found for username: {username}")
                return {
                    "success": False,
                    "error": "User profile not found",
                    "username": username
                }
            
            # Step 2: Find analysis state by username
            analysis = await self.db.analysis_states.find_one({
                "username": username,
                "status": "complete"
            })
            
            if not analysis:
                logger.warning(f"⚠️  No completed analysis found for username: {username}")
                return {
                    "success": False,
                    "error": "No completed analysis found",
                    "username": username
                }
            
            # Step 3: Extract data from both collections
            user_id = profile.get("user_id")
            
            # Profile data
            profile_data = {
                "name": profile.get("full_name"),
                "university": profile.get("university"),
                "university_short": profile.get("university_short"),
                "region": profile.get("region"),
                "state": profile.get("state"),
                "district": profile.get("district"),
                "nationality": profile.get("nationality"),
            }
            
            # Analysis data
            results = analysis.get("results", {})
            overall_scores = results.get("overall_scores", {})
            category_distribution = results.get("category_distribution", {})
            repositories = results.get("repositories", [])
            
            overall_score = overall_scores.get("overall_score", 0)
            
            # Count repositories by category
            flagship_count = category_distribution.get("flagship", 0)
            significant_count = category_distribution.get("significant", 0)
            supporting_count = category_distribution.get("supporting", 0)
            
            # Count evaluated repositories
            evaluated_count = len([r for r in repositories if r.get("evaluated")])
            
            # Step 4: Create user_rankings document
            user_ranking_doc = {
                "user_id": user_id,
                "github_username": username,
                
                # Profile information
                "name": profile_data["name"],
                "university": profile_data["university"],
                "university_short": profile_data["university_short"],
                "region": profile_data["region"],
                "state": profile_data["state"],
                "district": profile_data["district"],
                "nationality": profile_data["nationality"],
                
                # Score information
                "overall_score": round(overall_score, 1),
                
                # Repository statistics
                "repository_count": len(repositories),
                "evaluated_repository_count": evaluated_count,
                "flagship_count": flagship_count,
                "significant_count": significant_count,
                "supporting_count": supporting_count,
                
                # Regional ranking (placeholders - will be calculated by ranking service)
                "regional_rank": None,
                "regional_total_users": None,
                "regional_percentile": None,
                
                # University ranking (placeholders - will be calculated by ranking service)
                "university_rank": None,
                "university_total_users": None,
                "university_percentile": None,
                
                # Metadata
                "last_analysis_date": analysis.get("completed_at") or analysis.get("updated_at"),
                "last_sync_date": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Step 5: Upsert into user_rankings
            result = await self.db.user_rankings.update_one(
                {"github_username": username},
                {"$set": user_ranking_doc},
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"✅ Successfully synced user_rankings for {username}")
                logger.info(f"   - Overall Score: {overall_score:.1f}")
                logger.info(f"   - Flagship: {flagship_count}, Significant: {significant_count}, Supporting: {supporting_count}")
                logger.info(f"   - Region: {profile_data['region']}, University: {profile_data['university']}")
                
                return {
                    "success": True,
                    "username": username,
                    "user_id": user_id,
                    "overall_score": overall_score,
                    "flagship_count": flagship_count,
                    "significant_count": significant_count,
                    "supporting_count": supporting_count,
                    "upserted": result.upserted_id is not None,
                    "modified": result.modified_count > 0
                }
            else:
                logger.warning(f"⚠️  No changes made for {username}")
                return {
                    "success": False,
                    "error": "No changes made",
                    "username": username
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to sync user_rankings for {username}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "username": username
            }
    
    async def sync_all_users(self) -> Dict[str, Any]:
        """
        Sync all users who have both user_profiles and completed analysis_states.
        
        Returns:
            Dictionary with sync statistics
        """
        try:
            logger.info("🔄 Starting bulk sync of all users")
            
            # Get all completed analyses
            analyses_cursor = self.db.analysis_states.find({
                "status": "complete"
            })
            
            analyses = await analyses_cursor.to_list(None)
            logger.info(f"📊 Found {len(analyses)} completed analyses")
            
            # Sync each user
            results = {
                "total_analyses": len(analyses),
                "synced": 0,
                "failed": 0,
                "skipped": 0,
                "errors": []
            }
            
            for analysis in analyses:
                username = analysis.get("username")
                
                if not username:
                    logger.warning("⚠️  Analysis missing username, skipping")
                    results["skipped"] += 1
                    continue
                
                sync_result = await self.sync_single_user(username)
                
                if sync_result["success"]:
                    results["synced"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "username": username,
                        "error": sync_result.get("error")
                    })
            
            logger.info(f"✅ Bulk sync complete:")
            logger.info(f"   - Total: {results['total_analyses']}")
            logger.info(f"   - Synced: {results['synced']}")
            logger.info(f"   - Failed: {results['failed']}")
            logger.info(f"   - Skipped: {results['skipped']}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to sync all users: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def verify_sync(self, username: str) -> Dict[str, Any]:
        """
        Verify that a user's data is properly synced across all three collections.
        
        Args:
            username: GitHub username to verify
            
        Returns:
            Dictionary with verification results
        """
        try:
            logger.info(f"🔍 Verifying sync for user: {username}")
            
            # Check user_profiles
            profile = await self.db.user_profiles.find_one({"github_username": username})
            has_profile = profile is not None
            
            # Check analysis_states
            analysis = await self.db.analysis_states.find_one({
                "username": username,
                "status": "complete"
            })
            has_analysis = analysis is not None
            
            # Check user_rankings
            ranking = await self.db.user_rankings.find_one({"github_username": username})
            has_ranking = ranking is not None
            
            # Verify data consistency
            data_matches = False
            if has_profile and has_analysis and has_ranking:
                # Check if key fields match
                profile_user_id = profile.get("user_id")
                ranking_user_id = ranking.get("user_id")
                
                analysis_score = analysis.get("results", {}).get("overall_scores", {}).get("overall_score", 0)
                ranking_score = ranking.get("overall_score", 0)
                
                data_matches = (
                    profile_user_id == ranking_user_id and
                    abs(analysis_score - ranking_score) < 0.1  # Allow small floating point differences
                )
            
            verification_result = {
                "username": username,
                "has_profile": has_profile,
                "has_analysis": has_analysis,
                "has_ranking": has_ranking,
                "data_matches": data_matches,
                "is_synced": has_profile and has_analysis and has_ranking and data_matches
            }
            
            if verification_result["is_synced"]:
                logger.info(f"✅ User {username} is properly synced")
            else:
                logger.warning(f"⚠️  User {username} sync issues:")
                logger.warning(f"   - Has profile: {has_profile}")
                logger.warning(f"   - Has analysis: {has_analysis}")
                logger.warning(f"   - Has ranking: {has_ranking}")
                logger.warning(f"   - Data matches: {data_matches}")
            
            return verification_result
            
        except Exception as e:
            logger.error(f"❌ Failed to verify sync for {username}: {e}")
            return {
                "username": username,
                "error": str(e),
                "is_synced": False
            }
    
    async def get_sync_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the sync status across all collections.
        
        Returns:
            Dictionary with sync statistics
        """
        try:
            # Count documents in each collection
            profiles_count = await self.db.user_profiles.count_documents({})
            analyses_count = await self.db.analysis_states.count_documents({"status": "complete"})
            rankings_count = await self.db.user_rankings.count_documents({})
            
            # Find users with profiles but no analysis
            profiles_cursor = self.db.user_profiles.find({})
            profiles = await profiles_cursor.to_list(None)
            
            missing_analysis = 0
            missing_ranking = 0
            
            for profile in profiles:
                username = profile.get("github_username")
                
                # Check if analysis exists
                analysis = await self.db.analysis_states.find_one({
                    "username": username,
                    "status": "complete"
                })
                if not analysis:
                    missing_analysis += 1
                
                # Check if ranking exists
                ranking = await self.db.user_rankings.find_one({"github_username": username})
                if not ranking:
                    missing_ranking += 1
            
            stats = {
                "total_profiles": profiles_count,
                "total_completed_analyses": analyses_count,
                "total_rankings": rankings_count,
                "profiles_missing_analysis": missing_analysis,
                "profiles_missing_ranking": missing_ranking,
                "sync_percentage": round((rankings_count / profiles_count * 100), 2) if profiles_count > 0 else 0
            }
            
            logger.info(f"📊 Sync Statistics:")
            logger.info(f"   - Total Profiles: {stats['total_profiles']}")
            logger.info(f"   - Completed Analyses: {stats['total_completed_analyses']}")
            logger.info(f"   - Rankings: {stats['total_rankings']}")
            logger.info(f"   - Sync Percentage: {stats['sync_percentage']}%")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get sync statistics: {e}")
            return {
                "error": str(e)
            }
