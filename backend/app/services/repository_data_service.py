"""
Repository Data Service

Provides utilities for managing repository data including PR/issue/roadmap information.

Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.3
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models.repository import (
    PRStatistics,
    IssueStatistics,
    Roadmap,
    PullRequest,
    Issue,
    Milestone,
    Project
)

logger = logging.getLogger(__name__)


class RepositoryDataService:
    """Service for managing repository data with PR/issue/roadmap support"""
    
    @staticmethod
    def create_pr_statistics(
        prs: List[Dict[str, Any]],
        limit_recent: int = 10
    ) -> Optional[PRStatistics]:
        """
        Create PR statistics from raw PR data.
        
        Args:
            prs: List of pull request dictionaries
            limit_recent: Number of recent PRs to include
            
        Returns:
            PRStatistics object or None if no PRs
        """
        if not prs:
            return None
        
        try:
            total = len(prs)
            open_count = sum(1 for pr in prs if pr.get('state') == 'open')
            closed_count = sum(1 for pr in prs if pr.get('state') == 'closed' and not pr.get('merged_at'))
            merged_count = sum(1 for pr in prs if pr.get('merged_at'))
            
            # Convert recent PRs to PullRequest objects
            recent_prs = []
            for pr_data in prs[:limit_recent]:
                try:
                    pr = PullRequest(
                        number=pr_data.get('number', 0),
                        title=pr_data.get('title', ''),
                        state=pr_data.get('state', 'open'),
                        created_at=pr_data.get('created_at', datetime.utcnow()),
                        updated_at=pr_data.get('updated_at', datetime.utcnow()),
                        closed_at=pr_data.get('closed_at'),
                        merged_at=pr_data.get('merged_at'),
                        user=pr_data.get('user', {}).get('login', 'unknown'),
                        html_url=pr_data.get('html_url', ''),
                        additions=pr_data.get('additions', 0),
                        deletions=pr_data.get('deletions', 0),
                        changed_files=pr_data.get('changed_files', 0),
                        comments=pr_data.get('comments', 0),
                        review_comments=pr_data.get('review_comments', 0),
                        commits=pr_data.get('commits', 0)
                    )
                    recent_prs.append(pr)
                except Exception as e:
                    logger.warning(f"Failed to parse PR {pr_data.get('number')}: {e}")
                    continue
            
            # Calculate average time to merge
            merge_times = []
            for pr in prs:
                if pr.get('merged_at') and pr.get('created_at'):
                    try:
                        created = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                        merged = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                        hours = (merged - created).total_seconds() / 3600
                        merge_times.append(hours)
                    except Exception:
                        continue
            
            avg_time_to_merge = sum(merge_times) / len(merge_times) if merge_times else None
            
            # Calculate average additions/deletions
            additions = [pr.get('additions', 0) for pr in prs if pr.get('additions')]
            deletions = [pr.get('deletions', 0) for pr in prs if pr.get('deletions')]
            
            avg_additions = sum(additions) / len(additions) if additions else None
            avg_deletions = sum(deletions) / len(deletions) if deletions else None
            
            return PRStatistics(
                total=total,
                open=open_count,
                closed=closed_count,
                merged=merged_count,
                recent_prs=recent_prs,
                avg_time_to_merge_hours=avg_time_to_merge,
                avg_additions=avg_additions,
                avg_deletions=avg_deletions
            )
            
        except Exception as e:
            logger.error(f"Failed to create PR statistics: {e}")
            return None
    
    @staticmethod
    def create_issue_statistics(
        issues: List[Dict[str, Any]],
        limit_recent: int = 10
    ) -> Optional[IssueStatistics]:
        """
        Create issue statistics from raw issue data.
        
        Args:
            issues: List of issue dictionaries (excluding PRs)
            limit_recent: Number of recent issues to include
            
        Returns:
            IssueStatistics object or None if no issues
        """
        if not issues:
            return None
        
        try:
            total = len(issues)
            open_count = sum(1 for issue in issues if issue.get('state') == 'open')
            closed_count = sum(1 for issue in issues if issue.get('state') == 'closed')
            
            # Convert recent issues to Issue objects
            recent_issues = []
            for issue_data in issues[:limit_recent]:
                try:
                    issue = Issue(
                        number=issue_data.get('number', 0),
                        title=issue_data.get('title', ''),
                        state=issue_data.get('state', 'open'),
                        created_at=issue_data.get('created_at', datetime.utcnow()),
                        updated_at=issue_data.get('updated_at', datetime.utcnow()),
                        closed_at=issue_data.get('closed_at'),
                        user=issue_data.get('user', {}).get('login', 'unknown'),
                        html_url=issue_data.get('html_url', ''),
                        comments=issue_data.get('comments', 0),
                        labels=[label.get('name', '') for label in issue_data.get('labels', [])]
                    )
                    recent_issues.append(issue)
                except Exception as e:
                    logger.warning(f"Failed to parse issue {issue_data.get('number')}: {e}")
                    continue
            
            # Calculate average time to close
            close_times = []
            for issue in issues:
                if issue.get('closed_at') and issue.get('created_at'):
                    try:
                        created = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
                        closed = datetime.fromisoformat(issue['closed_at'].replace('Z', '+00:00'))
                        hours = (closed - created).total_seconds() / 3600
                        close_times.append(hours)
                    except Exception:
                        continue
            
            avg_time_to_close = sum(close_times) / len(close_times) if close_times else None
            
            # Calculate label distribution
            labels_distribution = {}
            for issue in issues:
                for label in issue.get('labels', []):
                    label_name = label.get('name', 'unknown')
                    labels_distribution[label_name] = labels_distribution.get(label_name, 0) + 1
            
            return IssueStatistics(
                total=total,
                open=open_count,
                closed=closed_count,
                recent_issues=recent_issues,
                avg_time_to_close_hours=avg_time_to_close,
                labels_distribution=labels_distribution
            )
            
        except Exception as e:
            logger.error(f"Failed to create issue statistics: {e}")
            return None
    
    @staticmethod
    def create_roadmap(
        milestones: List[Dict[str, Any]],
        projects: List[Dict[str, Any]]
    ) -> Optional[Roadmap]:
        """
        Create roadmap from milestones and projects data.
        
        Args:
            milestones: List of milestone dictionaries
            projects: List of project dictionaries
            
        Returns:
            Roadmap object or None if no data
        """
        if not milestones and not projects:
            return None
        
        try:
            # Convert milestones
            milestone_objects = []
            for milestone_data in milestones:
                try:
                    milestone = Milestone(
                        number=milestone_data.get('number', 0),
                        title=milestone_data.get('title', ''),
                        description=milestone_data.get('description'),
                        state=milestone_data.get('state', 'open'),
                        created_at=milestone_data.get('created_at', datetime.utcnow()),
                        updated_at=milestone_data.get('updated_at', datetime.utcnow()),
                        due_on=milestone_data.get('due_on'),
                        closed_at=milestone_data.get('closed_at'),
                        open_issues=milestone_data.get('open_issues', 0),
                        closed_issues=milestone_data.get('closed_issues', 0)
                    )
                    milestone_objects.append(milestone)
                except Exception as e:
                    logger.warning(f"Failed to parse milestone {milestone_data.get('number')}: {e}")
                    continue
            
            # Convert projects
            project_objects = []
            for project_data in projects:
                try:
                    project = Project(
                        id=project_data.get('id', 0),
                        name=project_data.get('name', ''),
                        body=project_data.get('body'),
                        state=project_data.get('state', 'open'),
                        created_at=project_data.get('created_at', datetime.utcnow()),
                        updated_at=project_data.get('updated_at', datetime.utcnow()),
                        html_url=project_data.get('html_url', '')
                    )
                    project_objects.append(project)
                except Exception as e:
                    logger.warning(f"Failed to parse project {project_data.get('id')}: {e}")
                    continue
            
            # Calculate statistics
            total_milestones = len(milestone_objects)
            open_milestones = sum(1 for m in milestone_objects if m.state == 'open')
            closed_milestones = sum(1 for m in milestone_objects if m.state == 'closed')
            
            total_projects = len(project_objects)
            open_projects = sum(1 for p in project_objects if p.state == 'open')
            closed_projects = sum(1 for p in project_objects if p.state == 'closed')
            
            return Roadmap(
                milestones=milestone_objects,
                projects=project_objects,
                total_milestones=total_milestones,
                open_milestones=open_milestones,
                closed_milestones=closed_milestones,
                total_projects=total_projects,
                open_projects=open_projects,
                closed_projects=closed_projects
            )
            
        except Exception as e:
            logger.error(f"Failed to create roadmap: {e}")
            return None
    
    @staticmethod
    def enrich_repository_data(
        repo_data: Dict[str, Any],
        prs: Optional[List[Dict[str, Any]]] = None,
        issues: Optional[List[Dict[str, Any]]] = None,
        milestones: Optional[List[Dict[str, Any]]] = None,
        projects: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Enrich repository data with PR/issue/roadmap information.
        
        Args:
            repo_data: Base repository data dictionary
            prs: Pull request data
            issues: Issue data (excluding PRs)
            milestones: Milestone data
            projects: Project data
            
        Returns:
            Enriched repository data dictionary
        """
        enriched = repo_data.copy()
        
        # Add PR statistics
        if prs:
            pr_stats = RepositoryDataService.create_pr_statistics(prs)
            if pr_stats:
                enriched['pull_requests'] = pr_stats.dict()
        
        # Add issue statistics
        if issues:
            issue_stats = RepositoryDataService.create_issue_statistics(issues)
            if issue_stats:
                enriched['issues'] = issue_stats.dict()
        
        # Add roadmap
        if milestones or projects:
            roadmap = RepositoryDataService.create_roadmap(
                milestones or [],
                projects or []
            )
            if roadmap:
                enriched['roadmap'] = roadmap.dict()
        
        return enriched


# Global service instance
repository_data_service = RepositoryDataService()
