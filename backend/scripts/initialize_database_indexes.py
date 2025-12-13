#!/usr/bin/env python3
"""
Database Index Initialization Script
Creates all required indexes for the multi-database architecture
"""

import asyncio
import sys
import os
sys.path.append('.')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.db_connection_multi import (
    get_external_users_db,
    get_raseen_temp_user_db,
    get_raseen_main_user_db,
    get_srie_main_user_db,
    get_raseen_main_hr_db,
    get_srie_main_hr_db
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_index_safely(collection, index_spec, **kwargs):
    """Create index safely, ignoring if it already exists"""
    try:
        await collection.create_index(index_spec, **kwargs)
        return True
    except Exception as e:
        if "already exists" in str(e) or "IndexOptionsConflict" in str(e):
            logger.debug(f"Index already exists: {index_spec}")
            return False
        else:
            logger.warning(f"Failed to create index {index_spec}: {e}")
            return False

async def create_external_users_indexes():
    """Create indexes for external_users database"""
    logger.info("🌐 Creating indexes for external_users database...")
    
    try:
        db = await get_external_users_db()
        
        # user_details collection indexes
        collection = db.user_details
        
        # Primary indexes
        await create_index_safely(collection, "github_username", unique=True)
        await create_index_safely(collection, "email")
        await create_index_safely(collection, [("scan_date", -1)])
        
        # Performance indexes
        await create_index_safely(collection, [("total_stars", -1)])
        await create_index_safely(collection, [("activity_score", -1)])
        await create_index_safely(collection, [("importance_score", -1)])
        await create_index_safely(collection, "primary_language")
        await create_index_safely(collection, "company")
        
        # Compound indexes
        await create_index_safely(collection, [("github_username", 1), ("scan_date", -1)])
        await create_index_safely(collection, [("total_stars", -1), ("total_forks", -1)])
        
        # Text search index
        await create_index_safely(collection, [
            ("github_username", "text"),
            ("bio", "text"),
            ("company", "text"),
            ("description", "text")
        ])
        
        # external_scan_cache collection indexes
        cache_collection = db.external_scan_cache
        await create_index_safely(cache_collection, "username")
        await create_index_safely(cache_collection, "user_id")
        await create_index_safely(cache_collection, [("scan_date", -1)])
        await create_index_safely(cache_collection, "user_type")
        
        logger.info("✅ External users database indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create external users indexes: {e}")
        raise

async def create_temp_user_indexes():
    """Create indexes for raseen_temp_user database"""
    logger.info("🔐 Creating indexes for raseen_temp_user database...")
    
    try:
        db = await get_raseen_temp_user_db()
        
        # internal_users_data collection indexes
        collection = db.internal_users_data
        
        # Primary indexes
        await create_index_safely(collection, "github_username", unique=True)
        await create_index_safely(collection, "email")
        await create_index_safely(collection, "official_name")
        
        # Geographic indexes
        await create_index_safely(collection, "nationality")
        await create_index_safely(collection, "state")
        await create_index_safely(collection, "district")
        await create_index_safely(collection, "university")
        
        # Performance indexes
        await create_index_safely(collection, [("scan_date", -1)])
        await create_index_safely(collection, [("total_stars", -1)])
        await create_index_safely(collection, [("activity_score", -1)])
        await create_index_safely(collection, [("acid_scoring.overall_score", -1)])
        await create_index_safely(collection, [("importance_score", -1)])
        await create_index_safely(collection, "primary_language")
        
        # TTL index for 24-hour expiry
        await create_index_safely(collection, "expires_at", expireAfterSeconds=0)
        
        # Compound indexes
        await create_index_safely(collection, [("github_username", 1), ("scan_date", -1)])
        await create_index_safely(collection, [("nationality", 1), ("state", 1)])
        await create_index_safely(collection, [("university", 1), ("nationality", 1)])
        
        # Text search index
        await create_index_safely(collection, [
            ("github_username", "text"),
            ("official_name", "text"),
            ("bio", "text"),
            ("company", "text"),
            ("university", "text")
        ])
        
        # internal_scan_cache collection indexes
        cache_collection = db.internal_scan_cache
        await create_index_safely(cache_collection, "username")
        await create_index_safely(cache_collection, "user_id")
        await create_index_safely(cache_collection, [("scan_date", -1)])
        await create_index_safely(cache_collection, "expires_at", expireAfterSeconds=0)
        
        logger.info("✅ Temp user database indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create temp user indexes: {e}")
        raise

async def create_main_user_indexes():
    """Create indexes for raseen_main_user database"""
    logger.info("🔐 Creating indexes for raseen_main_user database...")
    
    try:
        db = await get_raseen_main_user_db()
        
        # internal_users_data collection indexes
        collection = db.internal_users_data
        
        # All temp user indexes plus permanent storage indexes
        await collection.create_index("github_username", unique=True)
        await collection.create_index("email")
        await collection.create_index("official_name")
        await collection.create_index("nationality")
        await collection.create_index("state")
        await collection.create_index("district")
        await collection.create_index("university")
        await collection.create_index([("scan_date", -1)])
        await collection.create_index([("total_stars", -1)])
        await collection.create_index([("activity_score", -1)])
        await collection.create_index([("acid_scoring.overall_score", -1)])
        await collection.create_index([("importance_score", -1)])
        await collection.create_index("primary_language")
        
        # Additional permanent storage indexes
        await collection.create_index([("migrated_from_temp", -1)])
        await collection.create_index([("ranking_score", -1)])
        await collection.create_index("ranking_position")
        await collection.create_index("ranking_eligible")
        await collection.create_index([("profile_completeness", -1)])
        
        # Compound indexes
        await collection.create_index([("github_username", 1), ("scan_date", -1)])
        await collection.create_index([("nationality", 1), ("state", 1)])
        await collection.create_index([("university", 1), ("nationality", 1)])
        await collection.create_index([("ranking_eligible", 1), ("ranking_score", -1)])
        
        # Text search index
        await collection.create_index([
            ("github_username", "text"),
            ("official_name", "text"),
            ("bio", "text"),
            ("company", "text"),
            ("university", "text")
        ])
        
        logger.info("✅ Main user database indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create main user indexes: {e}")
        raise

async def create_backup_user_indexes():
    """Create indexes for srie_main_user database (backup)"""
    logger.info("🔐 Creating indexes for srie_main_user database (backup)...")
    
    try:
        db = await get_srie_main_user_db()
        
        # internal_users_data collection indexes (same as main + backup specific)
        collection = db.internal_users_data
        
        # All main user indexes
        await collection.create_index("github_username", unique=True)
        await collection.create_index("email")
        await collection.create_index("official_name")
        await collection.create_index("nationality")
        await collection.create_index("state")
        await collection.create_index("district")
        await collection.create_index("university")
        await collection.create_index([("scan_date", -1)])
        await collection.create_index([("total_stars", -1)])
        await collection.create_index([("activity_score", -1)])
        await collection.create_index([("acid_scoring.overall_score", -1)])
        await collection.create_index([("importance_score", -1)])
        await collection.create_index("primary_language")
        await collection.create_index([("migrated_from_temp", -1)])
        await collection.create_index([("ranking_score", -1)])
        await collection.create_index("ranking_position")
        await collection.create_index("ranking_eligible")
        await collection.create_index([("profile_completeness", -1)])
        
        # Backup-specific indexes
        await collection.create_index([("backup_date", -1)])
        await collection.create_index("sync_status")
        
        # Compound indexes
        await collection.create_index([("github_username", 1), ("scan_date", -1)])
        await collection.create_index([("nationality", 1), ("state", 1)])
        await collection.create_index([("university", 1), ("nationality", 1)])
        await collection.create_index([("ranking_eligible", 1), ("ranking_score", -1)])
        
        # Text search index
        await collection.create_index([
            ("github_username", "text"),
            ("official_name", "text"),
            ("bio", "text"),
            ("company", "text"),
            ("university", "text")
        ])
        
        logger.info("✅ Backup user database indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create backup user indexes: {e}")
        raise

async def create_hr_indexes():
    """Create indexes for raseen_main_hr database"""
    logger.info("🏢 Creating indexes for raseen_main_hr database...")
    
    try:
        db = await get_raseen_main_hr_db()
        
        # hr_users collection indexes
        collection = db.hr_users
        
        # Primary indexes
        await collection.create_index("email", unique=True)
        await collection.create_index("google_id", unique=True)
        
        # Query optimization indexes
        await collection.create_index("company")
        await collection.create_index("role")
        await collection.create_index("approved")
        await collection.create_index("is_active")
        await collection.create_index("access_level")
        
        # Performance indexes
        await collection.create_index([("date_filled", -1)])
        await collection.create_index([("last_login", -1)])
        await collection.create_index([("created_at", -1)])
        
        # Compound indexes
        await collection.create_index([("company", 1), ("role", 1)])
        await collection.create_index([("approved", 1), ("is_active", 1)])
        await collection.create_index([("company", 1), ("approved", 1)])
        
        # Text search index
        await collection.create_index([
            ("name", "text"),
            ("company", "text"),
            ("role", "text"),
            ("departments", "text")
        ])
        
        logger.info("✅ HR database indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create HR indexes: {e}")
        raise

async def create_backup_hr_indexes():
    """Create indexes for srie_main_hr database (backup)"""
    logger.info("🏢 Creating indexes for srie_main_hr database (backup)...")
    
    try:
        db = await get_srie_main_hr_db()
        
        # hr_users collection indexes (same as main + backup specific)
        collection = db.hr_users
        
        # All main HR indexes
        await collection.create_index("email", unique=True)
        await collection.create_index("google_id", unique=True)
        await collection.create_index("company")
        await collection.create_index("role")
        await collection.create_index("approved")
        await collection.create_index("is_active")
        await collection.create_index("access_level")
        await collection.create_index([("date_filled", -1)])
        await collection.create_index([("last_login", -1)])
        await collection.create_index([("created_at", -1)])
        
        # Backup-specific indexes
        await collection.create_index([("backup_date", -1)])
        await collection.create_index("sync_status")
        
        # Compound indexes
        await collection.create_index([("company", 1), ("role", 1)])
        await collection.create_index([("approved", 1), ("is_active", 1)])
        await collection.create_index([("company", 1), ("approved", 1)])
        
        # Text search index
        await collection.create_index([
            ("name", "text"),
            ("company", "text"),
            ("role", "text"),
            ("departments", "text")
        ])
        
        logger.info("✅ Backup HR database indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create backup HR indexes: {e}")
        raise

async def initialize_all_indexes():
    """Initialize all database indexes"""
    logger.info("🚀 Starting database index initialization...")
    
    try:
        # Create indexes for all databases
        await create_external_users_indexes()
        await create_temp_user_indexes()
        await create_main_user_indexes()
        await create_backup_user_indexes()
        await create_hr_indexes()
        await create_backup_hr_indexes()
        
        logger.info("🎉 All database indexes created successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database indexes: {e}")
        raise

async def verify_indexes():
    """Verify that all indexes were created correctly"""
    logger.info("🔍 Verifying database indexes...")
    
    try:
        # Check external_users database
        db = await get_external_users_db()
        indexes = await db.user_details.list_indexes().to_list(length=None)
        logger.info(f"📊 external_users.user_details indexes: {len(indexes)}")
        
        # Check temp user database
        db = await get_raseen_temp_user_db()
        indexes = await db.internal_users_data.list_indexes().to_list(length=None)
        logger.info(f"📊 raseen_temp_user.internal_users_data indexes: {len(indexes)}")
        
        # Check main user database
        db = await get_raseen_main_user_db()
        indexes = await db.internal_users_data.list_indexes().to_list(length=None)
        logger.info(f"📊 raseen_main_user.internal_users_data indexes: {len(indexes)}")
        
        # Check HR database
        db = await get_raseen_main_hr_db()
        indexes = await db.hr_users.list_indexes().to_list(length=None)
        logger.info(f"📊 raseen_main_hr.hr_users indexes: {len(indexes)}")
        
        logger.info("✅ Index verification completed")
        
    except Exception as e:
        logger.error(f"❌ Failed to verify indexes: {e}")
        raise

if __name__ == "__main__":
    async def main():
        await initialize_all_indexes()
        await verify_indexes()
    
    asyncio.run(main())