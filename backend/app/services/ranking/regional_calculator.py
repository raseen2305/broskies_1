"""
Regional Ranking Calculator
Calculates rankings and percentiles for users within regions
"""

from typing import Dict, List, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import re

from app.services.storage import RankingStorageService, UserStorageService

logger = logging.getLogger(__name__)


class RegionalRankingCalculator:
    """
    Calculates regional rankings for users
    
    Features:
    - Extract region from user location
    - Calculate rank position within region
    - Calculate percentile within region
    - Store rankings in database
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize regional ranking calculator
        
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
        
        # Extract region
        region = user.region or 'IN'
        
        # Get all users in region
        users_in_region = await self.user_storage.get_users_by_region(region)
        
        if not users_in_region:
            # User is the only one in region
            rank = 1
            percentile = 100.0
            total_users = 1
        else:
            # Calculate rank and percentile
            rank, percentile, total_users = self._calculate_rank_and_percentile(
                user.overall_score,
                [u.overall_score for u in users_in_region if u.overall_score]
            )
        
        # Store ranking
        await self.ranking_storage.update_regional_ranking(
            user_id=user_id,
            github_username=user.github_username,
            name=user.full_name,
            region=region,
            state=user.state,
            district=user.district,
            overall_score=user.overall_score,
            rank=rank,
            percentile=percentile,
            total_users=total_users
        )
        
        self.logger.info(
            f"Calculated regional ranking for {user.github_username}: "
            f"rank {rank}/{total_users} ({percentile:.1f}%)"
        )
        
        return {
            'user_id': user_id,
            'region': region,
            'rank': rank,
            'percentile': percentile,
            'total_users': total_users,
            'overall_score': user.overall_score
        }
    
    async def calculate_region_rankings(
        self,
        region: str
    ) -> int:
        """
        Calculate rankings for all users in a region
        
        Args:
            region: Region code
            
        Returns:
            Number of rankings calculated
        """
        self.logger.info(f"Calculating rankings for region: {region}")
        
        # Get all users in region
        users = await self.user_storage.get_users_by_region(region)
        
        if not users:
            self.logger.warning(f"No users found in region: {region}")
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
            await self.ranking_storage.update_regional_ranking(
                user_id=user.user_id,
                github_username=user.github_username,
                name=user.full_name,
                region=region,
                state=user.state,
                district=user.district,
                overall_score=user.overall_score or 0.0,
                rank=rank,
                percentile=round(percentile, 1),
                total_users=total_users
            )
            
            updated_count += 1
        
        self.logger.info(
            f"Calculated {updated_count} rankings for region {region}"
        )
        
        return updated_count
    
    async def calculate_all_rankings(self) -> Dict[str, int]:
        """
        Calculate rankings for all regions
        
        Returns:
            Dictionary with region -> count mapping
        """
        self.logger.info("Calculating rankings for all regions")
        
        # Get all unique regions
        regions = await self._get_all_regions()
        
        results = {}
        
        for region in regions:
            try:
                count = await self.calculate_region_rankings(region)
                results[region] = count
            except Exception as e:
                self.logger.error(f"Error calculating rankings for {region}: {e}")
                results[region] = 0
        
        total = sum(results.values())
        self.logger.info(
            f"Calculated {total} rankings across {len(regions)} regions"
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
            all_scores: List of all scores in region
            
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
    
    async def _get_all_regions(self) -> List[str]:
        """
        Get all unique regions from user profiles
        
        Returns:
            List of region codes
        """
        # Aggregate to get unique regions
        pipeline = [
            {
                '$match': {
                    'analysis_completed': True,
                    'overall_score': {'$ne': None}
                }
            },
            {
                '$group': {
                    '_id': '$region'
                }
            }
        ]
        
        cursor = self.db.user_profiles.aggregate(pipeline)
        regions = []
        
        async for doc in cursor:
            region = doc['_id']
            if region:
                regions.append(region)
        
        return regions
    
    def extract_region_from_location(
        self,
        location: Optional[str]
    ) -> str:
        """
        Extract region code from location string
        
        Args:
            location: Location string (e.g., "Mumbai, India")
            
        Returns:
            Region code (default: 'IN')
        """
        if not location:
            return 'IN'
        
        location = location.lower()
        
        # Country mappings
        country_mappings = {
            'india': 'IN',
            'united states': 'US',
            'usa': 'US',
            'united kingdom': 'UK',
            'uk': 'UK',
            'canada': 'CA',
            'australia': 'AU',
            'germany': 'DE',
            'france': 'FR',
            'japan': 'JP',
            'china': 'CN',
            'singapore': 'SG'
        }
        
        # Check for country in location
        for country, code in country_mappings.items():
            if country in location:
                return code
        
        # Default to India
        return 'IN'
    
    async def get_regional_leaderboard(
        self,
        region: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get regional leaderboard
        
        Args:
            region: Region code
            limit: Maximum number of results
            
        Returns:
            List of ranking dictionaries
        """
        rankings = await self.ranking_storage.get_regional_leaderboard(
            region,
            limit
        )
        
        return [
            {
                'user_id': r.user_id,
                'github_username': r.github_username,
                'name': r.name,
                'overall_score': r.overall_score,
                'rank': r.rank_in_region,
                'percentile': r.percentile_region
            }
            for r in rankings
        ]
    
    async def get_user_regional_rank(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's regional ranking
        
        Args:
            user_id: User ID
            
        Returns:
            Ranking dictionary or None if not found
        """
        ranking = await self.ranking_storage.get_regional_ranking(user_id)
        
        if ranking:
            return {
                'user_id': ranking.user_id,
                'region': ranking.region,
                'rank': ranking.rank_in_region,
                'percentile': ranking.percentile_region,
                'total_users': ranking.total_users_in_region,
                'overall_score': ranking.overall_score
            }
        
        return None
