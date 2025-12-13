"""
Quick setup script for ranking system
Run this after first scan to populate ranking collections
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

async def quick_setup():
    """Quick setup for ranking system"""
    print("=" * 60)
    print("🚀 Quick Ranking System Setup")
    print("=" * 60)
    
    try:
        from backend.app.db_connection import get_database
        from backend.app.services.enhanced_ranking_service import EnhancedRankingService
        
        # Connect to database
        print("\n1. Connecting to database...")
        db = await get_database()
        if not db:
            print("   ❌ Database connection failed")
            return False
        print("   ✅ Connected")
        
        # Check if user_rankings has data
        print("\n2. Checking for existing data...")
        count = await db.user_rankings.count_documents({})
        print(f"   Found {count} users in user_rankings collection")
        
        if count == 0:
            print("\n   ⚠️  No users found!")
            print("   Please complete a repository scan first:")
            print("   1. Login to the app")
            print("   2. Go to /developer/scan")
            print("   3. Scan your repositories")
            print("   4. Run this script again")
            return False
        
        # Initialize ranking service
        print("\n3. Initializing ranking service...")
        ranking_service = EnhancedRankingService(db)
        print("   ✅ Service initialized")
        
        # Get unique regions and universities
        print("\n4. Finding regions and universities...")
        regions = await db.user_rankings.distinct("region", {"region": {"$ne": None}})
        universities = await db.user_rankings.distinct("university_short", {"university_short": {"$ne": None}})
        
        print(f"   Regions: {len(regions)}")
        print(f"   Universities: {len(universities)}")
        
        if len(regions) == 0 and len(universities) == 0:
            print("\n   ⚠️  No regions or universities found!")
            print("   Users need to complete their profile with region/university info")
            return False
        
        # Update regional rankings
        print("\n5. Updating regional rankings...")
        for region in regions:
            result = await ranking_service.batch_update_regional_rankings(region)
            if result["success"]:
                print(f"   ✅ {region}: {result['users_updated']} users")
            else:
                print(f"   ❌ {region}: {result.get('error')}")
        
        # Update university rankings
        print("\n6. Updating university rankings...")
        for university in universities:
            result = await ranking_service.batch_update_university_rankings(university)
            if result["success"]:
                print(f"   ✅ {university}: {result['users_updated']} users")
            else:
                print(f"   ❌ {university}: {result.get('error')}")
        
        # Verify
        print("\n7. Verifying setup...")
        regional_count = await db.regional_rankings.count_documents({})
        university_count = await db.university_rankings.count_documents({})
        
        print(f"   regional_rankings: {regional_count} documents")
        print(f"   university_rankings: {university_count} documents")
        
        print("\n" + "=" * 60)
        print("✅ Setup Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Restart backend if running")
        print("2. Navigate to /developer/dashboard/rankings")
        print("3. View your rankings!")
        print("\n" + "=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_setup())
    sys.exit(0 if success else 1)
