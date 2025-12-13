"""
Background tasks for data migration and lifecycle management
Handles scheduled 24-hour data migrations and cleanup operations
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from celery import Celery
from celery.schedules import crontab

from app.services.data_migration_service import (
    data_migration_service,
    run_daily_migration,
    run_hr_migration,
    cleanup_temp_data,
    get_migration_status
)

logger = logging.getLogger(__name__)

# Celery app configuration
celery_app = Celery('migration_tasks')

@celery_app.task(bind=True, max_retries=3)
def scheduled_data_migration(self):
    """
    Scheduled task to run 24-hour data migration
    Runs daily to migrate expired data from temp to main databases
    """
    try:
        logger.info("🔐 [INTERNAL] Starting scheduled data migration task...")
        
        # Run the migration in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            migration_stats = loop.run_until_complete(run_daily_migration())
            
            # Log results
            logger.info(f"🔐 [INTERNAL] Scheduled migration completed successfully")
            logger.info(f"📊 Migration results: {migration_stats.migrated_records}/{migration_stats.total_records} records migrated")
            
            if migration_stats.errors:
                logger.warning(f"⚠️ Migration completed with {len(migration_stats.errors)} errors")
                for error in migration_stats.errors[:5]:  # Log first 5 errors
                    logger.warning(f"   - {error}")
            
            return {
                "success": True,
                "migrated_records": migration_stats.migrated_records,
                "total_records": migration_stats.total_records,
                "failed_records": migration_stats.failed_records,
                "duration": migration_stats.migration_duration,
                "errors": len(migration_stats.errors)
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        error_msg = f"Scheduled migration task failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)  # 1, 2, 4 minutes
            logger.info(f"🔄 Retrying migration task in {retry_delay} seconds...")
            raise self.retry(countdown=retry_delay, exc=e)
        
        return {
            "success": False,
            "error": error_msg,
            "retries": self.request.retries
        }

@celery_app.task(bind=True, max_retries=2)
def scheduled_hr_migration(self):
    """
    Scheduled task to migrate HR data
    Runs every 6 hours to handle HR-specific data migration
    """
    try:
        logger.info("🔐 [INTERNAL] Starting scheduled HR data migration task...")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            hr_stats = loop.run_until_complete(run_hr_migration())
            
            logger.info(f"🔐 [INTERNAL] HR migration completed successfully")
            logger.info(f"📊 HR migration results: {hr_stats.migrated_records}/{hr_stats.total_records} records migrated")
            
            return {
                "success": True,
                "migrated_records": hr_stats.migrated_records,
                "total_records": hr_stats.total_records,
                "failed_records": hr_stats.failed_records,
                "duration": hr_stats.migration_duration,
                "errors": len(hr_stats.errors)
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        error_msg = f"HR migration task failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        if self.request.retries < self.max_retries:
            retry_delay = 30 * (2 ** self.request.retries)  # 30, 60 seconds
            raise self.retry(countdown=retry_delay, exc=e)
        
        return {
            "success": False,
            "error": error_msg
        }

@celery_app.task(bind=True, max_retries=2)
def scheduled_cleanup_task(self):
    """
    Scheduled task to clean up migrated data from temp database
    Runs daily after migration to remove successfully migrated data
    """
    try:
        logger.info("🔐 [INTERNAL] Starting scheduled cleanup task...")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            cleanup_stats = loop.run_until_complete(cleanup_temp_data())
            
            logger.info(f"🔐 [INTERNAL] Cleanup completed successfully")
            logger.info(f"📊 Cleanup results: {cleanup_stats['documents_removed']} documents removed from {cleanup_stats['collections_cleaned']} collections")
            
            return {
                "success": True,
                "documents_removed": cleanup_stats["documents_removed"],
                "collections_cleaned": cleanup_stats["collections_cleaned"],
                "errors": cleanup_stats["errors"]
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        error_msg = f"Cleanup task failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        if self.request.retries < self.max_retries:
            retry_delay = 30 * (2 ** self.request.retries)
            raise self.retry(countdown=retry_delay, exc=e)
        
        return {
            "success": False,
            "error": error_msg
        }

@celery_app.task
def migration_health_check():
    """
    Health check task to monitor migration system status
    Runs every hour to check system health
    """
    try:
        logger.info("🔐 [INTERNAL] Running migration health check...")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            status = loop.run_until_complete(get_migration_status())
            
            # Check for issues
            issues = []
            
            # Check database connections
            db_connections = status.get("databases_connected", {})
            for db_name, connected in db_connections.items():
                if not connected:
                    issues.append(f"{db_name} database not connected")
            
            # Check for excessive pending migrations
            total_pending = status.get("total_pending_records", 0)
            if total_pending > 1000:
                issues.append(f"High number of pending migrations: {total_pending}")
            
            # Log health status
            if issues:
                logger.warning(f"⚠️ Migration health check found issues: {issues}")
            else:
                logger.info(f"✅ Migration system healthy - {total_pending} pending records")
            
            return {
                "healthy": len(issues) == 0,
                "issues": issues,
                "pending_records": total_pending,
                "timestamp": status.get("timestamp")
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        error_msg = f"Migration health check failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        return {
            "healthy": False,
            "error": error_msg,
            "timestamp": datetime.utcnow()
        }

# Celery beat schedule configuration
celery_app.conf.beat_schedule = {
    # Daily migration at 2 AM
    'daily-data-migration': {
        'task': 'app.tasks.migration_tasks.scheduled_data_migration',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM daily
        'options': {'queue': 'migration'}
    },
    
    # HR migration every 6 hours
    'hr-data-migration': {
        'task': 'app.tasks.migration_tasks.scheduled_hr_migration',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
        'options': {'queue': 'migration'}
    },
    
    # Cleanup task daily at 3 AM (after migration)
    'daily-cleanup': {
        'task': 'app.tasks.migration_tasks.scheduled_cleanup_task',
        'schedule': crontab(hour=3, minute=0),  # 3:00 AM daily
        'options': {'queue': 'migration'}
    },
    
    # Health check every hour
    'migration-health-check': {
        'task': 'app.tasks.migration_tasks.migration_health_check',
        'schedule': crontab(minute=0),  # Every hour
        'options': {'queue': 'monitoring'}
    },
}

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'app.tasks.migration_tasks.*': {'queue': 'migration'},
    },
    task_default_queue='default',
    task_default_exchange='default',
    task_default_exchange_type='direct',
    task_default_routing_key='default',
)

# Manual task execution functions for testing/debugging
async def run_migration_manually() -> Dict[str, Any]:
    """Manually trigger data migration for testing"""
    logger.info("🔧 Manual migration triggered")
    return await run_daily_migration()

async def run_cleanup_manually() -> Dict[str, Any]:
    """Manually trigger cleanup for testing"""
    logger.info("🔧 Manual cleanup triggered")
    return await cleanup_temp_data()

async def check_migration_health() -> Dict[str, Any]:
    """Manually check migration system health"""
    logger.info("🔧 Manual health check triggered")
    return await get_migration_status()

# Utility functions for monitoring and management
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of a specific migration task"""
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
            "traceback": result.traceback
        }
    except Exception as e:
        return {
            "task_id": task_id,
            "error": str(e)
        }

def cancel_task(task_id: str) -> bool:
    """Cancel a running migration task"""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        logger.info(f"🔧 Cancelled task {task_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to cancel task {task_id}: {e}")
        return False

def get_active_tasks() -> List[Dict[str, Any]]:
    """Get list of currently active migration tasks"""
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if active_tasks:
            all_tasks = []
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    all_tasks.append({
                        "worker": worker,
                        "task_id": task["id"],
                        "name": task["name"],
                        "args": task["args"],
                        "kwargs": task["kwargs"]
                    })
            return all_tasks
        
        return []
        
    except Exception as e:
        logger.error(f"❌ Failed to get active tasks: {e}")
        return []