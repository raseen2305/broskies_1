"""
Score Storage Service

Stores user overall scores and repository scores in a separate database (scores_comparison)
for HR to query and sort profiles efficiently.

This service is called after each scan to update the scoring data.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class ScoreStorageService:
    """
    Service to store and manage user scores in the scores_comparison database.
    
    This enables HR to quickly query and sort developer profiles by their scores
    without needing to process all repository data.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the score storage service.
        
        Args:
            db: MongoDB database connection (DEPRECATED: git_Evaluator database)
        """
        self.db = db
        self.collection = db.scores_comparison  # Collection name is scores_comparison
    
    async def initialize(self):
        """Create indexes for efficient querying"""
        try:
            # Index for sorting by overall score
            await self.collection.create_index([("overall_score", -1)])
            
            # Index for finding user by username
            await self.collection.create_index([("username", 1)], unique=True)
            
            # Index for finding user by user_id
            await self.collection.create_index([("user_id", 1)])
            
            # Index for filtering by last updated
            await self.collection.create_index([("last_updated", -1)])
            
            # Index for filtering by most used language
            await self.collection.create_index([("most_used_language", 1)])
            
            logger.info("Score storage indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create score storage indexes: {e}")
    
    async def store_user_scores(
        self,
        username: str,
        user_id: str,
        overall_score: float,
        flagship_repos: List[Dict[str, Any]],
        significant_repos: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store or update user scores in the database.
        
        Args:
            username: GitHub username
            user_id: Internal user ID
            overall_score: Overall developer score (0-100)
            flagship_repos: List of flagship repositories with scores
            significant_repos: List of significant repositories with scores
            metadata: Additional metadata (profile info, stats, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate most used language
            all_repos = flagship_repos + significant_repos
            language_count = {}
            for repo in all_repos:
                lang = repo.get("language")
                if lang:
                    language_count[lang] = language_count.get(lang, 0) + 1
            
            # Get most used language
            most_used_language = None
            if language_count:
                most_used_language = max(language_count.items(), key=lambda x: x[1])[0]
            
            # Prepare the document
            score_document = {
                "username": username,
                "user_id": user_id,
                "overall_score": round(overall_score, 2),
                "most_used_language": most_used_language,
                "flagship_repositories": [
                    {
                        "repo_name": repo.get("name"),
                        "full_name": repo.get("full_name"),
                        "score": round(repo.get("score", 0), 2),
                        "language": repo.get("language"),
                        "stars": repo.get("stars", 0),
                        "description": repo.get("description"),
                        "url": repo.get("html_url")
                    }
                    for repo in flagship_repos
                ],
                "significant_repositories": [
                    {
                        "repo_name": repo.get("name"),
                        "full_name": repo.get("full_name"),
                        "score": round(repo.get("score", 0), 2),
                        "language": repo.get("language"),
                        "stars": repo.get("stars", 0),
                        "description": repo.get("description"),
                        "url": repo.get("html_url")
                    }
                    for repo in significant_repos
                ],
                "metadata": metadata or {},
                "last_updated": datetime.utcnow(),
                "total_flagship_repos": len(flagship_repos),
                "total_significant_repos": len(significant_repos),
                "avg_flagship_score": round(
                    sum(repo.get("score", 0) for repo in flagship_repos) / len(flagship_repos), 2
                ) if flagship_repos else 0,
                "avg_significant_score": round(
                    sum(repo.get("score", 0) for repo in significant_repos) / len(significant_repos), 2
                ) if significant_repos else 0
            }
            
            # Upsert the document (update if exists, insert if not)
            result = await self.collection.update_one(
                {"username": username},
                {"$set": score_document},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"✅ Created new score record for user: {username} (score: {overall_score})")
            else:
                logger.info(f"✅ Updated score record for user: {username} (score: {overall_score})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store scores for user {username}: {e}")
            return False
    
    async def get_user_scores(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user scores from the database.
        
        Args:
            username: GitHub username
        
        Returns:
            User score document or None if not found
        """
        try:
            score_doc = await self.collection.find_one({"username": username})
            if score_doc:
                # Remove MongoDB _id field
                score_doc.pop("_id", None)
            return score_doc
        except Exception as e:
            logger.error(f"Failed to retrieve scores for user {username}: {e}")
            return None
    
    async def get_top_users(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get top users sorted by overall score.
        
        Args:
            limit: Maximum number of users to return
            skip: Number of users to skip (for pagination)
        
        Returns:
            List of user score documents sorted by overall_score descending
        """
        try:
            cursor = self.collection.find().sort("overall_score", -1).skip(skip).limit(limit)
            users = await cursor.to_list(length=limit)
            
            # Remove MongoDB _id field
            for user in users:
                user.pop("_id", None)
            
            return users
        except Exception as e:
            logger.error(f"Failed to retrieve top users: {e}")
            return []
    
    async def get_users_by_score_range(
        self,
        min_score: float,
        max_score: float,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get users within a specific score range.
        
        Args:
            min_score: Minimum overall score
            max_score: Maximum overall score
            limit: Maximum number of users to return
        
        Returns:
            List of user score documents within the score range
        """
        try:
            cursor = self.collection.find({
                "overall_score": {"$gte": min_score, "$lte": max_score}
            }).sort("overall_score", -1).limit(limit)
            
            users = await cursor.to_list(length=limit)
            
            # Remove MongoDB _id field
            for user in users:
                user.pop("_id", None)
            
            return users
        except Exception as e:
            logger.error(f"Failed to retrieve users by score range: {e}")
            return []
    
    async def get_users_by_language(
        self,
        language: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get users who primarily use a specific programming language.
        
        Args:
            language: Programming language (e.g., "Python", "JavaScript")
            limit: Maximum number of users to return
        
        Returns:
            List of user score documents sorted by overall_score descending
        """
        try:
            cursor = self.collection.find({
                "most_used_language": language
            }).sort("overall_score", -1).limit(limit)
            
            users = await cursor.to_list(length=limit)
            
            # Remove MongoDB _id field
            for user in users:
                user.pop("_id", None)
            
            return users
        except Exception as e:
            logger.error(f"Failed to retrieve users by language: {e}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics about stored scores.
        
        Returns:
            Dictionary with statistics (total users, avg score, etc.)
        """
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_users": {"$sum": 1},
                        "avg_overall_score": {"$avg": "$overall_score"},
                        "max_overall_score": {"$max": "$overall_score"},
                        "min_overall_score": {"$min": "$overall_score"},
                        "total_flagship_repos": {"$sum": "$total_flagship_repos"},
                        "total_significant_repos": {"$sum": "$total_significant_repos"}
                    }
                }
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=1)
            
            if result:
                stats = result[0]
                stats.pop("_id", None)
                return stats
            else:
                return {
                    "total_users": 0,
                    "avg_overall_score": 0,
                    "max_overall_score": 0,
                    "min_overall_score": 0,
                    "total_flagship_repos": 0,
                    "total_significant_repos": 0
                }
        except Exception as e:
            logger.error(f"Failed to retrieve statistics: {e}")
            return {}
    
    async def delete_user_scores(self, username: str) -> bool:
        """
        Delete user scores from the database.
        
        Args:
            username: GitHub username
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.collection.delete_one({"username": username})
            if result.deleted_count > 0:
                logger.info(f"Deleted score record for user: {username}")
                return True
            else:
                logger.warning(f"No score record found for user: {username}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete scores for user {username}: {e}")
            return False


# Global instance (will be initialized with database connection)
score_storage_service: Optional[ScoreStorageService] = None


async def get_score_storage_service(scores_db: AsyncIOMotorDatabase) -> ScoreStorageService:
    """
    Get or create the score storage service instance.
    
    Args:
        scores_db: MongoDB database connection for scores_comparison
    
    Returns:
        ScoreStorageService instance
    """
    global score_storage_service
    
    if score_storage_service is None:
        score_storage_service = ScoreStorageService(scores_db)
        await score_storage_service.initialize()
    
    return score_storage_service
