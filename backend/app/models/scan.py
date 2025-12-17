from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId

class ScanStatus(Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    ERROR = "error"

class ScanProgress(BaseModel):
    task_id: str
    user_id: str
    github_url: str
    scan_type: str
    status: ScanStatus
    progress: int = 0
    total_repos: int = 0
    processed_repos: int = 0
    current_repo: str = ""
    errors: List[str] = []
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }

class ScanResult(BaseModel):
    user_id: str
    github_url: str
    scan_type: str
    repositories: List[Dict[str, Any]]
    overall_scores: Dict[str, Any]
    summary: Dict[str, Any]
    scan_completed_at: datetime
    task_id: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }

class ScanRequest(BaseModel):
    github_url: str
    scan_type: str  # 'myself' or 'others'
    user_id: Optional[str] = None

class ScanResponse(BaseModel):
    scan_id: str
    message: str
    status: str = "started"

class RepositoryAnalysis(BaseModel):
    repository_id: str
    name: str
    full_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    languages: Dict[str, int] = {}
    stars: int = 0
    forks: int = 0
    size: int = 0
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime] = None
    
    # Analysis results
    acid_scores: Dict[str, Any] = {}
    complexity_metrics: Dict[str, Any] = {}
    security_analysis: Dict[str, Any] = {}
    quality_metrics: Dict[str, Any] = {}
    
    # Metadata
    analyzed_at: datetime
    analysis_version: str = "1.0"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }

class UserProfile(BaseModel):
    user_id: str
    github_username: str
    total_repositories: int = 0
    analyzed_repositories: int = 0
    overall_score: float = 0.0
    language_breakdown: Dict[str, Any] = {}
    skill_assessment: Dict[str, Any] = {}
    technology_stack: List[str] = []
    recommendations: List[str] = []
    last_scan_date: Optional[datetime] = None
    profile_updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }