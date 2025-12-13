"""
HR Candidate Models for Recruitment Dashboard
Models for displaying and filtering developer candidates
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime
from bson import ObjectId


class CandidateCard(BaseModel):
    """Candidate card model for dashboard display"""
    
    username: str
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    role_category: str  # "Full-Stack Developer", "Frontend Developer", etc.
    overall_score: float
    upvotes: int = 0
    primary_languages: List[str] = Field(default_factory=list)  # Top 3 languages
    github_url: str


class ScoredRepository(BaseModel):
    """Scored repository model for candidate profile"""
    
    name: str
    description: Optional[str] = None
    url: str
    score: float
    category: str
    primary_language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    last_updated: Optional[datetime] = None


class CandidateProfile(BaseModel):
    """Complete candidate profile model"""
    
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    profile_picture: Optional[str] = None
    email: Optional[str] = None
    github_url: str
    overall_score: float
    upvotes: int = 0
    repositories_count: int = 0
    total_stars: int = 0
    total_forks: int = 0
    language_proficiency: Dict[str, float] = Field(default_factory=dict)  # {language: percentage}
    scored_repositories: List[ScoredRepository] = Field(default_factory=list)
    account_created: Optional[datetime] = None
    last_active: Optional[datetime] = None


class CandidateFilters(BaseModel):
    """Filters for candidate search"""
    
    language: Optional[str] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    role: Optional[str] = None
    search: Optional[str] = None


class PaginatedCandidates(BaseModel):
    """Paginated candidates response"""
    
    candidates: List[CandidateCard]
    total: int
    page: int
    limit: int
    total_pages: int


class AggregateInsights(BaseModel):
    """Aggregate insights for dashboard"""
    
    total_candidates: int
    average_score: float
    top_languages: List[Tuple[str, int]]  # [(language, count)]
    skill_distribution: Dict[str, int]  # {level: count}
    top_performers: List[CandidateCard]  # Score >= 8.0


class TrendingLanguages(BaseModel):
    """Trending programming languages"""
    
    languages: List[Dict[str, Any]]  # [{"language": "Python", "count": 10, "percentage": 25.5}]


# Query parameter models

class CandidateQueryParams(BaseModel):
    """Query parameters for candidate search"""
    
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    language: Optional[str] = None
    min_score: Optional[float] = Field(default=None, ge=0, le=10)
    max_score: Optional[float] = Field(default=None, ge=0, le=10)
    role: Optional[str] = None
    sort_by: str = Field(default="score")  # "score", "upvotes", "recent"
    search: Optional[str] = None


# Response models

class CandidateListResponse(BaseModel):
    """Response model for candidate list"""
    
    success: bool = True
    data: PaginatedCandidates
    message: Optional[str] = None


class CandidateDetailResponse(BaseModel):
    """Response model for candidate detail"""
    
    success: bool = True
    data: CandidateProfile
    message: Optional[str] = None


class AggregateInsightsResponse(BaseModel):
    """Response model for aggregate insights"""
    
    success: bool = True
    data: AggregateInsights
    message: Optional[str] = None


class TrendingLanguagesResponse(BaseModel):
    """Response model for trending languages"""
    
    success: bool = True
    data: TrendingLanguages
    message: Optional[str] = None
