from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import logging
import os
import re
import asyncio

from app.models.analysis_response import (
    InitiateAnalysisRequest,
    InitiateAnalysisResponse,
    AnalysisStatusResponse,
    AnalysisResultsResponse,
    ErrorResponse
)
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

from app.database import get_database
from app.core.security import get_current_user_token
from app.core.validation import (
    ScanRequest, GitHubUrlRequest, PaginationParams, SearchParams,
    InputSanitizer, ValidationError
)
from app.database import get_database, Collections
from app.models.user import User
from app.models.scan import ScanStatus
from app.services.github_scanner import GitHubScanner
from app.services.evaluation_engine import EvaluationEngine
from app.services.profile_generator import ProfileGenerator

from app.services.ml_evaluation_service import ml_service
from app.tasks.scan_tasks import scan_user_repositories, scan_single_repository, get_scan_progress, get_scan_result
from app.services.cache_service import cache_service
from app.services.performance_service import performance_service
from app.services.scan_progress_tracker import (
    start_scan_progress, update_scan_phase, update_repository_progress,
    report_scan_error, report_scan_warning, complete_scan_progress,
    get_scan_progress_data, ScanPhase
)
from app.user_type_detector import UserTypeDetector

router = APIRouter()


async def get_analysis_orchestrator():
    """
    Get a properly configured AnalysisOrchestrator with MongoDB state storage.
    
    Returns:
        AnalysisOrchestrator instance with persistent state storage
    """
    from app.services.analysis_orchestrator import AnalysisOrchestrator
    from app.services.analysis_state_storage import AnalysisStateStorage
    from app.db_connection import get_database as get_db_connection
    
    try:
        # Get database connection
        db = await get_db_connection()
        
        if db is not None:
            # Use MongoDB-based state storage with Redis cache
            state_storage = AnalysisStateStorage(db, cache_service)
            await state_storage.initialize()
            return AnalysisOrchestrator(state_storage=state_storage)
        else:
            # Fallback to in-memory storage (for testing/development)
            logger.warning("Database not available, using in-memory state storage")
            return AnalysisOrchestrator()
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator with MongoDB storage: {e}")
        # Fallback to in-memory storage
        return AnalysisOrchestrator()


@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "message": "Scan API is working"}

