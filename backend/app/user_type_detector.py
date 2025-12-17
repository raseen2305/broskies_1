"""
User Type Detection and Database Routing System
Handles identification of internal vs external users based on JWT authentication status
and routes them to appropriate collections in the Single Database architecture.
"""

from typing import Optional, Dict, Any, Literal, Union
from fastapi import Request, HTTPException
from app.database import get_database, Collections
from app.core.security import get_current_user_optional
from app.services.hr_data_handler import is_hr_data, get_hr_data_type
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

UserType = Literal["internal", "external"]
DataCategory = Literal["user_data", "hr_data", "scan_cache", "analysis_progress"]

class UserTypeDetector:
    """Detects user type based on JWT authentication status and provides appropriate database routing"""
    
    @staticmethod
    async def detect_user_type(request: Request, username: Optional[str] = None) -> UserType:
        """
        Detect user type based purely on JWT authentication status
        """
        try:
            current_user = await get_current_user_optional(request)
            if current_user is not None:
                return "internal"
            return "external"
        except Exception as e:
            logger.debug(f"Authentication failed, treating as external user: {e}")
            return "external"
    
    @staticmethod
    def get_user_id_with_prefix(user_data: Union[str, Dict[str, Any]], user_type: UserType) -> str:
        """
        Get user ID. For internal users, use their ID. For external, use username.
        """
        if user_type == "internal":
            if isinstance(user_data, dict):
                username = user_data.get("username", user_data.get("login", user_data.get("email", "")))
            elif hasattr(user_data, 'username'):
                username = user_data.username
            elif hasattr(user_data, 'email'):
                username = user_data.email.split('@')[0] if user_data.email else str(user_data.id)
            else:
                username = str(user_data)
            return username
        else:  # external
            if isinstance(user_data, dict):
                username = user_data.get("username", user_data.get("login", ""))
            elif hasattr(user_data, 'username'):
                username = user_data.username
            else:
                username = str(user_data)
            return username
    
    @staticmethod
    async def get_appropriate_database(user_type: UserType, data_category: DataCategory = "user_data", data: Optional[Dict[str, Any]] = None, operation_context: Optional[str] = None):
        """
        Always returns the Single Database instance.
        """
        return await get_database()
    
    @staticmethod
    def get_collection_name(base_collection: str, user_type: UserType) -> str:
        """
        Get collection name based on user type.
        Internal -> internal_users
        External -> external_users
        """
        if user_type == "internal":
            return Collections.INTERNAL_USERS
        else:
            return Collections.EXTERNAL_USERS
    
    @staticmethod
    async def route_user_operation(request: Request, username: str, operation_type: str = "scan", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete user routing that detects type and provides all necessary routing information
        """
        try:
            # Detect user type
            user_type = await UserTypeDetector.detect_user_type(request, username)
            
            # Check if this is HR data
            is_hr_operation = data and is_hr_data(data, operation_type)
            hr_data_type = get_hr_data_type(data, operation_type) if is_hr_operation else None
            
            # Generate appropriate user ID
            if user_type == "internal":
                current_user = await get_current_user_optional(request)
                user_id = UserTypeDetector.get_user_id_with_prefix(current_user, user_type)
            else:
                user_id = UserTypeDetector.get_user_id_with_prefix(username, user_type)
            
            # Get Database (Always Single DB)
            database = await UserTypeDetector.get_appropriate_database(user_type, "user_data", data, operation_type)
            
            # Get collection names
            if is_hr_operation:
                # Map HR operations to HR collections
                if hr_data_type == "google_form":
                    scan_collection = Collections.HR_GOOGLE_FORM
                elif hr_data_type == "approved":
                    scan_collection = Collections.HR_APPROVED
                elif hr_data_type == "selected":
                    scan_collection = Collections.HR_SELECTED_STUDENTS
                else:
                    scan_collection = Collections.HR_STUDENTS_POOL # Default/Fallback
                
                # Use same collection for analysis progress or separate?
                # For simplicity, keeping it same or using a suffix if logic demands, 
                # but user spec was explicit about Folders.
                # Let's assume progress is stored in "internal_users" or same collection for simplicity unless specified.
                analysis_collection = scan_collection 
                storage_location = "HR_COLLECTION"
            else:
                if user_type == "internal":
                    scan_collection = Collections.INTERNAL_USERS
                    analysis_collection = Collections.INTERNAL_USERS
                else:
                    scan_collection = Collections.EXTERNAL_USERS
                    analysis_collection = Collections.EXTERNAL_USERS
                
                storage_location = "Broskies Hub"
            
            routing_info = {
                "user_type": user_type,
                "user_id": user_id,
                "username": username,
                "database": database,
                "scan_collection": scan_collection,
                "analysis_collection": analysis_collection,
                "storage_location": storage_location,
                "is_hr_operation": is_hr_operation,
                "hr_data_type": hr_data_type
            }
            
            logger.info(f"🔄 [ROUTING] User: {username} ({user_type}) -> Collection: {scan_collection}")
            
            return routing_info
            
        except Exception as e:
            error_msg = f"error in routing user operation for {username}: {e}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

# Convenience functions
async def detect_user_type_from_request(request: Request, username: Optional[str] = None) -> UserType:
    return await UserTypeDetector.detect_user_type(request, username)

async def get_user_database(request: Request, data_category: DataCategory = "user_data", data: Optional[Dict[str, Any]] = None, operation_context: Optional[str] = None, username: Optional[str] = None):
    return await get_database()

def create_prefixed_user_id(user_data: Union[str, Dict[str, Any]], user_type: UserType) -> str:
    return UserTypeDetector.get_user_id_with_prefix(user_data, user_type)

def get_prefixed_collection_name(base_collection: str, user_type: UserType) -> str:
    return UserTypeDetector.get_collection_name(base_collection, user_type)