"""
Cache Invalidation Service
Provides utilities for invalidating cached data
"""
import logging
from typing import List, Optional
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class CacheInvalidationService:
    """Service for invalidating cached data"""
    
    async def invalidate_user_cache(self, user_id: str) -> bool:
        """
        Invalidate all cached data for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear user-specific caches
            await cache_service.delete(user_id, "user_profile")
            await cache_service.delete(user_id, "scan_results")
            await cache_service.delete(user_id, "user_stats")
            
            # Clear user repositories cache (all pagination combinations)
            for limit in [20, 50, 100]:
                for skip in range(0, 200, limit):  # Clear first few pages
                    cache_key = f"{user_id}:repos:{limit}:{skip}"
                    await cache_service.delete(cache_key, "user_repos")
            
            # Clear user evaluations cache
            for limit in [20, 50, 100]:
                cache_key = f"{user_id}:evaluations:{limit}"
                await cache_service.delete(cache_key, "user_evaluations")
            
            logger.info(f"Invalidated cache for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate user cache for {user_id}: {e}")
            return False
    
    async def invalidate_repository_cache(self, repo_full_name: str) -> bool:
        """
        Invalidate cached data for a repository
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear repository analysis cache
            await cache_service.delete(repo_full_name, "repo_analysis")
            await cache_service.delete(repo_full_name, "repo_evaluation")
            await cache_service.delete(repo_full_name, "repo_metrics")
            
            logger.info(f"Invalidated cache for repository {repo_full_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate repository cache for {repo_full_name}: {e}")
            return False
    
    async def invalidate_scan_cache(self, scan_id: str) -> bool:
        """
        Invalidate cached data for a scan
        
        Args:
            scan_id: Scan identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await cache_service.delete(scan_id, "scan_progress")
            await cache_service.delete(scan_id, "scan_results")
            await cache_service.delete(scan_id, "scan_status")
            
            logger.info(f"Invalidated cache for scan {scan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate scan cache for {scan_id}: {e}")
            return False
    
    async def invalidate_analysis_cache(self, username: str) -> bool:
        """
        Invalidate cached analysis data for a user
        
        Args:
            username: GitHub username
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await cache_service.invalidate_analysis_results(username)
            await cache_service.delete(username, "importance_scores")
            
            # Invalidate all analysis states for this user
            await cache_service.invalidate_pattern(f"analysis_state:*{username}*")
            
            logger.info(f"Invalidated analysis cache for {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate analysis cache for {username}: {e}")
            return False
    
    async def invalidate_all_user_data(self, username: str, user_id: str = None) -> bool:
        """
        Invalidate all cached data for a user (comprehensive)
        
        Args:
            username: GitHub username
            user_id: Optional user ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Invalidate by username
            await self.invalidate_analysis_cache(username)
            
            # Invalidate by user_id if provided
            if user_id:
                await self.invalidate_user_cache(user_id)
            
            # Invalidate pattern-based caches
            await cache_service.invalidate_pattern(f"*{username}*")
            
            logger.info(f"Invalidated all cached data for {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate all user data for {username}: {e}")
            return False


# Global cache invalidation service instance
cache_invalidation_service = CacheInvalidationService()
