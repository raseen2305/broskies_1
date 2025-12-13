"""
Database utility functions for comprehensive GitHub integration.
Provides common database operations and helper functions.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

class DatabaseUtils:
    """Utility class for common database operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
    
    async def upsert_document(self, 
                            collection_name: str, 
                            filter_query: Dict[str, Any], 
                            document: Dict[str, Any],
                            update_timestamp: bool = True) -> str:
        """
        Insert or update a document based on filter query.
        Returns the document ID.
        """
        try:
            collection = getattr(self.db, collection_name)
            
            if update_timestamp:
                document["last_updated"] = datetime.utcnow()
            
            # Try to update existing document
            result = await collection.find_one_and_update(
                filter_query,
                {"$set": document},
                upsert=True,
                return_document=True
            )
            
            return str(result["_id"])
            
        except Exception as e:
            logger.error(f"Error upserting document in {collection_name}: {e}")
            raise
    
    async def bulk_upsert(self, 
                         collection_name: str, 
                         documents: List[Dict[str, Any]],
                         key_field: str = "_id") -> Dict[str, int]:
        """
        Perform bulk upsert operations.
        Returns counts of inserted and updated documents.
        """
        try:
            collection = getattr(self.db, collection_name)
            
            inserted_count = 0
            updated_count = 0
            
            for doc in documents:
                if key_field in doc:
                    # Update existing document
                    result = await collection.replace_one(
                        {key_field: doc[key_field]},
                        doc,
                        upsert=True
                    )
                    
                    if result.upserted_id:
                        inserted_count += 1
                    else:
                        updated_count += 1
                else:
                    # Insert new document
                    await collection.insert_one(doc)
                    inserted_count += 1
            
            return {
                "inserted": inserted_count,
                "updated": updated_count,
                "total": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Error in bulk upsert for {collection_name}: {e}")
            raise
    
    async def find_with_pagination(self, 
                                  collection_name: str, 
                                  filter_query: Dict[str, Any] = None,
                                  sort_field: str = "_id",
                                  sort_direction: int = 1,
                                  page: int = 1,
                                  page_size: int = 20) -> Dict[str, Any]:
        """
        Find documents with pagination support.
        Returns documents and pagination metadata.
        """
        try:
            collection = getattr(self.db, collection_name)
            filter_query = filter_query or {}
            
            # Calculate skip value
            skip = (page - 1) * page_size
            
            # Get total count
            total_count = await collection.count_documents(filter_query)
            
            # Get documents
            cursor = collection.find(filter_query).sort(sort_field, sort_direction).skip(skip).limit(page_size)
            documents = await cursor.to_list(length=page_size)
            
            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "documents": documents,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
            
        except Exception as e:
            logger.error(f"Error in paginated find for {collection_name}: {e}")
            raise
    
    async def aggregate_with_pipeline(self, 
                                    collection_name: str, 
                                    pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline and return results"""
        try:
            collection = getattr(self.db, collection_name)
            cursor = collection.aggregate(pipeline)
            return await cursor.to_list(length=None)
            
        except Exception as e:
            logger.error(f"Error in aggregation for {collection_name}: {e}")
            raise
    
    async def get_user_repositories(self, 
                                   user_id: str, 
                                   include_private: bool = True,
                                   sort_by: str = "stars",
                                   limit: int = None) -> List[Dict[str, Any]]:
        """Get repositories for a specific user with sorting and filtering"""
        try:
            filter_query = {"user_id": user_id}
            
            if not include_private:
                filter_query["is_private"] = False
            
            # Determine sort field and direction
            sort_direction = -1  # Descending by default
            if sort_by == "name":
                sort_direction = 1
            elif sort_by == "created_at":
                sort_direction = -1
            elif sort_by == "updated_at":
                sort_direction = -1
            
            cursor = self.db.detailed_repositories.find(filter_query).sort(sort_by, sort_direction)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return await cursor.to_list(length=None)
            
        except Exception as e:
            logger.error(f"Error getting user repositories: {e}")
            return []
    
    async def get_repository_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive repository analytics for a user"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "total_repositories": {"$sum": 1},
                    "total_stars": {"$sum": "$stars"},
                    "total_forks": {"$sum": "$forks"},
                    "total_size": {"$sum": "$size"},
                    "avg_acid_score": {"$avg": "$acid_scores.overall"},
                    "languages": {"$push": "$language"},
                    "private_repos": {"$sum": {"$cond": ["$is_private", 1, 0]}},
                    "public_repos": {"$sum": {"$cond": ["$is_private", 0, 1]}},
                    "forked_repos": {"$sum": {"$cond": ["$is_fork", 1, 0]}},
                    "original_repos": {"$sum": {"$cond": ["$is_fork", 0, 1]}}
                }},
                {"$project": {
                    "_id": 0,
                    "total_repositories": 1,
                    "total_stars": 1,
                    "total_forks": 1,
                    "total_size": 1,
                    "avg_acid_score": {"$round": ["$avg_acid_score", 2]},
                    "private_repos": 1,
                    "public_repos": 1,
                    "forked_repos": 1,
                    "original_repos": 1,
                    "languages": 1
                }}
            ]
            
            results = await self.aggregate_with_pipeline("detailed_repositories", pipeline)
            
            if results:
                analytics = results[0]
                
                # Process languages
                languages = analytics.get("languages", [])
                language_counts = {}
                for lang in languages:
                    if lang:
                        language_counts[lang] = language_counts.get(lang, 0) + 1
                
                analytics["language_breakdown"] = dict(
                    sorted(language_counts.items(), key=lambda x: x[1], reverse=True)
                )
                
                return analytics
            
            return {
                "total_repositories": 0,
                "total_stars": 0,
                "total_forks": 0,
                "total_size": 0,
                "avg_acid_score": 0.0,
                "private_repos": 0,
                "public_repos": 0,
                "forked_repos": 0,
                "original_repos": 0,
                "language_breakdown": {}
            }
            
        except Exception as e:
            logger.error(f"Error getting repository analytics: {e}")
            return {}
    
    async def search_repositories(self, 
                                 query: str, 
                                 filters: Dict[str, Any] = None,
                                 limit: int = 20) -> List[Dict[str, Any]]:
        """Search repositories using text search and filters"""
        try:
            search_filter = {"$text": {"$search": query}}
            
            if filters:
                search_filter.update(filters)
            
            cursor = self.db.detailed_repositories.find(
                search_filter,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            return await cursor.to_list(length=limit)
            
        except Exception as e:
            logger.error(f"Error searching repositories: {e}")
            return []
    
    async def get_trending_repositories(self, 
                                      language: str = None,
                                      days: int = 7,
                                      limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending repositories based on recent activity"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            match_filter = {
                "updated_at": {"$gte": cutoff_date},
                "is_private": False
            }
            
            if language:
                match_filter["language"] = language
            
            pipeline = [
                {"$match": match_filter},
                {"$addFields": {
                    "trending_score": {
                        "$add": [
                            {"$multiply": ["$stars", 0.4]},
                            {"$multiply": ["$forks", 0.3]},
                            {"$multiply": ["$acid_scores.overall", 0.3]}
                        ]
                    }
                }},
                {"$sort": {"trending_score": -1}},
                {"$limit": limit}
            ]
            
            return await self.aggregate_with_pipeline("detailed_repositories", pipeline)
            
        except Exception as e:
            logger.error(f"Error getting trending repositories: {e}")
            return []
    
    async def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired data across collections"""
        cleanup_results = {}
        
        try:
            # Clean up expired scan progress (older than 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            scan_progress_result = await self.db.scan_progress.delete_many({
                "last_update": {"$lt": cutoff_time}
            })
            cleanup_results["scan_progress"] = scan_progress_result.deleted_count
            
            # Clean up expired cache metadata
            cache_result = await self.db.cache_metadata.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            cleanup_results["cache_metadata"] = cache_result.deleted_count
            
            logger.info(f"Cleanup completed: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return cleanup_results
    
    async def get_collection_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all collections"""
        collections = [
            "users", "github_user_profiles", "repositories", 
            "detailed_repositories", "comprehensive_scan_results",
            "contribution_calendars", "pull_request_analysis", "issue_analysis"
        ]
        
        stats = {}
        
        for collection_name in collections:
            try:
                collection = getattr(self.db, collection_name)
                
                # Get document count
                count = await collection.count_documents({})
                
                # Get collection size (approximate)
                collection_stats = await self.db.command("collStats", collection_name)
                
                stats[collection_name] = {
                    "document_count": count,
                    "size_bytes": collection_stats.get("size", 0),
                    "avg_document_size": collection_stats.get("avgObjSize", 0),
                    "index_count": collection_stats.get("nindexes", 0),
                    "total_index_size": collection_stats.get("totalIndexSize", 0)
                }
                
            except Exception as e:
                logger.warning(f"Could not get stats for {collection_name}: {e}")
                stats[collection_name] = {"error": str(e)}
        
        return stats

# Utility functions
async def ensure_indexes_exist(database: AsyncIOMotorDatabase, 
                              collection_name: str, 
                              required_indexes: List[str]) -> bool:
    """Ensure that required indexes exist on a collection"""
    try:
        collection = getattr(database, collection_name)
        existing_indexes = await collection.list_indexes().to_list(length=None)
        existing_index_names = {idx.get("name", "") for idx in existing_indexes}
        
        missing_indexes = set(required_indexes) - existing_index_names
        
        if missing_indexes:
            logger.warning(f"Missing indexes in {collection_name}: {missing_indexes}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking indexes for {collection_name}: {e}")
        return False

async def convert_object_ids(document: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ObjectId fields to strings in a document"""
    if "_id" in document and isinstance(document["_id"], ObjectId):
        document["_id"] = str(document["_id"])
    
    for key, value in document.items():
        if isinstance(value, ObjectId):
            document[key] = str(value)
        elif isinstance(value, dict):
            document[key] = await convert_object_ids(value)
        elif isinstance(value, list):
            document[key] = [
                await convert_object_ids(item) if isinstance(item, dict) else 
                str(item) if isinstance(item, ObjectId) else item
                for item in value
            ]
    
    return document

async def validate_document_schema(document: Dict[str, Any], 
                                 required_fields: List[str]) -> List[str]:
    """Validate that a document contains required fields"""
    missing_fields = []
    
    for field in required_fields:
        if "." in field:
            # Handle nested fields
            parts = field.split(".")
            current = document
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    missing_fields.append(field)
                    break
        else:
            if field not in document:
                missing_fields.append(field)
    
    return missing_fields