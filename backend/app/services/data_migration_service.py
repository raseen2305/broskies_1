"""
Data Migration and Lifecycle Management Service
Handles 24-hour data migration from temp to main databases with backup replication
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
from dataclasses import dataclass
import time

from app.db_connection_multi import (
    multi_db_manager, 
    DatabaseType,
    get_raseen_temp_user_db,
    get_raseen_main_user_db,
    get_srie_main_user_db,
    get_raseen_main_hr_db,
    get_srie_main_hr_db
)

logger = logging.getLogger(__name__)

@dataclass
class MigrationRecord:
    """Record of a data migration operation"""
    migration_id: str
    user_id: str
    source_db: str
    target_db: str
    backup_db: str
    migration_date: datetime
    status: str  # "pending", "completed", "failed"
    data_size: int
    retry_count: int
    error_message: Optional[str] = None

@dataclass
class MigrationStats:
    """Statistics for migration operations"""
    total_records: int
    migrated_records: int
    failed_records: int
    total_data_size: int
    migration_duration: float
    errors: List[str]

class DataMigrationService:
    """Service for managing data lifecycle and migration between databases"""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay_base = 2  # seconds
        self.migration_batch_size = 100
        self.migration_timeout = 300  # 5 minutes per batch
        
    async def migrate_expired_data(self) -> MigrationStats:
        """
        Migrate data that has been in temp storage for 24 hours
        Returns statistics about the migration operation
        """
        logger.info("🔐 [INTERNAL] Starting 24-hour data migration process...")
        
        start_time = time.time()
        stats = MigrationStats(
            total_records=0,
            migrated_records=0,
            failed_records=0,
            total_data_size=0,
            migration_duration=0.0,
            errors=[]
        )
        
        try:
            # Get databases
            temp_db = await get_raseen_temp_user_db()
            main_db = await get_raseen_main_user_db()
            backup_db = await get_srie_main_user_db()
            
            if not all([temp_db, main_db, backup_db]):
                error_msg = "Failed to connect to required databases for migration"
                logger.error(f"❌ {error_msg}")
                stats.errors.append(error_msg)
                return stats
            
            # Find expired data (older than 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Get collections that need migration
            collections_to_migrate = await self._get_collections_for_migration(temp_db)
            
            for collection_name in collections_to_migrate:
                collection_stats = await self._migrate_collection(
                    temp_db[collection_name],
                    main_db[collection_name],
                    backup_db[collection_name],
                    cutoff_time,
                    collection_name
                )
                
                stats.total_records += collection_stats.total_records
                stats.migrated_records += collection_stats.migrated_records
                stats.failed_records += collection_stats.failed_records
                stats.total_data_size += collection_stats.total_data_size
                stats.errors.extend(collection_stats.errors)
            
            stats.migration_duration = time.time() - start_time
            
            logger.info(f"🔐 [INTERNAL] Migration completed in {stats.migration_duration:.2f}s")
            logger.info(f"📊 Migration stats: {stats.migrated_records}/{stats.total_records} records migrated")
            
            return stats
            
        except Exception as e:
            error_msg = f"error in moving data during migration: {str(e)}"
            logger.error(f"❌ {error_msg}")
            stats.errors.append(error_msg)
            stats.migration_duration = time.time() - start_time
            return stats
    
    async def _get_collections_for_migration(self, temp_db: AsyncIOMotorDatabase) -> List[str]:
        """Get list of collections that need migration"""
        try:
            all_collections = await temp_db.list_collection_names()
            
            # Filter collections that contain user data
            user_data_collections = [
                col for col in all_collections 
                if any(keyword in col.lower() for keyword in [
                    'user', 'profile', 'scan', 'repository', 'analysis', 'evaluation'
                ])
            ]
            
            logger.info(f"🔐 [INTERNAL] Found {len(user_data_collections)} collections for migration: {user_data_collections}")
            return user_data_collections
            
        except Exception as e:
            logger.error(f"❌ error in fetching collections from raseen_temp_user: {str(e)}")
            return []
    
    async def _migrate_collection(
        self,
        source_collection: AsyncIOMotorCollection,
        target_collection: AsyncIOMotorCollection,
        backup_collection: AsyncIOMotorCollection,
        cutoff_time: datetime,
        collection_name: str
    ) -> MigrationStats:
        """Migrate a single collection from temp to main with backup"""
        
        stats = MigrationStats(
            total_records=0,
            migrated_records=0,
            failed_records=0,
            total_data_size=0,
            migration_duration=0.0,
            errors=[]
        )
        
        try:
            logger.info(f"🔐 [INTERNAL] Migrating collection: {collection_name}")
            
            # Find expired documents
            query = {
                "$or": [
                    {"created_at": {"$lt": cutoff_time}},
                    {"last_updated": {"$lt": cutoff_time}},
                    {"timestamp": {"$lt": cutoff_time}}
                ]
            }
            
            expired_docs = await source_collection.find(query).to_list(length=None)
            stats.total_records = len(expired_docs)
            
            if stats.total_records == 0:
                logger.info(f"🔐 [INTERNAL] No expired data found in {collection_name}")
                return stats
            
            logger.info(f"🔐 [INTERNAL] Found {stats.total_records} expired documents in {collection_name}")
            
            # Process documents in batches
            for i in range(0, len(expired_docs), self.migration_batch_size):
                batch = expired_docs[i:i + self.migration_batch_size]
                batch_stats = await self._migrate_batch(
                    batch,
                    source_collection,
                    target_collection,
                    backup_collection,
                    collection_name
                )
                
                stats.migrated_records += batch_stats.migrated_records
                stats.failed_records += batch_stats.failed_records
                stats.total_data_size += batch_stats.total_data_size
                stats.errors.extend(batch_stats.errors)
            
            logger.info(f"🔐 [INTERNAL] Collection {collection_name} migration: {stats.migrated_records}/{stats.total_records} successful")
            
            return stats
            
        except Exception as e:
            error_msg = f"error in moving data from {collection_name}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            stats.errors.append(error_msg)
            return stats
    
    async def _migrate_batch(
        self,
        documents: List[Dict[str, Any]],
        source_collection: AsyncIOMotorCollection,
        target_collection: AsyncIOMotorCollection,
        backup_collection: AsyncIOMotorCollection,
        collection_name: str
    ) -> MigrationStats:
        """Migrate a batch of documents with retry logic"""
        
        stats = MigrationStats(
            total_records=len(documents),
            migrated_records=0,
            failed_records=0,
            total_data_size=0,
            migration_duration=0.0,
            errors=[]
        )
        
        for doc in documents:
            doc_id = doc.get("_id")
            retry_count = 0
            
            while retry_count < self.max_retries:
                try:
                    # Step 1: Insert into main database
                    await target_collection.insert_one(doc)
                    
                    # Step 2: Insert into backup database
                    await backup_collection.insert_one(doc.copy())
                    
                    # Step 3: Remove from temp database
                    await source_collection.delete_one({"_id": doc_id})
                    
                    stats.migrated_records += 1
                    stats.total_data_size += len(str(doc))
                    
                    logger.debug(f"🔐 [INTERNAL] Migrated document {doc_id} from {collection_name}")
                    break
                    
                except Exception as e:
                    retry_count += 1
                    error_msg = f"error in moving data to raseen_main_user (attempt {retry_count}): {str(e)}"
                    logger.warning(f"⚠️ {error_msg}")
                    
                    if retry_count < self.max_retries:
                        # Exponential backoff
                        delay = self.retry_delay_base ** retry_count
                        await asyncio.sleep(delay)
                    else:
                        # Final failure
                        final_error = f"error in moving data to raseen_main_user after {self.max_retries} retries: {str(e)}"
                        logger.error(f"❌ {final_error}")
                        stats.failed_records += 1
                        stats.errors.append(final_error)
        
        return stats
    
    async def migrate_hr_data(self) -> MigrationStats:
        """
        Migrate HR-related data to dedicated HR databases
        """
        logger.info("🔐 [INTERNAL] Starting HR data migration...")
        
        start_time = time.time()
        stats = MigrationStats(
            total_records=0,
            migrated_records=0,
            failed_records=0,
            total_data_size=0,
            migration_duration=0.0,
            errors=[]
        )
        
        try:
            # Get HR databases
            hr_main_db = await get_raseen_main_hr_db()
            hr_backup_db = await get_srie_main_hr_db()
            
            if not all([hr_main_db, hr_backup_db]):
                error_msg = "Failed to connect to HR databases"
                logger.error(f"❌ {error_msg}")
                stats.errors.append(error_msg)
                return stats
            
            # Get temp database to check for HR data
            temp_db = await get_raseen_temp_user_db()
            if not temp_db:
                error_msg = "Failed to connect to temp database for HR data migration"
                logger.error(f"❌ {error_msg}")
                stats.errors.append(error_msg)
                return stats
            
            # Find HR-related data in temp database
            hr_collections = await self._find_hr_data(temp_db)
            
            for collection_name, hr_docs in hr_collections.items():
                if hr_docs:
                    collection_stats = await self._migrate_hr_collection(
                        hr_docs,
                        temp_db[collection_name],
                        hr_main_db[collection_name],
                        hr_backup_db[collection_name],
                        collection_name
                    )
                    
                    stats.total_records += collection_stats.total_records
                    stats.migrated_records += collection_stats.migrated_records
                    stats.failed_records += collection_stats.failed_records
                    stats.total_data_size += collection_stats.total_data_size
                    stats.errors.extend(collection_stats.errors)
            
            stats.migration_duration = time.time() - start_time
            
            logger.info(f"🔐 [INTERNAL] HR data migration completed in {stats.migration_duration:.2f}s")
            logger.info(f"📊 HR migration stats: {stats.migrated_records}/{stats.total_records} records migrated")
            
            return stats
            
        except Exception as e:
            error_msg = f"error in moving HR data: {str(e)}"
            logger.error(f"❌ {error_msg}")
            stats.errors.append(error_msg)
            stats.migration_duration = time.time() - start_time
            return stats
    
    async def _find_hr_data(self, temp_db: AsyncIOMotorDatabase) -> Dict[str, List[Dict[str, Any]]]:
        """Find HR-related data in temp database"""
        hr_data = {}
        
        try:
            collections = await temp_db.list_collection_names()
            
            for collection_name in collections:
                collection = temp_db[collection_name]
                
                # Look for HR-related documents
                hr_query = {
                    "$or": [
                        {"user_type": "hr"},
                        {"is_hr_data": True},
                        {"data_category": "hr"},
                        {"collection_type": "hr"}
                    ]
                }
                
                hr_docs = await collection.find(hr_query).to_list(length=None)
                if hr_docs:
                    hr_data[collection_name] = hr_docs
                    logger.info(f"🔐 [INTERNAL] Found {len(hr_docs)} HR documents in {collection_name}")
            
            return hr_data
            
        except Exception as e:
            logger.error(f"❌ error in fetching HR data from raseen_temp_user: {str(e)}")
            return {}
    
    async def _migrate_hr_collection(
        self,
        hr_docs: List[Dict[str, Any]],
        source_collection: AsyncIOMotorCollection,
        hr_main_collection: AsyncIOMotorCollection,
        hr_backup_collection: AsyncIOMotorCollection,
        collection_name: str
    ) -> MigrationStats:
        """Migrate HR data to dedicated HR databases"""
        
        stats = MigrationStats(
            total_records=len(hr_docs),
            migrated_records=0,
            failed_records=0,
            total_data_size=0,
            migration_duration=0.0,
            errors=[]
        )
        
        logger.info(f"🔐 [INTERNAL] Migrating {len(hr_docs)} HR documents from {collection_name}")
        
        for doc in hr_docs:
            doc_id = doc.get("_id")
            retry_count = 0
            
            while retry_count < self.max_retries:
                try:
                    # Step 1: Insert into HR main database
                    await hr_main_collection.insert_one(doc)
                    
                    # Step 2: Insert into HR backup database
                    await hr_backup_collection.insert_one(doc.copy())
                    
                    # Step 3: Remove from temp database
                    await source_collection.delete_one({"_id": doc_id})
                    
                    stats.migrated_records += 1
                    stats.total_data_size += len(str(doc))
                    
                    logger.debug(f"🔐 [INTERNAL] Migrated HR document {doc_id} from {collection_name}")
                    break
                    
                except Exception as e:
                    retry_count += 1
                    error_msg = f"error in moving data to raseen_main_hr (attempt {retry_count}): {str(e)}"
                    logger.warning(f"⚠️ {error_msg}")
                    
                    if retry_count < self.max_retries:
                        delay = self.retry_delay_base ** retry_count
                        await asyncio.sleep(delay)
                    else:
                        final_error = f"error in moving data to raseen_main_hr after {self.max_retries} retries: {str(e)}"
                        logger.error(f"❌ {final_error}")
                        stats.failed_records += 1
                        stats.errors.append(final_error)
        
        return stats
    
    async def cleanup_migrated_data(self) -> Dict[str, int]:
        """
        Clean up successfully migrated data from temp database
        """
        logger.info("🔐 [INTERNAL] Starting cleanup of migrated data...")
        
        cleanup_stats = {
            "collections_cleaned": 0,
            "documents_removed": 0,
            "errors": 0
        }
        
        try:
            temp_db = await get_raseen_temp_user_db()
            if not temp_db:
                logger.error("❌ Failed to connect to temp database for cleanup")
                cleanup_stats["errors"] += 1
                return cleanup_stats
            
            # Get all collections in temp database
            collections = await temp_db.list_collection_names()
            
            for collection_name in collections:
                try:
                    collection = temp_db[collection_name]
                    
                    # Find documents that should have been migrated (older than 24 hours)
                    cutoff_time = datetime.utcnow() - timedelta(hours=24, minutes=30)  # Add 30 min buffer
                    
                    query = {
                        "$or": [
                            {"created_at": {"$lt": cutoff_time}},
                            {"last_updated": {"$lt": cutoff_time}},
                            {"timestamp": {"$lt": cutoff_time}}
                        ]
                    }
                    
                    # Check if these documents exist in main database
                    # For safety, we'll only clean up documents that are definitely migrated
                    docs_to_check = await collection.find(query).to_list(length=100)  # Limit for safety
                    
                    verified_migrated = []
                    main_db = await get_raseen_main_user_db()
                    
                    if main_db and docs_to_check:
                        main_collection = main_db[collection_name]
                        
                        for doc in docs_to_check:
                            # Check if document exists in main database
                            exists_in_main = await main_collection.find_one({"_id": doc["_id"]})
                            if exists_in_main:
                                verified_migrated.append(doc["_id"])
                    
                    # Remove verified migrated documents
                    if verified_migrated:
                        delete_result = await collection.delete_many({"_id": {"$in": verified_migrated}})
                        cleanup_stats["documents_removed"] += delete_result.deleted_count
                        logger.info(f"🔐 [INTERNAL] Cleaned up {delete_result.deleted_count} documents from {collection_name}")
                    
                    cleanup_stats["collections_cleaned"] += 1
                    
                except Exception as e:
                    logger.error(f"❌ error in cleaning up {collection_name}: {str(e)}")
                    cleanup_stats["errors"] += 1
            
            logger.info(f"🔐 [INTERNAL] Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"❌ error during cleanup process: {str(e)}")
            cleanup_stats["errors"] += 1
            return cleanup_stats
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status and statistics"""
        try:
            temp_db = await get_raseen_temp_user_db()
            main_db = await get_raseen_main_user_db()
            backup_db = await get_srie_main_user_db()
            
            status = {
                "timestamp": datetime.utcnow(),
                "databases_connected": {
                    "temp": temp_db is not None,
                    "main": main_db is not None,
                    "backup": backup_db is not None
                },
                "pending_migrations": {},
                "total_pending_records": 0
            }
            
            if temp_db:
                # Check for data that needs migration
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                collections = await temp_db.list_collection_names()
                
                for collection_name in collections:
                    collection = temp_db[collection_name]
                    
                    query = {
                        "$or": [
                            {"created_at": {"$lt": cutoff_time}},
                            {"last_updated": {"$lt": cutoff_time}},
                            {"timestamp": {"$lt": cutoff_time}}
                        ]
                    }
                    
                    pending_count = await collection.count_documents(query)
                    if pending_count > 0:
                        status["pending_migrations"][collection_name] = pending_count
                        status["total_pending_records"] += pending_count
            
            return status
            
        except Exception as e:
            logger.error(f"❌ error getting migration status: {str(e)}")
            return {
                "timestamp": datetime.utcnow(),
                "error": str(e),
                "databases_connected": {
                    "temp": False,
                    "main": False,
                    "backup": False
                }
            }

# Global service instance
data_migration_service = DataMigrationService()

# Convenience functions
async def run_daily_migration() -> MigrationStats:
    """Run the daily 24-hour data migration"""
    return await data_migration_service.migrate_expired_data()

async def run_hr_migration() -> MigrationStats:
    """Run HR data migration"""
    return await data_migration_service.migrate_hr_data()

async def cleanup_temp_data() -> Dict[str, int]:
    """Clean up migrated data from temp database"""
    return await data_migration_service.cleanup_migrated_data()

async def get_migration_status() -> Dict[str, Any]:
    """Get current migration status"""
    return await data_migration_service.get_migration_status()