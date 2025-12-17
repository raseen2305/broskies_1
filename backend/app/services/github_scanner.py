import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from github import Github, GithubException, RateLimitExceededException
import base64
import re
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors with detailed classification"""
    
    def __init__(self, message: str, error_type: str, status_code: int = None, retry_after: int = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.retry_after = retry_after
        self.user_friendly_message = self._get_user_friendly_message()
    
    def _get_user_friendly_message(self) -> str:
        """Generate user-friendly error messages"""
        error_messages = {
            "rate_limit": "GitHub API rate limit exceeded. Please try again in a few minutes.",
            "not_found": "The requested GitHub user or repository was not found. Please check the username/repository name.",
            "private_repo": "This repository is private and cannot be accessed. Only public repositories can be analyzed.",
            "forbidden": "Access to this resource is forbidden. The user may have restricted access or the repository is private.",
            "authentication": "GitHub authentication failed. Please check your GitHub token or re-authenticate.",
            "network": "Network error occurred while connecting to GitHub. Please check your internet connection and try again.",
            "server_error": "GitHub servers are experiencing issues. Please try again later.",
            "invalid_request": "Invalid request to GitHub API. Please check the provided information.",
            "unknown": "An unexpected error occurred while accessing GitHub data."
        }
        return error_messages.get(self.error_type, self.message)

class GitHubErrorHandler:
    """Enhanced error handler for GitHub API operations"""
    
    @staticmethod
    def classify_github_exception(e: GithubException) -> GitHubAPIError:
        """Classify GitHub exceptions into user-friendly error types"""
        status_code = e.status
        message = str(e)
        
        if status_code == 404:
            return GitHubAPIError(
                message=f"Resource not found: {message}",
                error_type="not_found",
                status_code=status_code
            )
        elif status_code == 403:
            if "rate limit" in message.lower():
                # Extract retry-after if available
                retry_after = None
                if hasattr(e, 'headers') and 'Retry-After' in e.headers:
                    try:
                        retry_after = int(e.headers['Retry-After'])
                    except (ValueError, KeyError):
                        retry_after = 3600  # Default to 1 hour
                
                return GitHubAPIError(
                    message=f"Rate limit exceeded: {message}",
                    error_type="rate_limit",
                    status_code=status_code,
                    retry_after=retry_after
                )
            elif "private" in message.lower() or "access" in message.lower():
                return GitHubAPIError(
                    message=f"Private repository or access denied: {message}",
                    error_type="private_repo",
                    status_code=status_code
                )
            else:
                return GitHubAPIError(
                    message=f"Access forbidden: {message}",
                    error_type="forbidden",
                    status_code=status_code
                )
        elif status_code == 401:
            return GitHubAPIError(
                message=f"Authentication failed: {message}",
                error_type="authentication",
                status_code=status_code
            )
        elif status_code >= 500:
            return GitHubAPIError(
                message=f"GitHub server error: {message}",
                error_type="server_error",
                status_code=status_code
            )
        elif status_code == 422:
            return GitHubAPIError(
                message=f"Invalid request: {message}",
                error_type="invalid_request",
                status_code=status_code
            )
        else:
            return GitHubAPIError(
                message=f"GitHub API error ({status_code}): {message}",
                error_type="unknown",
                status_code=status_code
            )
    
    @staticmethod
    def handle_network_error(e: Exception) -> GitHubAPIError:
        """Handle network-related errors"""
        return GitHubAPIError(
            message=f"Network error: {str(e)}",
            error_type="network"
        )
    
    @staticmethod
    def should_retry(error: GitHubAPIError, attempt: int, max_retries: int = 3) -> bool:
        """Determine if an operation should be retried"""
        if attempt >= max_retries:
            return False
        
        # Retry on rate limits, server errors, and network errors
        retry_types = ["rate_limit", "server_error", "network"]
        return error.error_type in retry_types

class GitHubRateLimiter:
    """Enhanced rate limiter for GitHub API calls with serverless-optimized backoff"""
    
    def __init__(self, requests_per_hour: int = 5000):
        self.requests_per_hour = requests_per_hour
        self.requests = []
        self.lock = asyncio.Lock()
        self.rate_limit_remaining = requests_per_hour
        self.rate_limit_reset = None
        self.last_rate_limit_check = None
        self.consecutive_rate_limits = 0
        # Serverless-specific settings
        self.max_wait_time = 300  # Max 5 minutes wait for serverless
        self.min_remaining_threshold = 50  # Be more conservative in serverless
    
    async def wait_if_needed(self, progress_callback=None):
        """Wait if rate limit would be exceeded with serverless-optimized backoff"""
        async with self.lock:
            now = time.time()
            
            # Check if we have recent rate limit info - be more conservative for serverless
            if self.rate_limit_remaining <= self.min_remaining_threshold and self.rate_limit_reset:
                wait_time = self.rate_limit_reset - now
                if wait_time > 0:
                    self.consecutive_rate_limits += 1
                    
                    # For serverless, use shorter exponential backoff
                    additional_wait = min(30 * (1.5 ** self.consecutive_rate_limits), self.max_wait_time)
                    total_wait = min(wait_time + additional_wait, self.max_wait_time)
                    
                    logger.warning(f"GitHub API rate limit reached. Waiting {total_wait:.2f} seconds (serverless-optimized, attempt #{self.consecutive_rate_limits})")
                    
                    if progress_callback:
                        await progress_callback(f"Rate limit reached - waiting {total_wait:.0f} seconds")
                    
                    # In serverless, if wait time is too long, raise an exception instead
                    if total_wait > self.max_wait_time:
                        raise GitHubAPIError(
                            message=f"Rate limit exceeded with wait time {total_wait:.0f}s exceeding serverless limit",
                            error_type="rate_limit",
                            retry_after=int(total_wait)
                        )
                    
                    await asyncio.sleep(total_wait)
                    self.consecutive_rate_limits = 0  # Reset on successful wait
                    return
            
            # Remove requests older than 1 hour
            self.requests = [req_time for req_time in self.requests if now - req_time < 3600]
            
            # Check local rate limiting - be more aggressive for serverless
            requests_per_minute = 60  # Limit to 60 requests per minute for serverless
            recent_requests = [req_time for req_time in self.requests if now - req_time < 60]
            
            if len(recent_requests) >= requests_per_minute:
                wait_time = min(60 - (now - recent_requests[0]) + 1, 60)  # Max 1 minute wait
                logger.warning(f"Serverless rate limit reached, waiting {wait_time:.2f} seconds")
                
                if progress_callback:
                    await progress_callback(f"Rate limit protection - waiting {wait_time:.0f} seconds")
                
                await asyncio.sleep(wait_time)
            
            self.requests.append(now)
    
    def update_rate_limit_info(self, remaining: int, reset_timestamp: int):
        """Update rate limit information from GitHub API response headers"""
        self.rate_limit_remaining = remaining
        self.rate_limit_reset = reset_timestamp
        self.last_rate_limit_check = time.time()
        
        if remaining > 100:
            self.consecutive_rate_limits = 0  # Reset if we have plenty of requests left

class GitHubScanner:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.github = None
        self.rate_limiter = GitHubRateLimiter()
        self.error_handler = GitHubErrorHandler()
        self.user = None
        self._token_validated = False
        self._initialize_github_client()
    
    def _initialize_github_client(self):
        """Initialize GitHub client with serverless-optimized settings"""
        try:
            # Initialize with timeout and retry settings for serverless
            self.github = Github(
                self.github_token, 
                per_page=100,
                timeout=30,  # 30 second timeout for serverless
                retry=3      # Retry failed requests
            )
            logger.info("GitHub client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            raise
    
    async def _validate_token(self):
        """Validate GitHub token and initialize user if not already done"""
        if self._token_validated and self.user:
            return
        
        try:
            await self.rate_limiter.wait_if_needed()
            self.user = self.github.get_user()
            self._token_validated = True
            logger.info(f"GitHub token validated for user: {self.user.login}")
        except GithubException as e:
            github_error = self.error_handler.classify_github_exception(e)
            logger.error(f"GitHub token validation failed: {github_error.user_friendly_message}")
            raise Exception(f"GitHub authentication failed: {github_error.user_friendly_message}")
        except Exception as e:
            logger.error(f"Failed to validate GitHub token: {e}")
            raise Exception("GitHub authentication failed")
    
    async def refresh_token_if_needed(self):
        """Check if token needs refresh and handle accordingly"""
        try:
            # For OAuth tokens, we would implement refresh logic here
            # For now, we'll just validate the current token
            await self._validate_token()
        except Exception as e:
            logger.error(f"Token refresh/validation failed: {e}")
            raise
    
    async def handle_rate_limit_response(self, response_headers: dict):
        """Handle rate limit information from GitHub API response headers"""
        try:
            if 'X-RateLimit-Remaining' in response_headers:
                remaining = int(response_headers['X-RateLimit-Remaining'])
                reset_timestamp = int(response_headers.get('X-RateLimit-Reset', 0))
                self.rate_limiter.update_rate_limit_info(remaining, reset_timestamp)
                
                logger.debug(f"Rate limit info updated: {remaining} requests remaining, resets at {reset_timestamp}")
        except (ValueError, KeyError) as e:
            logger.warning(f"Could not parse rate limit headers: {e}")
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status for monitoring"""
        return {
            "remaining": self.rate_limiter.rate_limit_remaining,
            "reset_timestamp": self.rate_limiter.rate_limit_reset,
            "consecutive_limits": self.rate_limiter.consecutive_rate_limits,
            "token_validated": self._token_validated
        }
    
    async def fetch_user_repositories(
        self, 
        username: str, 
        include_forks: bool = False, 
        max_display_repos: int = 35,
        evaluate_limit: int = 15,
        return_metadata: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch user repositories for display.
        
        Fetches all public non-forked repositories, but limits the returned results
        to the most recently updated repositories. Repositories are NOT automatically
        marked for evaluation - they will only be evaluated when the user explicitly
        clicks "Start Analysis".
        
        Args:
            username: GitHub username
            include_forks: Whether to include forked repositories (default: False, always excluded per requirements)
            max_display_repos: Maximum repositories to return (default: 35)
            evaluate_limit: DEPRECATED - No longer used, kept for backward compatibility
            return_metadata: Whether to return metadata along with repositories (default: False for backward compatibility)
        
        Returns:
            If return_metadata is False: List of repository data (backward compatible)
            If return_metadata is True: Dictionary with 'repositories' and 'metadata' keys
        """
        try:
            # Track start time for duration calculation
            start_time = time.time()
            start_timestamp = datetime.now().isoformat()
            
            # Log operation start with timestamp
            logger.info(f"🚀 Starting repository fetch for user: {username}")
            logger.info(f"   Timestamp: {start_timestamp}")
            logger.info(f"   Parameters: max_display={max_display_repos}, include_forks={include_forks}")
            
            # Validate token first
            await self._validate_token()
            logger.debug(f"Token validated successfully for {username}")
            
            await self.rate_limiter.wait_if_needed()
            user = self.github.get_user(username)
            repositories = []
            
            logger.info(f"📚 Fetching repositories (sorted by most recently updated)")
            
            # Get ALL repositories with pagination (sorted by most recently updated)
            repos = user.get_repos(type='public', sort='updated', direction='desc')
            repo_count = 0
            
            # Track filtering statistics
            skipped_forks = 0
            skipped_private = 0
            total_found = 0
            
            # Track errors for reporting
            repo_errors = []
            
            # Track API calls (approximate)
            api_calls_made = 2  # Initial: validate token + get user
            
            for repo in repos:
                total_found += 1
                
                # Apply display limit (max 35 repos returned)
                if repo_count >= max_display_repos:
                    logger.debug(f"Reached display limit of {max_display_repos} repositories")
                    break
                
                # Skip forks (always excluded per requirements)
                if repo.fork:
                    skipped_forks += 1
                    logger.debug(f"Skipping forked repository: {repo.name}")
                    continue
                
                # Skip private repos (they shouldn't be in public list, but double-check)
                if repo.private:
                    skipped_private += 1
                    logger.debug(f"Skipping private repository: {repo.name}")
                    continue
                
                # Use retry logic with graceful degradation
                await self.rate_limiter.wait_if_needed()
                
                # Extract repository data with retry and fallback
                repo_data, has_complete_data, errors = await self._extract_repository_data_with_retry(repo)
                
                # Track API calls (approximate: 1 for repo list + 3-5 per detailed extraction if successful)
                if has_complete_data:
                    api_calls_made += 4  # Approximate: languages, topics, commits, contributors
                else:
                    api_calls_made += 1  # Just the basic repo data
                
                # Add metadata flags
                repo_data['has_complete_data'] = has_complete_data
                # Don't mark for evaluation during scan - user must explicitly start analysis
                repo_data['evaluate_for_scoring'] = False
                
                # Track errors if any occurred
                if errors:
                    repo_errors.append({
                        "repository": repo.name,
                        "errors": errors
                    })
                    logger.warning(f"Repository {repo.name} processed with errors: {errors}")
                
                repositories.append(repo_data)
                repo_count += 1
                
                # Detailed logging for each repository
                status_icon = "✅" if has_complete_data else "⚠️"
                logger.debug(
                    f"{status_icon} Processed: {repo.name} (complete: {has_complete_data})"
                )
                
                # Periodic progress logging every 10 repos
                if repo_count % 10 == 0:
                    logger.info(f"   Progress: {repo_count} repos processed")
                    # Log rate limit status
                    rate_limit_info = self.rate_limiter.rate_limit_remaining
                    if rate_limit_info is not None:
                        logger.debug(f"   Rate limit: {rate_limit_info} requests remaining")
            
            # Calculate statistics
            complete_data_count = sum(1 for repo in repositories if repo.get('has_complete_data', False))
            partial_data_count = len(repositories) - complete_data_count
            fetch_duration = time.time() - start_time
            
            # Create comprehensive metadata
            metadata = {
                "total_found": total_found,
                "total_displayed": len(repositories),
                "skipped_forks": skipped_forks,
                "skipped_private": skipped_private,
                "partial_data_count": partial_data_count,
                "complete_data_count": complete_data_count,
                "errors": self._create_error_summary(repo_errors),
                "fetch_duration_seconds": round(fetch_duration, 2),
                "api_calls_made": api_calls_made
            }
            
            # Comprehensive summary logging
            logger.info("=" * 70)
            logger.info(f"✅ Repository fetch completed for {username}")
            logger.info(f"   📊 Summary:")
            logger.info(f"      • Total found: {total_found} repositories")
            logger.info(f"      • Excluded: {skipped_forks} forks, {skipped_private} private")
            logger.info(f"      • Returned: {len(repositories)} repositories")
            logger.info(f"      • Complete data: {complete_data_count}, Partial data: {partial_data_count}")
            logger.info(f"   ⏱️  Performance:")
            logger.info(f"      • Duration: {fetch_duration:.2f} seconds")
            logger.info(f"      • API calls: ~{api_calls_made}")
            logger.info(f"      • Avg time per repo: {fetch_duration/max(len(repositories), 1):.2f}s")
            
            if repo_errors:
                error_summary = metadata["errors"]
                logger.warning(f"   ⚠️  Errors encountered:")
                logger.warning(f"      • Repositories with errors: {error_summary['repositories_with_errors']}")
                logger.warning(f"      • Total errors: {error_summary['total_errors']}")
                logger.warning(f"      • Error types: {error_summary['error_types']}")
            
            logger.info("=" * 70)
            
            # Return based on return_metadata flag for backward compatibility
            if return_metadata:
                return {
                    "repositories": repositories,
                    "metadata": metadata
                }
            else:
                # Backward compatible: return just the list
                return repositories
            
        except GithubException as e:
            github_error = self.error_handler.classify_github_exception(e)
            logger.error(f"GitHub API error for user {username}: {github_error.user_friendly_message}")
            raise Exception(github_error.user_friendly_message)
        except Exception as e:
            if "network" in str(e).lower() or "connection" in str(e).lower():
                network_error = self.error_handler.handle_network_error(e)
                raise Exception(network_error.user_friendly_message)
            else:
                logger.error(f"Error fetching repositories for {username}: {e}")
                raise Exception(f"Failed to fetch repositories: {str(e)}")
    
    def _get_basic_repository_data(self, repo) -> Dict[str, Any]:
        """
        Extract basic repository data without additional API calls.
        
        This method extracts only the data that is already available from the
        initial repository list fetch, without making any additional API calls.
        This is used as a fallback when detailed data extraction fails.
        
        Args:
            repo: GitHub repository object from PyGithub
            
        Returns:
            Dictionary with basic repository information
        """
        try:
            return {
                # Basic identification
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                
                # Description and metadata
                "description": repo.description or "",
                "language": repo.language,
                
                # Metrics (available without additional API calls)
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "watchers_count": repo.watchers_count,
                "size": repo.size,
                "open_issues_count": repo.open_issues_count,
                
                # Timestamps
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                
                # Status flags
                "fork": repo.fork,
                "private": repo.private,
                "archived": repo.archived if hasattr(repo, 'archived') else False,
                "disabled": repo.disabled if hasattr(repo, 'disabled') else False,
                "is_template": repo.is_template if hasattr(repo, 'is_template') else False,
                
                # URLs
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "homepage": repo.homepage,
                
                # Branch info
                "default_branch": repo.default_branch,
                
                # License (basic info available without API call)
                "license": {"name": repo.license.name, "key": repo.license.key} if repo.license else None,
                
                # Fields that require additional API calls - set to defaults
                "languages": {},
                "topics": [],
                "commit_count": 0,
                "contributor_count": 0,
                "has_readme": False,
                "has_license": bool(repo.license),  # We know if license exists
                "has_contributing": False,
                "has_tests": False,
            }
        except Exception as e:
            logger.error(f"Error extracting basic data for repository {repo.name if hasattr(repo, 'name') else 'unknown'}: {e}")
            # Return absolute minimum data structure
            return {
                "id": getattr(repo, 'id', 0),
                "name": getattr(repo, 'name', 'unknown'),
                "full_name": getattr(repo, 'full_name', 'unknown'),
                "description": "",
                "language": None,
                "stargazers_count": 0,
                "forks_count": 0,
                "watchers_count": 0,
                "size": 0,
                "open_issues_count": 0,
                "created_at": None,
                "updated_at": None,
                "pushed_at": None,
                "fork": False,
                "private": False,
                "archived": False,
                "disabled": False,
                "is_template": False,
                "html_url": "",
                "clone_url": "",
                "homepage": "",
                "default_branch": "main",
                "license": None,
                "languages": {},
                "topics": [],
                "commit_count": 0,
                "contributor_count": 0,
                "has_readme": False,
                "has_license": False,
                "has_contributing": False,
                "has_tests": False,
            }
    
    async def _extract_repository_data_with_retry(
        self, 
        repo, 
        max_retries: int = 2
    ) -> Tuple[Dict[str, Any], bool, List[str]]:
        """
        Extract repository data with retry logic and exponential backoff.
        
        This method attempts to extract detailed repository data, with retry logic
        for transient errors like rate limits and network issues. If all retries fail,
        it falls back to basic repository data.
        
        Args:
            repo: GitHub repository object from PyGithub
            max_retries: Maximum number of retry attempts (default: 2)
            
        Returns:
            Tuple of (repo_data, has_complete_data, errors):
                - repo_data: Dictionary with repository information
                - has_complete_data: Boolean indicating if detailed data was successfully extracted
                - errors: List of error messages encountered during extraction
        """
        errors = []
        
        for attempt in range(max_retries + 1):
            try:
                # Attempt to extract detailed repository data
                detailed_data = await self._extract_repository_data(repo)
                
                # Success - return detailed data
                logger.debug(f"Successfully extracted detailed data for {repo.name} on attempt {attempt + 1}")
                return detailed_data, True, []
                
            except RateLimitExceededException as e:
                error_msg = f"Rate limit exceeded (attempt {attempt + 1}/{max_retries + 1})"
                logger.warning(f"{error_msg} for repository {repo.name}")
                errors.append(error_msg)
                
                # If we have retries left, wait with exponential backoff
                if attempt < max_retries:
                    # Exponential backoff: 60s, 120s, 300s (max)
                    wait_time = min(60 * (2 ** attempt), 300)
                    logger.info(f"Waiting {wait_time}s before retry for {repo.name}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # No more retries - fall back to basic data
                    logger.warning(f"Rate limit exceeded after {max_retries + 1} attempts for {repo.name}, using basic data")
                    break
                    
            except GithubException as e:
                # Classify the error
                if e.status in [403, 404]:
                    # Permission or not found errors - don't retry
                    error_msg = f"Access denied or not found: {e.status}"
                    logger.warning(f"{error_msg} for repository {repo.name}")
                    errors.append(error_msg)
                    break
                elif e.status >= 500:
                    # Server errors - retry with backoff
                    error_msg = f"GitHub server error: {e.status} (attempt {attempt + 1}/{max_retries + 1})"
                    logger.warning(f"{error_msg} for repository {repo.name}")
                    errors.append(error_msg)
                    
                    if attempt < max_retries:
                        wait_time = min(30 * (2 ** attempt), 120)  # Shorter backoff for server errors
                        logger.info(f"Waiting {wait_time}s before retry for {repo.name}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        break
                else:
                    # Other GitHub API errors - don't retry
                    error_msg = f"GitHub API error: {e.status} - {str(e)}"
                    logger.warning(f"{error_msg} for repository {repo.name}")
                    errors.append(error_msg)
                    break
                    
            except (ConnectionError, TimeoutError) as e:
                # Network errors - retry once
                error_msg = f"Network error: {type(e).__name__} (attempt {attempt + 1}/{max_retries + 1})"
                logger.warning(f"{error_msg} for repository {repo.name}")
                errors.append(error_msg)
                
                if attempt < max_retries:
                    wait_time = 30  # Fixed 30s wait for network errors
                    logger.info(f"Waiting {wait_time}s before retry for {repo.name}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break
                    
            except Exception as e:
                # Unexpected errors - don't retry
                error_msg = f"Unexpected error: {type(e).__name__} - {str(e)}"
                logger.error(f"{error_msg} for repository {repo.name}")
                errors.append(error_msg)
                break
        
        # All retries failed or non-retryable error - fall back to basic data
        logger.info(f"Falling back to basic data for {repo.name} due to errors: {errors}")
        basic_data = self._get_basic_repository_data(repo)
        return basic_data, False, errors
    
    def _classify_error_type(self, error_msg: str) -> str:
        """
        Classify error message into error type categories.
        
        Args:
            error_msg: Error message string
            
        Returns:
            Error type: 'rate_limit', 'permission', 'network', 'server_error', or 'unknown'
        """
        error_lower = error_msg.lower()
        
        if 'rate limit' in error_lower:
            return 'rate_limit'
        elif 'access denied' in error_lower or 'not found' in error_lower or '403' in error_msg or '404' in error_msg:
            return 'permission'
        elif 'network' in error_lower or 'connection' in error_lower or 'timeout' in error_lower:
            return 'network'
        elif 'server error' in error_lower or '500' in error_msg or '502' in error_msg or '503' in error_msg:
            return 'server_error'
        else:
            return 'unknown'
    
    def _create_error_summary(self, repo_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a summary of errors encountered during repository fetching.
        
        Args:
            repo_errors: List of error dictionaries with 'repository' and 'errors' keys
            
        Returns:
            Dictionary with error statistics and categorization
        """
        if not repo_errors:
            return {
                "total_errors": 0,
                "repositories_with_errors": 0,
                "error_types": {},
                "details": []
            }
        
        error_types = {
            'rate_limit': 0,
            'permission': 0,
            'network': 0,
            'server_error': 0,
            'unknown': 0
        }
        
        details = []
        
        for repo_error in repo_errors:
            repo_name = repo_error.get('repository', 'unknown')
            errors = repo_error.get('errors', [])
            
            for error_msg in errors:
                error_type = self._classify_error_type(error_msg)
                error_types[error_type] += 1
                
                details.append({
                    'repository': repo_name,
                    'error_type': error_type,
                    'message': error_msg
                })
        
        return {
            "total_errors": sum(error_types.values()),
            "repositories_with_errors": len(repo_errors),
            "error_types": error_types,
            "details": details[:10]  # Limit to first 10 for brevity
        }
    
    async def _extract_repository_data(self, repo) -> Dict[str, Any]:
        """Extract comprehensive data from a repository"""
        try:
            # Get language statistics
            languages = {}
            try:
                await self.rate_limiter.wait_if_needed()
                languages = repo.get_languages()
            except Exception as e:
                logger.warning(f"Could not fetch languages for {repo.name}: {e}")
            
            # Get topics
            topics = []
            try:
                await self.rate_limiter.wait_if_needed()
                topics = list(repo.get_topics())
            except Exception as e:
                logger.warning(f"Could not fetch topics for {repo.name}: {e}")
            
            # Get commit count (approximate)
            commit_count = 0
            try:
                await self.rate_limiter.wait_if_needed()
                commits = repo.get_commits()
                commit_count = commits.totalCount if hasattr(commits, 'totalCount') else 0
            except Exception as e:
                logger.warning(f"Could not fetch commit count for {repo.name}: {e}")
            
            # Get contributor count
            contributor_count = 0
            try:
                await self.rate_limiter.wait_if_needed()
                contributors = repo.get_contributors()
                contributor_count = contributors.totalCount if hasattr(contributors, 'totalCount') else 0
            except Exception as e:
                logger.warning(f"Could not fetch contributor count for {repo.name}: {e}")
            
            # Check for important files
            has_readme = self._check_file_exists(repo, ['README.md', 'README.rst', 'README.txt', 'readme.md'])
            has_license = self._check_file_exists(repo, ['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'license'])
            has_contributing = self._check_file_exists(repo, ['CONTRIBUTING.md', 'CONTRIBUTING.rst', 'contributing.md'])
            has_tests = self._check_directory_exists(repo, ['test', 'tests', '__tests__', 'spec'])
            
            repo_data = {
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description or "",
                "language": repo.language,
                "languages": languages,
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "watchers_count": repo.watchers_count,
                "size": repo.size,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "fork": repo.fork,
                "private": repo.private,
                "archived": repo.archived,
                "disabled": repo.disabled,
                "topics": topics,
                "license": {"name": repo.license.name, "key": repo.license.key} if repo.license else None,
                "default_branch": repo.default_branch,
                "clone_url": repo.clone_url,
                "html_url": repo.html_url,
                "homepage": repo.homepage,
                "open_issues_count": repo.open_issues_count,
                "commit_count": commit_count,
                "contributor_count": contributor_count,
                "has_readme": has_readme,
                "has_license": has_license,
                "has_contributing": has_contributing,
                "has_tests": has_tests,
                "is_template": repo.is_template if hasattr(repo, 'is_template') else False,
            }
            
            return repo_data
            
        except Exception as e:
            logger.error(f"Error extracting data for repository {repo.name}: {e}")
            # Return minimal data if detailed extraction fails
            return {
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description or "",
                "language": repo.language,
                "languages": {},
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "size": repo.size,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "fork": repo.fork,
                "private": repo.private,
                "topics": [],
                "license": None,
                "default_branch": repo.default_branch,
                "clone_url": repo.clone_url,
                "html_url": repo.html_url,
                "has_readme": False,
                "has_license": False,
                "has_contributing": False,
                "has_tests": False,
            }
    
    def _check_file_exists(self, repo, filenames: List[str]) -> bool:
        """Check if any of the specified files exist in the repository"""
        try:
            contents = repo.get_contents("")
            if not isinstance(contents, list):
                contents = [contents]
            
            existing_files = {content.name.lower() for content in contents if content.type == "file"}
            return any(filename.lower() in existing_files for filename in filenames)
        except:
            return False
    
    def _check_directory_exists(self, repo, dirnames: List[str]) -> bool:
        """Check if any of the specified directories exist in the repository"""
        try:
            contents = repo.get_contents("")
            if not isinstance(contents, list):
                contents = [contents]
            
            existing_dirs = {content.name.lower() for content in contents if content.type == "dir"}
            return any(dirname.lower() in existing_dirs for dirname in dirnames)
        except:
            return False
    
    async def get_repository_analysis(self, repo_full_name: str) -> Dict[str, Any]:
        """Get comprehensive analysis of a repository"""
        try:
            await self.rate_limiter.wait_if_needed()
            repo = self.github.get_repo(repo_full_name)
            
            analysis = {
                "basic_info": await self._extract_repository_data(repo),
                "code_metrics": await self._analyze_code_metrics(repo),
                "commit_analysis": await self._analyze_commit_history(repo),
                "collaboration_metrics": await self._analyze_collaboration(repo),
                "quality_indicators": await self._analyze_quality_indicators(repo)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing repository {repo_full_name}: {e}")
            raise Exception(f"Repository analysis failed: {e}")
    
    async def _analyze_code_metrics(self, repo) -> Dict[str, Any]:
        """Analyze code metrics for the repository"""
        try:
            metrics = {
                "total_files": 0,
                "code_files": 0,
                "total_lines": 0,
                "language_distribution": {},
                "file_types": defaultdict(int),
                "average_file_size": 0,
                "largest_files": [],
                "complexity_indicators": {}
            }
            
            # Get language statistics
            await self.rate_limiter.wait_if_needed()
            languages = repo.get_languages()
            total_bytes = sum(languages.values())
            
            if total_bytes > 0:
                metrics["language_distribution"] = {
                    lang: round((bytes_count / total_bytes) * 100, 2)
                    for lang, bytes_count in languages.items()
                }
            
            # Analyze repository structure (limited to avoid rate limits)
            try:
                await self.rate_limiter.wait_if_needed()
                contents = repo.get_contents("")
                if isinstance(contents, list):
                    for content in contents[:50]:  # Limit to first 50 items
                        if content.type == "file":
                            metrics["total_files"] += 1
                            file_ext = content.name.split('.')[-1].lower() if '.' in content.name else 'no_ext'
                            metrics["file_types"][file_ext] += 1
                            
                            if self._is_code_file(content.name):
                                metrics["code_files"] += 1
            except Exception as e:
                logger.warning(f"Could not analyze repository structure: {e}")
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Error analyzing code metrics: {e}")
            return {}
    
    async def _analyze_commit_history(self, repo, limit: int = 100) -> Dict[str, Any]:
        """Analyze commit history patterns"""
        try:
            await self.rate_limiter.wait_if_needed()
            commits = list(repo.get_commits()[:limit])
            
            if not commits:
                return {}
            
            analysis = {
                "total_commits": len(commits),
                "commit_frequency": {},
                "authors": defaultdict(int),
                "commit_times": defaultdict(int),
                "average_commit_size": 0,
                "recent_activity": []
            }
            
            total_additions = 0
            total_deletions = 0
            
            for commit in commits:
                try:
                    # Author analysis
                    if commit.author:
                        analysis["authors"][commit.author.login] += 1
                    
                    # Time analysis
                    commit_time = commit.commit.author.date
                    if commit_time:
                        hour = commit_time.hour
                        analysis["commit_times"][f"{hour:02d}:00"] += 1
                        
                        # Recent activity (last 30 days)
                        if (datetime.now() - commit_time.replace(tzinfo=None)).days <= 30:
                            analysis["recent_activity"].append({
                                "date": commit_time.isoformat(),
                                "message": commit.commit.message[:100],
                                "author": commit.author.login if commit.author else "Unknown"
                            })
                    
                    # Commit size analysis
                    if commit.stats:
                        total_additions += commit.stats.additions
                        total_deletions += commit.stats.deletions
                
                except Exception as e:
                    logger.warning(f"Error analyzing commit {commit.sha[:8]}: {e}")
                    continue
            
            if commits:
                analysis["average_commit_size"] = (total_additions + total_deletions) / len(commits)
            
            # Convert defaultdicts to regular dicts
            analysis["authors"] = dict(analysis["authors"])
            analysis["commit_times"] = dict(analysis["commit_times"])
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Error analyzing commit history: {e}")
            return {}
    
    async def _analyze_collaboration(self, repo) -> Dict[str, Any]:
        """Analyze collaboration metrics"""
        try:
            collaboration = {
                "contributors": 0,
                "forks": repo.forks_count,
                "stars": repo.stargazers_count,
                "watchers": repo.watchers_count,
                "open_issues": repo.open_issues_count,
                "has_discussions": False,
                "has_wiki": repo.has_wiki,
                "has_projects": repo.has_projects,
                "community_health": {}
            }
            
            # Get contributor count
            try:
                await self.rate_limiter.wait_if_needed()
                contributors = list(repo.get_contributors()[:100])
                collaboration["contributors"] = len(contributors)
            except Exception as e:
                logger.warning(f"Could not fetch contributors: {e}")
            
            # Check for community health files
            collaboration["community_health"] = {
                "has_readme": self._check_file_exists(repo, ['README.md', 'README.rst', 'readme.md']),
                "has_license": repo.license is not None,
                "has_contributing": self._check_file_exists(repo, ['CONTRIBUTING.md', 'contributing.md']),
                "has_code_of_conduct": self._check_file_exists(repo, ['CODE_OF_CONDUCT.md', 'code_of_conduct.md']),
                "has_issue_template": self._check_file_exists(repo, ['.github/ISSUE_TEMPLATE.md']),
                "has_pull_request_template": self._check_file_exists(repo, ['.github/PULL_REQUEST_TEMPLATE.md'])
            }
            
            return collaboration
            
        except Exception as e:
            logger.warning(f"Error analyzing collaboration metrics: {e}")
            return {}
    
    async def _analyze_quality_indicators(self, repo) -> Dict[str, Any]:
        """Analyze code quality indicators"""
        try:
            quality = {
                "has_tests": False,
                "has_ci": False,
                "has_documentation": False,
                "has_linting": False,
                "has_security": False,
                "dependency_management": {},
                "code_coverage": None,
                "security_alerts": 0
            }
            
            # Check for test directories/files
            quality["has_tests"] = (
                self._check_directory_exists(repo, ['test', 'tests', '__tests__', 'spec']) or
                self._check_file_exists(repo, ['test.py', 'test.js', 'test.ts', 'spec.py'])
            )
            
            # Check for CI/CD
            quality["has_ci"] = (
                self._check_directory_exists(repo, ['.github/workflows', '.gitlab-ci']) or
                self._check_file_exists(repo, ['.travis.yml', '.circleci/config.yml', 'Jenkinsfile', '.github/workflows'])
            )
            
            # Check for documentation
            quality["has_documentation"] = (
                self._check_directory_exists(repo, ['docs', 'documentation', 'doc']) or
                self._check_file_exists(repo, ['README.md', 'DOCUMENTATION.md'])
            )
            
            # Check for linting configuration
            quality["has_linting"] = self._check_file_exists(repo, [
                '.eslintrc', '.eslintrc.js', '.eslintrc.json',
                'pylint.cfg', '.pylintrc', 'setup.cfg',
                '.flake8', 'tox.ini', '.pre-commit-config.yaml'
            ])
            
            # Check for security files
            quality["has_security"] = self._check_file_exists(repo, [
                'SECURITY.md', '.github/SECURITY.md',
                'security.txt', '.well-known/security.txt'
            ])
            
            # Check dependency management
            quality["dependency_management"] = {
                "package_json": self._check_file_exists(repo, ['package.json']),
                "requirements_txt": self._check_file_exists(repo, ['requirements.txt']),
                "pipfile": self._check_file_exists(repo, ['Pipfile']),
                "poetry": self._check_file_exists(repo, ['pyproject.toml']),
                "gemfile": self._check_file_exists(repo, ['Gemfile']),
                "composer": self._check_file_exists(repo, ['composer.json']),
                "cargo": self._check_file_exists(repo, ['Cargo.toml']),
                "go_mod": self._check_file_exists(repo, ['go.mod'])
            }
            
            return quality
            
        except Exception as e:
            logger.warning(f"Error analyzing quality indicators: {e}")
            return {}

    async def fetch_repository_contents(self, repo_full_name: str, path: str = "") -> List[Dict[str, Any]]:
        """Fetch repository file contents for analysis"""
        try:
            repo = self.github.get_repo(repo_full_name)
            contents = []
            
            try:
                repo_contents = repo.get_contents(path)
                if not isinstance(repo_contents, list):
                    repo_contents = [repo_contents]
                
                for content in repo_contents:
                    if content.type == "file":
                        # Only analyze code files
                        if self._is_code_file(content.name):
                            file_content = ""
                            try:
                                if content.encoding == "base64":
                                    file_content = base64.b64decode(content.content).decode('utf-8', errors='ignore')
                                else:
                                    file_content = content.content
                            except:
                                continue  # Skip files that can't be decoded
                            
                            contents.append({
                                "name": content.name,
                                "path": content.path,
                                "size": content.size,
                                "content": file_content,
                                "sha": content.sha
                            })
                    
                    elif content.type == "dir" and not self._should_skip_directory(content.name):
                        # Recursively get directory contents (limit depth)
                        if path.count('/') < 3:  # Limit recursion depth
                            dir_contents = await self.fetch_repository_contents(repo_full_name, content.path)
                            contents.extend(dir_contents)
            
            except GithubException:
                pass  # Skip if can't access contents
            
            return contents
            
        except Exception as e:
            raise Exception(f"Error fetching repository contents: {e}")
    
    def _is_code_file(self, filename: str) -> bool:
        """Check if file is a code file worth analyzing"""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
            '.html', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
            '.sql', '.sh', '.bash', '.ps1', '.yaml', '.yml', '.json', '.xml'
        }
        
        _, ext = filename.rsplit('.', 1) if '.' in filename else ('', '')
        return f'.{ext.lower()}' in code_extensions
    
    def _should_skip_directory(self, dirname: str) -> bool:
        """Check if directory should be skipped"""
        skip_dirs = {
            'node_modules', '.git', '.vscode', '.idea', '__pycache__',
            'venv', 'env', '.env', 'dist', 'build', 'target', 'bin',
            '.next', '.nuxt', 'coverage', '.coverage', 'logs'
        }
        return dirname.lower() in skip_dirs
    
    async def get_commit_history(self, repo_full_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent commit history for analysis with enhanced error handling"""
        try:
            await self.rate_limiter.wait_if_needed()
            repo = self.github.get_repo(repo_full_name)
            commits = []
            
            for commit in repo.get_commits()[:limit]:
                try:
                    commits.append({
                        "sha": commit.sha,
                        "message": commit.commit.message,
                        "author": commit.commit.author.name if commit.commit.author else "Unknown",
                        "author_email": commit.commit.author.email if commit.commit.author else None,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author else None,
                        "additions": commit.stats.additions if commit.stats else 0,
                        "deletions": commit.stats.deletions if commit.stats else 0,
                        "total": commit.stats.total if commit.stats else 0,
                        "url": commit.html_url,
                        "verified": commit.commit.verification.verified if hasattr(commit.commit, 'verification') else False
                    })
                except Exception as e:
                    logger.warning(f"Error processing commit {commit.sha[:8]}: {e}")
                    continue
            
            return commits
            
        except GithubException as e:
            if e.status == 403:
                logger.warning(f"Repository '{repo_full_name}' is private or access denied")
            elif e.status == 404:
                logger.warning(f"Repository '{repo_full_name}' not found")
            else:
                logger.warning(f"GitHub API error for repository {repo_full_name}: {e}")
            return []
        except Exception as e:
            logger.warning(f"Error fetching commit history for {repo_full_name}: {e}")
            return []
    
    async def get_pull_requests_analysis(self, repo_full_name: str, limit: int = 50) -> Dict[str, Any]:
        """Get detailed pull request analysis for a repository"""
        try:
            await self.rate_limiter.wait_if_needed()
            repo = self.github.get_repo(repo_full_name)
            
            # Get pull requests (all states)
            prs = list(repo.get_pulls(state='all', sort='updated', direction='desc')[:limit])
            
            analysis = {
                "total_prs": len(prs),
                "open_prs": len([pr for pr in prs if pr.state == 'open']),
                "closed_prs": len([pr for pr in prs if pr.state == 'closed']),
                "merged_prs": len([pr for pr in prs if pr.merged]),
                "recent_prs": [],
                "pr_authors": defaultdict(int),
                "average_merge_time": 0,
                "review_participation": {}
            }
            
            merge_times = []
            
            for pr in prs[:20]:  # Detailed analysis for recent 20 PRs
                try:
                    pr_data = {
                        "number": pr.number,
                        "title": pr.title,
                        "state": pr.state,
                        "created_at": pr.created_at.isoformat(),
                        "updated_at": pr.updated_at.isoformat(),
                        "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                        "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                        "merged": pr.merged,
                        "author": pr.user.login if pr.user else None,
                        "base_ref": pr.base.ref,
                        "head_ref": pr.head.ref,
                        "additions": pr.additions,
                        "deletions": pr.deletions,
                        "changed_files": pr.changed_files,
                        "html_url": pr.html_url
                    }
                    
                    # Count author contributions
                    if pr.user:
                        analysis["pr_authors"][pr.user.login] += 1
                    
                    # Calculate merge time
                    if pr.merged and pr.created_at and pr.merged_at:
                        merge_time = (pr.merged_at - pr.created_at).total_seconds() / 3600  # hours
                        merge_times.append(merge_time)
                    
                    analysis["recent_prs"].append(pr_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing PR #{pr.number}: {e}")
                    continue
            
            # Calculate average merge time
            if merge_times:
                analysis["average_merge_time"] = round(sum(merge_times) / len(merge_times), 2)
            
            # Convert defaultdict to regular dict
            analysis["pr_authors"] = dict(analysis["pr_authors"])
            
            return analysis
            
        except GithubException as e:
            if e.status == 403:
                logger.warning(f"Repository '{repo_full_name}' is private or access denied")
                return {"error": "Repository is private or access denied"}
            elif e.status == 404:
                logger.warning(f"Repository '{repo_full_name}' not found")
                return {"error": "Repository not found"}
            else:
                logger.warning(f"GitHub API error for repository {repo_full_name}: {e}")
                return {"error": f"GitHub API error: {e}"}
        except Exception as e:
            logger.warning(f"Error analyzing pull requests for {repo_full_name}: {e}")
            return {"error": str(e)}
    
    async def get_issues_analysis(self, repo_full_name: str, limit: int = 50) -> Dict[str, Any]:
        """Get detailed issues analysis for a repository"""
        try:
            await self.rate_limiter.wait_if_needed()
            repo = self.github.get_repo(repo_full_name)
            
            # Get issues (excluding pull requests)
            issues = []
            for issue in repo.get_issues(state='all', sort='updated', direction='desc'):
                if not issue.pull_request:  # Exclude PRs
                    issues.append(issue)
                if len(issues) >= limit:
                    break
            
            analysis = {
                "total_issues": len(issues),
                "open_issues": len([issue for issue in issues if issue.state == 'open']),
                "closed_issues": len([issue for issue in issues if issue.state == 'closed']),
                "recent_issues": [],
                "issue_authors": defaultdict(int),
                "label_usage": defaultdict(int),
                "average_resolution_time": 0
            }
            
            resolution_times = []
            
            for issue in issues[:20]:  # Detailed analysis for recent 20 issues
                try:
                    issue_data = {
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "created_at": issue.created_at.isoformat(),
                        "updated_at": issue.updated_at.isoformat(),
                        "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                        "author": issue.user.login if issue.user else None,
                        "labels": [label.name for label in issue.labels],
                        "assignees": [assignee.login for assignee in issue.assignees],
                        "comments": issue.comments,
                        "html_url": issue.html_url
                    }
                    
                    # Count author contributions
                    if issue.user:
                        analysis["issue_authors"][issue.user.login] += 1
                    
                    # Count label usage
                    for label in issue.labels:
                        analysis["label_usage"][label.name] += 1
                    
                    # Calculate resolution time
                    if issue.state == 'closed' and issue.created_at and issue.closed_at:
                        resolution_time = (issue.closed_at - issue.created_at).total_seconds() / 3600  # hours
                        resolution_times.append(resolution_time)
                    
                    analysis["recent_issues"].append(issue_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing issue #{issue.number}: {e}")
                    continue
            
            # Calculate average resolution time
            if resolution_times:
                analysis["average_resolution_time"] = round(sum(resolution_times) / len(resolution_times), 2)
            
            # Convert defaultdicts to regular dicts
            analysis["issue_authors"] = dict(analysis["issue_authors"])
            analysis["label_usage"] = dict(analysis["label_usage"])
            
            return analysis
            
        except GithubException as e:
            if e.status == 403:
                logger.warning(f"Repository '{repo_full_name}' is private or access denied")
                return {"error": "Repository is private or access denied"}
            elif e.status == 404:
                logger.warning(f"Repository '{repo_full_name}' not found")
                return {"error": "Repository not found"}
            else:
                logger.warning(f"GitHub API error for repository {repo_full_name}: {e}")
                return {"error": f"GitHub API error: {e}"}
        except Exception as e:
            logger.warning(f"Error analyzing issues for {repo_full_name}: {e}")
            return {"error": str(e)}
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current GitHub API rate limit status"""
        try:
            rate_limit = self.github.get_rate_limit()
            return {
                "core": {
                    "limit": rate_limit.core.limit,
                    "remaining": rate_limit.core.remaining,
                    "reset": rate_limit.core.reset.isoformat(),
                    "used": rate_limit.core.used
                },
                "search": {
                    "limit": rate_limit.search.limit,
                    "remaining": rate_limit.search.remaining,
                    "reset": rate_limit.search.reset.isoformat(),
                    "used": rate_limit.search.used
                }
            }
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {}
    
    async def search_repositories(self, query: str, sort: str = "stars", order: str = "desc", limit: int = 30) -> List[Dict[str, Any]]:
        """Search for repositories using GitHub search API"""
        try:
            await self.rate_limiter.wait_if_needed()
            
            # Use GitHub search API
            repositories = self.github.search_repositories(
                query=query,
                sort=sort,
                order=order
            )
            
            results = []
            count = 0
            
            for repo in repositories:
                if count >= limit:
                    break
                
                try:
                    repo_data = await self._extract_repository_data(repo)
                    results.append(repo_data)
                    count += 1
                except Exception as e:
                    logger.warning(f"Error processing search result {repo.name}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching repositories: {e}")
            raise Exception(f"Repository search failed: {e}")
    
    async def validate_github_url(self, url: str) -> Tuple[bool, str, str]:
        """Validate and parse GitHub URL with enhanced pattern support"""
        try:
            # GitHub URL patterns
            patterns = [
                r'https://github\.com/([^/]+)/([^/]+)/?',
                r'https://github\.com/([^/]+)/?$',
                r'github\.com/([^/]+)/([^/]+)/?',
                r'github\.com/([^/]+)/?$',
                r'^([^/]+)/([^/]+)$',
                r'^([^/]+)$'
            ]
            
            for pattern in patterns:
                match = re.match(pattern, url.strip())
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        return True, groups[0], groups[1]  # username, repo
                    elif len(groups) == 1:
                        return True, groups[0], ""  # username only
            
            return False, "", ""
            
        except Exception as e:
            logger.error(f"Error validating GitHub URL: {e}")
            return False, "", ""
    
    async def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get detailed information about a GitHub user with enhanced error handling"""
        try:
            await self.rate_limiter.wait_if_needed()
            user = self.github.get_user(username)
            
            user_info = {
                "login": user.login,
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "bio": user.bio,
                "company": user.company,
                "location": user.location,
                "blog": user.blog,
                "twitter_username": user.twitter_username,
                "public_repos": user.public_repos,
                "public_gists": user.public_gists,
                "followers": user.followers,
                "following": user.following,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
                "avatar_url": user.avatar_url,
                "html_url": user.html_url,
                "type": user.type,
                "site_admin": user.site_admin,
                "hireable": user.hireable
            }
            
            return user_info
            
        except GithubException as e:
            github_error = self.error_handler.classify_github_exception(e)
            logger.error(f"GitHub API error for user {username}: {github_error.user_friendly_message}")
            raise Exception(github_error.user_friendly_message)
        except Exception as e:
            if "network" in str(e).lower() or "connection" in str(e).lower():
                network_error = self.error_handler.handle_network_error(e)
                raise Exception(network_error.user_friendly_message)
            else:
                logger.error(f"Error getting user info for {username}: {e}")
                raise Exception(f"Failed to get user information: {str(e)}")
    
    async def analyze_repository_structure(self, repo_full_name: str) -> Dict[str, Any]:
        """Analyze repository structure and patterns"""
        try:
            repo = self.github.get_repo(repo_full_name)
            
            # Check for important files
            important_files = {
                'README.md': False,
                'LICENSE': False,
                'package.json': False,
                'requirements.txt': False,
                'Dockerfile': False,
                '.gitignore': False,
                'tests': False,
                'test': False
            }
            
            try:
                contents = repo.get_contents("")
                for content in contents:
                    if content.name in important_files:
                        important_files[content.name] = True
                    elif content.type == "dir" and content.name.lower() in ['tests', 'test', '__tests__']:
                        important_files['tests'] = True
            except:
                pass
            
            # Get repository statistics
            stats = {
                "has_readme": important_files.get('README.md', False),
                "has_license": important_files.get('LICENSE', False),
                "has_package_json": important_files.get('package.json', False),
                "has_requirements": important_files.get('requirements.txt', False),
                "has_dockerfile": important_files.get('Dockerfile', False),
                "has_gitignore": important_files.get('.gitignore', False),
                "has_tests": important_files.get('tests', False),
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "issues": repo.open_issues_count,
                "size": repo.size,
                "language": repo.language,
                "topics": list(repo.get_topics())
            }
            
            return stats
            
        except Exception as e:
            return {}
    
    async def trigger_ranking_sync_after_scan(
        self, 
        user_id: str, 
        scan_type: str,
        db: Any = None
    ) -> None:
        """
        Trigger ranking synchronization after scan completion
        
        Only triggers for internal scans where user is scanning their own repos.
        Checks if user has profile before triggering sync.
        
        Args:
            user_id: User identifier
            scan_type: Type of scan ('self', 'internal', 'myself', 'external', etc.)
            db: Database connection (optional, will get if not provided)
        """
        try:
            # Only trigger for internal scans
            if scan_type not in ['self', 'internal', 'myself']:
                logger.info(f"Skipping ranking sync for scan_type: {scan_type}")
                return
            
            logger.info(f"🎯 Triggering ranking sync for user: {user_id}")
            
            # Get database connection if not provided
            if db is None:
                from app.database import get_database
                db = await get_database()
            
            if db is None:
                logger.warning("Database connection unavailable, skipping ranking sync")
                return
            
            # Check if user has profile
            profile = await db.user_profiles.find_one({"user_id": user_id})
            
            if not profile:
                logger.info(f"User {user_id} has no profile, skipping ranking sync")
                return
            
            # Import ranking services
            from app.services.ranking_service import RankingService
            from app.services.score_sync_service import ScoreSyncService
            
            # Trigger score sync
            ranking_service = RankingService(db)
            sync_service = ScoreSyncService(db, ranking_service)
            
            result = await sync_service.sync_user_score(user_id)
            
            if result["success"]:
                logger.info(f"✅ Rankings synced successfully for user {user_id}")
                logger.info(f"   - Regional updated: {result.get('regional_updated', False)}")
                logger.info(f"   - University updated: {result.get('university_updated', False)}")
                logger.info(f"   - ACID Score: {result.get('acid_score', 0)}")
            else:
                logger.warning(f"⚠️ Ranking sync failed for user {user_id}: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"❌ Error triggering ranking sync for user {user_id}: {e}")
            # Don't raise exception - ranking sync failure shouldn't block scan completion
