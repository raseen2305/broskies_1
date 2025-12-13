#!/usr/bin/env python3
"""
Database Schema Verification Script
Verifies the current database structure and suggests missing indexes
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

async def verify_database_structure():
    """Verify the structure of all databases"""
    logger.info("🔍 Verifying database structure...")
    
    databases = {
        "external_users": get_external_users_db,
        "raseen_temp_user": get_raseen_temp_user_db,
        "raseen_main_user": get_raseen_main_user_db,
        "srie_main_user": get_srie_main_user_db,
        "raseen_main_hr": get_raseen_main_hr_db,
        "srie_main_hr": get_srie_main_hr_db
    }
    
    for db_name, db_func in databases.items():
        try:
            logger.info(f"\n📊 Checking {db_name} database...")
            db = await db_func()
            
            # List all collections
            collections = await db.list_collection_names()
            logger.info(f"   Collections: {collections}")
            
            # Check each collection
            for collection_name in collections:
                collection = db[collection_name]
                
                # Get document count
                count = await collection.count_documents({})
                
                # Get indexes
                indexes = await collection.list_indexes().to_list(length=None)
                index_names = [idx.get('name', 'unnamed') for idx in indexes]
                
                logger.info(f"   📁 {collection_name}:")
                logger.info(f"      Documents: {count}")
                logger.info(f"      Indexes: {len(indexes)} - {index_names}")
                
                # Show sample document structure if collection has data
                if count > 0:
                    sample = await collection.find_one({})
                    if sample:
                        keys = list(sample.keys())
                        logger.info(f"      Sample fields: {keys[:10]}{'...' if len(keys) > 10 else ''}")
            
        except Exception as e:
            logger.error(f"❌ Failed to check {db_name}: {e}")

async def check_required_fields():
    """Check if required fields exist in the collections"""
    logger.info("\n🔍 Checking required fields...")
    
    # Check external_users database
    try:
        db = await get_external_users_db()
        
        # Check if user_details collection exists and has required fields
        if "user_details" in await db.list_collection_names():
            sample = await db.user_details.find_one({})
            if sample:
                required_fields = [
                    "github_username", "email", "bio", "company", "scan_date",
                    "total_stars", "total_forks", "activity_score", "languages"
                ]
                
                missing_fields = [field for field in required_fields if field not in sample]
                if missing_fields:
                    logger.warning(f"⚠️ external_users.user_details missing fields: {missing_fields}")
                else:
                    logger.info("✅ external_users.user_details has all required fields")
        
    except Exception as e:
        logger.error(f"❌ Failed to check external_users fields: {e}")
    
    # Check internal users database
    try:
        db = await get_raseen_main_user_db()
        
        if "internal_users_data" in await db.list_collection_names():
            sample = await db.internal_users_data.find_one({})
            if sample:
                required_fields = [
                    "github_username", "official_name", "email", "university",
                    "nationality", "state", "district", "acid_scoring"
                ]
                
                missing_fields = [field for field in required_fields if field not in sample]
                if missing_fields:
                    logger.warning(f"⚠️ internal_users_data missing fields: {missing_fields}")
                else:
                    logger.info("✅ internal_users_data has all required fields")
        
    except Exception as e:
        logger.error(f"❌ Failed to check internal users fields: {e}")
    
    # Check HR database
    try:
        db = await get_raseen_main_hr_db()
        
        if "hr_users" in await db.list_collection_names():
            sample = await db.hr_users.find_one({})
            if sample:
                required_fields = [
                    "name", "email", "google_id", "company", "role",
                    "date_filled", "approved"
                ]
                
                missing_fields = [field for field in required_fields if field not in sample]
                if missing_fields:
                    logger.warning(f"⚠️ hr_users missing fields: {missing_fields}")
                else:
                    logger.info("✅ hr_users has all required fields")
        
    except Exception as e:
        logger.error(f"❌ Failed to check HR fields: {e}")

async def suggest_missing_collections():
    """Suggest missing collections that should be created"""
    logger.info("\n💡 Checking for missing collections...")
    
    expected_collections = {
        "external_users": ["user_details", "external_scan_cache"],
        "raseen_temp_user": ["internal_users_data", "internal_scan_cache"],
        "raseen_main_user": ["internal_users_data"],
        "srie_main_user": ["internal_users_data"],
        "raseen_main_hr": ["hr_users"],
        "srie_main_hr": ["hr_users"]
    }
    
    databases = {
        "external_users": get_external_users_db,
        "raseen_temp_user": get_raseen_temp_user_db,
        "raseen_main_user": get_raseen_main_user_db,
        "srie_main_user": get_srie_main_user_db,
        "raseen_main_hr": get_raseen_main_hr_db,
        "srie_main_hr": get_srie_main_hr_db
    }
    
    for db_name, db_func in databases.items():
        try:
            db = await db_func()
            existing_collections = await db.list_collection_names()
            expected = expected_collections.get(db_name, [])
            
            missing = [col for col in expected if col not in existing_collections]
            if missing:
                logger.warning(f"⚠️ {db_name} missing collections: {missing}")
            else:
                logger.info(f"✅ {db_name} has all expected collections")
                
        except Exception as e:
            logger.error(f"❌ Failed to check {db_name} collections: {e}")

async def main():
    """Main verification function"""
    logger.info("🚀 Starting database schema verification...")
    
    await verify_database_structure()
    await check_required_fields()
    await suggest_missing_collections()
    
    logger.info("\n🎉 Database schema verification completed!")

if __name__ == "__main__":
    asyncio.run(main())