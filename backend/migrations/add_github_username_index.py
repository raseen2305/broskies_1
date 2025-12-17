"""
Migration script to add github_username index to user_profiles collection
Run this script once to add the index for fast lookups by GitHub username
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_github_username_index():
    """Add index on github_username field in user_profiles collection"""
    try:
        # Get MongoDB connection string
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        database_name = os.getenv("DATABASE_NAME", "github_analyzer")
        
        logger.info(f"Connecting to MongoDB: {mongodb_url}")
        
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_url)
        db = client[database_name]
        
        # Check if index already exists
        existing_indexes = await db.user_profiles.index_information()
        
        if "github_username_1" in existing_indexes:
            logger.info("✅ Index on github_username already exists")
        else:
            # Create index on github_username field
            await db.user_profiles.create_index("github_username")
            logger.info("✅ Created index on github_username field")
        
        # Verify the index was created
        indexes = await db.user_profiles.index_information()
        logger.info(f"Current indexes on user_profiles: {list(indexes.keys())}")
        
        # Close connection
        client.close()
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(add_github_username_index())
