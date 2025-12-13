"""
HR View Service

This service manages the hr_view collection - a centralized collection
that stores ALL developer information needed for the HR dashboard view button.

This collection consolidates data from multiple sources into a single document
per developer, making it the primary source for HR dashboard views.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class HRViewService:
    """Service for managing the hr_view collection"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def ensure_indexes(self):
        """Create indexes for hr_view collection for optimal performance"""
        try:
            # Create indexes
            await self.db.hr_view.create_index("github_username", unique=True)
            await self.db.hr_view.create_index("user_id")
            await self.db.hr_view.create_index("overall_score")
            await self.db.hr_view.create_index("primary_language")
            await self.db.hr_view.create_index("last_updated")
            await self.db.hr_view.create_index([("name", "text"), ("bio", "text")])
            
            logger.info("✅ HR view collection indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create hr_view indexes: {e}")
    
    async def upsert_developer_profile(
        self,
        user_id: str,
        github_username: str,
        profile_data: Optional[Dict[str, Any]] = None,
        repositories: Optional[List[Dict[str, Any]]] = None,
        scores: Optional[Dict[str, Any]] = None,
        rankings: Optional[Dict[str, Any]] = None,
        languages: Optional[List[Dict[str, Any]]] = None,
        tech_stack: Optional[List[str]] = None,
        pull_requests: Optional[Dict[str, Any]] = None,
        issues: Optional[Dict[str, Any]] = None,
        contributions: Optional[Dict[str, Any]] = None,
        category_distribution: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upsert a complete developer profile into hr_view collection
        
        This method consolidates all developer data into a single document
        that can be instantly retrieved for HR dashboard views.
        
        Args:
            user_id: User ID
            github_username: GitHub username
            profile_data: Basic profile information (name, bio, avatar, etc.)
            repositories: List of repository data with scores
            scores: Overall and ACID scores
            rankings: Regional and university rankings
            languages: Programming languages with percentages
            tech_stack: Technologies and frameworks used
            pull_requests: Pull request statistics
            issues: Issue statistics
            contributions: Contribution statistics
            category_distribution: Repository category distribution
            
        Returns:
            Result of the upsert operation
        """
        try:
            logger.info(f"📝 Upserting HR view profile for: {github_username}")
            
            # Build comprehensive document
            hr_view_doc = {
                "user_id": user_id,
                "github_username": github_username,
                "last_updated": datetime.utcnow(),
                
                # Profile information
                "name": profile_data.get("name") if profile_data else None,
                "bio": profile_data.get("bio") if profile_data else None,
                "avatar_url": profile_data.get("avatar_url") if profile_data else f"https://github.com/{github_username}.png",
                "location": profile_data.get("location") if profile_data else None,
                "company": profile_data.get("company") if profile_data else None,
                "email": profile_data.get("email") if profile_data else None,
                "blog": profile_data.get("blog") if profile_data else None,
                "twitter_username": profile_data.get("twitter_username") if profile_data else None,
                "public_repos": profile_data.get("public_repos", 0) if profile_data else 0,
                "followers": profile_data.get("followers", 0) if profile_data else 0,
                "following": profile_data.get("following", 0) if profile_data else 0,
                "github_created_at": profile_data.get("created_at") if profile_data else None,
                "github_updated_at": profile_data.get("updated_at") if profile_data else None,
                
                # Repositories with full details
                "repositories": repositories or [],
                "repository_count": len(repositories) if repositories else 0,
                
                # Scores
                "overall_score": scores.get("overall_score", 0.0) if scores else 0.0,
                "acid_scores": scores.get("acid_breakdown", {}) if scores else {},
                
                # Rankings
                "regional_rank": rankings.get("regional", {}).get("rank") if rankings else None,
                "regional_total_users": rankings.get("regional", {}).get("total") if rankings else None,
                "regional_percentile": rankings.get("regional", {}).get("percentile") if rankings else None,
                "region": rankings.get("regional", {}).get("region") if rankings else None,
                "state": rankings.get("regional", {}).get("state") if rankings else None,
                "regional_percentile_text": rankings.get("regional", {}).get("percentile_text") if rankings else None,
                
                "university_rank": rankings.get("university", {}).get("rank") if rankings else None,
                "university_total_users": rankings.get("university", {}).get("total") if rankings else None,
                "university_percentile": rankings.get("university", {}).get("percentile") if rankings else None,
                "university": rankings.get("university", {}).get("university") if rankings else None,
                "university_short": rankings.get("university", {}).get("university_short") if rankings else None,
                "university_percentile_text": rankings.get("university", {}).get("percentile_text") if rankings else None,
                
                # Languages and tech stack
                "languages": languages or [],
                "primary_language": languages[0].get("name") if languages and len(languages) > 0 else None,
                "tech_stack": tech_stack or [],
                
                # Pull requests
                "total_pull_requests": pull_requests.get("total", 0) if pull_requests else 0,
                "merged_pull_requests": pull_requests.get("merged", 0) if pull_requests else 0,
                "open_pull_requests": pull_requests.get("open", 0) if pull_requests else 0,
                "closed_pull_requests": pull_requests.get("closed", 0) if pull_requests else 0,
                "pull_request_details": pull_requests.get("details", []) if pull_requests else [],
                
                # Issues
                "total_issues": issues.get("total", 0) if issues else 0,
                "open_issues": issues.get("open", 0) if issues else 0,
                "closed_issues": issues.get("closed", 0) if issues else 0,
                "issue_details": issues.get("details", []) if issues else [],
                
                # Contributions
                "total_commits": contributions.get("total_commits", 0) if contributions else 0,
                "total_contributions": contributions.get("total_contributions", 0) if contributions else 0,
                "contribution_years": contributions.get("years", []) if contributions else [],
                
                # Category distribution
                "category_distribution": category_distribution or {},
                "flagship_repos": category_distribution.get("flagship", 0) if category_distribution else 0,
                "significant_repos": category_distribution.get("significant", 0) if category_distribution else 0,
                "learning_repos": category_distribution.get("learning", 0) if category_distribution else 0,
                "experimental_repos": category_distribution.get("experimental", 0) if category_distribution else 0,
            }
            
            # Upsert into hr_view collection
            result = await self.db.hr_view.update_one(
                {"github_username": github_username},
                {"$set": hr_view_doc},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"✅ Created new HR view profile for: {github_username}")
            else:
                logger.info(f"✅ Updated HR view profile for: {github_username}")
            
            return {
                "success": True,
                "github_username": github_username,
                "upserted": bool(result.upserted_id),
                "modified": result.modified_count > 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to upsert HR view profile for {github_username}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def sync_from_user_rankings(self, github_username: str) -> Dict[str, Any]:
        """
        Sync hr_view from user_rankings collection
        
        This method pulls data from user_rankings and populates hr_view.
        Useful for backfilling or updating existing data.
        
        Args:
            github_username: GitHub username to sync
            
        Returns:
            Sync result
        """
        try:
            logger.info(f"🔄 Syncing HR view from user_rankings for: {github_username}")
            
            # Get data from user_rankings
            user_data = await self.db.user_rankings.find_one(
                {"github_username": github_username}
            )
            
            if not user_data:
                logger.warning(f"No user_rankings data found for: {github_username}")
                return {
                    "success": False,
                    "error": "User not found in user_rankings"
                }
            
            # Extract data from user_rankings
            profile_data = {
                "name": user_data.get("name"),
                "bio": user_data.get("bio"),
                "avatar_url": user_data.get("profile_picture"),
                "location": user_data.get("location"),
                "company": user_data.get("company"),
                "email": user_data.get("email"),
                "blog": user_data.get("blog") or user_data.get("website"),
                "twitter_username": user_data.get("twitter_username"),
                "public_repos": user_data.get("public_repos") or user_data.get("total_repos", 0),
                "followers": user_data.get("followers", 0),
                "following": user_data.get("following", 0),
                "created_at": user_data.get("github_created_at") or user_data.get("created_at"),
                "updated_at": user_data.get("github_updated_at") or user_data.get("updated_at")
            }
            
            scores = {
                "overall_score": user_data.get("overall_score", 0.0),
                "acid_breakdown": user_data.get("acid_scores", {})
            }
            
            rankings = {
                "regional": {
                    "rank": user_data.get("regional_rank"),
                    "total": user_data.get("total_regional_users"),
                    "percentile": user_data.get("regional_percentile"),
                    "region": user_data.get("region"),
                    "state": user_data.get("state"),
                    "percentile_text": user_data.get("regional_percentile_text")
                },
                "university": {
                    "rank": user_data.get("university_rank"),
                    "total": user_data.get("total_university_users"),
                    "percentile": user_data.get("university_percentile"),
                    "university": user_data.get("university"),
                    "university_short": user_data.get("university_short"),
                    "percentile_text": user_data.get("university_percentile_text")
                }
            }
            
            # Upsert into hr_view
            result = await self.upsert_developer_profile(
                user_id=user_data.get("user_id"),
                github_username=github_username,
                profile_data=profile_data,
                repositories=user_data.get("repositories", []),
                scores=scores,
                rankings=rankings,
                languages=user_data.get("languages", []),
                tech_stack=user_data.get("tech_stack", []),
                pull_requests=user_data.get("pull_requests"),
                issues=user_data.get("issues"),
                contributions=user_data.get("contributions"),
                category_distribution=user_data.get("category_distribution", {})
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to sync HR view from user_rankings for {github_username}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_developer_profile(self, github_username: str) -> Optional[Dict[str, Any]]:
        """
        Get complete developer profile from hr_view collection
        
        Args:
            github_username: GitHub username
            
        Returns:
            Complete developer profile or None if not found
        """
        try:
            profile = await self.db.hr_view.find_one(
                {"github_username": github_username}
            )
            
            if profile:
                # Remove MongoDB _id field
                profile.pop("_id", None)
                logger.info(f"✅ Retrieved HR view profile for: {github_username}")
            else:
                logger.warning(f"⚠️  No HR view profile found for: {github_username}")
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Failed to get HR view profile for {github_username}: {e}")
            return None
    
    async def bulk_sync_from_user_rankings(self, limit: int = None) -> Dict[str, Any]:
        """
        Bulk sync all users from user_rankings to hr_view
        
        Useful for initial population or mass updates.
        
        Args:
            limit: Optional limit on number of users to sync
            
        Returns:
            Sync statistics
        """
        try:
            logger.info("🔄 Starting bulk sync from user_rankings to hr_view")
            
            # Get all users from user_rankings
            query = {}
            cursor = self.db.user_rankings.find(query)
            
            if limit:
                cursor = cursor.limit(limit)
            
            users = await cursor.to_list(length=None)
            
            total = len(users)
            success_count = 0
            error_count = 0
            errors = []
            
            logger.info(f"Found {total} users to sync")
            
            for user in users:
                github_username = user.get("github_username")
                if not github_username:
                    error_count += 1
                    continue
                
                result = await self.sync_from_user_rankings(github_username)
                
                if result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
                    errors.append({
                        "username": github_username,
                        "error": result.get("error")
                    })
                
                # Log progress every 10 users
                if (success_count + error_count) % 10 == 0:
                    logger.info(f"Progress: {success_count + error_count}/{total} users processed")
            
            logger.info(f"✅ Bulk sync completed: {success_count} success, {error_count} errors")
            
            return {
                "success": True,
                "total": total,
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors[:10]  # Return first 10 errors
            }
            
        except Exception as e:
            logger.error(f"❌ Bulk sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
