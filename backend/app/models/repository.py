from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId


class PullRequest(BaseModel):
    """Pull request data model"""
    number: int
    title: str
    state: str  # open, closed, merged
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    user: str  # PR author username
    html_url: str
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    comments: int = 0
    review_comments: int = 0
    commits: int = 0


class Issue(BaseModel):
    """Issue data model (excluding PRs)"""
    number: int
    title: str
    state: str  # open, closed
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    user: str  # Issue author username
    html_url: str
    comments: int = 0
    labels: List[str] = Field(default_factory=list)


class Milestone(BaseModel):
    """Milestone data model"""
    number: int
    title: str
    description: Optional[str] = None
    state: str  # open, closed
    created_at: datetime
    updated_at: datetime
    due_on: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    open_issues: int = 0
    closed_issues: int = 0


class Project(BaseModel):
    """Project data model"""
    id: int
    name: str
    body: Optional[str] = None
    state: str  # open, closed
    created_at: datetime
    updated_at: datetime
    html_url: str


class Roadmap(BaseModel):
    """Roadmap data aggregating milestones and projects"""
    milestones: List[Milestone] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    total_milestones: int = 0
    open_milestones: int = 0
    closed_milestones: int = 0
    total_projects: int = 0
    open_projects: int = 0
    closed_projects: int = 0


class PRStatistics(BaseModel):
    """Pull request statistics"""
    total: int = 0
    open: int = 0
    closed: int = 0
    merged: int = 0
    recent_prs: List[PullRequest] = Field(default_factory=list)
    avg_time_to_merge_hours: Optional[float] = None
    avg_additions: Optional[float] = None
    avg_deletions: Optional[float] = None


class IssueStatistics(BaseModel):
    """Issue statistics"""
    total: int = 0
    open: int = 0
    closed: int = 0
    recent_issues: List[Issue] = Field(default_factory=list)
    avg_time_to_close_hours: Optional[float] = None
    labels_distribution: Dict[str, int] = Field(default_factory=dict)


class Repository(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    user_id: str
    github_id: int
    name: str
    full_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    languages: Dict[str, int] = Field(default_factory=dict)
    stars: int = 0
    forks: int = 0
    size: int = 0
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime] = None
    is_fork: bool = False
    is_private: bool = False
    topics: List[str] = Field(default_factory=list)
    license: Optional[str] = None
    default_branch: str = "main"
    clone_url: str
    html_url: str
    
    # Enhanced fields for PR/Issue/Roadmap data (Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.3)
    pull_requests: Optional[PRStatistics] = None
    issues: Optional[IssueStatistics] = None
    roadmap: Optional[Roadmap] = None
    
    # Importance scoring fields (Stage 1 - Quick Scan)
    importance_score: Optional[float] = None  # 0-100 score
    category: Optional[str] = None  # flagship | significant | supporting
    
    # Analysis status (Stage 2 - Deep Analysis)
    analyzed: bool = False
    analyzed_at: Optional[datetime] = None

class RepositoryCreate(BaseModel):
    user_id: str
    github_id: int
    name: str
    full_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    languages: Dict[str, int] = Field(default_factory=dict)
    stars: int = 0
    forks: int = 0
    size: int = 0
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime] = None
    is_fork: bool = False
    is_private: bool = False
    topics: List[str] = Field(default_factory=list)
    license: Optional[str] = None
    default_branch: str = "main"
    clone_url: str
    html_url: str
    
    # Enhanced fields for PR/Issue/Roadmap data (Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.3)
    pull_requests: Optional[PRStatistics] = None
    issues: Optional[IssueStatistics] = None
    roadmap: Optional[Roadmap] = None
    
    # Importance scoring fields (Stage 1 - Quick Scan)
    importance_score: Optional[float] = None  # 0-100 score
    category: Optional[str] = None  # flagship | significant | supporting
    
    # Analysis status (Stage 2 - Deep Analysis)
    analyzed: bool = False
    analyzed_at: Optional[datetime] = None

class ACIDScore(BaseModel):
    atomicity: float = 0.0
    consistency: float = 0.0
    isolation: float = 0.0
    durability: float = 0.0
    overall: float = 0.0

class QualityMetrics(BaseModel):
    readability: float = 0.0
    maintainability: float = 0.0
    security: float = 0.0
    test_coverage: float = 0.0
    documentation: float = 0.0

class Evaluation(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    repo_id: str
    user_id: str
    acid_score: ACIDScore
    quality_metrics: QualityMetrics
    language_stats: Dict[str, int] = Field(default_factory=dict)
    complexity_score: float = 0.0
    best_practices_score: float = 0.0
    file_count: int = 0
    total_lines: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EvaluationCreate(BaseModel):
    repo_id: str
    user_id: str
    acid_score: ACIDScore
    quality_metrics: QualityMetrics
    language_stats: Dict[str, int] = Field(default_factory=dict)
    complexity_score: float = 0.0
    best_practices_score: float = 0.0
    file_count: int = 0
    total_lines: int = 0