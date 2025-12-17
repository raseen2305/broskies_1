"""
Concurrent Data Fetching Service

This service provides concurrent API request handling for parallel data fetching
to improve performance when scanning multiple repositories or fetching large datasets.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import time
from dataclasses import dataclass
from enum import Enum

# Optional aiohttp import for HTTP connection pooling
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

logger = logging.getLogger(__name__)

class RequestPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ConcurrentRequest:
    """Represents a concurrent API request"""
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: RequestPriority = RequestPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 30.0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def __lt__(self, other):
        """Support comparison for priority queue"""
        if not isinstance(other, ConcurrentRequest):
            return NotImplemented
        # Higher priority values should come first (lower in heap)
        return self.priority.value > other.priority.value

@dataclass
class RequestResult:
    """Result of a concurrent request"""
    request_id: str
    success: bool
    result: Any = None
    error: Exception = None
    duration: float = 0.0
    retry_count: int = 0

class RateLimitManager:
    """Manages API rate limits to prevent exhaustion"""
    
    def __init__(self):
        self.api_limits = {
            'github_rest': {'limit': 5000, 'remaining': 5000, 'reset_time': None},
            'github_graphql': {'limit': 5000, 'remaining': 5000, 'reset_time': None}
        }
        self.request_history = defaultdict(deque)
        self.lock = asyncio.Lock()
    
    async def can_make_request(self, api_type: str) -> bool:
        """Check if we can make a request without hitting rate limits"""
        async with self.lock:
            now = datetime.now()
            
            # Clean old requests (older than 1 hour)
            cutoff = now - timedelta(hours=1)
            while (self.request_history[api_type] and 
                   self.request_history[api_type][0] < cutoff):
                self.request_history[api_type].popleft()
            
            # Check current rate limit status
            api_info = self.api_limits.get(api_type, {})
            remaining = api_info.get('remaining', 0)
            reset_time = api_info.get('reset_time')
            
            # If we have remaining requests, allow
            if remaining > 10:  # Keep buffer of 10 requests
                return True
            
            # If reset time has passed, allow
            if reset_time and now > reset_time:
                return True
            
            # Check request frequency (max 30 requests per minute)
            recent_requests = len([
                req_time for req_time in self.request_history[api_type]
                if req_time > now - timedelta(minutes=1)
            ])
            
            return recent_requests < 30
    
    async def record_request(self, api_type: str, response_headers: Dict[str, str] = None):
        """Record a request and update rate limit info"""
        async with self.lock:
            now = datetime.now()
            self.request_history[api_type].append(now)
            
            # Update rate limit info from response headers
            if response_headers:
                if 'x-ratelimit-remaining' in response_headers:
                    self.api_limits[api_type]['remaining'] = int(
                        response_headers['x-ratelimit-remaining']
                    )
                
                if 'x-ratelimit-reset' in response_headers:
                    reset_timestamp = int(response_headers['x-ratelimit-reset'])
                    self.api_limits[api_type]['reset_time'] = datetime.fromtimestamp(reset_timestamp)
    
    async def wait_for_rate_limit(self, api_type: str) -> float:
        """Wait until we can make a request, return wait time"""
        wait_time = 0.0
        
        while not await self.can_make_request(api_type):
            sleep_duration = min(1.0, 60.0)  # Wait 1 second, max 60 seconds
            await asyncio.sleep(sleep_duration)
            wait_time += sleep_duration
            
            # If we've been waiting too long, break
            if wait_time > 300:  # 5 minutes max wait
                logger.warning(f"Rate limit wait exceeded 5 minutes for {api_type}")
                break
        
        return wait_time

class ConcurrentDataFetcher:
    """High-performance concurrent data fetching service"""
    
    def __init__(self, max_concurrent_requests: int = 10, max_queue_size: int = 1000):
        self.max_concurrent_requests = max_concurrent_requests
        self.max_queue_size = max_queue_size
        self.request_queue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self.active_requests = {}
        self.completed_requests = {}
        self.rate_limiter = RateLimitManager()
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.worker_tasks = []
        self.running = False
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_duration': 0.0,
            'average_duration': 0.0,
            'rate_limit_waits': 0,
            'retries': 0
        }
    
    async def start(self):
        """Start the concurrent fetcher workers"""
        if self.running:
            return
        
        self.running = True
        
        # Start worker tasks
        for i in range(self.max_concurrent_requests):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        logger.info(f"Started {len(self.worker_tasks)} concurrent fetcher workers")
    
    async def stop(self):
        """Stop the concurrent fetcher workers"""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        logger.info("Stopped concurrent fetcher workers")
    
    async def submit_request(self, 
                           request_id: str,
                           func: Callable,
                           *args,
                           priority: RequestPriority = RequestPriority.NORMAL,
                           timeout: float = 30.0,
                           max_retries: int = 3,
                           **kwargs) -> str:
        """Submit a request for concurrent execution"""
        
        if self.request_queue.qsize() >= self.max_queue_size:
            raise Exception("Request queue is full")
        
        request = ConcurrentRequest(
            id=request_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries
        )
        
        # Priority queue uses negative values for higher priority
        priority_value = -priority.value
        await self.request_queue.put((priority_value, request))
        
        self.stats['total_requests'] += 1
        logger.debug(f"Submitted request {request_id} with priority {priority.name}")
        
        return request_id
    
    async def get_result(self, request_id: str, timeout: float = None) -> RequestResult:
        """Get the result of a submitted request"""
        start_time = time.time()
        
        while request_id not in self.completed_requests:
            if timeout and (time.time() - start_time) > timeout:
                raise asyncio.TimeoutError(f"Request {request_id} timed out")
            
            await asyncio.sleep(0.1)
        
        result = self.completed_requests.pop(request_id)
        return result
    
    async def submit_and_wait(self,
                            request_id: str,
                            func: Callable,
                            *args,
                            priority: RequestPriority = RequestPriority.NORMAL,
                            timeout: float = 30.0,
                            max_retries: int = 3,
                            **kwargs) -> RequestResult:
        """Submit a request and wait for its completion"""
        
        await self.submit_request(
            request_id, func, *args,
            priority=priority, timeout=timeout, max_retries=max_retries, **kwargs
        )
        
        return await self.get_result(request_id, timeout=timeout + 10)
    
    async def submit_batch(self,
                          requests: List[Tuple[str, Callable, tuple, dict]],
                          priority: RequestPriority = RequestPriority.NORMAL,
                          timeout: float = 30.0) -> List[RequestResult]:
        """Submit multiple requests and wait for all to complete"""
        
        request_ids = []
        
        # Submit all requests
        for request_id, func, args, kwargs in requests:
            await self.submit_request(
                request_id, func, *args,
                priority=priority, timeout=timeout, **kwargs
            )
            request_ids.append(request_id)
        
        # Wait for all results
        results = []
        for request_id in request_ids:
            result = await self.get_result(request_id, timeout=timeout + 10)
            results.append(result)
        
        return results
    
    async def _worker(self, worker_name: str):
        """Worker task that processes requests from the queue"""
        logger.debug(f"Started worker {worker_name}")
        
        while self.running:
            try:
                # Get next request from queue
                try:
                    priority, request = await asyncio.wait_for(
                        self.request_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the request
                await self._process_request(request, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)
        
        logger.debug(f"Stopped worker {worker_name}")
    
    async def _process_request(self, request: ConcurrentRequest, worker_name: str):
        """Process a single request"""
        async with self.semaphore:
            start_time = time.time()
            
            try:
                self.active_requests[request.id] = {
                    'request': request,
                    'worker': worker_name,
                    'start_time': start_time
                }
                
                # Check rate limits if this is a GitHub API request
                api_type = self._detect_api_type(request.func)
                if api_type:
                    wait_time = await self.rate_limiter.wait_for_rate_limit(api_type)
                    if wait_time > 0:
                        self.stats['rate_limit_waits'] += 1
                        logger.debug(f"Waited {wait_time:.2f}s for rate limit on {api_type}")
                
                # Execute the request
                if asyncio.iscoroutinefunction(request.func):
                    result = await asyncio.wait_for(
                        request.func(*request.args, **request.kwargs),
                        timeout=request.timeout
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, request.func, *request.args
                        ),
                        timeout=request.timeout
                    )
                
                # Record successful request
                if api_type:
                    await self.rate_limiter.record_request(api_type)
                
                duration = time.time() - start_time
                
                request_result = RequestResult(
                    request_id=request.id,
                    success=True,
                    result=result,
                    duration=duration,
                    retry_count=request.retry_count
                )
                
                self.stats['successful_requests'] += 1
                self.stats['total_duration'] += duration
                self._update_average_duration()
                
                logger.debug(f"Request {request.id} completed successfully in {duration:.2f}s")
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Handle retries
                if request.retry_count < request.max_retries:
                    request.retry_count += 1
                    self.stats['retries'] += 1
                    
                    # Exponential backoff
                    delay = min(2 ** request.retry_count, 30)
                    await asyncio.sleep(delay)
                    
                    logger.debug(f"Retrying request {request.id} (attempt {request.retry_count + 1})")
                    
                    # Re-queue the request
                    priority_value = -request.priority.value
                    await self.request_queue.put((priority_value, request))
                    return
                
                # Max retries exceeded
                request_result = RequestResult(
                    request_id=request.id,
                    success=False,
                    error=e,
                    duration=duration,
                    retry_count=request.retry_count
                )
                
                self.stats['failed_requests'] += 1
                self.stats['total_duration'] += duration
                self._update_average_duration()
                
                logger.warning(f"Request {request.id} failed after {request.retry_count} retries: {e}")
            
            finally:
                # Clean up and store result
                if request.id in self.active_requests:
                    del self.active_requests[request.id]
                
                self.completed_requests[request.id] = request_result
    
    def _detect_api_type(self, func: Callable) -> Optional[str]:
        """Detect API type from function name/module for rate limiting"""
        func_name = getattr(func, '__name__', '')
        module_name = getattr(func, '__module__', '')
        
        if 'github' in module_name.lower() or 'github' in func_name.lower():
            if 'graphql' in func_name.lower() or 'graphql' in module_name.lower():
                return 'github_graphql'
            return 'github_rest'
        
        return None
    
    def _update_average_duration(self):
        """Update average duration statistics"""
        total_completed = self.stats['successful_requests'] + self.stats['failed_requests']
        if total_completed > 0:
            self.stats['average_duration'] = self.stats['total_duration'] / total_completed
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            **self.stats,
            'active_requests': len(self.active_requests),
            'queued_requests': self.request_queue.qsize(),
            'worker_count': len(self.worker_tasks),
            'running': self.running
        }
    
    def get_active_requests(self) -> Dict[str, Any]:
        """Get information about currently active requests"""
        now = time.time()
        active_info = {}
        
        for request_id, info in self.active_requests.items():
            duration = now - info['start_time']
            active_info[request_id] = {
                'worker': info['worker'],
                'duration': duration,
                'priority': info['request'].priority.name,
                'function': info['request'].func.__name__
            }
        
        return active_info

# Global concurrent fetcher instance
concurrent_fetcher = ConcurrentDataFetcher()

async def initialize_concurrent_fetcher():
    """Initialize the global concurrent fetcher"""
    await concurrent_fetcher.start()
    logger.info("Concurrent data fetcher initialized")

async def shutdown_concurrent_fetcher():
    """Shutdown the global concurrent fetcher"""
    await concurrent_fetcher.stop()
    logger.info("Concurrent data fetcher shutdown")