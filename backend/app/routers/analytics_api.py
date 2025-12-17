"""
Analytics Router
API endpoints for analytics and insights functionality
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.core.security import get_current_user_token
from app.database import get_database
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class OverallBreakdown(BaseModel):
    """Overall score breakdown"""
    score: float
    grade: str
    description: str
    calculation: Optional[Dict[str, Any]]


class ACIDComponent(BaseModel):
    """ACID component breakdown"""
    score: float
    grade: str
    description: str
    flagship: float
    significant: float


class ACIDBreakdown(BaseModel):
    """ACID scores breakdown"""
    overall: float
    grade: str
    components: Dict[str, ACIDComponent]


class RepositoryInfo(BaseModel):
    """Repository information"""
    id: str
    name: str
    category: str
    importance_score: float
    language: Optional[str]
    stars: int
    analyzed: bool
    overall_score: Optional[float]
    acid_score: Optional[float]


class RepositoryBreakdown(BaseModel):
    """Repository breakdown by category"""
    total: int
    flagship: Dict[str, Any]
    significant: Dict[str, Any]
    supporting: Dict[str, Any]


class ComplexityBreakdown(BaseModel):
    """Complexity metrics breakdown"""
    average_cyclomatic: float
    average_cognitive: float
    average_maintainability: float
    cyclomatic_grade: str
    maintainability_grade: str
    total_lines: int
    total_functions: int
    total_classes: int
    repositories_analyzed: int


class AnalyticsOverviewResponse(BaseModel):
    """Response model for analytics overview"""
    user_id: str
    github_username: str
    overall: OverallBreakdown
    acid: ACIDBreakdown
    repositories: RepositoryBreakdown
    complexity: ComplexityBreakdown


class Insight(BaseModel):
    """Insight model"""
    type: str  # strength or improvement
    category: str
    title: str
    description: str
    priority: str  # high, medium, low


class Recommendation(BaseModel):
    """Recommendation model"""
    repository_id: str
    repository_name: str
    action: str
    description: str
    impact: str  # high, medium, low
    difficulty: str  # easy, medium, hard
    estimated_score_increase: float


class RepositoryAnalyticsResponse(BaseModel):
    """Response model for repository analytics"""
    repository_id: str
    repository_name: str
    category: str
    importance_score: float
    overall_score: float
    acid_scores: Dict[str, float]
    complexity_metrics: Dict[str, Any]
    insights: List[Insight]
    recommendations: List[Recommendation]


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
                user_doc = await db.users.find_one({"_id": user_id})
                if user_doc:
                    return User(**user_doc)
            except Exception as e:
                logger.warning(f"Database query failed: {e}")
        
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


@router.get("/overview/{user_id}", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Get comprehensive analytics overview for a user
    
    Returns:
    - Overall score breakdown
    - ACID component breakdown
    - Repository breakdown by category
    - Complexity metrics breakdown
    
    Requirements: 15, 16, 17
    """
    try:
        # Verify authorization
        if str(current_user.id) != user_id:
            # Allow HR users to view any profile
            if not hasattr(current_user, 'user_type') or current_user.user_type != "hr":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        logger.info(f"Generating analytics overview for user: {user_id}")
        
        # Initialize score breakdown service
        from app.services.analytics.score_breakdown import ScoreBreakdownService
        
        breakdown_service = ScoreBreakdownService(db)
        
        # Generate complete breakdown
        breakdown = await breakdown_service.generate_complete_breakdown(user_id)
        
        # Format response
        return AnalyticsOverviewResponse(
            user_id=user_id,
            github_username=breakdown['github_username'],
            overall=OverallBreakdown(**breakdown['overall']),
            acid=ACIDBreakdown(
                overall=breakdown['acid']['overall'],
                grade=breakdown['acid']['grade'],
                components={
                    k: ACIDComponent(**v)
                    for k, v in breakdown['acid']['components'].items()
                }
            ),
            repositories=RepositoryBreakdown(**breakdown['repositories']),
            complexity=ComplexityBreakdown(**breakdown['complexity'])
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get analytics overview: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics overview: {str(e)}"
        )


