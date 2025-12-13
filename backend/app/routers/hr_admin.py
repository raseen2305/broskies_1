"""
HR Admin API Router

This router provides administrative endpoints for HR users to manage
the hr_view collection and perform bulk operations.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from app.db_connection import get_database
from app.services.hr_view_service import HRViewService
from app.core.security import verify_token
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def verify_hr_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify that the current user is an authenticated HR admin
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Token payload with user information
        
    Raises:
        HTTPException: If token is invalid or user is not HR type
    """
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        user_type = payload.get("user_type")
        
        if user_type != "hr":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. HR authentication required."
            )
        
        return payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HR authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


router = APIRouter(
    prefix="/api/hr/admin",
    tags=["HR Admin"],
    dependencies=[Depends(verify_hr_admin)]  # Require HR authentication
)


@router.get("/stats")
async def get_hr_view_stats(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get statistics about the hr_view collection
    
    Returns:
        Statistics including document counts and data freshness
    """
    try:
        logger.info("HR admin requesting hr_view statistics")
        
        # Get counts
        hr_view_count = await db.hr_view.count_documents({})
        user_rankings_count = await db.user_rankings.count_documents({})
        
        # Get sample to check data structure
        sample = await db.hr_view.find_one({})
        
        # Calculate coverage
        coverage_percentage = (hr_view_count / user_rankings_count * 100) if user_rankings_count > 0 else 0
        
        return {
            "success": True,
            "stats": {
                "hr_view_count": hr_view_count,
                "user_rankings_count": user_rankings_count,
                "coverage_percentage": round(coverage_percentage, 2),
                "has_data": hr_view_count > 0,
                "sample_fields": list(sample.keys()) if sample else []
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting hr_view stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/sync/{username}")
async def sync_user_to_hr_view(
    username: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Sync a specific user from user_rankings to hr_view
    
    Args:
        username: GitHub username to sync
        db: Database connection
        
    Returns:
        Sync result
    """
    try:
        logger.info(f"HR admin requesting sync for user: {username}")
        
        # Initialize service
        hr_view_service = HRViewService(db)
        
        # Sync user
        result = await hr_view_service.sync_from_user_rankings(username)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"Successfully synced {username} to hr_view",
                "username": username,
                "upserted": result.get("upserted", False),
                "modified": result.get("modified", False)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Sync failed")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing user to hr_view: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync user: {str(e)}"
        )


@router.post("/sync-all")
async def sync_all_to_hr_view(
    limit: int = Query(None, description="Optional limit on number of users to sync"),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Bulk sync all users from user_rankings to hr_view
    
    This is useful for initial population or mass updates.
    
    Args:
        limit: Optional limit on number of users to sync
        db: Database connection
        
    Returns:
        Bulk sync results with statistics
    """
    try:
        logger.info(f"HR admin requesting bulk sync (limit: {limit or 'all'})")
        
        # Initialize service
        hr_view_service = HRViewService(db)
        
        # Ensure indexes first
        await hr_view_service.ensure_indexes()
        
        # Perform bulk sync
        result = await hr_view_service.bulk_sync_from_user_rankings(limit=limit)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Bulk sync completed",
                "stats": {
                    "total": result.get("total", 0),
                    "success_count": result.get("success_count", 0),
                    "error_count": result.get("error_count", 0)
                },
                "errors": result.get("errors", [])[:10]  # Return first 10 errors
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Bulk sync failed")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing bulk sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk sync: {str(e)}"
        )


@router.post("/ensure-indexes")
async def ensure_hr_view_indexes(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Ensure all required indexes exist on hr_view collection
    
    Returns:
        Success status
    """
    try:
        logger.info("HR admin requesting index creation")
        
        # Initialize service
        hr_view_service = HRViewService(db)
        
        # Create indexes
        await hr_view_service.ensure_indexes()
        
        return {
            "success": True,
            "message": "Indexes created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create indexes: {str(e)}"
        )


@router.delete("/clear")
async def clear_hr_view(
    confirm: bool = Query(False, description="Must be true to confirm deletion"),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Clear all data from hr_view collection
    
    WARNING: This will delete all data in hr_view. Use with caution!
    
    Args:
        confirm: Must be true to confirm deletion
        db: Database connection
        
    Returns:
        Deletion result
    """
    try:
        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must set confirm=true to clear hr_view collection"
            )
        
        logger.warning("HR admin requesting to clear hr_view collection")
        
        # Delete all documents
        result = await db.hr_view.delete_many({})
        
        logger.warning(f"Deleted {result.deleted_count} documents from hr_view")
        
        return {
            "success": True,
            "message": f"Cleared hr_view collection",
            "deleted_count": result.deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing hr_view: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear hr_view: {str(e)}"
        )
