from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    async def connect_to_database(self):
        try:
            logger.info("Connecting to MongoDB...")
            self.client = AsyncIOMotorClient(
                settings.mongodb_url,
                uuidRepresentation="standard",
            )
            self.db = self.client[settings.database_name]
            # Ping
            await self.client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB Database: {settings.database_name}")
        except Exception as e:
            logger.error(f"❌ Could not connect to MongoDB: {e}")
            raise e

    async def close_database_connection(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB Connection closed.")

    def get_database(self):
        return self.db

db_manager = DatabaseManager()

async def get_database():
    return db_manager.get_database()
