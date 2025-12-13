#!/usr/bin/env python3
"""
Script to add database indexes for efficient ranking operations.
This script creates indexes on key fields used for joining and grouping in the unified ranking system.
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.database.collections import Collections
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_ranking_indexes():
    """
    Create database indexes for efficient ranking operations
    """
    try:
        # Connect to database
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        
        logger.info("Creating indexes for unified ranking system...")
        
        # Indexes for internal_users collection
        logger.info("Creating indexes on internal_users collection...")
        
        # Index on username for joining
        await db[Collections.INTERNAL_USERS].create_index("username")
        logger.info("✓ Created index on internal_users.username")
        
        # Index on user_id for lookups
        await db[Collections.INTERNAL_USERS].create_index("user_id")
        logger.info("✓ Created index on internal_users.user_id")
        
        # Index on overall_score for ranking calculations
        await db[Collections.INTERNAL_USERS].create_index("overall_score")
        logger.info("✓ Created index on internal_users.overall_score")
        
        # Compound index for score filtering
        await db[Collections.INTERNAL_USERS].create_index([
            ("overall_score", -1),  # Descending for ranking
            ("updated_at", -1)      # Most recent first
        ])
        logger.info("✓ Created compound index on internal_users (overall_score, updated_at)")
        
        # Indexes for internal_users_profile collection
        logger.info("Creating indexes on internal_users_profile collection...")
        
        # Index on github_username for joining
        await db[Collections.INTERNAL_USERS_PROFILE].create_index("github_username")
        logger.info("✓ Created index on internal_users_profile.github_username")
        
        # Index on university_short for university grouping
        await db[Collections.INTERNAL_USERS_PROFILE].create_index("university_short")
        logger.info("✓ Created index on internal_users_profile.university_short")
        
        # Index on district for regional grouping
        await db[Collections.INTERNAL_USERS_PROFILE].create_index("district")
        logger.info("✓ Created index on internal_users_profile.district")
        
        # Index on profile_completed for filtering
        await db[Collections.INTERNAL_USERS_PROFILE].create_index("profile_completed")
        logger.info("✓ Created index on internal_users_profile.profile_completed")
        
        # Compound index for regional grouping
        await db[Collections.INTERNAL_USERS_PROFILE].create_index([
            ("district", 1),
            ("state", 1),
            ("profile_completed", 1)
        ])
        logger.info("✓ Created compound index on internal_users_profile (district, state, profile_completed)")
        
        # Compound index for university grouping
        await db[Collections.INTERNAL_USERS_PROFILE].create_index([
            ("university_short", 1),
            ("profile_completed", 1)
        ])
        logger.info("✓ Created compound index on internal_users_profile (university_short, profile_completed)")
        
        # Indexes for regional_rankings collection
        logger.info("Creating indexes on regional_rankings collection...")
        
        # Index on user_id for lookups
        await db[Collections.REGIONAL_RANKINGS].create_index("user_id", unique=True)
        logger.info("✓ Created unique index on regional_rankings.user_id")
        
        # Index on github_username for external lookups
        await db[Collections.REGIONAL_RANKINGS].create_index("github_username")
        logger.info("✓ Created index on regional_rankings.github_username")
        
        # Index on district for leaderboards
        await db[Collections.REGIONAL_RANKINGS].create_index("district")
        logger.info("✓ Created index on regional_rankings.district")
        
        # Compound index for regional leaderboards
        await db[Collections.REGIONAL_RANKINGS].create_index([
            ("district", 1),
            ("rank", 1)
        ])
        logger.info("✓ Created compound index on regional_rankings (district, rank)")
        
        # Compound index for regional score sorting
        await db[Collections.REGIONAL_RANKINGS].create_index([
            ("district", 1),
            ("overall_score", -1)
        ])
        logger.info("✓ Created compound index on regional_rankings (district, overall_score)")
        
        # Indexes for university_rankings collection
        logger.info("Creating indexes on university_rankings collection...")
        
        # Index on user_id for lookups
        await db[Collections.UNIVERSITY_RANKINGS].create_index("user_id", unique=True)
        logger.info("✓ Created unique index on university_rankings.user_id")
        
        # Index on github_username for external lookups
        await db[Collections.UNIVERSITY_RANKINGS].create_index("github_username")
        logger.info("✓ Created index on university_rankings.github_username")
        
        # Index on university_short for leaderboards
        await db[Collections.UNIVERSITY_RANKINGS].create_index("university_short")
        logger.info("✓ Created index on university_rankings.university_short")
        
        # Compound index for university leaderboards
        await db[Collections.UNIVERSITY_RANKINGS].create_index([
            ("university_short", 1),
            ("rank", 1)
        ])
        logger.info("✓ Created compound index on university_rankings (university_short, rank)")
        
        # Compound index for university score sorting
        await db[Collections.UNIVERSITY_RANKINGS].create_index([
            ("university_short", 1),
            ("overall_score", -1)
        ])
        logger.info("✓ Created compound index on university_rankings (university_short, overall_score)")
        
        logger.info("✅ All indexes created successfully!")
        
        # List all indexes for verification
        logger.info("\nVerifying created indexes...")
        
        collections_to_check = [
            Collections.INTERNAL_USERS,
            Collections.INTERNAL_USERS_PROFILE,
            Collections.REGIONAL_RANKINGS,
            Collections.UNIVERSITY_RANKINGS
        ]
        
        for collection_name in collections_to_check:
            indexes = await db[collection_name].list_indexes().to_list(None)
            logger.info(f"\n{collection_name} indexes:")
            for idx in indexes:
                logger.info(f"  - {idx['name']}: {idx.get('key', {})}")
        
        # Close connection
        client.close()
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise


async def main():
    """Main function to run the index creation"""
    try:
        await create_ranking_indexes()
        logger.info("Index creation completed successfully!")
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())