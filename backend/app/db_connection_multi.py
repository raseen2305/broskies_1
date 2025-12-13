"""
[LEGACY COMPATIBILITY LAYER]
This file replaces the old Multi-Database Manager.
It redirects all calls to the Single Database Manager (Broskies Hub).
"""

from enum import Enum
from typing import Optional, Any, Callable
import logging
from app.database import get_database

logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    EXTERNAL_USERS = "external_users"
    RASEEN_TEMP_USER = "raseen_temp_user"
    RASEEN_MAIN_USER = "raseen_main_user"
    RASEEN_MAIN_HR = "raseen_main_hr"
    SRIE_MAIN_USER = "srie_main_user"
    SRIE_MAIN_HR = "srie_main_hr"

class MultiDatabaseManager:
    """Shim for legacy manager"""
    
    async def get_database(self, db_type: DatabaseType):
        """Redirects to Single DB"""
        # logger.warning(f"⚠️ [LEGACY_ACCESS] Redirecting request for {db_type} to Single DB")
        return await get_database()

    async def safe_db_operation(
        self, 
        db_type: DatabaseType, 
        operation: Callable, 
        fallback_result: Any = None,
        operation_name: str = "database operation"
    ) -> Any:
        """Executes operation against Single DB directly"""
        try:
            db = await get_database()
            return await operation(db)
        except Exception as e:
            logger.error(f"❌ [LEGACY_OP_FAILED] {operation_name}: {e}")
            return fallback_result

multi_db_manager = MultiDatabaseManager()

# Legacy Accessors Redirects
async def get_external_users_db(): return await get_database()
async def get_raseen_temp_user_db(): return await get_database()
async def get_raseen_main_user_db(): return await get_database()
async def get_raseen_main_hr_db(): return await get_database()
async def get_srie_main_user_db(): return await get_database()
async def get_srie_main_hr_db(): return await get_database()

async def initialize_multi_database_connections():
    return {"status": "Single DB Active"}

async def close_multi_database_connections():
    pass

async def get_multi_database_health():
    return {"status": "healthy", "mode": "single_db_shim"}