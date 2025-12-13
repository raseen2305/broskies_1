"""
Enhanced GitHub GraphQL Client Service

This service provides GraphQL API integration for complex GitHub data queries
including contribution calendars, repository relationships, and detailed analytics.
"""

import asyncio
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

class GitHubGraphQLClient:
    """Enhanced GitHub GraphQL client for complex data queries"""
    
    def __init__(self, github_token: str):
        self.token = github_token
        self.headers = {
            'Authorization': f'Bearer {github_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.github.v4+json'
        }
        self.endpoint = 'https://api.github.com/graphql'
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = None
    
    async def execute_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a GraphQL query with error handling and rate limiting"""
        try:
            # Check rate limit before making request
            await self._check_rate_limit()
            
            payload = {
                'query': query,
                'variables': variables or {}
            }
            
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            # Update rate limit info from response headers
            self._update_rate_limit_info(response)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for GraphQL errors
                if 'errors' in data:
                    logger.error(f"GraphQL errors: {data['errors']}")
                    raise Exception(f"GraphQL query failed: {data['errors']}")
                
                return data.get('data', {})
            else:
                logger.error(f"GraphQL request failed with status {response.status_code}: {response.text}")
                raise Exception(f"GraphQL request failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"GraphQL query execution failed: {e}")
            raise Exception(f"GraphQL query failed: {str(e)}")
    
    async def get_contribution_calendar(self, username: str, from_date: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive contribution calendar data using GraphQL"""
        try:
            # Calculate date range (default to last year)
            if not from_date:
                from_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            query = """
            query($username: String!, $from: DateTime!) {
                user(login: $username) {
                    contributionsCollection(from: $from) {
                        totalCommitContributions
                        totalIssueContributions
                        totalPullRequestContributions
                        totalPullRequestReviewContributions
                        totalRepositoryContributions
                        contributionCalendar {
                            totalContributions
                            weeks {
                                contributionDays {
                                    contributionCount
                                    date
                                    weekday
                                    color
                                }
                            }
                        }
                        commitContributionsByRepository(maxRepositories: 25) {
                            repository {
                                name
                                owner {
                                    login
                                }
                                url
                                primaryLanguage {
                                    name
                                    color
                                }
                            }
                            contributions(first: 100) {
                                totalCount
                            }
                        }
                        pullRequestContributionsByRepository(maxRepositories: 25) {
                            repository {
                                name
                                owner {
                                    login
                                }
                                url
                            }
                            contributions(first: 100) {
                                totalCount
                            }
                        }
                    }
                    repositoriesContributedTo(first: 100, contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]) {
                        totalCount
                        nodes {
                            name
                            owner {
                                login
                            }
                            url
                            primaryLanguage {
                                name
                                color
                            }
                            stargazerCount
                            forkCount
                        }
                    }
                }
            }
            """
            
            variables = {
                "username": username,
                "from": from_date
            }
            
            data = await self.execute_query(query, variables)
            
            if not data.get('user'):
                raise Exception(f"User '{username}' not found")
            
            contributions = data['user']['contributionsCollection']
            calendar = contributions['contributionCalendar']
            
            # Process calendar data
            calendar_data = []
            contribution_levels = defaultdict(int)
            
            for week in calendar['weeks']:
                for day in week['contributionDays']:
                    calendar_data.append({
                        'date': day['date'],
                        'count': day['contributionCount'],
                        'weekday': day['weekday'],
                        'level': self._get_contribution_level(day['contributionCount']),
                        'color': day.get('color', '#ebedf0')
                    })
                    contribution_levels[day['contributionCount']] += 1
            
            # Calculate streaks and patterns
            streaks = self._calculate_contribution_streaks(calendar_data)
            patterns = self._analyze_contribution_patterns(calendar_data)
            
            # Process repository contributions
            commit_repos = []
            for repo_contrib in contributions.get('commitContributionsByRepository', []):
                repo = repo_contrib['repository']
                commit_repos.append({
                    'name': repo['name'],
                    'owner': repo['owner']['login'],
                    'url': repo['url'],
                    'language': repo['primaryLanguage']['name'] if repo.get('primaryLanguage') else None,
                    'language_color': repo['primaryLanguage']['color'] if repo.get('primaryLanguage') else None,
                    'contributions': repo_contrib['contributions']['totalCount']
                })
            
            pr_repos = []
            for repo_contrib in contributions.get('pullRequestContributionsByRepository', []):
                repo = repo_contrib['repository']
                pr_repos.append({
                    'name': repo['name'],
                    'owner': repo['owner']['login'],
                    'url': repo['url'],
                    'contributions': repo_contrib['contributions']['totalCount']
                })
            
            # Process contributed repositories
            contributed_repos = []
            for repo in data['user']['repositoriesContributedTo'].get('nodes', []):
                contributed_repos.append({
                    'name': repo['name'],
                    'owner': repo['owner']['login'],
                    'url': repo['url'],
                    'language': repo['primaryLanguage']['name'] if repo.get('primaryLanguage') else None,
                    'language_color': repo['primaryLanguage']['color'] if repo.get('primaryLanguage') else None,
                    'stars': repo['stargazerCount'],
                    'forks': repo['forkCount']
                })
            
            return {
                "total_contributions": calendar['totalContributions'],
                "total_commits": contributions['totalCommitContributions'],
                "total_issues": contributions['totalIssueContributions'],
                "total_pull_requests": contributions['totalPullRequestContributions'],
                "total_reviews": contributions['totalPullRequestReviewContributions'],
                "total_repositories": contributions['totalRepositoryContributions'],
                "contributed_to_count": data['user']['repositoriesContributedTo']['totalCount'],
                "calendar_data": calendar_data,
                "contribution_streaks": streaks,
                "contribution_patterns": patterns,
                "contribution_levels": dict(contribution_levels),
                "commit_repositories": commit_repos,
                "pull_request_repositories": pr_repos,
                "contributed_repositories": contributed_repos,
                "data_source": "graphql",
                "query_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get contribution calendar for {username}: {e}")
            raise Exception(f"Contribution calendar query failed: {str(e)}")
    
    async def get_repository_details(self, owner: str, name: str) -> Dict[str, Any]:
        """Get detailed repository information including PRs, issues, and relationships"""
        try:
            query = """
            query($owner: String!, $name: String!) {
                repository(owner: $owner, name: $name) {
                    id
                    name
                    description
                    url
                    homepageUrl
                    createdAt
                    updatedAt
                    pushedAt
                    stargazerCount
                    forkCount
                    watchers {
                        totalCount
                    }
                    issues(states: [OPEN, CLOSED], first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
                        totalCount
                        nodes {
                            number
                            title
                            state
                            createdAt
                            updatedAt
                            closedAt
                            author {
                                login
                            }
                            labels(first: 10) {
                                nodes {
                                    name
                                    color
                                }
                            }
                            assignees(first: 5) {
                                nodes {
                                    login
                                }
                            }
                            url
                        }
                    }
                    pullRequests(states: [OPEN, CLOSED, MERGED], first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
                        totalCount
                        nodes {
                            number
                            title
                            state
                            createdAt
                            updatedAt
                            closedAt
                            mergedAt
                            merged
                            author {
                                login
                            }
                            baseRefName
                            headRefName
                            additions
                            deletions
                            changedFiles
                            reviews(first: 10) {
                                totalCount
                                nodes {
                                    state
                                    author {
                                        login
                                    }
                                    createdAt
                                }
                            }
                            url
                        }
                    }
                    releases(first: 20, orderBy: {field: CREATED_AT, direction: DESC}) {
                        totalCount
                        nodes {
                            name
                            tagName
                            createdAt
                            publishedAt
                            isPrerelease
                            url
                        }
                    }
                    collaborators(first: 50) {
                        totalCount
                        nodes {
                            login
                            avatarUrl
                            url
                        }
                    }
                    languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
                        totalSize
                        edges {
                            size
                            node {
                                name
                                color
                            }
                        }
                    }
                    repositoryTopics(first: 20) {
                        nodes {
                            topic {
                                name
                            }
                        }
                    }
                    licenseInfo {
                        name
                        key
                        url
                    }
                    primaryLanguage {
                        name
                        color
                    }
                    defaultBranchRef {
                        name
                    }
                    isPrivate
                    isFork
                    isArchived
                    isTemplate
                    hasIssuesEnabled
                    hasProjectsEnabled
                    hasWikiEnabled
                    hasDiscussionsEnabled
                }
            }
            """
            
            variables = {
                "owner": owner,
                "name": name
            }
            
            data = await self.execute_query(query, variables)
            
            if not data.get('repository'):
                raise Exception(f"Repository '{owner}/{name}' not found")
            
            repo = data['repository']
            
            # Process issues
            issues_data = {
                "total_count": repo['issues']['totalCount'],
                "open_count": len([issue for issue in repo['issues']['nodes'] if issue['state'] == 'OPEN']),
                "closed_count": len([issue for issue in repo['issues']['nodes'] if issue['state'] == 'CLOSED']),
                "recent_issues": []
            }
            
            for issue in repo['issues']['nodes'][:10]:
                issues_data["recent_issues"].append({
                    "number": issue['number'],
                    "title": issue['title'],
                    "state": issue['state'],
                    "created_at": issue['createdAt'],
                    "updated_at": issue['updatedAt'],
                    "closed_at": issue.get('closedAt'),
                    "author": issue['author']['login'] if issue.get('author') else None,
                    "labels": [label['name'] for label in issue['labels']['nodes']],
                    "assignees": [assignee['login'] for assignee in issue['assignees']['nodes']],
                    "url": issue['url']
                })
            
            # Process pull requests
            prs_data = {
                "total_count": repo['pullRequests']['totalCount'],
                "open_count": len([pr for pr in repo['pullRequests']['nodes'] if pr['state'] == 'OPEN']),
                "closed_count": len([pr for pr in repo['pullRequests']['nodes'] if pr['state'] == 'CLOSED']),
                "merged_count": len([pr for pr in repo['pullRequests']['nodes'] if pr['merged']]),
                "recent_prs": []
            }
            
            for pr in repo['pullRequests']['nodes'][:10]:
                prs_data["recent_prs"].append({
                    "number": pr['number'],
                    "title": pr['title'],
                    "state": pr['state'],
                    "created_at": pr['createdAt'],
                    "updated_at": pr['updatedAt'],
                    "closed_at": pr.get('closedAt'),
                    "merged_at": pr.get('mergedAt'),
                    "merged": pr['merged'],
                    "author": pr['author']['login'] if pr.get('author') else None,
                    "base_ref": pr['baseRefName'],
                    "head_ref": pr['headRefName'],
                    "additions": pr.get('additions', 0),
                    "deletions": pr.get('deletions', 0),
                    "changed_files": pr.get('changedFiles', 0),
                    "review_count": pr['reviews']['totalCount'],
                    "url": pr['url']
                })
            
            # Process languages
            languages = {}
            total_size = repo['languages']['totalSize']
            for edge in repo['languages']['edges']:
                lang_name = edge['node']['name']
                lang_size = edge['size']
                languages[lang_name] = {
                    "size": lang_size,
                    "percentage": round((lang_size / total_size) * 100, 2) if total_size > 0 else 0,
                    "color": edge['node']['color']
                }
            
            # Process topics
            topics = [topic['topic']['name'] for topic in repo['repositoryTopics']['nodes']]
            
            # Process collaborators
            collaborators = []
            for collab in repo['collaborators']['nodes']:
                collaborators.append({
                    "login": collab['login'],
                    "avatar_url": collab['avatarUrl'],
                    "url": collab['url']
                })
            
            # Process releases
            releases_data = {
                "total_count": repo['releases']['totalCount'],
                "latest_release": None,
                "recent_releases": []
            }
            
            if repo['releases']['nodes']:
                latest = repo['releases']['nodes'][0]
                releases_data["latest_release"] = {
                    "name": latest['name'],
                    "tag_name": latest['tagName'],
                    "created_at": latest['createdAt'],
                    "published_at": latest['publishedAt'],
                    "is_prerelease": latest['isPrerelease'],
                    "url": latest['url']
                }
                
                for release in repo['releases']['nodes'][:5]:
                    releases_data["recent_releases"].append({
                        "name": release['name'],
                        "tag_name": release['tagName'],
                        "created_at": release['createdAt'],
                        "published_at": release['publishedAt'],
                        "is_prerelease": release['isPrerelease'],
                        "url": release['url']
                    })
            
            return {
                "basic_info": {
                    "id": repo['id'],
                    "name": repo['name'],
                    "description": repo['description'],
                    "url": repo['url'],
                    "homepage_url": repo['homepageUrl'],
                    "created_at": repo['createdAt'],
                    "updated_at": repo['updatedAt'],
                    "pushed_at": repo['pushedAt'],
                    "stargazer_count": repo['stargazerCount'],
                    "fork_count": repo['forkCount'],
                    "watchers_count": repo['watchers']['totalCount'],
                    "primary_language": repo['primaryLanguage']['name'] if repo.get('primaryLanguage') else None,
                    "default_branch": repo['defaultBranchRef']['name'] if repo.get('defaultBranchRef') else 'main',
                    "is_private": repo['isPrivate'],
                    "is_fork": repo['isFork'],
                    "is_archived": repo['isArchived'],
                    "is_template": repo['isTemplate'],
                    "has_issues": repo['hasIssuesEnabled'],
                    "has_projects": repo['hasProjectsEnabled'],
                    "has_wiki": repo['hasWikiEnabled'],
                    "has_discussions": repo['hasDiscussionsEnabled']
                },
                "languages": languages,
                "topics": topics,
                "license": {
                    "name": repo['licenseInfo']['name'],
                    "key": repo['licenseInfo']['key'],
                    "url": repo['licenseInfo']['url']
                } if repo.get('licenseInfo') else None,
                "issues": issues_data,
                "pull_requests": prs_data,
                "releases": releases_data,
                "collaborators": {
                    "total_count": repo['collaborators']['totalCount'],
                    "collaborators": collaborators
                },
                "data_source": "graphql",
                "query_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get repository details for {owner}/{name}: {e}")
            raise Exception(f"Repository details query failed: {str(e)}")
    
    async def get_user_organizations(self, username: str) -> Dict[str, Any]:
        """Get user's organization memberships and details"""
        try:
            query = """
            query($username: String!) {
                user(login: $username) {
                    organizations(first: 50) {
                        totalCount
                        nodes {
                            login
                            name
                            description
                            url
                            avatarUrl
                            websiteUrl
                            location
                            createdAt
                            repositories {
                                totalCount
                            }
                            membersWithRole {
                                totalCount
                            }
                        }
                    }
                }
            }
            """
            
            variables = {"username": username}
            data = await self.execute_query(query, variables)
            
            if not data.get('user'):
                raise Exception(f"User '{username}' not found")
            
            orgs_data = data['user']['organizations']
            organizations = []
            
            for org in orgs_data['nodes']:
                organizations.append({
                    "login": org['login'],
                    "name": org['name'],
                    "description": org['description'],
                    "url": org['url'],
                    "avatar_url": org['avatarUrl'],
                    "website_url": org['websiteUrl'],
                    "location": org['location'],
                    "created_at": org['createdAt'],
                    "public_repos": org['repositories']['totalCount'],
                    "members_count": org['membersWithRole']['totalCount']
                })
            
            return {
                "total_count": orgs_data['totalCount'],
                "organizations": organizations,
                "data_source": "graphql",
                "query_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get organizations for {username}: {e}")
            raise Exception(f"Organizations query failed: {str(e)}")
    
    def _get_contribution_level(self, count: int) -> int:
        """Convert contribution count to level (0-4)"""
        if count == 0:
            return 0
        elif count <= 3:
            return 1
        elif count <= 6:
            return 2
        elif count <= 9:
            return 3
        else:
            return 4
    
    def _calculate_contribution_streaks(self, calendar_data: List[Dict]) -> Dict[str, Any]:
        """Calculate contribution streaks from calendar data"""
        if not calendar_data:
            return {"current_streak": 0, "longest_streak": 0, "streak_ranges": []}
        
        # Sort by date
        sorted_data = sorted(calendar_data, key=lambda x: x['date'])
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        streak_ranges = []
        streak_start = None
        
        # Calculate streaks
        for i, day in enumerate(sorted_data):
            if day['count'] > 0:
                if temp_streak == 0:
                    streak_start = day['date']
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                if temp_streak > 0:
                    streak_ranges.append({
                        "start": streak_start,
                        "end": sorted_data[i-1]['date'] if i > 0 else streak_start,
                        "length": temp_streak
                    })
                temp_streak = 0
        
        # Handle streak that continues to the end
        if temp_streak > 0:
            streak_ranges.append({
                "start": streak_start,
                "end": sorted_data[-1]['date'],
                "length": temp_streak
            })
        
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
            "longest_streak": longest_streak,
            "streak_ranges": sorted(streak_ranges, key=lambda x: x['length'], reverse=True)[:10]
        }
    
    def _analyze_contribution_patterns(self, calendar_data: List[Dict]) -> Dict[str, Any]:
        """Analyze contribution patterns by day of week and time periods"""
        if not calendar_data:
            return {}
        
        weekday_contributions = defaultdict(int)
        weekday_counts = defaultdict(int)
        monthly_contributions = defaultdict(int)
        
        for day in calendar_data:
            date_obj = datetime.fromisoformat(day['date']).date()
            weekday = date_obj.weekday()  # 0 = Monday, 6 = Sunday
            month_key = date_obj.strftime('%Y-%m')
            
            weekday_contributions[weekday] += day['count']
            weekday_counts[weekday] += 1
            monthly_contributions[month_key] += day['count']
        
        # Calculate average contributions per weekday
        weekday_averages = {}
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for weekday in range(7):
            if weekday_counts[weekday] > 0:
                weekday_averages[weekday_names[weekday]] = round(
                    weekday_contributions[weekday] / weekday_counts[weekday], 2
                )
            else:
                weekday_averages[weekday_names[weekday]] = 0
        
        # Find most active day
        most_active_day = max(weekday_averages.items(), key=lambda x: x[1])
        
        # Calculate monthly trends
        monthly_trends = dict(monthly_contributions)
        
        return {
            "weekday_averages": weekday_averages,
            "most_active_day": {
                "day": most_active_day[0],
                "average_contributions": most_active_day[1]
            },
            "monthly_trends": monthly_trends,
            "total_active_days": len([day for day in calendar_data if day['count'] > 0]),
            "total_days": len(calendar_data)
        }
    
    async def _check_rate_limit(self):
        """Check and handle GraphQL API rate limits"""
        if self.rate_limit_remaining <= 10:
            if self.rate_limit_reset:
                wait_time = (self.rate_limit_reset - datetime.now()).total_seconds()
                if wait_time > 0:
                    logger.warning(f"GraphQL rate limit low, waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time + 1)
    
    def _update_rate_limit_info(self, response):
        """Update rate limit information from response headers"""
        try:
            if 'X-RateLimit-Remaining' in response.headers:
                self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
            
            if 'X-RateLimit-Reset' in response.headers:
                reset_timestamp = int(response.headers['X-RateLimit-Reset'])
                self.rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
        except (ValueError, KeyError) as e:
            logger.debug(f"Could not parse rate limit headers: {e}")