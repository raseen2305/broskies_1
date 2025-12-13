"""
List all user profiles in the database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def list_profiles():
    mongo_uri = os.getenv("MONGODB_URL") or os.getenv("MONGODB_URI")
    db_name = os.getenv("DATABASE_NAME", "devrank")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    print("=" * 80)
    print("ALL USER PROFILES:")
    print("=" * 80)
    
    count = await db.user_profiles.count_documents({})
    print(f"\nTotal profiles: {count}\n")
    
    async for profile in db.user_profiles.find():
        print(f"📄 Profile:")
        print(f"   User ID: {profile.get('user_id')}")
        print(f"   Name: {profile.get('name', 'N/A')}")
        print(f"   GitHub Username: {profile.get('github_username', 'N/A')}")
        print(f"   University: {profile.get('university', 'N/A')}")
        print(f"   Region: {profile.get('region', 'N/A')}")
        print(f"   Created: {profile.get('created_at', 'N/A')}")
        print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(list_profiles())
