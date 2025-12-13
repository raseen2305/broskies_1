"""
Migration Script: Populate hr_view Collection

This script migrates existing data from user_rankings to the new hr_view collection.
The hr_view collection is the centralized source for all developer data needed
by the HR dashboard.

Usage:
    python migrate_to_hr_view.py [--limit N] [--dry-run]
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db_connection import get_database
from app.services.hr_view_service import HRViewService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_to_hr_view(limit: int = None, dry_run: bool = False):
    """
    Migrate data from user_rankings to hr_view collection
    
    Args:
        limit: Optional limit on number of users to migrate
        dry_run: If True, only show what would be migrated without making changes
    """
    try:
        logger.info("=" * 80)
        logger.info("HR VIEW MIGRATION SCRIPT")
        logger.info("=" * 80)
        
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made")
        
        # Get database connection
        db = await get_database()
        if not db:
            logger.error("❌ Failed to connect to database")
            return
        
        logger.info("✅ Connected to database")
        
        # Initialize HR view service
        hr_view_service = HRViewService(db)
        
        # Ensure indexes
        if not dry_run:
            logger.info("📊 Creating indexes for hr_view collection...")
            await hr_view_service.ensure_indexes()
        
        # Get statistics
        logger.info("\n" + "=" * 80)
        logger.info("CURRENT STATE")
        logger.info("=" * 80)
        
        user_rankings_count = await db.user_rankings.count_documents({})
        hr_view_count = await db.hr_view.count_documents({})
        
        logger.info(f"📊 user_rankings collection: {user_rankings_count} documents")
        logger.info(f"📊 hr_view collection: {hr_view_count} documents")
        
        if user_rankings_count == 0:
            logger.warning("⚠️  No data in user_rankings to migrate")
            return
        
        # Perform migration
        logger.info("\n" + "=" * 80)
        logger.info("MIGRATION")
        logger.info("=" * 80)
        
        if dry_run:
            logger.info(f"Would migrate {limit if limit else user_rankings_count} users from user_rankings to hr_view")
            
            # Show sample data
            sample = await db.user_rankings.find_one({})
            if sample:
                logger.info("\nSample user_rankings document fields:")
                for key in sorted(sample.keys()):
                    if key != "_id":
                        logger.info(f"  - {key}")
        else:
            logger.info(f"🚀 Starting migration of {limit if limit else 'all'} users...")
            
            start_time = datetime.now()
            
            result = await hr_view_service.bulk_sync_from_user_rankings(limit=limit)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("\n" + "=" * 80)
            logger.info("MIGRATION RESULTS")
            logger.info("=" * 80)
            
            if result.get("success"):
                logger.info(f"✅ Migration completed successfully")
                logger.info(f"   Total users: {result.get('total', 0)}")
                logger.info(f"   Successful: {result.get('success_count', 0)}")
                logger.info(f"   Errors: {result.get('error_count', 0)}")
                logger.info(f"   Duration: {duration:.2f} seconds")
                
                if result.get('error_count', 0) > 0:
                    logger.warning("\n⚠️  Errors encountered:")
                    for error in result.get('errors', [])[:10]:
                        logger.warning(f"   - {error.get('username')}: {error.get('error')}")
            else:
                logger.error(f"❌ Migration failed: {result.get('error')}")
        
        # Final statistics
        logger.info("\n" + "=" * 80)
        logger.info("FINAL STATE")
        logger.info("=" * 80)
        
        if not dry_run:
            hr_view_count_after = await db.hr_view.count_documents({})
            logger.info(f"📊 hr_view collection: {hr_view_count_after} documents")
            logger.info(f"📈 New documents added: {hr_view_count_after - hr_view_count}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ MIGRATION COMPLETE")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Migration failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())


async def verify_migration():
    """Verify the migration by comparing sample data"""
    try:
        logger.info("\n" + "=" * 80)
        logger.info("VERIFICATION")
        logger.info("=" * 80)
        
        db = await get_database()
        if not db:
            logger.error("❌ Failed to connect to database")
            return
        
        # Get sample from both collections
        user_rankings_sample = await db.user_rankings.find_one({})
        hr_view_sample = await db.hr_view.find_one({})
        
        if not user_rankings_sample:
            logger.warning("⚠️  No data in user_rankings")
            return
        
        if not hr_view_sample:
            logger.warning("⚠️  No data in hr_view")
            return
        
        username = user_rankings_sample.get("github_username")
        logger.info(f"Comparing data for user: {username}")
        
        # Compare key fields
        fields_to_check = [
            "github_username", "name", "overall_score", "primary_language",
            "regional_rank", "university_rank"
        ]
        
        logger.info("\nField comparison:")
        for field in fields_to_check:
            ur_value = user_rankings_sample.get(field)
            hv_value = hr_view_sample.get(field)
            match = "✅" if ur_value == hv_value else "❌"
            logger.info(f"  {match} {field}: {ur_value} == {hv_value}")
        
        logger.info("\n✅ Verification complete")
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate data to hr_view collection")
    parser.add_argument("--limit", type=int, help="Limit number of users to migrate")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--verify", action="store_true", help="Verify migration after completion")
    
    args = parser.parse_args()
    
    # Run migration
    asyncio.run(migrate_to_hr_view(limit=args.limit, dry_run=args.dry_run))
    
    # Run verification if requested
    if args.verify and not args.dry_run:
        asyncio.run(verify_migration())


if __name__ == "__main__":
    main()
