"""
Quick Scan Router
API endpoints for Stage 1 quick scan functionality
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.core.security import get_current_user_token
from app.user_type_detector import UserTypeDetector, detect_user_type_from_request, get_user_database
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scan", tags=["quick-scan"])


class QuickScanRequest(BaseModel):
    """Request model for quick scan"""
    github_username: Optional[str] = Field(
        None,
        description="GitHub username to scan (optional, defaults to authenticated user)"
    )


class RepositorySummary(BaseModel):
    """Summary of a repository from quick scan"""
    id: str
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    forks: int
    importance_score: float
    category: str  # flagship, significant, supporting


class QuickScanResponse(BaseModel):
    """Response model for quick scan"""
    success: bool
    username: str
    user_profile: Dict[str, Any]
    repositories: List[RepositorySummary]
    summary: Dict[str, int]
    scan_time: float
    message: str


async def get_current_user(
    current_user_token: dict = Depends(get_current_user_token),
    request: Request = None
) -> User:
    """Get current authenticated user using new database architecture"""
    try:
        user_id = current_user_token["user_id"]
        user_type = current_user_token["user_type"]
        
        if user_type == "developer":
            try:
                # Use new database routing system
                db = await get_user_database(request, "user_data") if request else None
                if db is not None:
                    user_doc = await db.users.find_one({"_id": user_id})
                    if user_doc:
                        return User(**user_doc)
            except Exception as e:
                logger.warning(f"🔐 [DATABASE_ROUTING] Database query failed: {e}")
        
        raise HTTPException(
            status_code=401,
            detail="Unable to authenticate user"
        )
    except KeyError as e:
        logger.error(f"Missing required token field: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Invalid token format: missing {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/quick-scan")
async def quick_scan(
    scan_request: QuickScanRequest,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Execute Stage 1 quick scan for INTERNAL USERS (Authenticated)
    
    Performs:
    1. OAuth token validation
    2. GraphQL query for user + repositories
    3. Parallel importance calculation
    4. Repository categorization
    5. Database storage in INTERNAL database
    
    Target: <1 second execution time
    
    Requirements: 1, 2, 5
    
    Response format matches fast_scan for frontend compatibility
    """
    import time
    start_time = time.time()
    
    try:
        # ============================================================================
        # INTERNAL USER DIFFERENTIATION - Enhanced Logging & Validation
        # ============================================================================
        
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] ========================================")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] AUTHENTICATED USER SCAN INITIATED")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] User ID: {current_user.id}")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] User Type: {current_user.user_type}")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] Email: {current_user.email}")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] GitHub Username: {current_user.github_username}")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] Database Target: INTERNAL_DB")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] Storage Prefix: internal_{current_user.id}")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] ========================================")
        
        # Validate OAuth token
        if not current_user.github_token:
            logger.error(f"🔐 [INTERNAL_QUICK_SCAN] ❌ No GitHub token for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub OAuth token not found. Please reconnect your GitHub account."
            )
        
        # Determine username to scan
        username = scan_request.github_username or current_user.github_username
        
        if not username:
            logger.error(f"🔐 [INTERNAL_QUICK_SCAN] ❌ No GitHub username for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub username is required"
            )
        
        # Additional internal user validation
        if username != current_user.github_username and scan_request.github_username:
            logger.warning(f"🔐 [INTERNAL_QUICK_SCAN] ⚠️ User {current_user.id} scanning different username: {username}")
        
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] Target Username: {username}")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] Starting INTERNAL scan for user: {username}")
        
        # ============================================================================
        # NEW DATABASE ROUTING SYSTEM
        # ============================================================================
        
        # Get routing information using new system
        routing_info = await UserTypeDetector.route_user_operation(request, username, "quick_scan")
        
        user_type = routing_info["user_type"]
        user_id = routing_info["user_id"] 
        database = routing_info["database"]
        scan_collection = routing_info["scan_collection"]
        storage_location = routing_info["storage_location"]
        
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] User Type: {user_type}")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] User ID: {user_id}")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] Database: {storage_location}")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] Collection: {scan_collection}")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] Data Isolation: ENABLED")
        
        # Initialize scan orchestrator with internal user context
        from backend.scoring.orchestration.scan_orchestrator import ScanOrchestrator
        
        orchestrator = ScanOrchestrator(database=db, logger=logger)
        
        # Execute quick scan with new database routing
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] Executing orchestrator with new routing...")
        result = await orchestrator.execute_quick_scan(
            username=username,
            token=current_user.github_token,
            user_id=user_id,  # Use routed user ID
            store_results=False,
            user_type=user_type,  # Use detected user type
            authenticated_user_id=str(current_user.id),  # Keep original ID for reference
            database=database  # Use routed database
        )
        
        # Format repositories for response (matching fast_scan format)
        repositories = []
        for repo in result['repositories']:
            repositories.append({
                'id': repo.get('id', ''),
                'name': repo.get('name', ''),
                'full_name': repo.get('full_name', ''),
                'description': repo.get('description'),
                'language': repo.get('language'),
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'importance_score': repo.get('importance_score', 0.0),
                'category': repo.get('category', 'supporting')
            })
        
        elapsed = time.time() - start_time
        
        # Build response data matching fast_scan format
        scan_data = {
            'username': username,
            'user_profile': result['user'],
            'repositories': repositories,
            'summary': result['summary'],
            'scan_date': datetime.utcnow().isoformat(),
            'processing_time': elapsed,
            'scan_type': 'quick',
            'fromCache': False,
            'overallScore': result.get('overall_score', 0)
        }
        
        # ============================================================================
        # NEW DATABASE STORAGE SYSTEM
        # ============================================================================
        
        # Store in appropriate database using new routing system
        if database is not None:
            try:
                # Store in routed database and collection
                scan_time = datetime.utcnow()
                cache_data = {
                    'scan_id': f"{user_id}_{int(scan_time.timestamp())}",  # Unique scan ID
                    'username': username,
                    'user_id': user_id,
                    'authenticated_user_id': str(current_user.id),
                    'user_type': user_type,
                    'email': current_user.email,
                    'scan_date': scan_time,
                    'storage_location': storage_location,
                    **scan_data
                }
                
                # Store in appropriate collection based on routing
                # First check if document exists to preserve deep analysis data
                existing_doc = await database[scan_collection].find_one({'user_id': user_id})
                
                if existing_doc:
                    # Preserve existing deep analysis fields
                    preserved_fields = {}
                    deep_analysis_fields = [
                        'deepAnalysisComplete', 'overallScore', 'analyzedAt', 
                        'activityScore', 'consistencyScore', 'innovationScore', 'deliveryScore'
                    ]
                    
                    for field in deep_analysis_fields:
                        if field in existing_doc and existing_doc[field] not in [None, 0, False, ""]:
                            preserved_fields[field] = existing_doc[field]
                    
                    # Merge preserved fields with new cache data
                    cache_data.update(preserved_fields)
                    
                    # Update existing document
                    await database[scan_collection].update_one(
                        {'user_id': user_id},
                        {'$set': cache_data}
                    )
                    
                    logger.info(f"🔐 [INTERNAL_QUICK_SCAN] ✅ Updated existing document, preserved: {list(preserved_fields.keys())}")
                else:
                    # Insert new document
                    await database[scan_collection].insert_one(cache_data)
                    logger.info(f"🔐 [INTERNAL_QUICK_SCAN] ✅ Inserted new document")
                
                logger.info(f"🔐 [INTERNAL_QUICK_SCAN] ✅ Stored in {storage_location}")
                logger.info(f"🔐 [INTERNAL_QUICK_SCAN] Collection: {scan_collection}")
                logger.info(f"🔐 [INTERNAL_QUICK_SCAN] User ID: {user_id}")
                
            except Exception as cache_error:
                logger.error(f"🔐 [INTERNAL_QUICK_SCAN] ❌ Failed to cache results: {cache_error}")
        
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] ✅ INTERNAL scan completed for {username} in {elapsed:.2f}s")
        logger.info(f"🔐 [INTERNAL_QUICK_SCAN] ========================================")
        
        # Return in fast_scan format (data wrapped)
        return {
            'success': True,
            'data': scan_data,
            'processingTime': elapsed,
            'message': f"Quick scan completed in {elapsed:.2f} seconds"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[QUICK SCAN] ❌ Failed for {username} after {elapsed:.2f}s: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick scan failed: {str(e)}"
        )


