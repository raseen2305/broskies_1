"""
HR Data Handler Service
Handles HR data detection, routing, and storage in Single Database Architecture
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from bson import ObjectId

from app.database import get_database, Collections
# from app.db_connection_multi import multi_db_manager, DatabaseType  <-- REMOVED

logger = logging.getLogger(__name__)

class HRDataType:
    """Constants for HR data types"""
    HR_GOOGLE_FORM = "google_form"      # Was HR_REGISTRATION
    APPROVED_HR_USER = "approved_hr_user" # Was APPROVED_HR_USER / HR_USER
    SELECTED_STUDENT = "selected_student"
    STUDENT_POOL = "student_pool" # Maybe not used for storage, just retrieval

    # Legacy mapping if needed, or re-define
    CANDIDATE_PROFILE = "candidate_profile" 
    HR_USER = "hr_user" 
    HR_REGISTRATION = "hr_registration"

class HRDataHandler:
    """Handles HR data operations with Single Database"""
    
    def __init__(self):
        # Map Internal Types to User's Requested Collection Names
        self.hr_collections = {
            HRDataType.HR_GOOGLE_FORM: Collections.HR_GOOGLE_FORM,
            HRDataType.HR_REGISTRATION: Collections.HR_GOOGLE_FORM, # Alias
            
            HRDataType.APPROVED_HR_USER: Collections.HR_APPROVED,
            HRDataType.HR_USER: Collections.HR_APPROVED, # Alias
            
            HRDataType.SELECTED_STUDENT: Collections.HR_SELECTED_STUDENTS,
            
            HRDataType.STUDENT_POOL: Collections.HR_STUDENTS_POOL,
        }
    
    @staticmethod
    def is_hr_data(data: Dict[str, Any], operation_context: Optional[str] = None) -> bool:
        """Video of HR Data Detection Logic (Simplified/Kept)"""
        try:
            if operation_context:
                hr_contexts = ["hr_dashboard", "hr_auth", "hr_form", "hr_google_form", "recruiter"]
                if any(context in operation_context.lower() for context in hr_contexts):
                    return True
            
            if isinstance(data, dict):
                if "google_form_id" in data or ("recruiter_email" in data):
                    return True
            
            return False
        except:
            return False

    @staticmethod
    def get_hr_data_type(data: Dict[str, Any], operation_context: Optional[str] = None) -> str:
        """Determine HR Data Type"""
        if operation_context:
            ctx = operation_context.lower()
            if "google_form" in ctx or "registration" in ctx:
                return HRDataType.HR_GOOGLE_FORM
            if "approve" in ctx or "login" in ctx:
                return HRDataType.APPROVED_HR_USER
            if "select" in ctx:
                return HRDataType.SELECTED_STUDENT
        
        return HRDataType.HR_GOOGLE_FORM # Default

    async def store_hr_data(self, data: Dict[str, Any], hr_data_type: Optional[str] = None, operation_context: Optional[str] = None) -> Dict[str, Any]:
        """Store HR Data in Single DB"""
        try:
            if not hr_data_type:
                hr_data_type = self.get_hr_data_type(data, operation_context)
            
            collection_name = self.hr_collections.get(hr_data_type, Collections.HR_GOOGLE_FORM)
            
            storage_data = {
                **data,
                "hr_data_type": hr_data_type,
                "stored_at": datetime.utcnow(),
                "storage_location": "Broskies Hub"
            }
            
            db = await get_database()
            if db is None:
                raise Exception("Database connection failed")
                
            result = await db[collection_name].insert_one(storage_data)
            
            logger.info(f"✅ [HR_STORAGE] Stored in {collection_name} ID: {result.inserted_id}")
            
            return {
                "success": True,
                "document_id": str(result.inserted_id),
                "collection": collection_name
            }
        except Exception as e:
            logger.error(f"❌ [HR_STORAGE] Failed: {e}")
            return {"success": False, "error": str(e)}

    async def retrieve_hr_data(self, query: Dict[str, Any], collection_name: Optional[str] = None, hr_data_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve HR Data"""
        try:
            if not collection_name:
                if hr_data_type:
                    collection_name = self.hr_collections.get(hr_data_type, Collections.HR_GOOGLE_FORM)
                else:
                    collection_name = Collections.HR_GOOGLE_FORM
            
            db = await get_database()
            documents = await db[collection_name].find(query).to_list(length=None)
            return documents
        except Exception as e:
            logger.error(f"❌ [HR_RETRIEVAL] Failed: {e}")
            return []

    async def update_hr_data(self, query: Dict[str, Any], update_data: Dict[str, Any], collection_name: Optional[str] = None, hr_data_type: Optional[str] = None) -> Dict[str, Any]:
        try:
            if not collection_name:
                collection_name = self.hr_collections.get(hr_data_type, Collections.HR_GOOGLE_FORM) if hr_data_type else Collections.HR_GOOGLE_FORM
            
            db = await get_database()
            result = await db[collection_name].update_many(query, update_data)
            return {"success": True, "modified_count": result.modified_count}
        except Exception as e:
             logger.error(f"❌ [HR_UPDATE] Failed: {e}")
             return {"success": False, "error": str(e)}
             
    async def get_hr_collections_info(self):
        """Mock info for now"""
        return {"status": "Single Database Active"}

hr_data_handler = HRDataHandler()

# Convenience Exports
async def store_hr_data(data: Dict, hr_data_type: str = None, operation_context: str = None):
    return await hr_data_handler.store_hr_data(data, hr_data_type, operation_context)

async def retrieve_hr_data(query: Dict, collection_name: str = None, hr_data_type: str = None):
    return await hr_data_handler.retrieve_hr_data(query, collection_name, hr_data_type)

async def update_hr_data(query: Dict, update_data: Dict, collection_name: str = None, hr_data_type: str = None):
    return await hr_data_handler.update_hr_data(query, update_data, collection_name, hr_data_type)

def is_hr_data(data: Dict, operation_context: str = None):
    return hr_data_handler.is_hr_data(data, operation_context)

def get_hr_data_type(data: Dict, operation_context: str = None):
    return hr_data_handler.get_hr_data_type(data, operation_context)

async def get_hr_collections_info():
    return await hr_data_handler.get_hr_collections_info()