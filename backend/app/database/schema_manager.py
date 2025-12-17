"""
Database schema manager for comprehensive GitHub integration.
Handles database schema creation, indexing, and migrations.
"""

import logging
from typing import Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SchemaManager:
    """Manages database schemas, indexes, and migrations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        
    async def create_all_indexes(self) -> None:
        """Create all indexes for comprehensive GitHub integration"""
        try:
            await self._create_user_indexes()
            await self._create_repository_indexes()
            await self._create_scan_indexes()
            await self._create_comprehensive_indexes()
            await self._create_cache_indexes()
            
            logger.info("All database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
            raise
    
    async def _create_user_indexes(self) -> None:
        """Create indexes for user-related collections"""
        
        # Users collection
        user_indexes = [
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("github_username", ASCENDING)]),
            IndexModel([("user_type", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("last_scan", DESCENDING)]),
            IndexModel([("is_active", ASCENDING)])
        ]
        await self.db.users.create_indexes(user_indexes)
        
        # HR Users collection
        hr_user_indexes = [
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("company", ASCENDING)]),
            IndexModel([("access_level", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)])
        ]
        await self.db.hr_users.create_indexes(hr_user_indexes)
        
        # GitHub User Profiles collection
        github_profile_indexes = [
            IndexModel([("user_id", ASCENDING)], unique=True),
            IndexModel([("login", ASCENDING)], unique=True),
            IndexModel([("github_id", ASCENDING)], unique=True),
            IndexModel([("last_updated", DESCENDING)]),
            IndexModel([("data_freshness", DESCENDING)]),
            IndexModel([("public_repos", DESCENDING)]),
            IndexModel([("followers", DESCENDING)])
        ]
        await self.db.github_user_profiles.create_indexes(github_profile_indexes)
        
        logger.info("User indexes created successfully")
    
    async def _create_repository_indexes(self) -> None:
        """Create indexes for repository-related collections"""
        
        # Basic Repositories collection
        repo_indexes = [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("github_id", ASCENDING)], unique=True),
            IndexModel([("full_name", ASCENDING)], unique=True),
            IndexModel([("name", ASCENDING)]),
            IndexModel([("language", ASCENDING)]),
            IndexModel([("stars", DESCENDING)]),
            IndexModel([("forks", DESCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("updated_at", DESCENDING)]),
            IndexModel([("is_private", ASCENDING)]),
            IndexModel([("is_fork", ASCENDING)]),
            IndexModel([("topics", ASCENDING)]),
            IndexModel([("user_id", ASCENDING), ("name", ASCENDING)], unique=True)
        ]
        await self.db.repositories.create_indexes(repo_indexes)
        
        # Detailed Repositories collection
        detailed_repo_indexes = [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("github_id", ASCENDING)], unique=True),
            IndexModel([("full_name", ASCENDING)]),
            IndexModel([("language", ASCENDING)]),
            IndexModel([("stars", DESCENDING)]),
            IndexModel([("last_analyzed", DESCENDING)]),
            IndexModel([("analysis_version", ASCENDING)]),
            IndexModel([("acid_scores.overall", DESCENDING)]),
            IndexModel([("code_analysis.total_lines", DESCENDING)]),
            IndexModel([("code_analysis.complexity_score", DESCENDING)]),
            IndexModel([("total_commits", DESCENDING)]),
            IndexModel([("is_private", ASCENDING), ("user_id", ASCENDING)])
        ]
        await self.db.detailed_repositories.create_indexes(detailed_repo_indexes)
        
        # Repository Evaluations collection
        evaluation_indexes = [
            IndexModel([("repo_id", ASCENDING)]),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("acid_score.overall", DESCENDING)]),
            IndexModel([("quality_metrics.maintainability", DESCENDING)]),
            IndexModel([("complexity_score", DESCENDING)]),
            IndexModel([("user_id", ASCENDING), ("repo_id", ASCENDING)])
        ]
        await self.db.evaluations.create_indexes(evaluation_indexes)
        
        logger.info("Repository indexes created successfully")
    
    async def _create_scan_indexes(self) -> None:
        """Create indexes for scanning-related collections"""
        
        # Scan Progress collection
        scan_progress_indexes = [
            IndexModel([("scan_id", ASCENDING)], unique=True),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("current_phase", ASCENDING)]),
            IndexModel([("start_time", DESCENDING)]),
            IndexModel([("last_update", DESCENDING)]),
            IndexModel([("progress_percentage", DESCENDING)])
        ]
        await self.db.scan_progress.create_indexes(scan_progress_indexes)
        
        # Comprehensive Scan Results collection
        scan_result_indexes = [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("scan_metadata.scan_id", ASCENDING)], unique=True),
            IndexModel([("scan_metadata.scan_type", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("last_updated", DESCENDING)]),
            IndexModel([("overall_acid_score", DESCENDING)]),
            IndexModel([("overall_quality_score", DESCENDING)]),
            IndexModel([("developer_level", ASCENDING)]),
            IndexModel([("data_version", ASCENDING)]),
            IndexModel([("scan_metadata.successful_repositories", DESCENDING)])
        ]
        await self.db.comprehensive_scan_results.create_indexes(scan_result_indexes)
        
        logger.info("Scan indexes created successfully")
    
    async def _create_comprehensive_indexes(self) -> None:
        """Create indexes for comprehensive data collections"""
        
        # Contribution Calendars collection
        calendar_indexes = [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("github_username", ASCENDING)]),
            IndexModel([("calendar_year", ASCENDING)]),
            IndexModel([("total_contributions", DESCENDING)]),
            IndexModel([("current_streak", DESCENDING)]),
            IndexModel([("longest_streak", DESCENDING)]),
            IndexModel([("last_updated", DESCENDING)]),
            IndexModel([("user_id", ASCENDING), ("calendar_year", ASCENDING)], unique=True)
        ]
        await self.db.contribution_calendars.create_indexes(calendar_indexes)
        
        # Pull Request Analysis collection
        pr_analysis_indexes = [
            IndexModel([("repository_id", ASCENDING)]),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("total_prs", DESCENDING)]),
            IndexModel([("merge_rate", DESCENDING)]),
            IndexModel([("average_review_time", ASCENDING)]),
            IndexModel([("last_updated", DESCENDING)]),
            IndexModel([("repository_id", ASCENDING)], unique=True)
        ]
        await self.db.pull_request_analysis.create_indexes(pr_analysis_indexes)
        
        # Issue Analysis collection
        issue_analysis_indexes = [
            IndexModel([("repository_id", ASCENDING)]),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("total_issues", DESCENDING)]),
            IndexModel([("resolution_rate", DESCENDING)]),
            IndexModel([("average_resolution_time", ASCENDING)]),
            IndexModel([("last_updated", DESCENDING)]),
            IndexModel([("repository_id", ASCENDING)], unique=True)
        ]
        await self.db.issue_analysis.create_indexes(issue_analysis_indexes)
        
        logger.info("Comprehensive data indexes created successfully")
    
    async def _create_cache_indexes(self) -> None:
        """Create indexes for cache management"""
        
        # Cache Metadata collection
        cache_indexes = [
            IndexModel([("cache_key", ASCENDING)], unique=True),
            IndexModel([("cache_type", ASCENDING)]),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("repository_id", ASCENDING)]),
            IndexModel([("expires_at", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("last_accessed", DESCENDING)]),
            IndexModel([("needs_refresh", ASCENDING)]),
            IndexModel([("cache_hit_rate", DESCENDING)])
        ]
        await self.db.cache_metadata.create_indexes(cache_indexes)
        
        logger.info("Cache indexes created successfully")
    
    async def create_text_indexes(self) -> None:
        """Create text search indexes for searchable content"""
        try:
            # Repository text search
            repo_text_indexes = [
                IndexModel([
                    ("name", TEXT),
                    ("description", TEXT),
                    ("topics", TEXT)
                ], name="repository_text_search")
            ]
            await self.db.repositories.create_indexes(repo_text_indexes)
            await self.db.detailed_repositories.create_indexes(repo_text_indexes)
            
            # User profile text search
            user_text_indexes = [
                IndexModel([
                    ("name", TEXT),
                    ("bio", TEXT),
                    ("company", TEXT),
                    ("location", TEXT)
                ], name="user_profile_text_search")
            ]
            await self.db.github_user_profiles.create_indexes(user_text_indexes)
            
            logger.info("Text search indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating text indexes: {e}")
    
    async def create_compound_indexes(self) -> None:
        """Create compound indexes for complex queries"""
        try:
            # User repositories with quality scores
            compound_indexes = [
                IndexModel([
                    ("user_id", ASCENDING),
                    ("acid_scores.overall", DESCENDING),
                    ("stars", DESCENDING)
                ], name="user_repo_quality"),
                
                IndexModel([
                    ("user_id", ASCENDING),
                    ("language", ASCENDING),
                    ("last_analyzed", DESCENDING)
                ], name="user_language_analysis"),
                
                IndexModel([
                    ("is_private", ASCENDING),
                    ("language", ASCENDING),
                    ("stars", DESCENDING)
                ], name="public_repo_language_popularity"),
                
                IndexModel([
                    ("scan_metadata.scan_type", ASCENDING),
                    ("created_at", DESCENDING),
                    ("overall_quality_score", DESCENDING)
                ], name="scan_results_quality")
            ]
            
            await self.db.detailed_repositories.create_indexes(compound_indexes[:3])
            await self.db.comprehensive_scan_results.create_indexes([compound_indexes[3]])
            
            logger.info("Compound indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating compound indexes: {e}")
    
    async def setup_ttl_indexes(self) -> None:
        """Create TTL (Time To Live) indexes for automatic data cleanup"""
        try:
            # Scan progress cleanup (24 hours)
            ttl_indexes = [
                IndexModel([("last_update", ASCENDING)], 
                          expireAfterSeconds=86400,  # 24 hours
                          name="scan_progress_ttl")
            ]
            await self.db.scan_progress.create_indexes(ttl_indexes)
            
            # Cache metadata cleanup (based on expires_at field)
            cache_ttl_indexes = [
                IndexModel([("expires_at", ASCENDING)], 
                          expireAfterSeconds=0,  # Use expires_at field value
                          name="cache_metadata_ttl")
            ]
            await self.db.cache_metadata.create_indexes(cache_ttl_indexes)
            
            logger.info("TTL indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating TTL indexes: {e}")
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about all collections"""
        stats = {}
        
        collections = [
            "users", "hr_users", "github_user_profiles",
            "repositories", "detailed_repositories", "evaluations",
            "scan_progress", "comprehensive_scan_results",
            "contribution_calendars", "pull_request_analysis", 
            "issue_analysis", "cache_metadata"
        ]
        
        for collection_name in collections:
            try:
                collection = getattr(self.db, collection_name)
                count = await collection.count_documents({})
                indexes = await collection.list_indexes().to_list(length=None)
                
                stats[collection_name] = {
                    "document_count": count,
                    "index_count": len(indexes),
                    "indexes": [idx.get("name", "unnamed") for idx in indexes]
                }
                
            except Exception as e:
                logger.warning(f"Could not get stats for {collection_name}: {e}")
                stats[collection_name] = {"error": str(e)}
        
        return stats
    
    async def validate_schema(self) -> Dict[str, bool]:
        """Validate that all required indexes exist"""
        validation_results = {}
        
        required_collections = [
            "users", "repositories", "detailed_repositories",
            "comprehensive_scan_results", "contribution_calendars"
        ]
        
        for collection_name in required_collections:
            try:
                collection = getattr(self.db, collection_name)
                indexes = await collection.list_indexes().to_list(length=None)
                
                # Check if collection has at least basic indexes
                has_indexes = len(indexes) > 1  # More than just _id index
                validation_results[collection_name] = has_indexes
                
            except Exception as e:
                logger.error(f"Schema validation failed for {collection_name}: {e}")
                validation_results[collection_name] = False
        
        return validation_results
    
    async def migrate_schema(self, from_version: str, to_version: str) -> bool:
        """Perform schema migration between versions"""
        try:
            logger.info(f"Starting schema migration from {from_version} to {to_version}")
            
            if from_version == "basic" and to_version == "comprehensive_v1":
                await self._migrate_to_comprehensive_v1()
                return True
            
            logger.warning(f"No migration path from {from_version} to {to_version}")
            return False
            
        except Exception as e:
            logger.error(f"Schema migration failed: {e}")
            return False
    
    async def _migrate_to_comprehensive_v1(self) -> None:
        """Migrate from basic schema to comprehensive v1"""
        # Create new collections and indexes
        await self.create_all_indexes()
        await self.create_text_indexes()
        await self.create_compound_indexes()
        await self.setup_ttl_indexes()
        
        # Migrate existing data if needed
        # This would involve transforming existing repository and user data
        # to the new comprehensive format
        
        logger.info("Migration to comprehensive_v1 completed")

# Utility functions for schema management
async def initialize_database_schema(database: AsyncIOMotorDatabase) -> None:
    """Initialize complete database schema with all indexes"""
    schema_manager = SchemaManager(database)
    
    await schema_manager.create_all_indexes()
    await schema_manager.create_text_indexes()
    await schema_manager.create_compound_indexes()
    await schema_manager.setup_ttl_indexes()
    
    # Validate schema
    validation_results = await schema_manager.validate_schema()
    if all(validation_results.values()):
        logger.info("Database schema initialized and validated successfully")
    else:
        logger.warning(f"Schema validation issues: {validation_results}")

async def get_database_health(database: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Get comprehensive database health information"""
    schema_manager = SchemaManager(database)
    
    stats = await schema_manager.get_collection_stats()
    validation = await schema_manager.validate_schema()
    
    return {
        "collection_stats": stats,
        "schema_validation": validation,
        "timestamp": datetime.utcnow().isoformat(),
        "healthy": all(validation.values())
    }