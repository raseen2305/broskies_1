"""
Comprehensive database models for enhanced GitHub integration.
These models extend the existing basic models with detailed data structures
for comprehensive GitHub data storage and analysis.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from bson import ObjectId
from enum import Enum

# ============================================================================
# Enhanced User Profile Models
# ============================================================================

class GitHubUserProfile(BaseModel):
    """Enhanced GitHub user profile with comprehensive data"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    user_id: str  # Reference to main user record
    
    # Basic GitHub profile data
    login: str
    github_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    blog: Optional[str] = None
    twitter_username: Optional[str] = None
    
    # GitHub statistics
    public_repos: int = 0
    public_gists: int = 0
    followers: int = 0
    following: int = 0
    
    # Profile metadata
    avatar_url: str
    html_url: str
    hireable: Optional[bool] = None
    github_created_at: datetime
    github_updated_at: datetime
    
    # System metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    data_freshness: datetime = Field(default_factory=datetime.utcnow)

class ContributionDay(BaseModel):
    """Individual day contribution data"""
    date: str  # YYYY-MM-DD format
    contribution_count: int
    level: int  # 0-4 intensity level for heatmap

class ContributionCalendar(BaseModel):
    """User contribution calendar data from GitHub GraphQL"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    user_id: str
    github_username: str
    
    # Contribution statistics
    total_contributions: int
    contribution_days: List[ContributionDay]
    current_streak: int
    longest_streak: int
    
    # Activity patterns
    most_active_day: str  # Day of week
    contribution_patterns: Dict[str, int]  # Hour/day patterns
    weekly_average: float
    monthly_totals: Dict[str, int]  # Month -> contribution count
    
    # Metadata
    calendar_year: int
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    data_source: str = "graphql"  # graphql or rest

# ============================================================================
# Enhanced Repository Models
# ============================================================================

class LanguageMetrics(BaseModel):
    """Detailed language analysis for a repository"""
    name: str
    bytes: int
    percentage: float
    files_count: int
    complexity_score: Optional[float] = None

class SecurityAnalysis(BaseModel):
    """Security analysis results for repository"""
    vulnerability_count: int = 0
    security_score: float = 0.0
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies_analyzed: int = 0
    outdated_dependencies: int = 0
    security_best_practices: Dict[str, bool] = Field(default_factory=dict)

class CodeAnalysisResult(BaseModel):
    """Comprehensive code analysis results"""
    total_files: int = 0
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    function_count: int = 0
    class_count: int = 0
    complexity_score: float = 0.0
    
    # Language breakdown
    language_breakdown: Dict[str, LanguageMetrics] = Field(default_factory=dict)
    
    # Quality metrics
    documentation_coverage: float = 0.0
    test_coverage: float = 0.0
    maintainability_index: float = 0.0
    
    # Security analysis
    security_analysis: SecurityAnalysis = Field(default_factory=SecurityAnalysis)

class ACIDScores(BaseModel):
    """Enhanced ACID scoring with detailed breakdown"""
    atomicity: float = 0.0
    consistency: float = 0.0
    isolation: float = 0.0
    durability: float = 0.0
    overall: float = 0.0
    
    # Detailed breakdown for each component
    detailed_breakdown: Dict[str, Any] = Field(default_factory=dict)
    scoring_methodology: str = "enhanced_v2"
    confidence_score: float = 0.0

class CommitData(BaseModel):
    """Individual commit information"""
    sha: str
    message: str
    author_name: str
    author_email: str
    author_date: datetime
    committer_name: str
    committer_email: str
    committer_date: datetime
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    url: str

class ContributorData(BaseModel):
    """Repository contributor information"""
    login: str
    id: int
    avatar_url: str
    contributions: int
    type: str = "User"  # User or Bot

class DetailedRepository(BaseModel):
    """Enhanced repository model with comprehensive analysis"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    user_id: str
    
    # Basic repository information (extends existing Repository model)
    github_id: int
    name: str
    full_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    languages: Dict[str, int] = Field(default_factory=dict)
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    size: int = 0
    open_issues: int = 0
    
    # Repository metadata
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime] = None
    is_fork: bool = False
    is_private: bool = False
    is_archived: bool = False
    is_disabled: bool = False
    topics: List[str] = Field(default_factory=list)
    license: Optional[str] = None
    default_branch: str = "main"
    
    # URLs
    clone_url: str
    html_url: str
    homepage: Optional[str] = None
    
    # Enhanced analysis data
    code_analysis: CodeAnalysisResult = Field(default_factory=CodeAnalysisResult)
    acid_scores: ACIDScores = Field(default_factory=ACIDScores)
    
    # Commit and contributor data
    commit_history: List[CommitData] = Field(default_factory=list)
    contributors: List[ContributorData] = Field(default_factory=list)
    total_commits: int = 0
    
    # Analysis metadata
    last_analyzed: datetime = Field(default_factory=datetime.utcnow)
    analysis_version: str = "comprehensive_v1"
    analysis_duration: Optional[float] = None  # seconds