@router.get("/test-no-auth")
async def test_no_auth():
    """Test endpoint without authentication"""
    return {
        "status": "success",
        "message": "API is working without authentication",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/test-scan/{username}")
async def test_scan_no_auth(username: str):
    """Test scan endpoint without authentication for debugging"""
    try:
        # Use GitHub token from settings
        from app.core.config import settings
        github_token = settings.github_token
        
        if not github_token:
            return {
                "error": "No GitHub token available for testing",
                "message": "GitHub token not configured in settings"
            }
        
        # Initialize basic scanner
        scanner = GitHubScanner(github_token)
        
        # Get basic user info
        user_info = await scanner.get_user_info(username)
        
        # Get ALL repositories with metadata
        result = await scanner.fetch_user_repositories(
            username, 
            include_forks=False, 
            max_display_repos=35, 
            evaluate_limit=15,
            return_metadata=True
        )
        
        repositories = result["repositories"]
        metadata = result["metadata"]
        
        # Separate evaluated and display-only repositories
        evaluated_repos = [repo for repo in repositories if repo.get('evaluate_for_scoring', True)]
        display_only_repos = [repo for repo in repositories if not repo.get('evaluate_for_scoring', True)]
        
        return {
            "status": "success",
            "username": username,
            "user_info": user_info,
            "total_repositories": len(repositories),
            "evaluated_repositories": len(evaluated_repos),
            "display_only_repositories": len(display_only_repos),
            "evaluated_repos_sample": [{"name": repo["name"], "language": repo.get("language")} for repo in evaluated_repos[:5]],
            "display_only_repos_sample": [{"name": repo["name"], "language": repo.get("language")} for repo in display_only_repos[:5]],
            "metadata": metadata,
            "message": f"Test scan completed - {metadata['evaluated_count']} repos evaluated, {metadata['total_displayed']} displayed"
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "message": "Test scan failed",
            "traceback": traceback.format_exc()
        }

@router.get("/test-evaluation-limit/{username}")
async def test_evaluation_limit(username: str):
    """Test endpoint to demonstrate new evaluation limits"""
    try:
        from app.core.config import settings
        github_token = settings.github_token
        
        if not github_token:
            return {"error": "No GitHub token available"}
        
        # Initialize services
        scanner = GitHubScanner(github_token)
        evaluator = EvaluationEngine()
        
        # Get ALL repositories with metadata
        result = await scanner.fetch_user_repositories(
            username, 
            include_forks=False, 
            max_display_repos=35, 
            evaluate_limit=15,
            return_metadata=True
        )
        
        repositories = result["repositories"]
        metadata = result["metadata"]
        
        # Simulate scoring (simplified)
        evaluated_repos = []
        display_only_repos = []
        
        for repo in repositories:
            if repo.get('evaluate_for_scoring', True):
                # Add mock scoring for demonstration
                repo['mock_score'] = 85.5  # This would be real evaluation
                evaluated_repos.append(repo)
            else:
                # No scoring for display-only repos
                display_only_repos.append(repo)
        
        # Calculate mock overall scores (only from evaluated repos)
        mock_overall_scores = evaluator.calculate_user_scores(evaluated_repos)
        
        return {
            "status": "success",
            "username": username,
            "evaluation_summary": {
                "total_repositories_found": metadata["total_found"],
                "repositories_evaluated_for_scoring": metadata["evaluated_count"],
                "repositories_display_only": metadata["total_displayed"] - metadata["evaluated_count"],
                "overall_score_based_on": f"{metadata['evaluated_count']} repositories",
                "skipped_forks": metadata["skipped_forks"],
                "skipped_private": metadata["skipped_private"],
                "complete_data": metadata["complete_data_count"],
                "partial_data": metadata["partial_data_count"]
            },
            "metadata": metadata,
            "evaluated_repositories": [
                {
                    "name": repo["name"],
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count", 0),
                    "evaluated_for_scoring": True,
                    "mock_score": repo.get("mock_score")
                } for repo in evaluated_repos[:10]
            ],
            "display_only_repositories": [
                {
                    "name": repo["name"],
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count", 0),
                    "evaluated_for_scoring": False,
                    "note": "Shown for completeness, not included in scoring"
                } for repo in display_only_repos[:10]
            ],
            "overall_scores": mock_overall_scores,
            "message": "Only the first 20 most recent repositories are evaluated for scoring. Others are shown for reference only."
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.post("/clear-cache/{username}")
async def clear_user_cache(username: str):
    """Clear all cached data for a user - useful for testing"""
    try:
        await cache_service.invalidate_user_comprehensive_cache(username)
        return {
            "status": "success",
            "message": f"Cache cleared for user: {username}",
            "username": username
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to clear cache: {str(e)}",
            "username": username
        }

@router.get("/debug-user-info/{username}")
async def debug_user_info(username: str):
    """Debug endpoint for user info"""
    try:
        from app.core.config import settings
        
        return {
            "username": username,
            "github_token_configured": bool(settings.github_token),
            "token_length": len(settings.github_token) if settings.github_token else 0,
            "status": "debug_info"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "debug_failed"
        }

class ScanResponse(BaseModel):
    scan_id: str
    message: str

class ScanProgress(BaseModel):
    scan_id: str
    status: str  # 'pending', 'scanning', 'analyzing', 'completed', 'error'
    progress: int
    current_repo: Optional[str] = None
    total_repos: int = 0
    message: Optional[str] = None

# In-memory storage for scan progress (in production, use Redis)
scan_progress_store = {}

async def get_current_user(
    current_user_token: dict = Depends(get_current_user_token),
    db = Depends(get_database)
) -> User:
    """Get current authenticated user"""
    try:
        user_id = current_user_token["user_id"]
        user_type = current_user_token["user_type"]
        
        if user_type == "developer" and db is not None:
            try:
                # Use correct collection
                user_doc = await db[Collections.INTERNAL_USERS].find_one({"user_id": user_id})
                
                # Fallback to ObjectId lookup if not found by string ID
                if not user_doc:
                    from bson import ObjectId
                    if ObjectId.is_valid(user_id):
                        user_doc = await db[Collections.INTERNAL_USERS].find_one({"_id": ObjectId(user_id)})
                
                if user_doc:
                    # Map internal user to User model
                    # Ensure _id is string
                    user_doc["_id"] = str(user_doc["_id"])
                    return User(**user_doc)
            except Exception as e:
                logger.warning(f"Database query failed: {e}")
        
        # Don't return mock user data - raise proper error
        raise HTTPException(
            status_code=401,
            detail="Unable to authenticate user: Database unavailable and no valid authentication found"
        )
    except KeyError as e:
        logger.error(f"Missing required token field: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Invalid token format: missing {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        # Don't return mock user - raise proper authentication error
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )

@router.post("/repositories", response_model=ScanResponse)
async def scan_repositories(
    request: ScanRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Start repository scanning process using Celery background tasks"""
    try:
        # Validate GitHub URL first
        scanner = GitHubScanner(current_user.github_token)
        is_valid, username, repo_name = await scanner.validate_github_url(request.github_url)
        
        if not is_valid or not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub URL"
            )
        
        # Determine which task to use
        if repo_name:
            # Single repository scan
            task = scan_single_repository.delay(
                str(current_user.id),
                request.github_url
            )
        else:
            # User repositories scan
            task = scan_user_repositories.delay(
                str(current_user.id),
                request.github_url,
                request.scan_type
            )
        
        # Initialize progress in database
        await db.scan_progress.insert_one({
            "task_id": task.id,
            "user_id": str(current_user.id),
            "github_url": request.github_url,
            "scan_type": request.scan_type,
            "status": ScanStatus.PENDING.value,
            "progress": 0,
            "total_repos": 0,
            "processed_repos": 0,
            "current_repo": "",
            "errors": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        return ScanResponse(
            scan_id=task.id,
            message="Repository scan started successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start scan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")

@router.get("/progress/{scan_id}")
async def get_scan_progress_endpoint(scan_id: str, current_user: User = Depends(get_current_user)):
    """Get enhanced scanning progress with detailed phase information"""
    try:
        # Get progress from enhanced tracker first
        progress = await get_scan_progress_data(scan_id)
        
        # Fallback to legacy progress system
        if not progress:
            progress = await get_scan_progress(scan_id)
        
        if not progress:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Verify user has access to this scan (for authenticated scans)
        if progress.get("user_id") and progress.get("user_id") != "external_user":
            if progress.get("user_id") != str(current_user.id):
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Format response for both legacy and enhanced progress
        if "phase" in progress:
            # Enhanced progress format
            return {
                "scan_id": scan_id,
                "status": progress.get("phase", "unknown"),
                "progress": progress.get("progress_percentage", 0),
                "current_repo": progress.get("current_repository"),
                "total_repos": progress.get("total_repositories", 0),
                "processed_repos": progress.get("processed_repositories", 0),
                "message": progress.get("current_step"),
                "phase": progress.get("phase"),
                "estimated_completion": progress.get("estimated_completion"),
                "errors": progress.get("errors", []),
                "warnings": progress.get("warnings", []),
                "start_time": progress.get("start_time"),
                "scan_type": "enhanced"
            }
        else:
            # Legacy progress format
            return {
                "scan_id": scan_id,
                "status": progress.get("status", "unknown"),
                "progress": progress.get("progress", 0),
                "current_repo": progress.get("current_repo"),
                "total_repos": progress.get("total_repos", 0),
                "message": progress.get("message"),
                "scan_type": "legacy"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scan progress")

@router.get("/results/{user_id}")
async def get_scan_results(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get scan results for a user with caching"""
    try:
        # Validate user_id format
        if not user_id or len(user_id.strip()) == 0:
            raise HTTPException(status_code=422, detail="Invalid user_id: cannot be empty")
        
        # Get database connection
        from app.db_connection import get_database as get_db_connection
        db = await get_db_connection()
        
        logger.info(f"Getting scan results for user_id: {user_id}, current_user: {current_user.id if current_user else 'None'}")
        
        # Verify user can access these results
        if str(current_user.id) != user_id and current_user.user_type != "hr":
            raise HTTPException(status_code=403, detail="Access denied to this user's data")
        
        # Try cache first
        cached_results = await cache_service.get_scan_results(user_id)
        if cached_results:
            return cached_results
        
        # Use optimized performance service for better query performance
        try:
            repositories = await performance_service.get_optimized_user_repositories(user_id)
            evaluations = await performance_service.get_optimized_user_evaluations(user_id)
        except Exception as e:
            logger.warning(f"Performance service failed: {e}")
            repositories = []
            evaluations = []
        
        # If no scan data exists, fetch real GitHub data with enhanced analysis
        if not evaluations or not repositories:
            return await get_real_github_stats(current_user)
        
        # Calculate overall statistics from existing scan data
        if not evaluations:
            return {
                "userId": user_id,
                "overallScore": 0,
                "repositoryCount": len(repositories),
                "lastScanDate": None,
                "languages": [],
                "techStack": [],
                "roadmap": []
            }
        
        # Calculate overall score
        total_score = sum(eval_data["acid_score"]["overall"] for eval_data in evaluations)
        overall_score = total_score / len(evaluations) if evaluations else 0
        
        # Get language statistics
        language_stats = {}
        for repo in repositories:
            if repo.get("languages"):
                for lang, lines in repo["languages"].items():
                    if lang not in language_stats:
                        language_stats[lang] = {"lines": 0, "repos": 0}
                    language_stats[lang]["lines"] += lines
                    language_stats[lang]["repos"] += 1
        
        # Convert to percentage
        total_lines = sum(stats["lines"] for stats in language_stats.values())
        languages = []
        if total_lines > 0:
            for lang, stats in language_stats.items():
                languages.append({
                    "language": lang,
                    "percentage": round((stats["lines"] / total_lines) * 100, 1),
                    "linesOfCode": stats["lines"],
                    "repositories": stats["repos"]
                })
        
        # Sort by percentage
        languages.sort(key=lambda x: x["percentage"], reverse=True)
        
        # Get latest scan date
        latest_eval = max(evaluations, key=lambda x: x["created_at"]) if evaluations else None
        last_scan_date = latest_eval["created_at"] if latest_eval else None
        
        # Extract tech stack from repositories
        tech_stack = await extract_tech_stack_from_repositories(repositories)
        
        # Generate learning roadmap
        roadmap = generate_learning_roadmap(languages, tech_stack, overall_score)
        
        scan_results = {
            "userId": user_id,
            "overallScore": round(overall_score, 1),
            "repositoryCount": len(repositories),
            "lastScanDate": last_scan_date.isoformat() if last_scan_date else None,
            "languages": languages[:10],  # Top 10 languages
            "techStack": tech_stack,
            "roadmap": roadmap
        }
        
        # CRITICAL: Populate user_overall_details collection for ranking system
        try:
            if overall_score > 0 and current_user.github_username:
                logger.info(f"📊 [USER_OVERALL_DETAILS] Storing scan results for {current_user.github_username}")
                
                # Prepare overall details document
                overall_details = {
                    "user_id": user_id,
                    "github_username": current_user.github_username,
                    "overall_score": round(overall_score, 1),
                    "repository_count": len(repositories),
                    "evaluated_repository_count": len(evaluations),
                    "languages": languages[:10],
                    "tech_stack": tech_stack,
                    "last_scan_date": last_scan_date,
                    "updated_at": datetime.utcnow(),
                    "scan_type": "internal"
                }
                
                # Upsert into user_overall_details collection
                await db.user_overall_details.update_one(
                    {"user_id": user_id},
                    {"$set": overall_details},
                    upsert=True
                )
                
                logger.info(f"✅ [USER_OVERALL_DETAILS] Successfully stored scan results")
                logger.info(f"   - Username: {current_user.github_username}")
                logger.info(f"   - Overall Score: {round(overall_score, 1)}")
                logger.info(f"   - Repository Count: {len(repositories)}")
        except Exception as details_error:
            logger.error(f"❌ [USER_OVERALL_DETAILS] Error storing scan results: {details_error}")
            # Don't fail the request if storage fails
        
        # Store scores in scores_comparison collection (for authenticated users)
        try:
            from app.services.score_extractor import ScoreExtractor
            from app.services.score_storage_service import get_score_storage_service
            from app.db_connection import get_scores_database
            
            logger.info(f"[SCORE STORAGE] Storing authenticated user scores for {current_user.github_username}")
            
            # Get scores database connection
            scores_db = await get_scores_database()
            
            if scores_db and overall_score > 0 and current_user.github_username:
                # Extract flagship and significant repositories
                # Add scores to repositories for extraction
                repos_with_scores = []
                for repo in repositories:
                    # Find matching evaluation
                    matching_eval = next(
                        (e for e in evaluations if e.get("repo_id") == str(repo.get("_id"))),
                        None
                    )
                    if matching_eval:
                        repo['overall_score'] = matching_eval.get("acid_score", {}).get("overall", 0)
                        repo['acid_scores'] = matching_eval.get("acid_score", {})
                        repos_with_scores.append(repo)
                
                if repos_with_scores:
                    flagship_repos, significant_repos = ScoreExtractor.extract_scores_from_repositories(
                        repos_with_scores,
                        overall_score
                    )
                    
                    # Get user info for metadata
                    user_metadata = {
                        "github_username": current_user.github_username,
                        "name": current_user.name or current_user.github_username,
                        "bio": None,
                        "location": None,
                        "company": None,
                        "total_repositories_analyzed": len(repos_with_scores),
                        "total_stars": sum(repo.get("stars", 0) for repo in repositories),
                        "total_forks": sum(repo.get("forks", 0) for repo in repositories),
                        "top_languages": [
                            {"language": lang["language"], "count": lang["repositories"]}
                            for lang in languages[:5]
                        ]
                    }
                    
                    # Get score storage service
                    score_service = await get_score_storage_service(scores_db)
                    
                    # Store scores
                    success = await score_service.store_user_scores(
                        username=current_user.github_username,
                        user_id=str(current_user.id),
                        overall_score=overall_score,
                        flagship_repos=flagship_repos,
                        significant_repos=significant_repos,
                        metadata=user_metadata
                    )
                    
                    if success:
                        logger.info(f"✅ [SCORE STORAGE] Successfully stored authenticated user scores")
                        logger.info(f"   - Username: {current_user.github_username}")
                        logger.info(f"   - Overall Score: {overall_score}")
                        logger.info(f"   - Flagship Repos: {len(flagship_repos)}")
                        logger.info(f"   - Significant Repos: {len(significant_repos)}")
                    else:
                        logger.warning(f"⚠️ [SCORE STORAGE] Failed to store authenticated user scores")
            else:
                if not scores_db:
                    logger.warning(f"[SCORE STORAGE] Scores database not available")
                elif not current_user.github_username:
                    logger.info(f"[SCORE STORAGE] No GitHub username for authenticated user")
                else:
                    logger.info(f"[SCORE STORAGE] No score to store (score: {overall_score})")
                    
        except Exception as score_error:
            logger.error(f"❌ [SCORE STORAGE] Error storing authenticated user scores: {score_error}")
            # Don't fail the request if score storage fails
        
        # Trigger ranking sync after scan completion (for internal scans only)
        try:
            if overall_score > 0 and current_user.github_username:
                logger.info(f"🎯 Triggering ranking sync after scan completion")
                scanner = GitHubScanner(current_user.github_token)
                await scanner.trigger_ranking_sync_after_scan(
                    user_id=str(current_user.id),
                    scan_type='self',  # This is an internal scan
                    db=db
                )
        except Exception as ranking_error:
            logger.error(f"❌ [RANKING SYNC] Error triggering ranking sync: {ranking_error}")
            # Don't fail the request if ranking sync fails
        
        # Cache the scan results for 30 minutes
        await cache_service.cache_scan_results(user_id, scan_results, 1800)
        
        return scan_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_scan_results: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get scan results: {str(e)}")

async def get_real_github_stats(user: User):
    """Fetch comprehensive real-time GitHub statistics for a user"""
    try:
        if not user.github_token or not user.github_username:
            return {
                "userId": str(user.id),
                "overallScore": 0,
                "repositoryCount": 0,
                "lastScanDate": None,
                "languages": [],
                "techStack": [],
                "roadmap": [],
                "githubProfile": None,
                "comprehensiveData": None
            }
        
        # Use basic scanner only (comprehensive scanner is too slow)
        comprehensive_profile = None
        
        # Initialize basic GitHub scanner as fallback
        scanner = GitHubScanner(user.github_token)
        
        # Get user's GitHub profile
        github_profile = await scanner.get_user_info(user.github_username)
        
        # Get ALL user's repositories - NO LIMITS, NO FILTERING (except forks/private)
        # Remove max_display_repos limit to show ALL repos
        repositories = await scanner.fetch_user_repositories(
            user.github_username, 
            include_forks=False,  # Only filter forks and private
            max_display_repos=100,  # Increased limit to show more repos
            evaluate_limit=15
        )
        
        logger.info(f"📊 Fetched {len(repositories)} repositories for {user.github_username}")
        
        # SIMPLIFIED APPROACH: Skip detailed analysis entirely, just add basic scores
        # This ensures ALL repos are shown immediately without any processing delays
        detailed_repositories = []
        
        # Add basic scores to ALL repos without any detailed analysis
        basic_acid_scores = {
            "atomicity": 50,
            "consistency": 50,
            "isolation": 50,
            "durability": 50,
            "overall": 50
        }
        
        basic_quality_metrics = {
            "readability": 50,
            "maintainability": 50,
            "security": 50,
            "test_coverage": 50,
            "documentation": 50
        }
        
        logger.info(f"📦 Adding all {len(repositories)} repositories with basic scores (no detailed analysis)")
        
        for repo in repositories:
            detailed_repositories.append({
                **repo,
                "analysis": {
                    "acid_scores": basic_acid_scores,
                    "quality_metrics": basic_quality_metrics,
                    "overall_score": 50
                }
            })
        
        logger.info(f"✅ All {len(detailed_repositories)} repositories added successfully - NO DETAILED ANALYSIS, NO FILTERING")
        
        # Calculate language statistics from repositories
        language_stats = {}
        total_repos = len(repositories)
        
        for repo in repositories:
            if repo.get("language"):
                lang = repo["language"]
                if lang not in language_stats:
                    language_stats[lang] = {"repos": 0, "stars": 0}
                language_stats[lang]["repos"] += 1
                language_stats[lang]["stars"] += repo.get("stargazers_count", 0)
        
        # Convert to percentage and format
        languages = []
        if language_stats:
            for lang, stats in language_stats.items():
                percentage = (stats["repos"] / total_repos) * 100 if total_repos > 0 else 0
                languages.append({
                    "language": lang,
                    "percentage": round(percentage, 1),
                    "repositories": stats["repos"],
                    "stars": stats["stars"]
                })
        
        # Sort by repository count
        languages.sort(key=lambda x: x["repositories"], reverse=True)
        
        # Calculate a basic score based on GitHub metrics
        total_stars = sum(repo.get("stargazers_count", 0) for repo in repositories)
        total_forks = sum(repo.get("forks_count", 0) for repo in repositories)
        public_repos = github_profile.get("public_repos", 0)
        followers = github_profile.get("followers", 0)
        
        # Simple scoring algorithm (can be improved)
        basic_score = min(100, (total_stars * 2 + total_forks + public_repos + followers) / 10)
        
        # Generate comprehensive developer profile using ProfileGenerator
        profile_generator = ProfileGenerator()
        
        # Create user data for profile generation
        user_profile_data = {
            "user_id": str(user.id),
            "github_username": user.github_username,
            "github_profile": github_profile
        }
        
        # Generate comprehensive profile
        try:
            comprehensive_profile = profile_generator.generate_developer_profile(repositories, user_profile_data)
        except Exception as e:
            logger.warning(f"Profile generation failed: {e}")
            comprehensive_profile = {"overall_scores": {"overall_score": basic_score}}
        
        # Extract tech stack and roadmap from comprehensive profile
        try:
            tech_stack = await extract_tech_stack_from_repositories(repositories)
        except Exception as e:
            logger.warning(f"Tech stack extraction failed: {e}")
            tech_stack = []
        roadmap = comprehensive_profile.get("technology_roadmap", {}).get("recommended_paths", [])
        
        # Convert roadmap format for frontend compatibility
        formatted_roadmap = []
        for path in roadmap[:6]:  # Limit to 6 items
            formatted_roadmap.append({
                "title": path.get("path", "Learning Path"),
                "description": path.get("description", ""),
                "priority": "High",
                "category": "Development",
                "estimatedTime": path.get("timeline", "3-6 months"),
                "skills": path.get("technologies", []),
                "resources": ["Online courses", "Documentation", "Practice projects"]
            })
        
        # Add skill gap recommendations
        skill_gaps = comprehensive_profile.get("technology_roadmap", {}).get("skill_gaps", [])
        for gap in skill_gaps[:3]:  # Add top 3 skill gaps
            formatted_roadmap.append({
                "title": f"Improve {gap.get('area', 'Skills')}",
                "description": gap.get("recommendation", ""),
                "priority": gap.get("priority", "Medium"),
                "category": "Skill Development",
                "estimatedTime": "1-2 months",
                "skills": [gap.get("area", "")],
                "resources": ["Best practices guide", "Online tutorials"]
            })
        
        # Use enhanced scoring from comprehensive profile
        enhanced_score = comprehensive_profile.get("overall_scores", {}).get("overall_score", basic_score)
        
        return {
            "userId": str(user.id),
            "overallScore": round(enhanced_score, 1),
            "repositoryCount": total_repos,
            "lastScanDate": None,  # No scan performed yet
            "languages": languages[:10],  # Top 10 languages
            "techStack": tech_stack,
            "roadmap": formatted_roadmap,
            "githubProfile": {
                "username": user.github_username,
                "name": github_profile.get("name"),
                "bio": github_profile.get("bio"),
                "location": github_profile.get("location"),
                "company": github_profile.get("company"),
                "blog": github_profile.get("blog"),
                "public_repos": github_profile.get("public_repos", 0),
                "followers": github_profile.get("followers", 0),
                "following": github_profile.get("following", 0),
                "created_at": github_profile.get("created_at") if github_profile.get("created_at") else None,
                "avatar_url": github_profile.get("avatar_url")
            },
            # Include additional enhanced data
            "skillAssessment": comprehensive_profile.get("skill_assessment", {}),
            "insights": comprehensive_profile.get("insights", {}),
            "profileCompleteness": comprehensive_profile.get("profile_completeness", {}),
            "nextSteps": comprehensive_profile.get("next_steps", []),
            # Include comprehensive GitHub data (like gitroll.io)
            "comprehensiveData": comprehensive_profile,
            "detailedStats": {
                "contributionStats": comprehensive_profile.get("contribution_stats", {}) if comprehensive_profile else {},
                "repositoryOverview": comprehensive_profile.get("repository_overview", {}) if comprehensive_profile else {},
                "activityCalendar": comprehensive_profile.get("activity_calendar", {}) if comprehensive_profile else {},
                "collaborationMetrics": comprehensive_profile.get("collaboration_metrics", {}) if comprehensive_profile else {},
                "languageStatistics": comprehensive_profile.get("language_statistics", {}) if comprehensive_profile else {},
                "achievementMetrics": comprehensive_profile.get("achievement_metrics", {}) if comprehensive_profile else {},
                "socialMetrics": comprehensive_profile.get("social_metrics", {}) if comprehensive_profile else {},
                "recentActivity": comprehensive_profile.get("recent_activity", {}) if comprehensive_profile else {},
                "organizations": comprehensive_profile.get("organizations", []) if comprehensive_profile else []
            },
            # Include detailed repository analysis
            "repositories": detailed_repositories,
            "repositoryDetails": detailed_repositories,  # Alias for frontend compatibility
            "scanMetadata": {
                "scanDate": datetime.utcnow().isoformat(),
                "scanDuration": "real_time",
                "dataSource": "github_api",
                "analysisDepth": "comprehensive",
                "repositoriesAnalyzed": len(detailed_repositories),
                "totalRepositories": total_repos
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch GitHub stats for user {user.id}: {str(e)}")
        # Return basic stats if GitHub API fails
        return {
            "userId": str(user.id),
            "overallScore": 0,
            "repositoryCount": 0,
            "lastScanDate": None,
            "languages": [],
            "techStack": [],
            "roadmap": [],
            "githubProfile": {
                "username": user.github_username if user.github_username else "unknown",
                "name": None,
                "bio": None,
                "location": None,
                "company": None,
                "blog": None,
                "public_repos": 0,
                "followers": 0,
                "following": 0,
                "created_at": None,
                "avatar_url": None
            }
        }

async def extract_tech_stack_from_repositories(repositories):
    """Extract comprehensive technology stack from repository data with enhanced detection"""
    tech_stack = {}
    
    # Enhanced technology indicators with more comprehensive patterns
    tech_indicators = {
        # Frontend Frameworks & Libraries
        'React': {
            'indicators': ['react', 'jsx', 'create-react-app', 'next.js', 'nextjs', 'gatsby'],
            'file_patterns': ['package.json', '.jsx', '.tsx'],
            'content_patterns': ['import.*react', 'from.*react', 'React.Component'],
            'category': 'Frontend Framework'
        },
        'Vue.js': {
            'indicators': ['vue', 'vuejs', 'nuxt', 'nuxtjs', 'quasar'],
            'file_patterns': ['.vue', 'package.json'],
            'content_patterns': ['import.*vue', 'Vue.component', 'new Vue'],
            'category': 'Frontend Framework'
        },
        'Angular': {
            'indicators': ['angular', '@angular', 'ng-', 'angular-cli'],
            'file_patterns': ['angular.json', 'package.json', '.ts'],
            'content_patterns': ['@Component', '@Injectable', 'import.*@angular'],
            'category': 'Frontend Framework'
        },
        'Svelte': {
            'indicators': ['svelte', 'sveltekit'],
            'file_patterns': ['.svelte', 'package.json'],
            'content_patterns': ['<script>', '<style>'],
            'category': 'Frontend Framework'
        },
        
        # Backend Frameworks
        'Express.js': {
            'indicators': ['express', 'expressjs'],
            'file_patterns': ['package.json', 'app.js', 'server.js'],
            'content_patterns': ['require.*express', 'import.*express', 'app.listen'],
            'category': 'Backend Framework'
        },
        'Django': {
            'indicators': ['django', 'django-rest-framework', 'drf'],
            'file_patterns': ['requirements.txt', 'manage.py', 'settings.py'],
            'content_patterns': ['from django', 'import django', 'DJANGO_SETTINGS'],
            'category': 'Backend Framework'
        },
        'Flask': {
            'indicators': ['flask', 'flask-restful', 'flask-api'],
            'file_patterns': ['requirements.txt', 'app.py', 'main.py'],
            'content_patterns': ['from flask', 'import flask', 'Flask(__name__)'],
            'category': 'Backend Framework'
        },
        'FastAPI': {
            'indicators': ['fastapi', 'uvicorn', 'starlette'],
            'file_patterns': ['requirements.txt', 'main.py', 'app.py'],
            'content_patterns': ['from fastapi', 'import fastapi', 'FastAPI()'],
            'category': 'Backend Framework'
        },
        'Spring Boot': {
            'indicators': ['spring-boot', 'springframework', 'spring'],
            'file_patterns': ['pom.xml', 'build.gradle', '.java'],
            'content_patterns': ['@SpringBootApplication', 'import org.springframework'],
            'category': 'Backend Framework'
        },
        'Laravel': {
            'indicators': ['laravel', 'artisan', 'composer'],
            'file_patterns': ['composer.json', 'artisan', '.php'],
            'content_patterns': ['use Illuminate', 'Laravel\\'],
            'category': 'Backend Framework'
        },
        
        # Databases
        'MongoDB': {
            'indicators': ['mongodb', 'mongoose', 'pymongo', 'mongo'],
            'file_patterns': ['package.json', 'requirements.txt'],
            'content_patterns': ['mongoose.connect', 'MongoClient', 'from pymongo'],
            'category': 'Database'
        },
        'PostgreSQL': {
            'indicators': ['postgresql', 'postgres', 'psycopg2', 'pg'],
            'file_patterns': ['requirements.txt', 'package.json', 'docker-compose.yml'],
            'content_patterns': ['psycopg2', 'pg.Pool', 'postgres://'],
            'category': 'Database'
        },
        'MySQL': {
            'indicators': ['mysql', 'mysql2', 'mariadb'],
            'file_patterns': ['requirements.txt', 'package.json'],
            'content_patterns': ['mysql.connector', 'mysql2', 'mysql://'],
            'category': 'Database'
        },
        'Redis': {
            'indicators': ['redis', 'redis-py', 'ioredis'],
            'file_patterns': ['requirements.txt', 'package.json'],
            'content_patterns': ['import redis', 'Redis()', 'redis.createClient'],
            'category': 'Database'
        },
        'SQLite': {
            'indicators': ['sqlite', 'sqlite3'],
            'file_patterns': ['.db', '.sqlite', '.sqlite3'],
            'content_patterns': ['sqlite3.connect', 'import sqlite3'],
            'category': 'Database'
        },
        
        # Cloud & DevOps
        'Docker': {
            'indicators': ['docker', 'dockerfile', 'docker-compose'],
            'file_patterns': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
            'content_patterns': ['FROM ', 'RUN ', 'COPY '],
            'category': 'DevOps'
        },
        'Kubernetes': {
            'indicators': ['kubernetes', 'k8s', 'kubectl', 'helm'],
            'file_patterns': ['.yaml', '.yml', 'deployment.yaml'],
            'content_patterns': ['apiVersion:', 'kind: Deployment', 'kubectl'],
            'category': 'DevOps'
        },
        'AWS': {
            'indicators': ['aws', 'boto3', 'aws-sdk', 'lambda', 's3', 'ec2'],
            'file_patterns': ['requirements.txt', 'package.json'],
            'content_patterns': ['import boto3', 'aws-sdk', 'AWS.'],
            'category': 'Cloud Platform'
        },
        'Google Cloud': {
            'indicators': ['gcp', 'google-cloud', 'firebase'],
            'file_patterns': ['requirements.txt', 'package.json'],
            'content_patterns': ['google.cloud', 'firebase', 'gcp'],
            'category': 'Cloud Platform'
        },
        
        # Testing Frameworks
        'Jest': {
            'indicators': ['jest', '@testing-library', 'enzyme'],
            'file_patterns': ['package.json', '.test.js', '.spec.js'],
            'content_patterns': ['describe(', 'test(', 'expect('],
            'category': 'Testing'
        },
        'Pytest': {
            'indicators': ['pytest', 'pytest-cov', 'unittest'],
            'file_patterns': ['requirements.txt', 'test_*.py', '*_test.py'],
            'content_patterns': ['import pytest', 'def test_', '@pytest.'],
            'category': 'Testing'
        },
        
        # Build Tools & Bundlers
        'Webpack': {
            'indicators': ['webpack', 'webpack-cli'],
            'file_patterns': ['webpack.config.js', 'package.json'],
            'content_patterns': ['module.exports', 'webpack'],
            'category': 'Build Tool'
        },
        'Vite': {
            'indicators': ['vite', 'vitejs'],
            'file_patterns': ['vite.config.js', 'package.json'],
            'content_patterns': ['import { defineConfig }', 'vite'],
            'category': 'Build Tool'
        },
        'TypeScript': {
            'indicators': ['typescript', '@types', 'ts-node'],
            'file_patterns': ['tsconfig.json', '.ts', '.tsx'],
            'content_patterns': ['interface ', 'type ', ': string'],
            'category': 'Language/Tool'
        },
        
        # Mobile Development
        'React Native': {
            'indicators': ['react-native', 'expo', 'metro'],
            'file_patterns': ['package.json', '.tsx', '.jsx'],
            'content_patterns': ['react-native', 'expo', 'StyleSheet.create'],
            'category': 'Mobile Framework'
        },
        'Flutter': {
            'indicators': ['flutter', 'dart'],
            'file_patterns': ['pubspec.yaml', '.dart'],
            'content_patterns': ['import \'package:flutter', 'StatelessWidget'],
            'category': 'Mobile Framework'
        },
        
        # AI/ML Frameworks
        'TensorFlow': {
            'indicators': ['tensorflow', 'tf', 'keras'],
            'file_patterns': ['requirements.txt', '.py'],
            'content_patterns': ['import tensorflow', 'tf.', 'keras.'],
            'category': 'AI/ML Framework'
        },
        'PyTorch': {
            'indicators': ['pytorch', 'torch', 'torchvision'],
            'file_patterns': ['requirements.txt', '.py'],
            'content_patterns': ['import torch', 'torch.nn', 'pytorch'],
            'category': 'AI/ML Framework'
        },
        'Scikit-learn': {
            'indicators': ['scikit-learn', 'sklearn', 'pandas', 'numpy'],
            'file_patterns': ['requirements.txt', '.py'],
            'content_patterns': ['from sklearn', 'import pandas', 'import numpy'],
            'category': 'AI/ML Framework'
        }
    }
    
    # Initialize GitHub scanner for content analysis
    scanner = None
    try:
        # We'll need a token for content analysis - this should be passed from the calling function
        pass
    except:
        pass
    
    for repo in repositories:
        # Basic repository information
        topics = repo.get('topics', [])
        repo_name = repo.get('name', '').lower()
        description = repo.get('description', '').lower()
        language = repo.get('language', '')
        languages = repo.get('languages', {})
        
        # Combine text for analysis
        repo_text = f"{repo_name} {description}"
        
        for tech_name, tech_config in tech_indicators.items():
            score = 0
            evidence = []
            
            # Check topics (high confidence)
            for topic in topics:
                if any(indicator in topic.lower() for indicator in tech_config['indicators']):
                    score += 5
                    evidence.append(f"topic: {topic}")
            
            # Check repository name and description (medium confidence)
            for indicator in tech_config['indicators']:
                if indicator in repo_text:
                    score += 3
                    evidence.append(f"name/desc: {indicator}")
            
            # Check primary language (medium confidence)
            if language and any(indicator in language.lower() for indicator in tech_config['indicators']):
                score += 4
                evidence.append(f"language: {language}")
            
            # Check all languages used (lower confidence)
            for lang in languages.keys():
                if any(indicator in lang.lower() for indicator in tech_config['indicators']):
                    score += 2
                    evidence.append(f"lang: {lang}")
            
            # File pattern detection (would need repository content access)
            # This is a placeholder for when we have content access
            
            if score > 0:
                if tech_name not in tech_stack:
                    tech_stack[tech_name] = {
                        'name': tech_name,
                        'confidence': 0,
                        'repositories': 0,
                        'category': tech_config['category'],
                        'evidence': [],
                        'total_score': 0
                    }
                
                tech_stack[tech_name]['confidence'] += score
                tech_stack[tech_name]['repositories'] += 1
                tech_stack[tech_name]['evidence'].extend(evidence)
                tech_stack[tech_name]['total_score'] += score
    
    # Convert to list and calculate final scores
    tech_list = []
    for tech_name, tech_data in tech_stack.items():
        # Calculate normalized confidence (0-100)
        max_possible_score = len(repositories) * 15  # Max score per repo * number of repos
        normalized_confidence = min(100, (tech_data['total_score'] / max(max_possible_score * 0.1, 1)) * 100)
        
        # Calculate experience level based on repositories and confidence
        repo_count = tech_data['repositories']
        if repo_count >= 5 and normalized_confidence >= 70:
            experience_level = 'Expert'
        elif repo_count >= 3 and normalized_confidence >= 50:
            experience_level = 'Advanced'
        elif repo_count >= 2 and normalized_confidence >= 30:
            experience_level = 'Intermediate'
        else:
            experience_level = 'Beginner'
        
        tech_list.append({
            'name': tech_name,
            'category': tech_data['category'],
            'confidence': round(normalized_confidence, 1),
            'repositories': repo_count,
            'experience_level': experience_level,
            'evidence_count': len(tech_data['evidence']),
            'last_used': 'Recent'  # Could be calculated from repo dates
        })
    
    # Sort by confidence and repository count
    tech_list.sort(key=lambda x: (x['confidence'], x['repositories']), reverse=True)
    
    return tech_list[:25]  # Top 25 technologies



def generate_learning_roadmap(languages, tech_stack, current_score):
    """Generate comprehensive personalized learning roadmap based on current skills and industry trends"""
    
    # Get primary language and current skill levels
    primary_language = languages[0]['language'] if languages else None
    
    # Analyze current tech stack by categories
    current_categories = {}
    skill_levels = {}
    
    for tech in tech_stack:
        category = tech['category']
        if category not in current_categories:
            current_categories[category] = []
        current_categories[category].append({
            'name': tech['name'],
            'level': tech.get('experience_level', 'Beginner'),
            'confidence': tech.get('confidence', 0)
        })
        skill_levels[tech['name']] = tech.get('experience_level', 'Beginner')
    
    # Calculate overall skill distribution
    total_repos = sum(lang.get('repositories', 0) for lang in languages)
    experience_score = current_score
    
    suggestions = []
    
    # === LANGUAGE-SPECIFIC ROADMAPS ===
    if primary_language:
        lang_lower = primary_language.lower()
        
        # JavaScript/TypeScript Ecosystem
        if lang_lower in ['javascript', 'typescript']:
            # Frontend Development Path
            if 'Frontend Framework' not in current_categories:
                suggestions.append({
                    'id': 'js-frontend-mastery',
                    'title': 'Master Modern Frontend Development',
                    'description': 'Build production-ready web applications with React ecosystem',
                    'priority': 'High',
                    'category': 'Frontend Development',
                    'estimatedTime': '3-4 months',
                    'difficulty': 'Intermediate',
                    'skills': ['React/Next.js', 'TypeScript', 'State Management (Redux/Zustand)', 'Testing (Jest/RTL)', 'CSS-in-JS'],
                    'prerequisites': ['JavaScript ES6+', 'HTML/CSS'],
                    'milestones': [
                        'Build a Todo App with React',
                        'Create a Dashboard with Charts',
                        'Deploy to Production',
                        'Add Authentication & Testing'
                    ],
                    'resources': [
                        {'type': 'course', 'name': 'React Official Tutorial', 'url': 'https://react.dev/learn'},
                        {'type': 'project', 'name': 'Build 5 React Projects', 'description': 'Hands-on practice'},
                        {'type': 'book', 'name': 'Fullstack React', 'description': 'Comprehensive guide'}
                    ],
                    'market_demand': 'Very High',
                    'salary_impact': '+15-25%'
                })
            
            # Backend Development Path
            if 'Backend Framework' not in current_categories:
                suggestions.append({
                    'id': 'js-backend-mastery',
                    'title': 'Node.js Backend Development',
                    'description': 'Build scalable APIs and microservices with Node.js ecosystem',
                    'priority': 'High',
                    'category': 'Backend Development',
                    'estimatedTime': '2-3 months',
                    'difficulty': 'Intermediate',
                    'skills': ['Express.js/Fastify', 'Database Integration', 'Authentication & Security', 'API Design', 'Testing'],
                    'prerequisites': ['JavaScript', 'Basic HTTP concepts'],
                    'milestones': [
                        'Build REST API',
                        'Add Database Integration',
                        'Implement Authentication',
                        'Deploy with Docker'
                    ],
                    'resources': [
                        {'type': 'course', 'name': 'Node.js Complete Guide', 'description': 'Backend fundamentals'},
                        {'type': 'project', 'name': 'E-commerce API', 'description': 'Real-world project'},
                        {'type': 'documentation', 'name': 'Express.js Docs', 'url': 'https://expressjs.com/'}
                    ],
                    'market_demand': 'High',
                    'salary_impact': '+20-30%'
                })
            
            # Full-Stack Enhancement
            if experience_score > 60:
                suggestions.append({
                    'id': 'js-fullstack-advanced',
                    'title': 'Advanced Full-Stack Architecture',
                    'description': 'Master advanced patterns, performance optimization, and system design',
                    'priority': 'Medium',
                    'category': 'Architecture',
                    'estimatedTime': '4-6 months',
                    'difficulty': 'Advanced',
                    'skills': ['Microservices', 'GraphQL', 'Performance Optimization', 'System Design', 'Advanced Testing'],
                    'prerequisites': ['React', 'Node.js', 'Database experience'],
                    'milestones': [
                        'Design Microservices Architecture',
                        'Implement GraphQL API',
                        'Optimize Performance',
                        'Build Monitoring Dashboard'
                    ],
                    'resources': [
                        {'type': 'course', 'name': 'System Design Course', 'description': 'Scalability patterns'},
                        {'type': 'book', 'name': 'Designing Data-Intensive Applications', 'description': 'System architecture'},
                        {'type': 'project', 'name': 'Distributed System Project', 'description': 'Hands-on experience'}
                    ],
                    'market_demand': 'Very High',
                    'salary_impact': '+30-50%'
                })
        
        # Python Ecosystem
        elif lang_lower == 'python':
            # Web Development Path
            if 'Backend Framework' not in current_categories:
                suggestions.append({
                    'id': 'python-web-development',
                    'title': 'Python Web Development Mastery',
                    'description': 'Build robust web applications with Django/FastAPI',
                    'priority': 'High',
                    'category': 'Backend Development',
                    'estimatedTime': '2-3 months',
                    'difficulty': 'Intermediate',
                    'skills': ['Django/FastAPI', 'ORM & Database Design', 'REST APIs', 'Authentication', 'Testing (pytest)'],
                    'prerequisites': ['Python basics', 'SQL fundamentals'],
                    'milestones': [
                        'Build Blog Application',
                        'Create REST API',
                        'Add User Authentication',
                        'Deploy to Cloud'
                    ],
                    'resources': [
                        {'type': 'course', 'name': 'Django for Professionals', 'description': 'Production-ready Django'},
                        {'type': 'documentation', 'name': 'FastAPI Docs', 'url': 'https://fastapi.tiangolo.com/'},
                        {'type': 'project', 'name': 'Social Media API', 'description': 'Complex backend project'}
                    ],
                    'market_demand': 'High',
                    'salary_impact': '+20-35%'
                })
            
            # Data Science & AI Path
            if 'AI/ML Framework' not in current_categories:
                suggestions.append({
                    'id': 'python-data-science',
                    'title': 'Data Science & Machine Learning',
                    'description': 'Master data analysis, visualization, and machine learning',
                    'priority': 'High',
                    'category': 'Data Science',
                    'estimatedTime': '4-6 months',
                    'difficulty': 'Intermediate to Advanced',
                    'skills': ['Pandas & NumPy', 'Data Visualization', 'Machine Learning', 'Deep Learning', 'MLOps'],
                    'prerequisites': ['Python', 'Statistics basics', 'Mathematics'],
                    'milestones': [
                        'Complete Data Analysis Project',
                        'Build ML Model',
                        'Create Data Dashboard',
                        'Deploy ML Model to Production'
                    ],
                    'resources': [
                        {'type': 'course', 'name': 'Kaggle Learn', 'url': 'https://www.kaggle.com/learn'},
                        {'type': 'course', 'name': 'Fast.ai Practical Deep Learning', 'description': 'Hands-on ML'},
                        {'type': 'project', 'name': 'End-to-end ML Project', 'description': 'Portfolio project'}
                    ],
                    'market_demand': 'Very High',
                    'salary_impact': '+25-45%'
                })
        
        # Java Ecosystem
        elif lang_lower == 'java':
            suggestions.append({
                'id': 'java-enterprise-development',
                'title': 'Enterprise Java Development',
                'description': 'Master Spring ecosystem and enterprise patterns',
                'priority': 'High',
                'category': 'Backend Development',
                'estimatedTime': '3-4 months',
                'difficulty': 'Intermediate to Advanced',
                'skills': ['Spring Boot', 'Spring Security', 'Microservices', 'JPA/Hibernate', 'Testing'],
                'prerequisites': ['Java fundamentals', 'OOP concepts'],
                'milestones': [
                    'Build Spring Boot Application',
                    'Implement Security & Authentication',
                    'Create Microservices',
                    'Add Monitoring & Logging'
                ],
                'resources': [
                    {'type': 'course', 'name': 'Spring Framework Course', 'description': 'Complete Spring ecosystem'},
                    {'type': 'documentation', 'name': 'Spring Boot Reference', 'url': 'https://spring.io/projects/spring-boot'},
                    {'type': 'project', 'name': 'E-commerce Microservices', 'description': 'Enterprise project'}
                ],
                'market_demand': 'High',
                'salary_impact': '+25-40%'
            })
    
    # === UNIVERSAL SKILL GAPS ===
    
    # Cloud & DevOps (Critical for all developers)
    if 'DevOps' not in current_categories and 'Cloud Platform' not in current_categories:
        suggestions.append({
            'id': 'cloud-devops-fundamentals',
            'title': 'Cloud Computing & DevOps Essentials',
            'description': 'Master containerization, CI/CD, and cloud deployment',
            'priority': 'High',
            'category': 'DevOps',
            'estimatedTime': '2-3 months',
            'difficulty': 'Intermediate',
            'skills': ['Docker & Kubernetes', 'CI/CD Pipelines', 'AWS/Azure/GCP', 'Infrastructure as Code', 'Monitoring'],
            'prerequisites': ['Basic command line', 'Git knowledge'],
            'milestones': [
                'Containerize Application',
                'Set up CI/CD Pipeline',
                'Deploy to Cloud',
                'Implement Monitoring'
            ],
            'resources': [
                {'type': 'course', 'name': 'Docker Mastery', 'description': 'Complete containerization'},
                {'type': 'hands-on', 'name': 'AWS Free Tier Projects', 'description': 'Real cloud experience'},
                {'type': 'certification', 'name': 'AWS Cloud Practitioner', 'description': 'Industry recognition'}
            ],
            'market_demand': 'Very High',
            'salary_impact': '+20-35%'
        })
    
    # Database Skills
    if 'Database' not in current_categories:
        suggestions.append({
            'id': 'database-mastery',
            'title': 'Database Design & Management',
            'description': 'Master both SQL and NoSQL databases for scalable applications',
            'priority': 'Medium',
            'category': 'Database',
            'estimatedTime': '1-2 months',
            'difficulty': 'Beginner to Intermediate',
            'skills': ['SQL Mastery', 'Database Design', 'PostgreSQL/MySQL', 'MongoDB', 'Performance Optimization'],
            'prerequisites': ['Basic programming knowledge'],
            'milestones': [
                'Design Normalized Database',
                'Write Complex Queries',
                'Optimize Performance',
                'Implement Backup Strategy'
            ],
            'resources': [
                {'type': 'course', 'name': 'SQL Complete Course', 'description': 'From basics to advanced'},
                {'type': 'practice', 'name': 'LeetCode Database Problems', 'description': 'Hands-on practice'},
                {'type': 'project', 'name': 'Database Design Project', 'description': 'Real-world application'}
            ],
            'market_demand': 'High',
            'salary_impact': '+15-25%'
        })
    
    # Mobile Development (High growth area)
    if 'Mobile Framework' not in current_categories and experience_score > 50:
        mobile_suggestion = {
            'id': 'mobile-development',
            'title': 'Mobile App Development',
            'description': 'Build cross-platform mobile applications',
            'priority': 'Medium',
            'category': 'Mobile Development',
            'estimatedTime': '3-4 months',
            'difficulty': 'Intermediate',
            'market_demand': 'Very High',
            'salary_impact': '+20-40%'
        }
        
        if primary_language and primary_language.lower() in ['javascript', 'typescript']:
            mobile_suggestion.update({
                'skills': ['React Native', 'Expo', 'Mobile UI/UX', 'App Store Deployment', 'Native Modules'],
                'prerequisites': ['React knowledge', 'JavaScript'],
                'resources': [
                    {'type': 'course', 'name': 'React Native Complete Guide', 'description': 'Mobile development'},
                    {'type': 'project', 'name': 'Social Media App', 'description': 'Full-featured mobile app'}
                ]
            })
        else:
            mobile_suggestion.update({
                'skills': ['Flutter', 'Dart', 'Mobile UI/UX', 'App Store Deployment', 'State Management'],
                'prerequisites': ['OOP concepts', 'Basic programming'],
                'resources': [
                    {'type': 'course', 'name': 'Flutter Complete Course', 'description': 'Cross-platform development'},
                    {'type': 'project', 'name': 'E-commerce Mobile App', 'description': 'Production-ready app'}
                ]
            })
        
        suggestions.append(mobile_suggestion)
    
    # === ADVANCED CAREER PATHS ===
    
    # System Design & Architecture (For senior developers)
    if experience_score > 70:
        suggestions.append({
            'id': 'system-design-architecture',
            'title': 'System Design & Software Architecture',
            'description': 'Design scalable, distributed systems and lead technical decisions',
            'priority': 'High',
            'category': 'Architecture',
            'estimatedTime': '4-6 months',
            'difficulty': 'Advanced',
            'skills': ['System Design Patterns', 'Scalability', 'Distributed Systems', 'Load Balancing', 'Caching Strategies'],
            'prerequisites': ['Backend experience', 'Database knowledge', 'Cloud familiarity'],
            'milestones': [
                'Design High-Level Architecture',
                'Implement Caching Strategy',
                'Build Distributed System',
                'Optimize for Scale'
            ],
            'resources': [
                {'type': 'book', 'name': 'Designing Data-Intensive Applications', 'description': 'System design bible'},
                {'type': 'course', 'name': 'System Design Interview Course', 'description': 'Interview preparation'},
                {'type': 'practice', 'name': 'Design Popular Systems', 'description': 'Hands-on system design'}
            ],
            'market_demand': 'Very High',
            'salary_impact': '+40-70%'
        })
    
    # Cybersecurity (Growing field)
    if experience_score > 40:
        suggestions.append({
            'id': 'cybersecurity-fundamentals',
            'title': 'Cybersecurity & Secure Development',
            'description': 'Learn security best practices and ethical hacking',
            'priority': 'Medium',
            'category': 'Security',
            'estimatedTime': '3-5 months',
            'difficulty': 'Intermediate to Advanced',
            'skills': ['Secure Coding', 'Penetration Testing', 'Network Security', 'Cryptography', 'Security Auditing'],
            'prerequisites': ['Programming experience', 'Network basics'],
            'milestones': [
                'Complete Security Audit',
                'Implement Security Measures',
                'Perform Penetration Test',
                'Get Security Certification'
            ],
            'resources': [
                {'type': 'course', 'name': 'Ethical Hacking Course', 'description': 'Hands-on security'},
                {'type': 'certification', 'name': 'CompTIA Security+', 'description': 'Industry standard'},
                {'type': 'platform', 'name': 'TryHackMe', 'description': 'Practical security challenges'}
            ],
            'market_demand': 'Very High',
            'salary_impact': '+25-45%'
        })
    
    # === PRIORITIZATION AND PERSONALIZATION ===
    
    # Adjust priorities based on current skill level and market trends
    for suggestion in suggestions:
        # Boost priority for complementary skills
        if primary_language:
            if (primary_language.lower() in ['javascript', 'typescript'] and 
                suggestion['category'] in ['Backend Development', 'DevOps']):
                suggestion['priority'] = 'High'
            elif (primary_language.lower() == 'python' and 
                  suggestion['category'] in ['Data Science', 'AI/ML Framework']):
                suggestion['priority'] = 'High'
        
        # Add personalized difficulty assessment
        if experience_score < 30:
            suggestion['recommended_for_beginners'] = suggestion['difficulty'] in ['Beginner', 'Intermediate']
        elif experience_score > 70:
            suggestion['recommended_for_experts'] = suggestion['difficulty'] == 'Advanced'
    
    # Sort by priority and relevance
    priority_order = {'High': 3, 'Medium': 2, 'Low': 1}
    suggestions.sort(key=lambda x: (
        priority_order.get(x['priority'], 0),
        x.get('salary_impact', '').replace('%', '').replace('+', '').split('-')[-1] if x.get('salary_impact') else '0'
    ), reverse=True)
    
    return suggestions[:8]  # Top 8 most relevant suggestions

@router.get("/repositories/{user_id}")
async def get_user_repositories(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get detailed repository information for a user (authenticated)"""
    try:
        # Verify user can access these repositories
        if str(current_user.id) != user_id and current_user.user_type != "hr":
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not current_user.github_token or not current_user.github_username:
            return {"repositories": []}
        
        # Initialize GitHub scanner with user's token
        scanner = GitHubScanner(current_user.github_token)
        
        # Get ALL user's repositories but only evaluate top 15 most recent
        repositories = await scanner.fetch_user_repositories(
            current_user.github_username, 
            include_forks=False, 
            max_repos=None,
            evaluate_limit=15
        )
        
        return {"repositories": repositories}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get repositories for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get repositories: {str(e)}")

@router.get("/external-repositories/{user_identifier}")
async def get_external_user_repositories(
    user_identifier: str
):
    """Get detailed repository information for external users or cached data (no authentication required)"""
    try:
        # Get database connection
        from app.db_connection import get_database as get_db_connection
        db = await get_db_connection()
        
        logger.info(f"Getting external repositories for identifier: {user_identifier}")
        
        # Check if this is an external user format (external_username)
        if user_identifier.startswith("external_"):
            username = user_identifier.replace("external_", "")
            logger.info(f"Fetching repositories for external user: {username}")
            
            # Get GitHub token from environment
            github_token = os.getenv("GITHUB_TOKEN", "")
            if not github_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No GitHub token available for external scanning"
                )
            
            # Initialize GitHub scanner
            scanner = GitHubScanner(github_token)
            
            # Get ALL user's repositories but only evaluate top 15 most recent
            repositories = await scanner.fetch_user_repositories(
                username, 
                include_forks=False, 
                max_repos=None,
                evaluate_limit=15
            )
            
            return {"repositories": repositories}
        
        # Otherwise, try to get cached repositories from database
        try:
            if db is not None:
                repositories = await performance_service.get_optimized_user_repositories(user_identifier)
                if repositories:
                    return {"repositories": repositories}
        except Exception as e:
            logger.warning(f"Failed to get cached repositories: {e}")
        
        # If no data found, return empty
        logger.info(f"No repositories found for user: {user_identifier}")
        return {"repositories": []}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get external repositories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get repositories: {str(e)}")

async def perform_repository_scan(
    scan_id: str,
    github_url: str,
    scan_type: str,
    user_id: str,
    github_token: str,
    db
):
    """Enhanced background task to perform repository scanning with detailed progress tracking"""
    try:
        # Initialize progress tracking if not exists
        if scan_id not in scan_progress_store:
            scan_progress_store[scan_id] = ScanProgress(
                scan_id=scan_id,
                status="pending",
                progress=0,
                current_repo=None,
                total_repos=0,
                message="Initializing scan..."
            )
        
        # Update progress
        scan_progress_store[scan_id].status = "scanning"
        scan_progress_store[scan_id].message = "Initializing GitHub scanner..."
        scan_progress_store[scan_id].progress = 5
        
        # Initialize scanner and evaluation engine
        scanner = GitHubScanner(github_token)
        evaluator = EvaluationEngine()
        
        # Parse GitHub URL to extract username/repo
        is_valid, username, repo_name = await scanner.validate_github_url(github_url)
        if not is_valid or not username:
            raise Exception("Invalid GitHub URL")
        
        scan_progress_store[scan_id].message = f"Fetching repositories for {username}..."
        scan_progress_store[scan_id].progress = 10
        
        # Fetch repositories based on scan type
        if repo_name:
            # Single repository scan
            try:
                repo_analysis = await scanner.get_repository_analysis(f"{username}/{repo_name}")
                repositories = [repo_analysis["basic_info"]]
            except Exception as e:
                raise Exception(f"Failed to analyze repository {username}/{repo_name}: {str(e)}")
        else:
            # User profile scan - fetch ALL non-fork repos (forks are copies)
            repositories = await scanner.fetch_user_repositories(
                username, 
                include_forks=False,  # Exclude forks (they are copies, not original work)
                max_repos=None,  # Fetch all repositories
                evaluate_limit=15  # Only evaluate top 15 most recent
            )
        
        if not repositories:
            raise Exception(f"No repositories found for {username}")
        
        scan_progress_store[scan_id].total_repos = len(repositories)
        scan_progress_store[scan_id].message = f"Found {len(repositories)} repositories. Starting detailed analysis..."
        scan_progress_store[scan_id].progress = 20
        
        # Process each repository with detailed progress tracking
        processed_repos = 0
        successful_evaluations = 0
        
        for i, repo_data in enumerate(repositories):
            try:
                scan_progress_store[scan_id].current_repo = repo_data["name"]
                scan_progress_store[scan_id].progress = 20 + int((i / len(repositories)) * 70)  # 20-90% for processing
                scan_progress_store[scan_id].status = "analyzing"
                scan_progress_store[scan_id].message = f"Analyzing {repo_data['name']} ({i+1}/{len(repositories)})"
                
                # Enhanced repository document with additional metadata
                repo_doc = {
                    "user_id": user_id,
                    "github_id": repo_data["id"],
                    "name": repo_data["name"],
                    "full_name": repo_data["full_name"],
                    "description": repo_data.get("description", ""),
                    "language": repo_data.get("language"),
                    "languages": repo_data.get("languages", {}),
                    "stars": repo_data.get("stargazers_count", 0),
                    "forks": repo_data.get("forks_count", 0),
                    "watchers": repo_data.get("watchers_count", 0),
                    "size": repo_data.get("size", 0),
                    "created_at": datetime.fromisoformat(repo_data["created_at"].replace('Z', '+00:00')) if repo_data.get("created_at") else datetime.utcnow(),
                    "updated_at": datetime.fromisoformat(repo_data["updated_at"].replace('Z', '+00:00')) if repo_data.get("updated_at") else datetime.utcnow(),
                    "pushed_at": datetime.fromisoformat(repo_data["pushed_at"].replace('Z', '+00:00')) if repo_data.get("pushed_at") else None,
                    "is_fork": repo_data.get("fork", False),
                    "is_private": repo_data.get("private", False),
                    "is_archived": repo_data.get("archived", False),
                    "is_disabled": repo_data.get("disabled", False),
                    "topics": repo_data.get("topics", []),
                    "license": repo_data.get("license", {}).get("name") if repo_data.get("license") else None,
                    "default_branch": repo_data.get("default_branch", "main"),
                    "clone_url": repo_data.get("clone_url", ""),
                    "html_url": repo_data.get("html_url", ""),
                    "homepage": repo_data.get("homepage"),
                    "open_issues_count": repo_data.get("open_issues_count", 0),
                    "commit_count": repo_data.get("commit_count", 0),
                    "contributor_count": repo_data.get("contributor_count", 0),
                    "has_readme": repo_data.get("has_readme", False),
                    "has_license": repo_data.get("has_license", False),
                    "has_contributing": repo_data.get("has_contributing", False),
                    "has_tests": repo_data.get("has_tests", False),
                    "is_template": repo_data.get("is_template", False),
                    "scanned_at": datetime.utcnow()
                }
                
                # Save or update repository in database
                if db and db.repositories:
                    existing_repo = await db.repositories.find_one({
                        "user_id": user_id,
                        "github_id": repo_data["id"]
                    })
                    
                    if existing_repo:
                        await db.repositories.update_one(
                            {"_id": existing_repo["_id"]},
                            {"$set": repo_doc}
                        )
                        repo_id = str(existing_repo["_id"])
                    else:
                        result = await db.repositories.insert_one(repo_doc)
                        repo_id = str(result.inserted_id)
                else:
                    # Mock repo_id for testing without database
                    repo_id = f"repo_{repo_data['id']}"
                
                # Evaluate repository with enhanced metrics
                evaluation = await evaluator.evaluate_repository(repo_data, user_id)
                evaluation["repo_id"] = repo_id
                evaluation["scan_id"] = scan_id
                evaluation["scan_type"] = scan_type
                
                # Save evaluation to database
                if db and db.evaluations:
                    await db.evaluations.replace_one(
                        {"repo_id": repo_id},
                        evaluation,
                        upsert=True
                    )
                
                successful_evaluations += 1
                processed_repos += 1
                
            except Exception as e:
                logger.warning(f"Failed to process repository {repo_data.get('name', 'unknown')}: {e}")
                processed_repos += 1
                continue
        
        # Update user's last scan date
        if db and db.users:
            await db.users.update_one(
                {"_id": user_id},
                {"$set": {"last_scan": datetime.utcnow()}}
            )
        
        # Final progress update
        scan_progress_store[scan_id].status = "completed"
        scan_progress_store[scan_id].progress = 100
        scan_progress_store[scan_id].message = f"Analysis complete! Successfully evaluated {successful_evaluations} out of {processed_repos} repositories"
        scan_progress_store[scan_id].current_repo = None
        
        # Store summary statistics
        scan_progress_store[scan_id].summary = {
            "total_repositories": len(repositories),
            "processed_repositories": processed_repos,
            "successful_evaluations": successful_evaluations,
            "failed_evaluations": processed_repos - successful_evaluations,
            "scan_duration": "N/A",  # Could calculate actual duration
            "username": username,
            "scan_type": scan_type
        }
        
    except Exception as e:
        logger.error(f"Repository scan failed for scan_id {scan_id}: {e}")
        scan_progress_store[scan_id].status = "error"
        scan_progress_store[scan_id].message = f"Scan failed: {str(e)}"
        scan_progress_store[scan_id].progress = 0

@router.post("/validate-github-url")
async def validate_github_url(
    request: GitHubUrlRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Validate a GitHub URL and extract user/repo information (authenticated)"""
    try:
        # URL is already validated by the Pydantic model
        scanner = GitHubScanner(current_user.github_token)
        is_valid, username, repo_name = await scanner.validate_github_url(request.url)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub URL format. Supported formats: https://github.com/username, https://github.com/username/repo, https://github.com/username?tab=repositories, https://github.com/username?tab=overview, https://github.com/username?tab=projects, https://github.com/username?tab=packages, https://github.com/username?tab=stars"
            )
        
        # Get user information
        user_info = None
        if username:
            try:
                user_info = await scanner.get_user_info(username)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"GitHub user not found: {str(e)}"
                )
        
        return {
            "valid": is_valid,
            "username": username,
            "repository": repo_name,
            "user_info": user_info,
            "url_type": "repository" if repo_name else "user"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"URL validation failed: {str(e)}"
        )

@router.post("/validate-github-url-public")
async def validate_github_url_public(request: GitHubUrlRequest):
    """Validate a GitHub URL and extract user/repo information (public endpoint)"""
    try:
        from app.core.config import settings
        
        # Use system GitHub token for validation
        if not settings.github_token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub validation service temporarily unavailable"
            )
        
        scanner = GitHubScanner(settings.github_token)
        is_valid, username, repo_name = await scanner.validate_github_url(request.url)
        
        if not is_valid:
            return {
                "valid": False,
                "error": "Invalid GitHub URL format",
                "supported_formats": [
                    "https://github.com/username",
                    "https://github.com/username/repo",
                    "https://github.com/username?tab=repositories",
                    "https://github.com/username?tab=overview"
                ],
                "example": "https://github.com/octocat"
            }
        
        # Get basic user information to verify user exists
        user_info = None
        user_exists = False
        if username:
            try:
                user_info = await scanner.get_user_info(username)
                user_exists = True
            except Exception as e:
                return {
                    "valid": False,
                    "error": f"GitHub user '{username}' not found",
                    "suggestion": "Please check the username spelling and try again",
                    "username": username
                }
        
        return {
            "valid": is_valid and user_exists,
            "username": username,
            "repository": repo_name,
            "user_info": {
                "login": user_info.get("login") if user_info else None,
                "name": user_info.get("name") if user_info else None,
                "public_repos": user_info.get("public_repos") if user_info else None,
                "avatar_url": user_info.get("avatar_url") if user_info else None
            } if user_info else None,
            "url_type": "repository" if repo_name else "user"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "valid": False,
            "error": f"URL validation failed: {str(e)}",
            "suggestion": "Please check your internet connection and try again"
        }

@router.get("/search-repositories")
async def search_repositories(
    search_params: SearchParams = Depends(),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Search for repositories using GitHub search API with validation"""
    try:
        # Validate search query
        if search_params.query:
            search_params.query = InputSanitizer.sanitize_string(search_params.query, max_length=200)
        
        scanner = GitHubScanner(current_user.github_token)
        results = await scanner.search_repositories(
            query=search_params.query or "",
            sort=pagination.sort_by or "stars",
            order=pagination.order or "desc",
            limit=pagination.limit
        )
        
        return {
            "query": search_params.query,
            "total_results": len(results),
            "repositories": results,
            "pagination": {
                "page": pagination.page,
                "limit": pagination.limit,
                "sort_by": pagination.sort_by,
                "order": pagination.order
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Repository search failed: {str(e)}"
        )

@router.get("/rate-limit")
async def get_rate_limit_status(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get GitHub API rate limit status"""
    try:
        scanner = GitHubScanner(current_user.github_token)
        rate_limit = await scanner.get_rate_limit_status()
        
        return rate_limit
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit status: {str(e)}"
        )

@router.get("/repository-analysis/{owner}/{repo}")
async def get_repository_analysis(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get comprehensive analysis of a specific repository"""
    try:
        repo_full_name = f"{owner}/{repo}"
        
        # Try cache first
        cached_analysis = await cache_service.get_repository_analysis(repo_full_name)
        if cached_analysis:
            return cached_analysis
        
        scanner = GitHubScanner(current_user.github_token)
        analysis = await scanner.get_repository_analysis(repo_full_name)
        
        result = {
            "repository": repo_full_name,
            "analysis": analysis,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        # Cache for 1 hour
        await cache_service.cache_repository_analysis(repo_full_name, result, 3600)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Repository analysis failed: {str(e)}"
        )

@router.get("/user-info/{username}")
async def get_github_user_info(username: str, request: Request):
    """Get detailed information about a GitHub user - redirects to quick scan"""
    try:
        # Import the quick scan function
        from app.routers.quick_scan import quick_scan_get
        
        # Call the quick scan endpoint directly
        result = await quick_scan_get(username, request, force_refresh=False)
        return result
    except Exception as e:
        logger.error(f"Failed to get user info for {username}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user information: {str(e)}"
        )
    try:
        # Validate username
        if not username or len(username.strip()) == 0:
            raise HTTPException(
                status_code=422,
                detail="Username cannot be empty"
            )
        
        # Clean username (remove any special characters)
        username = username.strip()
        
        # Validate username format (basic GitHub username validation)
        import re
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-])*[a-zA-Z0-9]$|^[a-zA-Z0-9]$', username):

            raise HTTPException(
                status_code=422,
                detail="Invalid GitHub username format"
            )
        
        logger.info(f"Getting user info for: {username}")
        
        # Try cache first
        try:
            cached_user_info = await cache_service.get_github_user_info(username)
            if cached_user_info:
                logger.info(f"Returning cached user info for: {username}")
                return cached_user_info
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        # Get GitHub token from settings
        from app.core.config import get_github_token
        github_token = get_github_token()
        
        logger.info(f"GitHub token retrieved: {'Yes' if github_token else 'No'}")
        if github_token:
            logger.info(f"Token starts with: {github_token[:10]}...")
        
        if not github_token:
            logger.error("No GitHub token configured")
            raise HTTPException(
                status_code=503,
                detail="GitHub API service is temporarily unavailable. Please try again later."
            )
        
        # Get user information directly from GitHub API
        logger.info(f"Fetching user info from GitHub API for: {username}")
        import httpx
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BroskiesHub-API"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(f"https://api.github.com/users/{username}", headers=headers)
                
                if response.status_code == 404:
                    raise HTTPException(
                        status_code=404,
                        detail=f"GitHub user '{username}' not found"
                    )
                elif response.status_code != 200:
                    logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=503,
                        detail="GitHub API service is temporarily unavailable. Please try again later."
                    )
                
                user_info = response.json()
                
            except httpx.TimeoutException:
                logger.error(f"GitHub API timeout for user: {username}")
                raise HTTPException(
                    status_code=503,
                    detail="GitHub API request timed out. Please try again later."
                )
            except Exception as e:
                logger.error(f"GitHub API request failed: {e}")
                raise HTTPException(
                    status_code=503,
                    detail="GitHub API service is temporarily unavailable. Please try again later."
                )
        
        logger.info(f"Successfully retrieved user info for: {username}")
        
        # Enhance user info with contribution calendar data
        try:
            logger.info(f"Enhancing user info with contribution calendar for: {username}")
            from app.services.github_graphql_client import GitHubGraphQLClient
            
            graphql_client = GitHubGraphQLClient(github_token)
            calendar_data = await graphql_client.get_contribution_calendar(username)
            
            # Add contribution calendar to user info
            user_info["contribution_calendar"] = await _calculate_contribution_metrics(calendar_data, username)
            logger.info(f"Successfully added contribution calendar to user info for: {username}")
            
        except Exception as calendar_error:
            logger.warning(f"Failed to add contribution calendar to user info for {username}: {calendar_error}")
            user_info["contribution_calendar"] = {
                "error": "Contribution calendar unavailable",
                "reason": str(calendar_error)
            }
        
        # Cache enhanced user info for 2 hours
        try:
            await cache_service.cache_github_user_info(username, user_info, 7200)
            logger.info(f"Cached enhanced user info for: {username}")
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
        
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user information for {username}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user information: {str(e)}"
        )

@router.get("/contribution-calendar/{username}")
async def get_contribution_calendar(
    username: str,
    current_user: User = Depends(get_current_user),
    from_date: Optional[str] = None
):
    """Get GitHub contribution calendar data using GraphQL with caching and streak calculation"""
    try:
        logger.info(f"Getting contribution calendar for: {username}")
        
        # Check cache first for contribution calendar data
        cache_key = f"contribution_calendar_{username}_{from_date or 'all'}"
        try:
            cached_calendar = await cache_service.get(cache_key, "contribution_calendars")
            if cached_calendar:
                logger.info(f"Returning cached contribution calendar for: {username}")
                return cached_calendar
        except Exception as cache_error:
            logger.warning(f"Cache get failed for contribution calendar: {cache_error}")
        
        # Import GraphQL client
        from app.services.github_graphql_client import GitHubGraphQLClient
        
        # Use the user's GitHub token or environment token
        github_token = current_user.github_token if hasattr(current_user, 'github_token') and current_user.github_token else os.getenv("GITHUB_TOKEN")
        
        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub token not available"
            )
        
        # Initialize GraphQL client
        graphql_client = GitHubGraphQLClient(github_token)
        
        try:
            # Get contribution calendar data using GraphQL
            logger.info(f"Fetching contribution calendar from GraphQL for: {username}")
            calendar_data = await graphql_client.get_contribution_calendar(username, from_date)
            
            # Calculate contribution streaks and activity patterns
            enhanced_calendar = await _calculate_contribution_metrics(calendar_data, username)
            
            # Prepare response with enhanced data
            response = {
                "username": username,
                "contribution_calendar": enhanced_calendar,
                "data_source": "graphql",
                "query_timestamp": datetime.utcnow().isoformat(),
                "from_date": from_date,
                "cache_duration": 3600  # 1 hour cache
            }
            
            # Cache the enhanced calendar data for 1 hour
            try:
                await cache_service.set(cache_key, response, "contribution_calendars", 3600)
                logger.info(f"Cached contribution calendar for: {username}")
            except Exception as cache_error:
                logger.warning(f"Cache set failed for contribution calendar: {cache_error}")
            
            return response
            
        except Exception as graphql_error:
            logger.warning(f"GraphQL contribution calendar failed for {username}: {graphql_error}")
            
            # Fallback to basic activity data using REST API
            logger.info(f"Falling back to REST API for contribution data: {username}")
            fallback_data = await _get_fallback_contribution_data(username, github_token, from_date)
            
            response = {
                "username": username,
                "contribution_calendar": fallback_data,
                "data_source": "rest_fallback",
                "query_timestamp": datetime.utcnow().isoformat(),
                "from_date": from_date,
                "fallback_reason": str(graphql_error)
            }
            
            return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get contribution calendar for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get contribution calendar: {str(e)}"
        )

@router.get("/comprehensive-profile/{username}")
async def get_comprehensive_github_profile(
    username: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get comprehensive GitHub profile analysis using enhanced scanner with GraphQL"""
    try:
        # Try cache first
        cache_key = f"comprehensive_profile_{username}"
        try:
            cached_profile = await cache_service.get(cache_key, "comprehensive_profiles")
            if cached_profile:
                return cached_profile
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        # Use enhanced comprehensive scanner with GraphQL support
        from app.services.github_comprehensive_scanner import GitHubComprehensiveScanner
        
        # Get GitHub token
        github_token = current_user.github_token if hasattr(current_user, 'github_token') and current_user.github_token else os.getenv("GITHUB_TOKEN")
        
        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub token not available"
            )
        
        # Initialize comprehensive scanner with GraphQL support
        scanner = GitHubComprehensiveScanner(github_token)
        
        # Get comprehensive profile with GraphQL enhancements
        logger.info(f"Getting comprehensive profile with PR/Issue analysis for: {username}")
        comprehensive_profile = await scanner.get_comprehensive_user_profile(username)
        
        # Add pull request and issue analysis for top repositories
        try:
            repositories = comprehensive_profile.get("repository_overview", {}).get("repositories", [])
            top_repos = sorted(repositories, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:5]
            
            logger.info(f"Analyzing pull requests and issues for {len(top_repos)} top repositories")
            
            # Analyze pull requests
            pr_analysis = await scanner.analyze_pull_requests_comprehensive(username, top_repos)
            comprehensive_profile["pull_request_analysis"] = pr_analysis
            
            # Analyze issues
            issue_analysis = await scanner.analyze_issues_comprehensive(username, top_repos)
            comprehensive_profile["issue_analysis"] = issue_analysis
            
            logger.info(f"Successfully added PR/Issue analysis to comprehensive profile for: {username}")
            
        except Exception as analysis_error:
            logger.warning(f"Failed to add PR/Issue analysis for {username}: {analysis_error}")
            comprehensive_profile["pull_request_analysis"] = scanner.pr_analyzer._empty_pr_analysis()
            comprehensive_profile["issue_analysis"] = scanner.issue_analyzer._empty_issue_analysis()
        
        # Prepare enhanced response
        enhanced_profile = {
            "username": username,
            "profile": comprehensive_profile,
            "generated_at": datetime.utcnow().isoformat(),
            "data_source": "github_api_comprehensive",
            "includes_pr_analysis": "pull_request_analysis" in comprehensive_profile,
            "includes_issue_analysis": "issue_analysis" in comprehensive_profile
        }
        
        # Cache enhanced profile for 1 hour
        try:
            await cache_service.set(cache_key, enhanced_profile, "comprehensive_profiles", 3600)
            logger.info(f"Cached enhanced comprehensive profile for: {username}")
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
        
        return enhanced_profile
        
    except Exception as e:
        logger.error(f"Failed to get comprehensive profile for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comprehensive profile: {str(e)}"
        )

# Removed get_current_user_optional function as it's no longer needed

def format_basic_repo_data(repo: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format repository with basic information only (no analysis/scoring).
    
    This function provides fast repository display by extracting only basic
    metadata from GitHub API responses without performing any code analysis
    or evaluation. This enables immediate display of all repositories without
    the performance overhead of detailed analysis.
    
    **Design Decision**: Evaluation is intentionally skipped to provide
    sub-5-second response times for displaying all user repositories.
    
    **Future Enhancement**: When scoring is needed, this function can be
    replaced with a call to the evaluation engine. The placeholder fields
    (analysis, acid_scores, quality_metrics, overall_score) are included
    to maintain API compatibility for future scoring integration.
    
    Args:
        repo: Raw repository data from GitHub API containing basic metadata
        
    Returns:
        Dictionary containing:
        - Basic repository fields (name, description, language, stars, etc.)
        - PR and issue counts (if available)
        - Placeholder scoring fields set to None
        - Metadata flags (analysis_available: False, display_only: True)
        
    Example:
        >>> repo_data = {"name": "my-repo", "stargazers_count": 100, ...}
        >>> formatted = format_basic_repo_data(repo_data)
        >>> formatted["analysis"]  # None
        >>> formatted["display_only"]  # True
    """
    # Extract PR and issue data if available
    pull_requests = repo.get("pull_requests", {})
    issues = repo.get("issues", {})
    
    return {
        # Basic repository fields
        "id": repo.get("id"),
        "name": repo.get("name", ""),
        "description": repo.get("description", ""),
        "language": repo.get("language"),
        "stargazers_count": repo.get("stargazers_count", 0),
        "forks_count": repo.get("forks_count", 0),
        "watchers_count": repo.get("watchers_count", 0),
        "size": repo.get("size", 0),
        "topics": repo.get("topics", []),
        "created_at": repo.get("created_at"),
        "updated_at": repo.get("updated_at"),
        "pushed_at": repo.get("pushed_at"),
        "private": repo.get("private", False),
        "fork": repo.get("fork", False),
        "archived": repo.get("archived", False),
        "open_issues_count": repo.get("open_issues_count", 0),
        "license": repo.get("license", {}).get("name") if repo.get("license") else None,
        "default_branch": repo.get("default_branch", "main"),
        
        # PR and Issue counts for frontend display
        "pullRequestsCount": pull_requests.get("total", 0),
        "issuesCount": issues.get("total", 0),
        
        # Detailed PR and issue data (if available)
        "pull_requests": pull_requests if pull_requests else None,
        "issues": issues if issues else None,
        
        # Placeholder fields for future scoring (set to None)
        "analysis": None,
        "acid_scores": None,
        "quality_metrics": None,
        "overall_score": None,
        
        # Metadata flags
        "analysis_available": False,
        "display_only": True
    }

@router.get("/scan-external-user/{username}")
async def scan_external_github_user(
    username: str, 
    request: Request,
    force_refresh: bool = False
):
    """
    Fast scan for external GitHub user - displays all repositories without evaluation.
    
    **IMPORTANT**: This endpoint has been optimized for fast display by skipping
    repository evaluation and scoring. All repositories are displayed with basic
    metadata only.
    
    **Performance Target**: < 5 seconds response time
    
    **What This Endpoint Does**:
    - Fetches user profile and all public repositories from GitHub API
    - Displays ALL repositories without filtering by evaluation criteria
    - Returns basic repository metadata (name, language, stars, etc.)
    - Skips code analysis and ACID scoring for fast response
    
    **What This Endpoint Does NOT Do**:
    - Does NOT perform code analysis or evaluation
    - Does NOT calculate ACID scores or quality metrics
    - Does NOT filter repositories by evaluation criteria
    - Does NOT generate learning roadmaps (requires evaluation data)
    
    **Future Scoring Integration**:
    To add scoring back in the future:
    1. Replace `format_basic_repo_data()` calls with evaluation engine calls
    2. Update `scanType` from "display_only" to "evaluated"
    3. Set `evaluationSkipped` to False in scanMetadata
    4. Calculate and set `overallScore` based on repository analysis
    5. Generate roadmap using evaluation data
    
    Args:
        username: GitHub username to scan
        
    Returns:
        Comprehensive user profile with:
        - All repositories (basic data only, no scoring)
        - User profile information
        - Language statistics
        - Tech stack detection
        - Null scoring fields (overallScore, roadmap, etc.)
        - Metadata indicating evaluation was skipped
        
    Response Time:
        Typically 2-4 seconds for users with 20-50 repositories
        
    Example Response:
        {
            "username": "johndoe",
            "repositoryCount": 25,
            "overallScore": null,
            "overallScore_unavailable_reason": "Evaluation skipped...",
            "scanType": "display_only",
            "repositories": [...],  # All 25 repos with basic data
            "scanMetadata": {
                "evaluationSkipped": true,
                "analysisDepth": "basic",
                "repositoriesAnalyzed": 0
            }
        }
    """
    try:
        # Start performance timing
        import time
        scan_start_time = time.time()
        
        # Detect user type based on authentication status
        routing_info = await UserTypeDetector.route_user_operation(request, username, "scan")
        user_type = routing_info["user_type"]
        user_id = routing_info["user_id"]
        
        logger.info(f"[{user_type.upper()} SCAN] Starting optimized scan for user: {username}")
        logger.info(f"[{user_type.upper()} SCAN] User ID: {user_id}")
        print(f"\n{'='*60}")
        print(f"[{user_type.upper()} SCAN] Starting scan for: {username}")
        print(f"{'='*60}\n")
        
        # Get GitHub token from settings (no authentication required for external scans)
        from app.core.config import settings
        github_token = settings.github_token
        
        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No GitHub token available. Please authenticate or set GITHUB_TOKEN environment variable."
            )
        
        # CACHING DISABLED - Always fetch fresh data to ensure PR/issue data is up-to-date
        # This ensures users always see the latest PR/issue information
        logger.info(f"Fetching fresh data for {username} (caching disabled)")
        
        # Invalidate any existing cache for this user before fresh scan
        try:
            db = await get_database()
            if db is not None:
                deleted = await db.fast_scan_cache.delete_many({"username": username})
                if deleted.deleted_count > 0:
                    logger.info(f"🗑️ Invalidated {deleted.deleted_count} cached entries for {username}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
        
        # Generate scan ID for progress tracking
        import uuid
        scan_id = str(uuid.uuid4())
        
        # Try to get authenticated user ID from token for WebSocket broadcasting
        websocket_user_id = "external_user"  # Default
        try:
            # This endpoint doesn't require auth, but if a token is provided, use it
            from fastapi import Request
            from app.core.security import get_current_user_token
            # We'll use external_user for now since this is an unauthenticated endpoint
            # The WebSocket will connect with the user's actual ID separately
        except:
            pass
        
        # Start progress tracking with faster updates
        await start_scan_progress(scan_id, websocket_user_id, 0)
        
        try:
            # ============================================================================
            # FAST DISPLAY MODE: Use Basic Scanner Only
            # ============================================================================
            # Use basic GitHubScanner instead of comprehensive scanner for speed
            # This skips all heavy operations like contribution calendar, PR/issue analysis
            # ============================================================================
            
            await update_scan_phase(scan_id, ScanPhase.CONNECTING_GITHUB)
            scanner = GitHubScanner(github_token)
            
            # Get basic user profile (fast - single API call)
            await update_scan_phase(scan_id, ScanPhase.FETCHING_USER_PROFILE)
            logger.info(f"[FAST SCAN] Fetching basic profile for: {username}")
            print(f"[FAST SCAN] Fetching basic profile for: {username}")
            
            user_info = await scanner.get_user_info(username)
            
            # Get all repositories (fast - no detailed analysis)
            logger.info(f"[FAST SCAN] Fetching repositories for: {username}")
            print(f"[FAST SCAN] Fetching repositories for: {username}")
            
            # Fetch repositories without evaluation limits
            result = await scanner.fetch_user_repositories(
                username,
                include_forks=False,
                max_display_repos=100,  # Get up to 100 repos
                evaluate_limit=0,  # Don't mark any for evaluation
                return_metadata=True
            )
            
            repositories = result.get("repositories", [])
            metadata = result.get("metadata", {})
            
            logger.info(f"[FAST SCAN] Fetched {len(repositories)} repositories")
            print(f"[FAST SCAN] Fetched {len(repositories)} repositories")
            
            # ============================================================================
            # FETCH PR/ISSUE DATA FOR REPOSITORIES
            # ============================================================================
            # Fetch PR and issue data for repositories (up to first 20 to avoid rate limits)
            logger.info(f"[PR/ISSUE FETCH] Fetching PR/issue data for repositories")
            from app.services.github_api_service import GitHubAPIService
            github_api = GitHubAPIService(github_token, cache_service=cache_service)
            
            for idx, repo in enumerate(repositories[:20]):  # Limit to first 20 repos
                try:
                    repo_full_name = repo.get('full_name')
                    if not repo_full_name or '/' not in repo_full_name:
                        continue
                    
                    owner, repo_name = repo_full_name.split('/')
                    logger.info(f"[PR/ISSUE] Fetching data for {repo_full_name}")
                    
                    # Fetch PRs
                    prs = await github_api.get_pull_requests(owner, repo_name, state='all', per_page=100)
                    
                    if prs:
                        open_prs = [pr for pr in prs if pr.get('state') == 'open']
                        closed_prs = [pr for pr in prs if pr.get('state') == 'closed' and not pr.get('merged_at')]
                        merged_prs = [pr for pr in prs if pr.get('merged_at')]
                        
                        # Calculate average merge time
                        merge_times = []
                        for pr in merged_prs:
                            if pr.get('created_at') and pr.get('merged_at'):
                                created = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                                merged = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                                merge_times.append((merged - created).total_seconds() / 3600)
                        
                        avg_merge_time = sum(merge_times) / len(merge_times) if merge_times else None
                        
                        # Format recent PRs
                        recent_prs = []
                        for pr in prs[:10]:
                            recent_prs.append({
                                'number': pr.get('number'),
                                'title': pr.get('title'),
                                'author': pr.get('user', {}).get('login', 'unknown'),
                                'state': 'merged' if pr.get('merged_at') else pr.get('state', 'open'),
                                'createdAt': pr.get('created_at'),
                                'mergedAt': pr.get('merged_at'),
                                'url': pr.get('html_url', '')
                            })
                        
                        repo['pull_requests'] = {
                            'total': len(prs),
                            'open': len(open_prs),
                            'closed': len(closed_prs),
                            'merged': len(merged_prs),
                            'recent': recent_prs,
                            'avgTimeToMerge': avg_merge_time
                        }
                        logger.info(f"[PR/ISSUE] Fetched {len(prs)} PRs for {repo_name}")
                    
                    # Fetch Issues
                    issues = await github_api.get_issues(owner, repo_name, state='all', per_page=100)
                    
                    if issues:
                        open_issues = [issue for issue in issues if issue.get('state') == 'open']
                        closed_issues = [issue for issue in issues if issue.get('state') == 'closed']
                        
                        # Calculate average close time
                        close_times = []
                        for issue in closed_issues:
                            if issue.get('created_at') and issue.get('closed_at'):
                                created = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
                                closed = datetime.fromisoformat(issue['closed_at'].replace('Z', '+00:00'))
                                close_times.append((closed - created).total_seconds() / 3600)
                        
                        avg_close_time = sum(close_times) / len(close_times) if close_times else None
                        
                        # Aggregate labels
                        labels_dist = {}
                        for issue in issues:
                            for label in issue.get('labels', []):
                                label_name = label.get('name', 'unknown')
                                labels_dist[label_name] = labels_dist.get(label_name, 0) + 1
                        
                        # Format recent issues
                        recent_issues = []
                        for issue in issues[:10]:
                            recent_issues.append({
                                'number': issue.get('number'),
                                'title': issue.get('title'),
                                'author': issue.get('user', {}).get('login', 'unknown'),
                                'state': issue.get('state', 'open'),
                                'createdAt': issue.get('created_at'),
                                'closedAt': issue.get('closed_at'),
                                'url': issue.get('html_url', ''),
                                'labels': [label.get('name') for label in issue.get('labels', [])]
                            })
                        
                        repo['issues'] = {
                            'total': len(issues),
                            'open': len(open_issues),
                            'closed': len(closed_issues),
                            'recent': recent_issues,
                            'avgTimeToClose': avg_close_time,
                            'labelsDistribution': labels_dist
                        }
                        logger.info(f"[PR/ISSUE] Fetched {len(issues)} issues for {repo_name}")
                    
                except Exception as e:
                    logger.error(f"[PR/ISSUE] Failed to fetch PR/issue data for {repo.get('name')}: {e}")
                    continue
            
            logger.info(f"[PR/ISSUE FETCH] Completed PR/issue data fetching")
            
            # Create minimal comprehensive profile structure for compatibility
            comprehensive_profile = {
                "basic_info": user_info,
                "repository_overview": {"repositories": repositories},
                "contribution_stats": {},
                "activity_calendar": {},
                "collaboration_metrics": {},
                "language_statistics": {},
                "achievement_metrics": {},
                "social_metrics": {},
                "recent_activity": {},
                "organizations": [],
                "pull_request_analysis": {},
                "issue_analysis": {},
                "contribution_calendar": {}
            }
        
            # Skip ANALYZING_REPOSITORIES phase - no analysis is performed in fast display mode
            
            # Update total repositories count
            total_repos = len(repositories)
            if total_repos > 0:
                await update_repository_progress(scan_id, 0, f"Found {total_repos} repositories - formatting for display")
            
            # ============================================================================
            # FAST DISPLAY MODE: No Evaluation/Scoring
            # ============================================================================
            # Format all repositories with basic data only (no evaluation/scoring)
            # This provides fast display without requiring evaluation engine processing
            #
            # TODO: To enable scoring in the future, replace this section with:
            #   1. Filter repositories for evaluation (e.g., top 15 most recent)
            #   2. Call evaluation engine for each repository
            #   3. Calculate ACID scores and quality metrics
            #   4. Update scanMetadata to reflect evaluation was performed
            #
            # Example future implementation:
            #   from app.services.evaluation_engine import EvaluationEngine
            #   evaluator = EvaluationEngine()
            #   for repo in repositories[:15]:  # Evaluate top 15
            #       analysis = await evaluator.evaluate_repository(repo)
            #       repo['analysis'] = analysis
            #       repo['acid_scores'] = analysis['acid_scores']
            # ============================================================================
            
            logger.info(f"[REPO DISPLAY] Displaying {total_repos} repositories without evaluation")
            print(f"[REPO DISPLAY] Displaying {total_repos} repositories without evaluation")
            
            # Use simple formatting for all repositories - no filtering, no analysis
            formatting_start = time.time()
            detailed_repositories = [format_basic_repo_data(repo) for repo in repositories]
            formatting_time = time.time() - formatting_start
            
            # Verify count consistency
            logger.info(f"[COUNT VERIFICATION] Total repos: {total_repos}, Formatted repos: {len(detailed_repositories)}")
            if len(detailed_repositories) != total_repos:
                logger.warning(f"[COUNT MISMATCH] Repository count mismatch detected!")
            else:
                logger.info(f"[COUNT VERIFIED] All {total_repos} repositories formatted successfully")
            
            # Performance logging
            logger.info(f"[PERFORMANCE] Repository formatting completed in {formatting_time:.2f}s for {total_repos} repositories")
            logger.info(f"[PERFORMANCE] Average time per repository: {(formatting_time/total_repos)*1000:.2f}ms")
            logger.info(f"[PERFORMANCE] Evaluation skipped - saved significant processing time")
            
            # Update progress to calculating metrics phase
            await update_scan_phase(scan_id, ScanPhase.CALCULATING_METRICS)
            logger.info(f"Processing {len(repositories)} repositories for: {username}")
            
            # Extract tech stack (simplified)
            tech_stack = []
            tech_count = {}
            for repo in repositories:
                if repo.get("language"):
                    lang = repo["language"]
                    tech_count[lang] = tech_count.get(lang, 0) + 1
            
            for lang, count in tech_count.items():
                tech_stack.append({
                "name": lang,
                "category": "Programming Language",
                "confidence": min(100, count * 20),
                "repositories": count,
                "experience_level": "Intermediate" if count > 2 else "Beginner"
                })
            
            # Calculate language statistics
            await update_scan_phase(scan_id, ScanPhase.GENERATING_INSIGHTS)
            language_stats = {}
            total_repos = len(repositories)
            
            for repo in repositories:
                if repo.get("language"):
                    lang = repo["language"]
                    if lang not in language_stats:
                        language_stats[lang] = {"repos": 0, "stars": 0}
                    language_stats[lang]["repos"] += 1
                    language_stats[lang]["stars"] += repo.get("stargazers_count", 0)
            
            # Convert to percentage and format
            languages = []
            if language_stats:
                for lang, stats in language_stats.items():
                    percentage = (stats["repos"] / total_repos) * 100 if total_repos > 0 else 0
                    languages.append({
                        "language": lang,
                        "percentage": round(percentage, 1),
                        "repositories": stats["repos"],
                        "stars": stats["stars"]
                    })
            
            # Sort by repository count
            languages.sort(key=lambda x: x["repositories"], reverse=True)
            
            # ============================================================================
            # SCORING DISABLED: Fast Display Mode
            # ============================================================================
            # Skip scoring calculation - evaluation is disabled for fast display
            # Overall score requires detailed code analysis which is not performed
            #
            # TODO: To enable scoring in the future:
            #   1. Calculate overall_score from repository analysis results
            #   2. Use EvaluationEngine.calculate_user_scores(analyzed_repos)
            #   3. Generate roadmap using generate_learning_roadmap(languages, tech_stack, overall_score)
            #   4. Set roadmap_unavailable_reason to None
            #
            # Example future implementation:
            #   analyzed_repos = [r for r in detailed_repositories if r.get('analysis')]
            #   if analyzed_repos:
            #       evaluator = EvaluationEngine()
            #       scores = evaluator.calculate_user_scores(analyzed_repos)
            #       overall_score = scores['overall_score']
            #       formatted_roadmap = generate_learning_roadmap(languages, tech_stack, overall_score)
            # ============================================================================
            
            overall_score = None
            
            # Skip roadmap generation - requires evaluation data
            formatted_roadmap = []
            roadmap_unavailable_reason = "Roadmap generation requires repository evaluation data which is skipped in fast display mode"
            
            logger.info(f"Scan completed for {username} with {len(repositories)} repositories")
            
            # Get empty structures for frontend compatibility
            pull_request_analysis = comprehensive_profile.get("pull_request_analysis", {})
            issue_analysis = comprehensive_profile.get("issue_analysis", {})
            
            # Finalize scan
            await update_scan_phase(scan_id, ScanPhase.FINALIZING)
            
            # Extract comprehensive data from the profile
            contribution_stats = comprehensive_profile.get("contribution_stats", {})
            activity_calendar = comprehensive_profile.get("activity_calendar", {})
            collaboration_metrics = comprehensive_profile.get("collaboration_metrics", {})
            language_statistics = comprehensive_profile.get("language_statistics", {})
            achievement_metrics = comprehensive_profile.get("achievement_metrics", {})
            social_metrics = comprehensive_profile.get("social_metrics", {})
            recent_activity = comprehensive_profile.get("recent_activity", {})
            organizations = comprehensive_profile.get("organizations", [])
            repository_overview = comprehensive_profile.get("repository_overview", {})

            # Check for existing analysis results (Task 4.1)
            orchestrator = await get_analysis_orchestrator()
            existing_analysis = await orchestrator.state_storage.find_latest_complete_analysis(username)
            
            # Merge analysis results if available (Task 4.2)
            if existing_analysis:
                logger.info(f"[ANALYSIS] Found existing analysis for {username}, merging results")
                results = existing_analysis.get('results', {})
                analyzed_repos = results.get('repositories', [])
                
                # Replace repositories with analyzed versions if available
                if analyzed_repos:
                    detailed_repositories = analyzed_repos
                    total_repos = len(analyzed_repos)
                
                # Use actual GitHub username from API (preserves case)
                actual_username = user_info.get("login", username)
                scan_results = {
                    "userId": user_id,
                    "username": actual_username,
                    "targetUsername": actual_username,
                    "overallScore": results.get('overall_scores', {}).get('overall_score'),
                    "analyzed": True,  # Flag indicating analysis completed
                    "analyzedAt": results.get('analyzedAt'),
                    "categoryDistribution": results.get('category_distribution', {}),
                    "analysis_available": True,
                    "analysis_type": "intelligent_scoring",
                    "repositoryCount": total_repos,
                    "lastScanDate": datetime.utcnow().isoformat(),
                    "languages": languages[:10],
                    "techStack": tech_stack,
                    "roadmap": [],
                    "roadmap_unavailable_reason": roadmap_unavailable_reason,
                    "githubProfile": {
                        "username": user_info.get("login", username),
                        "name": user_info.get("name"),
                        "bio": user_info.get("bio"),
                        "location": user_info.get("location"),
                        "company": user_info.get("company"),
                        "blog": user_info.get("blog"),
                        "public_repos": user_info.get("public_repos", 0),
                        "followers": user_info.get("followers", 0),
                        "following": user_info.get("following", 0),
                        "created_at": user_info.get("created_at") if user_info.get("created_at") else None,
                        "avatar_url": user_info.get("avatar_url"),
                        "email": user_info.get("email"),
                        "twitter_username": user_info.get("twitter_username"),
                        "public_gists": user_info.get("public_gists", 0),
                        "hireable": user_info.get("hireable"),
                        "type": user_info.get("type"),
                        "site_admin": user_info.get("site_admin", False)
                    },
                    "skillAssessment": {},
                    "insights": {},
                    "profileCompleteness": {},
                    "nextSteps": [],
                    "repositories": detailed_repositories,
                    "repositoryDetails": detailed_repositories,
                    "isExternalScan": True,
                    "scanType": "other",
                    "scanMetadata": {
                        "scanDate": datetime.utcnow().isoformat(),
                        "scanDuration": "real_time",
                        "dataSource": "github_api",
                        "analysisDepth": "intelligent",
                        "repositoriesAnalyzed": len([r for r in detailed_repositories if r.get('evaluated')]),
                        "totalRepositories": total_repos,
                        "evaluationSkipped": False,
                        "evaluationSkippedReason": None
                    },
                    "comprehensiveData": {
                        "contribution_stats": contribution_stats,
                        "activity_calendar": activity_calendar,
                        "collaboration_metrics": collaboration_metrics,
                        "language_statistics": language_statistics,
                        "achievement_metrics": achievement_metrics,
                        "social_metrics": social_metrics,
                        "recent_activity": recent_activity,
                        "organizations": organizations,
                        "repository_overview": repository_overview,
                        "pull_request_analysis": pull_request_analysis,
                        "issue_analysis": issue_analysis
                    },
                    "contributionStats": contribution_stats,
                    "activityCalendar": activity_calendar,
                    "collaborationMetrics": collaboration_metrics,
                    "languageStatistics": language_statistics,
                    "achievementMetrics": achievement_metrics,
                    "socialMetrics": social_metrics,
                    "recentActivity": recent_activity,
                    "organizations": organizations,
                    "repositoryOverview": repository_overview,
                    "pullRequestAnalysis": pull_request_analysis,
                    "issueAnalysis": issue_analysis
                }
            else:
                # No analysis yet - return basic repos without categorization (Task 4.3)
                logger.info(f"[ANALYSIS] No existing analysis for {username}, returning basic data")
                # Use actual GitHub username from API (preserves case)
                actual_username = user_info.get("login", username)
                scan_results = {
                    "userId": user_id,
                    "username": actual_username,
                    "targetUsername": actual_username,
                    "overallScore": None,
                    "overallScore_unavailable_reason": "Evaluation skipped for fast display - scoring requires detailed code analysis",
                    "analyzed": False,  # Flag indicating no analysis yet
                    "analysis_available": False,
                    "analysis_type": None,
                    "repositoryCount": total_repos,
                    "lastScanDate": datetime.utcnow().isoformat(),
                    "languages": languages[:10],
                    "techStack": tech_stack,
                    "roadmap": [],
                    "roadmap_unavailable_reason": roadmap_unavailable_reason,
                    "githubProfile": {
                        "username": user_info.get("login", username),
                        "name": user_info.get("name"),
                        "bio": user_info.get("bio"),
                        "location": user_info.get("location"),
                        "company": user_info.get("company"),
                        "blog": user_info.get("blog"),
                        "public_repos": user_info.get("public_repos", 0),
                        "followers": user_info.get("followers", 0),
                        "following": user_info.get("following", 0),
                        "created_at": user_info.get("created_at") if user_info.get("created_at") else None,
                        "avatar_url": user_info.get("avatar_url"),
                        "email": user_info.get("email"),
                        "twitter_username": user_info.get("twitter_username"),
                        "public_gists": user_info.get("public_gists", 0),
                        "hireable": user_info.get("hireable"),
                        "type": user_info.get("type"),
                        "site_admin": user_info.get("site_admin", False)
                    },
                    "skillAssessment": {},
                    "insights": {},
                    "profileCompleteness": {},
                    "nextSteps": [],
                    "repositories": detailed_repositories,
                    "repositoryDetails": detailed_repositories,
                    "isExternalScan": True,
                    "scanType": "display_only",
                    "scanMetadata": {
                        "scanDate": datetime.utcnow().isoformat(),
                        "scanDuration": "real_time",
                        "dataSource": "github_api",
                        "analysisDepth": "basic",
                        "repositoriesAnalyzed": 0,
                        "totalRepositories": total_repos,
                        "evaluationSkipped": True,
                        "evaluationSkippedReason": "Fast display mode - evaluation skipped for immediate results"
                    },
                    "comprehensiveData": {
                        "contribution_stats": contribution_stats,
                        "activity_calendar": activity_calendar,
                        "collaboration_metrics": collaboration_metrics,
                        "language_statistics": language_statistics,
                        "achievement_metrics": achievement_metrics,
                        "social_metrics": social_metrics,
                        "recent_activity": recent_activity,
                        "organizations": organizations,
                        "repository_overview": repository_overview,
                        "pull_request_analysis": pull_request_analysis,
                        "issue_analysis": issue_analysis
                    },
                    "contributionStats": contribution_stats,
                    "activityCalendar": activity_calendar,
                    "collaborationMetrics": collaboration_metrics,
                    "languageStatistics": language_statistics,
                    "achievementMetrics": achievement_metrics,
                    "socialMetrics": social_metrics,
                    "recentActivity": recent_activity,
                    "organizations": organizations,
                    "repositoryOverview": repository_overview,
                    "pullRequestAnalysis": pull_request_analysis,
                    "issueAnalysis": issue_analysis
                }
            
            # Store data in database for persistence
            await update_scan_phase(scan_id, ScanPhase.STORING_DATA)
            await store_external_scan_data(username, user_info, detailed_repositories, scan_results, user_id)
            
            # Store scores in scores_comparison database for HR queries
            try:
                from app.services.score_extractor import ScoreExtractor
                from app.services.score_storage_service import get_score_storage_service
                from app.db_connection import get_scores_database
                
                # Get scores database connection
                scores_db = await get_scores_database()
                
                if scores_db and scan_results.get("analyzed", False):
                    # Only store scores if analysis was performed
                    logger.info(f"[SCORE STORAGE] Storing scores for {username} in scores_comparison database")
                    
                    # Extract flagship and significant repositories
                    flagship_repos, significant_repos = ScoreExtractor.extract_scores_from_repositories(
                        detailed_repositories,
                        scan_results.get("overallScore", 0)
                    )
                    
                    # Extract metadata
                    metadata = ScoreExtractor.extract_metadata(user_info, detailed_repositories)
                    
                    # Get score storage service
                    score_service = await get_score_storage_service(scores_db)
                    
                    # Store scores
                    success = await score_service.store_user_scores(
                        username=username,
                        user_id=user_id,
                        overall_score=scan_results.get("overallScore", 0),
                        flagship_repos=flagship_repos,
                        significant_repos=significant_repos,
                        metadata=metadata
                    )
                    
                    if success:
                        logger.info(f"✅ [SCORE STORAGE] Successfully stored scores for {username}")
                        logger.info(f"   - Overall Score: {scan_results.get('overallScore', 0)}")
                        logger.info(f"   - Flagship Repos: {len(flagship_repos)}")
                        logger.info(f"   - Significant Repos: {len(significant_repos)}")
                    else:
                        logger.warning(f"⚠️ [SCORE STORAGE] Failed to store scores for {username}")
                else:
                    if not scores_db:
                        logger.warning(f"[SCORE STORAGE] Scores database not available for {username}")
                    else:
                        logger.info(f"[SCORE STORAGE] Skipping score storage for {username} - no analysis performed yet")
                        
            except Exception as score_error:
                logger.error(f"❌ [SCORE STORAGE] Error storing scores for {username}: {score_error}")
                # Don't fail the scan if score storage fails
            
            # Warm cache with comprehensive data
            try:
                await cache_service.warm_user_cache(username, scan_results)
                # Also cache the comprehensive profile for faster future access
                await cache_service.cache_comprehensive_profile(username, scan_results, 3600)
                logger.info(f"Cache warmed successfully for user: {username}")
            except Exception as cache_error:
                logger.warning(f"Cache warming failed for {username}: {cache_error}")
            
            # Complete scan progress tracking
            await complete_scan_progress(scan_id, scan_results)
            
            # Final performance logging
            total_scan_time = time.time() - scan_start_time
            logger.info(f"[PERFORMANCE] ===== SCAN COMPLETED =====")
            logger.info(f"[PERFORMANCE] Total scan time: {total_scan_time:.2f}s")
            logger.info(f"[PERFORMANCE] Repositories fetched: {total_repos}")
            logger.info(f"[PERFORMANCE] Repositories displayed: {len(detailed_repositories)}")
            logger.info(f"[PERFORMANCE] Evaluation skipped: YES (fast display mode)")
            logger.info(f"[PERFORMANCE] Time saved by skipping evaluation: ~{total_repos * 2}s (estimated)")
            logger.info(f"[PERFORMANCE] ===========================")
            print(f"\n[PERFORMANCE] Scan completed in {total_scan_time:.2f}s - {total_repos} repositories displayed without evaluation\n")
            
            # Add scan_id to response for WebSocket subscription
            scan_results["scan_id"] = scan_id
            
            return scan_results
            
        except Exception as scan_error:
            # Report error to progress tracker with specific error handling
            error_message = str(scan_error)
            
            # Handle specific error types with user-friendly messages
            if "private" in error_message.lower() or "access" in error_message.lower():
                await report_scan_error(scan_id, f"Access denied to private repository or user data for {username}", "access_error", True)
            elif "rate limit" in error_message.lower():
                await report_scan_error(scan_id, f"GitHub API rate limit reached while scanning {username}. Please try again later.", "rate_limit_error", True)
            elif "not found" in error_message.lower():
                await report_scan_error(scan_id, f"GitHub user '{username}' not found or does not exist", "not_found_error", False)
            else:
                await report_scan_error(scan_id, f"Scan failed for {username}: {error_message}", "scan_error", False)
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Comprehensive scan failed for {username}: {error_message}"
            )
        
    except Exception as e:
        logger.error(f"Failed to scan external user {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan external user: {str(e)}"
        )

# ML Evaluation Endpoints

@router.get("/scan-fast/{username}")
async def scan_github_user_fast(username: str, request: Request):
    """Fast optimized scan for GitHub user - minimal API calls for quick results"""
    try:
        # Detect user type based on authentication status
        routing_info = await UserTypeDetector.route_user_operation(request, username, "scan")
        user_type = routing_info["user_type"]
        user_id = routing_info["user_id"]
        
        logger.info(f"Starting fast scan for {user_type} user: {username}")
        logger.info(f"User ID: {user_id}")
        
        # Check cache first
        cache_key = f"fast_profile_{username}"
        try:
            cached_profile = await cache_service.get(cache_key, "fast_profiles")
            if cached_profile:
                logger.info(f"Returning cached fast profile for: {username}")
                return cached_profile
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        # Use fast scanner for quick results
        from app.services.github_fast_scanner import GitHubFastScanner
        
        # Get GitHub token
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub token not available"
            )
        
        # Initialize fast scanner
        scanner = GitHubFastScanner(github_token)
        
        # Check rate limits
        rate_limits = await scanner.check_rate_limits_fast()
        if not rate_limits.get("can_proceed", True):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Get fast profile
        logger.info(f"Getting fast profile for: {username}")
        fast_profile = await scanner.get_fast_user_profile(username)
        
        # Quick evaluation using simplified metrics
        evaluation_engine = EvaluationEngine()
        
        # Calculate fast ACID score
        repositories = fast_profile.get("repositories", {}).get("analyzed_repositories", 0)
        total_stars = fast_profile.get("repositories", {}).get("total_stars", 0)
        total_contributions = fast_profile.get("contribution_stats", {}).get("total_contributions", 0)
        account_age = fast_profile.get("derived_metrics", {}).get("account_age_years", 1)
        
        # Simplified ACID calculation
        activity_score = min(total_contributions / 500, 1) * 25  # Max 25 points
        consistency_score = min(repositories / (account_age * 5), 1) * 25  # Max 25 points
        impact_score = min(total_stars / 50, 1) * 25  # Max 25 points
        diversity_score = min(len(fast_profile.get("language_stats", {}).get("primary_languages", {})) / 5, 1) * 25  # Max 25 points
        
        fast_acid_score = activity_score + consistency_score + impact_score + diversity_score
        
        # Prepare fast response
        fast_response = {
            "userId": user_id,
            "githubProfile": fast_profile.get("basic_info", {}),
            "repositoryCount": repositories,
            "overallScore": round(fast_acid_score, 1),
            "languages": [
                {
                    "language": lang,
                    "repositories": count,
                    "percentage": round((count / repositories) * 100, 1) if repositories > 0 else 0
                }
                for lang, count in fast_profile.get("language_stats", {}).get("primary_languages", {}).items()
            ],
            "repositoryOverview": {
                "total_repositories": fast_profile.get("repositories", {}).get("total_repositories", 0),
                "total_stars": total_stars,
                "total_forks": fast_profile.get("repositories", {}).get("total_forks", 0),
                "most_starred_repo": fast_profile.get("repositories", {}).get("most_starred"),
                "recently_updated": fast_profile.get("repositories", {}).get("recently_updated", [])
            },
            "contributionStats": fast_profile.get("contribution_stats", {}),
            "activitySummary": fast_profile.get("activity_summary", {}),
            "derivedMetrics": fast_profile.get("derived_metrics", {}),
            "scanType": "fast_optimized",
            "scanDate": datetime.utcnow().isoformat(),
            "evaluationMethod": "fast_acid",
            "processingTime": "< 10 seconds",
            "_metadata": fast_profile.get("_metadata", {})
        }
        
        # Cache the result for 1 hour
        try:
            await cache_service.set(cache_key, fast_response, "fast_profiles", ttl=3600)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
        
        logger.info(f"Fast scan completed for user: {username} in minimal time")
        return fast_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fast scan failed for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fast scan failed: {str(e)}"
        )

class MLConfigRequest(BaseModel):
    ml_endpoint_url: str

class MLEvaluationRequest(BaseModel):
    github_url: str
    username: str
    ml_endpoint_url: Optional[str] = None

@router.post("/configure-ml-endpoint")
async def configure_ml_endpoint(
    request: MLConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Configure ML model endpoint (Colab via ngrok)"""
    try:
        # Validate URL format
        ml_url = InputSanitizer.sanitize_string(request.ml_endpoint_url, max_length=500)
        
        # Set ML endpoint
        ml_service.set_ml_endpoint(ml_url)
        
        # Check availability
        is_available = await ml_service.check_ml_availability()
        
        return {
            "message": "ML endpoint configured successfully",
            "ml_endpoint": ml_url,
            "ml_available": is_available,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to configure ML endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure ML endpoint: {str(e)}"
        )

@router.get("/ml-status")
async def get_ml_status():
    """Get ML model status and information"""
    try:
        ml_info = await ml_service.get_ml_model_info()
        
        return {
            "ml_status": ml_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get ML status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ML status: {str(e)}"
        )

@router.post("/evaluate-with-ml")
async def evaluate_repository_with_ml(
    request: MLEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Evaluate repository using hybrid ML + ACID approach"""
    try:
        # Validate GitHub URL
        scanner = GitHubScanner(current_user.github_token)
        is_valid, username, repo_name = await scanner.validate_github_url(request.github_url)
        
        if not is_valid or not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub URL"
            )
        
        # Get repository data for evaluation
        try:
            user_info = await scanner.get_user_info(username)
            repositories = await scanner.fetch_user_repositories(username, max_repos=10)
            
            # Prepare repository data for evaluation
            repo_data = {
                "user_info": user_info,
                "repositories": repositories,
                "primary_language": user_info.get("language"),
                "total_repos": len(repositories),
                "total_stars": sum(repo.get("stargazers_count", 0) for repo in repositories),
                "languages": {}
            }
            
            # Aggregate language data
            for repo in repositories:
                if repo.get("language"):
                    lang = repo["language"]
                    repo_data["languages"][lang] = repo_data["languages"].get(lang, 0) + 1
            
        except Exception as e:
            logger.warning(f"Failed to fetch repository data: {e}")
            # Use minimal data for evaluation
            repo_data = {
                "user_info": {"login": username},
                "repositories": [],
                "total_repos": 0,
                "languages": {}
            }
        
        # Perform hybrid evaluation
        evaluation_result = await ml_service.evaluate_repository_hybrid(
            github_url=request.github_url,
            username=username,
            repo_data=repo_data,
            ml_endpoint_url=request.ml_endpoint_url
        )
        
        # Store evaluation results in database
        try:
            evaluation_doc = {
                "user_id": str(current_user.id),
                "username": username,
                "github_url": request.github_url,
                "evaluation_result": evaluation_result,
                "created_at": datetime.utcnow(),
                "evaluation_type": "ml_hybrid"
            }
            
            await db.ml_evaluations.insert_one(evaluation_doc)
            
        except Exception as e:
            logger.warning(f"Failed to store evaluation results: {e}")
        
        return evaluation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML evaluation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML evaluation failed: {str(e)}"
        )

@router.get("/scan-status/{scan_id}")
async def get_scan_status(scan_id: str):
    """Get real-time scan status (public endpoint for external scans)"""
    try:
        # Get progress from enhanced tracker
        progress = await get_scan_progress_data(scan_id)
        
        if not progress:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Return public status information
        return {
            "scan_id": scan_id,
            "phase": progress.get("phase", "unknown"),
            "progress_percentage": progress.get("progress_percentage", 0),
            "current_step": progress.get("current_step", "Processing..."),
            "current_repository": progress.get("current_repository"),
            "total_repositories": progress.get("total_repositories", 0),
            "processed_repositories": progress.get("processed_repositories", 0),
            "estimated_completion": progress.get("estimated_completion"),
            "errors_count": len(progress.get("errors", [])),
            "warnings_count": len(progress.get("warnings", [])),
            "is_completed": progress.get("phase") in ["completed", "error"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scan status")

@router.get("/ml-evaluations/{user_id}")
async def get_ml_evaluations(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get ML evaluation history for a user"""
    try:
        # Verify access permissions
        if str(current_user.id) != user_id and not (hasattr(current_user, 'user_type') and current_user.user_type == "hr"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get ML evaluations from database
        evaluations = await db.ml_evaluations.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(10).to_list(None)
        
        return {
            "evaluations": evaluations,
            "count": len(evaluations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ML evaluations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ML evaluations: {str(e)}"
        )

@router.get("/external-results/{user_identifier}")
async def get_external_scan_results(
    user_identifier: str
):
    """Get scan results for external users or cached results without authentication"""
    try:
        # Get database connection
        from app.db_connection import get_database as get_db_connection
        db = await get_db_connection()
        
        logger.info(f"Getting external scan results for identifier: {user_identifier}")
        
        # Check if this is an external user format (external_username)
        if user_identifier.startswith("external_"):
            username = user_identifier.replace("external_", "")
            logger.info(f"Performing external scan for username: {username}")
            
            # Perform external scan (reuse the existing logic)
            return await scan_external_github_user(username, db)
        
        # Otherwise, try to get cached results from database (for authenticated users)
        try:
            # Try cache first
            cached_results = await cache_service.get_scan_results(user_identifier)
            if cached_results:
                logger.info(f"Returning cached results for user: {user_identifier}")
                return cached_results
            
            # Try to get from database
            if db is not None:
                # Get user's scan results from database
                repositories = await performance_service.get_optimized_user_repositories(user_identifier)
                evaluations = await performance_service.get_optimized_user_evaluations(user_identifier)
                
                if repositories or evaluations:
                    # Calculate basic statistics from stored data
                    overall_score = 0
                    if evaluations:
                        total_score = sum(eval_data.get("acid_score", {}).get("overall", 0) for eval_data in evaluations)
                        overall_score = total_score / len(evaluations) if evaluations else 0
                    
                    # Get language statistics
                    language_stats = {}
                    for repo in repositories:
                        if repo.get("languages"):
                            for lang, lines in repo["languages"].items():
                                if lang not in language_stats:
                                    language_stats[lang] = {"lines": 0, "repos": 0}
                                language_stats[lang]["lines"] += lines
                                language_stats[lang]["repos"] += 1
                    
                    # Convert to percentage
                    total_lines = sum(stats["lines"] for stats in language_stats.values())
                    languages = []
                    if total_lines > 0:
                        for lang, stats in language_stats.items():
                            languages.append({
                                "language": lang,
                                "percentage": round((stats["lines"] / total_lines) * 100, 1),
                                "linesOfCode": stats["lines"],
                                "repositories": stats["repos"]
                            })
                    
                    languages.sort(key=lambda x: x["percentage"], reverse=True)
                    
                    # Get latest scan date
                    latest_eval = max(evaluations, key=lambda x: x["created_at"]) if evaluations else None
                    last_scan_date = latest_eval["created_at"] if latest_eval else None
                    
                    # Extract tech stack
                    tech_stack = await extract_tech_stack_from_repositories(repositories)
                    
                    # Generate roadmap
                    roadmap = generate_learning_roadmap(languages, tech_stack, overall_score)
                    
                    scan_results = {
                        "userId": user_identifier,
                        "overallScore": round(overall_score, 1),
                        "repositoryCount": len(repositories),
                        "lastScanDate": last_scan_date.isoformat() if last_scan_date else None,
                        "languages": languages[:10],
                        "techStack": tech_stack,
                        "roadmap": roadmap,
                        "repositories": repositories,
                        "repositoryDetails": repositories,
                        "isExternalScan": False,
                        "scanType": "cached_results",
                        "scanMetadata": {
                            "scanDate": last_scan_date.isoformat() if last_scan_date else None,
                            "scanDuration": "cached",
                            "dataSource": "database",
                            "analysisDepth": "stored",
                            "repositoriesAnalyzed": len(repositories),
                            "totalRepositories": len(repositories)
                        }
                    }
                    
                    # Cache the results
                    await cache_service.cache_scan_results(user_identifier, scan_results, 1800)
                    
                    return scan_results
        
        except Exception as e:
            logger.warning(f"Failed to get cached results: {e}")
        
        # If no cached results found, return empty results
        logger.info(f"No results found for user: {user_identifier}")
        return {
            "userId": user_identifier,
            "overallScore": 0,
            "repositoryCount": 0,
            "lastScanDate": None,
            "languages": [],
            "techStack": [],
            "roadmap": [],
            "repositories": [],
            "repositoryDetails": [],
            "isExternalScan": False,
            "scanType": "no_data",
            "scanMetadata": {
                "scanDate": None,
                "scanDuration": "none",
                "dataSource": "none",
                "analysisDepth": "none",
                "repositoriesAnalyzed": 0,
                "totalRepositories": 0
            },
            "message": "No scan data found. Please perform a scan first."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get external scan results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scan results: {str(e)}"
        )

@router.get("/cache/performance")
async def get_cache_performance():
    """Get cache performance metrics and statistics"""
    try:
        performance_metrics = await cache_service.get_cache_performance_metrics()
        
        return {
            "cache_performance": performance_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache performance: {str(e)}"
        )

@router.post("/cache/invalidate/{username}")
async def invalidate_user_cache(username: str):
    """Invalidate all cache entries for a specific user"""
    try:
        await cache_service.invalidate_user_comprehensive_cache(username)
        
        return {
            "message": f"Cache invalidated for user: {username}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to invalidate cache for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache: {str(e)}"
        )

@router.post("/cache/warm/{username}")
async def warm_user_cache_endpoint(username: str):
    """Manually warm cache for a user by performing a fresh scan"""
    try:
        # Invalidate existing cache first
        await cache_service.invalidate_user_comprehensive_cache(username)
        
        # Perform fresh scan to warm cache
        scan_results = await scan_external_github_user(username)
        
        return {
            "message": f"Cache warmed for user: {username}",
            "scan_summary": {
                "repositories": scan_results.get("repositoryCount", 0),
                "overall_score": scan_results.get("overallScore", 0),
                "languages": len(scan_results.get("languages", [])),
                "tech_stack": len(scan_results.get("techStack", []))
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to warm cache for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to warm cache: {str(e)}"
        )

async def get_repository_analysis_if_possible(repo: dict, username: str, github_token: str) -> dict:
    """
    Try to get real repository analysis when possible.
    For external users: Returns unavailable indicator
    For authenticated users with access: Returns real ACID analysis
    """
    try:
        # For external scans, we can't do deep code analysis
        # But we can provide basic metrics based on available metadata
        
        # Check if this is a public repo we can analyze
        if repo.get("private", False):
            return {
                "analysis_available": False,
                "analysis_unavailable_reason": "Repository is private - detailed analysis not available"
            }
        
        # For very large repos, skip analysis to avoid timeouts
        repo_size = repo.get("size", 0)
        if repo_size > 100000:  # > 100MB
            return {
                "analysis_available": False,
                "analysis_unavailable_reason": "Repository too large for automated analysis"
            }
        
        # For external users, we can provide basic quality indicators based on metadata
        # This is NOT mock data - it's real analysis of available public information
        
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        has_description = bool(repo.get("description", "").strip())
        has_topics = bool(repo.get("topics", []))
        has_license = bool(repo.get("license"))
        # Check if repository is recently updated (handle timezone issues)
        is_recent = False
        try:
            if repo.get("pushed_at"):
                pushed_at_str = repo.get("pushed_at", "")
                if pushed_at_str:
                    # Handle different datetime formats
                    if pushed_at_str.endswith('Z'):
                        pushed_at_str = pushed_at_str[:-1] + '+00:00'
                    
                    from datetime import datetime, timezone
                    pushed_at = datetime.fromisoformat(pushed_at_str)
                    
                    # Make both datetimes timezone-aware for comparison
                    if pushed_at.tzinfo is None:
                        pushed_at = pushed_at.replace(tzinfo=timezone.utc)
                    
                    now = datetime.now(timezone.utc)
                    is_recent = (now - pushed_at).days < 365
        except Exception as e:
            logger.debug(f"Could not parse pushed_at date for {repo.get('name')}: {e}")
            is_recent = False
        
        # Calculate basic quality indicators (not mock - based on real metadata)
        community_score = min(100, max(0, (stars * 2 + forks * 5) / 10)) if stars > 0 or forks > 0 else 30
        documentation_score = 50 + (25 if has_description else 0) + (15 if has_topics else 0) + (10 if has_license else 0)
        maintenance_score = 70 if is_recent else 40
        
        # Overall basic score based on public indicators
        basic_score = (community_score + documentation_score + maintenance_score) / 3
        
        # Generate basic ACID scores based on available metadata
        # These are estimates based on public indicators, not full code analysis
        atomicity_score = min(100, 40 + (20 if has_description else 0) + (15 if has_topics else 0) + (10 if repo.get("language") else 0))
        consistency_score = min(100, 45 + (20 if has_license else 0) + (15 if is_recent else 0) + (10 if stars > 5 else 0))
        isolation_score = min(100, 50 + (15 if not repo.get("fork", False) else 0) + (10 if forks > 0 else 0) + (10 if has_topics else 0))
        durability_score = min(100, 35 + (25 if is_recent else 0) + (15 if has_license else 0) + (10 if stars > 10 else 0))
        overall_acid = (atomicity_score + consistency_score + isolation_score + durability_score) / 4
        
        return {
            "analysis_available": True,
            "analysis_type": "metadata_based",
            "analysis_note": "Basic analysis based on public repository metadata - not full code analysis",
            "analysis": {
                "acid_scores": {
                    "atomicity": round(atomicity_score, 1),
                    "consistency": round(consistency_score, 1),
                    "isolation": round(isolation_score, 1),
                    "durability": round(durability_score, 1),
                    "overall": round(overall_acid, 1)
                },
                "quality_metrics": {
                    "readability": round(documentation_score * 0.8, 1),
                    "maintainability": round(maintenance_score, 1),
                    "security": round(50 + (20 if has_license else 0) + (10 if is_recent else 0), 1),
                    "test_coverage": round(40 + (15 if stars > 5 else 0) + (10 if forks > 0 else 0), 1),
                    "documentation": round(documentation_score, 1)
                },
                "overall_score": round(basic_score, 1),
                "basic_quality_score": round(basic_score, 1),
                "community_indicators": {
                    "stars": stars,
                    "forks": forks,
                    "community_score": round(community_score, 1)
                },
                "documentation_indicators": {
                    "has_description": has_description,
                    "has_topics": has_topics,
                    "has_license": has_license,
                    "documentation_score": round(documentation_score, 1)
                },
                "maintenance_indicators": {
                    "recently_updated": is_recent,
                    "maintenance_score": round(maintenance_score, 1)
                }
            },
            "limitations": [
                "ACID scores estimated from public metadata (not full code analysis)",
                "Quality metrics based on repository indicators",
                "No security vulnerability scanning",
                "No detailed code complexity analysis"
            ]
        }
        
    except Exception as e:
        logger.warning(f"Could not analyze repository {repo.get('name', 'unknown')}: {e}")
        return {
            "analysis_available": False,
            "analysis_unavailable_reason": f"Analysis failed: {str(e)}"
        }

async def get_basic_github_profile_info_only(username: str, github_token: str, user_id: str = None) -> dict:
    """Get only basic GitHub profile information without analysis when full scan is not possible"""
    try:
        from github import Github
        g = Github(github_token)
        user = g.get_user(username)
        
        # Get basic repositories (limited to 10 for speed) - NO ANALYSIS
        repos = list(user.get_repos(type='public', sort='updated')[:10])
        
        basic_repositories = []
        for repo in repos:
            basic_repositories.append({
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description or "",
                "language": repo.language,
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "html_url": repo.html_url,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                # NO MOCK ANALYSIS DATA
            })
        
        return {
            "userId": user_id or f"external_{username}",
            "username": username,
            "userInfo": {
                "login": user.login,
                "name": user.name,
                "email": user.email,
                "bio": user.bio,
                "company": user.company,
                "location": user.location,
                "public_repos": user.public_repos,
                "followers": user.followers,
                "following": user.following,
                "avatar_url": user.avatar_url,
                "html_url": user.html_url
            },
            "repositories": basic_repositories,
            "repositoryDetails": basic_repositories,
            "isExternalScan": True,
            "scanType": "basic_info_only",
            "analysis_available": False,
            "analysis_unavailable_reason": "Rate limits exceeded or API restrictions",
            "_metadata": {
                "scan_method": "info_only_fallback",
                "scan_timestamp": datetime.utcnow().isoformat(),
                "note": "Only basic information available - no analysis performed due to API limitations"
            }
        }
    except Exception as e:
        logger.error(f"Failed to get basic profile for {username}: {e}")
        # Don't return mock data - return proper error
        raise HTTPException(
            status_code=500, 
            detail=f"Unable to fetch GitHub profile data for '{username}': {str(e)}"
        )

async def store_external_scan_data(username: str, user_info: dict, repositories: list, scan_results: dict, user_id: str):
    """Store external scan data in database for persistence and caching"""
    try:
        from app.db_connection import get_database
        
        db = await get_database()
        if db is None:
            logger.warning("Database not available, skipping data storage")
            return
        
        # Check if we're dealing with a mock database
        if hasattr(db, '__class__') and 'Mock' in str(db.__class__):
            logger.warning("Mock database detected, skipping data storage")
            return
        
        logger.info(f"Storing external scan data for user: {username}")
        
        # Store GitHub user profile
        user_profile_doc = {
            "user_id": user_id,
            "login": user_info.get("login", username),
            "name": user_info.get("name"),
            "bio": user_info.get("bio"),
            "location": user_info.get("location"),
            "company": user_info.get("company"),
            "blog": user_info.get("blog"),
            "email": user_info.get("email"),
            "twitter_username": user_info.get("twitter_username"),
            "public_repos": user_info.get("public_repos", 0),
            "public_gists": user_info.get("public_gists", 0),
            "followers": user_info.get("followers", 0),
            "following": user_info.get("following", 0),
            "created_at": user_info.get("created_at"),
            "updated_at": user_info.get("updated_at"),
            "avatar_url": user_info.get("avatar_url"),
            "gravatar_id": user_info.get("gravatar_id"),
            "html_url": user_info.get("html_url"),
            "type": user_info.get("type"),
            "site_admin": user_info.get("site_admin", False),
            "hireable": user_info.get("hireable"),
            "scan_date": datetime.utcnow(),
            "is_external_scan": True
        }
        
        # Upsert GitHub user profile
        try:
            await db.github_user_profiles.replace_one(
                {"user_id": user_id},
                user_profile_doc,
                upsert=True
            )
            logger.info(f"Stored GitHub profile for: {username}")
        except AttributeError as e:
            logger.warning(f"Database operation failed (using mock DB?): {e}")
            # Continue without storing if database is not available
        except Exception as e:
            logger.error(f"Failed to store GitHub profile for {username}: {e}")
        
        # Store repositories
        for repo in repositories:
            repo_doc = {
                "user_id": user_id,
                "github_id": repo.get("id"),
                "name": repo.get("name", ""),
                "full_name": repo.get("full_name", ""),
                "description": repo.get("description", ""),
                "language": repo.get("language"),
                "languages": repo.get("languages", {}),
                "stargazers_count": repo.get("stargazers_count", 0),
                "forks_count": repo.get("forks_count", 0),
                "watchers_count": repo.get("watchers_count", 0),
                "size": repo.get("size", 0),
                "topics": repo.get("topics", []),
                "created_at": datetime.fromisoformat(repo["created_at"].replace('Z', '+00:00')) if repo.get("created_at") else datetime.utcnow(),
                "updated_at": datetime.fromisoformat(repo["updated_at"].replace('Z', '+00:00')) if repo.get("updated_at") else datetime.utcnow(),
                "pushed_at": datetime.fromisoformat(repo["pushed_at"].replace('Z', '+00:00')) if repo.get("pushed_at") else None,
                "html_url": repo.get("html_url", ""),
                "clone_url": repo.get("clone_url", ""),
                "private": repo.get("private", False),
                "fork": repo.get("fork", False),
                "archived": repo.get("archived", False),
                "disabled": repo.get("disabled", False),
                "open_issues_count": repo.get("open_issues_count", 0),
                "license": repo.get("license"),
                "default_branch": repo.get("default_branch", "main"),
                "analysis": repo.get("analysis", {}),
                "code_metrics": repo.get("code_metrics", {}),
                "scan_date": datetime.utcnow(),
                "is_external_scan": True
            }
            
            # Upsert repository
            try:
                await db.repositories.replace_one(
                    {"user_id": user_id, "github_id": repo.get("id")},
                    repo_doc,
                    upsert=True
                )
            except AttributeError as e:
                logger.warning(f"Database operation failed (using mock DB?): {e}")
                # Continue without storing if database is not available
            except Exception as e:
                logger.error(f"Failed to store repository {repo.get('name', 'unknown')}: {e}")
        
        logger.info(f"Stored {len(repositories)} repositories for: {username}")
        
        # Store comprehensive scan results
        comprehensive_scan_doc = {
            "user_id": user_id,
            "username": username,
            "overall_score": scan_results.get("overallScore", 0),
            "repository_count": scan_results.get("repositoryCount", 0),
            "languages": scan_results.get("languages", []),
            "tech_stack": scan_results.get("techStack", []),
            "roadmap": scan_results.get("roadmap", []),
            "github_profile": scan_results.get("githubProfile", {}),
            "skill_assessment": scan_results.get("skillAssessment", {}),
            "insights": scan_results.get("insights", {}),
            "profile_completeness": scan_results.get("profileCompleteness", {}),
            "next_steps": scan_results.get("nextSteps", []),
            "comprehensive_data": scan_results.get("comprehensiveData", {}),
            "contribution_stats": scan_results.get("contributionStats", {}),
            "activity_calendar": scan_results.get("activityCalendar", {}),
            "collaboration_metrics": scan_results.get("collaborationMetrics", {}),
            "language_statistics": scan_results.get("languageStatistics", {}),
            "achievement_metrics": scan_results.get("achievementMetrics", {}),
            "social_metrics": scan_results.get("socialMetrics", {}),
            "recent_activity": scan_results.get("recentActivity", {}),
            "organizations": scan_results.get("organizations", []),
            "repository_overview": scan_results.get("repositoryOverview", {}),
            "pull_request_analysis": scan_results.get("pullRequestAnalysis", {}),
            "issue_analysis": scan_results.get("issueAnalysis", {}),
            "scan_metadata": scan_results.get("scanMetadata", {}),
            "scan_date": datetime.utcnow(),
            "is_external_scan": True,
            "scan_type": "external_comprehensive"
        }
        
        # Upsert comprehensive scan results
        try:
            await db.comprehensive_scan_results.replace_one(
                {"user_id": user_id},
                comprehensive_scan_doc,
                upsert=True
            )
            logger.info(f"Stored comprehensive scan results for: {username}")
        except AttributeError as e:
            logger.warning(f"Database operation failed (using mock DB?): {e}")
            # Continue without storing if database is not available
        except Exception as e:
            logger.error(f"Failed to store comprehensive scan results for {username}: {e}")
        
        # Store contribution calendar data if available
        if scan_results.get("activityCalendar"):
            calendar_doc = {
                "user_id": user_id,
                "username": username,
                "calendar_data": scan_results.get("activityCalendar", {}),
                "scan_date": datetime.utcnow(),
                "is_external_scan": True
            }
            
            try:
                await db.contribution_calendars.replace_one(
                    {"user_id": user_id},
                    calendar_doc,
                    upsert=True
                )
                logger.info(f"Stored contribution calendar for: {username}")
            except AttributeError as e:
                logger.warning(f"Database operation failed (using mock DB?): {e}")
                # Continue without storing if database is not available
            except Exception as e:
                logger.error(f"Failed to store contribution calendar for {username}: {e}")
        
        logger.info(f"✅ Successfully stored all external scan data for: {username}")
        
    except Exception as e:
        logger.error(f"Failed to store external scan data for {username}: {e}")
        # Don't raise the error - we don't want to fail the scan if storage fails
        import traceback
        logger.error(f"Storage error traceback: {traceback.format_exc()}")

async def _calculate_contribution_metrics(calendar_data: Dict[str, Any], username: str) -> Dict[str, Any]:
    """Calculate contribution streaks and activity patterns from calendar data"""
    try:
        logger.info(f"Calculating contribution metrics for: {username}")
        
        # Extract contribution days from GraphQL response
        contribution_days = calendar_data.get("contributionCalendar", {}).get("weeks", [])
        
        # Flatten contribution days
        all_days = []
        for week in contribution_days:
            for day in week.get("contributionDays", []):
                all_days.append({
                    "date": day.get("date"),
                    "contributionCount": day.get("contributionCount", 0),
                    "level": day.get("color", 0)  # GitHub uses color levels 0-4
                })
        
        # Sort by date
        all_days.sort(key=lambda x: x["date"])
        
        # Calculate streaks
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        # Calculate from most recent day backwards
        today = datetime.now().date()
        for day in reversed(all_days):
            day_date = datetime.fromisoformat(day["date"]).date()
            
            if day["contributionCount"] > 0:
                if day_date == today or (today - day_date).days <= current_streak + 1:
                    temp_streak += 1
                    if day_date == today or (today - day_date).days == current_streak:
                        current_streak = temp_streak
                else:
                    break
            else:
                if day_date == today:
                    continue  # Skip today if no contributions
                else:
                    break
        
        # Find longest streak
        temp_streak = 0
        for day in all_days:
            if day["contributionCount"] > 0:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
        
        # Calculate activity patterns
        day_patterns = {"Monday": 0, "Tuesday": 0, "Wednesday": 0, "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0}
        month_patterns = {}
        total_contributions = 0
        
        for day in all_days:
            contributions = day["contributionCount"]
            total_contributions += contributions
            
            if contributions > 0:
                day_date = datetime.fromisoformat(day["date"])
                day_name = day_date.strftime("%A")
                month_name = day_date.strftime("%B")
                
                day_patterns[day_name] += contributions
                month_patterns[month_name] = month_patterns.get(month_name, 0) + contributions
        
        # Find most active day and month
        most_active_day = max(day_patterns.items(), key=lambda x: x[1])[0] if any(day_patterns.values()) else "Monday"
        most_active_month = max(month_patterns.items(), key=lambda x: x[1])[0] if month_patterns else "January"
        
        # Calculate average contributions per day
        active_days = len([day for day in all_days if day["contributionCount"] > 0])
        avg_contributions_per_active_day = total_contributions / active_days if active_days > 0 else 0
        
        # Enhanced calendar data
        enhanced_calendar = {
            **calendar_data,
            "contribution_summary": {
                "total_contributions": total_contributions,
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "active_days": active_days,
                "total_days": len(all_days),
                "average_contributions_per_active_day": round(avg_contributions_per_active_day, 2)
            },
            "activity_patterns": {
                "day_of_week": day_patterns,
                "most_active_day": most_active_day,
                "month_distribution": month_patterns,
                "most_active_month": most_active_month
            },
            "contribution_levels": {
                "level_0": len([d for d in all_days if d["contributionCount"] == 0]),
                "level_1": len([d for d in all_days if 1 <= d["contributionCount"] <= 3]),
                "level_2": len([d for d in all_days if 4 <= d["contributionCount"] <= 6]),
                "level_3": len([d for d in all_days if 7 <= d["contributionCount"] <= 9]),
                "level_4": len([d for d in all_days if d["contributionCount"] >= 10])
            },
            "processed_days": all_days
        }
        
        logger.info(f"Calculated contribution metrics for {username}: {total_contributions} total contributions, {current_streak} current streak")
        return enhanced_calendar
        
    except Exception as e:
        logger.error(f"Error calculating contribution metrics for {username}: {e}")
        return calendar_data  # Return original data if calculation fails

async def _get_fallback_contribution_data(username: str, github_token: str, from_date: Optional[str] = None) -> Dict[str, Any]:
    """Get fallback contribution data using REST API when GraphQL fails"""
    try:
        logger.info(f"Getting fallback contribution data for: {username}")
        
        # Initialize basic GitHub scanner for fallback
        from app.services.github_scanner import GitHubScanner
        scanner = GitHubScanner(github_token)
        
        # Get user info and recent activity
        user_info = await scanner.get_user_info(username)
        
        # Get user's repositories for activity estimation
        repositories = await scanner.fetch_user_repositories(username, max_repos=20)
        
        # Calculate basic activity metrics from repositories
        total_contributions = 0
        recent_activity = []
        
        for repo in repositories:
            # Estimate contributions from repository data
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            
            # Simple heuristic for contribution estimation
            estimated_contributions = min(100, stars + (forks * 2))
            total_contributions += estimated_contributions
            
            if repo.get("updated_at"):
                recent_activity.append({
                    "date": repo["updated_at"],
                    "repository": repo["name"],
                    "estimated_contributions": estimated_contributions
                })
        
        # Create basic calendar structure
        fallback_calendar = {
            "contributionCalendar": {
                "totalContributions": total_contributions,
                "weeks": [],  # Would need more complex logic to generate
                "colors": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
            },
            "contribution_summary": {
                "total_contributions": total_contributions,
                "current_streak": 0,  # Cannot calculate without daily data
                "longest_streak": 0,  # Cannot calculate without daily data
                "active_days": len(recent_activity),
                "estimated_data": True
            },
            "activity_patterns": {
                "recent_repositories": recent_activity[:10],
                "total_repositories": len(repositories),
                "public_repositories": user_info.get("public_repos", 0)
            },
            "fallback_info": {
                "reason": "GraphQL API unavailable",
                "data_source": "repository_analysis",
                "accuracy": "estimated"
            }
        }
        
        logger.info(f"Generated fallback contribution data for {username}")
        return fallback_calendar
        
    except Exception as e:
        logger.error(f"Error getting fallback contribution data for {username}: {e}")
        return {
            "contributionCalendar": {"totalContributions": 0},
            "error": str(e),
            "fallback_info": {"reason": "All methods failed"}
        }



# ============================================================================
# ANALYSIS API ENDPOINTS - Intelligent Repository Scoring
# ============================================================================

@router.post("/scan-external-user/{username}/analyze", response_model=InitiateAnalysisResponse)
async def initiate_repository_analysis(
    username: str,
    request: InitiateAnalysisRequest = InitiateAnalysisRequest()
) -> InitiateAnalysisResponse:
    """
    Initiate intelligent repository analysis for an external user.
    
    This endpoint starts an asynchronous analysis process that:
    1. Calculates importance scores for all repositories
    2. Categorizes repositories into flagship/significant/supporting
    3. Performs deep evaluation on top 10-15 repositories
    4. Calculates overall developer score
    
    **Analysis Phases**:
    - Scoring: Calculate importance scores (1-2s)
    - Categorizing: Classify repositories (<1s)
    - Evaluating: Deep analysis of selected repos (30-60s)
    - Calculating: Compute overall score (<1s)
    
    **Requirements**: 2.1-2.7, 6.1-6.7
    
    Args:
        username: GitHub username to analyze
        max_evaluate: Maximum number of repositories to evaluate (default: 15)
        
    Returns:
        {
            "analysis_id": "unique-id",
            "status": "started",
            "message": "Analysis initiated for X repositories",
            "estimated_time": "45-60 seconds"
        }
        
    Example:
        POST /scan-external-user/johndoe/analyze
        Response: {"analysis_id": "abc123", "status": "started", ...}
    """
    try:
        max_evaluate = request.max_evaluate
        logger.info(f"[ANALYSIS] Initiating analysis for user: {username}, max_evaluate={max_evaluate}")
        
        # Log user engagement analytics
        analytics_logger = logging.getLogger("analytics")
        analytics_logger.info(
            "ANALYTICS_EVENT: analyze_button_clicked",
            extra={
                'event_type': 'analyze_button_clicked',
                'username': username,
                'max_evaluate': max_evaluate,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Invalidate existing cache (Requirements: 12.3, 13.3)
        await cache_service.invalidate_analysis_results(username)
        
        # Get GitHub token from settings
        from app.core.config import settings
        github_token = settings.github_token
        
        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No GitHub token available"
            )
        
        # First, fetch all repositories if not cached
        scanner = GitHubScanner(github_token)
        
        # Get repositories (basic data)
        result = await scanner.fetch_user_repositories(
            username,
            include_forks=False,
            max_display_repos=999,  # Get all repos (high limit)
            evaluate_limit=999,  # High limit for analysis
            return_metadata=True
        )
        
        repositories = result["repositories"]
        
        if not repositories:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No repositories found for user: {username}"
            )
        
        # Initialize analysis orchestrator with persistent storage
        orchestrator = await get_analysis_orchestrator()
        
        # Start analysis
        analysis_id = await orchestrator.initiate_analysis(
            username=username,
            repositories=repositories,
            max_evaluate=max_evaluate,
            github_token=github_token
        )
        
        # Estimate time based on repository count
        repos_to_evaluate = min(len(repositories), max_evaluate)
        estimated_time = f"{30 + (repos_to_evaluate * 2)}-{45 + (repos_to_evaluate * 3)} seconds"
        
        logger.info(
            f"[ANALYSIS] Analysis initiated for {username}: "
            f"analysis_id={analysis_id}, repos={len(repositories)}, "
            f"to_evaluate={repos_to_evaluate}"
        )
        
        return {
            "analysis_id": analysis_id,
            "status": "started",
            "message": f"Analysis initiated for {len(repositories)} repositories",
            "estimated_time": estimated_time,
            "repositories_count": len(repositories),
            "max_evaluate": max_evaluate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ANALYSIS] Failed to initiate analysis for {username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate analysis: {str(e)}"
        )


@router.get("/scan-external-user/{username}/analysis-status/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    username: str,
    analysis_id: str
) -> AnalysisStatusResponse:
    """
    Get the current status of a repository analysis.
    
    Returns real-time progress updates including:
    - Current phase (scoring, categorizing, evaluating, calculating)
    - Progress percentage
    - Number of repositories evaluated
    - Current status message
    
    **Requirements**: 6.1-6.7
    
    Args:
        username: GitHub username
        analysis_id: Unique analysis identifier from initiate_analysis
        
    Returns:
        {
            "analysis_id": "abc123",
            "status": "evaluating",
            "current_phase": "evaluating",
            "progress": {
                "total_repos": 288,
                "scored": 288,
                "categorized": 288,
                "evaluated": 5,
                "to_evaluate": 12,
                "percentage": 42
            },
            "message": "Evaluating 5 of 12 repositories..."
        }
        
    Status Values:
        - started: Analysis just initiated
        - scoring: Calculating importance scores
        - categorizing: Classifying repositories
        - evaluating: Performing deep evaluation
        - calculating: Computing overall score
        - complete: Analysis finished
        - failed: Analysis encountered an error
    """
    try:
        logger.debug(f"[ANALYSIS] Getting status for analysis: {analysis_id}")
        
        # Initialize orchestrator with persistent storage
        orchestrator = await get_analysis_orchestrator()
        
        # Get status
        status_data = await orchestrator.get_analysis_status(analysis_id)
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis not found: {analysis_id}"
            )
        
        # Verify username matches
        if status_data.get('username') != username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Analysis does not belong to this user"
            )
        
        # Return status information
        return {
            "analysis_id": analysis_id,
            "status": status_data.get('status'),
            "current_phase": status_data.get('current_phase'),
            "progress": status_data.get('progress', {}),
            "message": status_data.get('current_message'),
            "error": status_data.get('error'),
            "created_at": status_data.get('created_at'),
            "updated_at": status_data.get('updated_at')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ANALYSIS] Failed to get status for {analysis_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis status: {str(e)}"
        )


@router.get("/scan-external-user/{username}/analysis-results/{analysis_id}", response_model=AnalysisResultsResponse)
async def get_analysis_results(
    username: str,
    analysis_id: str,
    request: Request
) -> AnalysisResultsResponse:
    """
    Get complete analysis results for a finished analysis.
    
    Returns comprehensive results including:
    - All repositories with importance scores and categories
    - Evaluation data for selected repositories
    - Overall developer score
    - Category distribution (flagship/significant/supporting)
    
    **Requirements**: 2.5, 7.1-7.7, 8.1-8.8, 9.1-9.6
    
    Args:
        username: GitHub username
        analysis_id: Unique analysis identifier
        
    Returns:
        {
            "username": "johndoe",
            "repositoryCount": 288,
            "analyzed": true,
            "analyzedAt": "2024-11-13T12:00:00Z",
            "overallScore": 87.5,
            "evaluatedCount": 12,
            "flagshipCount": 4,
            "significantCount": 8,
            "supportingCount": 276,
            "repositories": [
                {
                    "name": "production-app",
                    "analyzed": true,
                    "importance_score": 95,
                    "category": "flagship",
                    "evaluated": true,
                    "evaluation": {
                        "overall_score": 88.5,
                        "acid_scores": {...},
                        "quality_metrics": {...},
                        "strengths": [...],
                        "improvements": [...]
                    }
                },
                ...
            ]
        }
        
    Note:
        - Returns 404 if analysis not found or not complete
        - Only returns results for completed analyses
        - Supporting repositories have evaluated=false and evaluation=null
    """
    try:
        # Detect user type based on authentication status
        routing_info = await UserTypeDetector.route_user_operation(request, username, "analysis")
        user_type = routing_info["user_type"]
        user_id = routing_info["user_id"]
        
        logger.info(f"[ANALYSIS] Getting results for {user_type} user analysis: {analysis_id}")
        logger.info(f"[ANALYSIS] User ID: {user_id}")
        
        # Check cache first (Requirements: 12.2)
        cached_results = await cache_service.get_analysis_results(username)
        if cached_results and cached_results.get('analysis_id') == analysis_id:
            logger.info(f"[ANALYSIS] Returning cached results for {username}")
            return cached_results
        
        # Initialize orchestrator with persistent storage
        orchestrator = await get_analysis_orchestrator()
        
        # Get results
        results = await orchestrator.get_analysis_results(analysis_id)
        
        if not results:
            # Check if analysis exists but not complete
            status_data = await orchestrator.get_analysis_status(analysis_id)
            if status_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Analysis not complete yet. Current status: {status_data.get('status')}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Analysis not found: {analysis_id}"
                )
        
        # Verify username matches
        if results.get('username') != username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Analysis does not belong to this user"
            )
        
        # Format response with complete repository data
        repositories = results.get('repositories', [])
        
        # Get results object if available (contains category_distribution, etc.)
        results_data = results.get('results', {})
        
        response = {
            "analysis_id": analysis_id,
            "username": username,
            "targetUsername": username,  # Add for frontend compatibility
            "repositoryCount": len(repositories),
            "analyzed": True,  # Flag indicating analysis completed
            "analyzedAt": results.get('analyzed_at') or results.get('completed_at'),
            "overallScore": results.get('overall_score'),
            "evaluatedCount": results.get('evaluated_count', 0),
            "flagshipCount": results.get('flagship_count', 0),
            "significantCount": results.get('significant_count', 0),
            "supportingCount": results.get('supporting_count', 0),
            "categoryDistribution": results_data.get('category_distribution', {
                'flagship': results.get('flagship_count', 0),
                'significant': results.get('significant_count', 0),
                'supporting': results.get('supporting_count', 0)
            }),
            "repositories": repositories,  # With all categorization fields
            "repositoryDetails": repositories,  # Alias for frontend compatibility
            "scanType": "other",  # Match frontend expectations
            "isExternalScan": True
        }
        
        # Cache results for 24 hours (Requirements: 12.1)
        await cache_service.cache_analysis_results(username, response, ttl=86400)
        
        # Cache importance scores separately
        importance_scores = {
            repo['name']: repo.get('importance_score')
            for repo in repositories
            if repo.get('importance_score') is not None
        }
        await cache_service.cache_importance_scores(username, importance_scores, ttl=86400)
        
        # Store scores in scores_comparison collection
        try:
            from app.services.score_extractor import ScoreExtractor
            from app.services.score_storage_service import get_score_storage_service
            from app.db_connection import get_scores_database
            
            logger.info(f"[SCORE STORAGE] Storing analysis scores for {username}")
            
            # Get scores database connection
            scores_db = await get_scores_database()
            
            if scores_db and results.get('overall_score'):
                # Get user info for metadata
                from app.services.github_scanner import GitHubScanner
                from app.core.config import settings
                
                scanner = GitHubScanner(settings.github_token)
                user_info = await scanner.get_user_info(username)
                
                # Extract flagship and significant repositories
                flagship_repos, significant_repos = ScoreExtractor.extract_scores_from_repositories(
                    repositories,
                    results.get('overall_score', 0)
                )
                
                # Extract metadata
                metadata = ScoreExtractor.extract_metadata(user_info, repositories)
                
                # Get score storage service
                score_service = await get_score_storage_service(scores_db)
                
                # Store scores
                success = await score_service.store_user_scores(
                    username=username,
                    user_id=user_id,
                    overall_score=results.get('overall_score', 0),
                    flagship_repos=flagship_repos,
                    significant_repos=significant_repos,
                    metadata=metadata
                )
                
                if success:
                    logger.info(f"✅ [SCORE STORAGE] Successfully stored scores for {username}")
                    logger.info(f"   - Overall Score: {results.get('overall_score', 0)}")
                    logger.info(f"   - Flagship Repos: {len(flagship_repos)}")
                    logger.info(f"   - Significant Repos: {len(significant_repos)}")
                else:
                    logger.warning(f"⚠️ [SCORE STORAGE] Failed to store scores for {username}")
            else:
                if not scores_db:
                    logger.warning(f"[SCORE STORAGE] Scores database not available for {username}")
                else:
                    logger.info(f"[SCORE STORAGE] No overall score available for {username}")
                    
        except Exception as score_error:
            logger.error(f"❌ [SCORE STORAGE] Error storing scores for {username}: {score_error}")
            # Don't fail the request if score storage fails
        
        logger.info(
            f"[ANALYSIS] Returning and caching results for {username}: "
            f"{len(repositories)} repos, {results.get('evaluated_count')} evaluated, "
            f"score={results.get('overall_score')}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ANALYSIS] Failed to get results for {analysis_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis results: {str(e)}"
        )


@router.get("/scan-external-user/{username}")
async def scan_external_github_user_with_analysis_flag(username: str, request: Request):
    """
    Enhanced version of scan_external_github_user that includes analyzed flag.
    
    This endpoint now returns an 'analyzed' flag to indicate whether
    repository analysis has been performed. Initially returns analyzed=false,
    prompting the user to click "Analyze Repositories" button.
    
    **Requirements**: 1.1-1.7, 8.1-8.8
    
    Returns:
        Same as original scan_external_github_user but with:
        - analyzed: false (initially)
        - importance_score: null (for all repos)
        - category: null (for all repos)
        - evaluated: false (for all repos)
        - evaluation: null (for all repos)
    """
    # Call the existing scan function
    result = await scan_external_github_user(username, request)
    
    # Add analysis flags to response
    if isinstance(result, dict):
        result['analyzed'] = False
        result['overallScore'] = None
        
        # Add analysis flags to each repository
        if 'repositories' in result:
            for repo in result['repositories']:
                repo['analyzed'] = False
                repo['importance_score'] = None
                repo['category'] = None
                repo['evaluated'] = False
                repo['evaluation'] = None
    
    return result
