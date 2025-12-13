"""
Comprehensive GitHub Scanner Service

This service provides detailed GitHub data extraction including:
- User profile with comprehensive stats
- Repository analysis with pull requests, issues, commits
- Contribution calendar and activity patterns
- Language and technology analysis
- Collaboration metrics
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from github import Github, GithubException
import requests
import json

from .github_graphql_client import GitHubGraphQLClient
from .pull_request_analyzer import PullRequestAnalyzer
from .issue_analyzer import IssueAnalyzer
from .performance_service import performance_service
from .concurrent_data_fetcher import concurrent_fetcher, RequestPriority
from .connection_pool_manager import connection_pool_manager

logger = logging.getLogger(__name__)

class GitHubComprehensiveScanner:
    """Enhanced GitHub scanner for comprehensive data extraction with concurrent processing"""
    
    def __init__(self, github_token: str):
        self.github = Github(github_token, per_page=100)
        self.token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.graphql_client = GitHubGraphQLClient(github_token)
        self.pr_analyzer = PullRequestAnalyzer(github_token)
        self.issue_analyzer = IssueAnalyzer(github_token)
        self.user = None
        
        # Resource management settings
        self.max_concurrent_repos = 5
        self.max_concurrent_requests = 10
        self.rate_limit_buffer = 100  # Keep buffer of requests
        
        self._initialize_user()
    
    def _initialize_user(self):
        """Initialize the authenticated user"""
        try:
            self.user = self.github.get_user()
            logger.info(f"Initialized comprehensive GitHub scanner for user: {self.user.login}")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub user: {e}")
            raise
    
    async def check_rate_limits(self) -> Dict[str, Any]:
        """Check current GitHub API rate limits"""
        try:
            rate_limit = self.github.get_rate_limit()
            
            # Handle different PyGithub versions
            if hasattr(rate_limit, 'core'):
                # Newer PyGithub version
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
                    },
                    "graphql": {
                        "limit": rate_limit.graphql.limit,
                        "remaining": rate_limit.graphql.remaining,
                        "reset": rate_limit.graphql.reset.isoformat(),
                        "used": rate_limit.graphql.used
                    }
                }
            else:
                # Older PyGithub version or different structure
                return {
                    "core": {
                        "limit": getattr(rate_limit, 'limit', 5000),
                        "remaining": getattr(rate_limit, 'remaining', 5000),
                        "reset": getattr(rate_limit, 'reset', datetime.now()).isoformat() if hasattr(getattr(rate_limit, 'reset', None), 'isoformat') else datetime.now().isoformat(),
                        "used": getattr(rate_limit, 'used', 0)
                    },
                    "search": {
                        "limit": 30,
                        "remaining": 30,
                        "reset": datetime.now().isoformat(),
                        "used": 0
                    },
                    "graphql": {
                        "limit": 5000,
                        "remaining": 5000,
                        "reset": datetime.now().isoformat(),
                        "used": 0
                    }
                }
        except Exception as e:
            logger.error(f"Error checking rate limits: {e}")
            # Return safe defaults
            return {
                "core": {
                    "limit": 5000,
                    "remaining": 5000,
                    "reset": datetime.now().isoformat(),
                    "used": 0
                },
                "search": {
                    "limit": 30,
                    "remaining": 30,
                    "reset": datetime.now().isoformat(),
                    "used": 0
                },
                "graphql": {
                    "limit": 5000,
                    "remaining": 5000,
                    "reset": datetime.now().isoformat(),
                    "used": 0
                }
            }
    
    async def can_proceed_with_scan(self, estimated_requests: int = 100) -> Tuple[bool, str]:
        """Check if we can proceed with a scan based on rate limits"""
        try:
            rate_limits = await self.check_rate_limits()
            
            core_remaining = rate_limits.get("core", {}).get("remaining", 0)
            graphql_remaining = rate_limits.get("graphql", {}).get("remaining", 0)
            
            # Check if we have enough requests remaining
            if core_remaining < (estimated_requests + self.rate_limit_buffer):
                reset_time = rate_limits.get("core", {}).get("reset", "unknown")
                return False, f"Insufficient REST API requests remaining ({core_remaining}). Reset at {reset_time}"
            
            if graphql_remaining < (estimated_requests // 10 + 10):  # GraphQL uses fewer requests
                reset_time = rate_limits.get("graphql", {}).get("reset", "unknown")
                return False, f"Insufficient GraphQL requests remaining ({graphql_remaining}). Reset at {reset_time}"
            
            return True, "Rate limits OK"
            
        except Exception as e:
            logger.warning(f"Could not check rate limits: {e}")
            return True, "Rate limit check failed, proceeding with caution"
    
    async def optimize_concurrent_settings(self) -> None:
        """Dynamically adjust concurrent settings based on rate limits"""
        try:
            rate_limits = await self.check_rate_limits()
            core_remaining = rate_limits.get("core", {}).get("remaining", 1000)
            
            # Adjust concurrent settings based on remaining requests
            if core_remaining > 2000:
                self.max_concurrent_repos = 8
                self.max_concurrent_requests = 15
            elif core_remaining > 1000:
                self.max_concurrent_repos = 5
                self.max_concurrent_requests = 10
            elif core_remaining > 500:
                self.max_concurrent_repos = 3
                self.max_concurrent_requests = 6
            else:
                self.max_concurrent_repos = 2
                self.max_concurrent_requests = 4
            
            logger.info(f"Optimized concurrent settings: repos={self.max_concurrent_repos}, requests={self.max_concurrent_requests}")
            
        except Exception as e:
            logger.warning(f"Could not optimize concurrent settings: {e}")
    
    async def get_scan_resource_estimate(self, username: str) -> Dict[str, int]:
        """Estimate resource requirements for scanning a user"""
        try:
            user = self.github.get_user(username)
            repo_count = user.public_repos
            
            # Estimate API requests needed
            estimates = {
                "basic_profile": 5,
                "repositories": min(repo_count * 2, 100),  # Cap at 50 repos
                "contribution_calendar": 1,
                "pull_requests": min(repo_count * 3, 150),
                "issues": min(repo_count * 2, 100),
                "organizations": 2,
                "total_estimated": 0
            }
            
            estimates["total_estimated"] = sum(estimates.values()) - estimates["total_estimated"]
            
            return estimates
            
        except Exception as e:
            logger.error(f"Error estimating scan resources: {e}")
            return {"total_estimated": 200}  # Conservative estimate
    
    async def make_github_api_request(self, url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Make GitHub API request using connection pool"""
        try:
            # Use connection pool if available
            if connection_pool_manager.initialized:
                http_pool = connection_pool_manager.get_http_pool()
                
                async with http_pool.get_session() as session:
                    request_headers = {**self.headers}
                    if headers:
                        request_headers.update(headers)
                    
                    async with session.get(url, headers=request_headers) as response:
                        response.raise_for_status()
                        return await response.json()
            else:
                # Fallback to requests library
                import requests
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"GitHub API request failed for {url}: {e}")
            raise
    
    async def get_comprehensive_user_profile_with_pools(self, username: str) -> Dict[str, Any]:
        """Get comprehensive user profile using connection pools and concurrent fetching"""
        try:
            # Check if we can proceed with the scan
            can_proceed, message = await self.can_proceed_with_scan()
            if not can_proceed:
                raise Exception(f"Cannot proceed with scan: {message}")
            
            # Optimize concurrent settings based on rate limits
            await self.optimize_concurrent_settings()
            
            # Track scanning performance
            scan_id = f"comprehensive_scan_{username}_{int(datetime.utcnow().timestamp())}"
            
            async with performance_service.track_scanning_performance(scan_id, username, "comprehensive_profile_pooled"):
                user = self.github.get_user(username)
                
                # Use concurrent fetching with connection pools
                profile = await self._get_comprehensive_profile_concurrent(user, username)
                
                # Add resource usage information
                if connection_pool_manager.initialized:
                    pool_stats = connection_pool_manager.get_all_stats()
                    profile["_metadata"] = {
                        "scan_method": "concurrent_with_pools",
                        "connection_pool_stats": pool_stats,
                        "scan_timestamp": datetime.now().isoformat()
                    }
                
                return profile
            
        except Exception as e:
            logger.error(f"Error getting comprehensive profile with pools for {username}: {e}")
            raise Exception(f"Failed to get comprehensive profile: {e}")
    
    async def get_comprehensive_user_profile(self, username: str) -> Dict[str, Any]:
        """Get comprehensive user profile with all available data using concurrent fetching"""
        try:
            # Track scanning performance
            scan_id = f"comprehensive_scan_{username}_{int(datetime.utcnow().timestamp())}"
            
            async with performance_service.track_scanning_performance(scan_id, username, "comprehensive_profile"):
                user = self.github.get_user(username)
                
                # Use concurrent fetching for parallel data collection
                profile = await self._get_comprehensive_profile_concurrent(user, username)
                
                return profile
            
        except Exception as e:
            logger.error(f"Error getting comprehensive profile for {username}: {e}")
            raise Exception(f"Failed to get comprehensive profile: {e}")
    
    async def _get_comprehensive_profile_concurrent(self, user, username: str) -> Dict[str, Any]:
        """Get comprehensive profile using concurrent data fetching"""
        try:
            # Prepare concurrent requests for all profile data
            requests = [
                (f"basic_info_{username}", self._get_basic_user_info, (user,), {}),
                (f"contribution_stats_{username}", self._get_contribution_statistics, (username,), {}),
                (f"repository_overview_{username}", self._get_repository_overview, (user,), {}),
                (f"activity_calendar_{username}", self._get_activity_calendar, (username,), {}),
                (f"collaboration_metrics_{username}", self._get_collaboration_metrics, (user,), {}),
                (f"language_statistics_{username}", self._get_language_statistics, (user,), {}),
                (f"achievement_metrics_{username}", self._get_achievement_metrics, (user,), {}),
                (f"social_metrics_{username}", self._get_social_metrics, (user,), {}),
                (f"recent_activity_{username}", self._get_recent_activity, (user,), {}),
                (f"organizations_{username}", self._get_organizations, (user,), {})
            ]
            
            # Submit all requests concurrently with high priority
            results = await concurrent_fetcher.submit_batch(
                requests, 
                priority=RequestPriority.HIGH,
                timeout=60.0
            )
            
            # Process results and build profile
            profile = {}
            result_mapping = {
                f"basic_info_{username}": "basic_info",
                f"contribution_stats_{username}": "contribution_stats", 
                f"repository_overview_{username}": "repository_overview",
                f"activity_calendar_{username}": "activity_calendar",
                f"collaboration_metrics_{username}": "collaboration_metrics",
                f"language_statistics_{username}": "language_statistics",
                f"achievement_metrics_{username}": "achievement_metrics",
                f"social_metrics_{username}": "social_metrics",
                f"recent_activity_{username}": "recent_activity",
                f"organizations_{username}": "organizations"
            }
            
            for result in results:
                if result.success:
                    profile_key = result_mapping.get(result.request_id)
                    if profile_key:
                        profile[profile_key] = result.result
                else:
                    logger.warning(f"Failed to get {result.request_id}: {result.error}")
                    # Provide empty fallback data
                    profile_key = result_mapping.get(result.request_id)
                    if profile_key:
                        profile[profile_key] = {}
            
            # Add empty structures for PR and issue analysis (filled separately)
            profile["pull_request_analysis"] = self.pr_analyzer._empty_pr_analysis()
            profile["issue_analysis"] = self.issue_analyzer._empty_issue_analysis()
            
            return profile
            
        except Exception as e:
            logger.error(f"Error in concurrent profile fetching: {e}")
            # Fallback to sequential processing
            return await self._get_comprehensive_profile_sequential(user, username)
    
    async def _get_comprehensive_profile_sequential(self, user, username: str) -> Dict[str, Any]:
        """Fallback sequential profile fetching"""
        return {
            "basic_info": await self._get_basic_user_info(user),
            "contribution_stats": await self._get_contribution_statistics(username),
            "repository_overview": await self._get_repository_overview(user),
            "activity_calendar": await self._get_activity_calendar(username),
            "collaboration_metrics": await self._get_collaboration_metrics(user),
            "language_statistics": await self._get_language_statistics(user),
            "achievement_metrics": await self._get_achievement_metrics(user),
            "social_metrics": await self._get_social_metrics(user),
            "recent_activity": await self._get_recent_activity(user),
            "organizations": await self._get_organizations(user),
            "pull_request_analysis": self.pr_analyzer._empty_pr_analysis(),
            "issue_analysis": self.issue_analyzer._empty_issue_analysis()
        }
    
    async def _get_basic_user_info(self, user) -> Dict[str, Any]:
        """Get basic user information"""
        return {
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
    
    async def _get_contribution_statistics(self, username: str) -> Dict[str, Any]:
        """Get detailed contribution statistics using enhanced GraphQL client"""
        try:
            # Use the enhanced GraphQL client for comprehensive contribution data
            contribution_data = await self.graphql_client.get_contribution_calendar(username)
            
            # The GraphQL client already provides comprehensive data
            return contribution_data
            
        except Exception as e:
            logger.warning(f"GraphQL contribution stats failed: {e}")
            # Fallback to basic stats if GraphQL fails
            return await self._get_basic_contribution_stats(username)
    
    async def _get_basic_contribution_stats(self, username: str) -> Dict[str, Any]:
        """Fallback method for contribution stats using REST API"""
        try:
            user = self.github.get_user(username)
            
            # Get recent events
            events = list(user.get_events()[:300])
            
            stats = {
                "total_commits": 0,
                "total_issues": 0,
                "total_pull_requests": 0,
                "total_reviews": 0,
                "recent_activity_count": len(events),
                "event_types": defaultdict(int),
                "active_days_last_30": set(),
                "contribution_streak": 0
            }
            
            # Analyze events
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            for event in events:
                event_type = event.type
                stats["event_types"][event_type] += 1
                
                if event.created_at.replace(tzinfo=None) > thirty_days_ago:
                    stats["active_days_last_30"].add(event.created_at.date().isoformat())
                
                if event_type == "PushEvent":
                    stats["total_commits"] += len(event.payload.get("commits", []))
                elif event_type == "IssuesEvent":
                    stats["total_issues"] += 1
                elif event_type == "PullRequestEvent":
                    stats["total_pull_requests"] += 1
                elif event_type == "PullRequestReviewEvent":
                    stats["total_reviews"] += 1
            
            stats["active_days_last_30"] = len(stats["active_days_last_30"])
            stats["event_types"] = dict(stats["event_types"])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting basic contribution stats: {e}")
            return {}
    
    def _calculate_contribution_streak(self, calendar_data: List[Dict]) -> Dict[str, Any]:
        """Calculate contribution streak from calendar data"""
        if not calendar_data:
            return {"current_streak": 0, "longest_streak": 0}
        
        # Sort by date
        sorted_data = sorted(calendar_data, key=lambda x: x['date'])
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        # Calculate streaks
        for i, day in enumerate(sorted_data):
            if day['count'] > 0:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
        
        # Calculate current streak (from today backwards)
        today = datetime.now().date()
        for day in reversed(sorted_data):
            day_date = datetime.fromisoformat(day['date']).date()
            if day_date > today:
                continue
            if day['count'] > 0:
                current_streak += 1
            else:
                break
        
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak
        }
    
    async def _get_repository_overview(self, user) -> Dict[str, Any]:
        """Get comprehensive repository overview"""
        try:
            repos = list(user.get_repos(type='public', sort='updated'))
            
            overview = {
                "total_repositories": len(repos),
                "original_repositories": 0,
                "forked_repositories": 0,
                "total_stars": 0,
                "total_forks": 0,
                "total_watchers": 0,
                "languages": defaultdict(int),
                "topics": defaultdict(int),
                "repository_sizes": [],
                "creation_timeline": defaultdict(int),
                "most_starred": None,
                "most_forked": None,
                "recently_updated": []
            }
            
            most_starred = {"stars": 0, "repo": None}
            most_forked = {"forks": 0, "repo": None}
            
            for repo in repos:
                # Basic counts
                if repo.fork:
                    overview["forked_repositories"] += 1
                else:
                    overview["original_repositories"] += 1
                
                # Metrics
                overview["total_stars"] += repo.stargazers_count
                overview["total_forks"] += repo.forks_count
                overview["total_watchers"] += repo.watchers_count
                
                # Languages
                if repo.language:
                    overview["languages"][repo.language] += 1
                
                # Topics
                try:
                    topics = repo.get_topics()
                    for topic in topics:
                        overview["topics"][topic] += 1
                except:
                    pass
                
                # Size tracking
                overview["repository_sizes"].append(repo.size)
                
                # Creation timeline
                year = repo.created_at.year
                overview["creation_timeline"][str(year)] += 1
                
                # Most starred/forked
                if repo.stargazers_count > most_starred["stars"]:
                    most_starred = {
                        "stars": repo.stargazers_count,
                        "repo": {
                            "name": repo.name,
                            "description": repo.description,
                            "html_url": repo.html_url,
                            "language": repo.language
                        }
                    }
                
                if repo.forks_count > most_forked["forks"]:
                    most_forked = {
                        "forks": repo.forks_count,
                        "repo": {
                            "name": repo.name,
                            "description": repo.description,
                            "html_url": repo.html_url,
                            "language": repo.language
                        }
                    }
                
                # Recently updated (last 30 days)
                if (datetime.now() - repo.updated_at.replace(tzinfo=None)).days <= 30:
                    overview["recently_updated"].append({
                        "name": repo.name,
                        "updated_at": repo.updated_at.isoformat(),
                        "language": repo.language,
                        "stars": repo.stargazers_count
                    })
            
            # Convert defaultdicts and add calculated fields
            overview["languages"] = dict(overview["languages"])
            overview["topics"] = dict(overview["topics"])
            overview["creation_timeline"] = dict(overview["creation_timeline"])
            overview["most_starred"] = most_starred["repo"]
            overview["most_forked"] = most_forked["repo"]
            overview["average_repository_size"] = sum(overview["repository_sizes"]) / len(overview["repository_sizes"]) if overview["repository_sizes"] else 0
            
            # Sort recently updated
            overview["recently_updated"].sort(key=lambda x: x["updated_at"], reverse=True)
            overview["recently_updated"] = overview["recently_updated"][:10]
            
            # Add the actual repositories list for external access
            repositories_list = []
            
            # Process ALL repos with full details
            for i, repo in enumerate(repos):  # Include all repositories
                try:
                    repo_data = {
                        "id": repo.id,
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "description": repo.description or "",
                        "language": repo.language,
                        "stargazers_count": repo.stargazers_count,
                        "forks_count": repo.forks_count,
                        "watchers_count": repo.watchers_count,
                        "size": repo.size,
                        "created_at": repo.created_at.isoformat(),
                        "updated_at": repo.updated_at.isoformat(),
                        "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                        "html_url": repo.html_url,
                        "clone_url": repo.clone_url,
                        "private": repo.private,
                        "fork": repo.fork,
                        "archived": repo.archived,
                        "disabled": repo.disabled,
                        "topics": list(repo.get_topics()) if hasattr(repo, 'get_topics') else [],
                        "license": {"name": repo.license.name, "key": repo.license.key} if repo.license else None,
                        "default_branch": repo.default_branch,
                        "open_issues_count": repo.open_issues_count,
                        "evaluate_for_scoring": True  # Mark for detailed evaluation
                    }
                    repositories_list.append(repo_data)
                except Exception as e:
                    logger.error(f"Error processing repository {repo.name}: {e}")
                    # Still add basic info even if detailed processing fails
                    try:
                        repo_data = {
                            "id": repo.id,
                            "name": repo.name,
                            "language": repo.language,
                            "stargazers_count": repo.stargazers_count,
                            "error": str(e)
                        }
                        repositories_list.append(repo_data)
                    except:
                        pass
            
            overview["repositories"] = repositories_list
            overview["evaluated_repositories_count"] = len(repos)
            overview["total_displayed_repositories"] = len(repositories_list)
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting repository overview: {e}")
            return {}
    
    async def _get_activity_calendar(self, username: str) -> Dict[str, Any]:
        """Get activity calendar data (contribution heatmap)"""
        try:
            # This data is included in contribution statistics
            # Return a simplified version for now
            return {
                "note": "Activity calendar data included in contribution_stats",
                "available": True
            }
        except Exception as e:
            logger.error(f"Error getting activity calendar: {e}")
            return {"available": False, "error": str(e)}
    
    async def _get_collaboration_metrics(self, user) -> Dict[str, Any]:
        """Get collaboration and community metrics"""
        try:
            metrics = {
                "followers": user.followers,
                "following": user.following,
                "public_gists": user.public_gists,
                "organizations_count": 0,
                "contributed_repositories": 0,
                "pull_requests_opened": 0,
                "issues_opened": 0,
                "code_reviews_given": 0
            }
            
            # Get organizations
            try:
                orgs = list(user.get_orgs())
                metrics["organizations_count"] = len(orgs)
            except:
                pass
            
            # Analyze recent events for collaboration metrics
            try:
                events = list(user.get_events()[:200])
                for event in events:
                    if event.type == "PullRequestEvent":
                        metrics["pull_requests_opened"] += 1
                    elif event.type == "IssuesEvent":
                        metrics["issues_opened"] += 1
                    elif event.type == "PullRequestReviewEvent":
                        metrics["code_reviews_given"] += 1
            except:
                pass
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting collaboration metrics: {e}")
            return {}
    
    async def _get_language_statistics(self, user) -> Dict[str, Any]:
        """Get comprehensive language usage statistics"""
        try:
            repos = list(user.get_repos(type='public'))
            
            language_stats = {
                "total_languages": 0,
                "language_breakdown": defaultdict(lambda: {
                    "repositories": 0,
                    "total_bytes": 0,
                    "stars": 0,
                    "forks": 0
                }),
                "primary_language": None,
                "language_diversity_score": 0
            }
            
            total_bytes = 0
            
            for repo in repos:
                if repo.language:
                    lang_data = language_stats["language_breakdown"][repo.language]
                    lang_data["repositories"] += 1
                    lang_data["stars"] += repo.stargazers_count
                    lang_data["forks"] += repo.forks_count
                
                # Get detailed language breakdown for this repo
                try:
                    languages = repo.get_languages()
                    for lang, bytes_count in languages.items():
                        language_stats["language_breakdown"][lang]["total_bytes"] += bytes_count
                        total_bytes += bytes_count
                except:
                    pass
            
            # Convert to regular dict and calculate percentages
            language_breakdown = {}
            for lang, data in language_stats["language_breakdown"].items():
                percentage = (data["total_bytes"] / total_bytes * 100) if total_bytes > 0 else 0
                language_breakdown[lang] = {
                    **data,
                    "percentage": round(percentage, 2)
                }
            
            # Sort by total bytes and get primary language
            sorted_languages = sorted(language_breakdown.items(), key=lambda x: x[1]["total_bytes"], reverse=True)
            
            language_stats["language_breakdown"] = dict(sorted_languages)
            language_stats["total_languages"] = len(language_breakdown)
            language_stats["primary_language"] = sorted_languages[0][0] if sorted_languages else None
            
            # Calculate diversity score (entropy-based)
            if total_bytes > 0:
                import math
                entropy = 0
                for lang_data in language_breakdown.values():
                    if lang_data["total_bytes"] > 0:
                        p = lang_data["total_bytes"] / total_bytes
                        entropy -= p * math.log2(p)
                language_stats["language_diversity_score"] = round(entropy, 2)
            
            return language_stats
            
        except Exception as e:
            logger.error(f"Error getting language statistics: {e}")
            return {}
    
    async def _get_achievement_metrics(self, user) -> Dict[str, Any]:
        """Calculate achievement-like metrics"""
        try:
            repos = list(user.get_repos(type='public'))
            
            achievements = {
                "total_stars_earned": sum(repo.stargazers_count for repo in repos),
                "total_forks_earned": sum(repo.forks_count for repo in repos),
                "repositories_with_stars": len([repo for repo in repos if repo.stargazers_count > 0]),
                "repositories_with_forks": len([repo for repo in repos if repo.forks_count > 0]),
                "popular_repositories": len([repo for repo in repos if repo.stargazers_count >= 10]),
                "highly_popular_repositories": len([repo for repo in repos if repo.stargazers_count >= 100]),
                "account_age_years": (datetime.now() - user.created_at.replace(tzinfo=None)).days / 365.25,
                "repositories_per_year": 0,
                "consistency_score": 0
            }
            
            # Calculate repositories per year
            if achievements["account_age_years"] > 0:
                achievements["repositories_per_year"] = round(len(repos) / achievements["account_age_years"], 2)
            
            # Calculate consistency score based on regular activity
            if repos:
                # Check if user has been consistently active (repositories spread over time)
                creation_years = set(repo.created_at.year for repo in repos)
                current_year = datetime.now().year
                account_years = current_year - user.created_at.year + 1
                
                if account_years > 0:
                    achievements["consistency_score"] = round((len(creation_years) / account_years) * 100, 1)
            
            achievements["account_age_years"] = round(achievements["account_age_years"], 1)
            
            return achievements
            
        except Exception as e:
            logger.error(f"Error calculating achievement metrics: {e}")
            return {}
    
    async def _get_social_metrics(self, user) -> Dict[str, Any]:
        """Get social engagement metrics"""
        try:
            return {
                "followers": user.followers,
                "following": user.following,
                "follower_following_ratio": round(user.followers / max(user.following, 1), 2),
                "social_presence": {
                    "has_bio": bool(user.bio),
                    "has_company": bool(user.company),
                    "has_location": bool(user.location),
                    "has_blog": bool(user.blog),
                    "has_twitter": bool(user.twitter_username),
                    "has_email": bool(user.email)
                },
                "profile_completeness": self._calculate_profile_completeness(user)
            }
        except Exception as e:
            logger.error(f"Error getting social metrics: {e}")
            return {}
    
    def _calculate_profile_completeness(self, user) -> float:
        """Calculate profile completeness percentage"""
        fields = [
            user.name, user.bio, user.company, user.location, 
            user.blog, user.twitter_username, user.email
        ]
        completed_fields = sum(1 for field in fields if field)
        return round((completed_fields / len(fields)) * 100, 1)
    
    async def _get_recent_activity(self, user) -> Dict[str, Any]:
        """Get recent activity summary"""
        try:
            # Get events with error handling
            events = []
            try:
                events_iter = user.get_events()
                events = list(events_iter[:20])  # Limit to 20 for performance
            except Exception as e:
                logger.warning(f"Could not fetch events: {e}")
                return {
                    "total_recent_events": 0,
                    "event_summary": {},
                    "recent_repositories": [],
                    "last_activity_date": None,
                    "activity_frequency": "unknown"
                }
            
            activity = {
                "total_recent_events": len(events),
                "event_summary": defaultdict(int),
                "recent_repositories": set(),
                "last_activity_date": None,
                "activity_frequency": "low"
            }
            
            if events and len(events) > 0:
                try:
                    activity["last_activity_date"] = events[0].created_at.isoformat()
                    
                    for event in events:
                        if hasattr(event, 'type'):
                            activity["event_summary"][event.type] += 1
                        if hasattr(event, 'repo') and event.repo and hasattr(event.repo, 'name'):
                            activity["recent_repositories"].add(event.repo.name)
                    
                    # Calculate activity frequency
                    if len(events) > 0 and hasattr(events[-1], 'created_at'):
                        recent_days = (datetime.now() - events[-1].created_at.replace(tzinfo=None)).days
                        if recent_days <= 7:
                            activity["activity_frequency"] = "very_high"
                        elif recent_days <= 30:
                            activity["activity_frequency"] = "high"
                        elif recent_days <= 90:
                            activity["activity_frequency"] = "medium"
                except Exception as e:
                    logger.warning(f"Error processing events: {e}")
            
            activity["event_summary"] = dict(activity["event_summary"])
            activity["recent_repositories"] = list(activity["recent_repositories"])
            
            return activity
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return {
                "total_recent_events": 0,
                "event_summary": {},
                "recent_repositories": [],
                "last_activity_date": None,
                "activity_frequency": "unknown"
            }
    
    async def _get_organizations(self, user) -> List[Dict[str, Any]]:
        """Get user's organizations using GraphQL for enhanced data"""
        try:
            # Try GraphQL first for comprehensive organization data
            try:
                org_data = await self.graphql_client.get_user_organizations(user.login)
                return org_data["organizations"]
            except Exception as graphql_error:
                logger.warning(f"GraphQL organizations query failed: {graphql_error}")
                
                # Fallback to REST API
                orgs = []
                for org in user.get_orgs():
                    orgs.append({
                        "login": org.login,
                        "id": org.id,
                        "name": org.name,
                        "description": org.description,
                        "avatar_url": org.avatar_url,
                        "html_url": org.html_url,
                        "public_repos": org.public_repos,
                        "created_at": org.created_at.isoformat() if org.created_at else None
                    })
                    
                    if len(orgs) >= 20:  # Limit to 20 organizations
                        break
                
                return orgs
            
        except Exception as e:
            logger.error(f"Error getting organizations: {e}")
            return []
    
    async def get_repository_comprehensive_analysis(self, repo_full_name: str) -> Dict[str, Any]:
        """Get comprehensive analysis of a specific repository using concurrent GraphQL and REST APIs"""
        try:
            # Parse owner and repo name
            owner, name = repo_full_name.split('/')
            
            # Get comprehensive repository data using concurrent fetching
            try:
                analysis = await self._get_repository_analysis_concurrent(owner, name, repo_full_name)
                return analysis
                
            except Exception as concurrent_error:
                logger.warning(f"Concurrent repository analysis failed: {concurrent_error}")
                # Fallback to sequential processing
                return await self._get_repository_analysis_sequential(owner, name, repo_full_name)
            
        except Exception as e:
            logger.error(f"Error getting comprehensive repository analysis: {e}")
            raise Exception(f"Repository analysis failed: {e}")
    
    async def _get_repository_analysis_concurrent(self, owner: str, name: str, repo_full_name: str) -> Dict[str, Any]:
        """Get repository analysis using concurrent data fetching"""
        try:
            repo = self.github.get_repo(repo_full_name)
            
            # Prepare concurrent requests for repository analysis
            requests = [
                (f"graphql_data_{repo_full_name}", self.graphql_client.get_repository_details, (owner, name), {}),
                (f"code_analysis_{repo_full_name}", self._get_repo_code_analysis, (repo,), {}),
                (f"collaboration_data_{repo_full_name}", self._get_repo_collaboration_data, (repo,), {}),
                (f"activity_timeline_{repo_full_name}", self._get_repo_activity_timeline, (repo,), {}),
                (f"commit_analysis_{repo_full_name}", self._get_repo_commit_analysis, (repo,), {}),
                (f"quality_metrics_{repo_full_name}", self._get_repo_quality_metrics, (repo,), {}),
                (f"pull_requests_{repo_full_name}", self._get_repo_pull_requests, (repo,), {}),
                (f"issues_{repo_full_name}", self._get_repo_issues, (repo,), {}),
                (f"releases_{repo_full_name}", self._get_repo_releases, (repo,), {}),
                (f"contributors_{repo_full_name}", self._get_repo_contributors, (repo,), {})
            ]
            
            # Submit all requests concurrently
            results = await concurrent_fetcher.submit_batch(
                requests,
                priority=RequestPriority.HIGH,
                timeout=90.0
            )
            
            # Process results
            analysis_data = {}
            graphql_data = None
            
            for result in results:
                if result.success:
                    if result.request_id == f"graphql_data_{repo_full_name}":
                        graphql_data = result.result
                    elif result.request_id == f"code_analysis_{repo_full_name}":
                        analysis_data["code_analysis"] = result.result
                    elif result.request_id == f"collaboration_data_{repo_full_name}":
                        analysis_data["collaboration_data"] = result.result
                    elif result.request_id == f"activity_timeline_{repo_full_name}":
                        analysis_data["activity_timeline"] = result.result
                    elif result.request_id == f"commit_analysis_{repo_full_name}":
                        analysis_data["commit_analysis"] = result.result
                    elif result.request_id == f"quality_metrics_{repo_full_name}":
                        analysis_data["quality_metrics"] = result.result
                    elif result.request_id == f"pull_requests_{repo_full_name}":
                        analysis_data["pull_requests"] = result.result
                    elif result.request_id == f"issues_{repo_full_name}":
                        analysis_data["issues"] = result.result
                    elif result.request_id == f"releases_{repo_full_name}":
                        analysis_data["releases"] = result.result
                    elif result.request_id == f"contributors_{repo_full_name}":
                        analysis_data["contributors"] = result.result
                else:
                    logger.warning(f"Failed to get {result.request_id}: {result.error}")
            
            # Build final analysis combining GraphQL and REST data
            if graphql_data:
                analysis = {
                    "basic_info": graphql_data.get("basic_info", {}),
                    "languages": graphql_data.get("languages", {}),
                    "topics": graphql_data.get("topics", []),
                    "license": graphql_data.get("license", {}),
                    "collaborators": graphql_data.get("collaborators", []),
                    **analysis_data,
                    "data_source": "concurrent_graphql_enhanced",
                    "analysis_date": datetime.now().isoformat()
                }
            else:
                # Fallback to REST-only data
                basic_info = await self._get_repo_basic_info(repo)
                analysis = {
                    "basic_info": basic_info,
                    **analysis_data,
                    "data_source": "concurrent_rest_fallback",
                    "analysis_date": datetime.now().isoformat()
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in concurrent repository analysis: {e}")
            raise
    
    async def _get_repository_analysis_sequential(self, owner: str, name: str, repo_full_name: str) -> Dict[str, Any]:
        """Fallback sequential repository analysis"""
        try:
            # Get comprehensive repository data using GraphQL
            try:
                graphql_data = await self.graphql_client.get_repository_details(owner, name)
                
                # Combine with REST API data for additional analysis
                repo = self.github.get_repo(repo_full_name)
                
                analysis = {
                    "basic_info": graphql_data["basic_info"],
                    "languages": graphql_data["languages"],
                    "topics": graphql_data["topics"],
                    "license": graphql_data["license"],
                    "issues": graphql_data["issues"],
                    "pull_requests": graphql_data["pull_requests"],
                    "releases": graphql_data["releases"],
                    "collaborators": graphql_data["collaborators"],
                    "code_analysis": await self._get_repo_code_analysis(repo),
                    "collaboration_data": await self._get_repo_collaboration_data(repo),
                    "activity_timeline": await self._get_repo_activity_timeline(repo),
                    "commit_analysis": await self._get_repo_commit_analysis(repo),
                    "quality_metrics": await self._get_repo_quality_metrics(repo),
                    "data_source": "sequential_graphql_enhanced",
                    "analysis_date": datetime.now().isoformat()
                }
                
                return analysis
                
            except Exception as graphql_error:
                logger.warning(f"GraphQL repository analysis failed: {graphql_error}")
                # Fallback to REST API only
                repo = self.github.get_repo(repo_full_name)
                
                analysis = {
                    "basic_info": await self._get_repo_basic_info(repo),
                    "code_analysis": await self._get_repo_code_analysis(repo),
                    "collaboration_data": await self._get_repo_collaboration_data(repo),
                    "activity_timeline": await self._get_repo_activity_timeline(repo),
                    "pull_requests": await self._get_repo_pull_requests(repo),
                    "issues": await self._get_repo_issues(repo),
                    "releases": await self._get_repo_releases(repo),
                    "contributors": await self._get_repo_contributors(repo),
                    "commit_analysis": await self._get_repo_commit_analysis(repo),
                    "quality_metrics": await self._get_repo_quality_metrics(repo),
                    "data_source": "rest_fallback",
                    "analysis_date": datetime.now().isoformat()
                }
                
                return analysis
            
        except Exception as e:
            logger.error(f"Error getting comprehensive repository analysis: {e}")
            raise Exception(f"Repository analysis failed: {e}")
    
    async def _get_repo_basic_info(self, repo) -> Dict[str, Any]:
        """Get basic repository information"""
        return {
            "id": repo.id,
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "html_url": repo.html_url,
            "clone_url": repo.clone_url,
            "language": repo.language,
            "size": repo.size,
            "stargazers_count": repo.stargazers_count,
            "forks_count": repo.forks_count,
            "watchers_count": repo.watchers_count,
            "open_issues_count": repo.open_issues_count,
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat(),
            "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
            "default_branch": repo.default_branch,
            "topics": list(repo.get_topics()),
            "license": {"name": repo.license.name, "key": repo.license.key} if repo.license else None,
            "is_fork": repo.fork,
            "is_private": repo.private,
            "is_archived": repo.archived,
            "is_template": repo.is_template if hasattr(repo, 'is_template') else False,
            "homepage": repo.homepage,
            "has_issues": repo.has_issues,
            "has_projects": repo.has_projects,
            "has_wiki": repo.has_wiki,
            "has_downloads": repo.has_downloads
        }
    
    async def _get_repo_code_analysis(self, repo) -> Dict[str, Any]:
        """Analyze repository code structure"""
        try:
            languages = repo.get_languages()
            total_bytes = sum(languages.values())
            
            return {
                "languages": languages,
                "primary_language": repo.language,
                "language_percentages": {
                    lang: round((bytes_count / total_bytes) * 100, 2) 
                    for lang, bytes_count in languages.items()
                } if total_bytes > 0 else {},
                "total_size_bytes": total_bytes,
                "file_structure": await self._analyze_file_structure(repo)
            }
        except Exception as e:
            logger.warning(f"Code analysis failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_file_structure(self, repo) -> Dict[str, Any]:
        """Analyze repository file structure"""
        try:
            contents = repo.get_contents("")
            if not isinstance(contents, list):
                contents = [contents]
            
            structure = {
                "total_files": 0,
                "directories": 0,
                "file_types": defaultdict(int),
                "has_readme": False,
                "has_license": False,
                "has_gitignore": False,
                "has_dockerfile": False,
                "has_tests": False,
                "has_ci_config": False,
                "config_files": []
            }
            
            for content in contents:
                if content.type == "file":
                    structure["total_files"] += 1
                    
                    # Check file extensions
                    if '.' in content.name:
                        ext = content.name.split('.')[-1].lower()
                        structure["file_types"][ext] += 1
                    
                    # Check for important files
                    name_lower = content.name.lower()
                    if name_lower.startswith('readme'):
                        structure["has_readme"] = True
                    elif name_lower in ['license', 'license.txt', 'license.md']:
                        structure["has_license"] = True
                    elif name_lower == '.gitignore':
                        structure["has_gitignore"] = True
                    elif name_lower in ['dockerfile', 'docker-compose.yml']:
                        structure["has_dockerfile"] = True
                    elif name_lower in ['package.json', 'requirements.txt', 'pom.xml', 'cargo.toml']:
                        structure["config_files"].append(content.name)
                
                elif content.type == "dir":
                    structure["directories"] += 1
                    
                    # Check for test directories
                    dir_lower = content.name.lower()
                    if dir_lower in ['test', 'tests', '__tests__', 'spec']:
                        structure["has_tests"] = True
                    elif dir_lower in ['.github', '.gitlab-ci.yml', '.travis.yml']:
                        structure["has_ci_config"] = True
            
            structure["file_types"] = dict(structure["file_types"])
            return structure
            
        except Exception as e:
            logger.warning(f"File structure analysis failed: {e}")
            return {"error": str(e)}
    
    async def _get_repo_collaboration_data(self, repo) -> Dict[str, Any]:
        """Get repository collaboration metrics"""
        try:
            return {
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "open_issues": repo.open_issues_count,
                "network_count": repo.network_count,
                "subscribers_count": repo.subscribers_count
            }
        except Exception as e:
            logger.warning(f"Collaboration data failed: {e}")
            return {"error": str(e)}
    
    async def _get_repo_activity_timeline(self, repo) -> Dict[str, Any]:
        """Get repository activity timeline"""
        try:
            # Get recent commits for activity timeline
            commits = list(repo.get_commits()[:100])
            
            timeline = {
                "total_commits": len(commits),
                "commit_frequency": defaultdict(int),
                "recent_activity": []
            }
            
            for commit in commits:
                # Group by month
                month_key = commit.commit.author.date.strftime("%Y-%m")
                timeline["commit_frequency"][month_key] += 1
                
                # Recent activity (last 30 days)
                if (datetime.now() - commit.commit.author.date.replace(tzinfo=None)).days <= 30:
                    timeline["recent_activity"].append({
                        "sha": commit.sha[:8],
                        "message": commit.commit.message[:100],
                        "author": commit.commit.author.name,
                        "date": commit.commit.author.date.isoformat()
                    })
            
            timeline["commit_frequency"] = dict(timeline["commit_frequency"])
            return timeline
            
        except Exception as e:
            logger.warning(f"Activity timeline failed: {e}")
            return {"error": str(e)}
    
    async def _get_repo_pull_requests(self, repo) -> Dict[str, Any]:
        """Get repository pull request data"""
        try:
            # Get recent pull requests
            prs = list(repo.get_pulls(state='all', sort='updated', direction='desc')[:50])
            
            pr_data = {
                "total_prs": len(prs),
                "open_prs": len([pr for pr in prs if pr.state == 'open']),
                "closed_prs": len([pr for pr in prs if pr.state == 'closed']),
                "merged_prs": len([pr for pr in prs if pr.merged]),
                "recent_prs": []
            }
            
            for pr in prs[:10]:  # Last 10 PRs
                pr_data["recent_prs"].append({
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "created_at": pr.created_at.isoformat(),
                    "updated_at": pr.updated_at.isoformat(),
                    "user": pr.user.login if pr.user else None,
                    "merged": pr.merged,
                    "html_url": pr.html_url
                })
            
            return pr_data
            
        except Exception as e:
            logger.warning(f"Pull request data failed: {e}")
            return {"error": str(e)}
    
    async def _get_repo_issues(self, repo) -> Dict[str, Any]:
        """Get repository issues data"""
        try:
            issues = list(repo.get_issues(state='all', sort='updated', direction='desc')[:50])
            
            issue_data = {
                "total_issues": len(issues),
                "open_issues": len([issue for issue in issues if issue.state == 'open']),
                "closed_issues": len([issue for issue in issues if issue.state == 'closed']),
                "recent_issues": []
            }
            
            for issue in issues[:10]:  # Last 10 issues
                if not issue.pull_request:  # Exclude PRs
                    issue_data["recent_issues"].append({
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "created_at": issue.created_at.isoformat(),
                        "updated_at": issue.updated_at.isoformat(),
                        "user": issue.user.login if issue.user else None,
                        "labels": [label.name for label in issue.labels],
                        "html_url": issue.html_url
                    })
            
            return issue_data
            
        except Exception as e:
            logger.warning(f"Issues data failed: {e}")
            return {"error": str(e)}
    
    async def _get_repo_releases(self, repo) -> Dict[str, Any]:
        """Get repository releases data"""
        try:
            releases = list(repo.get_releases()[:20])
            
            return {
                "total_releases": len(releases),
                "latest_release": {
                    "tag_name": releases[0].tag_name,
                    "name": releases[0].name,
                    "published_at": releases[0].published_at.isoformat(),
                    "html_url": releases[0].html_url
                } if releases else None,
                "recent_releases": [
                    {
                        "tag_name": release.tag_name,
                        "name": release.name,
                        "published_at": release.published_at.isoformat(),
                        "prerelease": release.prerelease,
                        "html_url": release.html_url
                    } for release in releases[:5]
                ]
            }
            
        except Exception as e:
            logger.warning(f"Releases data failed: {e}")
            return {"error": str(e)}
    
    async def _get_repo_contributors(self, repo) -> Dict[str, Any]:
        """Get repository contributors data"""
        try:
            contributors = list(repo.get_contributors()[:50])
            
            return {
                "total_contributors": len(contributors),
                "top_contributors": [
                    {
                        "login": contributor.login,
                        "contributions": contributor.contributions,
                        "avatar_url": contributor.avatar_url,
                        "html_url": contributor.html_url
                    } for contributor in contributors[:10]
                ]
            }
            
        except Exception as e:
            logger.warning(f"Contributors data failed: {e}")
            return {"error": str(e)}
    
    async def _get_repo_commit_analysis(self, repo) -> Dict[str, Any]:
        """Analyze repository commits"""
        try:
            commits = list(repo.get_commits()[:200])
            
            analysis = {
                "total_commits": len(commits),
                "commit_authors": defaultdict(int),
                "commit_timeline": defaultdict(int),
                "average_commits_per_day": 0,
                "commit_message_analysis": {
                    "average_length": 0,
                    "conventional_commits": 0
                }
            }
            
            total_message_length = 0
            conventional_pattern = r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+'
            
            for commit in commits:
                # Author analysis
                author = commit.commit.author.name
                analysis["commit_authors"][author] += 1
                
                # Timeline analysis
                date_key = commit.commit.author.date.strftime("%Y-%m-%d")
                analysis["commit_timeline"][date_key] += 1
                
                # Message analysis
                message = commit.commit.message
                total_message_length += len(message)
                
                if re.match(conventional_pattern, message):
                    analysis["commit_message_analysis"]["conventional_commits"] += 1
            
            # Calculate averages
            if commits:
                analysis["commit_message_analysis"]["average_length"] = total_message_length / len(commits)
                
                # Calculate commits per day
                if len(analysis["commit_timeline"]) > 0:
                    analysis["average_commits_per_day"] = len(commits) / len(analysis["commit_timeline"])
            
            # Convert defaultdicts
            analysis["commit_authors"] = dict(analysis["commit_authors"])
            analysis["commit_timeline"] = dict(analysis["commit_timeline"])
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Commit analysis failed: {e}")
            return {"error": str(e)}
    
    async def _get_repo_quality_metrics(self, repo) -> Dict[str, Any]:
        """Calculate repository quality metrics"""
        try:
            # This would integrate with the existing evaluation engine
            return {
                "has_readme": bool(repo.get_readme() if hasattr(repo, 'get_readme') else False),
                "has_license": bool(repo.license),
                "has_description": bool(repo.description),
                "has_topics": len(list(repo.get_topics())) > 0,
                "is_maintained": (datetime.now() - repo.updated_at.replace(tzinfo=None)).days < 365,
                "community_health": {
                    "has_code_of_conduct": False,  # Would need to check files
                    "has_contributing_guide": False,  # Would need to check files
                    "has_issue_templates": False,  # Would need to check .github folder
                    "has_security_policy": False   # Would need to check files
                }
            }
            
        except Exception as e:
            logger.warning(f"Quality metrics failed: {e}")
            return {"error": str(e)}
    
    async def _get_pull_request_analysis(self, username: str) -> Dict[str, Any]:
        """Get comprehensive pull request analysis for the user"""
        try:
            logger.info(f"Starting pull request analysis for user: {username}")
            analysis = await self.pr_analyzer.analyze_user_pull_requests(username)
            logger.info(f"Pull request analysis completed for {username}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting pull request analysis for {username}: {e}")
            return self.pr_analyzer._empty_pr_analysis()    

    async def _get_issue_analysis(self, username: str) -> Dict[str, Any]:
        """Get comprehensive issue analysis for the user"""
        try:
            logger.info(f"Starting issue analysis for user: {username}")
            analysis = await self.issue_analyzer.analyze_user_issues(username)
            logger.info(f"Issue analysis completed for {username}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting issue analysis for {username}: {e}")
            return self.issue_analyzer._empty_issue_analysis() 
   
    async def _get_pull_request_analysis_fast(self, username: str) -> Dict[str, Any]:
        """Get fast pull request analysis (limited scope)"""
        try:
            logger.info(f"Starting fast pull request analysis for user: {username}")
            # Limit to 5 repositories for fast analysis
            analysis = await self.pr_analyzer.analyze_user_pull_requests(username, max_repos=5)
            logger.info(f"Fast pull request analysis completed for {username}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting fast pull request analysis for {username}: {e}")
            return self.pr_analyzer._empty_pr_analysis()
    
    async def _get_issue_analysis_fast(self, username: str) -> Dict[str, Any]:
        """Get fast issue analysis (limited scope)"""
        try:
            logger.info(f"Starting fast issue analysis for user: {username}")
            # Limit to 5 repositories for fast analysis
            analysis = await self.issue_analyzer.analyze_user_issues(username, max_repos=5)
            logger.info(f"Fast issue analysis completed for {username}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting fast issue analysis for {username}: {e}")
            return self.issue_analyzer._empty_issue_analysis()
    
    async def get_contribution_calendar_data(self, username: str) -> Dict[str, Any]:
        """Get contribution calendar data using GraphQL"""
        try:
            logger.info(f"Fetching contribution calendar for: {username}")
            calendar_data = await self.graphql_client.get_contribution_calendar(username)
            return calendar_data
        except Exception as e:
            logger.warning(f"Failed to get contribution calendar for {username}: {e}")
            return {}
    
    async def analyze_pull_requests_comprehensive(self, username: str, repositories: List[Dict]) -> Dict[str, Any]:
        """Analyze pull requests for user's repositories comprehensively"""
        try:
            logger.info(f"Starting comprehensive PR analysis for {username} across {len(repositories)} repositories")
            
            # Use the pull request analyzer with repository list
            analysis = await self.pr_analyzer.analyze_repositories_pull_requests(repositories)
            
            logger.info(f"Completed comprehensive PR analysis for {username}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive PR analysis for {username}: {e}")
            return self.pr_analyzer._empty_pr_analysis()
    
    async def analyze_issues_comprehensive(self, username: str, repositories: List[Dict]) -> Dict[str, Any]:
        """Analyze issues for user's repositories comprehensively"""
        try:
            logger.info(f"Starting comprehensive issue analysis for {username} across {len(repositories)} repositories")
            
            # Use the issue analyzer with repository list
            analysis = await self.issue_analyzer.analyze_repositories_issues(repositories)
            
            logger.info(f"Completed comprehensive issue analysis for {username}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive issue analysis for {username}: {e}")
            return self.issue_analyzer._empty_issue_analysis()
    
    async def analyze_repositories_concurrent(self, repositories: List[Dict], max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """Analyze multiple repositories concurrently with resource management"""
        try:
            logger.info(f"Starting concurrent analysis of {len(repositories)} repositories")
            
            # Process repositories in batches to manage resources
            batch_size = min(max_concurrent, len(repositories))
            results = []
            
            for i in range(0, len(repositories), batch_size):
                batch = repositories[i:i + batch_size]
                batch_results = await self._process_repository_batch(batch)
                results.extend(batch_results)
                
                # Small delay between batches to prevent rate limiting
                if i + batch_size < len(repositories):
                    await asyncio.sleep(1)
            
            logger.info(f"Completed concurrent analysis of {len(repositories)} repositories")
            return results
            
        except Exception as e:
            logger.error(f"Error in concurrent repository analysis: {e}")
            return []
    
    async def _process_repository_batch(self, repositories: List[Dict]) -> List[Dict[str, Any]]:
        """Process a batch of repositories concurrently"""
        try:
            # Prepare concurrent requests for repository analysis
            requests = []
            for repo in repositories:
                repo_full_name = repo.get('full_name')
                if repo_full_name:
                    request_id = f"repo_analysis_{repo_full_name}_{int(datetime.now().timestamp())}"
                    requests.append((
                        request_id,
                        self.get_repository_comprehensive_analysis,
                        (repo_full_name,),
                        {}
                    ))
            
            if not requests:
                return []
            
            # Submit batch with normal priority to avoid overwhelming the system
            results = await concurrent_fetcher.submit_batch(
                requests,
                priority=RequestPriority.NORMAL,
                timeout=120.0
            )
            
            # Process results
            analysis_results = []
            for result in results:
                if result.success:
                    analysis_results.append(result.result)
                else:
                    logger.warning(f"Repository analysis failed for {result.request_id}: {result.error}")
                    # Add empty result to maintain order
                    analysis_results.append({
                        "error": str(result.error),
                        "analysis_date": datetime.now().isoformat()
                    })
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error processing repository batch: {e}")
            return []
    
    async def get_user_repositories_concurrent(self, username: str, max_repos: int = 50) -> List[Dict[str, Any]]:
        """Get user repositories with concurrent language analysis"""
        try:
            user = self.github.get_user(username)
            repos = list(user.get_repos(type='public', sort='updated')[:max_repos])
            
            if not repos:
                return []
            
            # Prepare concurrent requests for repository language analysis
            requests = []
            for repo in repos:
                request_id = f"repo_languages_{repo.full_name}"
                requests.append((
                    request_id,
                    self._get_repository_languages_concurrent,
                    (repo,),
                    {}
                ))
            
            # Submit batch for language analysis
            results = await concurrent_fetcher.submit_batch(
                requests,
                priority=RequestPriority.NORMAL,
                timeout=60.0
            )
            
            # Build repository list with language data
            repo_data = []
            for i, result in enumerate(results):
                repo = repos[i]
                
                # Basic repository data
                repo_info = {
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description or "",
                    "language": repo.language,
                    "stargazers_count": repo.stargazers_count,
                    "forks_count": repo.forks_count,
                    "watchers_count": repo.watchers_count,
                    "size": repo.size,
                    "created_at": repo.created_at.isoformat(),
                    "updated_at": repo.updated_at.isoformat(),
                    "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                    "html_url": repo.html_url,
                    "clone_url": repo.clone_url,
                    "private": repo.private,
                    "fork": repo.fork,
                    "archived": repo.archived,
                    "disabled": repo.disabled,
                    "default_branch": repo.default_branch,
                    "open_issues_count": repo.open_issues_count
                }
                
                # Add language data from concurrent analysis
                if result.success:
                    repo_info.update(result.result)
                else:
                    logger.warning(f"Language analysis failed for {repo.full_name}: {result.error}")
                    repo_info["languages"] = {}
                    repo_info["topics"] = []
                
                repo_data.append(repo_info)
            
            return repo_data
            
        except Exception as e:
            logger.error(f"Error getting user repositories concurrently: {e}")
            return []
    
    async def _get_repository_languages_concurrent(self, repo) -> Dict[str, Any]:
        """Get repository languages and topics (for concurrent processing)"""
        try:
            # Get languages
            languages = repo.get_languages()
            
            # Get topics
            topics = []
            try:
                topics = list(repo.get_topics())
            except:
                pass
            
            # Get license info
            license_info = None
            if repo.license:
                license_info = {
                    "name": repo.license.name,
                    "key": repo.license.key
                }
            
            return {
                "languages": languages,
                "topics": topics,
                "license": license_info
            }
            
        except Exception as e:
            logger.warning(f"Error getting repository languages for {repo.full_name}: {e}")
            return {
                "languages": {},
                "topics": [],
                "license": None
            }