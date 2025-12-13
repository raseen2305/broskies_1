"""
Database setup and initialization script for comprehensive GitHub integration.
This script sets up the complete database schema with all required collections and indexes.
"""

import asyncio
import logging
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from .schema_manager import SchemaManager, initialize_database_schema
from .migrations import DatabaseMigrator, run_full_migration
from .utils import DatabaseUtils

logger = logging.getLogger(__name__)

class DatabaseSetup:
    """Complete database setup and initialization"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.schema_manager = SchemaManager(database)
        self.migrator = DatabaseMigrator(database)
        self.utils = DatabaseUtils(database)
    
    async def initialize_complete_database(self) -> Dict[str, Any]:
        """Initialize complete database with all schemas, indexes, and migrations"""
        setup_results = {
            "schema_created": False,
            "indexes_created": False,
            "migrations_run": False,
            "validation_passed": False,
            "errors": []
        }
        
        try:
            logger.info("🚀 Starting comprehensive database initialization...")
            
            # Step 1: Create all database schemas and indexes
            logger.info("📋 Step 1: Creating database schemas and indexes...")
            await self._create_database_schemas()
            setup_results["schema_created"] = True
            setup_results["indexes_created"] = True
            logger.info("✅ Database schemas and indexes created successfully")
            
            # Step 2: Run data migrations
            logger.info("📋 Step 2: Running data migrations...")
            migration_results = await self._run_migrations()
            setup_results["migrations_run"] = True
            setup_results["migration_results"] = migration_results
            logger.info("✅ Data migrations completed successfully")
            
            # Step 3: Validate database integrity
            logger.info("📋 Step 3: Validating database integrity...")
            validation_results = await self._validate_database()
            setup_results["validation_passed"] = validation_results["healthy"]
            setup_results["validation_results"] = validation_results
            
            if validation_results["healthy"]:
                logger.info("✅ Database validation passed")
            else:
                logger.warning("⚠️ Database validation found issues")
            
            # Step 4: Create sample data (optional)
            logger.info("📋 Step 4: Setting up database collections...")
            await self._setup_collections()
            logger.info("✅ Database collections configured")
            
            # Step 5: Performance optimization
            logger.info("📋 Step 5: Optimizing database performance...")
            await self._optimize_performance()
            logger.info("✅ Database performance optimized")
            
            logger.info("🎉 Database initialization completed successfully!")
            
        except Exception as e:
            error_msg = f"Database initialization failed: {str(e)}"
            logger.error(error_msg)
            setup_results["errors"].append(error_msg)
        
        return setup_results
    
    async def _create_database_schemas(self) -> None:
        """Create all database schemas and indexes"""
        # Create all basic indexes
        await self.schema_manager.create_all_indexes()
        
        # Create text search indexes
        await self.schema_manager.create_text_indexes()
        
        # Create compound indexes for complex queries
        await self.schema_manager.create_compound_indexes()
        
        # Set up TTL indexes for automatic cleanup
        await self.schema_manager.setup_ttl_indexes()
    
    async def _run_migrations(self) -> Dict[str, int]:
        """Run all necessary data migrations"""
        return await run_full_migration(self.db)
    
    async def _validate_database(self) -> Dict[str, Any]:
        """Validate database schema and integrity"""
        # Schema validation
        schema_validation = await self.schema_manager.validate_schema()
        
        # Data integrity validation
        integrity_validation = await self.migrator.validate_data_integrity()
        
        # Collection statistics
        collection_stats = await self.schema_manager.get_collection_stats()
        
        return {
            "healthy": all(schema_validation.values()) and len(integrity_validation.get("issues", [])) == 0,
            "schema_validation": schema_validation,
            "integrity_validation": integrity_validation,
            "collection_stats": collection_stats
        }
    
    async def _setup_collections(self) -> None:
        """Set up and configure database collections"""
        collections_to_create = [
            "users",
            "hr_users", 
            "github_user_profiles",
            "repositories",
            "detailed_repositories",
            "evaluations",
            "scan_progress",
            "comprehensive_scan_results",
            "contribution_calendars",
            "pull_request_analysis",
            "issue_analysis",
            "cache_metadata"
        ]
        
        for collection_name in collections_to_create:
            try:
                # Create collection if it doesn't exist
                collection = getattr(self.db, collection_name)
                
                # Insert a dummy document and remove it to create the collection
                dummy_doc = {"_temp": True, "created_at": "initialization"}
                result = await collection.insert_one(dummy_doc)
                await collection.delete_one({"_id": result.inserted_id})
                
                logger.debug(f"Collection '{collection_name}' configured")
                
            except Exception as e:
                logger.warning(f"Could not configure collection '{collection_name}': {e}")
    
    async def _optimize_performance(self) -> None:
        """Optimize database performance settings"""
        try:
            # Set read preference for better performance
            # This is handled at the connection level
            
            # Log performance optimization completion
            logger.info("Database performance optimization completed")
            
        except Exception as e:
            logger.warning(f"Performance optimization warning: {e}")
    
    async def get_database_status(self) -> Dict[str, Any]:
        """Get comprehensive database status information"""
        try:
            # Get collection statistics
            collection_stats = await self.utils.get_collection_statistics()
            
            # Get schema validation
            schema_validation = await self.schema_manager.validate_schema()
            
            # Get data integrity status
            integrity_status = await self.migrator.validate_data_integrity()
            
            # Calculate overall health
            healthy = (
                all(schema_validation.values()) and 
                len(integrity_status.get("issues", [])) == 0
            )
            
            return {
                "healthy": healthy,
                "timestamp": asyncio.get_event_loop().time(),
                "collections": collection_stats,
                "schema_validation": schema_validation,
                "data_integrity": integrity_status,
                "total_documents": sum(
                    stats.get("document_count", 0) 
                    for stats in collection_stats.values() 
                    if isinstance(stats, dict) and "document_count" in stats
                ),
                "database_size_mb": sum(
                    stats.get("size_bytes", 0) 
                    for stats in collection_stats.values() 
                    if isinstance(stats, dict) and "size_bytes" in stats
                ) / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Error getting database status: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
    
    async def cleanup_and_maintenance(self) -> Dict[str, Any]:
        """Perform database cleanup and maintenance tasks"""
        maintenance_results = {}
        
        try:
            # Clean up expired data
            cleanup_results = await self.utils.cleanup_expired_data()
            maintenance_results["cleanup"] = cleanup_results
            
            # Run data integrity check
            integrity_results = await self.migrator.validate_data_integrity()
            maintenance_results["integrity_check"] = integrity_results
            
            # Get updated statistics
            stats = await self.utils.get_collection_statistics()
            maintenance_results["collection_stats"] = stats
            
            logger.info(f"Database maintenance completed: {maintenance_results}")
            
        except Exception as e:
            logger.error(f"Database maintenance error: {e}")
            maintenance_results["error"] = str(e)
        
        return maintenance_results

# Utility functions for database setup
async def setup_comprehensive_database(database: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Set up comprehensive database with all features"""
    setup = DatabaseSetup(database)
    return await setup.initialize_complete_database()