@router.get("/repository/{repo_id}", response_model=RepositoryAnalyticsResponse)
async def get_repository_analytics(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Get detailed analytics for a specific repository
    
    Returns:
    - Repository scores and metrics
    - Insights (strengths and improvements)
    - Actionable recommendations
    
    Requirements: 17, 18, 19, 20
    """
    try:
        logger.info(f"Generating repository analytics for repo: {repo_id}")
        
        # Get repository
        from bson import ObjectId
        
        try:
            repo_obj_id = ObjectId(repo_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid repository ID format"
            )
        
        repo = await db.repositories.find_one({"_id": repo_obj_id})
        
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # Verify authorization
        if str(current_user.id) != repo.get("user_id"):
            # Allow HR users to view any repository
            if not hasattr(current_user, 'user_type') or current_user.user_type != "hr":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        # Check if repository has been analyzed
        if not repo.get("analyzed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository has not been analyzed yet"
            )
        
        # Initialize analytics services
        from app.services.analytics.insights_generator import InsightsGenerator
        from app.services.analytics.recommendations import RecommendationsEngine
        
        insights_gen = InsightsGenerator(db)
        recommendations_engine = RecommendationsEngine(db)
        
        # Generate insights
        insights_data = await insights_gen.generate_repository_insights(repo_id)
        
        # Generate recommendations
        recommendations_data = await recommendations_engine.generate_repository_recommendations(
            repo_id
        )
        
        # Format insights
        insights = []
        for insight in insights_data.get('strengths', []):
            insights.append(Insight(
                type='strength',
                category=insight.get('category', 'general'),
                title=insight.get('title', ''),
                description=insight.get('description', ''),
                priority=insight.get('priority', 'medium')
            ))
        
        for insight in insights_data.get('improvements', []):
            insights.append(Insight(
                type='improvement',
                category=insight.get('category', 'general'),
                title=insight.get('title', ''),
                description=insight.get('description', ''),
                priority=insight.get('priority', 'medium')
            ))
        
        # Format recommendations
        recommendations = [
            Recommendation(
                repository_id=repo_id,
                repository_name=repo.get('name', ''),
                action=rec.get('action', ''),
                description=rec.get('description', ''),
                impact=rec.get('impact', 'medium'),
                difficulty=rec.get('difficulty', 'medium'),
                estimated_score_increase=rec.get('estimated_score_increase', 0.0)
            )
            for rec in recommendations_data
        ]
        
        # Get ACID scores
        acid_scores = repo.get('acid_scores', {})
        if isinstance(acid_scores, dict):
            acid_scores_dict = acid_scores
        else:
            acid_scores_dict = {
                'atomicity': 0.0,
                'consistency': 0.0,
                'isolation': 0.0,
                'durability': 0.0,
                'overall': 0.0
            }
        
        # Get complexity metrics
        complexity_metrics = repo.get('complexity_metrics', {})
        if not isinstance(complexity_metrics, dict):
            complexity_metrics = {}
        
        return RepositoryAnalyticsResponse(
            repository_id=repo_id,
            repository_name=repo.get('name', ''),
            category=repo.get('category', 'supporting'),
            importance_score=repo.get('importance_score', 0.0),
            overall_score=repo.get('overall_score', 0.0),
            acid_scores=acid_scores_dict,
            complexity_metrics=complexity_metrics,
            insights=insights,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get repository analytics: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get repository analytics: {str(e)}"
        )


@router.get("/insights/{user_id}")
async def get_user_insights(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Get insights for a user across all repositories
    
    Returns:
    - Strengths identified across repositories
    - Areas for improvement
    - Priority recommendations
    
    Requirements: 18, 19
    """
    try:
        # Verify authorization
        if str(current_user.id) != user_id:
            if not hasattr(current_user, 'user_type') or current_user.user_type != "hr":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        logger.info(f"Generating insights for user: {user_id}")
        
        # Initialize insights generator
        from app.services.analytics.insights_generator import InsightsGenerator
        
        insights_gen = InsightsGenerator(db)
        
        # Generate user-level insights
        insights = await insights_gen.generate_user_insights(user_id)
        
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user insights: {str(e)}"
        )


@router.get("/recommendations/{user_id}")
async def get_user_recommendations(
    user_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Get top recommendations for a user
    
    Returns prioritized recommendations across all repositories
    
    Requirements: 20
    """
    try:
        # Verify authorization
        if str(current_user.id) != user_id:
            if not hasattr(current_user, 'user_type') or current_user.user_type != "hr":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        logger.info(f"Generating recommendations for user: {user_id}")
        
        # Initialize recommendations engine
        from app.services.analytics.recommendations import RecommendationsEngine
        
        recommendations_engine = RecommendationsEngine(db)
        
        # Generate user-level recommendations
        recommendations = await recommendations_engine.generate_user_recommendations(
            user_id,
            limit=limit
        )
        
        return {
            'user_id': user_id,
            'recommendations': recommendations,
            'total': len(recommendations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user recommendations: {str(e)}"
        )
