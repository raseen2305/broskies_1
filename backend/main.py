from fastapi import FastAPI, HTTPException, Depends, WebSocket, Query, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import asyncio
import logging
import os
import uuid
from dotenv import load_dotenv

# Legacy database imports removed - using multi-database system
from app.routers import auth, scan, evaluation, performance, security, scan_simple, test_endpoint, profile, fast_scan, rankings
from app.routers import rankings_enhanced, debug_rankings, debug_users
from app.routers import quick_scan, deep_analysis, analytics_api
from app.api import debug
from app.core.config import settings, validate_configuration
from app.core.middleware import RateLimitMiddleware, SecurityValidationMiddleware, RequestLoggingMiddleware
from app.core.error_handler import (
    application_error_handler, http_exception_handler, validation_exception_handler,
    general_exception_handler, ApplicationError
)
from app.core.logging_config import setup_logging
from app.core.monitoring import monitoring_system, record_response_time, record_error
from app.websocket.scan_websocket import websocket_endpoint
from app.services.performance_service import performance_service
from app.services.concurrent_data_fetcher import initialize_concurrent_fetcher, shutdown_concurrent_fetcher
from app.services.connection_pool_manager import initialize_connection_pools, shutdown_connection_pools
from app.services.scan_queue_manager import initialize_scan_queue, shutdown_scan_queue

