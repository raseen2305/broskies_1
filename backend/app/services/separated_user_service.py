"""
User Service for Separated Database Architecture
Handles internal and external users with appropriate database routing
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from bson import ObjectId

from app.db_connection_separated import (
    get_internal_database, 
    get_external_database,
    safe_internal_operation,
    safe_external_operation
)
from app.models.user import User, UserCreate, HRUser, HRUserCreate

logger = logging.getLogger(__name__)

class SeparatedUserService:
    """Service for managing users across separated databases"""
    
    # Internal User Operations (Authenticated Users)
    
    async def create_internal_user(self, user_data: UserCreate) -> Optional[User]:
        """Create a new internal user (developer who registered)"""
        
        async def _create_user(db):
            # Check if user already exists
            existing = await db.users.find_one({
                "$or": [
                    {"email": user_data.email},
                    {"github_username": user_data.github_username}
                ]
            })
            
            if existing:
                raise ValueError("User with this email or GitHub username already exists")
            
            # Create user document
            user_doc = {
                **user_data.dict(),
                "created_at": datetime.utcnow(),
                "is_