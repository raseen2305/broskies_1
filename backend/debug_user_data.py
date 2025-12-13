#!/usr/bin/env python3
"""
Debug script to check user data linking issues
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_database, Collections
from app.services.ranking_service import RankingService

async def debug_user_data(user_id: str = "raseen2305"):
    """Debug user data to find ranking issues"""
    
    print(f"🔍 Debugging user data for: {user_id}")
    print("=" * 60)
    
    try:
        db = await get_database()
        if not db:
            print("❌ Could not connect to database")
            return
        
        print("✅ Database connected")
        
        # 1. Check internal_users collection
        print(f"\n1️⃣ Checking internal_users collection...")
        internal_users = await db[Collections.INTERNAL_USERS].find(
            {"user_id": user_id}
        ).to_list(None)
        
        print(f"   Found {len(internal_users)} records in internal_users")
        for i, user in enumerate(internal_users):
            print(f"   Record {i+1}:")
            print(f"     _id: {user.get('_id')}")
            print(f"     user_id: {user.get('user_id')}")
            print(f"     username: {user.get('username')}")
            print(f"     overall_score: {user.get('overall_score')}")
            print(f"     updated_at: {user.get('updated_at')}")
        
        # 2. Check internal_users_profile collection
        print(f"\n2️⃣ Checking internal_users_profile collection...")
        profile_users = await db[Collections.INTERNAL_USERS_PROFILE].find(
            {"user_id": user_id}
        ).to_list(None)
        
        print(f"   Found {len(profile_users)} records in internal_users_profile")
        for i, user in enumerate(profile_users):
            print(f"   Record {i+1}:")
            print(f"     _id: {user.get('_id')}")
            print(f"     user_id: {user.get('user_id')}")
            print(f"     github_username: {user.get('github_username')}")
            print(f"     full_name: {user.get('full_name')}")
            print(f"     profile_completed: {user.get('profile_completed')}")
            print(f"     university: {user.get('university')}")
            print(f"     district: {user.get('district')}")
        
        # 3. Check if _id values match
        print(f"\n3️⃣ Checking _id matching...")
        if internal_users and profile_users:
            internal_ids = [str(u['_id']) for u in internal_users]
            profile_ids = [str(u['_id']) for u in profile_users]
            
            print(f"   internal_users _ids: {internal_ids}")
            print(f"   profile_users _ids: {profile_ids}")
            
            matching_ids = set(internal_ids) & set(profile_ids)
            print(f"   Matching _ids: {list(matching_ids)}")
            
            if not matching_ids:
                print("   ❌ NO MATCHING _IDs FOUND - This is the problem!")
            else:
                print("   ✅ Found matching _ids")
        
        # 4. Test RankingService join
        print(f"\n4️⃣ Testing RankingService data join...")
        ranking_service = RankingService(db)
        joined_data = await ranking_service.get_joined_user_data({"user_id": user_id})
        
        print(f"   Joined data count: {len(joined_data)}")
        if joined_data:
            user_data = joined_data[0]
            print(f"   Joined user data:")
            print(f"     user_id: {user_data.get('user_id')}")
            print(f"     github_username: {user_data.get('github_username')}")
            print(f"     name: {user_data.get('name')}")
            print(f"     overall_score: {user_data.get('overall_score')}")
            print(f"     university: {user_data.get('university')}")
            print(f"     district: {user_data.get('district')}")
            print(f"     profile_completed: {user_data.get('profile_completed')}")
        else:
            print("   ❌ No joined data found - this explains the 'pending_scan' status")
        
        # 5. Check existing rankings
        print(f"\n5️⃣ Checking existing rankings...")
        regional_rankings = await db[Collections.REGIONAL_RANKINGS].find(
            {"user_id": user_id}
        ).to_list(None)
        
        university_rankings = await db[Collections.UNIVERSITY_RANKINGS].find(
            {"user_id": user_id}
        ).to_list(None)
        
        print(f"   Regional rankings: {len(regional_rankings)}")
        print(f"   University rankings: {len(university_rankings)}")
        
        # 6. Suggest fixes
        print(f"\n6️⃣ Suggested fixes:")
        if not internal_users:
            print("   ❌ No scan data found - user needs to complete a repository scan")
        elif not profile_users:
            print("   ❌ No profile data found - user needs to complete profile setup")
        elif internal_users and profile_users:
            internal_ids = [str(u['_id']) for u in internal_users]
            profile_ids = [str(u['_id']) for u in profile_users]
            if not (set(internal_ids) & set(profile_ids)):
                print("   🔧 _id mismatch detected - need to fix data linking")
                print("   💡 Solution: Update one collection to match the other's _id")
            else:
                print("   🔧 Data exists but join failed - check profile_completed status")
                if profile_users and not profile_users[0].get('profile_completed'):
                    print("   💡 Solution: Set profile_completed = True")
        
        print("\n" + "=" * 60)
        print("🏁 Debug complete")
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "raseen2305"
    asyncio.run(debug_user_data(user_id))