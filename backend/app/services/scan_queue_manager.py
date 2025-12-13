"""
Scan Queue Manager

This service manages queues for large scanning operations, providing
resource management and preventing API rate limit exhaustion.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
from collections import defaultdict, deque

from .concurrent_data_fetcher import concurrent_fetcher, RequestPriority

logger = logging.getLogger(__name__)

class ScanType(Enum):
    USER_PROFILE = "user_profile"
    REPOSITORY_ANALYSIS = "repository_analysis"
    PULL_REQUEST_ANALYSIS = "pull_request_analysis"
    ISSUE_ANALYSIS = "issue_analysis"
    CONTRIBUTION_CALENDAR = "contribution_calendar"
    COMPREHENSIVE_SCAN = "comprehensive_scan"

class ScanStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ScanJob:
    """Represents a scanning job in the queue"""
    id: str
    scan_type: ScanType
    user_id: str
    target: str  # username, repo name, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: RequestPriority = RequestPriority.NORMAL
    status: ScanStatus = ScanStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    current_phase: str = "Queued"
    result: Any = None
    error: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    completed_subtasks: List[str] = field(default_factory=list)
    estimated_duration: Optional[float] = None
    actual_duration: Optional[float] = None

@dataclass
class QueueStats:
    """Queue statistics"""
    total_jobs: int = 0
    queued_jobs: int = 0
    running_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    average_duration: float = 0.0
    throughput_per_hour: float = 0.0

class ScanQueueManager:
    """Manages scanning job queues with resource management"""
    
    def __init__(self, max_concurrent_scans: int = 5):
        self.max_concurrent_scans = max_concurrent_scans
        self.job_queue = asyncio.PriorityQueue()
        self.active_jobs = {}
        self.completed_jobs = {}
        self.job_history = deque(maxlen=1000)
        self.worker_tasks = []
        self.running = False
        self.stats = QueueStats()
        self.resource_monitor = ResourceMonitor()
        
    async def start(self):
        """Start the queue manager workers"""
        if self.running:
            return
            
        self.running = True
        
        # Start worker tasks
        for i in range(self.max_concurrent_scans):
            task = asyncio.create_task(self._worker(f"scan-worker-{i}"))
            self.worker_tasks.append(task)
        
        logger.info(f"Started {len(self.worker_tasks)} scan queue workers")
    
    async def stop(self):
        """Stop the queue manager workers"""
        if not self.running:
            return
            
        self.running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        logger.info("Stopped scan queue workers")
    
    async def submit_scan_job(self, 
                             scan_type: ScanType,
                             user_id: str,
                             target: str,
                             parameters: Dict[str, Any] = None,
                             priority: RequestPriority = RequestPriority.NORMAL) -> str:
        """Submit a new scan job to the queue"""
        
        job_id = str(uuid.uuid4())
        
        job = ScanJob(
            id=job_id,
            scan_type=scan_type,
            user_id=user_id,
            target=target,
            parameters=parameters or {},
            priority=priority
        )
        
        # Add to queue with priority
        priority_value = -priority.value
        await self.job_queue.put((priority_value, job))
        
        self.stats.total_jobs += 1
        self.stats.queued_jobs += 1
        
        logger.info(f"Submitted scan job {job_id} for {target} (type: {scan_type.value})")
        
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[ScanJob]:
        """Get the status of a scan job"""
        
        # Check active jobs
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        # Check completed jobs
        if job_id in self.completed_jobs:
            return self.completed_jobs[job_id]
        
        # Check job history
        for job in self.job_history:
            if job.id == job_id:
                return job
        
        return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a scan job"""
        
        # Check if job is active
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = ScanStatus.CANCELLED
            job.completed_at = datetime.now()
            
            # Move to completed jobs
            self.completed_jobs[job_id] = job
            del self.active_jobs[job_id]
            
            self.stats.running_jobs -= 1
            
            logger.info(f"Cancelled scan job {job_id}")
            return True
        
        return False
    
    async def get_queue_stats(self) -> QueueStats:
        """Get current queue statistics"""
        
        # Update current counts
        self.stats.queued_jobs = self.job_queue.qsize()
        self.stats.running_jobs = len(self.active_jobs)
        
        # Calculate throughput
        completed_last_hour = len([
            job for job in self.job_history
            if job.completed_at and 
            (datetime.now() - job.completed_at).total_seconds() < 3600
        ])
        self.stats.throughput_per_hour = completed_last_hour
        
        return self.stats
    
    async def _worker(self, worker_name: str):
        """Worker task that processes scan jobs from the queue"""
        logger.debug(f"Started scan worker {worker_name}")
        
        while self.running:
            try:
                # Get next job from queue
                try:
                    priority, job = await asyncio.wait_for(
                        self.job_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Check resource availability
                if not await self.resource_monitor.can_start_scan():
                    # Re-queue the job and wait
                    await self.job_queue.put((priority, job))
                    await asyncio.sleep(5)
                    continue
                
                # Process the job
                await self._process_scan_job(job, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scan worker {worker_name} error: {e}")
                await asyncio.sleep(1)
        
        logger.debug(f"Stopped scan worker {worker_name}")
    
    async def _process_scan_job(self, job: ScanJob, worker_name: str):
        """Process a single scan job"""
        
        try:
            # Mark job as running
            job.status = ScanStatus.RUNNING
            job.started_at = datetime.now()
            job.current_phase = "Starting scan"
            
            self.active_jobs[job.id] = job
            self.stats.queued_jobs -= 1
            self.stats.running_jobs += 1
            
            logger.info(f"Worker {worker_name} starting job {job.id} ({job.scan_type.value})")
            
            # Execute the scan based on type
            result = await self._execute_scan(job)
            
            # Mark job as completed
            job.status = ScanStatus.COMPLETED
            job.completed_at = datetime.now()
            job.result = result
            job.actual_duration = (job.completed_at - job.started_at).total_seconds()
            
            self.stats.completed_jobs += 1
            
            logger.info(f"Worker {worker_name} completed job {job.id} in {job.actual_duration:.2f}s")
            
        except Exception as e:
            # Mark job as failed
            job.status = ScanStatus.FAILED
            job.completed_at = datetime.now()
            job.error = str(e)
            
            if job.started_at:
                job.actual_duration = (job.completed_at - job.started_at).total_seconds()
            
            self.stats.failed_jobs += 1
            
            logger.error(f"Worker {worker_name} failed job {job.id}: {e}")
        
        finally:
            # Clean up
            if job.id in self.active_jobs:
                del self.active_jobs[job.id]
            
            self.completed_jobs[job.id] = job
            self.job_history.append(job)
            self.stats.running_jobs -= 1
            
            # Update average duration
            self._update_average_duration()
    
    async def _execute_scan(self, job: ScanJob) -> Any:
        """Execute a scan job based on its type"""
        
        # This would integrate with the GitHub comprehensive scanner
        # For now, return a placeholder
        
        if job.scan_type == ScanType.COMPREHENSIVE_SCAN:
            job.current_phase = "Comprehensive scanning"
            # Would call GitHubComprehensiveScanner methods
            await asyncio.sleep(2)  # Simulate work
            return {"status": "completed", "data": "scan_result"}
        
        elif job.scan_type == ScanType.USER_PROFILE:
            job.current_phase = "User profile analysis"
            await asyncio.sleep(1)
            return {"status": "completed", "profile": "user_data"}
        
        elif job.scan_type == ScanType.REPOSITORY_ANALYSIS:
            job.current_phase = "Repository analysis"
            await asyncio.sleep(3)
            return {"status": "completed", "repositories": "repo_data"}
        
        else:
            raise Exception(f"Unknown scan type: {job.scan_type}")
    
    def _update_average_duration(self):
        """Update average duration statistics"""
        completed_jobs = [job for job in self.job_history if job.actual_duration]
        
        if completed_jobs:
            total_duration = sum(job.actual_duration for job in completed_jobs)
            self.stats.average_duration = total_duration / len(completed_jobs)

class ResourceMonitor:
    """Monitors system resources and API rate limits"""
    
    def __init__(self):
        self.last_rate_check = None
        self.rate_limit_cache = {}
    
    async def can_start_scan(self) -> bool:
        """Check if we can start a new scan based on resources"""
        
        # Check rate limits (cache for 1 minute)
        now = datetime.now()
        if (not self.last_rate_check or 
            (now - self.last_rate_check).total_seconds() > 60):
            
            # Would check GitHub API rate limits here
            # For now, always allow
            self.last_rate_check = now
            return True
        
        return True

# Global scan queue manager instance
scan_queue_manager = ScanQueueManager()

async def initialize_scan_queue():
    """Initialize the global scan queue manager"""
    await scan_queue_manager.start()
    logger.info("Scan queue manager initialized")

async def shutdown_scan_queue():
    """Shutdown the global scan queue manager"""
    await scan_queue_manager.stop()
    logger.info("Scan queue manager shutdown")
        