# ============================================================================
# Pull Request and Issue Models
# ============================================================================

class PullRequestReview(BaseModel):
    """Pull request review data"""
    id: int
    user_login: str
    state: str  # APPROVED, CHANGES_REQUESTED, COMMENTED
    submitted_at: datetime
    body: Optional[str] = None

class PullRequestData(BaseModel):
    """Individual pull request information"""
    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str  # open, closed, merged
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    
    # Author information
    author_login: str
    author_id: int
    
    # PR metadata
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    commits: int = 0
    
    # Review data
    reviews: List[PullRequestReview] = Field(default_factory=list)
    review_comments: int = 0
    
    # Labels and assignees
    labels: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)
    
    # URLs
    html_url: str
    diff_url: str

class IssueData(BaseModel):
    """Individual issue information"""
    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str  # open, closed
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    
    # Author information
    author_login: str
    author_id: int
    
    # Issue metadata
    comments: int = 0
    labels: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)
    milestone: Optional[str] = None
    
    # Resolution data
    resolution_time: Optional[int] = None  # hours to close
    
    # URLs
    html_url: str

class PullRequestAnalysis(BaseModel):
    """Analysis of repository pull requests"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    repository_id: str
    user_id: str
    
    # Pull request data
    pull_requests: List[PullRequestData] = Field(default_factory=list)
    
    # Analysis metrics
    total_prs: int = 0
    open_prs: int = 0
    closed_prs: int = 0
    merged_prs: int = 0
    merge_rate: float = 0.0
    
    # Timing metrics
    average_review_time: Optional[float] = None  # hours
    average_merge_time: Optional[float] = None  # hours
    
    # Collaboration metrics
    unique_reviewers: int = 0
    review_participation_rate: float = 0.0
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    analysis_period: str = "all_time"

class IssueAnalysis(BaseModel):
    """Analysis of repository issues"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    repository_id: str
    user_id: str
    
    # Issue data
    issues: List[IssueData] = Field(default_factory=list)
    
    # Analysis metrics
    total_issues: int = 0
    open_issues: int = 0
    closed_issues: int = 0
    resolution_rate: float = 0.0
    
    # Timing metrics
    average_resolution_time: Optional[float] = None  # hours
    
    # Categorization
    issue_categories: Dict[str, int] = Field(default_factory=dict)  # label -> count
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    analysis_period: str = "all_time"

# ============================================================================
# Comprehensive Scan Result Models
# ============================================================================

class CollaborationMetrics(BaseModel):
    """User collaboration and teamwork metrics"""
    total_collaborators: int = 0
    repositories_contributed_to: int = 0
    pull_requests_created: int = 0
    pull_requests_reviewed: int = 0
    issues_created: int = 0
    issues_resolved: int = 0
    code_review_participation: float = 0.0
    mentoring_score: float = 0.0

class LanguageStatistics(BaseModel):
    """Comprehensive language usage statistics"""
    primary_languages: List[str] = Field(default_factory=list)
    language_diversity_score: float = 0.0
    total_bytes_by_language: Dict[str, int] = Field(default_factory=dict)
    repositories_by_language: Dict[str, int] = Field(default_factory=dict)
    language_trends: Dict[str, List[int]] = Field(default_factory=dict)  # monthly usage

