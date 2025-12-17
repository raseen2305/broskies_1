"""
Redis Cache Service
Provides caching functionality using Redis
"""
import json
import logging
from typing import Any, Optional
import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.default_ttl = 3600  # 1 hour default TTL
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Connected to Redis successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    def _make_key(self, key: str, prefix: str = "") -> str:
        """Create a cache key with optional prefix"""
        if prefix:
            return f"{prefix}:{key}"
        return key
    
    async def get(self, key: str, prefix: str = "") -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            prefix: Optional prefix for the key
            
        Returns:
            Cached value or None if not found
        """
        if not self.redis_client:
            return None
            
        try:
            cache_key = self._make_key(key, prefix)
            value = await self.redis_client.get(cache_key)
            
            if value:
                # Try to parse as JSON
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        prefix: str = "",
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            prefix: Optional prefix for the key
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            cache_key = self._make_key(key, prefix)
            ttl = ttl or self.default_ttl
            
            # Serialize value to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = str(value)
            
            await self.redis_client.setex(cache_key, ttl, value)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str, prefix: str = "") -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            prefix: Optional prefix for the key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            cache_key = self._make_key(key, prefix)
            await self.redis_client.delete(cache_key)
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str, prefix: str = "") -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
            
        try:
            cache_key = self._make_key(key, prefix)
            return await self.redis_client.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern
        
        Args:
            pattern: Redis key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
            
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Cache invalidate pattern error for {pattern}: {e}")
            return 0
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        if not self.redis_client:
            return {"connected": False}
            
        try:
            info = await self.redis_client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"connected": False, "error": str(e)}
    
    # Convenience methods for common cache operations
    
    async def cache_analysis_results(
        self,
        username: str,
        results: dict,
        ttl: int = 86400
    ) -> bool:
        """Cache analysis results for a user (24 hours default)"""
        return await self.set(username, results, prefix="analysis_results", ttl=ttl)
    
    async def get_analysis_results(self, username: str) -> Optional[dict]:
        """Get cached analysis results for a user"""
        return await self.get(username, prefix="analysis_results")
    
    async def invalidate_analysis_results(self, username: str) -> bool:
        """Invalidate cached analysis results for a user"""
        return await self.delete(username, prefix="analysis_results")
    
    async def cache_importance_scores(
        self,
        username: str,
        scores: dict,
        ttl: int = 86400
    ) -> bool:
        """Cache importance scores for repositories"""
        return await self.set(username, scores, prefix="importance_scores", ttl=ttl)
    
    async def get_importance_scores(self, username: str) -> Optional[dict]:
        """Get cached importance scores"""
        return await self.get(username, prefix="importance_scores")


# Global cache service instance
cache_service = CacheService()
