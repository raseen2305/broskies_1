"""
Ranking service for regional and university comparisons.
Handles ranking calculations, percentile computation, and batch updates.
Updated to join internal_users and internal_users_profile collections.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import UpdateOne
from app.database import Collections

logger = logging.getLogger(__name__)


class RankingService:
    """Service for calculating and managing user rankings with joined data from both collections"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
    
    # ========================================================================
    # Data Joining Methods
    # ========================================================================
    
    async def get_joined_user_data(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Join internal_users and internal_users_profile collections to get complete user data
        with comprehensive filtering and validation
        
        Args:
            filters: Optional MongoDB filters to apply to the joined data
        
        Returns:
            List of joined user documents with complete profile and scan data
        
        Raises:
            Exception: When database operations fail or data validation errors occur
        """
        try:
            # MongoDB aggregation pipeline to join the collections
            pipeline = [
                # Start with internal_users collection - filter for valid scan data
                {
                    "$match": {
                        "overall_score": {"$ne": None, "$gt": 0, "$lte": 100},  # Valid score range
                        "username": {"$ne": None, "$ne": ""},  # Must have username
                        **(filters or {})
                    }
                },
                # Join with internal_users_profile using _id mapping
                {
                    "$lookup": {
                        "from": Collections.INTERNAL_USERS_PROFILE,
                        "localField": "_id",  # internal_users._id
                        "foreignField": "_id",  # internal_users_profile._id (same ObjectId)
                        "as": "profile_data"
                    }
                },
                # Unwind the profile data (should be 1:1 mapping)
                {
                    "$unwind": {
                        "path": "$profile_data",
                        "preserveNullAndEmptyArrays": False  # Exclude users without profile
                    }
                },
                # Project the combined fields with case-insensitive username handling
                {
                    "$project": {
                        "user_id": 1,
                        "username": {"$toLower": "$username"},  # Normalize to lowercase
                        "github_username": {
                            "$toLower": {
                                "$ifNull": ["$profile_data.github_username", "$username"]
                            }
                        },
                        "overall_score": 1,
                        "scan_date": "$updated_at",
                        
                        # Profile fields
                        "name": "$profile_data.full_name",
                        "university": "$profile_data.university",
                        "university_short": "$profile_data.university_short",
                        "district": "$profile_data.district",
                        "state": "$profile_data.state",
                        "region": "$profile_data.region",
                        "nationality": "$profile_data.nationality",
                        
                        # Metadata
                        "profile_completed": "$profile_data.profile_completed",
                        "profile_updated_at": "$profile_data.profile_updated_at",
                        
                        # For duplicate detection
                        "internal_users_updated": "$updated_at",
                        "profile_users_updated": "$profile_data.profile_updated_at"
                    }
                },
                # Comprehensive filtering for complete data
                {
                    "$match": {
                        "profile_completed": True,
                        "name": {"$ne": None, "$ne": "", "$exists": True},
                        "github_username": {"$ne": None, "$ne": "", "$exists": True},
                        "university": {"$ne": None, "$ne": "", "$exists": True},
                        "university_short": {"$ne": None, "$ne": "", "$exists": True},
                        "district": {"$ne": None, "$ne": "", "$exists": True},
                        "state": {"$ne": None, "$ne": "", "$exists": True}
                    }
                },
                # Sort by most recent update for duplicate handling
                {
                    "$sort": {
                        "github_username": 1,
                        "profile_users_updated": -1,  # Most recent profile update first
                        "internal_users_updated": -1   # Most recent scan update first
                    }
                }
            ]
            
            # Execute aggregation
            cursor = self.db[Collections.INTERNAL_USERS].aggregate(pipeline)
            all_joined_data = await cursor.to_list(None)
            
            # Handle duplicates by keeping most recent record per github_username
            unique_users = {}
            duplicate_count = 0
            
            for user in all_joined_data:
                github_username = user["github_username"]
                
                if github_username in unique_users:
                    duplicate_count += 1
                    logger.warning(f"Duplicate github_username found: {github_username}. Using most recent record.")
                    continue
                
                # Validate user completeness
                if self.validate_user_completeness(user):
                    unique_users[github_username] = user
                else:
                    logger.debug(f"User {user.get('user_id')} excluded due to incomplete data")
            
            joined_data = list(unique_users.values())
            
            if duplicate_count > 0:
                logger.warning(f"Found and resolved {duplicate_count} duplicate github usernames")
            
            logger.info(f"Successfully joined {len(joined_data)} complete user profiles")
            return joined_data
            
        except Exception as e:
            logger.error(f"Error joining user data: {e}")
            # Return empty list for graceful degradation, but log the error
            if "timeout" in str(e).lower():
                logger.error("Database timeout occurred during user data joining")
            elif "connection" in str(e).lower():
                logger.error("Database connection error during user data joining")
            else:
                logger.error(f"Unexpected error during user data joining: {type(e).__name__}")
            return []
    
    def validate_user_completeness(self, user_data: Dict[str, Any]) -> bool:
        """
        Validate that a user has complete data for ranking calculations
        
        Args:
            user_data: Joined user document
        
        Returns:
            True if user has complete data, False otherwise
        """
        # Required fields for ranking calculations
        required_fields = {
            "overall_score": "GitHub scan score",
            "github_username": "GitHub username",
            "name": "User name",
            "university": "University name",
            "university_short": "University identifier",
            "district": "District/region",
            "state": "State/province",
            "profile_completed": "Profile completion status"
        }
        
        user_id = user_data.get("user_id", "unknown")
        
        # Check all required fields
        for field, description in required_fields.items():
            value = user_data.get(field)
            
            # Check for None or empty values
            if value is None:
                logger.debug(f"User {user_id} missing {description} ({field}): None")
                return False
            
            # Check for empty strings
            if isinstance(value, str) and value.strip() == "":
                logger.debug(f"User {user_id} missing {description} ({field}): empty string")
                return False
            
            # Special validation for profile_completed
            if field == "profile_completed" and not value:
                logger.debug(f"User {user_id} has incomplete profile")
                return False
        
        # Validate score range and type
        score = user_data.get("overall_score", 0)
        if not isinstance(score, (int, float)):
            logger.debug(f"User {user_id} has non-numeric score: {score} (type: {type(score)})")
            return False
        
        if not (0 <= score <= 100):
            logger.debug(f"User {user_id} has out-of-range score: {score}")
            return False
        
        # Validate username format (basic check)
        github_username = user_data.get("github_username", "")
        if len(github_username) < 1 or len(github_username) > 39:  # GitHub username limits
            logger.debug(f"User {user_id} has invalid github_username length: {github_username}")
            return False
        
        # Check for suspicious characters in username
        import re
        if not re.match(r'^[a-zA-Z0-9\-_]+$', github_username):
            logger.debug(f"User {user_id} has invalid github_username format: {github_username}")
            return False
        
        return True
    
    # ========================================================================
    # Core Ranking Calculation Methods (Updated for Accuracy)
    # ========================================================================
    
    def calculate_percentile(self, user_score: float, all_scores: List[float]) -> float:
        """
        Calculate percentile ranking where higher scores = better performance
        
        Formula: (users_with_lower_score / total_users) × 100
        This represents "you scored better than X% of users"
        
        Args:
            user_score: The user's overall score
            all_scores: List of all scores in the comparison group
        
        Returns:
            Percentile (0-100) where 100 = top performer, 0 = bottom performer
        
        Edge cases handled:
        - Empty list: returns 0.0
        - Single user: returns 100.0 (top of their group)
        - Tied scores: all users with same score get same percentile
        """
        if not all_scores:
            logger.warning("Empty scores list provided to calculate_percentile")
            return 0.0
        
        if len(all_scores) == 1:
            return 100.0
        
        # Validate and clamp score range
        if not isinstance(user_score, (int, float)):
            logger.warning(f"Non-numeric score provided: {user_score}")
            return 0.0
            
        if not (0 <= user_score <= 100):
            logger.warning(f"Score {user_score} outside valid range [0, 100], clamping")
            user_score = max(0, min(100, user_score))
        
        # Count users with strictly lower scores
        users_below = sum(1 for score in all_scores if score < user_score)
        total_users = len(all_scores)
        
        # Calculate percentile: percentage of users you scored better than
        percentile = (users_below / total_users) * 100
        
        return round(percentile, 1)
    
    def calculate_rank_position(self, user_score: float, all_scores: List[float]) -> int:
        """
        Calculate rank position (1 = best, N = worst) with proper tie handling
        
        All users with the same score get the same rank position.
        The next rank after tied users accounts for the number of tied users.
        
        Args:
            user_score: The user's overall score
            all_scores: List of all scores in the comparison group
        
        Returns:
            Rank position (1-indexed)
        """
        if not all_scores:
            return 1
        
        if len(all_scores) == 1:
            return 1
        
        # Validate score
        if not isinstance(user_score, (int, float)):
            logger.warning(f"Non-numeric score provided for ranking: {user_score}")
            return len(all_scores)  # Worst possible rank
        
        # Count users with strictly better scores
        users_above = sum(1 for score in all_scores if score > user_score)
        
        # Rank is 1 + number of users with better scores
        rank = users_above + 1
        
        return rank
    
    def calculate_statistics(self, scores: List[float]) -> Dict[str, float]:
        """
        Calculate statistical measures for a group of scores
        
        Args:
            scores: List of scores
        
        Returns:
            Dictionary with statistical measures
        """
        if not scores:
            return {
                "avg_score": 0.0,
                "median_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
                "total_users": 0
            }
        
        sorted_scores = sorted(scores)
        total_users = len(scores)
        
        return {
            "avg_score": round(sum(scores) / total_users, 1),
            "median_score": round(sorted_scores[total_users // 2], 1),
            "min_score": round(min(scores), 1),
            "max_score": round(max(scores), 1),
            "total_users": total_users
        }
    
    # ========================================================================
    # Regional Ranking Methods
    # ========================================================================
    
    async def update_regional_rankings(self, district: str) -> Dict[str, Any]:
        """
        Recalculate rankings for all users in a specific district (regional ranking)
        
        Args:
            district: District identifier (e.g., "Dindigul", "Chennai")
        
        Returns:
            Dictionary with update statistics
        """
        try:
            logger.info(f"Updating regional rankings for district: {district}")
            
            # Get joined user data for this district
            pipeline = [
                {
                    "$match": {
                        "overall_score": {"$ne": None, "$gt": 0}
                    }
                },
                {
                    "$lookup": {
                        "from": Collections.INTERNAL_USERS_PROFILE,
                        "localField": "_id",
                        "foreignField": "_id",
                        "as": "profile_data"
                    }
                },
                {
                    "$unwind": {
                        "path": "$profile_data",
                        "preserveNullAndEmptyArrays": False
                    }
                },
                {
                    "$match": {
                        "profile_data.district": district,
                        "profile_data.profile_completed": True
                    }
                },
                {
                    "$project": {
                        "user_id": 1,
                        "username": 1,
                        "github_username": {"$ifNull": ["$profile_data.github_username", "$username"]},
                        "overall_score": 1,
                        "name": "$profile_data.full_name",
                        "district": "$profile_data.district",
                        "state": "$profile_data.state",
                        "region": "$profile_data.region"
                    }
                },
                {
                    "$sort": {"overall_score": -1}
                }
            ]
            
            cursor = self.db[Collections.INTERNAL_USERS].aggregate(pipeline)
            users = await cursor.to_list(None)
            
            if not users:
                logger.warning(f"No users found in district: {district}")
                return {
                    "success": True,
                    "district": district,
                    "users_updated": 0,
                    "message": "No users in district"
                }
            
            total_users = len(users)
            all_scores = [u["overall_score"] for u in users]
            
            # Calculate statistics using improved method
            stats = self.calculate_statistics(all_scores)
            
            logger.info(f"Found {total_users} users in district {district}")
            
            # Prepare regional ranking documents
            regional_rankings = []
            
            for user in users:
                percentile = self.calculate_percentile(user["overall_score"], all_scores)
                rank = self.calculate_rank_position(user["overall_score"], all_scores)
                
                regional_ranking = {
                    "user_id": user["user_id"],
                    "github_username": user["github_username"],
                    "name": user["name"],
                    "district": district,
                    "state": user["state"],
                    "region": user["region"],
                    "overall_score": user["overall_score"],
                    "rank": rank,
                    "total_users": stats["total_users"],
                    "percentile": percentile,
                    "avg_score": stats["avg_score"],
                    "median_score": stats["median_score"],
                    "updated_at": datetime.utcnow()
                }
                regional_rankings.append(regional_ranking)
            
            # Update regional_rankings collection
            if regional_rankings:
                # Delete existing rankings for this district
                await self.db[Collections.REGIONAL_RANKINGS].delete_many({"district": district})
                
                # Insert new rankings
                await self.db[Collections.REGIONAL_RANKINGS].insert_many(regional_rankings)
                
                logger.info(f"Updated {len(regional_rankings)} regional rankings for district {district}")
                
                return {
                    "success": True,
                    "district": district,
                    "users_updated": len(regional_rankings),
                    "total_users": stats["total_users"],
                    "avg_score": stats["avg_score"],
                    "median_score": stats["median_score"]
                }
            
            return {
                "success": True,
                "district": district,
                "users_updated": 0,
                "total_users": total_users
            }
            
        except Exception as e:
            logger.error(f"Error updating regional rankings for {district}: {e}")
            return {
                "success": False,
                "district": district,
                "error": str(e)
            }
    
    async def get_regional_ranking(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get regional ranking for a specific user
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with ranking information or None
        """
        try:
            ranking = await self.db[Collections.REGIONAL_RANKINGS].find_one({"user_id": user_id})
            
            if ranking:
                # Remove MongoDB _id for cleaner response
                ranking.pop("_id", None)
                return ranking
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting regional ranking for user {user_id}: {e}")
            return None
    
    # ========================================================================
    # University Ranking Methods
    # ========================================================================
    
    async def update_university_rankings(self, university_short: str) -> Dict[str, Any]:
        """
        Recalculate rankings for all users in a specific university
        
        Args:
            university_short: University short identifier (e.g., "kalasalingam-(id:-c-27066)")
        
        Returns:
            Dictionary with update statistics
        """
        try:
            logger.info(f"Updating university rankings for: {university_short}")
            
            # Get joined user data for this university
            pipeline = [
                {
                    "$match": {
                        "overall_score": {"$ne": None, "$gt": 0}
                    }
                },
                {
                    "$lookup": {
                        "from": Collections.INTERNAL_USERS_PROFILE,
                        "localField": "_id",
                        "foreignField": "_id",
                        "as": "profile_data"
                    }
                },
                {
                    "$unwind": {
                        "path": "$profile_data",
                        "preserveNullAndEmptyArrays": False
                    }
                },
                {
                    "$match": {
                        "profile_data.university_short": university_short,
                        "profile_data.profile_completed": True
                    }
                },
                {
                    "$project": {
                        "user_id": 1,
                        "username": 1,
                        "github_username": {"$ifNull": ["$profile_data.github_username", "$username"]},
                        "overall_score": 1,
                        "name": "$profile_data.full_name",
                        "university": "$profile_data.university",
                        "university_short": "$profile_data.university_short"
                    }
                },
                {
                    "$sort": {"overall_score": -1}
                }
            ]
            
            cursor = self.db[Collections.INTERNAL_USERS].aggregate(pipeline)
            users = await cursor.to_list(None)
            
            if not users:
                logger.warning(f"No users found in university: {university_short}")
                return {
                    "success": True,
                    "university_short": university_short,
                    "users_updated": 0,
                    "message": "No users in university"
                }
            
            total_users = len(users)
            all_scores = [u["overall_score"] for u in users]
            
            # Calculate statistics using improved method
            stats = self.calculate_statistics(all_scores)
            
            logger.info(f"Found {total_users} users in university {university_short}")
            
            # Prepare university ranking documents
            university_rankings = []
            
            for user in users:
                percentile = self.calculate_percentile(user["overall_score"], all_scores)
                rank = self.calculate_rank_position(user["overall_score"], all_scores)
                
                university_ranking = {
                    "user_id": user["user_id"],
                    "github_username": user["github_username"],
                    "name": user["name"],
                    "university": user["university"],
                    "university_short": university_short,
                    "overall_score": user["overall_score"],
                    "rank": rank,
                    "total_users": stats["total_users"],
                    "percentile": percentile,
                    "avg_score": stats["avg_score"],
                    "median_score": stats["median_score"],
                    "updated_at": datetime.utcnow()
                }
                university_rankings.append(university_ranking)
            
            # Update university_rankings collection
            if university_rankings:
                # Delete existing rankings for this university
                await self.db[Collections.UNIVERSITY_RANKINGS].delete_many({"university_short": university_short})
                
                # Insert new rankings
                await self.db[Collections.UNIVERSITY_RANKINGS].insert_many(university_rankings)
                
                logger.info(f"Updated {len(university_rankings)} university rankings for {university_short}")
                
                return {
                    "success": True,
                    "university_short": university_short,
                    "users_updated": len(university_rankings),
                    "total_users": stats["total_users"],
                    "avg_score": stats["avg_score"],
                    "median_score": stats["median_score"]
                }
            
            return {
                "success": True,
                "university_short": university_short,
                "users_updated": 0,
                "total_users": total_users
            }
            
        except Exception as e:
            logger.error(f"Error updating university rankings for {university_short}: {e}")
            return {
                "success": False,
                "university_short": university_short,
                "error": str(e)
            }
    
    async def get_university_ranking(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get university ranking for a specific user
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with ranking information or None
        """
        try:
            ranking = await self.db[Collections.UNIVERSITY_RANKINGS].find_one({"user_id": user_id})
            
            if ranking:
                # Remove MongoDB _id for cleaner response
                ranking.pop("_id", None)
                return ranking
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting university ranking for user {user_id}: {e}")
            return None
    
    # ========================================================================
    # Combined Ranking Methods
    # ========================================================================
    
    async def get_user_rankings(self, user_id: str) -> Dict[str, Any]:
        """
        Get both regional and university rankings for a user
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with both rankings
        """
        regional = await self.get_regional_ranking(user_id)
        university = await self.get_university_ranking(user_id)
        
        return {
            "user_id": user_id,
            "regional_ranking": regional,
            "university_ranking": university,
            "has_regional": regional is not None,
            "has_university": university is not None
        }
    
    async def update_all_rankings_for_user(self, user_id: str) -> Dict[str, Any]:
        """
        Update both regional and university rankings for a user
        
        This triggers batch updates for all users in the same district and university.
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with update results
        """
        try:
            # Get user profile data from joined collections
            pipeline = [
                {
                    "$match": {"user_id": user_id}
                },
                {
                    "$lookup": {
                        "from": Collections.INTERNAL_USERS_PROFILE,
                        "localField": "_id",
                        "foreignField": "_id",
                        "as": "profile_data"
                    }
                },
                {
                    "$unwind": {
                        "path": "$profile_data",
                        "preserveNullAndEmptyArrays": False
                    }
                },
                {
                    "$project": {
                        "user_id": 1,
                        "district": "$profile_data.district",
                        "university_short": "$profile_data.university_short",
                        "profile_completed": "$profile_data.profile_completed"
                    }
                }
            ]
            
            cursor = self.db[Collections.INTERNAL_USERS].aggregate(pipeline)
            user_data = await cursor.to_list(1)
            
            if not user_data:
                return {
                    "success": False,
                    "error": "User profile not found or incomplete"
                }
            
            user_profile = user_data[0]
            district = user_profile.get("district")
            university_short = user_profile.get("university_short")
            
            results = {
                "success": True,
                "user_id": user_id,
                "regional_update": None,
                "university_update": None
            }
            
            # Update regional rankings (by district)
            if district:
                results["regional_update"] = await self.update_regional_rankings(district)
            else:
                logger.warning(f"User {user_id} has no district set, skipping regional ranking")
            
            # Update university rankings
            if university_short:
                results["university_update"] = await self.update_university_rankings(university_short)
            else:
                logger.warning(f"User {user_id} has no university_short set, skipping university ranking")
            
            return results
            
        except Exception as e:
            logger.error(f"Error updating all rankings for user {user_id}: {e}")
            return {
                "success": False,
                "user_id": user_id,
                "error": str(e)
            }
    
    # ========================================================================
    # Leaderboard Methods
    # ========================================================================
    
    async def get_regional_leaderboard(self, district: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top users in a district (regional leaderboard)
        
        Args:
            district: District identifier
            limit: Number of top users to return
        
        Returns:
            List of top users with their rankings
        """
        try:
            leaderboard = await self.db[Collections.REGIONAL_RANKINGS].find(
                {"district": district}
            ).sort("rank", 1).limit(limit).to_list(None)
            
            # Remove MongoDB _id and sensitive data
            for entry in leaderboard:
                entry.pop("_id", None)
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting regional leaderboard for {district}: {e}")
            return []
    
    async def get_university_leaderboard(self, university_short: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top users in a university
        
        Args:
            university_short: University short identifier
            limit: Number of top users to return
        
        Returns:
            List of top users with their rankings
        """
        try:
            leaderboard = await self.db[Collections.UNIVERSITY_RANKINGS].find(
                {"university_short": university_short}
            ).sort("rank", 1).limit(limit).to_list(None)
            
            # Remove MongoDB _id and sensitive data
            for entry in leaderboard:
                entry.pop("_id", None)
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting university leaderboard for {university_short}: {e}")
            return []
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    async def get_all_districts(self) -> List[str]:
        """
        Get all unique districts from the profile collection
        
        Returns:
            List of district identifiers
        """
        try:
            districts = await self.db[Collections.INTERNAL_USERS_PROFILE].distinct(
                "district",
                {"profile_completed": True, "district": {"$ne": None, "$ne": ""}}
            )
            return sorted(districts)
        except Exception as e:
            logger.error(f"Error getting districts: {e}")
            return []
    
    async def get_all_universities(self) -> List[str]:
        """
        Get all unique universities from the profile collection
        
        Returns:
            List of university short identifiers
        """
        try:
            universities = await self.db[Collections.INTERNAL_USERS_PROFILE].distinct(
                "university_short",
                {"profile_completed": True, "university_short": {"$ne": None, "$ne": ""}}
            )
            return sorted(universities)
        except Exception as e:
            logger.error(f"Error getting universities: {e}")
            return []