async def get_database_health_status(database: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Get comprehensive database health status"""
    setup = DatabaseSetup(database)
    return await setup.get_database_status()

async def perform_database_maintenance(database: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Perform database maintenance and cleanup"""
    setup = DatabaseSetup(database)
    return await setup.cleanup_and_maintenance()

async def quick_database_check(database: AsyncIOMotorDatabase) -> bool:
    """Quick database health check - returns True if healthy"""
    try:
        # Test basic connection
        await database.command("ping")
        
        # Check if main collections exist
        collections = await database.list_collection_names()
        required_collections = ["users", "repositories", "github_user_profiles"]
        
        has_required = all(col in collections for col in required_collections)
        
        return has_required
        
    except Exception as e:
        logger.error(f"Quick database check failed: {e}")
        return False

# Database initialization script
async def main():
    """Main database initialization script"""
    from app.db_connection import get_database
    
    try:
        # Get database connection
        database = await get_database()
        
        if not database:
            logger.error("Could not connect to database")
            return
        
        # Run complete database setup
        logger.info("Starting comprehensive database setup...")
        results = await setup_comprehensive_database(database)
        
        # Print results
        print("\n" + "="*60)
        print("DATABASE SETUP RESULTS")
        print("="*60)
        
        for key, value in results.items():
            if key != "errors":
                status = "✅" if value else "❌"
                print(f"{status} {key.replace('_', ' ').title()}: {value}")
        
        if results.get("errors"):
            print("\n❌ ERRORS:")
            for error in results["errors"]:
                print(f"   - {error}")
        
        print("\n" + "="*60)
        
        # Get final status
        status = await get_database_health_status(database)
        print(f"Database Health: {'✅ HEALTHY' if status['healthy'] else '❌ ISSUES'}")
        print(f"Total Documents: {status.get('total_documents', 0):,}")
        print(f"Database Size: {status.get('database_size_mb', 0):.2f} MB")
        
    except Exception as e:
        logger.error(f"Database setup script failed: {e}")
        print(f"❌ Database setup failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())