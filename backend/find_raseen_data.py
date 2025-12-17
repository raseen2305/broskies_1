#!/usr/bin/env python3
"""
Find all data related to raseen2305 in the database
"""
import asyncio
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_database, Collections

async def find_raseen_data():
    print("🔍 Searching for raseen2305 data in all collections...")
    
    db = await get_database()
    if not db:
        print("❌ Could not connect to database")
        return
    
    username = "raseen2305"
    
    # Search in internal_users collection
    print(f"\n📊 Searching {Collections.INTERNAL_USERS}...")
    internal_users = await db[Collections.INTERNAL_USERS].find({
        "$or": [
            {"user_id": username},
            {"username": username},
            {"github_username": username}
        ]
    }).to_list(None)
    
    print(f"Found {len(internal_users)} records in {Collections.INTERNAL_USERS}")
    for i, user in enumerate(internal_users):
        print(f"  Record {i+1}:")
        print(f"    _id: {user.get('_id')}")
        print(f"    user_id: {user.get('user_id')}")
        print(f"    username: {user.get('username')}")
        print(f"    github_username: {user.get('github_username')}")
        print(f"    overall_score: {user.get('overall_score')}")
        print(f"    updated_at: {user.get('updated_at')}")
    
    # Search in internal_users_profile collection
    print(f"\n👤 Searching {Collections.INTERNAL_USERS_PROFILE}...")
    profile_users = await db[Collections.INTERNAL_USERS_PROFILE].find({
        "$or": [
            {"user_id": username},
            {"github_username": username}
        ]
    }).to_list(None)
    
    print(f"Found {len(profile_users)} records in {Collections.INTERNAL_USERS_PROFILE}")
    for i, user in enumerate(profile_users):
        print(f"  Record {i+1}:")
        print(f"    _id: {user.get('_id')}")
        print(f"    user_id: {user.get('user_id')}")
        print(f"    github_username: {user.get('github_username')}")
        print(f"    full_name: {user.get('full_name')}")
        print(f"    profile_completed: {user.get('profile_completed')}")
        print(f"    university: {user.get('university')}")
        print(f"    district: {user.get('district')}")
    
    # Search in regional_rankings collection
    print(f"\n🏆 Searching {Collections.REGIONAL_RANKINGS}...")
    regional_rankings = await db[Collections.REGIONAL_RANKINGS].find({
        "$or": [
            {"user_id": username},
            {"github_username": username}
        ]
    }).to_list(None)
    
    print(f"Found {len(regional_rankings)} records in {Collections.REGIONAL_RANKINGS}")
    for i, ranking in enumerate(regional_rankings):
        print(f"  Record {i+1}:")
        print(f"    _id: {ranking.get('_id')}")
        print(f"    user_id: {ranking.get('user_id')}")
        print(f"    github_username: {ranking.get('github_username')}")
        print(f"    rank: {ranking.get('rank')}")
        print(f"    overall_score: {ranking.get('overall_score')}")
        print(f"    district: {ranking.get('district')}")
    
    # Search in university_rankings collection
    print(f"\n🎓 Searching {Collections.UNIVERSITY_RANKINGS}...")
    university_rankings = await db[Collections.UNIVERSITY_RANKINGS].find({
        "$or": [
            {"user_id": username},
            {"github_username": username}
        ]
    }).to_list(None)
    
    print(f"Found {len(university_rankings)} records in {Collections.UNIVERSITY_RANKINGS}")
    for i, ranking in enumerate(university_rankings):
        print(f"  Record {i+1}:")
        print(f"    _id: {ranking.get('_id')}")
        print(f"    user_id: {ranking.get('user_id')}")
        print(f"    github_username: {ranking.get('github_username')}")
        print(f"    rank: {ranking.get('rank')}")
        print(f"    overall_score: {ranking.get('overall_score')}")
        print(f"    university_short: {ranking.get('university_short')}")
    
    # Also search for any records that might have different user_id but same github_username
    print(f"\n🔍 Searching for any records with github_username = {username}...")
    
    # Check all collections for github_username
    collections_to_check = [
        Collections.INTERNAL_USERS,
        Collections.INTERNAL_USERS_PROFILE,
        Collections.REGIONAL_RANKINGS,
        Collections.UNIVERSITY_RANKINGS
    ]
    
    for collection_name in collections_to_check:
        records = await db[collection_name].find({"github_username": username}).to_list(None)
        if records:
            print(f"\n  {collection_name}: {len(records)} records")
            for record in records:
                print(f"    user_id: {record.get('user_id')}, _id: {record.get('_id')}")

if __name__ == "__main__":
    asyncio.run(find_raseen_data())