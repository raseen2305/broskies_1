"""
Enhanced Ranking Service with improved accuracy and batch updates
Manages rankings in user_rankings (primary) and syncs to view-only collections
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import Collections

logger = logging.getLogger(__name__)


class EnhancedRankingService:
    """
    Enhanced ranking service with accurate percentile calculations and batch updates
    
    Key improvements:
    - Accurate percentile calculations (handles ties correctly)
    - Batch updates for efficiency
    - Syncs to view-only collections (regional_rankings, university_rankings)
    - Proper rank position calculation with tie handling
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
    
    def calculate_accurate_percentile(self, user_score: float, all_scores: List[float]) -> Dict[str, float]:
        """
        Calculate accurate percentile with proper tie handling
        
        Percentile = (number of scores below user / total scores) × 100
        Where 100% = best (top position), 0% = worst (bottom position)
        
        Args:
            user_score: User's ACID score
            all_scores: List of all scores in comparison group
        
        Returns:
            Dictionary with percentile (100% = best), and rank
        """
        if not all_scores:
            return {
                "percentile": 0.0,
                "rank": 1,
                "total": 0
            }
        
        if len(all_scores) == 1:
            return {
                "percentile": 100.0,  # Single user is at 100% (top position)
                "rank": 1,
                "total": 1
            }
        
        total = len(all_scores)
        
        # Count scores strictly below user's score
        scores_below = sum(1 for score in all_scores if score < user_score)
        
        # Count scores equal to user's score
        scores_equal = sum(1 for score in all_scores if score == user_score)
        
        # Count scores strictly above user's score
        scores_above = sum(1 for score in all_scores if score > user_score)
        
        # Percentile: percentage of scores below you (100% = best, 0% = worst)
        # This represents "you scored better than X% of users"
        percentile = (scores_below / total) * 100
        
        # Rank: position in descending order (1 = best)
        # All users with same score get same rank
        rank = scores_above + 1
        
        return {
            "percentile": round(percentile, 1),
            "rank": rank,
            "total": total,
            "scores_above": scores_above,
            "scores_equal": scores_equal,
            "scores_below": scores_below
        }
    
    async def batch_update_regional_rankings(self, district: str) -> Dict[str, Any]:
        """
        Batch update rankings for all users in a district (regional ranking)
        
        Args:
            district: District identifier (e.g., "Dindigul", "Chennai")
        
        Returns:
            Update statistics
        """
        try:
            logger.info(f"🔄 Batch updating regional rankings for district: {district}")
            
            # Fetch all users in district with scores
            # NOTE: Using user_rankings as source. If this should be internal_users, update here.
            # For now, keeping legacy behavior but noting it.
            users = await self.db.user_rankings.find(
                {
                    "district": district,
                    "overall_score": {"$ne": None, "$gt": 0}
                }
            ).to_list(None)
            
            if not users:
                logger.warning(f"No users found in district: {district}")
                return {
                    "success": True,
                    "district": district,
                    "users_updated": 0,
                    "message": "No users in district"
                }
            
            # Extract all scores
            all_scores = [u["overall_score"] for u in users]
            total_users = len(users)
            
            logger.info(f"Found {total_users} users in district {district}")
            
            # Calculate statistics
            avg_score = sum(all_scores) / total_users
            sorted_scores = sorted(all_scores, reverse=True)
            median_score = sorted_scores[total_users // 2]
            
            # Update each user's ranking
            updates_count = 0
            view_only_docs = []
            
            for user in users:
                user_score = user["overall_score"]
                ranking_data = self.calculate_accurate_percentile(user_score, all_scores)
                
                # Update user_rankings collection (primary)
                await self.db.user_rankings.update_one(
                    {"user_id": user["user_id"]},
                    {
                        "$set": {
                            "regional_rank": ranking_data["rank"],
                            "regional_total_users": total_users,
                            "regional_percentile": ranking_data["percentile"],  # 100% = best, 0% = worst
                            "regional_avg_score": round(avg_score, 1),
                            "regional_median_score": round(median_score, 1),
                            "regional_updated_at": datetime.utcnow()
                        }
                    }
                )
                
                # Prepare view-only document
                view_only_docs.append({
                    "user_id": user["user_id"],
                    "github_username": user.get("github_username"),
                    "name": user.get("name"),
                    "district": district,
                    "state": user.get("state"),
                    "region": user.get("region"),
                    "overall_score": user_score,
                    "rank": ranking_data["rank"],
                    "total_users": total_users,
                    "percentile": ranking_data["percentile"],  # 100% = best, 0% = worst
                    "avg_score": round(avg_score, 1),
                    "median_score": round(median_score, 1),
                    "updated_at": datetime.utcnow()
                })
                
                updates_count += 1
            
            # Sync to view-only collection (regional_rankings)
            if view_only_docs:
                # Delete old entries for this district
                await self.db[Collections.REGIONAL_RANKINGS].delete_many({"district": district})
                # Insert new entries
                await self.db[Collections.REGIONAL_RANKINGS].insert_many(view_only_docs)
            
            logger.info(f"✅ Updated {updates_count} regional rankings for district {district}")
            
            return {
                "success": True,
                "district": district,
                "users_updated": updates_count,
                "total_users": total_users,
                "avg_score": round(avg_score, 1),
                "median_score": round(median_score, 1)
            }
            
        except Exception as e:
            logger.error(f"Error batch updating regional rankings for {district}: {e}")
            return {
                "success": False,
                "district": district,
                "error": str(e)
            }
    
    async def batch_update_university_rankings(self, university_short: str) -> Dict[str, Any]:
        """
        Batch update rankings for all users in a university
        
        Args:
            university_short: University short identifier
        
        Returns:
            Update statistics
        """
        try:
            logger.info(f"🔄 Batch updating university rankings for: {university_short}")
            
            # Fetch all users in university with scores
            users = await self.db.user_rankings.find(
                {
                    "university_short": university_short,
                    "overall_score": {"$ne": None, "$gt": 0}
                }
            ).to_list(None)
            
            if not users:
                logger.warning(f"No users found in university: {university_short}")
                return {
                    "success": True,
                    "university_short": university_short,
                    "users_updated": 0,
                    "message": "No users in university"
                }
            
            # Extract all scores
            all_scores = [u["overall_score"] for u in users]
            total_users = len(users)
            
            logger.info(f"Found {total_users} users in university {university_short}")
            
            # Calculate statistics
            avg_score = sum(all_scores) / total_users
            sorted_scores = sorted(all_scores, reverse=True)
            median_score = sorted_scores[total_users // 2]
            
            # Update each user's ranking
            updates_count = 0
            view_only_docs = []
            
            for user in users:
                user_score = user["overall_score"]
                ranking_data = self.calculate_accurate_percentile(user_score, all_scores)
                
                # Update user_rankings collection (primary)
                await self.db.user_rankings.update_one(
                    {"user_id": user["user_id"]},
                    {
                        "$set": {
                            "university_rank": ranking_data["rank"],
                            "university_total_users": total_users,
                            "university_percentile": ranking_data["percentile"],  # 100% = best, 0% = worst
                            "university_avg_score": round(avg_score, 1),
                            "university_median_score": round(median_score, 1),
                            "university_updated_at": datetime.utcnow()
                        }
                    }
                )
                
                # Prepare view-only document
                view_only_docs.append({
                    "user_id": user["user_id"],
                    "github_username": user.get("github_username"),
                    "name": user.get("name"),
                    "university": user.get("university"),
                    "university_short": university_short,
                    "overall_score": user_score,
                    "rank": ranking_data["rank"],
                    "total_users": total_users,
                    "percentile": ranking_data["percentile"],  # 100% = best, 0% = worst
                    "avg_score": round(avg_score, 1),
                    "median_score": round(median_score, 1),
                    "updated_at": datetime.utcnow()
                })
                
                updates_count += 1
            
            # Sync to view-only collection (university_rankings)
            if view_only_docs:
                # Delete old entries for this university
                await self.db[Collections.UNIVERSITY_RANKINGS].delete_many({"university_short": university_short})
                # Insert new entries
                await self.db[Collections.UNIVERSITY_RANKINGS].insert_many(view_only_docs)
            
            logger.info(f"✅ Updated {updates_count} university rankings for {university_short}")
            
            return {
                "success": True,
                "university_short": university_short,
                "users_updated": updates_count,
                "total_users": total_users,
                "avg_score": round(avg_score, 1),
                "median_score": round(median_score, 1)
            }
            
        except Exception as e:
            logger.error(f"Error batch updating university rankings for {university_short}: {e}")
            return {
                "success": False,
                "university_short": university_short,
                "error": str(e)
            }
    
    async def update_rankings_for_user(self, user_id: str) -> Dict[str, Any]:
        """
        Update rankings for a specific user (triggers batch update for their groups)
        
        Args:
            user_id: User identifier
        
        Returns:
            Update results
        """
        try:
            # Get user's ranking document
            user_ranking = await self.db.user_rankings.find_one({"user_id": user_id})
            
            if not user_ranking:
                return {
                    "success": False,
                    "error": "User ranking document not found"
                }
            
            district = user_ranking.get("district")
            university_short = user_ranking.get("university_short")
            
            results = {
                "success": True,
                "user_id": user_id,
                "regional_updated": False,
                "university_updated": False
            }
            
            # Batch update regional rankings (by district)
            if district:
                regional_result = await self.batch_update_regional_rankings(district)
                results["regional_updated"] = regional_result["success"]
                results["regional_result"] = regional_result
            else:
                logger.warning(f"User {user_id} has no district, skipping regional ranking")
            
            # Batch update university rankings
            if university_short:
                university_result = await self.batch_update_university_rankings(university_short)
                results["university_updated"] = university_result["success"]
                results["university_result"] = university_result
            else:
                logger.warning(f"User {user_id} has no university_short, skipping university ranking")
            
            return results
            
        except Exception as e:
            logger.error(f"Error updating rankings for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_leaderboard(
        self, 
        ranking_type: str, 
        identifier: str, 
        limit: int = 10,
        include_user: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard for district or university
        
        Args:
            ranking_type: 'regional' or 'university'
            identifier: District (for regional) or university_short (for university)
            limit: Number of top users to return
            include_user: Optional user_id to always include
        
        Returns:
            List of top users with rankings
        """
        try:
            if ranking_type == "regional":
                collection = self.db[Collections.REGIONAL_RANKINGS]
                filter_field = "district"
            else:
                collection = self.db[Collections.UNIVERSITY_RANKINGS]
                filter_field = "university_short"
            
            # Get top users
            leaderboard = await collection.find(
                {filter_field: identifier}
            ).sort("rank", 1).limit(limit).to_list(None)
            
            # If specific user requested and not in top, add them
            if include_user and not any(u["user_id"] == include_user for u in leaderboard):
                user_ranking = await collection.find_one(
                    {filter_field: identifier, "user_id": include_user}
                )
                if user_ranking:
                    leaderboard.append(user_ranking)
            
            # Remove MongoDB _id
            for entry in leaderboard:
                entry.pop("_id", None)
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    async def get_ranking_stats(self, ranking_type: str, identifier: str) -> Dict[str, Any]:
        """
        Get statistical summary for region or university
        
        Args:
            ranking_type: 'regional' or 'university'
            identifier: Region or university_short
        
        Returns:
            Statistical summary
        """
        try:
            if ranking_type == "regional":
                collection = self.db[Collections.REGIONAL_RANKINGS]
                filter_field = "region"
            else:
                collection = self.db[Collections.UNIVERSITY_RANKINGS]
                filter_field = "university_short"
            
            # Get all rankings
            rankings = await collection.find({filter_field: identifier}).to_list(None)
            
            if not rankings:
                return {
                    "total_users": 0,
                    "avg_score": 0,
                    "median_score": 0,
                    "min_score": 0,
                    "max_score": 0
                }
            
            scores = [r["overall_score"] for r in rankings]
            scores.sort()
            
            return {
                "total_users": len(scores),
                "avg_score": round(sum(scores) / len(scores), 1),
                "median_score": round(scores[len(scores) // 2], 1),
                "min_score": round(min(scores), 1),
                "max_score": round(max(scores), 1),
                "score_distribution": self._calculate_distribution(scores)
            }
            
        except Exception as e:
            logger.error(f"Error getting ranking stats: {e}")
            return {}
    
    def _calculate_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate score distribution in ranges"""
        distribution = {
            "0-20": 0,
            "20-40": 0,
            "40-60": 0,
            "60-80": 0,
            "80-100": 0
        }
        
        for score in scores:
            if score < 20:
                distribution["0-20"] += 1
            elif score < 40:
                distribution["20-40"] += 1
            elif score < 60:
                distribution["40-60"] += 1
            elif score < 80:
                distribution["60-80"] += 1
            else:
                distribution["80-100"] += 1
        
        return distribution
