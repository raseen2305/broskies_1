#!/usr/bin/env python3
"""
Fix script to resolve user data linking issues for rankings
"""

import asyncio
import sys
import os
from bson import ObjectId
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_database, Collections
from app.services.ranking_service import RankingService

async def fix_user_data_linking(user_id: str = "raseen2305", auto_fix: bool = False):
    """Fix user data linking issues"""
    
    print(f"🔧 Fixing user data linking for: {user_id}")
    print("=" * 60)
    
    try:
        db = await get_database()
        if not db:
            print("❌ Could not connect to database")
            return
        
        print("✅ Database connected")
        
        # 1. Get internal_users data
        internal_users = await db[Collections.INTERNAL_USERS].find(
            {"user_id": user_id}
        ).to_list(None)
        
        # 2. Get profile data
        profile_users = await db[Collections.INTERNAL_USERS_PROFILE].find(
            {"user_id": user_id}
        ).to_list(None)
        
        print(f"📊 Found {len(internal_users)} scan records, {len(profile_users)} profile records")
        
        if not internal_users:
            print("❌ No scan data found - user needs to complete repository scan first")
            return
        
        if not profile_users:
            print("❌ No profile data found - user needs to complete profile setup first")
            return
        
        # 3. Check for _id mismatch
        internal_user = internal_users[0]  # Use most recent
        profile_user = profile_users[0]    # Use most recent
        
        internal_id = internal_user['_id']
        profile_id = profile_user['_id']
        
        print(f"🔍 Checking _id matching:")
        print(f"   internal_users._id: {internal_id}")
        print(f"   profile_users._id: {profile_id}")
        
        if internal_id != profile_id:
            print("❌ _id mismatch detected!")
            print(f"🔧 Fix needed: Update profile record to use scan record's _id")
            
            if auto_fix:
                # Update profile record to use scan record's _id
                result = await db[Collections.INTERNAL_USERS_PROFILE].update_one(
                    {"user_id": user_id},
                    {"$set": {"_id": internal_id}}
                )
                print(f"✅ Updated profile _id: {result.modified_count} records modified")
            else:
                print("💡 Run with --auto-fix to apply this fix")
        else:
            print("✅ _ids match correctly")
        
        # 4. Check profile completion status
        if not profile_user.get('profile_completed'):
            print("❌ Profile not marked as completed")
            
            if auto_fix:
                result = await db[Collections.INTERNAL_USERS_PROFILE].update_one(
                    {"user_id": user_id},
                    {"$set": {"profile_completed": True}}
                )
                print(f"✅ Set profile_completed = True: {result.modified_count} records modified")
            else:
                print("💡 Run with --auto-fix to mark profile as completed")
        else:
            print("✅ Profile marked as completed")
        
        # 5. Test data join after fixes
        print(f"\n🧪 Testing data join...")
        ranking_service = RankingService(db)
        joined_data = await ranking_service.get_joined_user_data({"user_id": user_id})
        
        if joined_data:
            print(f"✅ Data join successful! Found {len(joined_data)} complete records")
            user_data = joined_data[0]
            print(f"   User: {user_data.get('name')} ({user_data.get('github_username')})")
            print(f"   Score: {user_data.get('overall_score')}")
            print(f"   University: {user_data.get('university')}")
            print(f"   District: {user_data.get('district')}")
            
            # 6. Trigger ranking calculation
            if auto_fix:
                print(f"\n🎯 Triggering ranking calculation...")
                result = await ranking_service.update_all_rankings_for_user(user_id)
                
                if result["success"]:
                    print("✅ Rankings calculated successfully!")
                    if result.get("regional_update"):
                        print(f"   Regional: {result['regional_update'].get('users_updated', 0)} users updated")
                    if result.get("university_update"):
                        print(f"   University: {result['university_update'].get('users_updated', 0)} users updated")
                else:
                    print(f"❌ Ranking calculation failed: {result.get('error')}")
            else:
                print("💡 Run with --auto-fix to calculate rankings")
        else:
            print("❌ Data join still failing - manual investigation needed")
        
        print("\n" + "=" * 60)
        print("🏁 Fix attempt complete")
        
    except Exception as e:
        print(f"❌ Error during fix: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    user_id = "raseen2305"
    auto_fix = False
    
    for arg in sys.argv[1:]:
        if arg.startswith("--user="):
            user_id = arg.split("=")[1]
        elif arg == "--auto-fix":
            auto_fix = True
        else:
            user_id = arg
    
    print(f"User ID: {user_id}")
    print(f"Auto-fix: {auto_fix}")
    print()
    
    asyncio.run(fix_user_data_linking(user_id, auto_fix))