"""
Ranking Storage Service
Handles storage of regional and university rankings
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.models.profile import RegionalScore, UniversityScore

logger = logging.getLogger(__name__)


class RankingStorageService:
    """
    Service for ranking storage operations
    
    Provides operations for storing and retrieving regional and university rankings
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize ranking storage service
        
        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.regional_collection = database.regional_scores
        self.university_collection = database.university_scores
    
    # ========================================================================
    # Regional Rankings
    # ========================================================================
    
    async def update_regional_ranking(
        self,
        user_id: str,
        github_username: str,
        name: str,
        region: str,
        state: str,
        district: str,
        overall_score: float,
        rank: int,
        percentile: float,
        total_users: int
    ) -> str:
        """
        Update or create regional ranking for a user
        
        Args:
            user_id: User ID
            github_username: GitHub username
            name: User's name
            region: Region code
            state: State
            district: District
            overall_score: Overall score
            rank: Rank in region
            percentile: Percentile in region
            total_users: Total users in region
            
        Returns:
            Ranking ID
        """
        doc = {
            'user_id': user_id,
            'github_username': github_username,
            'name': name,
            'region': region,
            'state': state,
            'district': district,
            'overall_score': overall_score,
            'percentile_region': percentile,
            'rank_in_region': rank,
            'total_users_in_region': total_users,
            'updated_at': datetime.utcnow()
        }
        
        result = await self.regional_collection.update_one(
            {'user_id': user_id},
            {'$set': doc},
            upsert=True
        )
        
        logger.info(
            f"Updated regional ranking for {github_username}: "
            f"rank {rank}/{total_users} in {region}"
        )
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            existing = await self.regional_collection.find_one({'user_id': user_id})
            return str(existing['_id']) if existing else user_id
    
    async def get_regional_ranking(
        self,
        user_id: str
    ) -> Optional[RegionalScore]:
        """
        Get regional ranking for a user
        
        Args:
            user_id: User ID
            
        Returns:
            RegionalScore or None if not found
        """
        doc = await self.regional_collection.find_one({'user_id': user_id})
        
        if doc:
            doc['_id'] = str(doc['_id'])
            return RegionalScore(**doc)
        
        return None
    
    async def get_regional_leaderboard(
        self,
        region: str,
        limit: int = 100
    ) -> List[RegionalScore]:
        """
        Get regional leaderboard
        
        Args:
            region: Region code
            limit: Maximum number of results
            
        Returns:
            List of RegionalScore objects
        """
        cursor = self.regional_collection.find({
            'region': region
        }).sort('overall_score', -1).limit(limit)
        
        rankings = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            rankings.append(RegionalScore(**doc))
        
        return rankings
    
    async def calculate_regional_rankings(
        self,
        region: str
    ) -> int:
        """
        Calculate and update rankings for all users in a region
        
        Args:
            region: Region code
            
        Returns:
            Number of rankings updated
        """
        # Get all users in region sorted by score
        cursor = self.regional_collection.find({
            'region': region
        }).sort('overall_score', -1)
        
        users = await cursor.to_list(length=None)
        total_users = len(users)
        
        if total_users == 0:
            return 0
        
        # Calculate rankings and percentiles
        updated_count = 0
        for i, user in enumerate(users):
            rank = i + 1
            
            # Calculate percentile (higher is better)
            users_below = total_users - rank
            percentile = (users_below / total_users) * 100 if total_users > 1 else 100.0
            
            # Update ranking
            result = await self.regional_collection.update_one(
                {'_id': user['_id']},
                {
                    '$set': {
                        'rank_in_region': rank,
                        'percentile_region': round(percentile, 1),
                        'total_users_in_region': total_users,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                updated_count += 1
        
        logger.info(f"Updated {updated_count} regional rankings in {region}")
        
        return updated_count
    
    async def delete_regional_ranking(self, user_id: str) -> bool:
        """
        Delete regional ranking for a user
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted successfully
        """
        result = await self.regional_collection.delete_one({'user_id': user_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted regional ranking for user: {user_id}")
            return True
        
        return False
    
    # ========================================================================
    # University Rankings
    # ========================================================================
    
    async def update_university_ranking(
        self,
        user_id: str,
        github_username: str,
        name: str,
        university: str,
        university_short: str,
        overall_score: float,
        rank: int,
        percentile: float,
        total_users: int
    ) -> str:
        """
        Update or create university ranking for a user
        
        Args:
            user_id: User ID
            github_username: GitHub username
            name: User's name
            university: University name
            university_short: University short name
            overall_score: Overall score
            rank: Rank in university
            percentile: Percentile in university
            total_users: Total users in university
            
        Returns:
            Ranking ID
        """
        doc = {
            'user_id': user_id,
            'github_username': github_username,
            'name': name,
            'university': university,
            'university_short': university_short,
            'overall_score': overall_score,
            'percentile_university': percentile,
            'rank_in_university': rank,
            'total_users_in_university': total_users,
            'updated_at': datetime.utcnow()
        }
        
        result = await self.university_collection.update_one(
            {'user_id': user_id},
            {'$set': doc},
            upsert=True
        )
        
        logger.info(
            f"Updated university ranking for {github_username}: "
            f"rank {rank}/{total_users} in {university_short}"
        )
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            existing = await self.university_collection.find_one({'user_id': user_id})
            return str(existing['_id']) if existing else user_id
    
    async def get_university_ranking(
        self,
        user_id: str
    ) -> Optional[UniversityScore]:
        """
        Get university ranking for a user
        
        Args:
            user_id: User ID
            
        Returns:
            UniversityScore or None if not found
        """
        doc = await self.university_collection.find_one({'user_id': user_id})
        
        if doc:
            doc['_id'] = str(doc['_id'])
            return UniversityScore(**doc)
        
        return None
    
    async def get_university_leaderboard(
        self,
        university: str,
        limit: int = 100
    ) -> List[UniversityScore]:
        """
        Get university leaderboard
        
        Args:
            university: University name
            limit: Maximum number of results
            
        Returns:
            List of UniversityScore objects
        """
        cursor = self.university_collection.find({
            'university': university
        }).sort('overall_score', -1).limit(limit)
        
        rankings = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            rankings.append(UniversityScore(**doc))
        
        return rankings
    
    async def calculate_university_rankings(
        self,
        university: str
    ) -> int:
        """
        Calculate and update rankings for all users in a university
        
        Args:
            university: University name
            
        Returns:
            Number of rankings updated
        """
        # Get all users in university sorted by score
        cursor = self.university_collection.find({
            'university': university
        }).sort('overall_score', -1)
        
        users = await cursor.to_list(length=None)
        total_users = len(users)
        
        if total_users == 0:
            return 0
        
        # Calculate rankings and percentiles
        updated_count = 0
        for i, user in enumerate(users):
            rank = i + 1
            
            # Calculate percentile (higher is better)
            users_below = total_users - rank
            percentile = (users_below / total_users) * 100 if total_users > 1 else 100.0
            
            # Update ranking
            result = await self.university_collection.update_one(
                {'_id': user['_id']},
                {
                    '$set': {
                        'rank_in_university': rank,
                        'percentile_university': round(percentile, 1),
                        'total_users_in_university': total_users,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                updated_count += 1
        
        logger.info(f"Updated {updated_count} university rankings in {university}")
        
        return updated_count
    
    async def delete_university_ranking(self, user_id: str) -> bool:
        """
        Delete university ranking for a user
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted successfully
        """
        result = await self.university_collection.delete_one({'user_id': user_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted university ranking for user: {user_id}")
            return True
        
        return False
    
    # ========================================================================
    # Combined Operations
    # ========================================================================
    
    async def update_all_rankings(
        self,
        user_id: str,
        github_username: str,
        name: str,
        region: str,
        state: str,
        district: str,
        university: str,
        university_short: str,
        overall_score: float
    ) -> Dict[str, str]:
        """
        Update both regional and university rankings for a user
        
        Args:
            user_id: User ID
            github_username: GitHub username
            name: User's name
            region: Region code
            state: State
            district: District
            university: University name
            university_short: University short name
            overall_score: Overall score
            
        Returns:
            Dictionary with regional and university ranking IDs
        """
        # Calculate regional rankings
        await self.calculate_regional_rankings(region)
        
        # Calculate university rankings
        await self.calculate_university_rankings(university)
        
        # Get updated rankings
        regional = await self.get_regional_ranking(user_id)
        university_rank = await self.get_university_ranking(user_id)
        
        return {
            'regional_id': str(regional.id) if regional else None,
            'university_id': str(university_rank.id) if university_rank else None
        }
    
    async def get_user_rankings(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get both regional and university rankings for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with both rankings
        """
        regional = await self.get_regional_ranking(user_id)
        university = await self.get_university_ranking(user_id)
        
        return {
            'regional': regional.model_dump() if regional else None,
            'university': university.model_dump() if university else None
        }
    
    async def delete_user_rankings(self, user_id: str) -> Dict[str, bool]:
        """
        Delete both regional and university rankings for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with deletion results
        """
        regional_deleted = await self.delete_regional_ranking(user_id)
        university_deleted = await self.delete_university_ranking(user_id)
        
        return {
            'regional_deleted': regional_deleted,
            'university_deleted': university_deleted
        }
    
    async def ensure_indexes(self) -> None:
        """
        Ensure required indexes exist for performance
        """
        try:
            # Regional collection indexes
            await self.regional_collection.create_index('user_id', unique=True)
            await self.regional_collection.create_index(
                [('region', 1), ('overall_score', -1)],
                name='region_score'
            )
            await self.regional_collection.create_index('overall_score')
            
            # University collection indexes
            await self.university_collection.create_index('user_id', unique=True)
            await self.university_collection.create_index(
                [('university', 1), ('overall_score', -1)],
                name='university_score'
            )
            await self.university_collection.create_index('overall_score')
            
            logger.info("Ranking indexes ensured")
            
        except Exception as e:
            logger.error(f"Error ensuring indexes: {e}")
