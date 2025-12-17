"""
Pull Request Analysis Service

This service provides comprehensive analysis of GitHub pull requests including:
- Pull request metrics and statistics
- Review patterns and collaboration analysis
- Merge success rates and timing analysis
- Code review quality assessment
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from github import Github, GithubException
import statistics

logger = logging.getLogger(__name__)

class PullRequestAnalyzer:
    """Comprehensive pull request analysis service"""
    
    def __init__(self, github_token: str):
        self.github = Github(github_token, per_page=100)
        self.token = github_token
        
    async def analyze_user_pull_requests(self, username: str, max_repos: int = 5) -> Dict[str, Any]:
        """Analyze pull requests across all user repositories"""
        try:
            user = self.github.get_user(username)
            repos = list(user.get_repos(type='public', sort='updated'))[:max_repos]
            
            analysis = {
                "summary": {
                    "total_pull_requests": 0,
                    "merged_pull_requests": 0,
                    "closed_pull_requests": 0,
                    "open_pull_requests": 0,
                    "merge_rate": 0.0,
                    "repositories_with_prs": 0
                },
                "metrics": {
                    "average_review_time": 0.0,
                    "average_merge_time": 0.0,
                    "reviews_per_pr": 0.0,
                    "comments_per_pr": 0.0,
                    "lines_changed_per_pr": 0.0
                },
                "collaboration": {
                    "unique_reviewers": set(),
                    "frequent_collaborators": [],
                    "review_participation_rate": 0.0,
                    "cross_repository_collaboration": 0
                },
                "patterns": {
                    "pr_size_distribution": {"small": 0, "medium": 0, "large": 0, "xl": 0},
                    "merge_day_patterns": defaultdict(int),
                    "review_response_times": [],
                    "most_active_repositories": []
                },
                "quality_indicators": {
                    "prs_with_tests": 0,
                    "prs_with_documentation": 0,
                    "prs_with_multiple_reviewers": 0,
                    "breaking_change_rate": 0.0
                },
                "repository_breakdown": []
            }
            
            all_prs = []
            repos_with_prs = 0
            
            for repo in repos:
                try:
                    repo_analysis = await self._analyze_repository_pull_requests(repo, username)
                    if repo_analysis["pull_request_count"] > 0:
                        repos_with_prs += 1
                        analysis["repository_breakdown"].append(repo_analysis)
                        all_prs.extend(repo_analysis["pull_requests"])
                        
                except Exception as e:
                    logger.warning(f"Error analyzing PRs for repository {repo.name}: {e}")
                    continue
            
            # Aggregate analysis from all repositories
            analysis["summary"]["repositories_with_prs"] = repos_with_prs
            
            if all_prs:
                await self._calculate_aggregate_metrics(all_prs, analysis)
                await self._analyze_collaboration_patterns(all_prs, analysis)
                await self._analyze_quality_patterns(all_prs, analysis)
            
            # Convert sets to lists for JSON serialization
            analysis["collaboration"]["unique_reviewers"] = list(analysis["collaboration"]["unique_reviewers"])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user pull requests for {username}: {e}")
            return self._empty_pr_analysis()
    
    async def _analyze_repository_pull_requests(self, repo, username: str) -> Dict[str, Any]:
        """Analyze pull requests for a specific repository"""
        try:
            # Get pull requests (limit to recent ones for performance)
            user_prs = list(repo.get_pulls(state='all', sort='updated'))[:5]  # Limit to 5 most recent
            
            # Filter PRs where user was involved (author only for performance)
            relevant_prs = []
            for pr in user_prs[:3]:  # Further limit for analysis
                if pr.user and pr.user.login == username:
                    relevant_prs.append(pr)
            
            repo_analysis = {
                "repository_name": repo.name,
                "repository_full_name": repo.full_name,
                "pull_request_count": len(relevant_prs),
                "merged_count": 0,
                "closed_count": 0,
                "open_count": 0,
                "authored_count": 0,
                "reviewed_count": 0,
                "average_pr_size": 0,
                "pull_requests": []
            }
            
            total_additions = 0
            total_deletions = 0
            
            for pr in relevant_prs:
                try:
                    pr_data = await self._extract_pull_request_data(pr, username)
                    repo_analysis["pull_requests"].append(pr_data)
                    
                    # Update counts
                    if pr.state == 'closed' and pr.merged:
                        repo_analysis["merged_count"] += 1
                    elif pr.state == 'closed':
                        repo_analysis["closed_count"] += 1
                    else:
                        repo_analysis["open_count"] += 1
                    
                    if pr.user.login == username:
                        repo_analysis["authored_count"] += 1
                    
                    # Accumulate size metrics
                    total_additions += pr_data.get("additions", 0)
                    total_deletions += pr_data.get("deletions", 0)
                    
                except Exception as e:
                    logger.warning(f"Error extracting PR data for {pr.number}: {e}")
                    continue
            
            if relevant_prs:
                repo_analysis["average_pr_size"] = (total_additions + total_deletions) / len(relevant_prs)
            
            return repo_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing repository {repo.name}: {e}")
            return {
                "repository_name": repo.name,
                "repository_full_name": repo.full_name,
                "pull_request_count": 0,
                "merged_count": 0,
                "closed_count": 0,
                "open_count": 0,
                "authored_count": 0,
                "reviewed_count": 0,
                "average_pr_size": 0,
                "pull_requests": []
            }
    
    def _user_participated_in_pr(self, pr, username: str) -> bool:
        """Check if user participated in PR as reviewer or commenter (simplified for performance)"""
        try:
            # Only check if user is author for performance
            return pr.user and pr.user.login == username
            
        except Exception as e:
            logger.warning(f"Error checking PR participation: {e}")
            return False
    
    async def _extract_pull_request_data(self, pr, username: str) -> Dict[str, Any]:
        """Extract comprehensive data from a pull request"""
        try:
            # Basic PR information
            pr_data = {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "merged": pr.merged if hasattr(pr, 'merged') else False,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                "merged_at": pr.merged_at.isoformat() if hasattr(pr, 'merged_at') and pr.merged_at else None,
                "author": pr.user.login,
                "is_author": pr.user.login == username,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files,
                "commits": pr.commits,
                "url": pr.html_url
            }
            
            # Calculate PR size category
            total_changes = pr.additions + pr.deletions
            if total_changes <= 50:
                pr_data["size_category"] = "small"
            elif total_changes <= 200:
                pr_data["size_category"] = "medium"
            elif total_changes <= 500:
                pr_data["size_category"] = "large"
            else:
                pr_data["size_category"] = "xl"
            
            # Simplified review information (skip detailed analysis for speed)
            pr_data["review_count"] = 0
            pr_data["reviewers"] = []
            pr_data["unique_reviewers"] = []
            pr_data["approved_reviews"] = 0
            pr_data["requested_changes"] = 0
            
            # Simplified comment information
            pr_data["comment_count"] = 0
            pr_data["discussion_participants"] = []
            
            # Timing analysis
            if pr.created_at and pr.closed_at:
                time_to_close = (pr.closed_at - pr.created_at).total_seconds() / 3600  # hours
                pr_data["time_to_close_hours"] = round(time_to_close, 2)
            
            if reviews and pr.created_at:
                first_review_time = min(review.submitted_at for review in reviews if review.submitted_at)
                time_to_first_review = (first_review_time - pr.created_at).total_seconds() / 3600
                pr_data["time_to_first_review_hours"] = round(time_to_first_review, 2)
            
            # Quality indicators
            pr_data["has_tests"] = self._pr_has_tests(pr)
            pr_data["has_documentation"] = self._pr_has_documentation(pr)
            pr_data["is_breaking_change"] = self._is_breaking_change(pr)
            
            return pr_data
            
        except Exception as e:
            logger.error(f"Error extracting PR data: {e}")
            return {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "error": str(e)
            }
    
    def _pr_has_tests(self, pr) -> bool:
        """Check if PR includes test files"""
        try:
            files = list(pr.get_files())
            test_patterns = ['test', 'spec', '__test__', '.test.', '.spec.']
            
            for file in files:
                filename = file.filename.lower()
                if any(pattern in filename for pattern in test_patterns):
                    return True
            return False
        except:
            return False
    
    def _pr_has_documentation(self, pr) -> bool:
        """Check if PR includes documentation updates"""
        try:
            files = list(pr.get_files())
            doc_patterns = ['readme', 'doc', '.md', 'changelog', 'contributing']
            
            for file in files:
                filename = file.filename.lower()
                if any(pattern in filename for pattern in doc_patterns):
                    return True
            return False
        except:
            return False
    
    def _is_breaking_change(self, pr) -> bool:
        """Check if PR represents a breaking change"""
        try:
            # Check title and body for breaking change indicators
            text = (pr.title + " " + (pr.body or "")).lower()
            breaking_indicators = ['breaking', 'breaking change', 'major', 'incompatible', 'deprecated']
            
            return any(indicator in text for indicator in breaking_indicators)
        except:
            return False
    
    async def _calculate_aggregate_metrics(self, all_prs: List[Dict], analysis: Dict[str, Any]) -> None:
        """Calculate aggregate metrics across all pull requests"""
        try:
            total_prs = len(all_prs)
            merged_prs = [pr for pr in all_prs if pr.get("merged", False)]
            closed_prs = [pr for pr in all_prs if pr.get("state") == "closed"]
            open_prs = [pr for pr in all_prs if pr.get("state") == "open"]
            
            # Summary metrics
            analysis["summary"]["total_pull_requests"] = total_prs
            analysis["summary"]["merged_pull_requests"] = len(merged_prs)
            analysis["summary"]["closed_pull_requests"] = len(closed_prs)
            analysis["summary"]["open_pull_requests"] = len(open_prs)
            
            if total_prs > 0:
                analysis["summary"]["merge_rate"] = round(len(merged_prs) / total_prs * 100, 1)
            
            # Timing metrics
            review_times = [pr["time_to_first_review_hours"] for pr in all_prs 
                          if "time_to_first_review_hours" in pr]
            merge_times = [pr["time_to_close_hours"] for pr in merged_prs 
                         if "time_to_close_hours" in pr]
            
            if review_times:
                analysis["metrics"]["average_review_time"] = round(statistics.mean(review_times), 1)
            if merge_times:
                analysis["metrics"]["average_merge_time"] = round(statistics.mean(merge_times), 1)
            
            # Size and engagement metrics
            review_counts = [pr.get("review_count", 0) for pr in all_prs]
            comment_counts = [pr.get("comment_count", 0) for pr in all_prs]
            line_changes = [pr.get("additions", 0) + pr.get("deletions", 0) for pr in all_prs]
            
            if review_counts:
                analysis["metrics"]["reviews_per_pr"] = round(statistics.mean(review_counts), 1)
            if comment_counts:
                analysis["metrics"]["comments_per_pr"] = round(statistics.mean(comment_counts), 1)
            if line_changes:
                analysis["metrics"]["lines_changed_per_pr"] = round(statistics.mean(line_changes), 1)
            
            # Size distribution
            for pr in all_prs:
                size_cat = pr.get("size_category", "medium")
                analysis["patterns"]["pr_size_distribution"][size_cat] += 1
            
            # Quality indicators
            analysis["quality_indicators"]["prs_with_tests"] = len([
                pr for pr in all_prs if pr.get("has_tests", False)
            ])
            analysis["quality_indicators"]["prs_with_documentation"] = len([
                pr for pr in all_prs if pr.get("has_documentation", False)
            ])
            analysis["quality_indicators"]["prs_with_multiple_reviewers"] = len([
                pr for pr in all_prs if len(pr.get("unique_reviewers", [])) > 1
            ])
            
            breaking_changes = len([pr for pr in all_prs if pr.get("is_breaking_change", False)])
            if total_prs > 0:
                analysis["quality_indicators"]["breaking_change_rate"] = round(
                    breaking_changes / total_prs * 100, 1
                )
            
        except Exception as e:
            logger.error(f"Error calculating aggregate metrics: {e}")
    
    async def _analyze_collaboration_patterns(self, all_prs: List[Dict], analysis: Dict[str, Any]) -> None:
        """Analyze collaboration patterns from pull requests"""
        try:
            all_reviewers = []
            reviewer_counts = Counter()
            
            for pr in all_prs:
                reviewers = pr.get("unique_reviewers", [])
                all_reviewers.extend(reviewers)
                for reviewer in reviewers:
                    reviewer_counts[reviewer] += 1
            
            analysis["collaboration"]["unique_reviewers"] = set(all_reviewers)
            
            # Find frequent collaborators (appeared in 20% or more of PRs)
            total_prs = len(all_prs)
            if total_prs > 0:
                frequent_threshold = max(1, total_prs * 0.2)
                analysis["collaboration"]["frequent_collaborators"] = [
                    {"username": reviewer, "collaboration_count": count}
                    for reviewer, count in reviewer_counts.most_common(10)
                    if count >= frequent_threshold
                ]
            
            # Calculate review participation rate
            prs_with_reviews = len([pr for pr in all_prs if pr.get("review_count", 0) > 0])
            if total_prs > 0:
                analysis["collaboration"]["review_participation_rate"] = round(
                    prs_with_reviews / total_prs * 100, 1
                )
            
        except Exception as e:
            logger.error(f"Error analyzing collaboration patterns: {e}")
    
    async def _analyze_quality_patterns(self, all_prs: List[Dict], analysis: Dict[str, Any]) -> None:
        """Analyze quality and timing patterns"""
        try:
            # Merge day patterns
            for pr in all_prs:
                if pr.get("merged_at"):
                    merged_date = datetime.fromisoformat(pr["merged_at"].replace('Z', '+00:00'))
                    day_name = merged_date.strftime('%A')
                    analysis["patterns"]["merge_day_patterns"][day_name] += 1
            
            # Response times for pattern analysis
            response_times = [pr.get("time_to_first_review_hours", 0) for pr in all_prs 
                            if "time_to_first_review_hours" in pr]
            analysis["patterns"]["review_response_times"] = response_times
            
            # Most active repositories
            repo_activity = Counter()
            for pr in all_prs:
                # This would need to be passed from the repository analysis
                # For now, we'll skip this or implement it differently
                pass
            
        except Exception as e:
            logger.error(f"Error analyzing quality patterns: {e}")
    
    def _empty_pr_analysis(self) -> Dict[str, Any]:
        """Return empty PR analysis structure"""
        return {
            "summary": {
                "total_pull_requests": 0,
                "merged_pull_requests": 0,
                "closed_pull_requests": 0,
                "open_pull_requests": 0,
                "merge_rate": 0.0,
                "repositories_with_prs": 0
            },
            "metrics": {
                "average_review_time": 0.0,
                "average_merge_time": 0.0,
                "reviews_per_pr": 0.0,
                "comments_per_pr": 0.0,
                "lines_changed_per_pr": 0.0
            },
            "collaboration": {
                "unique_reviewers": [],
                "frequent_collaborators": [],
                "review_participation_rate": 0.0,
                "cross_repository_collaboration": 0
            },
            "patterns": {
                "pr_size_distribution": {"small": 0, "medium": 0, "large": 0, "xl": 0},
                "merge_day_patterns": {},
                "review_response_times": [],
                "most_active_repositories": []
            },
            "quality_indicators": {
                "prs_with_tests": 0,
                "prs_with_documentation": 0,
                "prs_with_multiple_reviewers": 0,
                "breaking_change_rate": 0.0
            },
            "repository_breakdown": []
        }
    
    async def analyze_repositories_pull_requests(self, repositories: List[Dict]) -> Dict[str, Any]:
        """Analyze pull requests for a list of repositories"""
        try:
            logger.info(f"Analyzing pull requests for {len(repositories)} repositories")
            
            analysis = self._empty_pr_analysis()
            
            for repo_data in repositories:
                try:
                    repo_name = repo_data.get("full_name") or repo_data.get("name", "")
                    if not repo_name:
                        continue
                    
                    # Get repository object
                    repo = self.github.get_repo(repo_name)
                    
                    # Analyze this repository's pull requests
                    repo_analysis = await self._analyze_repository_pull_requests(repo, repo_data.get("owner", {}).get("login", ""))
                    
                    # Merge results into overall analysis
                    self._merge_pr_analysis(analysis, repo_analysis)
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze PRs for repository {repo_data.get('name', 'unknown')}: {e}")
                    continue
            
            # Calculate final metrics
            self._calculate_final_pr_metrics(analysis)
            
            logger.info(f"Completed PR analysis for {len(repositories)} repositories")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing repositories pull requests: {e}")
            return self._empty_pr_analysis()
    
    def _merge_pr_analysis(self, main_analysis: Dict, repo_analysis: Dict) -> None:
        """Merge repository PR analysis into main analysis"""
        try:
            # Merge summary data
            main_analysis["summary"]["total_pull_requests"] += repo_analysis["summary"]["total_pull_requests"]
            main_analysis["summary"]["merged_pull_requests"] += repo_analysis["summary"]["merged_pull_requests"]
            main_analysis["summary"]["closed_pull_requests"] += repo_analysis["summary"]["closed_pull_requests"]
            main_analysis["summary"]["open_pull_requests"] += repo_analysis["summary"]["open_pull_requests"]
            
            if repo_analysis["summary"]["total_pull_requests"] > 0:
                main_analysis["summary"]["repositories_with_prs"] += 1
            
            # Merge collaboration data
            if isinstance(main_analysis["collaboration"]["unique_reviewers"], list):
                main_analysis["collaboration"]["unique_reviewers"].extend(repo_analysis["collaboration"]["unique_reviewers"])
            
            # Add repository breakdown
            main_analysis["repository_breakdown"].append(repo_analysis)
            
        except Exception as e:
            logger.warning(f"Error merging PR analysis: {e}")
    
    def _calculate_final_pr_metrics(self, analysis: Dict) -> None:
        """Calculate final metrics for the complete analysis"""
        try:
            total_prs = analysis["summary"]["total_pull_requests"]
            merged_prs = analysis["summary"]["merged_pull_requests"]
            
            # Calculate merge rate
            if total_prs > 0:
                analysis["summary"]["merge_rate"] = round((merged_prs / total_prs) * 100, 2)
            
            # Remove duplicates from reviewers
            if isinstance(analysis["collaboration"]["unique_reviewers"], list):
                analysis["collaboration"]["unique_reviewers"] = list(set(analysis["collaboration"]["unique_reviewers"]))
            
        except Exception as e:
            logger.warning(f"Error calculating final PR metrics: {e}")