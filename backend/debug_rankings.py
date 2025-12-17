"""
Debug script to check why rankings are null for a specific user.
"""

import asyncio
import sys
import logging
from app.db_connection import get_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def debug_user_rankings(username: str):
    """Debug rankings for a specific user"""
    try:
        logger.info("=" * 80)
        logger.info(f"DEBUGGING RANKINGS FOR: {username}")
        logger.info("=" * 80)
        
        db = await get_database()
        if db is None:
            logger.error("❌ Failed to connect to database")
            return
        
        # Step 1: Get user's ranking document
        logger.info("\n📋 Step 1: Fetching user_rankings document...")
        ranking = await db.user_rankings.find_one({"github_username": username})
        
        if not ranking:
            logger.error(f"❌ No user_rankings document found for {username}")
            return
        
        logger.info(f"✅ Found user_rankings document:")
        logger.info(f"   - User ID: {ranking.get('user_id')}")
        logger.info(f"   - District: {ranking.get('district')}")
        logger.info(f"   - University: {ranking.get('university')}")
        logger.info(f"   - University Short: {ranking.get('university_short')}")
        logger.info(f"   - Overall Score: {ranking.get('overall_score')}")
        logger.info(f"   - Regional Rank: {ranking.get('regional_rank')}")
        logger.info(f"   - University Rank: {ranking.get('university_rank')}")
        
        # Step 2: Check district-based regional ranking
        district = ranking.get('district')
        if district:
            logger.info(f"\n📊 Step 2: Checking regional ranking (district: {district})...")
            
            # Find all users in same district
            district_users = await db.user_rankings.find({
                "district": district,
                "overall_score": {"$ne": None, "$gt": 0}
            }).to_list(None)
            
            logger.info(f"   - Found {len(district_users)} users in district '{district}':")
            for i, user in enumerate(sorted(district_users, key=lambda x: x.get('overall_score', 0), reverse=True)[:5], 1):
                logger.info(f"      {i}. {user['github_username']}: {user.get('overall_score', 0)}")
            
            if len(district_users) == 0:
                logger.warning(f"   ⚠️  No users found in district '{district}'")
            elif len(district_users) == 1:
                logger.info(f"   ℹ️  Only 1 user in district (should get rank 1)")
        else:
            logger.warning("   ⚠️  No district field found")
        
        # Step 3: Check university ranking
        university_short = ranking.get('university_short')
        if university_short:
            logger.info(f"\n📊 Step 3: Checking university ranking (university_short: {university_short})...")
            
            # Find all users in same university
            university_users = await db.user_rankings.find({
                "university_short": university_short,
                "overall_score": {"$ne": None, "$gt": 0}
            }).to_list(None)
            
            logger.info(f"   - Found {len(university_users)} users in university '{university_short}':")
            for i, user in enumerate(sorted(university_users, key=lambda x: x.get('overall_score', 0), reverse=True)[:5], 1):
                logger.info(f"      {i}. {user['github_username']}: {user.get('overall_score', 0)}")
            
            if len(university_users) == 0:
                logger.warning(f"   ⚠️  No users found in university '{university_short}'")
            elif len(university_users) == 1:
                logger.info(f"   ℹ️  Only 1 user in university (should get rank 1)")
        else:
            logger.warning("   ⚠️  No university_short field found")
        
        # Step 4: Try to manually trigger ranking calculation
        logger.info(f"\n🔄 Step 4: Manually triggering ranking calculation...")
        
        from app.services.enhanced_ranking_service import EnhancedRankingService
        ranking_service = EnhancedRankingService(db)
        
        user_id = ranking.get('user_id')
        if user_id:
            result = await ranking_service.update_rankings_for_user(user_id)
            
            logger.info(f"   - Result: {result}")
            
            if result.get('success'):
                logger.info("   ✅ Ranking calculation succeeded")
                
                # Fetch updated rankings
                updated_ranking = await db.user_rankings.find_one({"github_username": username})
                logger.info(f"\n📋 Updated Rankings:")
                logger.info(f"   - Regional Rank: {updated_ranking.get('regional_rank')}")
                logger.info(f"   - Regional Percentile: {updated_ranking.get('regional_percentile')}")
                logger.info(f"   - Regional Total Users: {updated_ranking.get('regional_total_users')}")
                logger.info(f"   - University Rank: {updated_ranking.get('university_rank')}")
                logger.info(f"   - University Percentile: {updated_ranking.get('university_percentile')}")
                logger.info(f"   - University Total Users: {updated_ranking.get('university_total_users')}")
            else:
                logger.error(f"   ❌ Ranking calculation failed: {result.get('error')}")
        else:
            logger.error("   ❌ No user_id found")
        
        logger.info("\n" + "=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Error debugging rankings: {e}")
        import traceback
        logger.error(traceback.format_exc())


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python debug_rankings.py <username>")
        print("Example: python debug_rankings.py raseen2305")
        sys.exit(1)
    
    username = sys.argv[1]
    asyncio.run(debug_user_rankings(username))


if __name__ == "__main__":
    main()
