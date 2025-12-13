#!/usr/bin/env python3
"""
Fast Scan Router for Quick GitHub Profile Analysis
"""

import asyncio
import time
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.services.fast_github_scanner import fast_scan_github_profile, FastScanConfig
from app.core.config import get_github_token
from app.db_connection import get_database

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/fast-scan/{username}")
async def fast_scan_user(
    username: str,
    background_tasks: BackgroundTasks,
    force_refresh: bool = False
) -> JSONResponse:
    """Fast GitHub profile scan with immediate results"""
    
    start_time = time.time()
    logger.info(f"🚀 Starting fast scan for {username}")
    
    try:
        # Get GitHub token
        github_token = get_github_token()
        if not github_token:
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        # Get database connection
        db = await get_database()
        
        # If force_refresh is True, invalidate old cache first
        if force_refresh and db is not None:
            deleted_count = await db.fast_scan_cache.delete_many({"username": username})
            if deleted_count.deleted_count > 0:
                logger.info(f"🗑️ Invalidated {deleted_count.deleted_count} cached entries for {username}")
        
        # Check for cached results only if NOT force refresh
        if not force_refresh:
            if db is not None:
                cached_result = await db.fast_scan_cache.find_one(
                    {"username": username},
                    sort=[("scan_date", -1)]
                )
                
                if cached_result:
                    # Check if cache is recent (less than 5 minutes old)
                    scan_date = cached_result.get('scan_date')
                    if scan_date and isinstance(scan_date, datetime):
                        age_minutes = (datetime.utcnow() - scan_date).total_seconds() / 60
                        if age_minutes < 5:
                            elapsed = time.time() - start_time
                            logger.info(f"⚡ Returning cached result for {username} in {elapsed:.2f}s (age: {age_minutes:.1f} min)")
                            
                            # Remove MongoDB ObjectId for JSON serialization
                            result = dict(cached_result)
                            result.pop('_id', None)
                            result['fromCache'] = True
                            result['cacheAge'] = f"{age_minutes:.1f} minutes"
                            
                            return JSONResponse({
                                "success": True,
                                "data": result,
                                "processingTime": elapsed,
                                "fromCache": True
                            })
        
        # If we reach here, perform fresh scan
        logger.info(f"🔄 Performing fresh scan for {username} (force_refresh={force_refresh})")
        
        # Perform fast scan
        scan_result = await fast_scan_github_profile(username, github_token)
        
        if not scan_result:
            raise HTTPException(status_code=404, detail=f"User {username} not found or scan failed")
        
        elapsed = time.time() - start_time
        
        # Add metadata
        current_time = datetime.utcnow()
        scan_result.update({
            'scan_date': current_time.isoformat(),  # ISO format for JSON response
            'processing_time': elapsed,
            'scan_type': 'fast',
            'fromCache': False
        })
        
        # Cache the result in background (pass datetime separately)
        background_tasks.add_task(cache_scan_result, username, scan_result, current_time)
        
        # Store in main scan results for compatibility
        background_tasks.add_task(store_scan_result, username, scan_result)
        
        logger.info(f"✅ Fast scan completed for {username} in {elapsed:.2f}s")
        
        return JSONResponse({
            "success": True,
            "data": scan_result,
            "processingTime": elapsed,
            "message": f"Fast scan completed in {elapsed:.2f} seconds"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ Fast scan failed for {username} after {elapsed:.2f}s: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Fast scan failed: {str(e)}"
        )

@router.get("/fast-scan/{username}/status")
async def get_fast_scan_status(username: str) -> JSONResponse:
    """Get the status of the most recent fast scan"""
    
    try:
        db = await get_database()
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Check fast scan cache
        cached_result = await db.fast_scan_cache.find_one(
            {"username": username},
            sort=[("scan_date", -1)]
        )
        
        if cached_result:
            scan_date = cached_result.get('scan_date')
            age_minutes = (datetime.utcnow() - scan_date).total_seconds() / 60 if scan_date else 999
            
            return JSONResponse({
                "success": True,
                "hasCachedResult": True,
                "lastScanDate": scan_date.isoformat() if scan_date else None,
                "cacheAgeMinutes": round(age_minutes, 1),
                "isRecent": age_minutes < 5,
                "overallScore": cached_result.get('overallScore', 0),
                "processingTime": cached_result.get('processing_time', 0)
            })
        else:
            return JSONResponse({
                "success": True,
                "hasCachedResult": False,
                "message": "No cached scan results found"
            })
            
    except Exception as e:
        logger.error(f"Failed to get scan status for {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scan status: {str(e)}")

@router.delete("/fast-scan/{username}/cache")
async def clear_fast_scan_cache(username: str) -> JSONResponse:
    """Clear cached fast scan results for a user"""
    
    try:
        db = await get_database()
        if db is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        result = await db.fast_scan_cache.delete_many({"username": username})
        
        return JSONResponse({
            "success": True,
            "deletedCount": result.deleted_count,
            "message": f"Cleared {result.deleted_count} cached results for {username}"
        })
        
    except Exception as e:
        logger.error(f"Failed to clear cache for {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

# Background task functions
async def cache_scan_result(username: str, scan_result: Dict[str, Any], scan_datetime: datetime):
    """Cache scan result for future use"""
    try:
        db = await get_database()
        if db is not None:
            # Remove old cache entries (keep only latest 3)
            old_entries = await db.fast_scan_cache.find(
                {"username": username},
                sort=[("scan_date", -1)]
            ).skip(2).to_list(length=None)
            
            if old_entries:
                old_ids = [entry['_id'] for entry in old_entries]
                await db.fast_scan_cache.delete_many({"_id": {"$in": old_ids}})
            
            # Insert new cache entry with datetime object
            cache_entry = {
                "username": username,
                **scan_result,
                "scan_date": scan_datetime  # Override with datetime object
            }
            
            # Debug: Check scan_date type before inserting
            scan_date_type = type(cache_entry.get('scan_date')).__name__
            logger.info(f"📦 Caching scan result for {username}, scan_date type: {scan_date_type}")
            
            await db.fast_scan_cache.insert_one(cache_entry)
            logger.info(f"✅ Cached fast scan result for {username}")
            
    except Exception as e:
        logger.error(f"Failed to cache scan result for {username}: {e}")

async def store_scan_result(username: str, scan_result: Dict[str, Any]):
    """Store scan result in main collection for compatibility"""
    try:
        db = await get_database()
        if db is not None:
            # Prepare data for main scan_results collection
            main_result = {
                "userId": username,
                "username": username,
                "scanDate": datetime.utcnow(),
                "lastScanDate": datetime.utcnow(),
                "scanType": "fast",
                "overallScore": scan_result.get('overallScore', 0),
                "activityScore": scan_result.get('activityScore', 0),
                "consistencyScore": scan_result.get('consistencyScore', 0),
                "innovationScore": scan_result.get('innovationScore', 0),
                "deliveryScore": scan_result.get('deliveryScore', 0),
                "repositoriesCount": scan_result.get('repositoriesCount', 0),
                "totalStars": scan_result.get('totalStars', 0),
                "totalForks": scan_result.get('totalForks', 0),
                "primaryLanguage": scan_result.get('primaryLanguage', ''),
                "languages": scan_result.get('languages', {}),
                "accountDetails": {
                    "name": scan_result.get('name', ''),
                    "bio": scan_result.get('bio', ''),
                    "location": scan_result.get('location', ''),
                    "company": scan_result.get('company', ''),
                    "followers": scan_result.get('followers', 0),
                    "following": scan_result.get('following', 0),
                    "public_repos": scan_result.get('public_repos', 0),
                    "created_at": scan_result.get('created_at', ''),
                    "avatar_url": scan_result.get('avatar_url', '')
                },
                "repositories": scan_result.get('repositories', []),
                "processingTime": scan_result.get('processing_time', 0),
                "isFastScan": True
            }
            
            # Upsert to main collection
            await db.scan_results.update_one(
                {"userId": username},
                {"$set": main_result},
                upsert=True
            )
            
            logger.info(f"💾 Stored fast scan result in main collection for {username}")
            
    except Exception as e:
        logger.error(f"Failed to store scan result for {username}: {e}")

# Test endpoint
@router.get("/test-fast-scan")
async def test_fast_scan_endpoint() -> JSONResponse:
    """Test the fast scan with raseen2305"""
    
    try:
        # Test with raseen2305
        result = await fast_scan_user("raseen2305", BackgroundTasks(), force_refresh=True)
        return result
        
    except Exception as e:
        logger.error(f"Test fast scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")