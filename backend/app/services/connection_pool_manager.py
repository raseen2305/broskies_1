"""
Connection Pool Manager

This service manages connection pools for database and API connections
to improve performance and resource utilization.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncContextManager
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from dataclasses import dataclass
import time

# Optional imports with fallbacks
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

try:
    import motor.motor_asyncio
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    motor = None

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

@dataclass
class PoolStats:
    """Connection pool statistics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    created_connections: int = 0
    closed_connections: int = 0
    failed_connections: int = 0
    average_connection_time: float = 0.0
    peak_connections: int = 0

class HTTPConnectionPool:
    """HTTP connection pool for API requests"""
    
    def __init__(self, 
                 max_connections: int = 100,
                 max_connections_per_host: int = 30,
                 timeout: float = 30.0):
        
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.timeout = timeout
        self.stats = PoolStats()
        self.connection_times = []
        
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp not available, HTTP connection pooling disabled")
            self.session = None
            return
        
        # Connection pool configuration
        connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_connections_per_host,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        # Timeout configuration
        timeout_config = aiohttp.ClientTimeout(
            total=timeout,
            connect=10.0,
            sock_read=timeout
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config,
            headers={
                'User-Agent': 'GitHub-Scanner/1.0'
            }
        )
        
    async def close(self):
        """Close the HTTP connection pool"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("HTTP connection pool closed")
    
    @asynccontextmanager
    async def get_session(self):
        """Get an HTTP session from the pool"""
        if not AIOHTTP_AVAILABLE or self.session is None:
            raise RuntimeError("aiohttp not available, cannot create HTTP session")
        
        start_time = time.time()
        
        try:
            self.stats.active_connections += 1
            self.stats.peak_connections = max(
                self.stats.peak_connections, 
                self.stats.active_connections
            )
            
            yield self.session
            
            # Record successful connection
            connection_time = time.time() - start_time
            self.connection_times.append(connection_time)
            
            # Keep only last 1000 connection times
            if len(self.connection_times) > 1000:
                self.connection_times = self.connection_times[-1000:]
            
            # Update average
            self.stats.average_connection_time = sum(self.connection_times) / len(self.connection_times)
            
        except Exception as e:
            self.stats.failed_connections += 1
            logger.error(f"HTTP connection error: {e}")
            raise
        finally:
            self.stats.active_connections -= 1
    
    def get_stats(self) -> PoolStats:
        """Get connection pool statistics"""
        # Update current stats
        if hasattr(self.session, '_connector') and self.session._connector:
            connector = self.session._connector
            self.stats.total_connections = len(connector._conns)
            self.stats.idle_connections = sum(
                len(conns) for conns in connector._conns.values()
            )
        
        return self.stats

class MongoConnectionPool:
    """MongoDB connection pool manager"""
    
    def __init__(self, 
                 connection_string: str,
                 database_name: str,
                 max_pool_size: int = 50,
                 min_pool_size: int = 5):
        
        self.connection_string = connection_string
        self.database_name = database_name
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.stats = PoolStats()
        
        if not MOTOR_AVAILABLE:
            logger.warning("motor not available, MongoDB connection pooling disabled")
            self.client = None
            self.database = None
            return
        
        # Create MongoDB client with connection pooling
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            connection_string,
            maxPoolSize=max_pool_size,
            minPoolSize=min_pool_size,
            maxIdleTimeMS=30000,
            waitQueueTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000
        )
        
        self.database = self.client[database_name]
        
    async def close(self):
        """Close the MongoDB connection pool"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection pool closed")
    
    @asynccontextmanager
    async def get_database(self):
        """Get a database connection from the pool"""
        if not MOTOR_AVAILABLE or self.database is None:
            raise RuntimeError("motor not available, cannot create MongoDB connection")
        
        start_time = time.time()
        
        try:
            self.stats.active_connections += 1
            yield self.database
            
            # Record successful connection
            connection_time = time.time() - start_time
            self.stats.average_connection_time = (
                (self.stats.average_connection_time * self.stats.created_connections + connection_time) /
                (self.stats.created_connections + 1)
            )
            self.stats.created_connections += 1
            
        except Exception as e:
            self.stats.failed_connections += 1
            logger.error(f"MongoDB connection error: {e}")
            raise
        finally:
            self.stats.active_connections -= 1
    
    async def ping(self) -> bool:
        """Test MongoDB connection"""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB ping failed: {e}")
            return False
    
    def get_stats(self) -> PoolStats:
        """Get MongoDB connection pool statistics"""
        return self.stats

