"""
Debug endpoints for troubleshooting deployment issues
"""

from fastapi import APIRouter, HTTPException
from app.db_connection import get_db_health, diagnose_connection_issues
import logging
import os
import sys
import platform

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "message": "API is running",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "python_version": sys.version,
        "platform": platform.platform()
    }

@router.get("/db-health")
async def database_health():
    """Database health check endpoint"""
    try:
        health_info = await get_db_health()
        return {
            "status": "success",
            "database": health_info
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "database": {"healthy": False, "error": str(e)}
        }

@router.get("/db-diagnostics")
async def database_diagnostics():
    """Comprehensive database connection diagnostics"""
    try:
        diagnostics = await diagnose_connection_issues()
        return {
            "status": "success",
            "diagnostics": diagnostics
        }
    except Exception as e:
        logger.error(f"Database diagnostics failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/env-info")
async def environment_info():
    """Get environment information"""
    try:
        env_info = {
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "mongodb_configured": bool(os.getenv("MONGODB_URL")),
            "redis_configured": bool(os.getenv("REDIS_URL")),
            "github_configured": bool(os.getenv("GITHUB_TOKEN"))
        }
        
        return {
            "status": "success",
            "environment": env_info,
            "platform_info": {
                "python_version": sys.version,
                "platform": platform.platform(),
                "architecture": platform.architecture(),
                "processor": platform.processor()
            }
        }
    except Exception as e:
        logger.error(f"Environment info failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.post("/test-connection")
async def test_database_connection():
    """Force a database connection test"""
    try:
        from app.db_connection import connect_to_mongo_serverless, get_database
        
        # Force reconnection
        await connect_to_mongo_serverless()
        
        # Test database operations
        database = await get_database()
        if database:
            # Try a simple operation
            collections = await database.list_collection_names()
            
            return {
                "status": "success",
                "message": "Database connection successful",
                "collections_count": len(collections),
                "collections": collections[:5]  # First 5 collections
            }
        else:
            return {
                "status": "error",
                "message": "Database connection failed - no database instance"
            }
            
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Database connection test failed"
        }

@router.get("/logs")
async def get_recent_logs():
    """Get recent application logs (if available)"""
    try:
        # This is a simple implementation - in production you might want to use a proper logging service
        return {
            "status": "success",
            "message": "Logs endpoint available",
            "note": "Check Vercel function logs for detailed information"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
