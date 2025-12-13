"""
Database initialization script for HR Dashboard collections.
Creates necessary collections and indexes for HR user management.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, DESCENDING
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")


async def init_hr_collections():
    """Initialize HR-related collections with proper indexes"""
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print("Initializing HR Dashboard collections...")
    
    # 1. approved_hr_users collection
    print("\n1. Setting up 'approved_hr_users' collection...")
    approved_hr_collection = db["approved_hr_users"]
    
    # Create indexes for approved_hr_users
    approved_hr_indexes = [
        IndexModel([("email", ASCENDING)], unique=True, name="email_unique"),
    ]
    
    try:
        await approved_hr_collection.create_indexes(approved_hr_indexes)
        print("   ✓ Created indexes for 'approved_hr_users'")
    except Exception as e:
        print(f"   ⚠ Error creating indexes for 'approved_hr_users': {e}")
    
    # 2. hr_registrations collection
    print("\n2. Setting up 'hr_registrations' collection...")
    hr_registrations_collection = db["hr_registrations"]
    
    # Create indexes for hr_registrations
    hr_registrations_indexes = [
        IndexModel([("email", ASCENDING)], name="email_index"),
        IndexModel([("submitted_at", DESCENDING)], name="submitted_at_index"),
        IndexModel([("reviewed", ASCENDING), ("approved", ASCENDING)], name="review_status_index"),
    ]
    
    try:
        await hr_registrations_collection.create_indexes(hr_registrations_indexes)
        print("   ✓ Created indexes for 'hr_registrations'")
    except Exception as e:
        print(f"   ⚠ Error creating indexes for 'hr_registrations': {e}")
    
    # 3. hr_users collection
    print("\n3. Setting up 'hr_users' collection...")
    hr_users_collection = db["hr_users"]
    
    # Create indexes for hr_users
    hr_users_indexes = [
        IndexModel([("email", ASCENDING)], unique=True, name="email_unique"),
        IndexModel([("google_id", ASCENDING)], unique=True, name="google_id_unique"),
        IndexModel([("is_approved", ASCENDING)], name="is_approved_index"),
    ]
    
    try:
        await hr_users_collection.create_indexes(hr_users_indexes)
        print("   ✓ Created indexes for 'hr_users'")
    except Exception as e:
        # Check if it's just a naming conflict for existing indexes
        if "Index already exists" in str(e):
            print("   ℹ Some indexes already exist (this is okay)")
        else:
            print(f"   ⚠ Error creating indexes for 'hr_users': {e}")
    
    # 4. Verify scores_comparison collection exists
    print("\n4. Verifying 'scores_comparison' collection...")
    collections = await db.list_collection_names()
    
    if "scores_comparison" in collections:
        print("   ✓ 'scores_comparison' collection exists")
        
        # Check if it has data
        count = await db["scores_comparison"].count_documents({})
        print(f"   ℹ Collection has {count} documents")
    else:
        print("   ⚠ 'scores_comparison' collection does not exist yet")
        print("   ℹ This collection will be populated when developers complete their GitHub scans")
    
    print("\n✅ HR Dashboard collections initialized successfully!")
    print("\nNext steps:")
    print("1. Configure Google OAuth in Google Cloud Console")
    print("2. Add authorized redirect URI: http://localhost:5173/hr/auth/callback")
    print("3. Manually add approved HR emails to 'approved_hr_users' collection")
    
    client.close()


async def add_sample_approved_hr(email: str):
    """Helper function to add a sample approved HR user"""
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    from datetime import datetime
    
    approved_hr_collection = db["approved_hr_users"]
    
    try:
        await approved_hr_collection.insert_one({
            "email": email,
            "approved_at": datetime.utcnow(),
            "approved_by": "system_admin",
            "notes": "Initial setup - sample approved HR user"
        })
        print(f"✓ Added {email} to approved HR users")
    except Exception as e:
        print(f"⚠ Error adding approved HR user: {e}")
    
    client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("HR Dashboard Database Initialization")
    print("=" * 60)
    
    asyncio.run(init_hr_collections())
    
    # Optionally add a sample approved HR user
    # Uncomment and replace with your email to test
    # asyncio.run(add_sample_approved_hr("your-email@example.com"))
