"""
Analysis State Storage Service
Manages persistence of analysis state using MongoDB for complex state objects
and Redis for quick lookups.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class AnalysisStateStorage:
    """
    MongoDB-based storage for analysis state with Redis caching.
    
    Stores analysis state including:
    - Analysis progress and status
    - Repository data
    - Evaluation results
    - Error information
    
    Requirements: 12.1-12.6
    """
    
    def __init__(self, database: AsyncIOMotorDatabase, cache_service=None):
        """
        Initialize analysis state storage.
        
        Args:
            database: MongoDB database instance
            cache_service: Optional Redis cache service for quick lookups
        """
        self.db = database
        self.collection = database.analysis_states
        self.cache_service = cache_service
        self.cache_ttl = 3600  # 1 hour cache TTL
        
    async def initialize(self):
        """Initialize indexes for efficient queries"""
        try:
            # Create indexes
            await self.collection.create_index("analysis_id")
            await self.collection.create_index("username", unique=True)  # Username is now unique key
            await self.collection.create_index("status")
            await self.collection.create_index("created_at")
            await self.collection.create_index(
                "created_at",
                expireAfterSeconds=86400  # Auto-delete after 24 hours
            )
            logger.info("Analysis state storage indexes created")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    async def store_state(self, analysis_id: str, state: Dict[str, Any]):
        """
        Store analysis state.
        
        Args:
            analysis_id: Unique analysis identifier
            state: Analysis state dictionary
        """
        try:
            # Add metadata
            state['analysis_id'] = analysis_id
            state['updated_at'] = datetime.utcnow()
            
            if 'created_at' not in state:
                state['created_at'] = datetime.utcnow()
            
            # Store in MongoDB using username as unique key (overrides previous analysis)
            # This ensures reanalyze replaces old data instead of creating duplicates
            username = state.get('username')
            if username:
                await self.collection.update_one(
                    {'username': username},
                    {'$set': state},
                    upsert=True
                )
            else:
                # Fallback to analysis_id if username not available
                await self.collection.update_one(
                    {'analysis_id': analysis_id},
                    {'$set': state},
                    upsert=True
                )
            
            # Cache in Redis for quick access
            if self.cache_service:
                await self.cache_service.set(
                    analysis_id,
                    state,
                    prefix='analysis_state',
                    ttl=self.cache_ttl
                )
            
            logger.debug(f"Stored state for analysis: {analysis_id}")
            
        except Exception as e:
            logger.error(f"Failed to store state for {analysis_id}: {e}")
            raise
    
    async def get_state(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis state.
        
        Args:
            analysis_id: Unique analysis identifier
            
        Returns:
            Analysis state dictionary or None if not found
        """
        try:
            # Try cache first
            if self.cache_service:
                cached_state = await self.cache_service.get(
                    analysis_id,
                    prefix='analysis_state'
                )
                if cached_state:
                    logger.debug(f"Retrieved state from cache: {analysis_id}")
                    return cached_state
            
            # Get from MongoDB
            state = await self.collection.find_one({'analysis_id': analysis_id})
            
            if state:
                # Remove MongoDB _id field
                state.pop('_id', None)
                
                # Convert datetime objects to ISO strings
                if 'created_at' in state and isinstance(state['created_at'], datetime):
                    state['created_at'] = state['created_at'].isoformat()
                if 'updated_at' in state and isinstance(state['updated_at'], datetime):
                    state['updated_at'] = state['updated_at'].isoformat()
                
                # Update cache
                if self.cache_service:
                    await self.cache_service.set(
                        analysis_id,
                        state,
                        prefix='analysis_state',
                        ttl=self.cache_ttl
                    )
                
                logger.debug(f"Retrieved state from MongoDB: {analysis_id}")
                return state
            
            logger.debug(f"State not found: {analysis_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get state for {analysis_id}: {e}")
            return None
    
    async def update_state(self, analysis_id: str, updates: Dict[str, Any]):
        """
        Update analysis state with partial updates.
        
        Args:
            analysis_id: Unique analysis identifier
            updates: Dictionary of fields to update
        """
        try:
            # Add update timestamp
            updates['updated_at'] = datetime.utcnow()
            
            # First try to find by username if available in updates
            username = updates.get('username')
            if username:
                # Update using username as the key (ensures reanalyze overrides existing data)
                result = await self.collection.update_one(
                    {'username': username},
                    {'$set': updates},
                    upsert=True
                )
            else:
                # Fallback: try to get username from existing document
                existing = await self.collection.find_one({'analysis_id': analysis_id})
                if existing and existing.get('username'):
                    result = await self.collection.update_one(
                        {'username': existing['username']},
                        {'$set': updates}
                    )
                else:
                    # Last resort: use analysis_id
                    result = await self.collection.update_one(
                        {'analysis_id': analysis_id},
                        {'$set': updates}
                    )
            
            if result.modified_count > 0 or result.upserted_id:
                # Invalidate cache to force refresh
                if self.cache_service:
                    await self.cache_service.delete(
                        analysis_id,
                        prefix='analysis_state'
                    )
                
                logger.debug(f"Updated state for analysis: {analysis_id}")
            else:
                logger.warning(f"No state found to update: {analysis_id}")
            
        except Exception as e:
            logger.error(f"Failed to update state for {analysis_id}: {e}")
            raise
    
    async def delete_state(self, analysis_id: str):
        """
        Delete analysis state.
        
        Args:
            analysis_id: Unique analysis identifier
        """
        try:
            # Delete from MongoDB
            await self.collection.delete_one({'analysis_id': analysis_id})
            
            # Delete from cache
            if self.cache_service:
                await self.cache_service.delete(
                    analysis_id,
                    prefix='analysis_state'
                )
            
            logger.info(f"Deleted state for analysis: {analysis_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete state for {analysis_id}: {e}")
            raise
    
    async def get_states_by_username(
        self,
        username: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent analysis states for a user.
        
        Args:
            username: GitHub username
            limit: Maximum number of states to return
            
        Returns:
            List of analysis state dictionaries
        """
        try:
            cursor = self.collection.find(
                {'username': username}
            ).sort('created_at', -1).limit(limit)
            
            states = []
            async for state in cursor:
                state.pop('_id', None)
                
                # Convert datetime objects
                if 'created_at' in state and isinstance(state['created_at'], datetime):
                    state['created_at'] = state['created_at'].isoformat()
                if 'updated_at' in state and isinstance(state['updated_at'], datetime):
                    state['updated_at'] = state['updated_at'].isoformat()
                
                states.append(state)
            
            return states
            
        except Exception as e:
            logger.error(f"Failed to get states for user {username}: {e}")
            return []
    
    async def cleanup_old_states(self, days: int = 1):
        """
        Clean up old analysis states.
        
        Args:
            days: Delete states older than this many days
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await self.collection.delete_many({
                'created_at': {'$lt': cutoff_date}
            })
            
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} old analysis states")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old states: {e}")
    
    async def cleanup_failed_states(self, hours: int = 2):
        """
        Clean up failed analysis states.
        
        Args:
            hours: Delete failed states older than this many hours
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(hours=hours)
            
            result = await self.collection.delete_many({
                'status': 'failed',
                'created_at': {'$lt': cutoff_date}
            })
            
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} failed analysis states")
            
        except Exception as e:
            logger.error(f"Failed to cleanup failed states: {e}")
    
    async def get_active_analyses(self) -> List[Dict[str, Any]]:
        """
        Get all currently active (in-progress) analyses.
        
        Returns:
            List of active analysis state dictionaries
        """
        try:
            cursor = self.collection.find({
                'status': {'$in': ['started', 'scoring', 'categorizing', 'evaluating', 'calculating']}
            }).sort('created_at', -1)
            
            states = []
            async for state in cursor:
                state.pop('_id', None)
                
                # Convert datetime objects
                if 'created_at' in state and isinstance(state['created_at'], datetime):
                    state['created_at'] = state['created_at'].isoformat()
                if 'updated_at' in state and isinstance(state['updated_at'], datetime):
                    state['updated_at'] = state['updated_at'].isoformat()
                
                states.append(state)
            
            return states
            
        except Exception as e:
            logger.error(f"Failed to get active analyses: {e}")
            return []
    
    async def update_results(self, analysis_id: str, results: Dict[str, Any]):
        """
        Update analysis results in storage.
        This is used to store the complete results after analysis completes.
        
        Args:
            analysis_id: Analysis identifier
            results: Complete results dictionary including repositories with all fields
        """
        try:
            # Try to find by analysis_id first to get username
            existing = await self.collection.find_one({'analysis_id': analysis_id})
            
            update_data = {
                'results': results,
                'updated_at': datetime.utcnow(),
                'status': 'complete'
            }
            
            if existing and existing.get('username'):
                # Update using username as the key (ensures reanalyze overrides existing data)
                await self.collection.update_one(
                    {'username': existing['username']},
                    {'$set': update_data}
                )
            else:
                # Fallback to analysis_id
                await self.collection.update_one(
                    {'analysis_id': analysis_id},
                    {'$set': update_data}
                )
            
            # Invalidate cache to force refresh
            if self.cache_service:
                await self.cache_service.delete(
                    analysis_id,
                    prefix='analysis_state'
                )
            
            logger.info(f"Updated results for analysis: {analysis_id}")
            
        except Exception as e:
            logger.error(f"Failed to update results for {analysis_id}: {e}")
            raise
    
    async def find_latest_complete_analysis(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Find the most recent completed analysis for a username.
        This is used when the page reloads to fetch categorization data.
        
        Args:
            username: GitHub username
            
        Returns:
            Complete analysis state with results, or None if no analysis found
        """
        try:
            # Query for most recent completed analysis
            state = await self.collection.find_one(
                {
                    'username': username,
                    'status': 'complete'
                },
                sort=[('updated_at', -1)]  # Most recent first
            )
            
            if state:
                # Remove MongoDB _id field
                state.pop('_id', None)
                
                # Convert datetime objects to ISO strings
                if 'created_at' in state and isinstance(state['created_at'], datetime):
                    state['created_at'] = state['created_at'].isoformat()
                if 'updated_at' in state and isinstance(state['updated_at'], datetime):
                    state['updated_at'] = state['updated_at'].isoformat()
                if 'completed_at' in state and isinstance(state['completed_at'], datetime):
                    state['completed_at'] = state['completed_at'].isoformat()
                
                logger.info(f"Found latest complete analysis for {username}: {state.get('analysis_id')}")
                return state
            
            logger.debug(f"No complete analysis found for username: {username}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to find latest analysis for {username}: {e}")
            return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about analysis states.
        
        Returns:
            Dictionary with statistics
        """
        try:
            total = await self.collection.count_documents({})
            
            # Count by status
            pipeline = [
                {'$group': {
                    '_id': '$status',
                    'count': {'$sum': 1}
                }}
            ]
            
            status_counts = {}
            async for doc in self.collection.aggregate(pipeline):
                status_counts[doc['_id']] = doc['count']
            
            # Get recent analyses
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_count = await self.collection.count_documents({
                'created_at': {'$gte': recent_cutoff}
            })
            
            return {
                'total_analyses': total,
                'status_counts': status_counts,
                'recent_24h': recent_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

