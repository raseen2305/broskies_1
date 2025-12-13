"""
Background task for batch ranking updates
Runs periodically to keep rankings fresh
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
import asyncio

logger = logging.getLogger(__name__)


async def batch_update_all_rankings():
    """
    Update rankings for all regions and universities
    Should be run periodically (e.g., every hour)
    """
    try:
        from app.db_connection import get_database
        from app.services.enhanced_ranking_service import EnhancedRankingService
        
        logger.info("🔄 Starting batch ranking update for all groups")
        start_time = datetime.utcnow()
        
        db = await get_database()
        if not db:
            logger.error("Database connection not available")
            return {
                "success": False,
                "error": "Database unavailable"
            }
        
        ranking_service = EnhancedRankingService(db)
        
        # Get all unique regions
        regions = await db.user_rankings.distinct("region", {"region": {"$ne": None}})
        logger.info(f"Found {len(regions)} regions to update")
        
        # Get all unique universities
        universities = await db.user_rankings.distinct(
            "university_short", 
            {"university_short": {"$ne": None}}
        )
        logger.info(f"Found {len(universities)} universities to update")
        
        results = {
            "success": True,
            "start_time": start_time.isoformat(),
            "regional_updates": [],
            "university_updates": [],
            "total_regions": len(regions),
            "total_universities": len(universities),
            "regions_updated": 0,
            "universities_updated": 0,
            "errors": []
        }
        
        # Update regional rankings
        for region in regions:
            try:
                result = await ranking_service.batch_update_regional_rankings(region)
                results["regional_updates"].append(result)
                if result["success"]:
                    results["regions_updated"] += 1
            except Exception as e:
                logger.error(f"Error updating region {region}: {e}")
                results["errors"].append({
                    "type": "regional",
                    "identifier": region,
                    "error": str(e)
                })
        
        # Update university rankings
        for university in universities:
            try:
                result = await ranking_service.batch_update_university_rankings(university)
                results["university_updates"].append(result)
                if result["success"]:
                    results["universities_updated"] += 1
            except Exception as e:
                logger.error(f"Error updating university {university}: {e}")
                results["errors"].append({
                    "type": "university",
                    "identifier": university,
                    "error": str(e)
                })
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = duration
        
        logger.info(f"✅ Batch ranking update completed in {duration:.2f}s")
        logger.info(f"   - Regions updated: {results['regions_updated']}/{results['total_regions']}")
        logger.info(f"   - Universities updated: {results['universities_updated']}/{results['total_universities']}")
        logger.info(f"   - Errors: {len(results['errors'])}")
        
        return results
        
    except Exception as e:
        logger.error(f"Fatal error in batch ranking update: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def update_rankings_for_groups(regions: List[str] = None, universities: List[str] = None):
    """
    Update rankings for specific regions and/or universities
    
    Args:
        regions: List of region identifiers to update
        universities: List of university_short identifiers to update
    """
    try:
        from app.db_connection import get_database
        from app.services.enhanced_ranking_service import EnhancedRankingService
        
        db = await get_database()
        if not db:
            logger.error("Database connection not available")
            return {"success": False, "error": "Database unavailable"}
        
        ranking_service = EnhancedRankingService(db)
        
        results = {
            "success": True,
            "regional_updates": [],
            "university_updates": []
        }
        
        # Update specified regions
        if regions:
            for region in regions:
                result = await ranking_service.batch_update_regional_rankings(region)
                results["regional_updates"].append(result)
        
        # Update specified universities
        if universities:
            for university in universities:
                result = await ranking_service.batch_update_university_rankings(university)
                results["university_updates"].append(result)
        
        return results
        
    except Exception as e:
        logger.error(f"Error updating specific groups: {e}")
        return {"success": False, "error": str(e)}


# Celery task wrapper (if using Celery)
try:
    from app.celery_app import celery_app
    
    @celery_app.task(name="ranking_batch_update")
    def celery_batch_update_rankings():
        """Celery task wrapper for batch ranking updates"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(batch_update_all_rankings())
    
except ImportError:
    logger.warning("Celery not available, batch updates must be triggered manually")
