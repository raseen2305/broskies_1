"""
Ranking system database schema manager.
Handles creation of collections and indexes for regional and university ranking comparisons.
"""

import logging
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING
from datetime import datetime

logger = logging.getLogger(__name__)

class RankingSchemaManager:
    """Manages ranking system database schemas and indexes"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
    
    async def create_all_ranking_indexes(self) -> None:
        """Create all indexes for ranking system collections"""
        try:
            await self._create_user_profiles_indexes()
            await self._create_regional_scores_indexes()
            await self._create_university_scores_indexes()
            
            logger.info("✅ All ranking system indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ Error creating ranking indexes: {e}")
            raise
    
    async def _create_user_profiles_indexes(self) -> None:
        """Create indexes for user_profiles collection"""
        
        user_profile_indexes = [
            # Unique index on user_id to prevent duplicate profiles
            IndexModel([("user_id", ASCENDING)], unique=True, name="user_id_unique"),
            
            # Index on region for fast regional ranking queries
            IndexModel([("region", ASCENDING)], name="region_idx"),
            
            # Index on university_short for fast university ranking queries
            IndexModel([("university_short", ASCENDING)], name="university_short_idx"),
            
            # Index on created_at for sorting and filtering
            IndexModel([("created_at", DESCENDING)], name="created_at_idx"),
            
            # Index on updated_at for tracking profile changes
            IndexModel([("updated_at", DESCENDING)], name="updated_at_idx"),
            
            # Compound index for region-based queries
            IndexModel([("region", ASCENDING), ("created_at", DESCENDING)], 
                      name="region_created_compound"),
            
            # Compound index for university-based queries
            IndexModel([("university_short", ASCENDING), ("created_at", DESCENDING)], 
                      name="university_created_compound")
        ]
        
        await self.db.user_profiles.create_indexes(user_profile_indexes)
        logger.info("✅ user_profiles indexes created")
    
    async def _create_regional_scores_indexes(self) -> None:
        """Create indexes for regional_scores collection"""
        
        regional_scores_indexes = [
            # Unique index on user_id to ensure one entry per user
            IndexModel([("user_id", ASCENDING)], unique=True, name="user_id_unique"),
            
            # Compound index on (region, acid_score DESC) for fast ranking queries
            # This is the most important index for ranking calculations
            IndexModel([("region", ASCENDING), ("acid_score", DESCENDING)], 
                      name="region_score_ranking"),
            
            # Index on region for filtering by region
            IndexModel([("region", ASCENDING)], name="region_idx"),
            
            # Index on acid_score for score-based queries
            IndexModel([("acid_score", DESCENDING)], name="acid_score_idx"),
            
            # Index on last_updated for tracking data freshness
            IndexModel([("last_updated", DESCENDING)], name="last_updated_idx"),
            
            # Index on rank_position for leaderboard queries
            IndexModel([("rank_position", ASCENDING)], name="rank_position_idx"),
            
            # Compound index for region-based leaderboards
            IndexModel([("region", ASCENDING), ("rank_position", ASCENDING)], 
                      name="region_rank_leaderboard"),
            
            # Compound index for percentile queries
            IndexModel([("region", ASCENDING), ("percentile_score", DESCENDING)], 
                      name="region_percentile")
        ]
        
        await self.db.regional_scores.create_indexes(regional_scores_indexes)
        logger.info("✅ regional_scores indexes created")
    
    async def _create_university_scores_indexes(self) -> None:
        """Create indexes for university_scores collection"""
        
        university_scores_indexes = [
            # Unique index on user_id to ensure one entry per user
            IndexModel([("user_id", ASCENDING)], unique=True, name="user_id_unique"),
            
            # Compound index on (university_short, acid_score DESC) for fast ranking queries
            # This is the most important index for ranking calculations
            IndexModel([("university_short", ASCENDING), ("acid_score", DESCENDING)], 
                      name="university_score_ranking"),
            
            # Index on university_short for filtering by university
            IndexModel([("university_short", ASCENDING)], name="university_short_idx"),
            
            # Index on acid_score for score-based queries
            IndexModel([("acid_score", DESCENDING)], name="acid_score_idx"),
            
            # Index on last_updated for tracking data freshness
            IndexModel([("last_updated", DESCENDING)], name="last_updated_idx"),
            
            # Index on rank_position for leaderboard queries
            IndexModel([("rank_position", ASCENDING)], name="rank_position_idx"),
            
            # Compound index for university-based leaderboards
            IndexModel([("university_short", ASCENDING), ("rank_position", ASCENDING)], 
                      name="university_rank_leaderboard"),
            
            # Compound index for percentile queries
            IndexModel([("university_short", ASCENDING), ("percentile_score", DESCENDING)], 
                      name="university_percentile")
        ]
        
        await self.db.university_scores.create_indexes(university_scores_indexes)
        logger.info("✅ university_scores indexes created")
    
    async def get_ranking_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about ranking collections"""
        stats = {}
        
        collections = ["user_profiles", "regional_scores", "university_scores"]
        
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
    
    async def validate_ranking_schema(self) -> Dict[str, bool]:
        """Validate that all required ranking indexes exist"""
        validation_results = {}
        
        required_collections = ["user_profiles", "regional_scores", "university_scores"]
        
        for collection_name in required_collections:
            try:
                collection = getattr(self.db, collection_name)
                indexes = await collection.list_indexes().to_list(length=None)
                
                # Check if collection has required indexes
                has_indexes = len(indexes) > 1  # More than just _id index
                validation_results[collection_name] = has_indexes
                
                if has_indexes:
                    logger.info(f"✅ {collection_name}: {len(indexes)} indexes found")
                else:
                    logger.warning(f"⚠️ {collection_name}: Missing indexes")
                
            except Exception as e:
                logger.error(f"❌ Schema validation failed for {collection_name}: {e}")
                validation_results[collection_name] = False
        
        return validation_results
    
    async def create_sample_ranking_data(self) -> bool:
        """Create sample data to demonstrate the ranking system"""
        try:
            logger.info("📝 Creating sample ranking data...")
            
            # Sample user profile
            sample_profile = {
                "user_id": "sample_ranking_user_001",
                "full_name": "Sample Developer",
                "university": "Massachusetts Institute of Technology",
                "university_short": "mit",
                "nationality": "US",
                "state": "Massachusetts",
                "district": "Cambridge",
                "region": "US-Massachusetts",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Sample regional score
            sample_regional_score = {
                "user_id": "sample_ranking_user_001",
                "region": "US-Massachusetts",
                "acid_score": 85.5,
                "rank_position": 1,
                "total_users_in_region": 1,
                "percentile_score": 100.0,
                "last_updated": datetime.utcnow()
            }
            
            # Sample university score
            sample_university_score = {
                "user_id": "sample_ranking_user_001",
                "university_short": "mit",
                "acid_score": 85.5,
                "rank_position": 1,
                "total_users_in_university": 1,
                "percentile_score": 100.0,
                "last_updated": datetime.utcnow()
            }
            
            # Insert sample data (use upsert to avoid duplicates)
            await self.db.user_profiles.update_one(
                {"user_id": sample_profile["user_id"]},
                {"$set": sample_profile},
                upsert=True
            )
            
            await self.db.regional_scores.update_one(
                {"user_id": sample_regional_score["user_id"]},
                {"$set": sample_regional_score},
                upsert=True
            )
            
            await self.db.university_scores.update_one(
                {"user_id": sample_university_score["user_id"]},
                {"$set": sample_university_score},
                upsert=True
            )
            
            logger.info("✅ Sample ranking data created successfully")
            logger.info("   • Sample user: Sample Developer")
            logger.info("   • University: MIT")
            logger.info("   • Region: US-Massachusetts")
            logger.info("   • ACID Score: 85.5")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating sample data: {e}")
            return False


# Utility functions for ranking schema management
async def initialize_ranking_schema(database: AsyncIOMotorDatabase) -> None:
    """Initialize ranking system database schema with all indexes"""
    schema_manager = RankingSchemaManager(database)
    
    await schema_manager.create_all_ranking_indexes()
    
    # Validate schema
    validation_results = await schema_manager.validate_ranking_schema()
    if all(validation_results.values()):
        logger.info("✅ Ranking database schema initialized and validated successfully")
    else:
        logger.warning(f"⚠️ Schema validation issues: {validation_results}")


async def get_ranking_database_health(database: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Get comprehensive ranking database health information"""
    schema_manager = RankingSchemaManager(database)
    
    stats = await schema_manager.get_ranking_collection_stats()
    validation = await schema_manager.validate_ranking_schema()
    
    return {
        "collection_stats": stats,
        "schema_validation": validation,
        "timestamp": datetime.utcnow().isoformat(),
        "healthy": all(validation.values())
    }
