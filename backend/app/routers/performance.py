from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
import time

from app.database import get_database
from app.routers.auth import get_current_user
from app.services.cache_service import cache_service
from app.services.performance_service import performance_service
from app.services.concurrent_data_fetcher import concurrent_fetcher
from app.services.connection_pool_manager import connection_pool_manager
from app.services.scan_queue_manager import scan_queue_manager

router = APIRouter()

@router.get("/health")
async def performance_health_check():
    """Check the health of performance-related services"""
    try:
        start_time = time.time()
        
        # Test database connection
        db = await get_database()
        db_healthy = db is not None
        
        # Test cache connection
        cache_stats = await cache_service.get_cache_stats()
        cache_healthy = cache_stats.get("connected", False)
        
        # Calculate response time
        response_time = round((time.time() - start_time) * 1000, 2)  # in milliseconds
        
        return {
            "status": "healthy" if db_healthy and cache_healthy else "degraded",
            "database": {
                "status": "connected" if db_healthy else "disconnected",
                "type": "MongoDB"
            },
            "cache": {
                "status": "connected" if cache_healthy else "disconnected",
                "type": "Redis",
                "stats": cache_stats
            },
            "response_time_ms": response_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/metrics")
async def get_performance_metrics(
    current_user = Depends(get_current_user)
):
    """Get comprehensive performance metrics"""
    try:
        metrics = await performance_service.get_performance_metrics()
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.post("/benchmark")
async def run_performance_benchmark(
    iterations: int = Query(default=10, ge=1, le=100),
    current_user = Depends(get_current_user),
    db = Depends(get_database)
):
    """Run performance benchmark tests"""
    try:
        results = {
            "iterations": iterations,
            "tests": {},
            "summary": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Test 1: Database query performance
        start_time = time.time()
        for i in range(iterations):
            await db.users.find_one({"user_type": "developer"})
        db_query_time = (time.time() - start_time) / iterations
        results["tests"]["database_query_avg_ms"] = round(db_query_time * 1000, 2)
        
        # Test 2: Cache performance
        start_time = time.time()
        for i in range(iterations):
            await cache_service.set(f"benchmark_key_{i}", {"test": "data"}, ttl=60)
            await cache_service.get(f"benchmark_key_{i}")
        cache_time = (time.time() - start_time) / iterations
        results["tests"]["cache_operation_avg_ms"] = round(cache_time * 1000, 2)
        
        # Test 3: Aggregation query performance
        start_time = time.time()
        for i in range(min(iterations, 5)):  # Limit aggregation tests
            await performance_service.get_aggregated_user_stats("test_user")
        agg_time = (time.time() - start_time) / min(iterations, 5)
        results["tests"]["aggregation_query_avg_ms"] = round(agg_time * 1000, 2)
        
        # Clean up benchmark cache keys
        for i in range(iterations):
            await cache_service.delete(f"benchmark_key_{i}")
        
        # Summary
        results["summary"] = {
            "fastest_operation": min(results["tests"], key=results["tests"].get),
            "slowest_operation": max(results["tests"], key=results["tests"].get),
            "total_benchmark_time_ms": round(sum(results["tests"].values()), 2)
        }
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")

@router.post("/cache/warm-up")
async def warm_up_cache(
    current_user = Depends(get_current_user),
    db = Depends(get_database)
):
    """Warm up cache with frequently accessed data"""
    try:
        warmed_items = 0
        
        # Warm up top developers cache
        top_devs = await performance_service.get_top_developers(limit=50)
        if top_devs:
            warmed_items += len(top_devs)
        
        # Warm up user profiles for active users
        recent_users = await db.users.find({
            "last_scan": {"$exists": True}
        }).sort("last_scan", -1).limit(20).to_list(None)
        
        for user in recent_users:
            user_id = str(user["_id"])
            # This will cache the user stats
            await performance_service.get_aggregated_user_stats(user_id)
            warmed_items += 1
        
        return {
            "message": "Cache warm-up completed",
            "items_cached": warmed_items,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache warm-up failed: {str(e)}")

@router.delete("/cache/clear")
async def clear_all_cache(
    confirm: bool = Query(default=False),
    current_user = Depends(get_current_user)
):
    """Clear all cache data (use with caution)"""
    try:
        if not confirm:
            raise HTTPException(
                status_code=400, 
                detail="Add ?confirm=true to confirm cache clearing"
            )
        
        # Clear different cache prefixes
        prefixes = ["user_profile", "user_repos", "user_evaluations", "user_stats", 
                   "top_developers", "scan_results", "repo_analysis", "github_user"]
        
        cleared_count = 0
        for prefix in prefixes:
            count = await cache_service.clear_prefix(prefix)
            cleared_count += count
        
        return {
            "message": "Cache cleared successfully",
            "items_cleared": cleared_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clearing failed: {str(e)}")

@router.get("/database/indexes")
async def get_database_indexes(
    current_user = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get information about database indexes"""
    try:
        collections = ["users", "repositories", "evaluations", "hr_users"]
        indexes_info = {}
        
        for collection_name in collections:
            try:
                collection = getattr(db, collection_name)
                indexes = await collection.list_indexes().to_list(None)
                indexes_info[collection_name] = [
                    {
                        "name": idx.get("name"),
                        "key": idx.get("key"),
                        "unique": idx.get("unique", False),
                        "sparse": idx.get("sparse", False)
                    }
                    for idx in indexes
                ]
            except Exception as e:
                indexes_info[collection_name] = {"error": str(e)}
        
        return {
            "indexes": indexes_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get index information: {str(e)}")

@router.post("/database/optimize")
async def optimize_database_performance(
    current_user = Depends(get_current_user)
):
    """Run database optimization tasks"""
    try:
        await performance_service.optimize_database_queries()
        
        return {
            "message": "Database optimization completed",
            "optimizations": [
                "Created/updated indexes for better query performance",
                "Added compound indexes for common query patterns",
                "Optimized aggregation pipeline indexes"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database optimization failed: {str(e)}")

@router.get("/query-analysis")
async def analyze_query_performance(
    collection: str = Query(..., description="Collection name to analyze"),
    current_user = Depends(get_current_user),
    db = Depends(get_database)
):
    """Analyze query performance for a specific collection"""
    try:
        if collection not in ["users", "repositories", "evaluations", "hr_users"]:
            raise HTTPException(status_code=400, detail="Invalid collection name")
        
        collection_obj = getattr(db, collection)
        
        # Get collection stats
        stats = await db.command("collStats", collection)
        
        # Sample some common queries and their execution stats
        query_analysis = {
            "collection": collection,
            "stats": {
                "count": stats.get("count", 0),
                "size": stats.get("size", 0),
                "avgObjSize": stats.get("avgObjSize", 0),
                "storageSize": stats.get("storageSize", 0),
                "totalIndexSize": stats.get("totalIndexSize", 0)
            },
            "indexes": stats.get("indexSizes", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return query_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query analysis failed: {str(e)}")

@router.get("/dashboard")
async def get_performance_dashboard(
    current_user = Depends(get_current_user)
):
    """Get comprehensive performance dashboard data"""
    try:
        dashboard_data = await performance_service.get_performance_dashboard_data()
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance dashboard: {str(e)}")

@router.get("/api-metrics")
async def get_api_performance_metrics(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to retrieve"),
    current_user = Depends(get_current_user)
):
    """Get API performance metrics for the specified time period"""
    try:
        api_metrics = performance_service.get_api_performance_summary(hours)
        return api_metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get API metrics: {str(e)}")

@router.get("/database-metrics")
async def get_database_performance_metrics(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to retrieve"),
    current_user = Depends(get_current_user)
):
    """Get database performance metrics for the specified time period"""
    try:
        db_metrics = performance_service.get_database_performance_summary(hours)
        return db_metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database metrics: {str(e)}")

@router.get("/scanning-metrics")
async def get_scanning_performance_metrics(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to retrieve"),
    current_user = Depends(get_current_user)
):
    """Get scanning operation performance metrics for the specified time period"""
    try:
        scanning_metrics = performance_service.get_scanning_performance_summary(hours)
        return scanning_metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scanning metrics: {str(e)}")

@router.get("/system-resources")
async def get_system_resource_metrics(
    current_user = Depends(get_current_user)
):
    """Get current system resource usage metrics"""
    try:
        system_metrics = performance_service.get_system_resource_metrics()
        return system_metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")

@router.get("/alerts")
async def get_performance_alerts(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of alerts to retrieve"),
    current_user = Depends(get_current_user)
):
    """Get performance alerts for the specified time period"""
    try:
        alerts = performance_service.get_performance_alerts(hours)
        return {
            "alerts": alerts,
            "count": len(alerts),
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance alerts: {str(e)}")

@router.post("/record-metric")
async def record_performance_metric(
    metric_data: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Manually record a performance metric (for testing/debugging)"""
    try:
        metric_type = metric_data.get("type", "api")
        
        if metric_type == "api":
            performance_service.record_api_metric(
                endpoint=metric_data.get("endpoint", "/test"),
                method=metric_data.get("method", "GET"),
                response_time_ms=metric_data.get("response_time_ms", 100),
                status_code=metric_data.get("status_code", 200),
                user_id=metric_data.get("user_id"),
                error=metric_data.get("error")
            )
        elif metric_type == "database":
            performance_service.record_database_metric(
                operation=metric_data.get("operation", "find"),
                collection=metric_data.get("collection", "test"),
                duration_ms=metric_data.get("duration_ms", 50),
                success=metric_data.get("success", True),
                error=metric_data.get("error"),
                query_type=metric_data.get("query_type", "find")
            )
        elif metric_type == "scanning":
            performance_service.record_scanning_metric(
                scan_id=metric_data.get("scan_id", "test_scan"),
                username=metric_data.get("username", "test_user"),
                phase=metric_data.get("phase", "test_phase"),
                duration_ms=metric_data.get("duration_ms", 1000),
                repositories_processed=metric_data.get("repositories_processed", 1),
                success=metric_data.get("success", True),
                error=metric_data.get("error")
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid metric type")
        
        return {
            "message": "Metric recorded successfully",
            "type": metric_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record metric: {str(e)}")

@router.get("/concurrent-fetcher/stats")
async def get_concurrent_fetcher_stats(
    current_user = Depends(get_current_user)
):
    """Get concurrent data fetcher performance statistics"""
    try:
        stats = concurrent_fetcher.get_stats()
        active_requests = concurrent_fetcher.get_active_requests()
        
        return {
            "stats": stats,
            "active_requests": active_requests,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get concurrent fetcher stats: {str(e)}")

@router.get("/connection-pools/stats")
async def get_connection_pool_stats(
    current_user = Depends(get_current_user)
):
    """Get connection pool statistics"""
    try:
        if not connection_pool_manager.initialized:
            return {
                "status": "not_initialized",
                "message": "Connection pool manager not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        pool_stats = connection_pool_manager.get_all_stats()
        health_status = await connection_pool_manager.health_check()
        
        return {
            "status": "initialized",
            "pool_stats": pool_stats,
            "health_status": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connection pool stats: {str(e)}")

@router.get("/scan-queue/stats")
async def get_scan_queue_stats(
    current_user = Depends(get_current_user)
):
    """Get scan queue manager statistics"""
    try:
        queue_stats = await scan_queue_manager.get_queue_stats()
        
        return {
            "queue_stats": {
                "total_jobs": queue_stats.total_jobs,
                "queued_jobs": queue_stats.queued_jobs,
                "running_jobs": queue_stats.running_jobs,
                "completed_jobs": queue_stats.completed_jobs,
                "failed_jobs": queue_stats.failed_jobs,
                "average_duration": queue_stats.average_duration,
                "throughput_per_hour": queue_stats.throughput_per_hour
            },
            "running": scan_queue_manager.running,
            "max_concurrent_scans": scan_queue_manager.max_concurrent_scans,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scan queue stats: {str(e)}")

@router.post("/concurrent-fetcher/test")
async def test_concurrent_fetcher(
    num_requests: int = Query(default=5, ge=1, le=20, description="Number of test requests"),
    current_user = Depends(get_current_user)
):
    """Test concurrent data fetcher performance"""
    try:
        import time
        
        # Define a simple test function
        async def test_function(request_id: str, delay: float = 0.1):
            await asyncio.sleep(delay)
            return {
                "request_id": request_id,
                "processed_at": datetime.utcnow().isoformat(),
                "delay": delay
            }
        
        # Submit multiple concurrent requests
        start_time = time.time()
        request_ids = []
        
        for i in range(num_requests):
            request_id = f"test_request_{i}_{int(time.time())}"
            await concurrent_fetcher.submit_request(
                request_id=request_id,
                func=test_function,
                delay=0.1 + (i * 0.05)  # Varying delays
            )
            request_ids.append(request_id)
        
        # Wait for all results
        results = []
        for request_id in request_ids:
            result = await concurrent_fetcher.get_result(request_id, timeout=10.0)
            results.append({
                "request_id": result.request_id,
                "success": result.success,
                "duration": result.duration,
                "retry_count": result.retry_count,
                "result": result.result if result.success else None,
                "error": str(result.error) if result.error else None
            })
        
        total_time = time.time() - start_time
        
        return {
            "test_summary": {
                "num_requests": num_requests,
                "total_time_seconds": round(total_time, 3),
                "successful_requests": sum(1 for r in results if r["success"]),
                "failed_requests": sum(1 for r in results if not r["success"]),
                "average_request_duration": round(
                    sum(r["duration"] for r in results) / len(results), 3
                ),
                "concurrent_speedup": round(
                    (sum(0.1 + (i * 0.05) for i in range(num_requests))) / total_time, 2
                )
            },
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Concurrent fetcher test failed: {str(e)}")

@router.get("/performance-overview")
async def get_performance_overview(
    current_user = Depends(get_current_user)
):
    """Get comprehensive performance overview including concurrent processing"""
    try:
        # Get concurrent fetcher stats
        concurrent_stats = concurrent_fetcher.get_stats()
        
        # Get connection pool stats
        pool_stats = {}
        pool_health = {}
        if connection_pool_manager.initialized:
            pool_stats = connection_pool_manager.get_all_stats()
            pool_health = await connection_pool_manager.health_check()
        
        # Get scan queue stats
        queue_stats = await scan_queue_manager.get_queue_stats()
        
        # Get system performance metrics
        system_metrics = performance_service.get_system_resource_metrics()
        
        return {
            "concurrent_processing": {
                "fetcher_stats": concurrent_stats,
                "active_requests": len(concurrent_fetcher.active_requests),
                "queue_size": concurrent_fetcher.request_queue.qsize()
            },
            "connection_pools": {
                "initialized": connection_pool_manager.initialized,
                "stats": pool_stats,
                "health": pool_health
            },
            "scan_queue": {
                "running": scan_queue_manager.running,
                "stats": {
                    "total_jobs": queue_stats.total_jobs,
                    "queued_jobs": queue_stats.queued_jobs,
                    "running_jobs": queue_stats.running_jobs,
                    "completed_jobs": queue_stats.completed_jobs,
                    "failed_jobs": queue_stats.failed_jobs,
                    "throughput_per_hour": queue_stats.throughput_per_hour
                }
            },
            "system_resources": system_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance overview: {str(e)}")