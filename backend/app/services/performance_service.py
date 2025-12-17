import gzip
import json
import logging
import time
import asyncio
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from app.services.cache_service import cache_service
from app.database import get_database
from app.core.monitoring import monitoring_system, record_metric, MetricType

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

@dataclass
class APIMetrics:
    """API performance metrics"""
    endpoint: str
    method: str
    response_time_ms: float
    status_code: int
    timestamp: datetime
    user_id: Optional[str] = None
    error: Optional[str] = None

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    operation: str
    collection: str
    duration_ms: float
    timestamp: datetime
    success: bool = True
    error: Optional[str] = None
    query_type: str = "find"

@dataclass
class ScanningMetrics:
    """Scanning operation metrics"""
    scan_id: str
    username: str
    phase: str
    duration_ms: float
    timestamp: datetime
    repositories_processed: int = 0
    success: bool = True
    error: Optional[str] = None

class PerformanceService:
    """Enhanced service for performance monitoring, optimization, and metrics collection"""
    
    def __init__(self):
        # Performance metrics storage
        self.api_metrics: deque = deque(maxlen=10000)
        self.database_metrics: deque = deque(maxlen=10000)
        self.scanning_metrics: deque = deque(maxlen=5000)
        
        # Performance counters
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        
        # Alert thresholds
        self.thresholds = {
            "api_response_time_ms": 5000,
            "database_query_time_ms": 2000,
            "scanning_phase_time_ms": 30000,
            "error_rate_percent": 5,
            "cache_miss_rate_percent": 30
        }
        
        # Performance tracking state
        self.active_operations = {}
        self.performance_alerts = []
    
    # ============ Performance Monitoring Methods ============
    
    def record_api_metric(self, endpoint: str, method: str, response_time_ms: float, 
                         status_code: int, user_id: Optional[str] = None, 
                         error: Optional[str] = None):
        """Record API performance metric"""
        metric = APIMetrics(
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time_ms,
            status_code=status_code,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            error=error
        )
        
        self.api_metrics.append(metric)
        
        # Record in monitoring system
        record_metric(
            "api_response_time",
            response_time_ms,
            MetricType.HISTOGRAM,
            {
                "endpoint": endpoint,
                "method": method,
                "status_code": str(status_code),
                "success": str(error is None)
            },
            "ms"
        )
        
        # Check thresholds
        if response_time_ms > self.thresholds["api_response_time_ms"]:
            self._create_performance_alert(
                "API Response Time Alert",
                f"Endpoint {endpoint} took {response_time_ms}ms (threshold: {self.thresholds['api_response_time_ms']}ms)"
            )
    
    def record_database_metric(self, operation: str, collection: str, duration_ms: float, 
                              success: bool = True, error: Optional[str] = None, 
                              query_type: str = "find"):
        """Record database performance metric"""
        metric = DatabaseMetrics(
            operation=operation,
            collection=collection,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow(),
            success=success,
            error=error,
            query_type=query_type
        )
        
        self.database_metrics.append(metric)
        
        # Record in monitoring system
        record_metric(
            "database_operation_time",
            duration_ms,
            MetricType.HISTOGRAM,
            {
                "operation": operation,
                "collection": collection,
                "query_type": query_type,
                "success": str(success)
            },
            "ms"
        )
        
        # Check thresholds
        if duration_ms > self.thresholds["database_query_time_ms"]:
            self._create_performance_alert(
                "Database Query Performance Alert",
                f"Database {operation} on {collection} took {duration_ms}ms (threshold: {self.thresholds['database_query_time_ms']}ms)"
            )
    
    def record_scanning_metric(self, scan_id: str, username: str, phase: str, 
                              duration_ms: float, repositories_processed: int = 0, 
                              success: bool = True, error: Optional[str] = None):
        """Record scanning operation metric"""
        metric = ScanningMetrics(
            scan_id=scan_id,
            username=username,
            phase=phase,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow(),
            repositories_processed=repositories_processed,
            success=success,
            error=error
        )
        
        self.scanning_metrics.append(metric)
        
        # Record in monitoring system
        record_metric(
            "scanning_operation_time",
            duration_ms,
            MetricType.HISTOGRAM,
            {
                "phase": phase,
                "success": str(success),
                "username": username
            },
            "ms"
        )
        
        # Check thresholds
        if duration_ms > self.thresholds["scanning_phase_time_ms"]:
            self._create_performance_alert(
                "Scanning Performance Alert",
                f"Scanning phase '{phase}' for {username} took {duration_ms}ms (threshold: {self.thresholds['scanning_phase_time_ms']}ms)"
            )
    
    def _create_performance_alert(self, title: str, message: str):
        """Create a performance alert"""
        alert = {
            "id": f"perf_{int(time.time())}",
            "title": title,
            "message": message,
            "timestamp": datetime.utcnow(),
            "level": "warning"
        }
        self.performance_alerts.append(alert)
        logger.warning(f"Performance Alert: {title} - {message}")
    
    # ============ Performance Analysis Methods ============
    
    def get_api_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get API performance summary for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.api_metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"total_requests": 0, "period_hours": hours}
        
        # Calculate statistics
        response_times = [m.response_time_ms for m in recent_metrics]
        error_count = len([m for m in recent_metrics if m.status_code >= 400])
        
        # Group by endpoint
        endpoint_stats = defaultdict(list)
        for metric in recent_metrics:
            endpoint_stats[metric.endpoint].append(metric.response_time_ms)
        
        endpoint_summary = {}
        for endpoint, times in endpoint_stats.items():
            endpoint_summary[endpoint] = {
                "requests": len(times),
                "avg_response_time": sum(times) / len(times),
                "min_response_time": min(times),
                "max_response_time": max(times),
                "p95_response_time": sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times)
            }
        
        return {
            "period_hours": hours,
            "total_requests": len(recent_metrics),
            "error_count": error_count,
            "error_rate": (error_count / len(recent_metrics)) * 100,
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 20 else max(response_times),
            "endpoints": endpoint_summary
        }
    
    def get_database_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get database performance summary for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.database_metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"total_operations": 0, "period_hours": hours}
        
        # Calculate statistics
        durations = [m.duration_ms for m in recent_metrics]
        error_count = len([m for m in recent_metrics if not m.success])
        
        # Group by collection and operation
        collection_stats = defaultdict(lambda: defaultdict(list))
        for metric in recent_metrics:
            collection_stats[metric.collection][metric.operation].append(metric.duration_ms)
        
        collection_summary = {}
        for collection, operations in collection_stats.items():
            operation_summary = {}
            for operation, times in operations.items():
                operation_summary[operation] = {
                    "operations": len(times),
                    "avg_duration": sum(times) / len(times),
                    "min_duration": min(times),
                    "max_duration": max(times)
                }
            collection_summary[collection] = operation_summary
        
        return {
            "period_hours": hours,
            "total_operations": len(recent_metrics),
            "error_count": error_count,
            "error_rate": (error_count / len(recent_metrics)) * 100,
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "collections": collection_summary
        }
    
    def get_scanning_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get scanning performance summary for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.scanning_metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"total_scans": 0, "period_hours": hours}
        
        # Calculate statistics
        durations = [m.duration_ms for m in recent_metrics]
        error_count = len([m for m in recent_metrics if not m.success])
        total_repos_processed = sum(m.repositories_processed for m in recent_metrics)
        
        # Group by phase
        phase_stats = defaultdict(list)
        for metric in recent_metrics:
            phase_stats[metric.phase].append(metric.duration_ms)
        
        phase_summary = {}
        for phase, times in phase_stats.items():
            phase_summary[phase] = {
                "operations": len(times),
                "avg_duration": sum(times) / len(times),
                "min_duration": min(times),
                "max_duration": max(times)
            }
        
        return {
            "period_hours": hours,
            "total_scans": len(recent_metrics),
            "total_repositories_processed": total_repos_processed,
            "error_count": error_count,
            "error_rate": (error_count / len(recent_metrics)) * 100,
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "phases": phase_summary
        }
    
    def get_performance_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance alerts for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            alert for alert in self.performance_alerts 
            if alert["timestamp"] >= cutoff_time
        ]
    
    def get_system_resource_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            import psutil
        except ImportError:
            return {
                "error": "psutil not available - install with: pip install psutil",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "percent": memory_percent,
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3)
                },
                "disk": {
                    "percent": disk_percent,
                    "total_gb": disk.total / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "used_gb": disk.used / (1024**3)
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system resource metrics: {e}")
            return {"error": str(e)}
    
    # ============ Performance Dashboard Methods ============
    
    async def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        try:
            # Get performance summaries
            api_summary = self.get_api_performance_summary(24)
            db_summary = self.get_database_performance_summary(24)
            scanning_summary = self.get_scanning_performance_summary(24)
            
            # Get system metrics
            system_metrics = self.get_system_resource_metrics()
            
            # Get recent alerts
            recent_alerts = self.get_performance_alerts(24)
            
            # Get cache performance
            cache_stats = await cache_service.get_cache_stats()
            
            # Calculate overall health score
            health_score = self._calculate_health_score(api_summary, db_summary, system_metrics)
            
            return {
                "overview": {
                    "health_score": health_score,
                    "status": self._get_system_status(health_score),
                    "timestamp": datetime.utcnow().isoformat()
                },
                "api_performance": api_summary,
                "database_performance": db_summary,
                "scanning_performance": scanning_summary,
                "system_resources": system_metrics,
                "cache_performance": cache_stats,
                "alerts": {
                    "recent_count": len(recent_alerts),
                    "alerts": recent_alerts[:10]  # Last 10 alerts
                }
            }
        except Exception as e:
            logger.error(f"Error getting performance dashboard data: {e}")
            return {"error": str(e)}
    
    def _calculate_health_score(self, api_summary: Dict, db_summary: Dict, system_metrics: Dict) -> float:
        """Calculate overall system health score (0-100)"""
        try:
            score = 100.0
            
            # API performance impact (30% weight)
            if api_summary.get("total_requests", 0) > 0:
                error_rate = api_summary.get("error_rate", 0)
                avg_response_time = api_summary.get("avg_response_time", 0)
                
                # Penalize high error rates
                if error_rate > 5:
                    score -= min(30, error_rate * 2)
                
                # Penalize slow response times
                if avg_response_time > 2000:  # 2 seconds
                    score -= min(20, (avg_response_time - 2000) / 100)
            
            # Database performance impact (25% weight)
            if db_summary.get("total_operations", 0) > 0:
                db_error_rate = db_summary.get("error_rate", 0)
                avg_db_duration = db_summary.get("avg_duration", 0)
                
                # Penalize database errors
                if db_error_rate > 2:
                    score -= min(25, db_error_rate * 3)
                
                # Penalize slow queries
                if avg_db_duration > 1000:  # 1 second
                    score -= min(15, (avg_db_duration - 1000) / 100)
            
            # System resources impact (25% weight)
            if "cpu" in system_metrics:
                cpu_percent = system_metrics["cpu"].get("percent", 0)
                memory_percent = system_metrics["memory"].get("percent", 0)
                
                # Penalize high resource usage
                if cpu_percent > 80:
                    score -= min(15, (cpu_percent - 80) / 2)
                
                if memory_percent > 85:
                    score -= min(15, (memory_percent - 85) / 2)
            
            # Alert impact (20% weight)
            recent_alerts = len(self.get_performance_alerts(1))  # Last hour
            if recent_alerts > 0:
                score -= min(20, recent_alerts * 5)
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 50.0  # Default to moderate health
    
    def _get_system_status(self, health_score: float) -> str:
        """Get system status based on health score"""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 75:
            return "good"
        elif health_score >= 60:
            return "fair"
        elif health_score >= 40:
            return "poor"
        else:
            return "critical"
    
    # ============ Context Managers for Performance Tracking ============
    
    @asynccontextmanager
    async def track_api_performance(self, endpoint: str, method: str, user_id: Optional[str] = None):
        """Context manager to track API performance"""
        start_time = time.time()
        error = None
        status_code = 200
        
        try:
            yield
        except Exception as e:
            error = str(e)
            status_code = 500
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_api_metric(endpoint, method, duration_ms, status_code, user_id, error)
    
    @asynccontextmanager
    async def track_database_performance(self, operation: str, collection: str, query_type: str = "find"):
        """Context manager to track database performance"""
        start_time = time.time()
        error = None
        success = True
        
        try:
            yield
        except Exception as e:
            error = str(e)
            success = False
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_database_metric(operation, collection, duration_ms, success, error, query_type)
    
    @asynccontextmanager
    async def track_scanning_performance(self, scan_id: str, username: str, phase: str):
        """Context manager to track scanning performance"""
        start_time = time.time()
        error = None
        success = True
        repositories_processed = 0
        
        try:
            result = yield
            if hasattr(result, 'repositories_processed'):
                repositories_processed = result.repositories_processed
        except Exception as e:
            error = str(e)
            success = False
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_scanning_metric(scan_id, username, phase, duration_ms, repositories_processed, success, error)
    
    # ============ Response Optimization Methods ============
    
    @staticmethod
    def compress_response(data: Any) -> bytes:
        """Compress response data using gzip"""
        try:
            json_str = json.dumps(data, default=str)
            return gzip.compress(json_str.encode('utf-8'))
        except Exception as e:
            logger.error(f"Response compression error: {e}")
            return json.dumps(data, default=str).encode('utf-8')
    
    @staticmethod
    def decompress_response(compressed_data: bytes) -> Any:
        """Decompress gzip compressed data"""
        try:
            decompressed = gzip.decompress(compressed_data)
            return json.loads(decompressed.decode('utf-8'))
        except Exception as e:
            logger.error(f"Response decompression error: {e}")
            return None
    
    @staticmethod
    async def get_optimized_user_repositories(user_id: str, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """Get user repositories with optimized query and caching"""
        cache_key = f"{user_id}:repos:{limit}:{skip}"
        
        # Try cache first
        try:
            cached_repos = await cache_service.get(cache_key, "user_repos")
            if cached_repos:
                return cached_repos
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        try:
            db = await get_database()
            if not db:
                return []
            
            # Optimized query with projection to reduce data transfer
            repositories = await db.repositories.find(
                {"user_id": user_id},
                {
                    "_id": 1,
                    "name": 1,
                    "full_name": 1,
                    "description": 1,
                    "language": 1,
                    "languages": 1,
                    "stars": 1,
                    "forks": 1,
                    "updated_at": 1,
                    "html_url": 1
                }
            ).sort("updated_at", -1).skip(skip).limit(limit).to_list(None)
            
            # Cache for 15 minutes
            try:
                await cache_service.set(cache_key, repositories, "user_repos", 900)
            except Exception as e:
                logger.warning(f"Cache set failed: {e}")
            
            return repositories
            
        except Exception as e:
            logger.error(f"Error getting optimized user repositories: {e}")
            return []
    
    @staticmethod
    async def get_optimized_user_evaluations(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user evaluations with optimized query and caching"""
        cache_key = f"{user_id}:evaluations:{limit}"
        
        # Try cache first
        try:
            cached_evals = await cache_service.get(cache_key, "user_evaluations")
            if cached_evals:
                return cached_evals
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        try:
            db = await get_database()
            if not db:
                return []
            
            # Optimized query with projection
            evaluations = await db.evaluations.find(
                {"user_id": user_id},
                {
                    "_id": 1,
                    "repo_id": 1,
                    "acid_score": 1,
                    "quality_metrics": 1,
                    "created_at": 1
                }
            ).sort("created_at", -1).limit(limit).to_list(None)
            
            # Cache for 10 minutes
            try:
                await cache_service.set(cache_key, evaluations, "user_evaluations", 600)
            except Exception as e:
                logger.warning(f"Cache set failed: {e}")
            
            return evaluations
            
        except Exception as e:
            logger.error(f"Error getting optimized user evaluations: {e}")
            return []
    
    @staticmethod
    async def get_aggregated_user_stats(user_id: str) -> Dict[str, Any]:
        """Get aggregated user statistics with caching"""
        cache_key = f"{user_id}:stats"
        
        # Try cache first
        cached_stats = await cache_service.get(cache_key, "user_stats")
        if cached_stats:
            return cached_stats
        
        try:
            db = await get_database()
            
            # Use MongoDB aggregation pipeline for better performance
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "total_repos": {"$sum": 1},
                    "avg_score": {"$avg": "$acid_score.overall"},
                    "total_stars": {"$sum": "$stars"},
                    "total_forks": {"$sum": "$forks"},
                    "languages": {"$push": "$language"},
                    "last_updated": {"$max": "$updated_at"}
                }}
            ]
            
            result = await db.repositories.aggregate(pipeline).to_list(None)
            
            if result:
                stats = result[0]
                # Process languages
                language_counts = {}
                for lang in stats.get("languages", []):
                    if lang:
                        language_counts[lang] = language_counts.get(lang, 0) + 1
                
                stats["language_distribution"] = language_counts
                stats.pop("languages", None)  # Remove raw languages array
                stats.pop("_id", None)  # Remove MongoDB _id
                
                # Cache for 20 minutes
                await cache_service.set(cache_key, stats, "user_stats", 1200)
                
                return stats
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting aggregated user stats: {e}")
            return {}
    
    @staticmethod
    async def get_top_developers(limit: int = 50, min_score: float = 0) -> List[Dict[str, Any]]:
        """Get top developers with optimized aggregation query"""
        cache_key = f"top_devs:{limit}:{min_score}"
        
        # Try cache first
        cached_devs = await cache_service.get(cache_key, "top_developers")
        if cached_devs:
            return cached_devs
        
        try:
            db = await get_database()
            
            # Complex aggregation pipeline for top developers
            pipeline = [
                # Join users with their evaluations
                {
                    "$lookup": {
                        "from": "evaluations",
                        "localField": "_id",
                        "foreignField": "user_id",
                        "as": "evaluations"
                    }
                },
                # Filter users with evaluations
                {"$match": {"evaluations": {"$ne": []}}},
                # Add computed fields
                {
                    "$addFields": {
                        "avg_score": {"$avg": "$evaluations.acid_score.overall"},
                        "repo_count": {"$size": "$evaluations"},
                        "total_score": {"$sum": "$evaluations.acid_score.overall"}
                    }
                },
                # Filter by minimum score
                {"$match": {"avg_score": {"$gte": min_score}}},
                # Sort by average score
                {"$sort": {"avg_score": -1}},
                # Limit results
                {"$limit": limit},
                # Project only needed fields
                {
                    "$project": {
                        "_id": 1,
                        "email": 1,
                        "github_username": 1,
                        "avg_score": 1,
                        "repo_count": 1,
                        "last_scan": 1,
                        "created_at": 1
                    }
                }
            ]
            
            developers = await db.users.aggregate(pipeline).to_list(None)
            
            # Cache for 30 minutes
            await cache_service.set(cache_key, developers, "top_developers", 1800)
            
            return developers
            
        except Exception as e:
            logger.error(f"Error getting top developers: {e}")
            return []
    
    @staticmethod
    async def optimize_database_queries():
        """Run database optimization tasks"""
        try:
            db = await get_database()
            
            # Ensure all indexes exist
            await db.users.create_index([("github_username", 1), ("user_type", 1)])
            await db.repositories.create_index([("user_id", 1), ("updated_at", -1)])
            await db.evaluations.create_index([("user_id", 1), ("created_at", -1)])
            await db.evaluations.create_index([("acid_score.overall", -1)])
            
            # Create compound indexes for common queries
            await db.repositories.create_index([
                ("user_id", 1), 
                ("language", 1), 
                ("stars", -1)
            ])
            
            await db.evaluations.create_index([
                ("user_id", 1), 
                ("acid_score.overall", -1), 
                ("created_at", -1)
            ])
            
            logger.info("Database optimization completed")
            
        except Exception as e:
            logger.error(f"Database optimization error: {e}")
    
    @staticmethod
    async def get_performance_metrics() -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            db = await get_database()
            
            # Database stats
            db_stats = await db.command("dbStats")
            
            # Collection stats
            collections_stats = {}
            for collection_name in ["users", "repositories", "evaluations", "hr_users"]:
                try:
                    stats = await db.command("collStats", collection_name)
                    collections_stats[collection_name] = {
                        "count": stats.get("count", 0),
                        "size": stats.get("size", 0),
                        "avgObjSize": stats.get("avgObjSize", 0),
                        "indexSizes": stats.get("indexSizes", {})
                    }
                except:
                    collections_stats[collection_name] = {"error": "Stats not available"}
            
            # Cache stats
            cache_stats = await cache_service.get_cache_stats()
            
            return {
                "database": {
                    "dataSize": db_stats.get("dataSize", 0),
                    "indexSize": db_stats.get("indexSize", 0),
                    "collections": db_stats.get("collections", 0),
                    "objects": db_stats.get("objects", 0)
                },
                "collections": collections_stats,
                "cache": cache_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}

# Global performance service instance
performance_service = PerformanceService()