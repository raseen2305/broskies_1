"""
University Ranking Calculator
Calculates rankings and percentiles for users within universities
"""

from typing import Dict, List, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.services.storage import RankingStorageService, UserStorageService

logger = logging.getLogger(__name__)


class UniversityRankingCalculator:
    """
    Calculates university rankings for users
    
    Features:
    - Calculate rank position within university
    - Calculate percentile within university
    - Store rankings in database
    - Generate university leaderboards
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize university ranking calculator
        
        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.ranking_storage = RankingStorageService(database)
        self.user_storage = UserStorageService(database)
        self.logger = logger
    
    async def calculate_user_ranking(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Calculate ranking for a specific user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with ranking information
        """
        # Get user profile
        user = await self.user_storage.get_user_by_id(user_id)
        
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        if not user.overall_score:
            raise ValueError(f"User has no overall score: {user_id}")
        
        if not user.university:
            raise ValueError(f"User has no university: {user_id}")
        
        # Get all users in university
        users_in_university = await self.user_storage.get_users_by_university(
            user.university
        )
        
        if not users_in_university:
            # User is the only one in university
            rank = 1
            percentile = 100.0
            total_users = 1
        else:
            # Calculate rank and percentile
            rank, percentile, total_users = self._calculate_rank_and_percentile(
                user.overall_score,
                [u.overall_score for u in users_in_university if u.overall_score]
            )
        
        # Store ranking
        await self.ranking_storage.update_university_ranking(
            user_id=user_id,
            github_username=user.github_username,
            name=user.full_name,
            university=user.university,
            university_short=user.university_short or user.university,
            overall_score=user.overall_score,
            rank=rank,
            percentile=percentile,
            total_users=total_users
        )
        
        self.logger.info(
            f"Calculated university ranking for {user.github_username}: "
            f"rank {rank}/{total_users} ({percentile:.1f}%) in {user.university_short}"
        )
        
        return {
            'user_id': user_id,
            'university': user.university,
            'university_short': user.university_short,
            'rank': rank,
            'percentile': percentile,
            'total_users': total_users,
            'overall_score': user.overall_score
        }
    
    async def calculate_university_rankings(
        self,
        university: str
    ) -> int:
        """
        Calculate rankings for all users in a university
        
        Args:
            university: University name
            
        Returns:
            Number of rankings calculated
        """
        self.logger.info(f"Calculating rankings for university: {university}")
        
        # Get all users in university
        users = await self.user_storage.get_users_by_university(university)
        
        if not users:
            self.logger.warning(f"No users found in university: {university}")
            return 0
        
        # Sort by overall score (descending)
        users.sort(key=lambda u: u.overall_score or 0.0, reverse=True)
        
        total_users = len(users)
        updated_count = 0
        
        # Calculate rankings
        for i, user in enumerate(users):
            rank = i + 1
            
            # Calculate percentile (higher is better)
            users_below = total_users - rank
            percentile = (users_below / total_users * 100) if total_users > 1 else 100.0
            
            # Store ranking
            await self.ranking_storage.update_university_ranking(
                user_id=user.user_id,
                github_username=user.github_username,
                name=user.full_name,
                university=user.university,
                university_short=user.university_short or user.university,
                overall_score=user.overall_score or 0.0,
                rank=rank,
                percentile=round(percentile, 1),
                total_users=total_users
            )
            
            updated_count += 1
        
        self.logger.info(
            f"Calculated {updated_count} rankings for university {university}"
        )
        
        return updated_count
    
    async def calculate_all_rankings(self) -> Dict[str, int]:
        """
        Calculate rankings for all universities
        
        Returns:
            Dictionary with university -> count mapping
        """
        self.logger.info("Calculating rankings for all universities")
        
        # Get all unique universities
        universities = await self._get_all_universities()
        
        results = {}
        
        for university in universities:
            try:
                count = await self.calculate_university_rankings(university)
                results[university] = count
            except Exception as e:
                self.logger.error(
                    f"Error calculating rankings for {university}: {e}"
                )
                results[university] = 0
        
        total = sum(results.values())
        self.logger.info(
            f"Calculated {total} rankings across {len(universities)} universities"
        )
        
        return results
    
    def _calculate_rank_and_percentile(
        self,
        user_score: float,
        all_scores: List[float]
    ) -> Tuple[int, float, int]:
        """
        Calculate rank and percentile for a user
        
        Args:
            user_score: User's overall score
            all_scores: List of all scores in university
            
        Returns:
            Tuple of (rank, percentile, total_users)
        """
        if not all_scores:
            return 1, 100.0, 1
        
        # Sort scores in descending order
        sorted_scores = sorted(all_scores, reverse=True)
        
        # Find rank (1-based)
        rank = 1
        for score in sorted_scores:
            if score > user_score:
                rank += 1
            else:
                break
        
        total_users = len(sorted_scores)
        
        # Calculate percentile (higher is better)
        users_below = total_users - rank
        percentile = (users_below / total_users * 100) if total_users > 1 else 100.0
        
        return rank, round(percentile, 1), total_users
    
    async def _get_all_universities(self) -> List[str]:
        """
        Get all unique universities from user profiles
        
        Returns:
            List of university names
        """
        # Aggregate to get unique universities
        pipeline = [
            {
                '$match': {
                    'analysis_completed': True,
                    'overall_score': {'$ne': None},
                    'university': {'$ne': None, '$ne': ''}
                }
            },
            {
                '$group': {
                    '_id': '$university'
                }
            }
        ]
        
        cursor = self.db.user_profiles.aggregate(pipeline)
        universities = []
        
        async for doc in cursor:
            university = doc['_id']
            if university:
                universities.append(university)
        
        return universities
    
    async def get_university_leaderboard(
        self,
        university: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get university leaderboard
        
        Args:
            university: University name
            limit: Maximum number of results
            
        Returns:
            List of ranking dictionaries
        """
        rankings = await self.ranking_storage.get_university_leaderboard(
            university,
            limit
        )
        
        return [
            {
                'user_id': r.user_id,
                'github_username': r.github_username,
                'name': r.name,
                'overall_score': r.overall_score,
                'rank': r.rank_in_university,
                'percentile': r.percentile_university
            }
            for r in rankings
        ]
    
    async def get_user_university_rank(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's university ranking
        
        Args:
            user_id: User ID
            
        Returns:
            Ranking dictionary or None if not found
        """
        ranking = await self.ranking_storage.get_university_ranking(user_id)
        
        if ranking:
            return {
                'user_id': ranking.user_id,
                'university': ranking.university,
                'university_short': ranking.university_short,
                'rank': ranking.rank_in_university,
                'percentile': ranking.percentile_university,
                'total_users': ranking.total_users_in_university,
                'overall_score': ranking.overall_score
            }
        
        return None
    
    async def get_top_universities(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top universities by average score
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of university statistics
        """
        # Aggregate to get university statistics
        pipeline = [
            {
                '$match': {
                    'analysis_completed': True,
                    'overall_score': {'$ne': None},
                    'university': {'$ne': None, '$ne': ''}
                }
            },
            {
                '$group': {
                    '_id': '$university',
                    'university_short': {'$first': '$university_short'},
                    'avg_score': {'$avg': '$overall_score'},
                    'user_count': {'$sum': 1},
                    'max_score': {'$max': '$overall_score'},
                    'min_score': {'$min': '$overall_score'}
                }
            },
            {
                '$sort': {'avg_score': -1}
            },
            {
                '$limit': limit
            }
        ]
        
        cursor = self.db.user_profiles.aggregate(pipeline)
        universities = []
        
        async for doc in cursor:
            universities.append({
                'university': doc['_id'],
                'university_short': doc.get('university_short', doc['_id']),
                'average_score': round(doc['avg_score'], 1),
                'user_count': doc['user_count'],
                'max_score': round(doc['max_score'], 1),
                'min_score': round(doc['min_score'], 1)
            })
        
        return universities
