"""
Issue Analysis Service

This service provides comprehensive analysis of GitHub issues including:
- Issue metrics and resolution patterns
- Label analysis and categorization
- Response time tracking
- Issue lifecycle analysis
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from github import Github, GithubException
import statistics

logger = logging.getLogger(__name__)

class IssueAnalyzer:
    """Comprehensive issue analysis service"""
    
    def __init__(self, github_token: str):
        self.github = Github(github_token, per_page=100)
        self.token = github_token
        
    async def analyze_user_issues(self, username: str, max_repos: int = 20) -> Dict[str, Any]:
        """Analyze issues across all user repositories"""
        try:
            user = self.github.get_user(username)
            repos = list(user.get_repos(type='public', sort='updated'))[:max_repos]
            
            analysis = {
                "summary": {
                    "total_issues": 0,
                    "open_issues": 0,
                    "closed_issues": 0,
                    "resolution_rate": 0.0,
                    "repositories_with_issues": 0,
                    "issues_created": 0,
                    "issues_participated": 0
                },
                "metrics": {
                    "average_resolution_time": 0.0,
                    "average_response_time": 0.0,
                    "comments_per_issue": 0.0,
                    "assignees_per_issue": 0.0,
                    "labels_per_issue": 0.0
                },
                "patterns": {
                    "issue_types": defaultdict(int),
                    "priority_distribution": defaultdict(int),
                    "resolution_day_patterns": defaultdict(int),
                    "creation_trends": defaultdict(int),
                    "label_frequency": Counter()
                },
                "collaboration": {
                    "unique_assignees": set(),
                    "frequent_collaborators": [],
                    "cross_repository_participation": 0,
                    "community_engagement_score": 0.0
                },
                "quality_indicators": {
                    "issues_with_labels": 0,
                    "issues_with_assignees": 0,
                    "issues_with_milestones": 0,
                    "duplicate_issue_rate": 0.0,
                    "stale_issue_rate": 0.0
                },
                "repository_breakdown": []
            }
            
            all_issues = []
            repos_with_issues = 0
            
            for repo in repos:
                try:
                    repo_analysis = await self._analyze_repository_issues(repo, username)
                    if repo_analysis["issue_count"] > 0:
                        repos_with_issues += 1
                        analysis["repository_breakdown"].append(repo_analysis)
                        all_issues.extend(repo_analysis["issues"])
                        
                except Exception as e:
                    logger.warning(f"Error analyzing issues for repository {repo.name}: {e}")
                    continue
            
            analysis["summary"]["repositories_with_issues"] = repos_with_issues
            
            if all_issues:
                await self._calculate_aggregate_metrics(all_issues, analysis)
                await self._analyze_collaboration_patterns(all_issues, analysis)
                await self._analyze_quality_patterns(all_issues, analysis)
            
            # Convert sets to lists for JSON serialization
            analysis["collaboration"]["unique_assignees"] = list(analysis["collaboration"]["unique_assignees"])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user issues for {username}: {e}")
            return self._empty_issue_analysis()
    
    async def _analyze_repository_issues(self, repo, username: str) -> Dict[str, Any]:
        """Analyze issues for a specific repository"""
        try:
            # Get recent issues only for performance
            all_issues = list(repo.get_issues(state='all', sort='updated'))[:15]  # Limit to 15 most recent
            
            # Filter out pull requests and get issues where user is author
            relevant_issues = []
            for issue in all_issues:
                # Skip pull requests
                if issue.pull_request:
                    continue
                    
                # Only check if user is author for performance
                if issue.user and issue.user.login == username:
                    relevant_issues.append(issue)
            
            repo_analysis = {
                "repository_name": repo.name,
                "repository_full_name": repo.full_name,
                "issue_count": len(relevant_issues),
                "open_count": 0,
                "closed_count": 0,
                "created_count": 0,
                "participated_count": 0,
                "average_resolution_time": 0.0,
                "issues": []
            }
            
            resolution_times = []
            
            for issue in relevant_issues:
                try:
                    issue_data = await self._extract_issue_data(issue, username)
                    repo_analysis["issues"].append(issue_data)
                    
                    # Update counts
                    if issue.state == 'open':
                        repo_analysis["open_count"] += 1
                    else:
                        repo_analysis["closed_count"] += 1
                        if "resolution_time_hours" in issue_data:
                            resolution_times.append(issue_data["resolution_time_hours"])
                    
                    if issue.user.login == username:
                        repo_analysis["created_count"] += 1
                    else:
                        repo_analysis["participated_count"] += 1
                        
                except Exception as e:
                    logger.warning(f"Error extracting issue data for #{issue.number}: {e}")
                    continue
            
            if resolution_times:
                repo_analysis["average_resolution_time"] = statistics.mean(resolution_times)
            
            return repo_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing repository {repo.name}: {e}")
            return {
                "repository_name": repo.name,
                "repository_full_name": repo.full_name,
                "issue_count": 0,
                "open_count": 0,
                "closed_count": 0,
                "created_count": 0,
                "participated_count": 0,
                "average_resolution_time": 0.0,
                "issues": []
            }
    
    def _user_participated_in_issue(self, issue, username: str) -> bool:
        """Check if user participated in issue (simplified for performance)"""
        try:
            # Only check if user is author for performance
            return issue.user and issue.user.login == username
            
        except Exception as e:
            logger.warning(f"Error checking issue participation: {e}")
            return False
    
    async def _extract_issue_data(self, issue, username: str) -> Dict[str, Any]:
        """Extract comprehensive data from an issue"""
        try:
            # Basic issue information
            issue_data = {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                "author": issue.user.login,
                "is_author": issue.user.login == username,
                "body_length": len(issue.body or ""),
                "url": issue.html_url,
                "labels": [label.name for label in issue.labels],
                "assignees": [assignee.login for assignee in issue.assignees] if issue.assignees else [],
                "milestone": issue.milestone.title if issue.milestone else None
            }
            
            # Categorize issue type based on labels and title
            issue_data["issue_type"] = self._categorize_issue_type(issue)
            issue_data["priority"] = self._determine_priority(issue)
            
            # Simplified comment analysis (skip for speed)
            issue_data["comment_count"] = 0
            issue_data["participants"] = [issue.user.login]
            issue_data["user_participated"] = issue.user.login == username
            
            # Simplified timing analysis
            if issue.created_at and issue.closed_at:
                resolution_time = (issue.closed_at - issue.created_at).total_seconds() / 3600  # hours
                issue_data["resolution_time_hours"] = round(resolution_time, 2)
            
            # Quality indicators
            issue_data["has_labels"] = len(issue_data["labels"]) > 0
            issue_data["has_assignees"] = len(issue_data["assignees"]) > 0
            issue_data["has_milestone"] = issue_data["milestone"] is not None
            issue_data["is_stale"] = self._is_stale_issue(issue)
            
            return issue_data
            
        except Exception as e:
            logger.error(f"Error extracting issue data: {e}")
            return {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "error": str(e)
            }
    
    def _categorize_issue_type(self, issue) -> str:
        """Categorize issue type based on labels and content"""
        try:
            labels = [label.name.lower() for label in issue.labels]
            title_body = (issue.title + " " + (issue.body or "")).lower()
            
            # Check labels first
            if any(label in ['bug', 'defect', 'error'] for label in labels):
                return 'bug'
            elif any(label in ['enhancement', 'feature', 'improvement'] for label in labels):
                return 'enhancement'
            elif any(label in ['documentation', 'docs'] for label in labels):
                return 'documentation'
            elif any(label in ['question', 'help', 'support'] for label in labels):
                return 'question'
            
            # Check title/body content
            if any(word in title_body for word in ['bug', 'error', 'broken', 'issue', 'problem']):
                return 'bug'
            elif any(word in title_body for word in ['feature', 'add', 'implement', 'enhancement']):
                return 'enhancement'
            elif any(word in title_body for word in ['documentation', 'readme', 'docs']):
                return 'documentation'
            elif any(word in title_body for word in ['question', 'how', 'help']):
                return 'question'
            
            return 'other'
            
        except Exception:
            return 'other'
    
    def _determine_priority(self, issue) -> str:
        """Determine issue priority based on labels"""
        try:
            labels = [label.name.lower() for label in issue.labels]
            
            if any(label in ['critical', 'urgent', 'high priority', 'p0'] for label in labels):
                return 'high'
            elif any(label in ['medium priority', 'p1'] for label in labels):
                return 'medium'
            elif any(label in ['low priority', 'p2', 'nice to have'] for label in labels):
                return 'low'
            
            # Default priority based on issue type
            issue_type = self._categorize_issue_type(issue)
            if issue_type == 'bug':
                return 'medium'
            elif issue_type == 'enhancement':
                return 'low'
            
            return 'medium'
            
        except Exception:
            return 'medium'
    
    def _is_stale_issue(self, issue) -> bool:
        """Check if issue is stale (no activity for 90+ days)"""
        try:
            if issue.state == 'closed':
                return False
            
            last_activity = max(issue.created_at, issue.updated_at)
            days_since_activity = (datetime.now() - last_activity.replace(tzinfo=None)).days
            
            return days_since_activity > 90
            
        except Exception:
            return False
    
    async def _calculate_aggregate_metrics(self, all_issues: List[Dict], analysis: Dict[str, Any]) -> None:
        """Calculate aggregate metrics across all issues"""
        try:
            total_issues = len(all_issues)
            open_issues = [issue for issue in all_issues if issue.get("state") == "open"]
            closed_issues = [issue for issue in all_issues if issue.get("state") == "closed"]
            created_issues = [issue for issue in all_issues if issue.get("is_author", False)]
            
            # Summary metrics
            analysis["summary"]["total_issues"] = total_issues
            analysis["summary"]["open_issues"] = len(open_issues)
            analysis["summary"]["closed_issues"] = len(closed_issues)
            analysis["summary"]["issues_created"] = len(created_issues)
            analysis["summary"]["issues_participated"] = total_issues - len(created_issues)
            
            if total_issues > 0:
                analysis["summary"]["resolution_rate"] = round(len(closed_issues) / total_issues * 100, 1)
            
            # Timing metrics
            resolution_times = [issue["resolution_time_hours"] for issue in closed_issues 
                              if "resolution_time_hours" in issue]
            response_times = [issue["response_time_hours"] for issue in all_issues 
                            if "response_time_hours" in issue]
            
            if resolution_times:
                analysis["metrics"]["average_resolution_time"] = round(statistics.mean(resolution_times), 1)
            if response_times:
                analysis["metrics"]["average_response_time"] = round(statistics.mean(response_times), 1)
            
            # Engagement metrics
            comment_counts = [issue.get("comment_count", 0) for issue in all_issues]
            assignee_counts = [len(issue.get("assignees", [])) for issue in all_issues]
            label_counts = [len(issue.get("labels", [])) for issue in all_issues]
            
            if comment_counts:
                analysis["metrics"]["comments_per_issue"] = round(statistics.mean(comment_counts), 1)
            if assignee_counts:
                analysis["metrics"]["assignees_per_issue"] = round(statistics.mean(assignee_counts), 1)
            if label_counts:
                analysis["metrics"]["labels_per_issue"] = round(statistics.mean(label_counts), 1)
            
            # Pattern analysis
            for issue in all_issues:
                issue_type = issue.get("issue_type", "other")
                priority = issue.get("priority", "medium")
                
                analysis["patterns"]["issue_types"][issue_type] += 1
                analysis["patterns"]["priority_distribution"][priority] += 1
                
                # Label frequency
                for label in issue.get("labels", []):
                    analysis["patterns"]["label_frequency"][label] += 1
                
                # Creation trends (by month)
                if "created_at" in issue:
                    created_date = datetime.fromisoformat(issue["created_at"].replace('Z', '+00:00'))
                    month_key = created_date.strftime('%Y-%m')
                    analysis["patterns"]["creation_trends"][month_key] += 1
                
                # Resolution day patterns
                if issue.get("closed_at"):
                    closed_date = datetime.fromisoformat(issue["closed_at"].replace('Z', '+00:00'))
                    day_name = closed_date.strftime('%A')
                    analysis["patterns"]["resolution_day_patterns"][day_name] += 1
            
            # Quality indicators
            analysis["quality_indicators"]["issues_with_labels"] = len([
                issue for issue in all_issues if issue.get("has_labels", False)
            ])
            analysis["quality_indicators"]["issues_with_assignees"] = len([
                issue for issue in all_issues if issue.get("has_assignees", False)
            ])
            analysis["quality_indicators"]["issues_with_milestones"] = len([
                issue for issue in all_issues if issue.get("has_milestone", False)
            ])
            
            stale_issues = len([issue for issue in all_issues if issue.get("is_stale", False)])
            if total_issues > 0:
                analysis["quality_indicators"]["stale_issue_rate"] = round(
                    stale_issues / total_issues * 100, 1
                )
            
        except Exception as e:
            logger.error(f"Error calculating aggregate metrics: {e}")
    
    async def _analyze_collaboration_patterns(self, all_issues: List[Dict], analysis: Dict[str, Any]) -> None:
        """Analyze collaboration patterns from issues"""
        try:
            all_assignees = []
            assignee_counts = Counter()
            participant_counts = Counter()
            
            for issue in all_issues:
                assignees = issue.get("assignees", [])
                participants = issue.get("participants", [])
                
                all_assignees.extend(assignees)
                for assignee in assignees:
                    assignee_counts[assignee] += 1
                
                for participant in participants:
                    participant_counts[participant] += 1
            
            analysis["collaboration"]["unique_assignees"] = set(all_assignees)
            
            # Find frequent collaborators
            total_issues = len(all_issues)
            if total_issues > 0:
                frequent_threshold = max(1, total_issues * 0.1)
                analysis["collaboration"]["frequent_collaborators"] = [
                    {"username": participant, "participation_count": count}
                    for participant, count in participant_counts.most_common(10)
                    if count >= frequent_threshold
                ]
            
            # Calculate community engagement score
            unique_participants = len(set(participant_counts.keys()))
            if total_issues > 0:
                analysis["collaboration"]["community_engagement_score"] = round(
                    unique_participants / total_issues * 100, 1
                )
            
        except Exception as e:
            logger.error(f"Error analyzing collaboration patterns: {e}")
    
    async def _analyze_quality_patterns(self, all_issues: List[Dict], analysis: Dict[str, Any]) -> None:
        """Analyze quality and management patterns"""
        try:
            # Convert defaultdicts to regular dicts for JSON serialization
            analysis["patterns"]["issue_types"] = dict(analysis["patterns"]["issue_types"])
            analysis["patterns"]["priority_distribution"] = dict(analysis["patterns"]["priority_distribution"])
            analysis["patterns"]["resolution_day_patterns"] = dict(analysis["patterns"]["resolution_day_patterns"])
            analysis["patterns"]["creation_trends"] = dict(analysis["patterns"]["creation_trends"])
            
            # Get top labels
            analysis["patterns"]["top_labels"] = [
                {"label": label, "count": count}
                for label, count in analysis["patterns"]["label_frequency"].most_common(10)
            ]
            
            # Remove the Counter object
            del analysis["patterns"]["label_frequency"]
            
        except Exception as e:
            logger.error(f"Error analyzing quality patterns: {e}")
    
    def _empty_issue_analysis(self) -> Dict[str, Any]:
        """Return empty issue analysis structure"""
        return {
            "summary": {
                "total_issues": 0,
                "open_issues": 0,
                "closed_issues": 0,
                "resolution_rate": 0.0,
                "repositories_with_issues": 0,
                "issues_created": 0,
                "issues_participated": 0
            },
            "metrics": {
                "average_resolution_time": 0.0,
                "average_response_time": 0.0,
                "comments_per_issue": 0.0,
                "assignees_per_issue": 0.0,
                "labels_per_issue": 0.0
            },
            "patterns": {
                "issue_types": {},
                "priority_distribution": {},
                "resolution_day_patterns": {},
                "creation_trends": {},
                "top_labels": []
            },
            "collaboration": {
                "unique_assignees": [],
                "frequent_collaborators": [],
                "cross_repository_participation": 0,
                "community_engagement_score": 0.0
            },
            "quality_indicators": {
                "issues_with_labels": 0,
                "issues_with_assignees": 0,
                "issues_with_milestones": 0,
                "duplicate_issue_rate": 0.0,
                "stale_issue_rate": 0.0
            },
            "repository_breakdown": []
        }
    
    async def analyze_repositories_issues(self, repositories: List[Dict]) -> Dict[str, Any]:
        """Analyze issues for a list of repositories"""
        try:
            logger.info(f"Analyzing issues for {len(repositories)} repositories")
            
            analysis = self._empty_issue_analysis()
            
            for repo_data in repositories:
                try:
                    repo_name = repo_data.get("full_name") or repo_data.get("name", "")
                    if not repo_name:
                        continue
                    
                    # Get repository object
                    repo = self.github.get_repo(repo_name)
                    
                    # Analyze this repository's issues
                    repo_analysis = await self._analyze_repository_issues(repo, repo_data.get("owner", {}).get("login", ""))
                    
                    # Merge results into overall analysis
                    self._merge_issue_analysis(analysis, repo_analysis)
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze issues for repository {repo_data.get('name', 'unknown')}: {e}")
                    continue
            
            # Calculate final metrics
            self._calculate_final_issue_metrics(analysis)
            
            logger.info(f"Completed issue analysis for {len(repositories)} repositories")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing repositories issues: {e}")
            return self._empty_issue_analysis()
    
    def _merge_issue_analysis(self, main_analysis: Dict, repo_analysis: Dict) -> None:
        """Merge repository issue analysis into main analysis"""
        try:
            # Merge summary data
            main_analysis["summary"]["total_issues"] += repo_analysis["summary"]["total_issues"]
            main_analysis["summary"]["open_issues"] += repo_analysis["summary"]["open_issues"]
            main_analysis["summary"]["closed_issues"] += repo_analysis["summary"]["closed_issues"]
            main_analysis["summary"]["issues_created"] += repo_analysis["summary"]["issues_created"]
            main_analysis["summary"]["issues_participated"] += repo_analysis["summary"]["issues_participated"]
            
            if repo_analysis["summary"]["total_issues"] > 0:
                main_analysis["summary"]["repositories_with_issues"] += 1
            
            # Merge collaboration data
            if isinstance(main_analysis["collaboration"]["unique_assignees"], list):
                main_analysis["collaboration"]["unique_assignees"].extend(repo_analysis["collaboration"]["unique_assignees"])
            
            # Add repository breakdown
            main_analysis["repository_breakdown"].append(repo_analysis)
            
        except Exception as e:
            logger.warning(f"Error merging issue analysis: {e}")
    
    def _calculate_final_issue_metrics(self, analysis: Dict) -> None:
        """Calculate final metrics for the complete analysis"""
        try:
            total_issues = analysis["summary"]["total_issues"]
            closed_issues = analysis["summary"]["closed_issues"]
            
            # Calculate resolution rate
            if total_issues > 0:
                analysis["summary"]["resolution_rate"] = round((closed_issues / total_issues) * 100, 2)
            
            # Remove duplicates from assignees
            if isinstance(analysis["collaboration"]["unique_assignees"], list):
                analysis["collaboration"]["unique_assignees"] = list(set(analysis["collaboration"]["unique_assignees"]))
            
        except Exception as e:
            logger.warning(f"Error calculating final issue metrics: {e}")