class AchievementMetrics(BaseModel):
    """Developer achievement and milestone metrics"""
    total_stars_earned: int = 0
    total_forks_earned: int = 0
    longest_commit_streak: int = 0
    most_productive_month: Optional[str] = None
    repository_milestones: List[Dict[str, Any]] = Field(default_factory=list)
    contribution_consistency: float = 0.0

class ScanError(BaseModel):
    """Individual scan error information"""
    error_type: str
    error_message: str
    repository: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    recoverable: bool = True

class ScanMetadata(BaseModel):
    """Metadata about the scanning process"""
    scan_id: str
    scan_type: str  # comprehensive, basic, external
    total_repositories: int = 0
    successful_repositories: int = 0
    failed_repositories: int = 0
    scan_duration: float = 0.0  # seconds
    api_calls_made: int = 0
    rate_limits_hit: int = 0
    errors: List[ScanError] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)  # rest, graphql
    scan_started_at: datetime = Field(default_factory=datetime.utcnow)
    scan_completed_at: Optional[datetime] = None

class ComprehensiveScanResult(BaseModel):
    """Complete scan result with all comprehensive data"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    user_id: str
    
    # Core data
    user_profile: GitHubUserProfile
    repositories: List[DetailedRepository] = Field(default_factory=list)
    contribution_calendar: Optional[ContributionCalendar] = None
    
    # Analysis results
    collaboration_metrics: CollaborationMetrics = Field(default_factory=CollaborationMetrics)
    language_statistics: LanguageStatistics = Field(default_factory=LanguageStatistics)
    achievement_metrics: AchievementMetrics = Field(default_factory=AchievementMetrics)
    
    # Overall scores
    overall_acid_score: float = 0.0
    overall_quality_score: float = 0.0
    developer_level: str = "beginner"  # beginner, intermediate, advanced, expert
    
    # Scan metadata
    scan_metadata: ScanMetadata
    
    # System metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    data_version: str = "comprehensive_v1"

# ============================================================================
# Real-time Scanning Progress Models
# ============================================================================

class ScanPhase(Enum):
    """Scanning phases for progress tracking"""
    INITIALIZING = "initializing"
    FETCHING_PROFILE = "fetching_profile"
    FETCHING_REPOSITORIES = "fetching_repositories"
    ANALYZING_CODE = "analyzing_code"
    FETCHING_COMMITS = "fetching_commits"
    FETCHING_PULL_REQUESTS = "fetching_pull_requests"
    FETCHING_ISSUES = "fetching_issues"
    FETCHING_CALENDAR = "fetching_calendar"
    CALCULATING_METRICS = "calculating_metrics"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    ERROR = "error"

class ScanProgressState(BaseModel):
    """Real-time scan progress state"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        use_enum_values=True
    )
    
    id: str = Field(default="", alias="_id")
    scan_id: str
    user_id: str
    
    # Progress tracking
    current_phase: ScanPhase
    progress_percentage: int = 0
    current_repository: Optional[str] = None
    total_repositories: int = 0
    processed_repositories: int = 0
    
    # Status information
    status_message: str = ""
    estimated_completion: Optional[datetime] = None
    
    # Error tracking
    errors: List[ScanError] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Performance metrics
    start_time: datetime = Field(default_factory=datetime.utcnow)
    last_update: datetime = Field(default_factory=datetime.utcnow)
    api_calls_remaining: Optional[int] = None
    
    # Results preview
    repositories_found: int = 0
    repositories_analyzed: int = 0

# ============================================================================
# Cache Metadata Models
# ============================================================================

class CacheMetadata(BaseModel):
    """Metadata for cache invalidation and management"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: str = Field(default="", alias="_id")
    cache_key: str
    cache_type: str  # user_profile, repository, scan_result, etc.
    user_id: Optional[str] = None
    repository_id: Optional[str] = None
    
    # Cache lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = 0
    
    # Cache metadata
    data_size: int = 0  # bytes
    cache_hit_rate: float = 0.0
    invalidation_triggers: List[str] = Field(default_factory=list)
    
    # Data freshness
    source_updated_at: Optional[datetime] = None
    needs_refresh: bool = False