#!/usr/bin/env python3
"""
Connection Diagnostic Script
Tests database and cache connections to identify health check failures
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

async def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongodb_url = os.getenv("MONGODB_URL", "mongodb+srv://thoshifraseen4_db_user:iojkJvAoEhBOLbmM@online-evaluation.lkxqo8m.mongodb.net/?retryWrites=true&w=majority&appName=online-evaluation")
        database_name = os.getenv("DATABASE_NAME", "broskieshub")
        
        logger.info(f"Testing MongoDB connection to: {mongodb_url[:50]}...")
        logger.info(f"Database name: {database_name}")
        
        client = AsyncIOMotorClient(mongodb_url, serverSelectionTimeoutMS=10000)
        db = client[database_name]
        
        # Test connection with ping
        await client.admin.command('ping')
        logger.info("✅ MongoDB connection successful")
        
        # Test database access
        collections = await db.list_collection_names()
        logger.info(f"✅ Database accessible, found {len(collections)} collections")
        
        # Test a simple query
        if "regional_rankings" in collections:
            count = await db.regional_rankings.count_documents({})
            logger.info(f"✅ Sample query successful, regional_rankings has {count} documents")
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return False

async def test_redis_connection():
    """Test Redis connection"""
    try:
        import redis.asyncio as redis
        
        # Try multiple Redis URLs
        redis_urls = [
            os.getenv("REDIS_URL"),
            "redis://default:H2fhJw9TnGHT2Q1aAWlrEtxgDVslpFtG@redis-11883.c330.asia-south1-1.gce.redns.redis-cloud.com:11883",
            "redis://localhost:6379/0"
        ]
        
        for redis_url in redis_urls:
            if not redis_url:
                continue
                
            try:
                logger.info(f"Testing Redis connection to: {redis_url[:50]}...")
                
                client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                
                # Test connection
                await client.ping()
                logger.info("✅ Redis connection successful")
                
                # Test basic operations
                await client.set("test_key", "test_value", ex=10)
                value = await client.get("test_key")
                if value == "test_value":
                    logger.info("✅ Redis read/write operations successful")
                
                await client.delete("test_key")
                await client.close()
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed for {redis_url[:50]}: {e}")
                continue
        
        logger.error("❌ All Redis connection attempts failed")
        return False
        
    except ImportError:
        logger.error("❌ Redis library not installed")
        return False
    except Exception as e:
        logger.error(f"❌ Redis connection test failed: {e}")
        return False

async def test_health_checks():
    """Test the actual health check functions"""
    try:
        from app.services.cache_service import cache_service
        from app.database.connection import db_manager
        
        logger.info("Testing application health check functions...")
        
        # Test database manager
        try:
            await db_manager.connect_to_database()
            db = db_manager.get_database()
            if db:
                logger.info("✅ Database manager connection successful")
            else:
                logger.error("❌ Database manager returned None")
        except Exception as e:
            logger.error(f"❌ Database manager failed: {e}")
        
        # Test cache service
        try:
            await cache_service.connect()
            stats = await cache_service.get_cache_stats()
            if stats.get("connected", False):
                logger.info("✅ Cache service connection successful")
                logger.info(f"Cache stats: {stats}")
            else:
                logger.error(f"❌ Cache service not connected: {stats}")
        except Exception as e:
            logger.error(f"❌ Cache service failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Health check test failed: {e}")
        return False

async def main():
    """Run all connection tests"""
    logger.info("🔍 Starting connection diagnostics...")
    
    results = {
        "mongodb": await test_mongodb_connection(),
        "redis": await test_redis_connection(),
        "health_checks": await test_health_checks()
    }
    
    logger.info("\n" + "="*50)
    logger.info("DIAGNOSTIC RESULTS:")
    logger.info("="*50)
    
    for service, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{service.upper()}: {status}")
    
    if all(results.values()):
        logger.info("\n🎉 All connections are working properly!")
        logger.info("The health check failures might be temporary or due to network issues.")
    else:
        logger.info("\n⚠️ Some connections are failing.")
        logger.info("This explains the health check failures in your application.")
        
        # Provide specific recommendations
        if not results["mongodb"]:
            logger.info("\n📋 MongoDB Troubleshooting:")
            logger.info("1. Check if MongoDB Atlas cluster is running")
            logger.info("2. Verify network access (IP whitelist)")
            logger.info("3. Check credentials and connection string")
            
        if not results["redis"]:
            logger.info("\n📋 Redis Troubleshooting:")
            logger.info("1. Check if Redis Cloud instance is running")
            logger.info("2. Verify Redis URL and credentials")
            logger.info("3. Consider using local Redis for development")
            logger.info("4. Add REDIS_URL to your .env file")

if __name__ == "__main__":
    asyncio.run(main())