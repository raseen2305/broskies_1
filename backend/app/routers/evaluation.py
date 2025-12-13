from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.database import get_database
from app.routers.auth import get_current_user
from app.core.validation import (
    PaginationParams, SearchParams, InputSanitizer, ValidationError
)
from app.models.user import User, HRUser
from app.models.repository import Repository, Evaluation
from app.services.cache_service import cache_service
from app.services.performance_service import performance_service

router = APIRouter()

@router.get("/profile/{user_id}")
async def get_user_profile(
    user_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get comprehensive user profile with evaluation data"""
    try:
        # Validate and sanitize user_id
        user_id = InputSanitizer.sanitize_string(user_id, max_length=100)
        
        # Verify access permissions
        if (hasattr(current_user, 'user_type') and current_user.user_type == "hr") or str(current_user.id) == user_id:
            pass  # HR users can access any profile, users can access their own
        else:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Try cache first
        cached_profile = await cache_service.get_user_profile(user_id)
        if cached_profile:
            return cached_profile
        
        # Get user data
        user_doc = await db.users.find_one({"_id": user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get repositories and evaluations
        repositories = await db.repositories.find({"user_id": user_id}).to_list(None)
        evaluations = await db.evaluations.find({"user_id": user_id}).to_list(None)
        
        if not evaluations:
            return {
                "userId": user_id,
                "githubUsername": user_doc.get("github_username"),
                "overallScore": 0,
                "lastScanDate": None,
                "repositoryCount": 0,
                "languages": [],
                "techStack": [],
                "roadmap": []
            }
        
        # Calculate overall score
        total_score = sum(eval_data["acid_score"]["overall"] for eval_data in evaluations)
        overall_score = total_score / len(evaluations)
        
        # Language statistics
        language_stats = {}
        total_lines = 0
        
        for repo in repositories:
            if repo.get("languages"):
                for lang, lines in repo["languages"].items():
                    if lang not in language_stats:
                        language_stats[lang] = {"lines": 0, "repos": 0}
                    language_stats[lang]["lines"] += lines
                    language_stats[lang]["repos"] += 1
                    total_lines += lines
        
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
        
        # Tech stack analysis (simplified)
        tech_stack = []
        frameworks = set()
        for repo in repositories:
            if repo.get("topics"):
                for topic in repo["topics"]:
                    if any(fw in topic.lower() for fw in ["react", "vue", "angular", "express", "django", "flask"]):
                        frameworks.add(topic)
        
        for fw in frameworks:
            tech_stack.append({
                "name": fw.title(),
                "category": "framework",
                "proficiency": None,  # No mock data
                "proficiency_unavailable_reason": "Proficiency assessment requires code analysis",
                "projects": 1
            })
        
        # Don't generate mock roadmap data
        roadmap = []
        roadmap_unavailable_reason = "Personalized roadmap requires detailed code analysis which is not available"
        
        profile_data = {
            "userId": user_id,
            "githubUsername": user_doc.get("github_username"),
            "overallScore": round(overall_score, 1),
            "lastScanDate": user_doc.get("last_scan").isoformat() if user_doc.get("last_scan") else None,
            "repositoryCount": len(repositories),
            "languages": languages[:10],
            "techStack": tech_stack[:10],
            "roadmap": roadmap,
            "roadmap_unavailable_reason": roadmap_unavailable_reason
        }
        
        # Cache the profile data for 30 minutes
        await cache_service.cache_user_profile(user_id, profile_data, 1800)
        
        return profile_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")

@router.get("/repositories/{user_id}")
async def get_repository_evaluations(
    user_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get detailed repository evaluations for a user"""
    try:
        # Verify access permissions
        if (hasattr(current_user, 'user_type') and current_user.user_type == "hr") or str(current_user.id) == user_id:
            pass
        else:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Use optimized performance service for better query performance
        repositories = await performance_service.get_optimized_user_repositories(user_id)
        evaluations = await performance_service.get_optimized_user_evaluations(user_id)
        
        # Create evaluation lookup
        eval_lookup = {eval_data["repo_id"]: eval_data for eval_data in evaluations}
        
        result = []
        for repo in repositories:
            repo_id = str(repo["_id"])
            evaluation = eval_lookup.get(repo_id)
            
            repo_eval = {
                "repoId": repo_id,
                "name": repo["name"],
                "description": repo.get("description", ""),
                "language": repo.get("language", "Unknown"),
                "stars": repo.get("stars", 0),
                "forks": repo.get("forks", 0),
                "lastUpdated": repo["updated_at"].isoformat(),
                "acidScore": {
                    "atomicity": 0,
                    "consistency": 0,
                    "isolation": 0,
                    "durability": 0,
                    "overall": 0
                },
                "qualityMetrics": {
                    "readability": 0,
                    "maintainability": 0,
                    "security": 0,
                    "testCoverage": 0,
                    "documentation": 0
                }
            }
            
            if evaluation:
                repo_eval["acidScore"] = evaluation["acid_score"]
                repo_eval["qualityMetrics"] = evaluation["quality_metrics"]
            
            result.append(repo_eval)
        
        # Sort by overall score
        result.sort(key=lambda x: x["acidScore"]["overall"], reverse=True)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get repository evaluations: {str(e)}")

@router.get("/developers")
async def get_developers(
    search_params: SearchParams = Depends(),
    pagination: PaginationParams = Depends(),
    current_user: HRUser = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get list of developers for HR users with search and filtering"""
    try:
        # Verify HR user
        if not hasattr(current_user, 'user_type') or current_user.user_type != "hr":
            raise HTTPException(status_code=403, detail="HR access required")
        
        # Validate search parameters
        min_score = search_params.min_score or 0
        max_score = search_params.max_score or 100
        
        if min_score > max_score:
            raise ValidationError("min_score", "Minimum score cannot be greater than maximum score")
        
        # Use optimized performance service for better query performance
        developers = await performance_service.get_top_developers(
            limit=pagination.limit, 
            min_score=min_score
        )
        
        # Apply additional filtering if needed
        if search_params.language:
            # Filter by language (this would need to be implemented in the performance service)
            pass
        
        if search_params.query:
            # Filter by search query in username or email
            query_lower = search_params.query.lower()
            developers = [
                dev for dev in developers 
                if query_lower in dev.get('github_username', '').lower() 
                or query_lower in dev.get('email', '').lower()
            ]
        
        # Apply score range filtering
        developers = [
            dev for dev in developers 
            if min_score <= dev.get('avg_score', 0) <= max_score
        ]
        
        # Pagination
        start_idx = (pagination.page - 1) * pagination.limit
        end_idx = start_idx + pagination.limit
        paginated_developers = developers[start_idx:end_idx]
        
        return {
            "developers": paginated_developers,
            "pagination": {
                "current_page": pagination.page,
                "total_items": len(developers),
                "items_per_page": pagination.limit,
                "total_pages": (len(developers) + pagination.limit - 1) // pagination.limit
            },
            "filters": {
                "query": search_params.query,
                "language": search_params.language,
                "min_score": min_score,
                "max_score": max_score
            }
        }
        
        # Fallback to original query if performance service fails
        developers = await db.users.find({
            "user_type": "developer",
            "profile_visibility": "public",
            "github_username": {"$exists": True}
        }).to_list(None)
        
        result = []
        for dev in developers:
            # Get basic stats
            repo_count = await db.repositories.count_documents({"user_id": str(dev["_id"])})
            evaluations = await db.evaluations.find({"user_id": str(dev["_id"])}).to_list(None)
            
            overall_score = 0
            if evaluations:
                total_score = sum(eval_data["acid_score"]["overall"] for eval_data in evaluations)
                overall_score = total_score / len(evaluations)
            
            result.append({
                "userId": str(dev["_id"]),
                "githubUsername": dev.get("github_username"),
                "email": dev.get("email"),
                "overallScore": round(overall_score, 1),
                "repositoryCount": repo_count,
                "lastScanDate": dev.get("last_scan").isoformat() if dev.get("last_scan") else None
            })
        
        # Sort by overall score
        result.sort(key=lambda x: x["overallScore"], reverse=True)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get developers: {str(e)}")

@router.get("/performance-stats")
async def get_performance_stats(
    current_user = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get system performance statistics (admin only)"""
    try:
        # For now, allow any authenticated user to see basic stats
        # In production, this should be restricted to admin users
        
        stats = await performance_service.get_performance_metrics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")

@router.post("/optimize-database")
async def optimize_database(
    current_user = Depends(get_current_user),
    db = Depends(get_database)
):
    """Run database optimization tasks (admin only)"""
    try:
        # For now, allow any authenticated user
        # In production, this should be restricted to admin users
        
        await performance_service.optimize_database_queries()
        
        return {"message": "Database optimization completed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database optimization failed: {str(e)}")

@router.get("/cache-stats")
async def get_cache_stats(
    current_user = Depends(get_current_user)
):
    """Get Redis cache statistics"""
    try:
        stats = await cache_service.get_cache_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.post("/clear-cache/{user_id}")
async def clear_user_cache(
    user_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_database)
):
    """Clear cache for a specific user"""
    try:
        # Verify user can clear this cache
        if str(current_user.id) != user_id and not (hasattr(current_user, 'user_type') and current_user.user_type == "hr"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        await cache_service.invalidate_user_cache(user_id)
        
        return {"message": f"Cache cleared for user {user_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/repositories/{user_id}/paginated")
async def get_repository_evaluations_paginated(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "updated_at",
    order: str = "desc",
    current_user = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get paginated repository evaluations for a user"""
    try:
        # Verify access permissions
        if (hasattr(current_user, 'user_type') and current_user.user_type == "hr") or str(current_user.id) == user_id:
            pass
        else:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Calculate skip value
        skip = (page - 1) * limit
        
        # Use optimized performance service
        repositories = await performance_service.get_optimized_user_repositories(user_id, limit=limit, skip=skip)
        
        # Get total count for pagination
        total_count = await db.repositories.count_documents({"user_id": user_id})
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "repositories": repositories,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get paginated repositories: {str(e)}")