"""
Analysis Response Models
Pydantic models for analysis API responses with validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class ProductionIndicators(BaseModel):
    """Production indicators for a repository"""
    has_tests: bool = False
    has_ci_cd: bool = False
    has_docker: bool = False
    has_monitoring: bool = False


class ACIDScores(BaseModel):
    """ACID scores for repository evaluation"""
    architecture: float = Field(ge=0, le=100)
    code_quality: float = Field(ge=0, le=100)
    innovation: float = Field(ge=0, le=100)
    documentation: float = Field(ge=0, le=100)


class QualityMetrics(BaseModel):
    """Quality metrics for repository evaluation"""
    code_quality: float = Field(ge=0, le=100)
    technical_excellence: float = Field(ge=0, le=100)
    production_readiness: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)


class RepositoryEvaluation(BaseModel):
    """Evaluation data for a repository"""
    overall_score: float = Field(ge=0, le=100)
    acid_scores: ACIDScores
    quality_metrics: QualityMetrics
    production_indicators: ProductionIndicators
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list, alias="improvement_areas")
    evaluated_at: str
    evaluation_type: str = "metadata_based"


class AnalyzedRepository(BaseModel):
    """
    Repository with analysis fields.
    
    Requirements: 8.1-8.8
    """
    # Basic repository information (always present)
    id: Optional[int] = None
    name: str
    full_name: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = Field(default=0, alias="stargazers_count")
    forks: int = Field(default=0, alias="forks_count")
    watchers: int = Field(default=0, alias="watchers_count")
    size: int = 0
    topics: List[str] = Field(default_factory=list)
    homepage: Optional[str] = None
    html_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Analysis fields (added after analysis)
    analyzed: bool = False
    importance_score: Optional[float] = Field(default=None, ge=0, le=100)
    category: Optional[Literal["flagship", "significant", "supporting"]] = None
    evaluated: bool = False
    evaluation: Optional[RepositoryEvaluation] = None
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "production-app",
                "description": "Production application",
                "language": "Python",
                "stars": 100,
                "forks": 25,
                "size": 5000,
                "analyzed": True,
                "importance_score": 95.0,
                "category": "flagship",
                "evaluated": True,
                "evaluation": {
                    "overall_score": 88.5,
                    "acid_scores": {
                        "architecture": 90.0,
                        "code_quality": 88.0,
                        "innovation": 87.0,
                        "documentation": 89.0
                    },
                    "quality_metrics": {
                        "code_quality": 88.0,
                        "technical_excellence": 90.0,
                        "production_readiness": 92.0,
                        "innovation_score": 85.0
                    },
                    "production_indicators": {
                        "has_tests": True,
                        "has_ci_cd": True,
                        "has_docker": True,
                        "has_monitoring": False
                    },
                    "strengths": [
                        "Comprehensive test coverage",
                        "Automated CI/CD pipeline"
                    ],
                    "improvements": [
                        "Add monitoring and logging"
                    ],
                    "evaluated_at": "2024-11-13T12:00:00Z",
                    "evaluation_type": "metadata_based"
                }
            }
        }


class AnalysisProgress(BaseModel):
    """Progress information for ongoing analysis"""
    total_repos: int
    scored: int = 0
    categorized: int = 0
    evaluated: int = 0
    to_evaluate: int = 0
    percentage: int = Field(ge=0, le=100)
    current_message: Optional[str] = None


class AnalysisStatusResponse(BaseModel):
    """
    Response for analysis status endpoint.
    
    Requirements: 6.1-6.7
    """
    analysis_id: str
    status: Literal["started", "scoring", "categorizing", "evaluating", "calculating", "complete", "failed"]
    current_phase: str
    progress: AnalysisProgress
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "abc123",
                "status": "evaluating",
                "current_phase": "evaluating",
                "progress": {
                    "total_repos": 288,
                    "scored": 288,
                    "categorized": 288,
                    "evaluated": 5,
                    "to_evaluate": 12,
                    "percentage": 42,
                    "current_message": "Evaluating 5 of 12 repositories..."
                },
                "message": "Evaluating 5 of 12 repositories...",
                "error": None,
                "created_at": "2024-11-13T12:00:00Z",
                "updated_at": "2024-11-13T12:00:30Z"
            }
        }


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown"""
    category: Literal["flagship", "significant"]
    count: int
    average_score: float
    weight: float
    contribution: float
    percentage: str


class DetailedScoreBreakdown(BaseModel):
    """Detailed breakdown of overall score calculation"""
    overall_score: float
    components: List[ScoreBreakdown]


class AnalysisResultsResponse(BaseModel):
    """
    Response for analysis results endpoint.
    
    Requirements: 7.1-7.7, 8.1-8.8, 9.1-9.6
    """
    username: str
    repositoryCount: int
    analyzed: bool
    analyzedAt: Optional[str] = None
    overallScore: Optional[float] = Field(default=None, ge=0, le=100)
    evaluatedCount: int = 0
    flagshipCount: int = 0
    significantCount: int = 0
    supportingCount: int = 0
    repositories: List[AnalyzedRepository]
    scoreBreakdown: Optional[DetailedScoreBreakdown] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "developer",
                "repositoryCount": 288,
                "analyzed": True,
                "analyzedAt": "2024-11-13T12:01:00Z",
                "overallScore": 87.5,
                "evaluatedCount": 12,
                "flagshipCount": 4,
                "significantCount": 8,
                "supportingCount": 276,
                "repositories": [],
                "scoreBreakdown": {
                    "overall_score": 87.5,
                    "components": [
                        {
                            "category": "flagship",
                            "count": 4,
                            "average_score": 90.0,
                            "weight": 0.6,
                            "contribution": 54.0,
                            "percentage": "60%"
                        },
                        {
                            "category": "significant",
                            "count": 8,
                            "average_score": 83.0,
                            "weight": 0.4,
                            "contribution": 33.2,
                            "percentage": "40%"
                        }
                    ]
                }
            }
        }


class InitiateAnalysisRequest(BaseModel):
    """Request body for initiating analysis"""
    max_evaluate: int = Field(default=15, ge=1, le=50)
    
    @field_validator('max_evaluate')
    @classmethod
    def validate_max_evaluate(cls, v):
        if v < 1:
            raise ValueError('max_evaluate must be at least 1')
        if v > 50:
            raise ValueError('max_evaluate cannot exceed 50')
        return v


class InitiateAnalysisResponse(BaseModel):
    """Response for initiating analysis"""
    analysis_id: str
    status: Literal["started"]
    message: str
    estimated_time: str
    repositories_count: int
    max_evaluate: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "abc123",
                "status": "started",
                "message": "Analysis initiated for 288 repositories",
                "estimated_time": "45-60 seconds",
                "repositories_count": 288,
                "max_evaluate": 15
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Analysis not found",
                "error_code": "ANALYSIS_NOT_FOUND",
                "timestamp": "2024-11-13T12:00:00Z"
            }
        }
