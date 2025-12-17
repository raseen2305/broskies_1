"""
Enhanced Scan Progress Tracker

This service provides comprehensive progress tracking for GitHub scanning operations
with real-time WebSocket updates, detailed phase management, and error reporting.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import json

from app.websocket.scan_websocket import websocket_manager
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

class ScanPhase(Enum):
    """Enumeration of scanning phases"""
    INITIALIZING = "initializing"
    CONNECTING_GITHUB = "connecting_github"
    FETCHING_USER_PROFILE = "fetching_user_profile"
    FETCHING_REPOSITORIES = "fetching_repositories"
    ANALYZING_REPOSITORIES = "analyzing_repositories"
    FETCHING_CONTRIBUTIONS = "fetching_contributions"
    FETCHING_CONTRIBUTION_CALENDAR = "fetching_contribution_calendar"
    ANALYZING_PULL_REQUESTS = "analyzing_pull_requests"
    ANALYZING_ISSUES = "analyzing_issues"
    CALCULATING_METRICS = "calculating_metrics"
    GENERATING_INSIGHTS = "generating_insights"
    STORING_DATA = "storing_data"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class ScanProgress:
    """Data class for scan progress information"""
    scan_id: str
    user_id: str
    phase: ScanPhase
    progress_percentage: float
    current_repository: Optional[str] = None
    total_repositories: int = 0
    processed_repositories: int = 0
    current_step: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    errors: List[Dict[str, Any]] = None
    warnings: List[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    phase_start_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

class ScanProgressTracker:
    """Enhanced progress tracker for GitHub scanning operations"""
    
    def __init__(self):
        self.active_scans: Dict[str, ScanProgress] = {}
        self.phase_descriptions = {
            ScanPhase.INITIALIZING: "Initializing scan process...",
            ScanPhase.CONNECTING_GITHUB: "Connecting to GitHub API...",
            ScanPhase.FETCHING_USER_PROFILE: "Fetching user profile information...",
            ScanPhase.FETCHING_REPOSITORIES: "Discovering repositories...",
            ScanPhase.ANALYZING_REPOSITORIES: "Analyzing repository details...",
            ScanPhase.FETCHING_CONTRIBUTION_CALENDAR: "Fetching contribution calendar...",
            ScanPhase.ANALYZING_PULL_REQUESTS: "Analyzing pull requests and reviews...",
            ScanPhase.ANALYZING_ISSUES: "Analyzing issues and collaboration...",
            ScanPhase.CALCULATING_METRICS: "Calculating quality metrics and scores...",
            ScanPhase.GENERATING_INSIGHTS: "Generating insights and recommendations...",
            ScanPhase.STORING_DATA: "Storing data to database...",
            ScanPhase.FINALIZING: "Finalizing scan results...",
            ScanPhase.COMPLETED: "Scan completed successfully!",
            ScanPhase.ERROR: "Scan encountered an error"
        }
        
        # Phase weights for progress calculation
        self.phase_weights = {
            ScanPhase.INITIALIZING: 2,
            ScanPhase.CONNECTING_GITHUB: 3,
            ScanPhase.FETCHING_USER_PROFILE: 5,
            ScanPhase.FETCHING_REPOSITORIES: 10,
            ScanPhase.ANALYZING_REPOSITORIES: 40,
            ScanPhase.FETCHING_CONTRIBUTION_CALENDAR: 8,
            ScanPhase.ANALYZING_PULL_REQUESTS: 12,
            ScanPhase.ANALYZING_ISSUES: 8,
            ScanPhase.CALCULATING_METRICS: 7,
            ScanPhase.GENERATING_INSIGHTS: 3,
            ScanPhase.STORING_DATA: 3,
            ScanPhase.FINALIZING: 2
        }
    
    async def start_scan(self, scan_id: str, user_id: str, total_repositories: int = 0) -> None:
        """Initialize a new scan progress tracking"""
        try:
            progress = ScanProgress(
                scan_id=scan_id,
                user_id=user_id,
                phase=ScanPhase.INITIALIZING,
                progress_percentage=0.0,
                total_repositories=total_repositories,
                start_time=datetime.utcnow(),
                phase_start_time=datetime.utcnow()
            )
            
            self.active_scans[scan_id] = progress
            
            # Cache the progress
            await self._cache_progress(scan_id, progress)
            
            # Send initial WebSocket update
            await self._send_websocket_update(progress)
            
            logger.info(f"Started scan progress tracking for scan_id: {scan_id}, user_id: {user_id}")
            
        except Exception as e:
            logger.error(f"Error starting scan progress: {e}")
    
    async def update_phase(self, scan_id: str, phase: ScanPhase, 
                          current_step: Optional[str] = None,
                          current_repository: Optional[str] = None) -> None:
        """Update the current scanning phase"""
        try:
            if scan_id not in self.active_scans:
                logger.warning(f"Scan {scan_id} not found in active scans")
                return
            
            progress = self.active_scans[scan_id]
            
            # Update phase information
            progress.phase = phase
            progress.current_step = current_step or self.phase_descriptions.get(phase, "Processing...")
            progress.phase_start_time = datetime.utcnow()
            
            if current_repository:
                progress.current_repository = current_repository
            
            # Calculate progress percentage
            progress.progress_percentage = self._calculate_progress_percentage(progress)
            
            # Estimate completion time
            progress.estimated_completion = self._estimate_completion_time(progress)
            
            # Cache and broadcast update
            await self._cache_progress(scan_id, progress)
            await self._send_websocket_update(progress)
            
            logger.debug(f"Updated scan {scan_id} to phase {phase.value}: {progress.progress_percentage:.1f}%")
            
        except Exception as e:
            logger.error(f"Error updating scan phase: {e}")
    
    async def update_repository_progress(self, scan_id: str, processed_count: int, 
                                       current_repo: Optional[str] = None) -> None:
        """Update repository processing progress"""
        try:
            if scan_id not in self.active_scans:
                return
            
            progress = self.active_scans[scan_id]
            progress.processed_repositories = processed_count
            
            if current_repo:
                progress.current_repository = current_repo
                progress.current_step = f"Analyzing {current_repo}..."
            
            # Recalculate progress
            progress.progress_percentage = self._calculate_progress_percentage(progress)
            progress.estimated_completion = self._estimate_completion_time(progress)
            
            await self._cache_progress(scan_id, progress)
            await self._send_websocket_update(progress)
            
        except Exception as e:
            logger.error(f"Error updating repository progress: {e}")
    
    async def report_error(self, scan_id: str, error_message: str, 
                          error_type: str = "general", 
                          continue_scan: bool = True) -> None:
        """Report an error during scanning"""
        try:
            if scan_id not in self.active_scans:
                return
            
            progress = self.active_scans[scan_id]
            
            error_info = {
                "type": error_type,
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat(),
                "phase": progress.phase.value
            }
            
            progress.errors.append(error_info)
            
            if not continue_scan:
                progress.phase = ScanPhase.ERROR
                progress.current_step = f"Error: {error_message}"
            else:
                progress.current_step = f"Warning: {error_message} (continuing...)"
            
            await self._cache_progress(scan_id, progress)
            await self._send_websocket_update(progress)
            
            logger.warning(f"Scan {scan_id} error: {error_message}")
            
        except Exception as e:
            logger.error(f"Error reporting scan error: {e}")
    
    async def report_warning(self, scan_id: str, warning_message: str, 
                           warning_type: str = "general") -> None:
        """Report a warning during scanning"""
        try:
            if scan_id not in self.active_scans:
                return
            
            progress = self.active_scans[scan_id]
            
            warning_info = {
                "type": warning_type,
                "message": warning_message,
                "timestamp": datetime.utcnow().isoformat(),
                "phase": progress.phase.value
            }
            
            progress.warnings.append(warning_info)
            
            await self._cache_progress(scan_id, progress)
            await self._send_websocket_update(progress)
            
            logger.info(f"Scan {scan_id} warning: {warning_message}")
            
        except Exception as e:
            logger.error(f"Error reporting scan warning: {e}")
    
    async def complete_scan(self, scan_id: str, results: Dict[str, Any]) -> None:
        """Mark scan as completed with results"""
        try:
            if scan_id not in self.active_scans:
                return
            
            progress = self.active_scans[scan_id]
            progress.phase = ScanPhase.COMPLETED
            progress.progress_percentage = 100.0
            progress.current_step = "Scan completed successfully!"
            progress.estimated_completion = datetime.utcnow()
            
            # Cache final progress and results
            await self._cache_progress(scan_id, progress)
            await self._cache_scan_results(scan_id, results)
            
            # Send completion update
            completion_message = {
                "type": "scan_completed",
                "scan_id": scan_id,
                "progress": asdict(progress),
                "results_summary": {
                    "total_repositories": results.get("repositoryCount", 0),
                    "overall_score": results.get("overallScore", 0),
                    "languages_detected": len(results.get("languages", [])),
                    "tech_stack_items": len(results.get("techStack", [])),
                    "scan_duration": self._calculate_scan_duration(progress)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket_manager.broadcast_to_user(progress.user_id, completion_message)
            
            # Clean up active scan
            del self.active_scans[scan_id]
            
            logger.info(f"Completed scan {scan_id} successfully")
            
        except Exception as e:
            logger.error(f"Error completing scan: {e}")
    
    async def get_progress(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress for a scan"""
        try:
            # Check active scans first
            if scan_id in self.active_scans:
                progress = self.active_scans[scan_id]
                return asdict(progress)
            
            # Check cache
            cached_progress = await cache_service.get(f"scan_progress_{scan_id}")
            if cached_progress:
                return cached_progress
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting scan progress: {e}")
            return None
    
    def _calculate_progress_percentage(self, progress: ScanProgress) -> float:
        """Calculate overall progress percentage based on current phase and repository progress"""
        try:
            # Get base progress from completed phases
            completed_weight = 0
            total_weight = sum(self.phase_weights.values())
            
            for phase in ScanPhase:
                if phase == ScanPhase.COMPLETED or phase == ScanPhase.ERROR:
                    continue
                
                if phase.value < progress.phase.value or (phase == progress.phase and progress.phase == ScanPhase.COMPLETED):
                    completed_weight += self.phase_weights.get(phase, 0)
                elif phase == progress.phase:
                    # Add partial progress for current phase
                    phase_weight = self.phase_weights.get(phase, 0)
                    
                    if phase == ScanPhase.ANALYZING_REPOSITORIES and progress.total_repositories > 0:
                        # Calculate repository analysis progress
                        repo_progress = progress.processed_repositories / progress.total_repositories
                        completed_weight += phase_weight * repo_progress
                    else:
                        # Assume 50% progress for current phase
                        completed_weight += phase_weight * 0.5
                    break
            
            percentage = (completed_weight / total_weight) * 100
            return min(max(percentage, 0.0), 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating progress percentage: {e}")
            return 0.0
    
    def _estimate_completion_time(self, progress: ScanProgress) -> Optional[datetime]:
        """Estimate scan completion time based on current progress"""
        try:
            if not progress.start_time or progress.progress_percentage <= 0:
                return None
            
            elapsed_time = datetime.utcnow() - progress.start_time
            elapsed_seconds = elapsed_time.total_seconds()
            
            if elapsed_seconds <= 0:
                return None
            
            # Calculate estimated total time
            estimated_total_seconds = (elapsed_seconds / progress.progress_percentage) * 100
            remaining_seconds = estimated_total_seconds - elapsed_seconds
            
            if remaining_seconds <= 0:
                return datetime.utcnow()
            
            return datetime.utcnow() + timedelta(seconds=remaining_seconds)
            
        except Exception as e:
            logger.error(f"Error estimating completion time: {e}")
            return None
    
    def _calculate_scan_duration(self, progress: ScanProgress) -> str:
        """Calculate human-readable scan duration"""
        try:
            if not progress.start_time:
                return "Unknown"
            
            duration = datetime.utcnow() - progress.start_time
            total_seconds = int(duration.total_seconds())
            
            if total_seconds < 60:
                return f"{total_seconds} seconds"
            elif total_seconds < 3600:
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                return f"{minutes}m {seconds}s"
            else:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                return f"{hours}h {minutes}m"
                
        except Exception as e:
            logger.error(f"Error calculating scan duration: {e}")
            return "Unknown"
    
    async def _cache_progress(self, scan_id: str, progress: ScanProgress) -> None:
        """Cache progress information"""
        try:
            cache_key = f"scan_progress_{scan_id}"
            progress_dict = asdict(progress)
            
            # Convert datetime objects to ISO strings for JSON serialization
            if progress_dict.get('start_time'):
                progress_dict['start_time'] = progress.start_time.isoformat()
            if progress_dict.get('phase_start_time'):
                progress_dict['phase_start_time'] = progress.phase_start_time.isoformat()
            if progress_dict.get('estimated_completion'):
                progress_dict['estimated_completion'] = progress.estimated_completion.isoformat()
            
            # Convert enum to string
            progress_dict['phase'] = progress.phase.value
            
            await cache_service.set(cache_key, progress_dict, ttl=3600)  # Cache for 1 hour
            
        except Exception as e:
            logger.error(f"Error caching progress: {e}")
    
    async def _cache_scan_results(self, scan_id: str, results: Dict[str, Any]) -> None:
        """Cache scan results"""
        try:
            cache_key = f"scan_results_{scan_id}"
            await cache_service.set(cache_key, results, ttl=86400)  # Cache for 24 hours
            
        except Exception as e:
            logger.error(f"Error caching scan results: {e}")
    
    async def _send_websocket_update(self, progress: ScanProgress) -> None:
        """Send progress update via WebSocket"""
        try:
            progress_dict = asdict(progress)
            
            # Convert datetime objects to ISO strings
            if progress_dict.get('start_time'):
                progress_dict['start_time'] = progress.start_time.isoformat()
            if progress_dict.get('phase_start_time'):
                progress_dict['phase_start_time'] = progress.phase_start_time.isoformat()
            if progress_dict.get('estimated_completion'):
                progress_dict['estimated_completion'] = progress.estimated_completion.isoformat()
            
            # Convert enum to string
            progress_dict['phase'] = progress.phase.value
            
            message = {
                "type": "scan_progress_update",
                "scan_id": progress.scan_id,
                "progress": progress_dict,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket_manager.broadcast_to_user(progress.user_id, message)
            
        except Exception as e:
            logger.error(f"Error sending WebSocket update: {e}")

# Global progress tracker instance
progress_tracker = ScanProgressTracker()

# Helper functions for easy access
async def start_scan_progress(scan_id: str, user_id: str, total_repositories: int = 0) -> None:
    """Start tracking progress for a scan"""
    await progress_tracker.start_scan(scan_id, user_id, total_repositories)

async def update_scan_phase(scan_id: str, phase: ScanPhase, 
                           current_step: Optional[str] = None,
                           current_repository: Optional[str] = None) -> None:
    """Update scan phase"""
    await progress_tracker.update_phase(scan_id, phase, current_step, current_repository)

async def update_repository_progress(scan_id: str, processed_count: int, 
                                   current_repo: Optional[str] = None) -> None:
    """Update repository processing progress"""
    await progress_tracker.update_repository_progress(scan_id, processed_count, current_repo)

async def report_scan_error(scan_id: str, error_message: str, 
                           error_type: str = "general", 
                           continue_scan: bool = True) -> None:
    """Report a scan error"""
    await progress_tracker.report_error(scan_id, error_message, error_type, continue_scan)

async def report_scan_warning(scan_id: str, warning_message: str, 
                             warning_type: str = "general") -> None:
    """Report a scan warning"""
    await progress_tracker.report_warning(scan_id, warning_message, warning_type)

async def complete_scan_progress(scan_id: str, results: Dict[str, Any]) -> None:
    """Complete scan progress tracking"""
    await progress_tracker.complete_scan(scan_id, results)

async def get_scan_progress_data(scan_id: str) -> Optional[Dict[str, Any]]:
    """Get scan progress data"""
    return await progress_tracker.get_progress(scan_id)