class RedisConnectionPool:
    """Redis connection pool manager"""
    
    def __init__(self, 
                 redis_url: str,
                 max_connections: int = 50,
                 retry_on_timeout: bool = True):
        
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.stats = PoolStats()
        
        if not REDIS_AVAILABLE:
            logger.warning("redis.asyncio not available, Redis connection pooling disabled")
            self.pool = None
            return
        
        # Create Redis connection pool
        self.pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            retry_on_timeout=retry_on_timeout,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30
        )
        
    async def close(self):
        """Close the Redis connection pool"""
        if self.pool:
            await self.pool.disconnect()
            logger.info("Redis connection pool closed")
    
    @asynccontextmanager
    async def get_redis(self):
        """Get a Redis connection from the pool"""
        if not REDIS_AVAILABLE or self.pool is None:
            raise RuntimeError("redis.asyncio not available, cannot create Redis connection")
        
        start_time = time.time()
        redis_client = None
        
        try:
            redis_client = redis.Redis(connection_pool=self.pool)
            self.stats.active_connections += 1
            
            yield redis_client
            
            # Record successful connection
            connection_time = time.time() - start_time
            self.stats.average_connection_time = (
                (self.stats.average_connection_time * self.stats.created_connections + connection_time) /
                (self.stats.created_connections + 1)
            )
            self.stats.created_connections += 1
            
        except Exception as e:
            self.stats.failed_connections += 1
            logger.error(f"Redis connection error: {e}")
            raise
        finally:
            if redis_client:
                await redis_client.close()
            self.stats.active_connections -= 1
    
    async def ping(self) -> bool:
        """Test Redis connection"""
        try:
            async with self.get_redis() as redis_client:
                await redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    def get_stats(self) -> PoolStats:
        """Get Redis connection pool statistics"""
        return self.stats

class ConnectionPoolManager:
    """Manages all connection pools"""
    
    def __init__(self):
        self.http_pool: Optional[HTTPConnectionPool] = None
        self.mongo_pool: Optional[MongoConnectionPool] = None
        self.redis_pool: Optional[RedisConnectionPool] = None
        self.initialized = False
        
    async def initialize(self, 
                        mongo_connection_string: str = None,
                        mongo_database: str = None,
                        redis_url: str = None,
                        http_max_connections: int = 100):
        """Initialize all connection pools"""
        
        try:
            # Initialize HTTP connection pool
            self.http_pool = HTTPConnectionPool(max_connections=http_max_connections)
            logger.info("HTTP connection pool initialized")
            
            # Initialize MongoDB connection pool
            if mongo_connection_string and mongo_database:
                self.mongo_pool = MongoConnectionPool(
                    mongo_connection_string, 
                    mongo_database
                )
                
                # Test connection
                if await self.mongo_pool.ping():
                    logger.info("MongoDB connection pool initialized")
                else:
                    logger.warning("MongoDB connection pool initialized but ping failed")
            
            # Initialize Redis connection pool
            if redis_url:
                self.redis_pool = RedisConnectionPool(redis_url)
                
                # Test connection
                if await self.redis_pool.ping():
                    logger.info("Redis connection pool initialized")
                else:
                    logger.warning("Redis connection pool initialized but ping failed")
            
            self.initialized = True
            logger.info("Connection pool manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pools: {e}")
            raise
    
    async def close_all(self):
        """Close all connection pools"""
        
        if self.http_pool:
            await self.http_pool.close()
        
        if self.mongo_pool:
            await self.mongo_pool.close()
        
        if self.redis_pool:
            await self.redis_pool.close()
        
        self.initialized = False
        logger.info("All connection pools closed")
    
    def get_http_pool(self) -> HTTPConnectionPool:
        """Get HTTP connection pool"""
        if not self.http_pool:
            raise RuntimeError("HTTP connection pool not initialized")
        return self.http_pool
    
    def get_mongo_pool(self) -> MongoConnectionPool:
        """Get MongoDB connection pool"""
        if not self.mongo_pool:
            raise RuntimeError("MongoDB connection pool not initialized")
        return self.mongo_pool
    
    def get_redis_pool(self) -> RedisConnectionPool:
        """Get Redis connection pool"""
        if not self.redis_pool:
            raise RuntimeError("Redis connection pool not initialized")
        return self.redis_pool
    
    def get_all_stats(self) -> Dict[str, PoolStats]:
        """Get statistics for all connection pools"""
        stats = {}
        
        if self.http_pool:
            stats['http'] = self.http_pool.get_stats()
        
        if self.mongo_pool:
            stats['mongodb'] = self.mongo_pool.get_stats()
        
        if self.redis_pool:
            stats['redis'] = self.redis_pool.get_stats()
        
        return stats
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all connection pools"""
        health = {}
        
        if self.http_pool:
            # HTTP pool is healthy if session is not closed
            if self.http_pool.session is not None:
                health['http'] = not self.http_pool.session.closed
            else:
                health['http'] = False  # aiohttp not available
        
        if self.mongo_pool:
            health['mongodb'] = await self.mongo_pool.ping()
        
        if self.redis_pool:
            health['redis'] = await self.redis_pool.ping()
        
        return health

# Global connection pool manager instance
connection_pool_manager = ConnectionPoolManager()

async def initialize_connection_pools(mongo_connection_string: str = None,
                                    mongo_database: str = None,
                                    redis_url: str = None,
                                    http_max_connections: int = 100):
    """Initialize the global connection pool manager"""
    await connection_pool_manager.initialize(
        mongo_connection_string=mongo_connection_string,
        mongo_database=mongo_database,
        redis_url=redis_url,
        http_max_connections=http_max_connections
    )
    logger.info("Connection pool manager initialized")

async def shutdown_connection_pools():
    """Shutdown the global connection pool manager"""
    await connection_pool_manager.close_all()
    logger.info("Connection pool manager shutdown")