@router.get("/quick-scan/{username}")
async def quick_scan_get(
    username: str,
    request: Request,
    force_refresh: bool = False
):
    """
    GET endpoint for quick scan - EXTERNAL USERS (Public Access)
    
    This endpoint handles EXTERNAL user scans (no authentication required)
    Data is stored in EXTERNAL database with external_ prefix
    """
    import time
    start_time = time.time()
    
    try:
        # ============================================================================
        # EXTERNAL USER DIFFERENTIATION - Enhanced Logging
        # ============================================================================
        
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ========================================")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] EXTERNAL USER SCAN INITIATED")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] Username: {username}")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] Force refresh: {force_refresh}")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] Authentication: NOT REQUIRED")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] Database Target: EXTERNAL_DB")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] Storage Prefix: external_{username}")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] User Type: EXTERNAL")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ========================================")
        
        # ============================================================================
        # NEW DATABASE ROUTING SYSTEM
        # ============================================================================
        
        # Get routing information using new system
        routing_info = await UserTypeDetector.route_user_operation(request, username, "quick_scan")
        
        user_type = routing_info["user_type"]
        user_id = routing_info["user_id"]
        database = routing_info["database"]
        scan_collection = routing_info["scan_collection"]
        storage_location = routing_info["storage_location"]
        
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] User Type: {user_type}")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] User ID: {user_id}")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] Database: {storage_location}")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] Collection: {scan_collection}")
        
        # Use fast_scan service directly
        logger.info(f"📦 [QUICK SCAN GET] Importing fast_scan_github_profile...")
        try:
            from app.services.fast_github_scanner import fast_scan_github_profile
            from app.core.config import get_github_token, settings
        except ImportError as ie:
            logger.error(f"❌ [QUICK SCAN GET] Import failed: {ie}")
            raise HTTPException(status_code=500, detail=f"Server configuration error: {ie}")
        
        logger.info(f"🔑 [QUICK SCAN GET] Getting GitHub token...")
        try:
            github_token = get_github_token()
            # If get_github_token returns None, try getting from settings directly as fallback
            if not github_token:
                logger.warning("get_github_token returned None, trying settings.github_oauth_token")
                github_token = settings.github_oauth_token
        except Exception as token_error:
             logger.error(f"❌ [QUICK SCAN GET] Token retrieval failed: {token_error}")
             raise HTTPException(status_code=500, detail=f"Token configuration error: {token_error}")

        if not github_token:
            logger.error(f"❌ [QUICK SCAN GET] GitHub token not configured!")
            raise HTTPException(
                status_code=500,
                detail="GitHub token not configured"
            )
        logger.info(f"✅ [QUICK SCAN GET] GitHub token obtained (Length: {len(github_token)})")
        
        # ============================================================================
        # NEW DATABASE CACHE CHECK
        # ============================================================================
        
        # Check cache first (unless force_refresh)
        if not force_refresh and database is not None:
            logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] Checking cache for {username}...")
            
            # Check appropriate database cache using new routing
            # Use case-insensitive search for username
            cached_result = await database[scan_collection].find_one(
                {
                    "username": {"$regex": f"^{username}$", "$options": "i"},
                    "user_type": user_type
                },
                sort=[("scan_date", -1)]
            )
            
            if cached_result:
                logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ✅ Found EXTERNAL cached result for {username}")
                scan_date = cached_result.get('scan_date')
                if scan_date and isinstance(scan_date, datetime):
                    age_minutes = (datetime.utcnow() - scan_date).total_seconds() / 60
                    logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ⏰ Cache age: {age_minutes:.1f} minutes")
                    if age_minutes < 5:
                        elapsed = time.time() - start_time
                        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ⚡ Returning EXTERNAL cached result (age: {age_minutes:.1f} min)")
                        
                        result = dict(cached_result)
                        result.pop('_id', None)
                        result['fromCache'] = True
                        result['cacheAge'] = f"{age_minutes:.1f} minutes"
                        result['user_type'] = user_type
                        result['storage_location'] = storage_location
                        
                        return {
                            'success': True,
                            'data': result,
                            'processingTime': elapsed,
                            'fromCache': True,
                            'userType': user_type
                        }
                    else:
                        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ⏰ Cache too old ({age_minutes:.1f} min), performing fresh EXTERNAL scan")
                else:
                    logger.warning(f"🌐 [EXTERNAL_QUICK_SCAN] ⚠️ Invalid scan_date in EXTERNAL cache")
            else:
                logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ❌ No EXTERNAL cached result found for {username}")
        elif force_refresh:
            logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] 🔄 Force refresh requested, skipping EXTERNAL cache")
        
        # ============================================================================
        # EXTERNAL USER SCAN EXECUTION
        # ============================================================================
        
        # Perform EXTERNAL scan using fast_scan service
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] Performing fresh EXTERNAL scan for {username}")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] Calling fast_scan_github_profile('{username}', token)...")
        
        try:
            scan_result = await fast_scan_github_profile(username, github_token)
            logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ✅ EXTERNAL scan completed successfully")
            logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] 📊 Scan result keys: {list(scan_result.keys()) if scan_result else 'None'}")
        except Exception as scan_error:
            logger.error(f"🌐 [EXTERNAL_QUICK_SCAN] ❌ EXTERNAL scan failed: {scan_error}")
            import traceback
            logger.error(f"🌐 [EXTERNAL_QUICK_SCAN] Traceback: {traceback.format_exc()}")
            raise
        
        if not scan_result:
            logger.error(f"🌐 [EXTERNAL_QUICK_SCAN] ❌ User {username} not found (empty result)")
            raise HTTPException(status_code=404, detail=f"User {username} not found")
        
        elapsed = time.time() - start_time
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ⏱️ EXTERNAL scan completed in {elapsed:.2f}s")
        
        # ============================================================================
        # EXTERNAL USER METADATA & STORAGE
        # ============================================================================
        
        # Add user metadata using new routing system
        current_time = datetime.utcnow()
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] 📝 Adding metadata to scan result...")
        scan_result.update({
            'user_id': user_id,
            'user_type': user_type,
            'storage_location': storage_location,
            'scan_date': current_time.isoformat(),
            'processing_time': elapsed,
            'scan_type': 'quick',
            'fromCache': False
        })
        
        # Cache the result using new routing system
        if database is not None:
            try:
                logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] 💾 Caching results for {username}...")
                
                # Store in appropriate database and collection
                cache_data = {
                    'scan_id': f"{user_id}_{int(current_time.timestamp())}",  # Unique scan ID
                    'username': username,
                    'user_id': user_id,
                    'user_type': user_type,
                    'storage_location': storage_location,
                    'scan_date': current_time,
                    **scan_result
                }
                
                # First check if document exists to preserve deep analysis data
                existing_doc = await database[scan_collection].find_one({'user_id': user_id})
                
                if existing_doc:
                    # Preserve existing deep analysis fields
                    preserved_fields = {}
                    deep_analysis_fields = [
                        'deepAnalysisComplete', 'overallScore', 'analyzedAt', 
                        'activityScore', 'consistencyScore', 'innovationScore', 'deliveryScore'
                    ]
                    
                    for field in deep_analysis_fields:
                        if field in existing_doc and existing_doc[field] not in [None, 0, False, ""]:
                            preserved_fields[field] = existing_doc[field]
                    
                    # Merge preserved fields with new cache data
                    cache_data.update(preserved_fields)
                    
                    # Update existing document
                    await database[scan_collection].update_one(
                        {'user_id': user_id},
                        {'$set': cache_data}
                    )
                    
                    logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ✅ Updated existing document, preserved: {list(preserved_fields.keys())}")
                else:
                    # Insert new document
                    await database[scan_collection].insert_one(cache_data)
                    logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ✅ Inserted new document")
                
                logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ✅ Results cached")
                logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] Collection: {scan_collection}")
                logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] User ID: {user_id}")
                
            except Exception as cache_error:
                logger.warning(f"🌐 [EXTERNAL_QUICK_SCAN] ⚠️ Failed to cache results: {cache_error}")
        
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ========================================")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ✅ EXTERNAL scan completed for {username} in {elapsed:.2f}s")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] 📊 Returning response with {len(scan_result.get('repositories', []))} repositories")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] 🗄️ Storage: EXTERNAL_DATABASE")
        logger.info(f"🌐 [EXTERNAL_QUICK_SCAN] ========================================")
        
        return {
            'success': True,
            'data': scan_result,
            'processingTime': elapsed,
            'message': f"External quick scan completed in {elapsed:.2f} seconds",
            'userType': user_type,
            'storageLocation': storage_location
        }
        
    except HTTPException as he:
        elapsed = time.time() - start_time
        logger.error(f"❌ [QUICK SCAN GET] ========================================")
        logger.error(f"❌ [QUICK SCAN GET] HTTP Exception for {username} after {elapsed:.2f}s")
        logger.error(f"❌ [QUICK SCAN GET] Status: {he.status_code}")
        logger.error(f"❌ [QUICK SCAN GET] Detail: {he.detail}")
        logger.error(f"❌ [QUICK SCAN GET] ========================================")
        raise
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ [QUICK SCAN GET] ========================================")
        logger.error(f"❌ [QUICK SCAN GET] Failed for {username} after {elapsed:.2f}s: {e}")
        import traceback
        logger.error(f"❌ [QUICK SCAN GET] Traceback: {traceback.format_exc()}")
        logger.error(f"❌ [QUICK SCAN GET] ========================================")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick scan failed: {str(e)}"
        )


@router.get("/scan-status/{user_id}")
async def get_scan_status(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Get scan status for a user
    
    Returns information about the most recent scan
    """
    try:
        # Verify access
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get appropriate database for user
        db = await get_user_database(request, "user_data")
        
        # Get user profile from database
        user_profile = await db.user_profiles.find_one({"user_id": user_id})
        
        if not user_profile:
            return {
                "scanned": False,
                "message": "No scan data found"
            }
        
        return {
            "scanned": user_profile.get("scan_completed", False),
            "scanned_at": user_profile.get("scanned_at"),
            "repository_count": user_profile.get("repository_count", 0),
            "flagship_count": user_profile.get("flagship_count", 0),
            "significant_count": user_profile.get("significant_count", 0),
            "supporting_count": user_profile.get("supporting_count", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scan status: {str(e)}"
        )
