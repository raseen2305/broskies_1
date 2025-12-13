#!/usr/bin/env python3
"""
List all users in the database to find the correct user_id for raseen2305
"""
import asyncio
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_database, Collections

async def list_all_users():
    print("🔍 Listing all users in the database...")
    
    db = await get_database()
    if not db:
        print("❌ Could not connect to database")
        return
    
    # List all users in internal_users collection
    print(f"\n📊 {Collections.INTERNAL_USERS} collection:")
    internal_users = await db[Collections.INTERNAL_USERS].find({}).to_list(None)
    print(f"Total records: {len(internal_users)}")
    
    for i, user in enumerate(internal_users[:10]):  # Show first 10
        print(f"  {i+1}. user_id: {user.get('user_id')}, username: {user.get('username')}, github_username: {user.get('github_username')}")
    
    if len(internal_users) > 10:
        print(f"  ... and {len(internal_users) - 10} more records")
    
    # List all users in internal_users_profile collection
    print(f"\n👤 {Collections.INTERNAL_USERS_PROFILE} collection:")
    profile_users = await db[Collections.INTERNAL_USERS_PROFILE].find({}).to_list(None)
    print(f"Total records: {len(profile_users)}")
    
    for i, user in enumerate(profile_users[:10]):  # Show first 10
        print(f"  {i+1}. user_id: {user.get('user_id')}, github_username: {user.get('github_username')}, full_name: {user.get('full_name')}")
    
    if len(profile_users) > 10:
        print(f"  ... and {len(profile_users) - 10} more records")
    
    # Look specifically for any records containing "raseen"
    print(f"\n🔍 Searching for records containing 'raseen'...")
    
    # Search internal_users
    raseen_internal = await db[Collections.INTERNAL_USERS].find({
        "$or": [
            {"user_id": {"$regex": "raseen", "$options": "i"}},
            {"username": {"$regex": "raseen", "$options": "i"}},
            {"github_username": {"$regex": "raseen", "$options": "i"}}
        ]
    }).to_list(None)
    
    print(f"Internal users with 'raseen': {len(raseen_internal)}")
    for user in raseen_internal:
        print(f"  user_id: {user.get('user_id')}, username: {user.get('username')}, github_username: {user.get('github_username')}")
    
    # Search profile_users
    raseen_profile = await db[Collections.INTERNAL_USERS_PROFILE].find({
        "$or": [
            {"user_id": {"$regex": "raseen", "$options": "i"}},
            {"github_username": {"$regex": "raseen", "$options": "i"}},
            {"full_name": {"$regex": "raseen", "$options": "i"}}
        ]
    }).to_list(None)
    
    print(f"Profile users with 'raseen': {len(raseen_profile)}")
    for user in raseen_profile:
        print(f"  user_id: {user.get('user_id')}, github_username: {user.get('github_username')}, full_name: {user.get('full_name')}")

if __name__ == "__main__":
    asyncio.run(list_all_users())