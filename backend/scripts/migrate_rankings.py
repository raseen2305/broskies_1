"""
Migration script to populate new ranking collections from existing data
Run this once to migrate from old ranking system to new enhanced system
"""

import asyncio
import sys
import os
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_rankings():
    """Migrate existing ranking data to new enhanced system"""
    try:
        logger.info("=" * 80)
        logger.info("🔄 Starting ranking system migration")
        logger.info("=" * 80)
        
        from backend.app.db_connection import get_database
        from backend.app.services.enhanced_ranking_service import EnhancedRankingService
        
        # Get database connection
        db = await get_database()
        if not db:
            logger.error("❌ Database connection failed")
            return False
        
        logger.info("✅ Database connected")
        
        # Initialize enhanced ranking service
        ranking_service = EnhancedRankingService(db)
        
        # Step 1: Get all unique regions
        logger.info("\n📍 Step 1: Finding all regions...")
        regions = await db.user_rankings.distinct("region", {"region": {"$ne": None}})
        logger.info(f"   Found {len(regions)} regions: {regions}")
        
        # Step 2: Get all unique universities
        logger.info("\n🎓 Step 2: Finding all universities...")
        universities = await db.user_rankings.distinct(
            "university_short",
            {"university_short": {"$ne": None}}
        )
        logger.info(f"   Found {len(universities)} universities: {universities}")
        
        # Step 3: Update regional rankings
        logger.info("\n📊 Step 3: Updating regional rankings...")
        regional_success = 0
        regional_failed = 0
        
        for region in regions:
            try:
                result = await ranking_service.batch_update_regional_rankings(region)
                if result["success"]:
                    regional_success += 1
                    logger.info(f"   ✅ {region}: {result['users_updated']} users updated")
                else:
                    regional_failed += 1
                    logger.error(f"   ❌ {region}: {result.get('error')}")
            except Exception as e:
                regional_failed += 1
                logger.error(f"   ❌ {region}: {str(e)}")
        
        logger.info(f"\n   Regional Summary: {regional_success} success, {regional_failed} failed")
        
        # Step 4: Update university rankings
        logger.info("\n📊 Step 4: Updating university rankings...")
        university_success = 0
        university_failed = 0
        
        for university in universities:
            try:
                result = await ranking_service.batch_update_university_rankings(university)
                if result["success"]:
                    university_success += 1
                    logger.info(f"   ✅ {university}: {result['users_updated']} users updated")
                else:
                    university_failed += 1
                    logger.error(f"   ❌ {university}: {result.get('error')}")
            except Exception as e:
                university_failed += 1
                logger.error(f"   ❌ {university}: {str(e)}")
        
        logger.info(f"\n   University Summary: {university_success} success, {university_failed} failed")
        
        # Step 5: Verify migration
        logger.info("\n✅ Step 5: Verifying migration...")
        
        user_rankings_count = await db.user_rankings.count_documents({})
        regional_rankings_count = await db.regional_rankings.count_documents({})
        university_rankings_count = await db.university_rankings.count_documents({})
        
        logger.info(f"   user_rankings: {user_rankings_count} documents")
        logger.info(f"   regional_rankings: {regional_rankings_count} documents")
        logger.info(f"   university_rankings: {university_rankings_count} documents")
        
        # Step 6: Create indexes
        logger.info("\n🔧 Step 6: Creating indexes...")
        
        try:
            # user_rankings indexes
            await db.user_rankings.create_index([("user_id", 1)], unique=True)
            await db.user_rankings.create_index([("region", 1), ("overall_score", -1)])
            await db.user_rankings.create_index([("university_short", 1), ("overall_score", -1)])
            logger.info("   ✅ user_rankings indexes created")
            
            # regional_rankings indexes
            await db.regional_rankings.create_index([("region", 1), ("rank", 1)])
            await db.regional_rankings.create_index([("region", 1), ("overall_score", -1)])
            logger.info("   ✅ regional_rankings indexes created")
            
            # university_rankings indexes
            await db.university_rankings.create_index([("university_short", 1), ("rank", 1)])
            await db.university_rankings.create_index([("university_short", 1), ("overall_score", -1)])
            logger.info("   ✅ university_rankings indexes created")
            
        except Exception as e:
            logger.warning(f"   ⚠️  Index creation warning: {e}")
            logger.warning("   (Indexes may already exist)")
        
        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("🎉 Migration completed!")
        logger.info("=" * 80)
        logger.info(f"✅ Regions migrated: {regional_success}/{len(regions)}")
        logger.info(f"✅ Universities migrated: {university_success}/{len(universities)}")
        logger.info(f"✅ Total users with rankings: {user_rankings_count}")
        logger.info(f"✅ Regional rankings created: {regional_rankings_count}")
        logger.info(f"✅ University rankings created: {university_rankings_count}")
        
        if regional_failed > 0 or university_failed > 0:
            logger.warning(f"\n⚠️  Some migrations failed:")
            logger.warning(f"   Regional failures: {regional_failed}")
            logger.warning(f"   University failures: {university_failed}")
            logger.warning(f"   Check logs above for details")
        
        logger.info("\n📝 Next steps:")
        logger.info("   1. Verify data in MongoDB")
        logger.info("   2. Setup cron job for hourly updates")
        logger.info("   3. Test API endpoints")
        logger.info("   4. Access frontend rankings page")
        logger.info("\n" + "=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fatal error during migration: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def verify_migration():
    """Verify migration was successful"""
    try:
        from backend.app.db_connection import get_database
        
        db = await get_database()
        if not db:
            logger.error("❌ Database connection failed")
            return False
        
        logger.info("\n🔍 Verification Report:")
        logger.info("=" * 80)
        
        # Check collections exist
        collections = await db.list_collection_names()
        required_collections = ['user_rankings', 'regional_rankings', 'university_rankings']
        
        for collection in required_collections:
            if collection in collections:
                count = await db[collection].count_documents({})
                logger.info(f"✅ {collection}: {count} documents")
            else:
                logger.error(f"❌ {collection}: NOT FOUND")
        
        # Sample data check
        logger.info("\n📊 Sample Data:")
        sample_user = await db.user_rankings.find_one({})
        if sample_user:
            logger.info(f"   User: {sample_user.get('github_username')}")
            logger.info(f"   Score: {sample_user.get('overall_score')}")
            logger.info(f"   Regional Rank: {sample_user.get('regional_rank')}")
            logger.info(f"   University Rank: {sample_user.get('university_rank')}")
        
        # Index check
        logger.info("\n🔧 Indexes:")
        for collection in required_collections:
            indexes = await db[collection].index_information()
            logger.info(f"   {collection}: {len(indexes)} indexes")
        
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate ranking system to enhanced version')
    parser.add_argument('--verify-only', action='store_true', help='Only verify migration, do not migrate')
    args = parser.parse_args()
    
    if args.verify_only:
        logger.info("Running verification only...")
        success = await verify_migration()
    else:
        logger.info("Running full migration...")
        success = await migrate_rankings()
        
        if success:
            logger.info("\nRunning verification...")
            await verify_migration()
    
    if success:
        logger.info("\n✅ All operations completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
