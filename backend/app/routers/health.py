"""
Health Check API Endpoints
Provides comprehensive health monitoring endpoints for the multi-database system
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import logging

from app.services.database_initialization import (
    database_init_system,
    get_system_health_check,
    get_database_status,
    is_system_initialized
)
from app.services.error_diagnostic_system import error_diagnostic_system

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health Monitoring"])

@router.get("/", response_model=Dict[str, Any])
async def get_health_status(
    force_refresh: bool = Query(False, description="Force refresh of cached health data"),
    include_details: bool = Query(True, description="Include detailed health information")
):
    """
    Get comprehensive system health status
    
    Returns overall system health including:
    - Database connectivity status
    - Error statistics
    - Initialization status
    - System metrics
    """
    try:
        health_data = await get_system_health_check(force_refresh=force_refresh)
        
        if not include_details:
            # Return simplified health status
            return {
                "status": health_data.get("overall_status", "unknown"),
                "timestamp": health_data.get("timestamp"),
                "initialization_complete": health_data.get("initialization_complete", False),
                "healthy_databases": health_data.get("system_metrics", {}).get("healthy_databases", 0),
                "total_databases": health_data.get("system_metrics", {}).get("total_databases", 0)
            }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/database/{database_name}", response_model=Dict[str, Any])
async def get_specific_database_health(database_name: str):
    """
    Get detailed health status for a specific database
    
    Args:
        database_name: Name of the database to check (e.g., 'external_users', 'raseen_main_user')
    
    Returns:
        Detailed status information for the specified database
    """
    try:
        database_status = await get_database_status(database_name)
        
        if "error" in database_status and "not found" in database_status["error"]:
            raise HTTPException(
                status_code=404,
                detail=database_status["error"]
            )
        
        return database_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database health check failed for {database_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database health check failed: {str(e)}"
        )

@router.get("/databases", response_model=Dict[str, Any])
async def get_all_databases_health():
    """
    Get health status for all databases in the system
    
    Returns:
        Health status for each database in the multi-database architecture
    """
    try:
        from app.db_connection_multi import DatabaseType
        
        all_database_status = {}
        
        for db_type in DatabaseType:
            try:
                db_status = await get_database_status(db_type.value)
                all_database_status[db_type.value] = db_status
            except Exception as e:
                all_database_status[db_type.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Calculate summary statistics
        healthy_count = sum(
            1 for status in all_database_status.values()
            if status.get("status") == "healthy"
        )
        
        return {
            "summary": {
                "total_databases": len(DatabaseType),
                "healthy_databases": healthy_count,
                "unhealthy_databases": len(DatabaseType) - healthy_count,
                "overall_status": "healthy" if healthy_count == len(DatabaseType) else "degraded"
            },
            "databases": all_database_status,
            "timestamp": database_init_system.health_check_cache.get("timestamp") if database_init_system.health_check_cache else None
        }
        
    except Exception as e:
        logger.error(f"All databases health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"All databases health check failed: {str(e)}"
        )

@router.get("/errors", response_model=Dict[str, Any])
async def get_error_statistics(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back (1-168)")
):
    """
    Get error statistics for the specified time period
    
    Args:
        hours: Number of hours to look back (default: 24, max: 168/1 week)
    
    Returns:
        Comprehensive error statistics including breakdowns by database and operation type
    """
    try:
        error_stats = error_diagnostic_system.get_error_statistics(hours=hours)
        
        return {
            "time_period": f"{hours} hours",
            "statistics": error_stats,
            "health_summary": error_diagnostic_system.get_database_health_summary()
        }
        
    except Exception as e:
        logger.error(f"Error statistics endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error statistics retrieval failed: {str(e)}"
        )

@router.get("/initialization", response_model=Dict[str, Any])
async def get_initialization_status():
    """
    Get database system initialization status and results
    
    Returns:
        Detailed information about the database initialization process
    """
    try:
        if not is_system_initialized():
            return {
                "initialized": False,
                "status": "not_initialized",
                "message": "Database system has not been initialized yet"
            }
        
        initialization_results = database_init_system.initialization_results
        
        return {
            "initialized": True,
            "status": "completed",
            "results": initialization_results
        }
        
    except Exception as e:
        logger.error(f"Initialization status endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Initialization status retrieval failed: {str(e)}"
        )

@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_database_system():
    """
    Initialize or re-initialize the database system
    
    This endpoint triggers a complete database system initialization including:
    - Connection establishment to all seven databases
    - Connectivity verification
    - Schema validation
    - Index creation
    - Health checks
    
    Note: This is typically called automatically at startup, but can be manually triggered
    """
    try:
        logger.info("🔄 Manual database system initialization requested")
        
        initialization_results = await database_init_system.initialize_database_system()
        
        return {
            "message": "Database system initialization completed",
            "results": initialization_results
        }
        
    except Exception as e:
        logger.error(f"Manual initialization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database system initialization failed: {str(e)}"
        )

@router.get("/ping", response_model=Dict[str, str])
async def ping():
    """
    Simple ping endpoint for basic health monitoring
    
    Returns:
        Simple status message indicating the service is responsive
    """
    return {
        "status": "ok",
        "message": "Health monitoring service is responsive",
        "service": "database-health-monitor"
    }

@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check():
    """
    Kubernetes-style readiness check
    
    Returns:
        Readiness status indicating if the service is ready to handle requests
    """
    try:
        # Check if system is initialized
        if not is_system_initialized():
            raise HTTPException(
                status_code=503,
                detail="Database system not initialized"
            )
        
        # Quick health check
        health_data = await get_system_health_check(force_refresh=False)
        overall_status = health_data.get("overall_status", "unknown")
        
        if overall_status in ["critical", "unhealthy"]:
            raise HTTPException(
                status_code=503,
                detail=f"System not ready: {overall_status}"
            )
        
        return {
            "ready": True,
            "status": overall_status,
            "message": "Service is ready to handle requests"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Readiness check failed: {str(e)}"
        )

@router.get("/live", response_model=Dict[str, str])
async def liveness_check():
    """
    Kubernetes-style liveness check
    
    Returns:
        Liveness status indicating if the service is alive
    """
    return {
        "alive": "true",
        "message": "Service is alive and responding"
    }

# Additional utility endpoints

@router.get("/metrics", response_model=Dict[str, Any])
async def get_system_metrics():
    """
    Get system metrics for monitoring and alerting
    
    Returns:
        Key system metrics in a format suitable for monitoring systems
    """
    try:
        health_data = await get_system_health_check(force_refresh=False)
        
        # Extract key metrics
        system_metrics = health_data.get("system_metrics", {})
        error_stats = health_data.get("error_statistics", {})
        
        metrics = {
            "database_health": {
                "total_databases": system_metrics.get("total_databases", 0),
                "healthy_databases": system_metrics.get("healthy_databases", 0),
                "unhealthy_databases": system_metrics.get("total_databases", 0) - system_metrics.get("healthy_databases", 0)
            },
            "error_metrics": {
                "total_errors_24h": error_stats.get("total_errors", 0),
                "critical_errors_24h": error_stats.get("severity_counts", {}).get("critical", 0),
                "high_errors_24h": error_stats.get("severity_counts", {}).get("high", 0)
            },
            "system_status": {
                "overall_status": health_data.get("overall_status", "unknown"),
                "initialization_complete": health_data.get("initialization_complete", False),
                "uptime_seconds": system_metrics.get("uptime_seconds", 0)
            },
            "timestamp": health_data.get("timestamp")
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"System metrics endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"System metrics retrieval failed: {str(e)}"
        )