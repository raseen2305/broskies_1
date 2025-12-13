"""
User Storage Service
Handles CRUD operations for user profiles
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.models.profile import UserProfile, UserProfileCreate, UserProfileUpdate

logger = logging.getLogger(__name__)


class UserStorageService:
    """
    Service for user profile storage operations
    
    Provides CRUD operations for user profiles with optimized queries
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize user storage service
        
        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.collection = database.user_profiles
    
    async def create_user_profile(
        self,
        user_id: str,
        github_username: str,
        profile_data: UserProfileCreate
    ) -> str:
        """
        Create a new user profile
        
        Args:
            user_id: User ID from auth system
            github_username: GitHub username
            profile_data: Profile creation data
            
        Returns:
            Created profile ID
            
        Raises:
            ValueError: If user already exists
        """
        # Check if user already exists
        existing = await self.get_user_by_id(user_id)
        if existing:
            raise ValueError(f"User profile already exists for user_id: {user_id}")
        
        # Prepare document
        doc = {
            'user_id': user_id,
            'github_username': github_username,
            'full_name': profile_data.full_name,
            'university': profile_data.university,
            'university_short': profile_data.university_short or '',
            'description': profile_data.description or '',
            'nationality': profile_data.nationality,
            'state': profile_data.state,
            'district': profile_data.district,
            'region': profile_data.region or 'IN',
            'overall_score': None,
            'flagship_count': 0,
            'significant_count': 0,
            'supporting_count': 0,
            'scan_completed': False,
            'scanned_at': None,
            'analysis_completed': False,
            'analyzed_at': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = await self.collection.insert_one(doc)
        logger.info(f"Created user profile for {github_username}")
        
        return str(result.inserted_id)
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile by user ID
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile or None if not found
        """
        doc = await self.collection.find_one({'user_id': user_id})
        
        if doc:
            doc['_id'] = str(doc['_id'])
            return UserProfile(**doc)
        
        return None
    
    async def get_user_by_github_username(
        self,
        github_username: str
    ) -> Optional[UserProfile]:
        """
        Get user profile by GitHub username
        
        Args:
            github_username: GitHub username
            
        Returns:
            UserProfile or None if not found
        """
        doc = await self.collection.find_one({'github_username': github_username})
        
        if doc:
            doc['_id'] = str(doc['_id'])
            return UserProfile(**doc)
        
        return None
    
    async def update_user_profile(
        self,
        user_id: str,
        profile_data: UserProfileUpdate
    ) -> bool:
        """
        Update user profile
        
        Args:
            user_id: User ID
            profile_data: Profile update data
            
        Returns:
            True if updated successfully
        """
        # Build update document (only include non-None fields)
        update_doc = {}
        
        if profile_data.full_name is not None:
            update_doc['full_name'] = profile_data.full_name
        if profile_data.university is not None:
            update_doc['university'] = profile_data.university
        if profile_data.university_short is not None:
            update_doc['university_short'] = profile_data.university_short
        if profile_data.description is not None:
            update_doc['description'] = profile_data.description
        if profile_data.nationality is not None:
            update_doc['nationality'] = profile_data.nationality
        if profile_data.state is not None:
            update_doc['state'] = profile_data.state
        if profile_data.district is not None:
            update_doc['district'] = profile_data.district
        if profile_data.region is not None:
            update_doc['region'] = profile_data.region
        
        if not update_doc:
            return False
        
        update_doc['updated_at'] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {'user_id': user_id},
            {'$set': update_doc}
        )
        
        return result.modified_count > 0
    
    async def update_user_scores(
        self,
        user_id: str,
        overall_score: float,
        flagship_count: int,
        significant_count: int,
        supporting_count: int
    ) -> bool:
        """
        Update user scores and repository counts
        
        Args:
            user_id: User ID
            overall_score: Overall developer score
            flagship_count: Number of flagship repositories
            significant_count: Number of significant repositories
            supporting_count: Number of supporting repositories
            
        Returns:
            True if updated successfully
        """
        update_doc = {
            'overall_score': overall_score,
            'flagship_count': flagship_count,
            'significant_count': significant_count,
            'supporting_count': supporting_count,
            'analysis_completed': True,
            'analyzed_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {'user_id': user_id},
            {'$set': update_doc}
        )
        
        logger.info(
            f"Updated scores for user {user_id}: "
            f"overall={overall_score:.1f}, "
            f"flagship={flagship_count}, "
            f"significant={significant_count}"
        )
        
        return result.modified_count > 0
    
    async def update_scan_status(
        self,
        user_id: str,
        scan_completed: bool = True
    ) -> bool:
        """
        Update scan completion status
        
        Args:
            user_id: User ID
            scan_completed: Scan completion status
            
        Returns:
            True if updated successfully
        """
        update_doc = {
            'scan_completed': scan_completed,
            'scanned_at': datetime.utcnow() if scan_completed else None,
            'updated_at': datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {'user_id': user_id},
            {'$set': update_doc}
        )
        
        return result.modified_count > 0
    
    async def delete_user_profile(self, user_id: str) -> bool:
        """
        Delete user profile
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted successfully
        """
        result = await self.collection.delete_one({'user_id': user_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted user profile for user_id: {user_id}")
            return True
        
        return False
    
    async def get_users_by_score_range(
        self,
        min_score: float,
        max_score: float,
        limit: int = 100
    ) -> List[UserProfile]:
        """
        Get users within a score range
        
        Args:
            min_score: Minimum overall score
            max_score: Maximum overall score
            limit: Maximum number of results
            
        Returns:
            List of UserProfile objects
        """
        cursor = self.collection.find({
            'overall_score': {
                '$gte': min_score,
                '$lte': max_score
            },
            'analysis_completed': True
        }).sort('overall_score', -1).limit(limit)
        
        users = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            users.append(UserProfile(**doc))
        
        return users
    
    async def get_top_users(self, limit: int = 100) -> List[UserProfile]:
        """
        Get top users by overall score
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of UserProfile objects
        """
        cursor = self.collection.find({
            'analysis_completed': True,
            'overall_score': {'$ne': None}
        }).sort('overall_score', -1).limit(limit)
        
        users = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            users.append(UserProfile(**doc))
        
        return users
    
    async def get_users_by_region(
        self,
        region: str,
        limit: int = 1000
    ) -> List[UserProfile]:
        """
        Get users in a specific region
        
        Args:
            region: Region code
            limit: Maximum number of results
            
        Returns:
            List of UserProfile objects
        """
        cursor = self.collection.find({
            'region': region,
            'analysis_completed': True,
            'overall_score': {'$ne': None}
        }).sort('overall_score', -1).limit(limit)
        
        users = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            users.append(UserProfile(**doc))
        
        return users
    
    async def get_users_by_university(
        self,
        university: str,
        limit: int = 1000
    ) -> List[UserProfile]:
        """
        Get users from a specific university
        
        Args:
            university: University name
            limit: Maximum number of results
            
        Returns:
            List of UserProfile objects
        """
        cursor = self.collection.find({
            'university': university,
            'analysis_completed': True,
            'overall_score': {'$ne': None}
        }).sort('overall_score', -1).limit(limit)
        
        users = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            users.append(UserProfile(**doc))
        
        return users
    
    async def count_users(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count users matching filters
        
        Args:
            filters: Optional filter criteria
            
        Returns:
            Number of matching users
        """
        if filters is None:
            filters = {}
        
        return await self.collection.count_documents(filters)
    
    async def ensure_indexes(self) -> None:
        """
        Ensure required indexes exist for performance
        """
        try:
            # Unique index on user_id
            await self.collection.create_index('user_id', unique=True)
            
            # Unique index on github_username
            await self.collection.create_index('github_username', unique=True)
            
            # Index on overall_score for leaderboards
            await self.collection.create_index(
                [('overall_score', -1)],
                name='overall_score_desc'
            )
            
            # Compound index for regional queries
            await self.collection.create_index(
                [('region', 1), ('overall_score', -1)],
                name='region_score'
            )
            
            # Compound index for university queries
            await self.collection.create_index(
                [('university', 1), ('overall_score', -1)],
                name='university_score'
            )
            
            # Index on analysis_completed for filtering
            await self.collection.create_index('analysis_completed')
            
            logger.info("User profile indexes ensured")
            
        except Exception as e:
            logger.error(f"Error ensuring indexes: {e}")
