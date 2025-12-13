"""
GitHub API Service for Vercel Serverless Environment
Handles token management, rate limiting, and API interactions optimized for serverless
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
import httpx
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class GitHubAPIService:
    """Serverless-optimized GitHub API service with comprehensive error handling"""
    
    def __init__(self, access_token: str, cache_service=None):
        self.access_token = access_token
        self.base_url = "https://api.github.com"
        self.timeout = 30.0  # 30 second timeout for serverless
        self.max_retries = 3
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.cache_service = cache_service
        
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to GitHub API with retry logic"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BroskiesHub/1.0"
        }
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, headers=headers, params=params)
                    elif method.upper() == "POST":
                        response = await client.post(url, headers=headers, json=data)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    
                    # Update rate limit info
                    self._update_rate_limit_info(response.headers)
                    
                    # Handle rate limiting
                    if response.status_code == 403 and "rate limit" in response.text.lower():
                        if attempt < self.max_retries - 1:
                            wait_time = self._calculate_wait_time()
                            logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail="GitHub API rate limit exceeded"
                            )
                    
                    # Handle other errors
                    if response.status_code == 401:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="GitHub token is invalid or expired"
                        )
                    elif response.status_code == 404:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="GitHub resource not found"
                        )
                    elif response.status_code >= 500:
                        if attempt < self.max_retries - 1:
                            wait_time = 2 ** attempt  # Exponential backoff
                            logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_502_BAD_GATEWAY,
                                detail="GitHub API server error"
                            )
                    elif response.status_code >= 400:
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"GitHub API error: {response.text}"
                        )
                    
                    return response.json()
                    
            except httpx.TimeoutException:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request timeout, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise HTTPException(
                        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                        detail="GitHub API request timeout"
                    )
            except httpx.RequestError as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request error: {e}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"GitHub API connection error: {str(e)}"
                    )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete GitHub API request after retries"
        )
    
    def _update_rate_limit_info(self, headers: Dict[str, str]):
        """Update rate limit information from response headers"""
        try:
            if 'X-RateLimit-Remaining' in headers:
                self.rate_limit_remaining = int(headers['X-RateLimit-Remaining'])
            if 'X-RateLimit-Reset' in headers:
                self.rate_limit_reset = int(headers['X-RateLimit-Reset'])
                
            logger.debug(f"Rate limit: {self.rate_limit_remaining} remaining, resets at {self.rate_limit_reset}")
        except (ValueError, KeyError) as e:
            logger.warning(f"Could not parse rate limit headers: {e}")
    
    def _calculate_wait_time(self) -> int:
        """Calculate wait time for rate limit"""
        if self.rate_limit_reset:
            wait_time = max(self.rate_limit_reset - int(time.time()), 60)
            return min(wait_time, 300)  # Max 5 minutes for serverless
        return 60  # Default 1 minute
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information"""
        return await self._make_request("GET", "/user")
    
    async def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """Get user information by username"""
        return await self._make_request("GET", f"/users/{username}")
    
    async def get_user_repositories(self, username: str, per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """Get user's public repositories"""
        params = {
            "type": "public",
            "sort": "updated",
            "direction": "desc",
            "per_page": min(per_page, 100),
            "page": page
        }
        return await self._make_request("GET", f"/users/{username}/repos", params=params)
    
    async def get_all_user_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Get ALL user's public repositories with pagination"""
        all_repos = []
        page = 1
        per_page = 100
        
        while True:
            repos = await self.get_user_repositories(username, per_page=per_page, page=page)
            if not repos:
                break
            
            all_repos.extend(repos)
            
            # If we got less than per_page, we've reached the end
            if len(repos) < per_page:
                break
            
            page += 1
        
        return all_repos
    
    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information"""
        return await self._make_request("GET", f"/repos/{owner}/{repo}")
    
    async def get_repository_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get repository languages"""
        return await self._make_request("GET", f"/repos/{owner}/{repo}/languages")
    
    async def get_repository_topics(self, owner: str, repo: str) -> List[str]:
        """Get repository topics"""
        result = await self._make_request("GET", f"/repos/{owner}/{repo}/topics")
        return result.get("names", [])
    
    async def get_repository_commits(self, owner: str, repo: str, per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """Get repository commits"""
        params = {
            "per_page": min(per_page, 100),
            "page": page
        }
        return await self._make_request("GET", f"/repos/{owner}/{repo}/commits", params=params)
    
    async def get_repository_contributors(self, owner: str, repo: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get repository contributors"""
        params = {"per_page": min(per_page, 100)}
        return await self._make_request("GET", f"/repos/{owner}/{repo}/contributors", params=params)
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        return await self._make_request("GET", "/rate_limit")
    
    async def validate_token(self) -> bool:
        """Validate the current access token"""
        try:
            await self.get_user_info()
            return True
        except HTTPException as e:
            if e.status_code == 401:
                return False
            raise
    
    def get_current_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information"""
        return {
            "remaining": self.rate_limit_remaining,
            "reset_timestamp": self.rate_limit_reset,
            "reset_time": time.ctime(self.rate_limit_reset) if self.rate_limit_reset else None
        }
  
  # Enhanced methods for PR/Issue/Roadmap fetching (Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.3)
    
    async def get_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        per_page: int = 30,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Fetch pull requests for a repository with state filtering.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state filter ('open', 'closed', 'all')
            per_page: Number of PRs per page (max 100)
            page: Page number
            
        Returns:
            List of pull request data
            
        Requirements: 2.1, 6.1
        """
        # Check cache first
        cache_key = f"{owner}/{repo}:prs:{state}:{page}"
        if self.cache_service:
            cached_prs = await self.cache_service.get(cache_key, prefix="github_prs")
            if cached_prs:
                logger.debug(f"Retrieved PRs from cache: {cache_key}")
                return cached_prs
        
        params = {
            "state": state,
            "per_page": min(per_page, 100),
            "page": page,
            "sort": "updated",
            "direction": "desc"
        }
        
        prs = await self._make_request("GET", f"/repos/{owner}/{repo}/pulls", params=params)
        
        # Cache the results (30 minutes TTL)
        if self.cache_service and prs:
            await self.cache_service.set(cache_key, prs, prefix="github_prs", ttl=1800)
        
        return prs
    
    async def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        per_page: int = 30,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Fetch issues for a repository (excluding PRs).
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state filter ('open', 'closed', 'all')
            per_page: Number of issues per page (max 100)
            page: Page number
            
        Returns:
            List of issue data (PRs excluded)
            
        Requirements: 2.2, 6.2
        """
        # Check cache first
        cache_key = f"{owner}/{repo}:issues:{state}:{page}"
        if self.cache_service:
            cached_issues = await self.cache_service.get(cache_key, prefix="github_issues")
            if cached_issues:
                logger.debug(f"Retrieved issues from cache: {cache_key}")
                return cached_issues
        
        params = {
            "state": state,
            "per_page": min(per_page, 100),
            "page": page,
            "sort": "updated",
            "direction": "desc"
        }
        
        issues = await self._make_request("GET", f"/repos/{owner}/{repo}/issues", params=params)
        
        # Filter out PRs (GitHub API returns PRs as issues)
        filtered_issues = [issue for issue in issues if "pull_request" not in issue]
        
        # Cache the results (30 minutes TTL)
        if self.cache_service and filtered_issues:
            await self.cache_service.set(cache_key, filtered_issues, prefix="github_issues", ttl=1800)
        
        return filtered_issues
    
    async def get_milestones(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch milestones for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Milestone state filter ('open', 'closed', 'all')
            per_page: Number of milestones per page (max 100)
            
        Returns:
            List of milestone data
            
        Requirements: 2.3, 6.3
        """
        # Check cache first
        cache_key = f"{owner}/{repo}:milestones:{state}"
        if self.cache_service:
            cached_milestones = await self.cache_service.get(cache_key, prefix="github_milestones")
            if cached_milestones:
                logger.debug(f"Retrieved milestones from cache: {cache_key}")
                return cached_milestones
        
        params = {
            "state": state,
            "per_page": min(per_page, 100),
            "sort": "due_on",
            "direction": "asc"
        }
        
        milestones = await self._make_request("GET", f"/repos/{owner}/{repo}/milestones", params=params)
        
        # Cache the results (1 hour TTL)
        if self.cache_service and milestones:
            await self.cache_service.set(cache_key, milestones, prefix="github_milestones", ttl=3600)
        
        return milestones
    
    async def get_projects(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch projects for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Project state filter ('open', 'closed', 'all')
            per_page: Number of projects per page (max 100)
            
        Returns:
            List of project data
            
        Requirements: 2.3, 6.3
        """
        # Check cache first
        cache_key = f"{owner}/{repo}:projects:{state}"
        if self.cache_service:
            cached_projects = await self.cache_service.get(cache_key, prefix="github_projects")
            if cached_projects:
                logger.debug(f"Retrieved projects from cache: {cache_key}")
                return cached_projects
        
        params = {
            "state": state,
            "per_page": min(per_page, 100)
        }
        
        # Note: Projects API requires special accept header
        headers = {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.inertia-preview+json",
            "User-Agent": "BroskiesHub/1.0"
        }
        
        url = f"{self.base_url}/repos/{owner}/{repo}/projects"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)
                
                # Update rate limit info
                self._update_rate_limit_info(response.headers)
                
                if response.status_code == 404:
                    # Projects might not be enabled for this repo
                    logger.debug(f"Projects not available for {owner}/{repo}")
                    return []
                
                response.raise_for_status()
                projects = response.json()
                
                # Cache the results (1 hour TTL)
                if self.cache_service and projects:
                    await self.cache_service.set(cache_key, projects, prefix="github_projects", ttl=3600)
                
                return projects
                
        except Exception as e:
            logger.warning(f"Error fetching projects for {owner}/{repo}: {e}")
            return []
    
    async def get_pr_issue_counts(
        self,
        owner: str,
        repo: str
    ) -> Dict[str, Any]:
        """
        Get PR and issue counts for a repository (optimized with caching).
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with PR and issue counts
            
        Requirements: 2.1, 2.2, 6.1, 6.2
        """
        # Check cache first (longer TTL for counts)
        cache_key = f"{owner}/{repo}:counts"
        if self.cache_service:
            cached_counts = await self.cache_service.get(cache_key, prefix="github_counts")
            if cached_counts:
                logger.debug(f"Retrieved PR/issue counts from cache: {cache_key}")
                return cached_counts
        
        # Fetch first page to get counts from headers/data
        prs_open = await self.get_pull_requests(owner, repo, state="open", per_page=1)
        prs_closed = await self.get_pull_requests(owner, repo, state="closed", per_page=1)
        issues_open = await self.get_issues(owner, repo, state="open", per_page=1)
        issues_closed = await self.get_issues(owner, repo, state="closed", per_page=1)
        
        # Get repository data for total counts
        repo_data = await self.get_repository(owner, repo)
        
        counts = {
            "pull_requests": {
                "total": repo_data.get("open_issues_count", 0),  # This includes PRs
                "open": len(prs_open) if prs_open else 0,
                "closed": len(prs_closed) if prs_closed else 0
            },
            "issues": {
                "total": repo_data.get("open_issues_count", 0),
                "open": len(issues_open) if issues_open else 0,
                "closed": len(issues_closed) if issues_closed else 0
            }
        }
        
        # Cache the results (2 hours TTL)
        if self.cache_service:
            await self.cache_service.set(cache_key, counts, prefix="github_counts", ttl=7200)
        
        return counts
    
    async def get_repository_with_details(
        self,
        owner: str,
        repo: str,
        include_prs: bool = True,
        include_issues: bool = True,
        include_roadmap: bool = True,
        pr_limit: int = 10,
        issue_limit: int = 10
    ) -> Dict[str, Any]:
        """
        Fetch repository with comprehensive details including PRs, issues, and roadmap.
        
        Args:
            owner: Repository owner
            repo: Repository name
            include_prs: Whether to include PR data
            include_issues: Whether to include issue data
            include_roadmap: Whether to include roadmap data
            pr_limit: Number of recent PRs to fetch
            issue_limit: Number of recent issues to fetch
            
        Returns:
            Repository data with enhanced details
            
        Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.3
        """
        # Fetch basic repository info
        repo_data = await self.get_repository(owner, repo)
        
        # Fetch PRs if requested
        if include_prs:
            try:
                prs_all = await self.get_pull_requests(owner, repo, state="all", per_page=pr_limit)
                
                # Process PR data
                prs_open = [pr for pr in prs_all if pr.get("state") == "open"]
                prs_closed = [pr for pr in prs_all if pr.get("state") == "closed"]
                prs_merged = [pr for pr in prs_closed if pr.get("merged_at")]
                
                repo_data["pullRequests"] = {
                    "total": len(prs_all),
                    "open": len(prs_open),
                    "closed": len(prs_closed),
                    "merged": len(prs_merged),
                    "recent": [
                        {
                            "number": pr.get("number"),
                            "title": pr.get("title"),
                            "author": pr.get("user", {}).get("login"),
                            "state": pr.get("state"),
                            "createdAt": pr.get("created_at"),
                            "mergedAt": pr.get("merged_at"),
                            "url": pr.get("html_url")
                        }
                        for pr in prs_all[:pr_limit]
                    ]
                }
            except Exception as e:
                logger.warning(f"Error fetching PRs for {owner}/{repo}: {e}")
                repo_data["pullRequests"] = {"total": 0, "open": 0, "closed": 0, "merged": 0, "recent": []}
        
        # Fetch issues if requested
        if include_issues:
            try:
                issues_all = await self.get_issues(owner, repo, state="all", per_page=issue_limit)
                
                # Process issue data
                issues_open = [issue for issue in issues_all if issue.get("state") == "open"]
                issues_closed = [issue for issue in issues_all if issue.get("state") == "closed"]
                
                repo_data["issues"] = {
                    "total": len(issues_all),
                    "open": len(issues_open),
                    "closed": len(issues_closed),
                    "recent": [
                        {
                            "number": issue.get("number"),
                            "title": issue.get("title"),
                            "author": issue.get("user", {}).get("login"),
                            "state": issue.get("state"),
                            "labels": [label.get("name") for label in issue.get("labels", [])],
                            "createdAt": issue.get("created_at"),
                            "closedAt": issue.get("closed_at"),
                            "url": issue.get("html_url")
                        }
                        for issue in issues_all[:issue_limit]
                    ]
                }
            except Exception as e:
                logger.warning(f"Error fetching issues for {owner}/{repo}: {e}")
                repo_data["issues"] = {"total": 0, "open": 0, "closed": 0, "recent": []}
        
        # Fetch roadmap data if requested
        if include_roadmap:
            try:
                milestones = await self.get_milestones(owner, repo, state="all")
                projects = await self.get_projects(owner, repo, state="all")
                
                # Process milestone data
                processed_milestones = []
                for milestone in milestones:
                    total_issues = milestone.get("open_issues", 0) + milestone.get("closed_issues", 0)
                    progress = (milestone.get("closed_issues", 0) / max(total_issues, 1)) * 100
                    
                    processed_milestones.append({
                        "title": milestone.get("title"),
                        "description": milestone.get("description"),
                        "dueDate": milestone.get("due_on"),
                        "state": milestone.get("state"),
                        "progress": round(progress, 2),
                        "openIssues": milestone.get("open_issues", 0),
                        "closedIssues": milestone.get("closed_issues", 0)
                    })
                
                # Process project data
                processed_projects = []
                for project in projects:
                    processed_projects.append({
                        "name": project.get("name"),
                        "description": project.get("body"),
                        "state": project.get("state"),
                        "progress": 0  # Projects don't have built-in progress
                    })
                
                repo_data["roadmap"] = {
                    "milestones": processed_milestones,
                    "projects": processed_projects
                }
            except Exception as e:
                logger.warning(f"Error fetching roadmap for {owner}/{repo}: {e}")
                repo_data["roadmap"] = {"milestones": [], "projects": []}
        
        return repo_data
    
    async def invalidate_repo_cache(self, owner: str, repo: str):
        """
        Invalidate all cached data for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        if not self.cache_service:
            return
        
        cache_prefixes = ["github_prs", "github_issues", "github_milestones", "github_projects", "github_counts"]
        repo_key = f"{owner}/{repo}"
        
        for prefix in cache_prefixes:
            # Delete all variations of cached data
            await self.cache_service.delete(f"{repo_key}:prs:all:1", prefix=prefix)
            await self.cache_service.delete(f"{repo_key}:prs:open:1", prefix=prefix)
            await self.cache_service.delete(f"{repo_key}:prs:closed:1", prefix=prefix)
            await self.cache_service.delete(f"{repo_key}:issues:all:1", prefix=prefix)
            await self.cache_service.delete(f"{repo_key}:issues:open:1", prefix=prefix)
            await self.cache_service.delete(f"{repo_key}:issues:closed:1", prefix=prefix)
            await self.cache_service.delete(f"{repo_key}:milestones:all", prefix=prefix)
            await self.cache_service.delete(f"{repo_key}:projects:all", prefix=prefix)
            await self.cache_service.delete(f"{repo_key}:counts", prefix=prefix)
        
        logger.info(f"Invalidated cache for repository: {owner}/{repo}")
