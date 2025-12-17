"""
Progress Tracker
Tracks and stores analysis progress with real-time updates
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Tracks analysis progress for real-time updates
    
    Stores progress in database and provides methods for:
    - Starting analysis
    - Updating progress
    - Calculating percentage and ETA
    - Completing analysis
    - Handling failures
    """
    
    # Update interval (seconds)
    UPDATE_INTERVAL = 2.0
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize progress tracker
        
        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.collection = database.analysis_progress
        self.logger = logger
        self._last_update = {}  # Track last update time per user
    
    async def start_analysis(
        self,
        user_id: str,
        total_repositories: int
    ) -> str:
        """
        Start analysis progress tracking
        
        Args:
            user_id: User ID
            total_repositories: Total number of repositories to analyze
            
        Returns:
            Progress ID
        """
        doc = {
            'user_id': user_id,
            'stage': 'deep_analysis',
            'status': 'in_progress',
            'progress': {
                'current': 0,
                'total': total_repositories,
                'percentage': 0.0,
                'current_repo': None
            },
            'started_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'completed_at': None,
            'error': None
        }
        
        # Upsert progress document
        result = await self.collection.update_one(
            {'user_id': user_id, 'stage': 'deep_analysis'},
            {'$set': doc},
            upsert=True
        )
        
        self.logger.info(
            f"Started analysis progress tracking for user {user_id}: "
            f"{total_repositories} repositories"
        )
        
        # Initialize last update time
        self._last_update[user_id] = datetime.utcnow()
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            existing = await self.collection.find_one({
                'user_id': user_id,
                'stage': 'deep_analysis'
            })
            return str(existing['_id']) if existing else user_id
    
    async def update_progress(
        self,
        user_id: str,
        current: int,
        total: int,
        current_repo: Optional[str] = None
    ) -> bool:
        """
        Update analysis progress
        
        Updates every UPDATE_INTERVAL seconds to avoid excessive writes
        
        Args:
            user_id: User ID
            current: Current repository number
            total: Total repositories
            current_repo: Name of current repository being analyzed
            
        Returns:
            True if updated, False if skipped (too soon)
        """
        # Check if enough time has passed since last update
        now = datetime.utcnow()
        last_update = self._last_update.get(user_id)
        
        if last_update:
            time_since_update = (now - last_update).total_seconds()
            if time_since_update < self.UPDATE_INTERVAL and current < total:
                # Skip update if too soon (unless it's the last one)
                return False
        
        # Calculate percentage
        percentage = (current / total * 100) if total > 0 else 0.0
        
        # Calculate estimated time remaining
        eta_seconds = self._calculate_eta(user_id, current, total)
        
        # Update document
        update_doc = {
            'progress.current': current,
            'progress.total': total,
            'progress.percentage': round(percentage, 1),
            'progress.current_repo': current_repo,
            'updated_at': now
        }
        
        if eta_seconds is not None:
            update_doc['progress.eta_seconds'] = eta_seconds
        
        result = await self.collection.update_one(
            {'user_id': user_id, 'stage': 'deep_analysis'},
            {'$set': update_doc}
        )
        
        if result.modified_count > 0:
            self.logger.debug(
                f"Updated progress for user {user_id}: "
                f"{current}/{total} ({percentage:.1f}%)"
            )
            self._last_update[user_id] = now
            return True
        
        return False
    
    async def complete_analysis(
        self,
        user_id: str
    ) -> bool:
        """
        Mark analysis as completed
        
        Args:
            user_id: User ID
            
        Returns:
            True if updated successfully
        """
        now = datetime.utcnow()
        
        # Get start time to calculate total duration
        progress = await self.get_progress(user_id)
        duration = None
        
        if progress and progress.get('started_at'):
            started_at = progress['started_at']
            duration = (now - started_at).total_seconds()
        
        update_doc = {
            'status': 'completed',
            'progress.percentage': 100.0,
            'completed_at': now,
            'updated_at': now
        }
        
        if duration is not None:
            update_doc['duration_seconds'] = round(duration, 2)
        
        result = await self.collection.update_one(
            {'user_id': user_id, 'stage': 'deep_analysis'},
            {'$set': update_doc}
        )
        
        self.logger.info(
            f"Completed analysis for user {user_id} "
            f"(duration: {duration:.2f}s)" if duration else ""
        )
        
        # Clean up last update time
        self._last_update.pop(user_id, None)
        
        return result.modified_count > 0
    
    async def fail_analysis(
        self,
        user_id: str,
        error_message: str
    ) -> bool:
        """
        Mark analysis as failed
        
        Args:
            user_id: User ID
            error_message: Error message
            
        Returns:
            True if updated successfully
        """
        update_doc = {
            'status': 'failed',
            'error': error_message,
            'completed_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {'user_id': user_id, 'stage': 'deep_analysis'},
            {'$set': update_doc}
        )
        
        self.logger.error(
            f"Analysis failed for user {user_id}: {error_message}"
        )
        
        # Clean up last update time
        self._last_update.pop(user_id, None)
        
        return result.modified_count > 0
    
    async def get_progress(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get current progress for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Progress dictionary or None if not found
        """
        doc = await self.collection.find_one({
            'user_id': user_id,
            'stage': 'deep_analysis'
        })
        
        if doc:
            doc['_id'] = str(doc['_id'])
            return doc
        
        return None
    
    async def delete_progress(
        self,
        user_id: str
    ) -> bool:
        """
        Delete progress record
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted successfully
        """
        result = await self.collection.delete_one({
            'user_id': user_id,
            'stage': 'deep_analysis'
        })
        
        # Clean up last update time
        self._last_update.pop(user_id, None)
        
        return result.deleted_count > 0
    
    def _calculate_eta(
        self,
        user_id: str,
        current: int,
        total: int
    ) -> Optional[int]:
        """
        Calculate estimated time remaining
        
        Args:
            user_id: User ID
            current: Current repository number
            total: Total repositories
            
        Returns:
            Estimated seconds remaining or None if cannot calculate
        """
        if current == 0 or total == 0:
            return None
        
        # Get start time
        last_update = self._last_update.get(user_id)
        if not last_update:
            return None
        
        # Calculate elapsed time
        elapsed = (datetime.utcnow() - last_update).total_seconds()
        
        if elapsed == 0:
            return None
        
        # Calculate average time per repository
        avg_time_per_repo = elapsed / current
        
        # Calculate remaining repositories
        remaining = total - current
        
        # Calculate ETA
        eta_seconds = int(avg_time_per_repo * remaining)
        
        return eta_seconds
    
    async def cleanup_old_progress(
        self,
        days: int = 7
    ) -> int:
        """
        Clean up old progress records
        
        Args:
            days: Delete records older than this many days
            
        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.collection.delete_many({
            'updated_at': {'$lt': cutoff_date}
        })
        
        if result.deleted_count > 0:
            self.logger.info(
                f"Cleaned up {result.deleted_count} old progress records"
            )
        
        return result.deleted_count
    
    async def get_active_analyses(self) -> list:
        """
        Get all active analyses
        
        Returns:
            List of active progress documents
        """
        cursor = self.collection.find({
            'status': 'in_progress'
        }).sort('started_at', -1)
        
        analyses = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            analyses.append(doc)
        
        return analyses
    
    async def ensure_indexes(self) -> None:
        """
        Ensure required indexes exist
        """
        try:
            # Compound index for user + stage queries
            await self.collection.create_index(
                [('user_id', 1), ('stage', 1)],
                unique=True,
                name='user_stage'
            )
            
            # Index on status for active queries
            await self.collection.create_index('status')
            
            # TTL index on updated_at (auto-delete after 7 days)
            await self.collection.create_index(
                'updated_at',
                expireAfterSeconds=7 * 24 * 60 * 60,  # 7 days
                name='updated_at_ttl'
            )
            
            self.logger.info("Progress tracker indexes ensured")
            
        except Exception as e:
            self.logger.error(f"Error ensuring indexes: {e}")
