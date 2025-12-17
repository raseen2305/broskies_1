"""
Cache Manager
Manages caching for performance optimization
"""

import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import asyncio
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages in-memory caching for performance optimization
    
    Provides simple key-value caching with TTL support
    """
    
    def __init__(self):
        """Initialize cache manager"""
        self._cache: dict = {}
        self._ttl: dict = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        # Check TTL
        if key in self._ttl:
            import time
            if time.time() > self._ttl[key]:
                # Expired
                del self._cache[key]
                del self._ttl[key]
                return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        self._cache[key] = value
        
        if ttl:
            import time
            self._ttl[key] = time.time() + ttl
    
    def delete(self, key: str):
        """
        Delete value from cache
        
        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
        if key in self._ttl:
            del self._ttl[key]
    
    def clear(self):
        """Clear all cache"""
        self._cache = {}
        self._ttl = {}
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        import time
        current_time = time.time()
        
        expired_count = sum(
            1 for key, expiry in self._ttl.items()
            if expiry < current_time
        )
        
        return {
            'total_keys': len(self._cache),
            'expired_keys': expired_count,
            'active_keys': len(self._cache) - expired_count
        }


# Global instance
_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """
    Get global cache manager instance
    
    Returns:
        CacheManager instance
    """
    return _cache_manager


def cache_result(ttl: int = 300, key_prefix: str = ''):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Optional prefix for cache key
        
    Usage:
        @cache_result(ttl=600, key_prefix='user')
        async def get_user(user_id: str):
            return await fetch_user(user_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            
            # Add args to key
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
                else:
                    # Hash complex objects
                    key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
            
            # Add kwargs to key
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}={v}")
                else:
                    key_parts.append(f"{k}={hashlib.md5(str(v).encode()).hexdigest()[:8]}")
            
            cache_key = ':'.join(key_parts)
            
            # Try to get from cache
            cache_manager = get_cache_manager()
            cached_value = cache_manager.get(cache_key)
            
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key (same logic as async)
            key_parts = [key_prefix, func.__name__]
            
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
                else:
                    key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
            
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}={v}")
                else:
                    key_parts.append(f"{k}={hashlib.md5(str(v).encode()).hexdigest()[:8]}")
            
            cache_key = ':'.join(key_parts)
            
            # Try to get from cache
            cache_manager = get_cache_manager()
            cached_value = cache_manager.get(cache_key)
            
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Convenience functions
def get_cached(key: str) -> Optional[Any]:
    """
    Get value from cache
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None
    """
    return get_cache_manager().get(key)


def set_cached(key: str, value: Any, ttl: Optional[int] = None):
    """
    Set value in cache
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds
    """
    get_cache_manager().set(key, value, ttl)


def delete_cached(key: str):
    """
    Delete value from cache
    
    Args:
        key: Cache key
    """
    get_cache_manager().delete(key)


def clear_cache():
    """Clear all cache"""
    get_cache_manager().clear()


def get_cache_stats() -> dict:
    """
    Get cache statistics
    
    Returns:
        Dictionary with cache stats
    """
    return get_cache_manager().get_stats()
