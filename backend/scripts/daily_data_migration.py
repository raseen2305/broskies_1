#!/usr/bin/env python3
"""
Daily Data Migration Script
Migrates data from temp databases to main databases every 24 hours
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
sys.path.append('.')

from app.db_connection_multi import (
    get_raseen_temp_user_db,
    get_raseen_main_user_db,
    get_srie_main_user_db
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_temp_to_main():
    """Migrate data from raseen_temp_user to raseen_main_user"""
    logger.info("🔄 Starting migration from temp to main database...")
    
    try:
        temp_db = await get_raseen_temp_user_db()
        main_db = await get_raseen_main_user_db()
        
        # Find data older than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Get users to migrate
        users_to_migrate = await temp_db.internal_users_data.find({
            "created_at": {"$lt": cutoff_time}
        }).to_list(length=None)
        
        logger.info(f"📊 Found {len(users_to_migrate)} users to migrate")
        
        migrated_count = 0
        for user in users_to_migrate:
            try:
                # Add migration metadata
                user["migrated_from_temp"] = datetime.utcnow()
                user["data_retention_policy"] = "permanent"
                user["profile_completeness"] = calculate_profile_completeness(user)
                user["ranking_eligible"] = True
                user["ranking_score"] = user.get("acid_scoring", {}).get("overall_score", 0)
                
                # Remove TTL field
                if "expires_at" in user:
                    del user["expires_at"]
                
                # Check if user already exists in main database
                existing_user = await main_db.internal_users_data.find_one({
                    "github_username": user["github_username"]
                })
                
                if existing_user:
                    # Update existing user
                    await main_db.internal_users_data.update_one(
                        {"github_username": user["github_username"]},
                        {"$set": user}
                    )
                    logger.info(f"📝 Updated existing user: {user['github_username']}")
                else:
                    # Insert new user
                    await main_db.internal_users_data.insert_one(user)
                    logger.info(f"➕ Inserted new user: {user['github_username']}")
                
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to migrate user {user.get('github_username', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ Successfully migrated {migrated_count} users to main database")
        return migrated_count
        
    except Exception as e:
        logger.error(f"❌ Failed to migrate temp to main: {e}")
        raise

async def migrate_main_to_backup():
    """Migrate data from raseen_main_user to srie_main_user (backup)"""
    logger.info("🔄 Starting migration from main to backup database...")
    
    try:
        main_db = await get_raseen_main_user_db()
        backup_db = await get_srie_main_user_db()
        
        # Get all users from main database
        users_to_backup = await main_db.internal_users_data.find({}).to_list(length=None)
        
        logger.info(f"📊 Found {len(users_to_backup)} users to backup")
        
        backed_up_count = 0
        for user in users_to_backup:
            try:
                # Add backup metadata
                user["backup_source"] = "raseen_main_user"
                user["backup_date"] = datetime.utcnow()
                user["backup_version"] = "v1.0"
                user["sync_status"] = "synchronized"
                
                # Check if user already exists in backup database
                existing_user = await backup_db.internal_users_data.find_one({
                    "github_username": user["github_username"]
                })
                
                if existing_user:
                    # Update existing backup
                    await backup_db.internal_users_data.update_one(
                        {"github_username": user["github_username"]},
                        {"$set": user}
                    )
                    logger.debug(f"📝 Updated backup for user: {user['github_username']}")
                else:
                    # Insert new backup
                    await backup_db.internal_users_data.insert_one(user)
                    logger.debug(f"➕ Created backup for user: {user['github_username']}")
                
                backed_up_count += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to backup user {user.get('github_username', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ Successfully backed up {backed_up_count} users to backup database")
        return backed_up_count
        
    except Exception as e:
        logger.error(f"❌ Failed to migrate main to backup: {e}")
        raise

async def cleanup_temp_database():
    """Clean up migrated data from temp database"""
    logger.info("🧹 Cleaning up temp database...")
    
    try:
        temp_db = await get_raseen_temp_user_db()
        
        # Find data older than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Delete migrated users
        result = await temp_db.internal_users_data.delete_many({
            "created_at": {"$lt": cutoff_time}
        })
        
        logger.info(f"🗑️ Deleted {result.deleted_count} users from temp database")
        
        # Clean up scan cache
        cache_result = await temp_db.internal_scan_cache.delete_many({
            "scan_date": {"$lt": cutoff_time}
        })
        
        logger.info(f"🗑️ Deleted {cache_result.deleted_count} cache entries from temp database")
        
        return result.deleted_count + cache_result.deleted_count
        
    except Exception as e:
        logger.error(f"❌ Failed to cleanup temp database: {e}")
        raise

def calculate_profile_completeness(user):
    """Calculate profile completeness percentage"""
    required_fields = [
        "github_username", "official_name", "email", "university",
        "nationality", "state", "district", "bio", "company"
    ]
    
    optional_fields = [
        "links", "description", "profile_pic"
    ]
    
    completed_required = sum(1 for field in required_fields if user.get(field))
    completed_optional = sum(1 for field in optional_fields if user.get(field))
    
    # Required fields are worth 80%, optional fields 20%
    required_percentage = (completed_required / len(required_fields)) * 80
    optional_percentage = (completed_optional / len(optional_fields)) * 20
    
    return round(required_percentage + optional_percentage, 1)

async def update_ranking_positions():
    """Update ranking positions for all users"""
    logger.info("🏆 Updating ranking positions...")
    
    try:
        main_db = await get_raseen_main_user_db()
        
        # Get all eligible users sorted by ranking score
        users = await main_db.internal_users_data.find({
            "ranking_eligible": True
        }).sort("ranking_score", -1).to_list(length=None)
        
        # Update ranking positions
        for position, user in enumerate(users, 1):
            await main_db.internal_users_data.update_one(
                {"_id": user["_id"]},
                {"$set": {"ranking_position": position}}
            )
        
        logger.info(f"🏆 Updated ranking positions for {len(users)} users")
        
    except Exception as e:
        logger.error(f"❌ Failed to update ranking positions: {e}")
        raise

async def generate_migration_report():
    """Generate migration report"""
    logger.info("📊 Generating migration report...")
    
    try:
        temp_db = await get_raseen_temp_user_db()
        main_db = await get_raseen_main_user_db()
        backup_db = await get_srie_main_user_db()
        
        # Count records in each database
        temp_count = await temp_db.internal_users_data.count_documents({})
        main_count = await main_db.internal_users_data.count_documents({})
        backup_count = await backup_db.internal_users_data.count_documents({})
        
        # Count recent migrations
        recent_migrations = await main_db.internal_users_data.count_documents({
            "migrated_from_temp": {"$gte": datetime.utcnow() - timedelta(hours=1)}
        })
        
        report = {
            "migration_date": datetime.utcnow().isoformat(),
            "temp_database_count": temp_count,
            "main_database_count": main_count,
            "backup_database_count": backup_count,
            "recent_migrations": recent_migrations,
            "sync_status": "synchronized" if main_count == backup_count else "out_of_sync"
        }
        
        logger.info("📊 Migration Report:")
        logger.info(f"   Temp Database: {temp_count} users")
        logger.info(f"   Main Database: {main_count} users")
        logger.info(f"   Backup Database: {backup_count} users")
        logger.info(f"   Recent Migrations: {recent_migrations} users")
        logger.info(f"   Sync Status: {report['sync_status']}")
        
        return report
        
    except Exception as e:
        logger.error(f"❌ Failed to generate migration report: {e}")
        raise

async def daily_migration_process():
    """Execute the complete daily migration process"""
    logger.info("🚀 Starting daily migration process...")
    start_time = datetime.utcnow()
    
    try:
        # Step 1: Migrate from temp to main
        migrated_count = await migrate_temp_to_main()
        
        # Step 2: Migrate from main to backup
        backed_up_count = await migrate_main_to_backup()
        
        # Step 3: Clean up temp database
        cleaned_count = await cleanup_temp_database()
        
        # Step 4: Update ranking positions
        await update_ranking_positions()
        
        # Step 5: Generate report
        report = await generate_migration_report()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("🎉 Daily migration process completed successfully!")
        logger.info(f"⏱️ Total duration: {duration:.2f} seconds")
        logger.info(f"📊 Summary:")
        logger.info(f"   - Migrated: {migrated_count} users")
        logger.info(f"   - Backed up: {backed_up_count} users")
        logger.info(f"   - Cleaned: {cleaned_count} records")
        
        return {
            "success": True,
            "duration": duration,
            "migrated_count": migrated_count,
            "backed_up_count": backed_up_count,
            "cleaned_count": cleaned_count,
            "report": report
        }
        
    except Exception as e:
        logger.error(f"❌ Daily migration process failed: {e}")
        raise

if __name__ == "__main__":
    async def main():
        await daily_migration_process()
    
    asyncio.run(main())