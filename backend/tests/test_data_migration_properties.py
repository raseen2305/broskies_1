"""
Property-based tests for data migration and lifecycle management
Tests correctness properties for the database restructuring system
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
import logging
from bson import ObjectId

from app.services.data_migration_service import DataMigrationService, MigrationStats
from app.db_connection_multi import (
    multi_db_manager,
    get_raseen_temp_user_db,
    get_raseen_main_user_db,
    get_srie_main_user_db,
    get_raseen_main_hr_db,
    get_srie_main_hr_db
)

logger = logging.getLogger(__name__)

# Test data generators
@composite
def user_document(draw):
    """Generate a realistic user document for testing"""
    user_id = draw(st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    # Generate timestamp that's older than 24 hours for migration testing
    base_time = datetime.utcnow() - timedelta(hours=25)  # 25 hours ago
    time_offset = draw(st.integers(min_value=0, max_value=3600))  # Up to 1 hour variation
    created_at = base_time - timedelta(seconds=time_offset)
    
    return {
        "_id": ObjectId(),
        "user_id": f"internal_{user_id}",
        "github_username": draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "email": f"{user_id}@example.com",
        "created_at": created_at,
        "last_updated": created_at,
        "scan_data": {
            "repositories": draw(st.lists(st.text(min_size=5, max_size=30), min_size=0, max_size=10)),
            "total_commits": draw(st.integers(min_value=0, max_value=1000)),
            "languages": draw(st.dictionaries(st.text(min_size=2, max_size=15), st.integers(min_value=1, max_value=10000), min_size=0, max_size=5))
        },
        "metadata": {
            "storage_location": "RASEEN_TEMP",
            "backup_status": "pending"
        }
    }

@composite
def hr_document(draw):
    """Generate an HR-related document for testing"""
    user_id = draw(st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    return {
        "_id": ObjectId(),
        "user_id": f"internal_{user_id}",
        "user_type": "hr",
        "is_hr_data": True,
        "data_category": "hr",
        "hr_profile": {
            "company": draw(st.text(min_size=5, max_size=30)),
            "position": draw(st.text(min_size=5, max_size=30)),
            "department": draw(st.text(min_size=3, max_size=20))
        },
        "created_at": datetime.utcnow() - timedelta(hours=25),
        "timestamp": datetime.utcnow() - timedelta(hours=25)
    }

@composite
def migration_batch(draw):
    """Generate a batch of documents for migration testing"""
    batch_size = draw(st.integers(min_value=1, max_value=20))
    return [draw(user_document()) for _ in range(batch_size)]

class TestDataMigrationProperties:
    """Property-based tests for data migration service"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment"""
        self.migration_service = DataMigrationService()
        self.test_collections = []
    
    async def cleanup_test_data(self):
        """Clean up test data after tests"""
        try:
            temp_db = await get_raseen_temp_user_db()
            main_db = await get_raseen_main_user_db()
            backup_db = await get_srie_main_user_db()
            
            for collection_name in self.test_collections:
                if temp_db:
                    await temp_db[collection_name].delete_many({"_test_data": True})
                if main_db:
                    await main_db[collection_name].delete_many({"_test_data": True})
                if backup_db:
                    await backup_db[collection_name].delete_many({"_test_data": True})
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    @given(documents=migration_batch())
    @settings(max_examples=100, deadline=30000)  # 30 second timeout
    @pytest.mark.asyncio
    async def test_data_migration_and_backup_consistency(self, documents):
        """
        **Feature: database-restructuring, Property 3: Data Migration and Backup Consistency**
        **Validates: Requirements 1.4, 1.5, 3.1, 3.2, 3.4**
        
        For any data that has been in temporary storage for 24 hours, migrating it should 
        result in the data appearing in both raseen_main_user and srie_main_user databases 
        while being removed from raseen_temp_user
        """
        assume(len(documents) > 0)
        
        # Mark documents as test data
        for doc in documents:
            doc["_test_data"] = True
        
        collection_name = f"test_migration_{ObjectId()}"
        self.test_collections.append(collection_name)
        
        try:
            # Get database connections
            temp_db = await get_raseen_temp_user_db()
            main_db = await get_raseen_main_user_db()
            backup_db = await get_srie_main_user_db()
            
            assume(temp_db is not None and main_db is not None and backup_db is not None)
            
            # Insert test documents into temp database
            temp_collection = temp_db[collection_name]
            await temp_collection.insert_many(documents)
            
            # Verify documents are in temp database
            temp_count_before = await temp_collection.count_documents({"_test_data": True})
            assert temp_count_before == len(documents), "Documents not properly inserted into temp database"
            
            # Run migration for this specific collection
            main_collection = main_db[collection_name]
            backup_collection = backup_db[collection_name]
            
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            migration_stats = await self.migration_service._migrate_collection(
                temp_collection,
                main_collection,
                backup_collection,
                cutoff_time,
                collection_name
            )
            
            # Property verification: Data should appear in both main and backup databases
            main_count = await main_collection.count_documents({"_test_data": True})
            backup_count = await backup_collection.count_documents({"_test_data": True})
            temp_count_after = await temp_collection.count_documents({"_test_data": True})
            
            # Verify migration consistency
            expected_migrated = len([doc for doc in documents if doc.get("created_at", datetime.utcnow()) < cutoff_time])
            
            assert main_count == expected_migrated, f"Main database should have {expected_migrated} documents, found {main_count}"
            assert backup_count == expected_migrated, f"Backup database should have {expected_migrated} documents, found {backup_count}"
            assert temp_count_after == (len(documents) - expected_migrated), f"Temp database should have {len(documents) - expected_migrated} documents remaining, found {temp_count_after}"
            
            # Verify data integrity: Documents in main and backup should be identical
            main_docs = await main_collection.find({"_test_data": True}).to_list(length=None)
            backup_docs = await backup_collection.find({"_test_data": True}).to_list(length=None)
            
            # Sort by _id for comparison
            main_docs.sort(key=lambda x: str(x["_id"]))
            backup_docs.sort(key=lambda x: str(x["_id"]))
            
            assert len(main_docs) == len(backup_docs), "Main and backup should have same number of documents"
            
            for main_doc, backup_doc in zip(main_docs, backup_docs):
                # Compare all fields except potentially different timestamps
                for key in main_doc:
                    if key not in ["_id"]:  # _id might be different due to insertion
                        assert main_doc[key] == backup_doc[key], f"Field {key} differs between main and backup"
            
            # Verify migration statistics
            assert migration_stats.migrated_records == expected_migrated, f"Migration stats should show {expected_migrated} migrated records"
            assert migration_stats.failed_records == 0, "No records should fail migration in normal conditions"
            
        finally:
            await self.cleanup_test_data()
    
    @given(hr_docs=st.lists(hr_document(), min_size=1, max_size=10))
    @settings(max_examples=50, deadline=20000)
    @pytest.mark.asyncio
    async def test_hr_data_routing_and_backup(self, hr_docs):
        """
        **Feature: database-restructuring, Property 4: HR Data Routing and Backup**
        **Validates: Requirements 3.3**
        
        For any HR-related data, the system should store it in raseen_main_hr and 
        simultaneously backup to srie_main_hr
        """
        assume(len(hr_docs) > 0)
        
        # Mark documents as test data
        for doc in hr_docs:
            doc["_test_data"] = True
        
        collection_name = f"test_hr_migration_{ObjectId()}"
        self.test_collections.append(collection_name)
        
        try:
            # Get database connections
            temp_db = await get_raseen_temp_user_db()
            hr_main_db = await get_raseen_main_hr_db()
            hr_backup_db = await get_srie_main_hr_db()
            
            assume(temp_db is not None and hr_main_db is not None and hr_backup_db is not None)
            
            # Insert HR documents into temp database
            temp_collection = temp_db[collection_name]
            await temp_collection.insert_many(hr_docs)
            
            # Run HR migration
            hr_main_collection = hr_main_db[collection_name]
            hr_backup_collection = hr_backup_db[collection_name]
            
            migration_stats = await self.migration_service._migrate_hr_collection(
                hr_docs,
                temp_collection,
                hr_main_collection,
                hr_backup_collection,
                collection_name
            )
            
            # Property verification: HR data should appear in both HR databases
            hr_main_count = await hr_main_collection.count_documents({"_test_data": True})
            hr_backup_count = await hr_backup_collection.count_documents({"_test_data": True})
            temp_count_after = await temp_collection.count_documents({"_test_data": True})
            
            assert hr_main_count == len(hr_docs), f"HR main database should have {len(hr_docs)} documents, found {hr_main_count}"
            assert hr_backup_count == len(hr_docs), f"HR backup database should have {len(hr_docs)} documents, found {hr_backup_count}"
            assert temp_count_after == 0, f"Temp database should be empty after HR migration, found {temp_count_after}"
            
            # Verify data integrity between HR main and backup
            hr_main_docs = await hr_main_collection.find({"_test_data": True}).to_list(length=None)
            hr_backup_docs = await hr_backup_collection.find({"_test_data": True}).to_list(length=None)
            
            # Sort by user_id for comparison
            hr_main_docs.sort(key=lambda x: x["user_id"])
            hr_backup_docs.sort(key=lambda x: x["user_id"])
            
            for main_doc, backup_doc in zip(hr_main_docs, hr_backup_docs):
                # Verify HR-specific fields are preserved
                assert main_doc["user_type"] == "hr", "HR documents should maintain user_type"
                assert main_doc["is_hr_data"] == True, "HR documents should maintain is_hr_data flag"
                assert main_doc["data_category"] == "hr", "HR documents should maintain data_category"
                
                # Verify data consistency between main and backup
                for key in main_doc:
                    if key != "_id":  # _id might differ due to separate insertions
                        assert main_doc[key] == backup_doc[key], f"HR field {key} differs between main and backup"
            
            # Verify migration statistics
            assert migration_stats.migrated_records == len(hr_docs), "All HR documents should be migrated"
            assert migration_stats.failed_records == 0, "No HR records should fail migration"
            
        finally:
            await self.cleanup_test_data()
    
    @given(documents=migration_batch())
    @settings(max_examples=50, deadline=20000)
    @pytest.mark.asyncio
    async def test_migration_preserves_data_integrity(self, documents):
        """
        Additional property test: Migration should preserve all document fields and structure
        """
        assume(len(documents) > 0)
        
        # Mark documents as test data
        for doc in documents:
            doc["_test_data"] = True
        
        collection_name = f"test_integrity_{ObjectId()}"
        self.test_collections.append(collection_name)
        
        try:
            temp_db = await get_raseen_temp_user_db()
            main_db = await get_raseen_main_user_db()
            backup_db = await get_srie_main_user_db()
            
            assume(temp_db is not None and main_db is not None and backup_db is not None)
            
            # Store original documents for comparison
            original_docs = [doc.copy() for doc in documents]
            
            # Insert and migrate
            temp_collection = temp_db[collection_name]
            await temp_collection.insert_many(documents)
            
            main_collection = main_db[collection_name]
            backup_collection = backup_db[collection_name]
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            await self.migration_service._migrate_collection(
                temp_collection,
                main_collection,
                backup_collection,
                cutoff_time,
                collection_name
            )
            
            # Verify data integrity
            migrated_docs = await main_collection.find({"_test_data": True}).to_list(length=None)
            
            # Check that all expected fields are preserved
            for original_doc in original_docs:
                if original_doc.get("created_at", datetime.utcnow()) < cutoff_time:
                    # Find corresponding migrated document
                    migrated_doc = next(
                        (doc for doc in migrated_docs if doc["user_id"] == original_doc["user_id"]),
                        None
                    )
                    
                    assert migrated_doc is not None, f"Document {original_doc['user_id']} not found after migration"
                    
                    # Verify all original fields are preserved
                    for key, value in original_doc.items():
                        if key != "_id":  # _id might change during migration
                            assert key in migrated_doc, f"Field {key} missing after migration"
                            assert migrated_doc[key] == value, f"Field {key} value changed during migration"
            
        finally:
            await self.cleanup_test_data()

# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])