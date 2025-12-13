"""
Repository Storage Service
Handles CRUD operations for repositories
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import UpdateOne
import logging

from app.models.repository import Repository, RepositoryCreate

logger = logging.getLogger(__name__)


class RepositoryStorageService:
    """
    Service for repository storage operations
    
    Provides CRUD operations for repositories with bulk operations support
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize repository storage service
        
        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.collection = database.repositories
    
    async def create_repository(
        self,
        repo_data: RepositoryCreate
    ) -> str:
        """
        Create a new repository
        
        Args:
            repo_data: Repository creation data
            
        Returns:
            Created repository ID
        """
        doc = repo_data.model_dump(by_alias=True, exclude={'id'})
        doc['created_at'] = datetime.utcnow()
        doc['updated_at'] = datetime.utcnow()
        
        result = await self.collection.insert_one(doc)
        logger.info(f"Created repository: {repo_data.name}")
        
        return str(result.inserted_id)
    
    async def bulk_upsert_repositories(
        self,
        repositories: List[RepositoryCreate]
    ) -> Dict[str, int]:
        """
        Bulk insert or update repositories
        
        Args:
            repositories: List of repository data
            
        Returns:
            Dictionary with counts of inserted and modified
        """
        if not repositories:
            return {'inserted': 0, 'modified': 0}
        
        operations = []
        
        for repo in repositories:
            doc = repo.model_dump(by_alias=True, exclude={'id'})
            doc['updated_at'] = datetime.utcnow()
            
            operations.append(
                UpdateOne(
                    {
                        'user_id': repo.user_id,
                        'github_id': repo.github_id
                    },
                    {
                        '$set': doc,
                        '$setOnInsert': {'created_at': datetime.utcnow()}
                    },
                    upsert=True
                )
            )
        
        result = await self.collection.bulk_write(operations, ordered=False)
        
        logger.info(
            f"Bulk upserted {len(repositories)} repositories: "
            f"{result.upserted_count} new, {result.modified_count} updated"
        )
        
        return {
            'inserted': result.upserted_count,
            'modified': result.modified_count
        }
    
    async def get_repository_by_id(self, repo_id: str) -> Optional[Repository]:
        """
        Get repository by ID
        
        Args:
            repo_id: Repository ID
            
        Returns:
            Repository or None if not found
        """
        from bson import ObjectId
        
        try:
            doc = await self.collection.find_one({'_id': ObjectId(repo_id)})
        except Exception:
            doc = await self.collection.find_one({'_id': repo_id})
        
        if doc:
            doc['_id'] = str(doc['_id'])
            return Repository(**doc)
        
        return None
    
    async def get_repository_by_github_id(
        self,
        user_id: str,
        github_id: int
    ) -> Optional[Repository]:
        """
        Get repository by GitHub ID
        
        Args:
            user_id: User ID
            github_id: GitHub repository ID
            
        Returns:
            Repository or None if not found
        """
        doc = await self.collection.find_one({
            'user_id': user_id,
            'github_id': github_id
        })
        
        if doc:
            doc['_id'] = str(doc['_id'])
            return Repository(**doc)
        
        return None
    
    async def get_user_repositories(
        self,
        user_id: str,
        category: Optional[str] = None,
        analyzed_only: bool = False
    ) -> List[Repository]:
        """
        Get repositories for a user
        
        Args:
            user_id: User ID
            category: Optional category filter (flagship/significant/supporting)
            analyzed_only: Only return analyzed repositories
            
        Returns:
            List of Repository objects
        """
        query = {'user_id': user_id}
        
        if category:
            query['category'] = category
        
        if analyzed_only:
            query['analyzed'] = True
        
        cursor = self.collection.find(query).sort('importance_score', -1)
        
        repositories = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            repositories.append(Repository(**doc))
        
        return repositories
    
    async def get_repositories_for_analysis(
        self,
        user_id: str,
        limit: int = 15
    ) -> List[Repository]:
        """
        Get repositories selected for Stage 2 analysis
        
        Returns flagship and significant repositories, limited to specified count
        
        Args:
            user_id: User ID
            limit: Maximum number of repositories
            
        Returns:
            List of Repository objects
        """
        cursor = self.collection.find({
            'user_id': user_id,
            'category': {'$in': ['flagship', 'significant']}
        }).sort('importance_score', -1).limit(limit)
        
        repositories = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            repositories.append(Repository(**doc))
        
        return repositories
    
    async def update_repository_analysis(
        self,
        repo_id: str,
        acid_scores: Dict[str, float],
        complexity_metrics: Dict[str, float],
        overall_score: float
    ) -> bool:
        """
        Update repository with analysis results
        
        Args:
            repo_id: Repository ID
            acid_scores: ACID scores dictionary
            complexity_metrics: Complexity metrics dictionary
            overall_score: Overall repository score
            
        Returns:
            True if updated successfully
        """
        from bson import ObjectId
        
        update_doc = {
            'acid_scores': acid_scores,
            'complexity_metrics': complexity_metrics,
            'overall_score': overall_score,
            'analyzed': True,
            'analyzed_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        try:
            result = await self.collection.update_one(
                {'_id': ObjectId(repo_id)},
                {'$set': update_doc}
            )
        except Exception:
            result = await self.collection.update_one(
                {'_id': repo_id},
                {'$set': update_doc}
            )
        
        return result.modified_count > 0
    
    async def update_repository_importance(
        self,
        repo_id: str,
        importance_score: float,
        category: str
    ) -> bool:
        """
        Update repository importance score and category
        
        Args:
            repo_id: Repository ID
            importance_score: Importance score (0-100)
            category: Category (flagship/significant/supporting)
            
        Returns:
            True if updated successfully
        """
        from bson import ObjectId
        
        update_doc = {
            'importance_score': importance_score,
            'category': category,
            'updated_at': datetime.utcnow()
        }
        
        try:
            result = await self.collection.update_one(
                {'_id': ObjectId(repo_id)},
                {'$set': update_doc}
            )
        except Exception:
            result = await self.collection.update_one(
                {'_id': repo_id},
                {'$set': update_doc}
            )
        
        return result.modified_count > 0
    
    async def delete_repository(self, repo_id: str) -> bool:
        """
        Delete repository
        
        Args:
            repo_id: Repository ID
            
        Returns:
            True if deleted successfully
        """
        from bson import ObjectId
        
        try:
            result = await self.collection.delete_one({'_id': ObjectId(repo_id)})
        except Exception:
            result = await self.collection.delete_one({'_id': repo_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted repository: {repo_id}")
            return True
        
        return False
    
    async def delete_user_repositories(self, user_id: str) -> int:
        """
        Delete all repositories for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of repositories deleted
        """
        result = await self.collection.delete_many({'user_id': user_id})
        
        logger.info(f"Deleted {result.deleted_count} repositories for user {user_id}")
        
        return result.deleted_count
    
    async def count_repositories(
        self,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        analyzed_only: bool = False
    ) -> int:
        """
        Count repositories matching criteria
        
        Args:
            user_id: Optional user ID filter
            category: Optional category filter
            analyzed_only: Only count analyzed repositories
            
        Returns:
            Number of matching repositories
        """
        query = {}
        
        if user_id:
            query['user_id'] = user_id
        
        if category:
            query['category'] = category
        
        if analyzed_only:
            query['analyzed'] = True
        
        return await self.collection.count_documents(query)
    
    async def get_repository_statistics(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get repository statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with statistics
        """
        total = await self.count_repositories(user_id=user_id)
        flagship = await self.count_repositories(user_id=user_id, category='flagship')
        significant = await self.count_repositories(user_id=user_id, category='significant')
        supporting = await self.count_repositories(user_id=user_id, category='supporting')
        analyzed = await self.count_repositories(user_id=user_id, analyzed_only=True)
        
        return {
            'total': total,
            'flagship': flagship,
            'significant': significant,
            'supporting': supporting,
            'analyzed': analyzed,
            'pending_analysis': flagship + significant - analyzed
        }
    
    async def get_top_repositories_by_score(
        self,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Repository]:
        """
        Get top repositories by overall score
        
        Args:
            user_id: Optional user ID filter
            limit: Maximum number of results
            
        Returns:
            List of Repository objects
        """
        query = {'analyzed': True, 'overall_score': {'$ne': None}}
        
        if user_id:
            query['user_id'] = user_id
        
        cursor = self.collection.find(query).sort('overall_score', -1).limit(limit)
        
        repositories = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            repositories.append(Repository(**doc))
        
        return repositories
    
    async def ensure_indexes(self) -> None:
        """
        Ensure required indexes exist for performance
        """
        try:
            # Compound index for user queries
            await self.collection.create_index(
                [('user_id', 1), ('importance_score', -1)],
                name='user_importance'
            )
            
            # Compound index for category queries
            await self.collection.create_index(
                [('user_id', 1), ('category', 1)],
                name='user_category'
            )
            
            # Compound index for analysis queries
            await self.collection.create_index(
                [('user_id', 1), ('analyzed', 1)],
                name='user_analyzed'
            )
            
            # Index for GitHub ID lookups
            await self.collection.create_index(
                [('user_id', 1), ('github_id', 1)],
                unique=True,
                name='user_github_id'
            )
            
            # Index for overall score queries
            await self.collection.create_index(
                [('overall_score', -1)],
                name='overall_score_desc'
            )
            
            logger.info("Repository indexes ensured")
            
        except Exception as e:
            logger.error(f"Error ensuring indexes: {e}")
