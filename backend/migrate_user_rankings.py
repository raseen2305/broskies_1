#!/usr/bin/env python3
"""
Migration Script: Populate user_rankings with Complete Profile Data

⚠️  DEPRECATED: This script is for the old single-database architecture.
⚠️  The new multi-database architecture handles user rankings differently.
⚠️  Use the new database restructuring system instead.

This script copies profile data from comprehensive_scans to user_rankings
so HR users can view complete candidate profiles instantly.
"""

import asyncio
import sys
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def migrate_user_rankings():
    """Migrate profile data from comprehensive_scans to user_rankings"""
    
    # Get MongoDB connection (DEPRECATED - use multi-database architecture)
    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME", "git_Evaluator")  # Legacy database
    
    if not mongodb_url:
        print("❌ MONGODB_URL not found in environment variables")
        return
    
    print(f"🔗 Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]
    
    try:
        # Test connection
        await db.command('ping')
        print(f"✅ Connected to database: {database_name}")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return
    
    # Get all user_rankings
    print(f"\n📊 Fetching user_rankings...")
    cursor = db.user_rankings.find({})
    users = await cursor.to_list(length=None)
    
    print(f"Found {len(users)} users in user_rankings")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for i, user in enumerate(users, 1):
        username = user.get("github_username")
        print(f"\n[{i}/{len(users)}] Processing {username}...")
        
        try:
            # Try to get data from comprehensive_scans
            scan = await db.comprehensive_scans.find_one({"github_username": username})
            
            if scan and scan.get("userInfo"):
                user_info = scan["userInfo"]
                
                # Prepare update data
                update_data = {
                    "bio": user_info.get("bio"),
                    "location": user_info.get("location"),
                    "company": user_info.get("company"),
                    "email": user_info.get("email"),
                    "blog": user_info.get("blog"),
                    "website": user_info.get("blog"),  # Duplicate for compatibility
                    "public_repos": user_info.get("public_repos", 0),
                    "total_repos": user_info.get("public_repos", 0),  # Duplicate
                    "followers": user_info.get("followers", 0),
                    "following": user_info.get("following", 0),
                    "github_created_at": user_info.get("created_at"),
                    "created_at": user_info.get("created_at"),  # Duplicate
                    "updated_at": datetime.utcnow(),
                    "last_updated": datetime.utcnow()  # Duplicate
                }
                
                # Remove None values
                update_data = {k: v for k, v in update_data.items() if v is not None}
                
                if update_data:
                    # Update user_rankings
                    result = await db.user_rankings.update_one(
                        {"github_username": username},
                        {"$set": update_data}
                    )
                    
                    if result.modified_count > 0:
                        print(f"  ✅ Updated {username} with {len(update_data)} fields")
                        updated_count += 1
                    else:
                        print(f"  ℹ️  No changes needed for {username}")
                        skipped_count += 1
                else:
                    print(f"  ⚠️  No data to update for {username}")
                    skipped_count += 1
            else:
                print(f"  ⚠️  No comprehensive_scans data for {username}")
                skipped_count += 1
                
        except Exception as e:
            print(f"  ❌ Error processing {username}: {e}")
            error_count += 1
    
    # Summary
    print(f"\n" + "="*60)
    print(f"Migration Complete!")
    print(f"="*60)
    print(f"✅ Updated: {updated_count}")
    print(f"⚠️  Skipped: {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total: {len(users)}")
    print(f"="*60)
    
    # Close connection
    client.close()


async def verify_migration(sample_username: str = None):
    """Verify migration by checking a sample user"""
    
    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME", "git_Evaluator")
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]
    
    if sample_username:
        user = await db.user_rankings.find_one({"github_username": sample_username})
    else:
        # Get first user
        user = await db.user_rankings.find_one({})
    
    if user:
        username = user.get("github_username")
        print(f"\n📋 Sample User: {username}")
        print(f"="*60)
        
        fields_to_check = [
            "name", "bio", "location", "company", "email", "blog",
            "public_repos", "followers", "following", "github_created_at"
        ]
        
        for field in fields_to_check:
            value = user.get(field)
            status = "✅" if value else "❌"
            print(f"{status} {field}: {value}")
        
        print(f"="*60)
    else:
        print("❌ No users found in user_rankings")
    
    client.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate user_rankings profile data")
    parser.add_argument("--verify", type=str, help="Verify migration for a specific username")
    parser.add_argument("--verify-sample", action="store_true", help="Verify migration with a sample user")
    
    args = parser.parse_args()
    
    if args.verify:
        asyncio.run(verify_migration(args.verify))
    elif args.verify_sample:
        asyncio.run(verify_migration())
    else:
        asyncio.run(migrate_user_rankings())
