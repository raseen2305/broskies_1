"""
Quick diagnostic script to identify backend startup issues
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

async def test_mongodb():
    """Test MongoDB connection"""
    print("🔍 Testing MongoDB connection...")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongodb_url = os.getenv("MONGODB_URL")
        database_name = os.getenv("DATABASE_NAME", "git_Evaluator")  # Legacy database
        
        print(f"   URL: {mongodb_url[:50]}...")
        print(f"   Database: {database_name}")
        
        client = AsyncIOMotorClient(
            mongodb_url,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        
        # Test connection with timeout
        await asyncio.wait_for(client.admin.command('ping'), timeout=10.0)
        
        print("   ✅ MongoDB connection successful")
        client.close()
        return True
        
    except asyncio.TimeoutError:
        print("   ❌ MongoDB connection TIMEOUT (network issue)")
        return False
    except Exception as e:
        print(f"   ❌ MongoDB connection failed: {e}")
        return False

async def test_redis():
    """Test Redis connection"""
    print("\n🔍 Testing Redis connection...")
    try:
        import redis.asyncio as redis
        
        redis_url = os.getenv("REDIS_URL")
        print(f"   URL: {redis_url[:50]}...")
        
        client = redis.from_url(redis_url, socket_connect_timeout=10)
        
        # Test connection with timeout
        await asyncio.wait_for(client.ping(), timeout=10.0)
        
        print("   ✅ Redis connection successful")
        await client.close()
        return True
        
    except asyncio.TimeoutError:
        print("   ❌ Redis connection TIMEOUT (network issue)")
        return False
    except Exception as e:
        print(f"   ❌ Redis connection failed: {e}")
        return False

async def test_github_api():
    """Test GitHub API access"""
    print("\n🔍 Testing GitHub API access...")
    try:
        import httpx
        
        github_token = os.getenv("GITHUB_TOKEN")
        headers = {"Authorization": f"token {github_token}"} if github_token else {}
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get("https://api.github.com/rate_limit", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ GitHub API accessible")
                print(f"   Rate limit: {data['rate']['remaining']}/{data['rate']['limit']}")
                return True
            else:
                print(f"   ❌ GitHub API returned status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"   ❌ GitHub API test failed: {e}")
        return False

async def main():
    print("=" * 60)
    print("Backend Startup Diagnostics")
    print("=" * 60)
    
    results = {
        "mongodb": await test_mongodb(),
        "redis": await test_redis(),
        "github": await test_github_api()
    }
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service.upper()}: {'OK' if status else 'FAILED'}")
    
    print("\n" + "=" * 60)
    
    if not all(results.values()):
        print("\n⚠️  Some services failed to connect.")
        print("Possible issues:")
        print("  - Network connectivity problems")
        print("  - Firewall blocking connections")
        print("  - Service credentials expired")
        print("  - Service temporarily unavailable")
        print("\nThe backend will likely get stuck during startup.")
    else:
        print("\n✅ All services are accessible!")
        print("The backend should start successfully.")

if __name__ == "__main__":
    asyncio.run(main())
