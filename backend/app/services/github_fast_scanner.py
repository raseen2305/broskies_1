"""
Fast GitHub Scanner Service - Optimized for Speed

This service provides fast GitHub data extraction with minimal API calls:
- Prioritizes essential data over comprehensive analysis
- Uses concurrent processing for critical data
- Implements smart caching and rate limit management
- Focuses on core metrics for quick evaluation
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
from .performance_service import performance_service
from .concurrent_data_fetcher import concurrent_fetcher, RequestPriority

logger = logging.getLogger(__name__)

class GitHubFastScanner:
    """Fast GitHub scanner optimized for speed with minimal API calls"""
    
    def __init__(self, github_token: str):
        self.github = Github(github_token, per_page=100)
        self.token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.graphql_client = GitHubGraphQLClient(github_token)
        self.user = None
        
        # Fast scanning settings
        self.max_repos_to_analyze = 20  # Limit repositories for speed
        self.max_concurrent_requests = 8
        self.skip_detailed_analysis = True  # Skip time-consuming analysis
        
        self._initialize_user()
    
    def _initialize_user(self):
        """Initialize the authenticated user"""
        try:
            self.user = self.github.get_user()
            logger.info(f"Initialized fast GitHub scanner for user: {self.user.login}")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub user: {e}")
            raise
    
    async def get_fast_user_profile(self, username: str) -> Dict[str, Any]:
        """Get user profile optimized for speed - minimal API calls"""
        try:
            scan_id = f"fast_scan_{username}_{int(datetime.utcnow().timestamp())}"
            
            async with performance_service.track_scanning_performance(scan_id, username, "fast_profile"):
                user = self.github.get_user(username)
                
                # Use concurrent fetching for only essential data
                profile = await self._get_fast_profile_concurrent(user, username)
                
                # Add metadata
                profile["_metadata"] = {
                    "scan_method": "fast_optimized",
                    "scan_timestamp": datetime.now().isoformat(),
                    "api_calls_estimated": 15  # Much lower than comprehensive scan
                }
                
                return profile
            
        except Exception as e:
            logger.error(f"Error getting fast profile for {username}: {e}")
            raise Exception(f"Failed to get fast profile: {e}")
    
    async def _get_fast_profile_concurrent(self, user, username: str) -> Dict[str, Any]:
        """Get essential profile data using concurrent fetching"""
        try:
            # Prepare concurrent requests for essential data only
            requests = [
                (f"basic_info_{username}", self._get_basic_user_info_fast, (user,), {}),
                (f"repositories_{username}", self._get_repositories_fast, (user,), {}),
                (f"contribution_stats_{username}", self._get_contribution_stats_fast, (username,), {}),
                (f"language_stats_{username}", self._get_language_stats_fast, (user,), {}),
                (f"activity_summary_{username}", self._get_activity_summary_fast, (user,), {})
            ]
            
            # Submit all requests concurrently with high priority
            results = await concurrent_fetcher.submit_batch(
                requests, 
                priority=RequestPriority.HIGH,
                timeout=30.0  # Shorter timeout for fast scanning
            )
            
            # Process results and build profile
            profile = {}
            result_mapping = {
                f"basic_info_{username}": "basic_info",
                f"repositories_{username}": "repositories",
                f"contribution_stats_{username}": "contribution_stats",
                f"language_stats_{username}": "language_stats",
                f"activity_summary_{username}": "activity_summary"
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
            
            # Calculate derived metrics quickly
            profile["derived_metrics"] = self._calculate_fast_metrics(profile)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error in fast concurrent profile fetching: {e}")
            # Fallback to sequential processing
            return await self._get_fast_profile_sequential(user, username)
    
    async def _get_fast_profile_sequential(self, user, username: str) -> Dict[str, Any]:
        """Fallback sequential profile fetching"""
        return {
            "basic_info": await self._get_basic_user_info_fast(user),
            "repositories": await self._get_repositories_fast(user),
            "contribution_stats": await self._get_contribution_stats_fast(username),
            "language_stats": await self._get_language_stats_fast(user),
            "activity_summary": await self._get_activity_summary_fast(user),
            "derived_metrics": {}
        }
    
    async def _get_basic_user_info_fast(self, user) -> Dict[str, Any]:
        """Get essential user information quickly"""
        return {
            "login": user.login,
            "id": user.id,
            "name": user.name,
            "bio": user.bio,
            "company": user.company,
            "location": user.location,
            "blog": user.blog,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "following": user.following,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "avatar_url": user.avatar_url,
            "html_url": user.html_url
        }
    
    async def _get_repositories_fast(self, user) -> Dict[str, Any]:
        """Get repository overview optimized for speed"""
        try:
            # Limit to most recent repositories for speed
            repos = list(user.get_repos(type='public', sort='updated')[:self.max_repos_to_analyze])
            
            overview = {
                "total_repositories": user.public_repos,  # Use cached value
                "analyzed_repositories": len(repos),
                "original_repositories": 0,
                "forked_repositories": 0,
                "total_stars": 0,
                "total_forks": 0,
                "languages": defaultdict(int),
                "most_starred": None,
                "recently_updated": []
            }
            
            most_starred = {"stars": 0, "repo": None}
            
            for repo in repos:
                # Basic counts
                if repo.fork:
                    overview["forked_repositories"] += 1
                else:
                    overview["original_repositories"] += 1
                
                # Metrics
                overview["total_stars"] += repo.stargazers_count
                overview["total_forks"] += repo.forks_count
                
                # Languages (use primary language only for speed)
                if repo.language:
                    overview["languages"][repo.language] += 1
                
                # Most starred
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
                
                # Recently updated (last 30 days)
                if (datetime.now() - repo.updated_at.replace(tzinfo=None)).days <= 30:
                    overview["recently_updated"].append({
                        "name": repo.name,
                        "updated_at": repo.updated_at.isoformat(),
                        "language": repo.language,
                        "stars": repo.stargazers_count
                    })
            
            # Convert defaultdicts
            overview["languages"] = dict(overview["languages"])
            overview["most_starred"] = most_starred["repo"]
            
            # Sort recently updated
            overview["recently_updated"].sort(key=lambda x: x["updated_at"], reverse=True)
            overview["recently_updated"] = overview["recently_updated"][:5]  # Limit for speed
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting fast repository overview: {e}")
            return {}
    
    async def _get_contribution_stats_fast(self, username: str) -> Dict[str, Any]:
        """Get contribution statistics optimized for speed"""
        try:
            # Use GraphQL for efficient contribution data
            contribution_data = await self.graphql_client.get_contribution_calendar(username)
            
            # Extract key metrics quickly
            if contribution_data and "contributionCalendar" in contribution_data:
                calendar = contribution_data["contributionCalendar"]
                return {
                    "total_contributions": calendar.get("totalContributions", 0),
                    "contribution_calendar": calendar.get("weeks", []),
                    "current_streak": self._calculate_streak_fast(calendar.get("weeks", [])),
                    "most_active_day": self._find_most_active_day(calendar.get("weeks", []))
                }
            
            return {"total_contributions": 0, "contribution_calendar": []}
            
        except Exception as e:
            logger.warning(f"Fast contribution stats failed: {e}")
            return {"total_contributions": 0, "contribution_calendar": []}
    
    def _calculate_streak_fast(self, weeks: List[Dict]) -> int:
        """Calculate current contribution streak quickly"""
        if not weeks:
            return 0
        
        current_streak = 0
        today = datetime.now().date()
        
        # Flatten weeks into days and reverse for recent-first order
        all_days = []
        for week in weeks:
            all_days.extend(week.get("contributionDays", []))
        
        # Calculate current streak from today backwards
        for day in reversed(all_days):
            day_date = datetime.fromisoformat(day["date"]).date()
            if day_date > today:
                continue
            if day["contributionCount"] > 0:
                current_streak += 1
            else:
                break
        
        return current_streak
    
    def _find_most_active_day(self, weeks: List[Dict]) -> Dict[str, Any]:
        """Find the most active contribution day"""
        if not weeks:
            return {"date": None, "count": 0}
        
        max_day = {"date": None, "count": 0}
        
        for week in weeks:
            for day in week.get("contributionDays", []):
                if day["contributionCount"] > max_day["count"]:
                    max_day = {
                        "date": day["date"],
                        "count": day["contributionCount"]
                    }
        
        return max_day
    
    async def _get_language_stats_fast(self, user) -> Dict[str, Any]:
        """Get language statistics optimized for speed"""
        try:
            # Use only recent repositories for speed
            repos = list(user.get_repos(type='public', sort='updated')[:10])
            
            language_stats = {
                "primary_languages": defaultdict(int),
                "total_languages": 0,
                "most_used_language": None
            }
            
            for repo in repos:
                if repo.language:
                    language_stats["primary_languages"][repo.language] += 1
            
            # Convert to regular dict and find most used
            languages = dict(language_stats["primary_languages"])
            language_stats["primary_languages"] = languages
            language_stats["total_languages"] = len(languages)
            
            if languages:
                language_stats["most_used_language"] = max(languages.items(), key=lambda x: x[1])[0]
            
            return language_stats
            
        except Exception as e:
            logger.error(f"Error getting fast language statistics: {e}")
            return {}
    
    async def _get_activity_summary_fast(self, user) -> Dict[str, Any]:
        """Get activity summary optimized for speed"""
        try:
            # Get only recent events for speed
            events = list(user.get_events()[:50])  # Limit to 50 events
            
            activity = {
                "recent_events_count": len(events),
                "event_types": defaultdict(int),
                "last_activity_date": None,
                "activity_level": "unknown"
            }
            
            if events:
                activity["last_activity_date"] = events[0].created_at.isoformat()
                
                # Count event types
                for event in events:
                    activity["event_types"][event.type] += 1
                
                # Determine activity level based on recent events
                recent_days = (datetime.now() - events[-1].created_at.replace(tzinfo=None)).days
                if recent_days <= 7:
                    activity["activity_level"] = "very_active"
                elif recent_days <= 30:
                    activity["activity_level"] = "active"
                elif recent_days <= 90:
                    activity["activity_level"] = "moderate"
                else:
                    activity["activity_level"] = "low"
            
            activity["event_types"] = dict(activity["event_types"])
            return activity
            
        except Exception as e:
            logger.error(f"Error getting fast activity summary: {e}")
            return {}
    
    def _calculate_fast_metrics(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived metrics quickly from profile data"""
        try:
            basic_info = profile.get("basic_info", {})
            repositories = profile.get("repositories", {})
            contribution_stats = profile.get("contribution_stats", {})
            
            # Calculate key metrics
            account_age_days = 0
            if basic_info.get("created_at"):
                created_date = datetime.fromisoformat(basic_info["created_at"].replace("Z", "+00:00"))
                account_age_days = (datetime.now(created_date.tzinfo) - created_date).days
            
            metrics = {
                "account_age_days": account_age_days,
                "account_age_years": round(account_age_days / 365.25, 1),
                "repos_per_year": 0,
                "stars_per_repo": 0,
                "contribution_consistency": 0,
                "overall_activity_score": 0
            }
            
            # Calculate rates
            if account_age_days > 0:
                total_repos = repositories.get("total_repositories", 0)
                metrics["repos_per_year"] = round((total_repos / account_age_days) * 365.25, 2)
            
            if repositories.get("analyzed_repositories", 0) > 0:
                total_stars = repositories.get("total_stars", 0)
                metrics["stars_per_repo"] = round(total_stars / repositories["analyzed_repositories"], 2)
            
            # Calculate contribution consistency (simplified)
            total_contributions = contribution_stats.get("total_contributions", 0)
            if account_age_days > 0:
                metrics["contribution_consistency"] = round(total_contributions / max(account_age_days, 1), 2)
            
            # Calculate overall activity score (0-100)
            score_components = [
                min(total_contributions / 1000, 1) * 30,  # Contributions (max 30 points)
                min(repositories.get("total_stars", 0) / 100, 1) * 25,  # Stars (max 25 points)
                min(repositories.get("total_repositories", 0) / 50, 1) * 20,  # Repos (max 20 points)
                min(basic_info.get("followers", 0) / 100, 1) * 15,  # Followers (max 15 points)
                min(contribution_stats.get("current_streak", 0) / 30, 1) * 10  # Streak (max 10 points)
            ]
            
            metrics["overall_activity_score"] = round(sum(score_components), 1)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating fast metrics: {e}")
            return {}
    
    async def get_repository_fast_analysis(self, repo_full_name: str) -> Dict[str, Any]:
        """Get fast repository analysis with minimal API calls"""
        try:
            repo = self.github.get_repo(repo_full_name)
            
            # Get only essential repository data
            analysis = {
                "basic_info": {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "language": repo.language,
                    "stargazers_count": repo.stargazers_count,
                    "forks_count": repo.forks_count,
                    "size": repo.size,
                    "created_at": repo.created_at.isoformat(),
                    "updated_at": repo.updated_at.isoformat(),
                    "html_url": repo.html_url
                },
                "quick_metrics": {
                    "is_popular": repo.stargazers_count >= 10,
                    "is_active": (datetime.now() - repo.updated_at.replace(tzinfo=None)).days <= 90,
                    "has_description": bool(repo.description),
                    "has_license": bool(repo.license),
                    "fork_ratio": repo.forks_count / max(repo.stargazers_count, 1)
                },
                "analysis_type": "fast",
                "analysis_date": datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting fast repository analysis: {e}")
            return {"error": str(e)}
    
    async def check_rate_limits_fast(self) -> Dict[str, Any]:
        """Quick rate limit check"""
        try:
            rate_limit = self.github.get_rate_limit()
            
            return {
                "core_remaining": getattr(rate_limit.core, 'remaining', 5000),
                "core_limit": getattr(rate_limit.core, 'limit', 5000),
                "can_proceed": getattr(rate_limit.core, 'remaining', 5000) > 100,
                "reset_time": getattr(rate_limit.core, 'reset', datetime.now()).isoformat()
            }
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}")
            return {"can_proceed": True, "core_remaining": 1000}