"""
Enhanced Scan Progress Emitter
Provides detailed real-time progress updates during repository scanning
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ScanPhase(str, Enum):
    """Scan phases for progress tracking"""
    CONNECTING = "connecting"
    FETCHING_PROFILE = "fetching_profile"
    FETCHING_REPOS = "fetching_repos"
    FETCHING_PRS = "fetching_prs"
    FETCHING_ISSUES = "fetching_issues"
    ANALYZING_CODE = "analyzing_code"
    CALCULATING_SCORES = "calculating_scores"
    GENERATING_INSIGHTS = "generating_insights"
    COMPLETED = "completed"


class OperationType(str, Enum):
    """Types of operations during scanning"""
    FETCH_REPO = "fetch_repo"
    FETCH_PR = "fetch_pr"
    FETCH_ISSUE = "fetch_issue"
    ANALYZE_FILE = "analyze_file"
    CALCULATE_SCORE = "calculate_score"
    FETCH_ACCOUNT = "fetch_account"


class ScanProgressEmitter:
    """
    Emits detailed progress events during repository scanning.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    def __init__(self, scan_id: str, user_id: str, websocket_manager):
        """
        Initialize the progress emitter.
        
        Args:
            scan_id: Unique identifier for this scan
            user_id: User ID for WebSocket broadcasting
            websocket_manager: WebSocket manager instance
        """
        self.scan_id = scan_id
        self.user_id = user_id
        self.websocket_manager = websocket_manager
        self.start_time = datetime.utcnow()
        self.phase_start_times: Dict[str, datetime] = {}
        self.errors: List[Dict[str, Any]] = []
        self.total_repositories = 0
        self.current_repository_index = 0
        
        # Phase weights for progress calculation
        self.phase_weights = {
            ScanPhase.CONNECTING: 2,
            ScanPhase.FETCHING_PROFILE: 5,
            ScanPhase.FETCHING_REPOS: 10,
            ScanPhase.FETCHING_PRS: 15,
            ScanPhase.FETCHING_ISSUES: 15,
            ScanPhase.ANALYZING_CODE: 35,
            ScanPhase.CALCULATING_SCORES: 15,
            ScanPhase.GENERATING_INSIGHTS: 3
        }
        
        logger.info(f"Initialized progress emitter for scan {scan_id}")
    
    def _calculate_progress_percentage(
        self,
        phase: ScanPhase,
        phase_progress: float = 0.0
    ) -> float:
        """
        Calculate overall progress percentage based on phase and phase progress.
        
        Args:
            phase: Current scan phase
            phase_progress: Progress within current phase (0.0 to 1.0)
            
        Returns:
            Overall progress percentage (0-100)
        """
        # Calculate cumulative weight of completed phases
        completed_weight = 0
        total_weight = sum(self.phase_weights.values())
        
        phase_order = list(ScanPhase)
        current_phase_index = phase_order.index(phase)
        
        for i, p in enumerate(phase_order):
            if i < current_phase_index:
                completed_weight += self.phase_weights.get(p, 0)
        
        # Add progress within current phase
        current_phase_weight = self.phase_weights.get(phase, 0)
        current_phase_contribution = current_phase_weight * phase_progress
        
        # Calculate percentage
        total_progress = (completed_weight + current_phase_contribution) / total_weight
        return min(100.0, max(0.0, total_progress * 100))
    
    def _calculate_time_estimates(
        self,
        progress_percentage: float
    ) -> Dict[str, Any]:
        """
        Calculate time estimates based on current progress.
        
        Args:
            progress_percentage: Current progress (0-100)
            
        Returns:
            Dictionary with time estimates
        """
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        
        if progress_percentage > 0:
            estimated_total = (elapsed / progress_percentage) * 100
            estimated_remaining = max(0, estimated_total - elapsed)
        else:
            estimated_remaining = 0
        
        estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_remaining)
        
        return {
            "elapsedSeconds": int(elapsed),
            "estimatedRemainingSeconds": int(estimated_remaining),
            "estimatedCompletionTime": estimated_completion.isoformat()
        }
    
    async def emit_progress(
        self,
        phase: ScanPhase,
        current_operation: Dict[str, Any],
        phase_progress: float = 0.0,
        account_info: Optional[Dict[str, Any]] = None,
        repository_progress: Optional[Dict[str, Any]] = None,
        pr_progress: Optional[Dict[str, Any]] = None,
        issue_progress: Optional[Dict[str, Any]] = None,
        analysis_metrics: Optional[Dict[str, Any]] = None,
        status: str = "in_progress"
    ):
        """
        Emit a detailed progress event.
        
        Args:
            phase: Current scan phase
            current_operation: Details about current operation
            phase_progress: Progress within current phase (0.0 to 1.0)
            account_info: Account-level information
            repository_progress: Repository scanning progress
            pr_progress: Pull request fetching progress
            issue_progress: Issue fetching progress
            analysis_metrics: Code analysis metrics
            status: Current status (in_progress, completed, error, paused)
            
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
        """
        try:
            # Calculate progress percentage
            progress_percentage = self._calculate_progress_percentage(phase, phase_progress)
            
            # Calculate time estimates
            time_estimates = self._calculate_time_estimates(progress_percentage)
            
            # Build progress event
            event = {
                "scanId": self.scan_id,
                "timestamp": datetime.utcnow().isoformat(),
                "phase": phase.value,
                "progressPercentage": round(progress_percentage, 2),
                "currentOperation": current_operation,
                "timeEstimates": time_estimates,
                "status": status,
                "errors": self.errors
            }
            
            # Add optional fields
            if account_info:
                event["accountInfo"] = account_info
            
            if repository_progress:
                event["repositoryProgress"] = repository_progress
            
            if pr_progress:
                event["prProgress"] = pr_progress
            
            if issue_progress:
                event["issueProgress"] = issue_progress
            
            if analysis_metrics:
                event["analysisMetrics"] = analysis_metrics
            
            # Broadcast to user via WebSocket
            await self.websocket_manager.broadcast_to_user(self.user_id, {
                "type": "scan_progress",
                "task_id": self.scan_id,
                "progress": event
            })
            
            logger.debug(f"Emitted progress: {phase.value} - {progress_percentage:.1f}%")
            
        except Exception as e:
            logger.error(f"Error emitting progress: {e}")
    
    async def emit_account_info(
        self,
        username: str,
        account_type: str,
        avatar_url: str,
        followers: int = 0,
        following: int = 0,
        public_repos: int = 0,
        total_stars: int = 0,
        contribution_streak: int = 0
    ):
        """
        Emit account-level progress information.
        
        Args:
            username: GitHub username
            account_type: Account type (User or Organization)
            avatar_url: Avatar URL
            followers: Follower count
            following: Following count
            public_repos: Public repository count
            total_stars: Total stars across all repos
            contribution_streak: Current contribution streak
            
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
        """
        account_info = {
            "username": username,
            "accountType": account_type,
            "avatarUrl": avatar_url,
            "followers": followers,
            "following": following,
            "publicRepos": public_repos,
            "totalStars": total_stars,
            "contributionStreak": contribution_streak
        }
        
        await self.emit_progress(
            phase=ScanPhase.FETCHING_PROFILE,
            current_operation={
                "type": OperationType.FETCH_ACCOUNT.value,
                "target": username,
                "details": f"Fetched account information for {username}",
                "startTime": datetime.utcnow().isoformat()
            },
            phase_progress=1.0,
            account_info=account_info
        )
    
    async def emit_repository_progress(
        self,
        current_index: int,
        total: int,
        current_repo: Optional[Dict[str, Any]] = None
    ):
        """
        Emit repository-level progress.
        
        Args:
            current_index: Current repository index (1-based)
            total: Total number of repositories
            current_repo: Current repository details
            
        Requirements: 1.2, 1.3
        """
        self.current_repository_index = current_index
        self.total_repositories = total
        
        repository_progress = {
            "current": current_index,
            "total": total
        }
        
        if current_repo:
            repository_progress["currentRepo"] = current_repo
        
        # Calculate phase progress based on repository progress
        phase_progress = current_index / max(total, 1)
        
        operation_details = f"Processing repository {current_index} of {total}"
        if current_repo:
            operation_details = f"Processing {current_repo.get('name', 'repository')} ({current_index}/{total})"
        
        await self.emit_progress(
            phase=ScanPhase.FETCHING_REPOS,
            current_operation={
                "type": OperationType.FETCH_REPO.value,
                "target": current_repo.get("fullName", "") if current_repo else "",
                "details": operation_details,
                "startTime": datetime.utcnow().isoformat()
            },
            phase_progress=phase_progress,
            repository_progress=repository_progress
        )
    
    async def emit_pr_progress(
        self,
        repo_name: str,
        fetched: int,
        total: int,
        open_count: int = 0,
        closed_count: int = 0,
        merged_count: int = 0
    ):
        """
        Emit pull request fetching progress.
        
        Args:
            repo_name: Repository name
            fetched: Number of PRs fetched
            total: Total number of PRs
            open_count: Number of open PRs
            closed_count: Number of closed PRs
            merged_count: Number of merged PRs
            
        Requirements: 1.4
        """
        pr_progress = {
            "fetched": fetched,
            "total": total,
            "openCount": open_count,
            "closedCount": closed_count,
            "mergedCount": merged_count
        }
        
        phase_progress = fetched / max(total, 1)
        
        await self.emit_progress(
            phase=ScanPhase.FETCHING_PRS,
            current_operation={
                "type": OperationType.FETCH_PR.value,
                "target": repo_name,
                "details": f"Fetching pull requests for {repo_name} ({fetched}/{total})",
                "startTime": datetime.utcnow().isoformat()
            },
            phase_progress=phase_progress,
            pr_progress=pr_progress
        )
    
    async def emit_issue_progress(
        self,
        repo_name: str,
        fetched: int,
        total: int,
        open_count: int = 0,
        closed_count: int = 0
    ):
        """
        Emit issue fetching progress.
        
        Args:
            repo_name: Repository name
            fetched: Number of issues fetched
            total: Total number of issues
            open_count: Number of open issues
            closed_count: Number of closed issues
            
        Requirements: 1.5
        """
        issue_progress = {
            "fetched": fetched,
            "total": total,
            "openCount": open_count,
            "closedCount": closed_count
        }
        
        phase_progress = fetched / max(total, 1)
        
        await self.emit_progress(
            phase=ScanPhase.FETCHING_ISSUES,
            current_operation={
                "type": OperationType.FETCH_ISSUE.value,
                "target": repo_name,
                "details": f"Fetching issues for {repo_name} ({fetched}/{total})",
                "startTime": datetime.utcnow().isoformat()
            },
            phase_progress=phase_progress,
            issue_progress=issue_progress
        )
    
    async def emit_analysis_progress(
        self,
        repo_name: str,
        current_file: str,
        files_analyzed: int,
        total_files: int,
        lines_of_code: int = 0,
        api_calls_made: int = 0,
        api_calls_remaining: int = 0
    ):
        """
        Emit code analysis progress with file details.
        
        Args:
            repo_name: Repository name
            current_file: Current file being analyzed
            files_analyzed: Number of files analyzed
            total_files: Total number of files
            lines_of_code: Total lines of code processed
            api_calls_made: Number of API calls made
            api_calls_remaining: Remaining API calls
            
        Requirements: 1.3, 4.3, 4.4
        """
        analysis_metrics = {
            "filesAnalyzed": files_analyzed,
            "totalFiles": total_files,
            "linesOfCode": lines_of_code,
            "apiCallsMade": api_calls_made,
            "apiCallsRemaining": api_calls_remaining
        }
        
        phase_progress = files_analyzed / max(total_files, 1)
        
        await self.emit_progress(
            phase=ScanPhase.ANALYZING_CODE,
            current_operation={
                "type": OperationType.ANALYZE_FILE.value,
                "target": current_file,
                "details": f"Analyzing {current_file} in {repo_name} ({files_analyzed}/{total_files})",
                "startTime": datetime.utcnow().isoformat()
            },
            phase_progress=phase_progress,
            analysis_metrics=analysis_metrics
        )
    
    async def emit_score_calculation(
        self,
        repo_name: str,
        calculation_type: str,
        progress: float = 0.0
    ):
        """
        Emit score calculation progress.
        
        Args:
            repo_name: Repository name
            calculation_type: Type of score being calculated
            progress: Progress within score calculation (0.0 to 1.0)
            
        Requirements: 1.3
        """
        await self.emit_progress(
            phase=ScanPhase.CALCULATING_SCORES,
            current_operation={
                "type": OperationType.CALCULATE_SCORE.value,
                "target": repo_name,
                "details": f"Calculating {calculation_type} score for {repo_name}",
                "startTime": datetime.utcnow().isoformat()
            },
            phase_progress=progress
        )
    
    async def emit_error(
        self,
        error_code: str,
        error_message: str,
        recovery_suggestion: Optional[str] = None
    ):
        """
        Emit error event with recovery suggestions.
        
        Args:
            error_code: Error code
            error_message: Error message
            recovery_suggestion: Suggested recovery action
            
        Requirements: 3.3
        """
        error_entry = {
            "code": error_code,
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if recovery_suggestion:
            error_entry["recoverySuggestion"] = recovery_suggestion
        
        self.errors.append(error_entry)
        
        await self.emit_progress(
            phase=ScanPhase.ANALYZING_CODE,  # Use current phase
            current_operation={
                "type": "error",
                "target": "",
                "details": error_message,
                "startTime": datetime.utcnow().isoformat()
            },
            status="error"
        )
        
        logger.error(f"Scan error: {error_code} - {error_message}")
    
    async def emit_completion(
        self,
        summary: Optional[Dict[str, Any]] = None
    ):
        """
        Emit scan completion event.
        
        Args:
            summary: Summary of scan results
            
        Requirements: 5.5
        """
        await self.emit_progress(
            phase=ScanPhase.COMPLETED,
            current_operation={
                "type": "completion",
                "target": "",
                "details": "Scan completed successfully",
                "startTime": datetime.utcnow().isoformat()
            },
            phase_progress=1.0,
            status="completed"
        )
        
        logger.info(f"Scan {self.scan_id} completed")
