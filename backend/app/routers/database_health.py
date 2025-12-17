"""
Database Health Check Router
Provides endpoints for monitoring database connectivity and health
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
import logging
from datetime import datetime

from app.db_connection_multi import multi_db_manager, DatabaseType
from app.services.error_diagnostic_system import error_diagnostic_system
from app.core.security import get_current_user_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["database-health"])

async def verify_admin_access(current_user_token: dict = Depends(get_current_user_token)):
    """Verify that the current user has admin access to health endpoints"""
    try:
        user_type = current_user_token.get("user_type")
        if user_type not in ["admin", "developer"]:  # Allow developers for debugging
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for health endpoints"
            )
        return current_user_token
    except Exception as e:
        logger.error(f"Admin verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

@router.get("/databases")
async def get_database_health(
    admin_user: dict = Depends(verify_admin_access)
) -> Dict[str, Any]:
    """
    Get comprehensive health status of all databases
    
    Returns connection status, recent errors, and performance metrics
    for all seven databases in the multi-database architecture.
    
    Requires admin authentication.
    """
    try:
        logger.info("🏥 [HEALTH_CHECK] Getting database health status...")
        
        # Get connection health from multi-database manager
        connection_health = await multi_db_manager.get_health_status()
        
        # Get error statistics from diagnostic system
        error_stats = error_diagnostic_system.get_error_statistics(hours=24)
        
        # Get operation health summary
        operation_health = error_diagnostic_system.get_database_health_summary()
        
        # Calculate overall health score
        total_databases = len(DatabaseType)
        healthy_databases = sum(
            1 for db_health in connection_health["databases"].values()
            if db_health["connected"]
        )
        
        health_score = (healthy_databases / total_databases) * 100
        
        # Determine overall status
        if health_score >= 90:
            overall_status = "healthy"
        elif health_score >= 70:
            overall_status = "degraded"
        elif health_score >= 50:
            overall_status = "unhealthy"
        else:
            overall_status = "critical"
        
        # Recent critical errors
        critical_errors = [
            error for error in error_stats["most_recent_errors"]
            if error["severity"] == "critical"
        ]
        
        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status,
            "health_score": round(health_score, 1),
            "database_connections": connection_health,
            "error_statistics": {
                "last_24_hours": error_stats["total_errors"],
                "critical_errors": len(critical_errors),
                "error_breakdown": error_stats["error_breakdown"],
                "severity_distribution": error_stats["severity_counts"]
            },
            "operation_performance": operation_health["operation_health"],
            "recent_critical_errors": critical_errors[:5],  # Last 5 critical errors
            "recommendations": []
        }
        
        # Add recommendations based on health status
        if health_score < 100:
            disconnected_dbs = [
                db_name for db_name, db_health in connection_health["databases"].items()
                if not db_health["connected"]
            ]
            if disconnected_dbs:
                health_report["recommendations"].append({
                    "type": "connection_issue",
                    "message": f"Reconnect to databases: {', '.join(disconnected_dbs)}",
                    "severity": "high"
                })
        
        if error_stats["total_errors"] > 50:
            health_report["recommendations"].append({
                "type": "high_error_rate",
                "message": f"High error rate detected: {error_stats['total_errors']} errors in 24h",
                "severity": "medium"
            })
        
        if len(critical_errors) > 0:
            health_report["recommendations"].append({
                "type": "critical_errors",
                "message": f"{len(critical_errors)} critical errors require immediate attention",
                "severity": "critical"
            })
        
        logger.info(f"🏥 [HEALTH_CHECK] Health report generated: {overall_status} ({health_score}%)")
        
        return {
            "success": True,
            "data": health_report
        }
        
    except Exception as e:
        logger.error(f"🏥 [HEALTH_CHECK] Failed to get database health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database health: {str(e)}"
        )

@router.get("/databases/{database_name}")
async def get_specific_database_health(
    database_name: str,
    admin_user: dict = Depends(verify_admin_access)
) -> Dict[str, Any]:
    """
    Get detailed health information for a specific database
    
    Args:
        database_name: Name of the database (e.g., "raseen_main_user", "external_users")
    
    Returns:
        Detailed health information including connection status, recent operations,
        and error history for the specified database.
    """
    try:
        # Validate database name
        try:
            db_type = DatabaseType(database_name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid database name: {database_name}. Valid names: {[db.value for db in DatabaseType]}"
            )
        
        logger.info(f"🏥 [HEALTH_CHECK] Getting health for database: {database_name}")
        
        # Get connection health
        overall_health = await multi_db_manager.get_health_status()
        db_health = overall_health["databases"].get(database_name, {})
        
        # Get error statistics for this database
        all_errors = error_diagnostic_system.get_error_statistics(hours=24)
        db_errors = [
            error for error in all_errors["most_recent_errors"]
            if error["database_name"] == database_name
        ]
        
        # Get operation statistics for this database
        operation_health = error_diagnostic_system.get_database_health_summary()
        db_operations = {
            op_key: stats for op_key, stats in operation_health["operation_health"].items()
            if database_name in op_key
        }
        
        # Test connection with a simple ping
        connection_test = {"status": "unknown", "response_time": None, "error": None}
        try:
            import time
            start_time = time.time()
            
            async def ping_operation(database):
                # Simple ping operation
                return await database.command("ping")
            
            await multi_db_manager.safe_db_operation(
                db_type,
                ping_operation,
                operation_name="health_check_ping"
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            connection_test = {
                "status": "success",
                "response_time": round(response_time, 2),
                "error": None
            }
            
        except Exception as e:
            connection_test = {
                "status": "failed",
                "response_time": None,
                "error": str(e)
            }
        
        detailed_health = {
            "database_name": database_name,
            "timestamp": datetime.utcnow().isoformat(),
            "connection_status": db_health,
            "connection_test": connection_test,
            "recent_errors": {
                "count_24h": len(db_errors),
                "errors": db_errors[-10:]  # Last 10 errors
            },
            "operation_statistics": db_operations,
            "recommendations": []
        }
        
        # Add specific recommendations
        if not db_health.get("connected", False):
            detailed_health["recommendations"].append({
                "type": "connection_failed",
                "message": f"Database {database_name} is not connected",
                "action": "Check connection string and network connectivity",
                "severity": "critical"
            })
        
        if connection_test["status"] == "failed":
            detailed_health["recommendations"].append({
                "type": "ping_failed",
                "message": f"Ping test failed: {connection_test['error']}",
                "action": "Verify database is running and accessible",
                "severity": "high"
            })
        
        if connection_test["response_time"] and connection_test["response_time"] > 1000:
            detailed_health["recommendations"].append({
                "type": "slow_response",
                "message": f"Slow response time: {connection_test['response_time']}ms",
                "action": "Check network latency and database performance",
                "severity": "medium"
            })
        
        if len(db_errors) > 10:
            detailed_health["recommendations"].append({
                "type": "high_error_rate",
                "message": f"High error rate: {len(db_errors)} errors in 24h",
                "action": "Review error logs and investigate root causes",
                "severity": "medium"
            })
        
        return {
            "success": True,
            "data": detailed_health
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🏥 [HEALTH_CHECK] Failed to get health for {database_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database health: {str(e)}"
        )

@router.post("/databases/initialize")
async def initialize_all_databases(
    admin_user: dict = Depends(verify_admin_access)
) -> Dict[str, Any]:
    """
    Initialize connections to all databases
    
    This endpoint attempts to establish connections to all seven databases
    and returns the initialization results. Useful for startup verification
    and troubleshooting connection issues.
    """
    try:
        logger.info("🚀 [HEALTH_CHECK] Initializing all database connections...")
        
        # Initialize all connections
        initialization_results = await multi_db_manager.initialize_all_connections()
        
        # Count successful connections
        successful_connections = sum(
            1 for status in initialization_results.values()
            if "✅" in status
        )
        total_connections = len(initialization_results)
        
        # Determine overall result
        if successful_connections == total_connections:
            overall_status = "success"
            message = f"All {total_connections} database connections initialized successfully"
        elif successful_connections > 0:
            overall_status = "partial"
            message = f"{successful_connections}/{total_connections} database connections initialized"
        else:
            overall_status = "failed"
            message = "Failed to initialize any database connections"
        
        return {
            "success": successful_connections > 0,
            "overall_status": overall_status,
            "message": message,
            "initialization_results": initialization_results,
            "successful_connections": successful_connections,
            "total_connections": total_connections,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"🚀 [HEALTH_CHECK] Database initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database initialization failed: {str(e)}"
        )

@router.get("/errors")
async def get_error_summary(
    hours: int = 24,
    admin_user: dict = Depends(verify_admin_access)
) -> Dict[str, Any]:
    """
    Get error summary for the specified time period
    
    Args:
        hours: Number of hours to look back (default: 24)
    
    Returns:
        Summary of errors, including breakdown by database, operation type,
        and severity levels.
    """
    try:
        if hours < 1 or hours > 168:  # Max 1 week
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hours must be between 1 and 168 (1 week)"
            )
        
        logger.info(f"📊 [HEALTH_CHECK] Getting error summary for last {hours} hours")
        
        error_stats = error_diagnostic_system.get_error_statistics(hours=hours)
        
        return {
            "success": True,
            "data": {
                "time_period_hours": hours,
                "summary": error_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"📊 [HEALTH_CHECK] Failed to get error summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get error summary: {str(e)}"
        )

@router.get("/status")
async def get_quick_status() -> Dict[str, Any]:
    """
    Get quick health status without authentication
    
    Returns basic connectivity status for monitoring systems.
    This endpoint provides minimal information and doesn't require authentication.
    """
    try:
        # Get basic connection health
        health_status = await multi_db_manager.get_health_status()
        
        # Count healthy databases
        healthy_count = sum(
            1 for db_health in health_status["databases"].values()
            if db_health["connected"]
        )
        total_count = len(health_status["databases"])
        
        # Get recent critical errors count
        error_stats = error_diagnostic_system.get_error_statistics(hours=1)
        critical_errors = error_stats["severity_counts"]["critical"]
        
        status = "healthy"
        if healthy_count < total_count:
            status = "degraded"
        if critical_errors > 0:
            status = "critical"
        
        return {
            "status": status,
            "databases_healthy": f"{healthy_count}/{total_count}",
            "critical_errors_last_hour": critical_errors,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"⚡ [HEALTH_CHECK] Quick status check failed: {e}")
        return {
            "status": "error",
            "databases_healthy": "unknown",
            "critical_errors_last_hour": "unknown",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }