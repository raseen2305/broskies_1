"""
Database Initialization and Health Check System
Provides comprehensive startup verification, health monitoring, and schema validation
for the multi-database architecture
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from app.db_connection_multi import (
    multi_db_manager, DatabaseType, 
    initialize_multi_database_connections,
    get_multi_database_health
)
from app.services.error_diagnostic_system import (
    error_diagnostic_system, OperationType, ErrorSeverity
)

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

class DatabaseInitializationSystem:
    """Comprehensive database initialization and health monitoring system"""
    
    def __init__(self):
        self.initialization_complete = False
        self.initialization_start_time: Optional[float] = None
        self.initialization_results: Dict[str, Any] = {}
        self.health_check_cache: Dict[str, Any] = {}
        self.health_check_cache_ttl = 30  # 30 seconds cache
        self.last_health_check = 0
        
        # Expected collections for each database type
        self.expected_collections = {
            DatabaseType.EXTERNAL_USERS: [
                "external_user_profiles", "external_scan_cache", 
                "external_repositories", "external_analysis_results"
            ],
            DatabaseType.RASEEN_TEMP_USER: [
                "internal_user_profiles", "internal_scan_cache",
                "internal_repositories", "internal_analysis_results"
            ],
            DatabaseType.RASEEN_MAIN_USER: [
                "internal_user_profiles", "internal_scan_cache",
                "internal_repositories", "internal_analysis_results",
                "user_rankings", "user_statistics"
            ],
            DatabaseType.RASEEN_MAIN_HR: [
                "hr_candidates", "hr_evaluations", "hr_reports"
            ],
            DatabaseType.SRIE_MAIN_USER: [
                "internal_user_profiles", "internal_scan_cache",
                "internal_repositories", "internal_analysis_results",
                "user_rankings", "user_statistics"
            ],
            DatabaseType.SRIE_MAIN_HR: [
                "hr_candidates", "hr_evaluations", "hr_reports"
            ]
        }
        
        # Required indexes for each collection
        self.required_indexes = {
            "external_user_profiles": [
                {"key": "user_id", "unique": True},
                {"key": "github_username", "unique": True},
                {"key": "created_at"}
            ],
            "internal_user_profiles": [
                {"key": "user_id", "unique": True},
                {"key": "github_username", "unique": True},
                {"key": "email", "unique": True},
                {"key": "created_at"}
            ],
            "external_scan_cache": [
                {"key": "user_id"},
                {"key": "scan_id", "unique": True},
                {"key": "created_at"}
            ],
            "internal_scan_cache": [
                {"key": "user_id"},
                {"key": "scan_id", "unique": True},
                {"key": "created_at"}
            ],
            "external_repositories": [
                {"key": "user_id"},
                {"key": "repo_name"},
                {"key": "full_name", "unique": True}
            ],
            "internal_repositories": [
                {"key": "user_id"},
                {"key": "repo_name"},
                {"key": "full_name", "unique": True}
            ],
            "user_rankings": [
                {"key": "user_id", "unique": True},
                {"key": "overall_score"},
                {"key": "regional_rank"},
                {"key": "university_rank"}
            ],
            "hr_candidates": [
                {"key": "candidate_id", "unique": True},
                {"key": "email", "unique": True},
                {"key": "github_username"}
            ]
        }

    async def initialize_database_system(self) -> Dict[str, Any]:
        """
        Complete database system initialization with comprehensive verification
        
        Returns:
            Dict containing initialization results and status
        """
        logger.info("🚀 Starting comprehensive database system initialization...")
        self.initialization_start_time = time.time()
        
        try:
            # Step 1: Initialize all database connections
            connection_results = await self._initialize_connections()
            
            # Step 2: Verify database connectivity
            connectivity_results = await self._verify_connectivity()
            
            # Step 3: Validate database schemas
            schema_results = await self._validate_schemas()
            
            # Step 4: Create required indexes
            index_results = await self._ensure_indexes()
            
            # Step 5: Perform health checks
            health_results = await self._perform_initial_health_checks()
            
            # Compile final results
            initialization_time = time.time() - self.initialization_start_time
            
            self.initialization_results = {
                "success": True,
                "initialization_time": round(initialization_time, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "connection_results": connection_results,
                "connectivity_results": connectivity_results,
                "schema_results": schema_results,
                "index_results": index_results,
                "health_results": health_results,
                "overall_status": self._determine_overall_status(
                    connection_results, connectivity_results, 
                    schema_results, index_results, health_results
                )
            }
            
            self.initialization_complete = True
            
            logger.info(f"✅ Database system initialization completed in {initialization_time:.2f}s")
            logger.info(f"📊 Overall Status: {self.initialization_results['overall_status']}")
            
            return self.initialization_results
            
        except Exception as e:
            initialization_time = time.time() - self.initialization_start_time
            
            error_diagnostic_system.log_error(
                operation_type=OperationType.CONNECT,
                database_name="system_initialization",
                error_message=f"Database system initialization failed: {str(e)}",
                severity=ErrorSeverity.CRITICAL,
                context={"initialization_time": initialization_time}
            )
            
            self.initialization_results = {
                "success": False,
                "error": str(e),
                "initialization_time": round(initialization_time, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.error(f"❌ Database system initialization failed after {initialization_time:.2f}s: {e}")
            raise

    async def _initialize_connections(self) -> Dict[str, Any]:
        """Initialize connections to all seven databases"""
        logger.info("🔗 Initializing database connections...")
        
        try:
            connection_results = await initialize_multi_database_connections()
            
            successful_connections = sum(1 for status in connection_results.values() if "✅" in status)
            total_connections = len(connection_results)
            
            return {
                "success": successful_connections == total_connections,
                "successful_connections": successful_connections,
                "total_connections": total_connections,
                "connection_details": connection_results
            }
            
        except Exception as e:
            logger.error(f"❌ Connection initialization failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "successful_connections": 0,
                "total_connections": len(DatabaseType)
            }

    async def _verify_connectivity(self) -> Dict[str, Any]:
        """Verify connectivity to all databases with ping tests"""
        logger.info("🏓 Verifying database connectivity...")
        
        connectivity_results = {}
        successful_pings = 0
        
        for db_type in DatabaseType:
            try:
                database = await multi_db_manager.get_database(db_type)
                if database is None:
                    connectivity_results[db_type.value] = {
                        "success": False,
                        "error": "Database connection not available"
                    }
                    continue
                
                # Perform ping test with timeout
                start_time = time.time()
                await asyncio.wait_for(
                    database.command('ping'),
                    timeout=5.0
                )
                ping_time = time.time() - start_time
                
                connectivity_results[db_type.value] = {
                    "success": True,
                    "ping_time": round(ping_time * 1000, 2)  # Convert to milliseconds
                }
                successful_pings += 1
                
            except Exception as e:
                connectivity_results[db_type.value] = {
                    "success": False,
                    "error": str(e)
                }
                
                error_diagnostic_system.log_error(
                    operation_type=OperationType.CONNECT,
                    database_name=db_type.value,
                    error_message=f"Connectivity verification failed: {str(e)}",
                    severity=ErrorSeverity.HIGH
                )
        
        return {
            "success": successful_pings == len(DatabaseType),
            "successful_pings": successful_pings,
            "total_databases": len(DatabaseType),
            "ping_results": connectivity_results
        }

    async def _validate_schemas(self) -> Dict[str, Any]:
        """Validate database schemas and collections"""
        logger.info("📋 Validating database schemas...")
        
        schema_results = {}
        successful_validations = 0
        
        for db_type in DatabaseType:
            try:
                database = await multi_db_manager.get_database(db_type)
                if database is None:
                    schema_results[db_type.value] = {
                        "success": False,
                        "error": "Database not available"
                    }
                    continue
                
                # Get existing collections
                existing_collections = await database.list_collection_names()
                expected_collections = self.expected_collections.get(db_type, [])
                
                # Check which collections exist vs expected
                missing_collections = [
                    col for col in expected_collections 
                    if col not in existing_collections
                ]
                
                # Create missing collections (they'll be created on first insert)
                collection_status = {}
                for collection_name in expected_collections:
                    if collection_name in existing_collections:
                        collection_status[collection_name] = "exists"
                    else:
                        collection_status[collection_name] = "will_be_created_on_use"
                
                schema_results[db_type.value] = {
                    "success": True,
                    "existing_collections": len(existing_collections),
                    "expected_collections": len(expected_collections),
                    "missing_collections": missing_collections,
                    "collection_status": collection_status
                }
                successful_validations += 1
                
            except Exception as e:
                schema_results[db_type.value] = {
                    "success": False,
                    "error": str(e)
                }
                
                error_diagnostic_system.log_error(
                    operation_type=OperationType.FETCH,
                    database_name=db_type.value,
                    error_message=f"Schema validation failed: {str(e)}",
                    severity=ErrorSeverity.MEDIUM
                )
        
        return {
            "success": successful_validations == len(DatabaseType),
            "successful_validations": successful_validations,
            "total_databases": len(DatabaseType),
            "schema_details": schema_results
        }

    async def _ensure_indexes(self) -> Dict[str, Any]:
        """Ensure required indexes exist on all collections"""
        logger.info("🔍 Ensuring database indexes...")
        
        index_results = {}
        successful_index_operations = 0
        
        for db_type in DatabaseType:
            try:
                database = await multi_db_manager.get_database(db_type)
                if database is None:
                    index_results[db_type.value] = {
                        "success": False,
                        "error": "Database not available"
                    }
                    continue
                
                db_index_results = {}
                expected_collections = self.expected_collections.get(db_type, [])
                
                for collection_name in expected_collections:
                    collection = database[collection_name]
                    required_indexes = self.required_indexes.get(collection_name, [])
                    
                    collection_index_results = {
                        "created": [],
                        "existing": [],
                        "errors": []
                    }
                    
                    # Get existing indexes
                    try:
                        existing_indexes = await collection.list_indexes().to_list(length=None)
                        existing_index_keys = [
                            list(idx.get('key', {}).keys()) for idx in existing_indexes
                        ]
                    except:
                        existing_index_keys = []
                    
                    # Create required indexes
                    for index_spec in required_indexes:
                        try:
                            index_key = index_spec['key']
                            index_options = {k: v for k, v in index_spec.items() if k != 'key'}
                            
                            # Check if index already exists
                            if [index_key] in existing_index_keys:
                                collection_index_results["existing"].append(index_key)
                                continue
                            
                            # Create the index
                            await collection.create_index(index_key, **index_options)
                            collection_index_results["created"].append(index_key)
                            
                        except Exception as idx_error:
                            collection_index_results["errors"].append({
                                "index": index_key,
                                "error": str(idx_error)
                            })
                    
                    db_index_results[collection_name] = collection_index_results
                
                index_results[db_type.value] = {
                    "success": True,
                    "collections": db_index_results
                }
                successful_index_operations += 1
                
            except Exception as e:
                index_results[db_type.value] = {
                    "success": False,
                    "error": str(e)
                }
                
                error_diagnostic_system.log_error(
                    operation_type=OperationType.UPDATE,
                    database_name=db_type.value,
                    error_message=f"Index creation failed: {str(e)}",
                    severity=ErrorSeverity.MEDIUM
                )
        
        return {
            "success": successful_index_operations == len(DatabaseType),
            "successful_operations": successful_index_operations,
            "total_databases": len(DatabaseType),
            "index_details": index_results
        }

    async def _perform_initial_health_checks(self) -> Dict[str, Any]:
        """Perform comprehensive initial health checks"""
        logger.info("🏥 Performing initial health checks...")
        
        try:
            health_status = await get_multi_database_health()
            
            # Add additional health metrics
            health_status["initialization_context"] = True
            health_status["error_statistics"] = error_diagnostic_system.get_error_statistics(hours=1)
            
            return {
                "success": health_status.get("overall_healthy", False),
                "health_details": health_status
            }
            
        except Exception as e:
            logger.error(f"❌ Initial health check failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _determine_overall_status(self, connection_results: Dict, connectivity_results: Dict,
                                schema_results: Dict, index_results: Dict, 
                                health_results: Dict) -> str:
        """Determine overall system status based on all initialization results"""
        
        # Critical: All connections must be successful
        if not connection_results.get("success", False):
            return HealthStatus.CRITICAL.value
        
        # High priority: Connectivity must work
        if not connectivity_results.get("success", False):
            return HealthStatus.UNHEALTHY.value
        
        # Medium priority: Schema and indexes
        schema_success = schema_results.get("success", False)
        index_success = index_results.get("success", False)
        health_success = health_results.get("success", False)
        
        if schema_success and index_success and health_success:
            return HealthStatus.HEALTHY.value
        elif schema_success and (index_success or health_success):
            return HealthStatus.DEGRADED.value
        else:
            return HealthStatus.UNHEALTHY.value

    async def get_health_check(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive health check with caching
        
        Args:
            force_refresh: Force refresh of cached health data
            
        Returns:
            Dict containing comprehensive health information
        """
        current_time = time.time()
        
        # Return cached result if still valid and not forcing refresh
        if (not force_refresh and 
            self.health_check_cache and 
            current_time - self.last_health_check < self.health_check_cache_ttl):
            return self.health_check_cache
        
        logger.debug("🔍 Performing health check...")
        
        try:
            # Get multi-database health status
            db_health = await get_multi_database_health()
            
            # Get error statistics
            error_stats = error_diagnostic_system.get_error_statistics(hours=1)
            
            # Get database health summary
            db_health_summary = error_diagnostic_system.get_database_health_summary()
            
            # Compile comprehensive health check
            health_check = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": self._determine_health_status(db_health, error_stats),
                "initialization_complete": self.initialization_complete,
                "database_connectivity": db_health,
                "error_statistics": error_stats,
                "operation_health": db_health_summary,
                "system_metrics": {
                    "uptime_seconds": current_time - (self.initialization_start_time or current_time),
                    "total_databases": len(DatabaseType),
                    "healthy_databases": sum(
                        1 for db_status in db_health.get("databases", {}).values()
                        if db_status.get("connected", False)
                    )
                }
            }
            
            # Add initialization results if available
            if self.initialization_results:
                health_check["initialization_results"] = self.initialization_results
            
            # Cache the results
            self.health_check_cache = health_check
            self.last_health_check = current_time
            
            return health_check
            
        except Exception as e:
            error_diagnostic_system.log_error(
                operation_type=OperationType.FETCH,
                database_name="health_check_system",
                error_message=f"Health check failed: {str(e)}",
                severity=ErrorSeverity.HIGH
            )
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": HealthStatus.CRITICAL.value,
                "error": str(e),
                "initialization_complete": self.initialization_complete
            }

    def _determine_health_status(self, db_health: Dict, error_stats: Dict) -> str:
        """Determine overall health status based on database health and error statistics"""
        
        # Check database connectivity
        total_dbs = len(DatabaseType)
        healthy_dbs = sum(
            1 for db_status in db_health.get("databases", {}).values()
            if db_status.get("connected", False)
        )
        
        # Check recent errors
        critical_errors = error_stats.get("severity_counts", {}).get("critical", 0)
        total_recent_errors = error_stats.get("total_errors", 0)
        
        # Determine status
        if healthy_dbs == total_dbs and critical_errors == 0:
            if total_recent_errors <= 5:  # Allow some minor errors
                return HealthStatus.HEALTHY.value
            else:
                return HealthStatus.DEGRADED.value
        elif healthy_dbs >= total_dbs * 0.8:  # 80% of databases healthy
            return HealthStatus.DEGRADED.value
        elif healthy_dbs >= total_dbs * 0.5:  # 50% of databases healthy
            return HealthStatus.UNHEALTHY.value
        else:
            return HealthStatus.CRITICAL.value

    async def get_database_status(self, database_name: str) -> Dict[str, Any]:
        """Get detailed status for a specific database"""
        
        # Find the database type
        db_type = None
        for dt in DatabaseType:
            if dt.value == database_name:
                db_type = dt
                break
        
        if db_type is None:
            return {
                "error": f"Database '{database_name}' not found",
                "available_databases": [dt.value for dt in DatabaseType]
            }
        
        try:
            database = await multi_db_manager.get_database(db_type)
            
            if database is None:
                return {
                    "database_name": database_name,
                    "status": "unavailable",
                    "error": "Database connection not available"
                }
            
            # Perform detailed checks
            start_time = time.time()
            
            # Ping test
            await database.command('ping')
            ping_time = time.time() - start_time
            
            # Collection count
            collections = await database.list_collection_names()
            
            # Get recent operations stats for this database
            error_stats = error_diagnostic_system.get_error_statistics(hours=24)
            db_errors = [
                error for error in error_stats.get("most_recent_errors", [])
                if error.get("database_name") == database_name
            ]
            
            return {
                "database_name": database_name,
                "status": "healthy",
                "ping_time_ms": round(ping_time * 1000, 2),
                "collections_count": len(collections),
                "collections": collections,
                "recent_errors_24h": len(db_errors),
                "last_activity": multi_db_manager.last_activity.get(db_type, 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "database_name": database_name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global instance
database_init_system = DatabaseInitializationSystem()

# Convenience functions
async def initialize_database_system() -> Dict[str, Any]:
    """Initialize the complete database system"""
    return await database_init_system.initialize_database_system()

async def get_system_health_check(force_refresh: bool = False) -> Dict[str, Any]:
    """Get comprehensive system health check"""
    return await database_init_system.get_health_check(force_refresh)

async def get_database_status(database_name: str) -> Dict[str, Any]:
    """Get status for a specific database"""
    return await database_init_system.get_database_status(database_name)

def is_system_initialized() -> bool:
    """Check if the database system has been initialized"""
    return database_init_system.initialization_complete