load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Validate configuration first
    validate_configuration()
    
    # Setup logging with configuration values
    setup_logging(
        log_level=settings.log_level,
        log_file=os.getenv("LOG_FILE", "logs/app.log"),
        enable_json_logging=settings.json_logging,
        enable_console_logging=True
    )
    
    # Local development environment - initialize all services
    logger.info("🚀 Initializing services for local development...")
    
    # Initialize multi-database system with comprehensive health checks
    try:
        logger.info("🔗 Initializing single database system: Broskies Hub")
        from app.database.connection import db_manager
        await db_manager.connect_to_database()
        # await asyncio.wait_for(initialize_database_system(), timeout=60.0)
        from app.services.cache_service import cache_service
        await cache_service.connect()
        # await asyncio.wait_for(initialize_connection_pools(multi_db_manager, settings), timeout=15.0)
    except asyncio.TimeoutError:
        logger.error("❌ Application cannot start without database connections")
        raise Exception("Database initialization timeout - check network connectivity and database URLs")
    except Exception as e:
        logger.error(f"❌ Multi-database system initialization failed: {e}")
        logger.error("❌ Application cannot start without database connections")
        raise Exception(f"Database initialization failed: {e}")
    
    # Initialize connection pools with timeout protection
    try:
        await asyncio.wait_for(
            initialize_connection_pools(
                mongo_connection_string=settings.mongodb_url,
                mongo_database=settings.database_name,
                redis_url=settings.redis_url,
                http_max_connections=50  # Standard connection pool size for local dev
            ),
            timeout=15.0
        )
    except asyncio.TimeoutError:
        logger.warning("Connection pool initialization timed out, continuing with limited functionality")
    except Exception as e:
        logger.warning(f"Connection pool initialization failed: {e}, continuing with limited functionality")
    
    # Initialize concurrent data fetcher with timeout protection
    try:
        await asyncio.wait_for(initialize_concurrent_fetcher(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("Concurrent data fetcher initialization timed out")
    
    # Initialize scan queue manager with timeout protection
    try:
        await asyncio.wait_for(initialize_scan_queue(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("Scan queue manager initialization timed out")
    
    # Start background services (monitoring, optimization, etc.)
    asyncio.create_task(_initialize_background_services())
    
    # Setup health checks (register only, don't run immediately)
    setup_health_checks()
    
    logger.info("✅ Core services initialized - API ready to accept requests")
    
    yield
    
    # Shutdown
    await shutdown_scan_queue()
    await shutdown_connection_pools()
    await shutdown_concurrent_fetcher()
    await monitoring_system.stop_monitoring()
    
    # Disconnect cache service
    try:
        from app.services.cache_service import cache_service
        await cache_service.disconnect()
    except Exception as e:
        logger.warning(f"Cache service shutdown failed: {e}")
    
    # Close multi-database connections
    try:
        from app.database.connection import db_manager
        await db_manager.close_database_connection()
        logger.info("✅ Multi-database connections closed")
    except Exception as e:
        logger.warning(f"Multi-database shutdown failed: {e}")
    
    # Legacy database connection handling removed - using multi-database system

app = FastAPI(
    title="BroskiesHub API",
    description="API for analyzing GitHub repositories and evaluating code quality",
    version="1.0.0",
    lifespan=lifespan
)

# Optimized: Add request ID middleware with minimal overhead
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response

# Optimized: Add response caching for static/slow endpoints
@app.middleware("http")
async def cache_static_responses(request: Request, call_next):
    """Cache responses for static endpoints to reduce database load"""
    # Only cache GET requests
    if request.method != "GET":
        return await call_next(request)
    
    # Define cacheable endpoints (static data that doesn't change often)
    cacheable_paths = [
        "/profile/data/universities",
        "/profile/data/countries",
        "/profile/data/states",
        "/health"
    ]
    
    # Check if this is a cacheable endpoint
    is_cacheable = any(request.url.path.endswith(path) for path in cacheable_paths)
    
    if is_cacheable:
        # Add cache control headers
        response = await call_next(request)
        response.headers["Cache-Control"] = "public, max-age=3600"  # Cache for 1 hour
        response.headers["X-Cache-Status"] = "CACHEABLE"
        return response
    
    return await call_next(request)

# Add response time monitoring middleware
@app.middleware("http")
async def monitor_response_time(request: Request, call_next):
    """Monitor API response times"""
    import time
    
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    
    # Record response time metric
    record_response_time(
        endpoint=request.url.path,
        duration_ms=duration_ms,
        status_code=response.status_code
    )
    
    return response

# Add error handlers
app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# CORS middleware - Must be added FIRST to handle preflight requests
def get_allowed_origins():
    """Get allowed origins based on environment"""
    # Base development origins
    origins = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:3001",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173",   # Vite default port
        "http://localhost:8080",   # Alternative dev port
        "http://127.0.0.1:8080",
    ]
    
    # Add configured frontend URL
    frontend_url = settings.get_frontend_url()
    if frontend_url not in origins:
        origins.append(frontend_url)
    
    # Add any additional CORS origins from configuration
    if settings.cors_origins:
        origins.extend(settings.cors_origins)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_origins = []
    for origin in origins:
        if origin not in seen:
            seen.add(origin)
            unique_origins.append(origin)
    
    return unique_origins

# Get allowed origins
allowed_origins = get_allowed_origins()

# Add CORS middleware with enhanced configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Use configured origins for local development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language", 
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID",
        "Cache-Control",
        "Pragma",
        "Expires"
    ],
    expose_headers=["X-Request-ID", "X-Total-Count", "X-Page-Count"],
    max_age=86400,  # 24 hours for preflight cache
)

# CORS debugging middleware (add after CORS)
@app.middleware("http")
async def cors_debug_middleware(request: Request, call_next):
    """Middleware to log CORS-related information for debugging"""
    origin = request.headers.get("origin")
    method = request.method
    
    # Log CORS requests for debugging
    if origin and method == "OPTIONS":
        logger = logging.getLogger("cors")
        logger.info(f"CORS preflight request from origin: {origin}")
        logger.info(f"Request headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    # Log CORS response headers
    if origin:
        logger = logging.getLogger("cors")
        cors_headers = {k: v for k, v in response.headers.items() if k.lower().startswith("access-control")}
        if cors_headers:
            logger.info(f"CORS response headers for {origin}: {cors_headers}")
    
    return response

# Security and logging middleware (add after CORS)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityValidationMiddleware)

# Response compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Enhanced rate limiting middleware (configurable)
if settings.rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware, default_requests_per_minute=settings.rate_limit_requests_per_minute)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(scan.router, prefix="/scan", tags=["scanning"])
app.include_router(scan_simple.router, prefix="/scan", tags=["scanning"])
app.include_router(test_endpoint.router, prefix="/test", tags=["testing"])
app.include_router(evaluation.router, prefix="/evaluation", tags=["evaluation"])
app.include_router(performance.router, prefix="/performance", tags=["performance"])
app.include_router(security.router, prefix="/security", tags=["security"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
app.include_router(rankings_enhanced.router, prefix="/rankings/v2", tags=["rankings-enhanced"])
app.include_router(debug_rankings.router, prefix="/debug/rankings", tags=["debug-rankings"])
app.include_router(debug_users.router, prefix="/debug/users", tags=["debug-users"])
app.include_router(fast_scan.router, prefix="/scan", tags=["fast-scan"])
app.include_router(debug.router, prefix="/debug", tags=["debug"])

# New scoring system routers
app.include_router(quick_scan.router, tags=["quick-scan"])
app.include_router(deep_analysis.router, tags=["deep-analysis"])
app.include_router(analytics_api.router, tags=["analytics"])

# HR Dashboard routers
from app.routers import hr_auth, hr_candidates, hr_admin
app.include_router(hr_auth.router, tags=["hr-authentication"])
app.include_router(hr_candidates.router, tags=["hr-candidates"])
app.include_router(hr_admin.router, tags=["hr-admin"])

# Import and include scores router
from app.routers import scores
app.include_router(scores.router, tags=["scores"])

# Import and include health monitoring router
from app.routers import health
app.include_router(health.router, tags=["health-monitoring"])

# WebSocket endpoint for real-time scan progress
@app.websocket("/ws/scan-progress")
async def websocket_scan_progress(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time scan progress updates"""
    await websocket_endpoint(websocket, token)

@app.get("/")
async def root():
    return {"message": "BroskiesHub API", "version": "1.0.0"}

@app.options("/{path:path}")
async def options_handler(request: Request):
    """CORS preflight handler for local development"""
    origin = request.headers.get("origin")
    allowed_origins = get_allowed_origins()
    
    # Use the origin if it's in allowed list, otherwise use wildcard
    allowed_origin = origin if origin in allowed_origins else "*"
    
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, X-Request-ID, Cache-Control, Pragma, Expires",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",
            "Access-Control-Expose-Headers": "X-Request-ID, X-Total-Count, X-Page-Count"
        }
    )

async def _initialize_background_services():
    """Initialize non-critical background services after app startup"""
    try:
        logger.info("Initializing background services...")
        
        # Start monitoring system (non-blocking)
        await monitoring_system.start_monitoring()
        logger.info("✅ Monitoring system started")
        
        # Database optimization disabled - method doesn't exist
        # await asyncio.sleep(10)
        # await performance_service.optimize_database_queries()
        # logger.info("✅ Database optimization completed")
        
    except Exception as e:
        logger.error(f"Error initializing background services: {e}")
        # Don't fail startup if background services fail

def setup_health_checks():
    """Setup health checks for system components"""
    from app.services.cache_service import cache_service
    
    async def database_health_check():
        """Check multi-database connectivity"""
        try:
            from app.services.database_initialization import get_system_health_check
            health_data = await get_system_health_check(force_refresh=False)
            
            overall_status = health_data.get("overall_status", "unknown")
            healthy_dbs = health_data.get("system_metrics", {}).get("healthy_databases", 0)
            total_dbs = health_data.get("system_metrics", {}).get("total_databases", 0)
            
            if overall_status == "healthy":
                return {
                    "healthy": True, 
                    "message": f"Multi-database system healthy ({healthy_dbs}/{total_dbs} databases connected)"
                }
            else:
                return {
                    "healthy": False, 
                    "message": f"Multi-database system {overall_status} ({healthy_dbs}/{total_dbs} databases connected)"
                }
        except Exception as e:
            return {"healthy": False, "message": f"Multi-database system error: {str(e)}"}
    
    async def cache_health_check():
        """Check cache connectivity"""
        try:
            stats = await cache_service.get_cache_stats()
            if stats.get("connected", False):
                return {"healthy": True, "message": "Cache connection successful", "stats": stats}
            else:
                return {"healthy": False, "message": "Cache not connected"}
        except Exception as e:
            return {"healthy": False, "message": f"Cache error: {str(e)}"}
    
    async def github_api_health_check():
        """Check GitHub API connectivity"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get("https://api.github.com/rate_limit")
                if response.status_code == 200:
                    return {"healthy": True, "message": "GitHub API accessible"}
                else:
                    return {"healthy": False, "message": f"GitHub API returned {response.status_code}"}
        except Exception as e:
            return {"healthy": False, "message": f"GitHub API error: {str(e)}"}
    
    # Add health checks to monitoring system
    monitoring_system.add_health_check("database", database_health_check, interval=60)
    monitoring_system.add_health_check("cache", cache_health_check, interval=60)
    monitoring_system.add_health_check("github_api", github_api_health_check, interval=300)  # 5 minutes

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        system_status = monitoring_system.get_system_status()
        
        # Simple health check for basic endpoint
        if system_status["status"] in ["healthy", "warning"]:
            return {"status": "healthy", "timestamp": system_status["timestamp"]}
        else:
            return {"status": "unhealthy", "timestamp": system_status["timestamp"]}
    except Exception:
        return {"status": "unknown"}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with full system status"""
    return monitoring_system.get_system_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )