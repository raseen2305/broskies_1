"""
HR Candidates API Router

This router provides endpoints for HR users to view candidate profiles
instantly by fetching data from the HR database with fallback to regular database.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from app.db_connection import get_database
from app.services.candidate_profile_service import CandidateProfileService
from app.services.hr_data_handler import store_hr_data, retrieve_hr_data, HRDataType
from app.core.security import verify_token
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def verify_hr_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify that the current user is an authenticated HR user
    
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
    prefix="/api/hr/candidates",
    tags=["HR Candidates"],
    # dependencies=[Depends(verify_hr_user)]  # TEMPORARILY DISABLED for testing
)


@router.get("/")
async def get_candidates_list(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    sort_by: str = "score",
    language: str = None,
    min_score: float = None,
    max_score: float = None,
    role: str = None
) -> Dict[str, Any]:
    """
    Get paginated list of candidates with filters and sorting
    
    This endpoint provides a list of candidates for the HR dashboard
    with support for filtering, searching, and sorting.
    
    Uses user_rankings collection which contains data from both analysis_states 
    and user_profiles collections, providing comprehensive candidate information.
    
    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 10)
        search: Search query for username/name/language
        sort_by: Sort field (score, upvotes, recent)
        language: Filter by programming language
        min_score: Minimum overall score
        max_score: Maximum overall score
        role: Filter by role category
        db: Database connection
        
    Returns:
        Paginated list of candidates with metadata
    """
    try:
        logger.info(f"HR requesting candidates list: page={page}, limit={limit}, search={search}")
        
        # Try to get database connection
        try:
            db = await get_database()
            if db is None:
                raise Exception("Database not available")
        except Exception as db_error:
            logger.error(f"Database connection failed: {db_error}")
            # Return mock data if database is not available
            mock_candidates = [
                {
                    "username": "samyu",
                    "full_name": "Sam Yu",
                    "profile_picture": "https://github.com/samyu.png",
                    "role_category": "Developer",
                    "overall_score": 88.5,
                    "upvotes": 0,
                    "primary_languages": ["Python", "JavaScript", "TypeScript"],
                    "github_url": "https://github.com/samyu",
                    "university": "Unknown",
                    "region": "Unknown",
                    "repository_count": 15,
                    "flagship_count": 3,
                    "significant_count": 7,
                    "supporting_count": 5
                }
            ]
            
            return {
                "success": True,
                "data": {
                    "candidates": mock_candidates,
                    "total": len(mock_candidates),
                    "page": page,
                    "limit": limit,
                    "total_pages": 1
                },
                "message": "Using mock data - database not available"
            }
        
        # Build query filter for user_rankings collection
        query_filter = {}
        
        # Search filter (search in github_username and name)
        if search:
            search_conditions = [
                {"github_username": {"$regex": search, "$options": "i"}},
                {"name": {"$regex": search, "$options": "i"}},
            ]
            query_filter["$or"] = search_conditions
        
        # Language filter - Note: user_rankings doesn't have primary_language field
        # We'll need to implement this differently or skip for now
        if language:
            # For now, we'll skip language filtering as user_rankings doesn't have this field
            # TODO: Add language information to user_rankings or implement join query
            pass
        
        # Score filter
        if min_score is not None:
            query_filter["overall_score"] = query_filter.get("overall_score", {})
            query_filter["overall_score"]["$gte"] = min_score
        
        if max_score is not None:
            query_filter["overall_score"] = query_filter.get("overall_score", {})
            query_filter["overall_score"]["$lte"] = max_score
        
        # Role filter (if available in user_rankings)
        if role:
            query_filter["role_category"] = role
        
        # Build sort criteria
        sort_criteria = []
        if sort_by == "score":
            sort_criteria = [("overall_score", -1)]
        elif sort_by == "upvotes":
            sort_criteria = [("upvotes", -1)]
        elif sort_by == "recent":
            sort_criteria = [("last_updated", -1)]
        else:
            sort_criteria = [("overall_score", -1)]
        
        # Try to get candidates from HR database first
        logger.info("🏢 Checking HR database for candidates...")
        hr_candidates = []
        try:
            hr_candidates = await retrieve_hr_data(query_filter, hr_data_type=HRDataType.CANDIDATE_PROFILE)
        except Exception as hr_error:
            logger.warning(f"🏢 HR database not available: {hr_error}")
            hr_candidates = []
        
        if hr_candidates:
            logger.info(f"🏢 Found {len(hr_candidates)} candidates in HR database")
            candidates_data = hr_candidates
            total = len(hr_candidates)
            
            # Apply sorting to HR data
            if sort_by == "upvotes":
                candidates_data.sort(key=lambda x: x.get("upvotes", 0), reverse=True)
            elif sort_by == "recent":
                candidates_data.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
            else:
                candidates_data.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
            
            # Apply pagination to HR data
            skip = (page - 1) * limit
            candidates_data = candidates_data[skip:skip + limit]
            total_pages = (total + limit - 1) // limit if total > 0 else 1
        else:
            # Fall back to user_rankings as the primary source
            logger.info("🏢 No candidates in HR database, falling back to user_rankings")
            total = await db.user_rankings.count_documents(query_filter)
            collection = db.user_rankings
            logger.info(f"Using user_rankings collection ({total} candidates)")
            
            # Calculate pagination
            skip = (page - 1) * limit
            total_pages = (total + limit - 1) // limit if total > 0 else 1
            
            # Fetch candidates
            cursor = collection.find(query_filter).sort(sort_criteria).skip(skip).limit(limit)
            candidates_data = await cursor.to_list(length=limit)
            
            # Store candidates in HR database for future use (if available)
            logger.info("🏢 Migrating candidates to HR database...")
            for candidate in candidates_data:
                hr_candidate_data = {
                    **candidate,
                    "source": "user_rankings",
                    "migrated_to_hr": "2024-12-10T00:00:00Z",
                    "hr_access_count": 1
                }
                try:
                    await store_hr_data(hr_candidate_data, HRDataType.CANDIDATE_PROFILE, "hr_candidate_migration")
                except Exception as e:
                    logger.warning(f"Failed to migrate candidate {candidate.get('github_username')}: {e}")
                    # Continue with other candidates even if one fails
        
        # Format candidates for response
        candidates = []
        for candidate in candidates_data:
            # Handle None values gracefully
            github_username = candidate.get("github_username", "")
            
            candidates.append({
                "username": github_username,
                "full_name": candidate.get("name") or github_username,  # Fallback to username if name is None
                "profile_picture": f"https://github.com/{github_username}.png",  # GitHub default avatar
                "role_category": "Developer",  # Default role category
                "overall_score": float(candidate.get("overall_score", 0.0)),
                "upvotes": 0,  # Not available in user_rankings, set to 0
                "primary_languages": ["Unknown"],  # TODO: Get from analysis_states or add to user_rankings
                "github_url": f"https://github.com/{github_username}",
                "university": candidate.get("university"),
                "region": candidate.get("region"),
                "repository_count": candidate.get("repository_count", 0),
                "flagship_count": candidate.get("flagship_count", 0),
                "significant_count": candidate.get("significant_count", 0),
                "supporting_count": candidate.get("supporting_count", 0)
            })
        
        logger.info(f"Returning {len(candidates)} candidates (page {page}/{total_pages})")
        
        return {
            "success": True,
            "data": {
                "candidates": candidates,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            }
        }
        
        # TODO: Switch to comprehensive_scans when data is accurate
        # Keeping the old implementation commented for reference:
        """
        # Build query filter for comprehensive_scans
        query_filter = {}
        
        # Search filter
        if search:
            query_filter["$or"] = [
                {"github_username": {"$regex": search, "$options": "i"}},
                {"userInfo.name": {"$regex": search, "$options": "i"}},
                {"languages": {"$regex": search, "$options": "i"}},
            ]
        
        # Language filter
        if language:
            query_filter["languages"] = language
        
        # Score filter
        if min_score is not None:
            query_filter["overall_score"] = query_filter.get("overall_score", {})
            query_filter["overall_score"]["$gte"] = min_score
        
        if max_score is not None:
            query_filter["overall_score"] = query_filter.get("overall_score", {})
            query_filter["overall_score"]["$lte"] = max_score
        
        # Role filter
        if role:
            query_filter["role_category"] = role
        
        # Build sort criteria
        sort_criteria = []
        if sort_by == "score":
            sort_criteria = [("overall_score", -1)]
        elif sort_by == "upvotes":
            sort_criteria = [("upvotes", -1)]
        elif sort_by == "recent":
            sort_criteria = [("scan_date", -1)]
        else:
            sort_criteria = [("overall_score", -1)]
        
        # Get total count
        total = await db.comprehensive_scans.count_documents(query_filter)
        
        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = (total + limit - 1) // limit
        
        # Fetch candidates
        cursor = db.comprehensive_scans.find(query_filter).sort(sort_criteria).skip(skip).limit(limit)
        candidates_data = await cursor.to_list(length=limit)
        
        # Format candidates for response
        candidates = []
        for candidate in candidates_data:
            user_info = candidate.get("userInfo", {})
            candidates.append({
                "username": candidate.get("github_username", user_info.get("login")),
                "full_name": user_info.get("name"),
                "profile_picture": user_info.get("avatar_url"),
                "role_category": candidate.get("role_category", "Developer"),
                "overall_score": candidate.get("overall_score", 0.0),
                "upvotes": candidate.get("upvotes", 0),
                "primary_languages": candidate.get("languages", [])[:3],
                "github_url": user_info.get("html_url", f"https://github.com/{candidate.get('github_username')}")
            })
        """
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error fetching candidates list: {e}")
        logger.error(f"Full traceback: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": f"Unable to retrieve candidates list: {str(e)}",
                "trace": error_trace if logger.level == logging.DEBUG else None
            }
        )


@router.get("/{username}")
async def get_candidate_profile(
    username: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get complete candidate profile data for HR viewing
    
    This endpoint fetches all candidate data from the database including:
    - GitHub profile information
    - Repository data with categories and scores
    - Overall ACID scores
    - Regional and university rankings
    - Language statistics and tech stack
    
    Args:
        username: GitHub username (case-sensitive)
        db: Database connection
        
    Returns:
        Complete candidate profile data
        
    Raises:
        404: Profile not found
        500: Database error
    """
    try:
        logger.info(f"HR requesting candidate profile for: {username}")
        
        # Try to get candidate from HR database first
        logger.info(f"🏢 Checking HR database for candidate: {username}")
        hr_candidates = []
        try:
            hr_candidates = await retrieve_hr_data(
                {"github_username": username}, 
                hr_data_type=HRDataType.CANDIDATE_PROFILE
            )
        except Exception as hr_error:
            logger.warning(f"🏢 HR database not available for {username}: {hr_error}")
            hr_candidates = []
        
        if hr_candidates:
            logger.info(f"🏢 Found candidate {username} in HR database")
            profile = hr_candidates[0]
            
            # Update access count (if HR database is available)
            try:
                from app.services.hr_data_handler import update_hr_data
                await update_hr_data(
                    {"github_username": username},
                    {"$inc": {"hr_access_count": 1}, "$set": {"last_hr_access": "2024-12-10T00:00:00Z"}},
                    hr_data_type=HRDataType.CANDIDATE_PROFILE
                )
            except Exception as e:
                logger.warning(f"Failed to update HR access count for {username}: {e}")
                # Continue without updating access count
        else:
            # Fall back to regular service
            logger.info(f"🏢 Candidate {username} not in HR database, using regular service")
            service = CandidateProfileService(db)
            profile = await service.get_candidate_profile(username)
            
            # Store in HR database for future use (if available)
            if profile:
                hr_candidate_data = {
                    **profile,
                    "source": "candidate_profile_service",
                    "migrated_to_hr": "2024-12-10T00:00:00Z",
                    "hr_access_count": 1,
                    "last_hr_access": "2024-12-10T00:00:00Z"
                }
                try:
                    await store_hr_data(hr_candidate_data, HRDataType.CANDIDATE_PROFILE, "hr_candidate_profile_access")
                    logger.info(f"🏢 Migrated candidate {username} to HR database")
                except Exception as e:
                    logger.warning(f"Failed to migrate candidate {username} to HR database: {e}")
                    # Continue without HR storage
        
        return {
            "success": True,
            "candidate": profile
        }
        
    except ValueError as e:
        # Profile not found
        logger.warning(f"Profile not found for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Profile not found",
                "message": f"No profile data found for username '{username}'. The user may not have been scanned yet.",
                "username": username,
                "suggestion": "Try scanning this user first to generate profile data."
            }
        )
    
    except Exception as e:
        # Database or other error
        logger.error(f"Error fetching candidate profile for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "Unable to retrieve candidate profile. Please try again later.",
                "username": username
            }
        )


@router.get("/{username}/exists")
async def check_candidate_exists(
    username: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Quick check if candidate profile exists in database
    
    This is a lightweight endpoint to check profile availability
    without fetching all the data.
    
    Args:
        username: GitHub username (case-sensitive)
        db: Database connection
        
    Returns:
        Existence status with last scan date and data age
    """
    try:
        logger.info(f"Checking if candidate profile exists for: {username}")
        
        # Initialize service
        service = CandidateProfileService(db)
        
        # Check existence
        result = await service.check_profile_exists(username)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Error checking candidate existence for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "Unable to check candidate profile existence.",
                "username": username
            }
        )


@router.get("/test")
async def test_hr_candidates_api() -> Dict[str, Any]:
    """
    Test endpoint to verify HR candidates API is working
    """
    try:
        return {
            "success": True,
            "message": "HR Candidates API is working",
            "timestamp": "2024-12-11T17:15:00Z",
            "status": "healthy"
        }
    except Exception as e:
        logger.error(f"Test endpoint failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )


@router.get("/mock")
async def get_mock_candidates() -> Dict[str, Any]:
    """
    Mock endpoint to test frontend without database dependency
    """
    try:
        mock_candidates = [
            {
                "username": "samyu",
                "full_name": "Sam Yu",
                "profile_picture": "https://github.com/samyu.png",
                "role_category": "Developer",
                "overall_score": 88.5,
                "upvotes": 0,
                "primary_languages": ["Python", "JavaScript", "TypeScript"],
                "github_url": "https://github.com/samyu",
                "university": "Unknown",
                "region": "Unknown",
                "repository_count": 15,
                "flagship_count": 3,
                "significant_count": 7,
                "supporting_count": 5
            },
            {
                "username": "testuser",
                "full_name": "Test User",
                "profile_picture": "https://github.com/testuser.png",
                "role_category": "Developer",
                "overall_score": 91.2,
                "upvotes": 0,
                "primary_languages": ["Java", "Python", "Go"],
                "github_url": "https://github.com/testuser",
                "university": "Unknown",
                "region": "Unknown",
                "repository_count": 20,
                "flagship_count": 4,
                "significant_count": 8,
                "supporting_count": 8
            }
        ]
        
        return {
            "success": True,
            "data": {
                "candidates": mock_candidates,
                "total": len(mock_candidates),
                "page": 1,
                "limit": 10,
                "total_pages": 1
            }
        }
    except Exception as e:
        logger.error(f"Mock endpoint failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock endpoint failed: {str(e)}"
        )


@router.post("/{username}/refresh")
async def refresh_candidate_profile(
    username: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Trigger a fresh scan for a candidate profile
    
    This endpoint initiates a new comprehensive scan for the candidate,
    which will update their profile data in the database. The scan runs
    asynchronously and the updated profile can be fetched after completion.
    
    Args:
        username: GitHub username (case-sensitive)
        db: Database connection
        
    Returns:
        Scan initiation status with scan_id for tracking
        
    Raises:
        500: Failed to initiate scan
    """
    try:
        logger.info(f"HR requesting profile refresh for: {username}")
        
        # Import scan function
        from app.routers.scan import scan_external_github_user
        
        # Trigger a fresh scan with force_refresh=True
        scan_result = await scan_external_github_user(username, force_refresh=True)
        
        logger.info(f"Profile refresh initiated for {username}")
        
        return {
            "success": True,
            "message": f"Profile refresh initiated for {username}",
            "username": username,
            "scan_initiated": True
        }
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    
    except Exception as e:
        # Handle other errors
        logger.error(f"Error refreshing candidate profile for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": f"Unable to refresh candidate profile: {str(e)}",
                "username": username
            }
        )
