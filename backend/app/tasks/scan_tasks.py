import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import traceback

from celery import current_task
from celery.exceptions import Retry

from app.celery_app import celery_app
from app.services.github_scanner import GitHubScanner
from app.services.github_api_service import GitHubAPIService
from app.services.evaluation_engine import EvaluationEngine
from app.services.technology_detector import TechnologyDetector
from app.services.cache_invalidation import cache_invalidation_service
from app.services.scan_progress_emitter import ScanProgressEmitter, ScanPhase, OperationType
from app.websocket.scan_websocket import websocket_manager
from app.database import get_database, Collections
from app.models.scan import ScanResult, ScanProgress, ScanStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

class ScanProgressTracker:
    """Helper class to track and update scan progress"""
    
    def __init__(self, task_id: str, total_repos: int = 0):
        self.task_id = task_id
        self.total_repos = total_repos
        self.processed_repos = 0
        self.current_repo = ""
        self.status = ScanStatus.PENDING
        self.errors = []
        
    async def update_progress(self, 
                            current_repo: str = None, 
                            status: ScanStatus = None,
                            increment: bool = False,
                            error: str = None):
        """Update scan progress in database and Celery"""
        
        if current_repo:
            self.current_repo = current_repo
        if status:
            self.status = status
        if increment:
            self.processed_repos += 1
        if error:
            self.errors.append(error)
            
        progress_percentage = 0
        if self.total_repos > 0:
            progress_percentage = min(100, int((self.processed_repos / self.total_repos) * 100))
        
        # Update Celery task state
        if current_task:
            current_task.update_state(
                state=status.value if status else self.status.value,
                meta={
                    'progress': progress_percentage,
                    'current_repo': self.current_repo,
                    'total_repos': self.total_repos,
                    'processed_repos': self.processed_repos,
                    'status': self.status.value,
                    'errors': self.errors[-5:],  # Keep last 5 errors
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        
        # Update database
        try:
            db = await get_database()
            await db.scan_progress.update_one(
                {"task_id": self.task_id},
                {
                    "$set": {
                        "progress": progress_percentage,
                        "current_repo": self.current_repo,
                        "total_repos": self.total_repos,
                        "processed_repos": self.processed_repos,
                        "status": self.status.value,
                        "errors": self.errors,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Failed to update progress in database: {e}")

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def scan_user_repositories(self, user_id: str, github_url: str, scan_type: str = "myself"):
    """
    Main task to scan all repositories for a user
    """
    task_id = self.request.id
    logger.info(f"Starting repository scan for user {user_id}, task {task_id}")
    
    try:
        # Run the async scan function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _scan_user_repositories_async(task_id, user_id, github_url, scan_type)
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Scan failed for user {user_id}: {exc}")
        logger.error(traceback.format_exc())
        
        # Update progress to error state
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tracker = ScanProgressTracker(task_id)
            loop.run_until_complete(
                tracker.update_progress(status=ScanStatus.ERROR, error=str(exc))
            )
        finally:
            loop.close()
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying scan for user {user_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        raise exc

async def _scan_user_repositories_async(task_id: str, user_id: str, github_url: str, scan_type: str):
    """Async implementation of repository scanning"""
    
    tracker = ScanProgressTracker(task_id)
    
    # Initialize enhanced progress emitter
    progress_emitter = ScanProgressEmitter(task_id, user_id, websocket_manager)
    
    try:
        # Initialize services
        github_scanner = GitHubScanner(settings.GITHUB_TOKEN)
        github_api = GitHubAPIService(settings.GITHUB_TOKEN)
        acid_evaluator = EvaluationEngine()
        tech_detector = TechnologyDetector()
        db = await get_database()
        
        # Extract username from URL
        username = github_url.split('/')[-1]
        
        # Emit connecting phase
        await progress_emitter.emit_progress(
            phase=ScanPhase.CONNECTING,
            current_operation={
                "type": OperationType.FETCH_ACCOUNT.value,
                "target": username,
                "details": "Connecting to GitHub API",
                "startTime": datetime.utcnow().isoformat()
            },
            phase_progress=0.5
        )
        
        await tracker.update_progress(
            status=ScanStatus.SCANNING,
            current_repo="Fetching repository list..."
        )
        
        # Emit fetching profile phase
        await progress_emitter.emit_progress(
            phase=ScanPhase.FETCHING_PROFILE,
            current_operation={
                "type": OperationType.FETCH_ACCOUNT.value,
                "target": username,
                "details": f"Fetching account information for {username}",
                "startTime": datetime.utcnow().isoformat()
            },
            phase_progress=0.3
        )
        
        # Fetch user repositories
        repositories = await github_scanner.fetch_user_repositories(username)
        tracker.total_repos = len(repositories)
        
        logger.info(f"Found {len(repositories)} repositories for user {username}")
        
        # Emit account info (Requirements: 5.1, 5.2, 5.3, 5.4, 5.5)
        total_stars = sum(repo.get('stargazers_count', 0) for repo in repositories)
        await progress_emitter.emit_account_info(
            username=username,
            account_type="User",  # Could be enhanced to detect Organization
            avatar_url="",  # Could be fetched from user profile
            followers=0,  # Could be fetched from user profile
            following=0,  # Could be fetched from user profile
            public_repos=len(repositories),
            total_stars=total_stars,
            contribution_streak=0  # Could be calculated from contribution data
        )
        
        await tracker.update_progress(
            current_repo=f"Found {len(repositories)} repositories"
        )
        
        # Process repositories - only evaluate first 20 for scoring
        processed_repos = []
        display_only_repos = []
        
        # Process first 20 repositories with full evaluation
        for i, repo_data in enumerate(repositories[:20]):
            try:
                repo_index = i + 1
                repo_name = repo_data['name']
                repo_full_name = repo_data['full_name']
                
                # Emit repository progress (Requirements: 1.2, 1.3)
                await progress_emitter.emit_repository_progress(
                    current_index=repo_index,
                    total=len(repositories),
                    current_repo={
                        "name": repo_name,
                        "fullName": repo_full_name,
                        "description": repo_data.get('description', ''),
                        "language": repo_data.get('language', ''),
                        "stars": repo_data.get('stargazers_count', 0),
                        "forks": repo_data.get('forks_count', 0),
                        "size": repo_data.get('size', 0),
                        "lastUpdated": repo_data.get('updated_at', '')
                    }
                )
                
                await tracker.update_progress(
                    current_repo=f"Analyzing {repo_name} (scoring)...",
                    status=ScanStatus.ANALYZING
                )
                
                # Emit fetching PRs phase (Requirements: 1.4)
                await progress_emitter.emit_progress(
                    phase=ScanPhase.FETCHING_PRS,
                    current_operation={
                        "type": OperationType.FETCH_PR.value,
                        "target": repo_full_name,
                        "details": f"Fetching pull requests for {repo_name}",
                        "startTime": datetime.utcnow().isoformat()
                    },
                    phase_progress=0.0
                )
                
                # Fetch repository contents
                contents = await github_scanner.fetch_repository_contents(
                    repo_full_name, 
                    max_files=50
                )
                
                # Emit analysis progress for each file (Requirements: 1.3, 4.3, 4.4)
                total_files = len(contents)
                for file_idx, file_content in enumerate(contents):
                    file_path = file_content.get('path', 'unknown')
                    await progress_emitter.emit_analysis_progress(
                        repo_name=repo_name,
                        current_file=file_path,
                        files_analyzed=file_idx + 1,
                        total_files=total_files,
                        lines_of_code=sum(len(f.get('content', '').split('\n')) for f in contents[:file_idx+1]),
                        api_calls_made=0,  # Could be tracked from github_scanner
                        api_calls_remaining=5000  # Could be fetched from rate limit
                    )
                
                # Get commit history
                commit_history = await github_scanner.get_commit_history(
                    repo_full_name, 
                    limit=50
                )
                
                # Analyze repository structure
                structure_analysis = await github_scanner.analyze_repository_structure(
                    repo_full_name
                )
                
                # Emit score calculation phase (Requirements: 1.3)
                await progress_emitter.emit_score_calculation(
                    repo_name=repo_name,
                    calculation_type="ACID scores",
                    progress=0.0
                )
                
                # Calculate ACID scores
                acid_scores = await acid_evaluator.evaluate_repository(
                    repo_data, contents, commit_history, structure_analysis
                )
                
                # Emit score calculation completion
                await progress_emitter.emit_score_calculation(
                    repo_name=repo_name,
                    calculation_type="ACID scores",
                    progress=1.0
                )
                
                # Fetch PR/Issue/Roadmap data (Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.3)
                pr_statistics = None
                issue_statistics = None
                roadmap_data = None
                
                try:
                    # Extract owner and repo from full_name
                    owner, repo = repo_full_name.split('/')
                    logger.info(f"Fetching PR/Issue data for {owner}/{repo}")
                    
                    # Fetch pull requests
                    prs = await github_api.get_pull_requests(
                        owner=owner,
                        repo=repo,
                        state='all',
                        per_page=100
                    )
                    logger.info(f"Fetched {len(prs) if prs else 0} PRs for {repo_name}")
                    
                    # Calculate PR statistics
                    if prs:
                        open_prs = [pr for pr in prs if pr.get('state') == 'open']
                        closed_prs = [pr for pr in prs if pr.get('state') == 'closed' and not pr.get('merged_at')]
                        merged_prs = [pr for pr in prs if pr.get('merged_at')]
                        
                        # Calculate average time to merge
                        merge_times = []
                        for pr in merged_prs:
                            if pr.get('created_at') and pr.get('merged_at'):
                                created = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                                merged = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                                merge_times.append((merged - created).total_seconds() / 3600)
                        
                        avg_time_to_merge = sum(merge_times) / len(merge_times) if merge_times else None
                        
                        # Calculate average additions/deletions
                        additions = [pr.get('additions', 0) for pr in prs if pr.get('additions')]
                        deletions = [pr.get('deletions', 0) for pr in prs if pr.get('deletions')]
                        
                        # Transform PR data to match frontend expectations
                        recent_prs_formatted = []
                        for pr in prs[:10]:
                            recent_prs_formatted.append({
                                'number': pr.get('number'),
                                'title': pr.get('title'),
                                'author': pr.get('user', {}).get('login', 'unknown'),
                                'state': 'merged' if pr.get('merged_at') else pr.get('state', 'open'),
                                'createdAt': pr.get('created_at'),
                                'mergedAt': pr.get('merged_at'),
                                'url': pr.get('html_url', '')
                            })
                        
                        pr_statistics = {
                            'total': len(prs),
                            'open': len(open_prs),
                            'closed': len(closed_prs),
                            'merged': len(merged_prs),
                            'recent': recent_prs_formatted,  # Frontend expects 'recent', not 'recent_prs'
                            'avgTimeToMerge': avg_time_to_merge,  # Frontend expects camelCase
                            'avg_additions': sum(additions) / len(additions) if additions else None,
                            'avg_deletions': sum(deletions) / len(deletions) if deletions else None
                        }
                    
                    # Fetch issues (excluding PRs)
                    issues = await github_api.get_issues(
                        owner=owner,
                        repo=repo,
                        state='all',
                        per_page=100
                    )
                    logger.info(f"Fetched {len(issues) if issues else 0} issues for {repo_name}")
                    
                    # Calculate issue statistics
                    if issues:
                        open_issues = [issue for issue in issues if issue.get('state') == 'open']
                        closed_issues = [issue for issue in issues if issue.get('state') == 'closed']
                        
                        # Calculate average time to close
                        close_times = []
                        for issue in closed_issues:
                            if issue.get('created_at') and issue.get('closed_at'):
                                created = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
                                closed = datetime.fromisoformat(issue['closed_at'].replace('Z', '+00:00'))
                                close_times.append((closed - created).total_seconds() / 3600)
                        
                        avg_time_to_close = sum(close_times) / len(close_times) if close_times else None
                        
                        # Calculate label distribution
                        labels_dist = {}
                        for issue in issues:
                            for label in issue.get('labels', []):
                                label_name = label.get('name', 'unknown')
                                labels_dist[label_name] = labels_dist.get(label_name, 0) + 1
                        
                        # Transform issue data to match frontend expectations
                        recent_issues_formatted = []
                        for issue in issues[:10]:
                            recent_issues_formatted.append({
                                'number': issue.get('number'),
                                'title': issue.get('title'),
                                'author': issue.get('user', {}).get('login', 'unknown'),
                                'state': issue.get('state', 'open'),
                                'createdAt': issue.get('created_at'),
                                'closedAt': issue.get('closed_at'),
                                'url': issue.get('html_url', ''),
                                'labels': [label.get('name') for label in issue.get('labels', [])]
                            })
                        
                        issue_statistics = {
                            'total': len(issues),
                            'open': len(open_issues),
                            'closed': len(closed_issues),
                            'recent': recent_issues_formatted,  # Frontend expects 'recent', not 'recent_issues'
                            'avgTimeToClose': avg_time_to_close,  # Frontend expects camelCase
                            'labelsDistribution': labels_dist  # Frontend expects camelCase
                        }
                    
                    # Fetch milestones and projects for roadmap
                    milestones = await github_api.get_milestones(
                        owner=owner,
                        repo=repo,
                        state='all',
                        per_page=50
                    )
                    
                    projects = await github_api.get_projects(
                        owner=owner,
                        repo=repo,
                        state='all',
                        per_page=50
                    )
                    
                    # Calculate roadmap statistics
                    if milestones or projects:
                        open_milestones = [m for m in milestones if m.get('state') == 'open']
                        closed_milestones = [m for m in milestones if m.get('state') == 'closed']
                        open_projects = [p for p in projects if p.get('state') == 'open']
                        closed_projects = [p for p in projects if p.get('state') == 'closed']
                        
                        roadmap_data = {
                            'milestones': milestones,
                            'projects': projects,
                            'total_milestones': len(milestones),
                            'open_milestones': len(open_milestones),
                            'closed_milestones': len(closed_milestones),
                            'total_projects': len(projects),
                            'open_projects': len(open_projects),
                            'closed_projects': len(closed_projects)
                        }
                    
                except Exception as e:
                    logger.error(f"Failed to fetch PR/Issue/Roadmap data for {repo_name}: {e}")
                    logger.error(f"Error details: {type(e).__name__}: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    # Continue without this data
                
                # Combine all data
                repository_result = {
                    **repo_data,
                    'contents': contents,
                    'commit_history': commit_history,
                    'structure_analysis': structure_analysis,
                    'acid_scores': acid_scores,
                    'overall_score': acid_scores.get('overall_score', 0),
                    'analyzed_at': datetime.utcnow().isoformat(),
                    'evaluated_for_scoring': True,
                    'pull_requests': pr_statistics,
                    'issues': issue_statistics,
                    'roadmap': roadmap_data
                }
                
                processed_repos.append(repository_result)
                
                await tracker.update_progress(increment=True)
                
                # Small delay to prevent overwhelming the API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Failed to process repository {repo_data['name']}: {e}")
                
                # Emit error (Requirements: 3.3)
                await progress_emitter.emit_error(
                    error_code="REPO_PROCESSING_ERROR",
                    error_message=f"Failed to process {repo_data['name']}: {str(e)}",
                    recovery_suggestion="Continuing with next repository"
                )
                
                await tracker.update_progress(
                    increment=True,
                    error=f"Failed to process {repo_data['name']}: {str(e)}"
                )
                continue
        
        # Process remaining repositories (21+) with basic info only
        for i, repo_data in enumerate(repositories[20:], start=21):
            try:
                repo_name = repo_data['name']
                repo_full_name = repo_data['full_name']
                
                # Emit repository progress for display-only repos (Requirements: 1.2)
                await progress_emitter.emit_repository_progress(
                    current_index=i,
                    total=len(repositories),
                    current_repo={
                        "name": repo_name,
                        "fullName": repo_full_name,
                        "description": repo_data.get('description', ''),
                        "language": repo_data.get('language', ''),
                        "stars": repo_data.get('stargazers_count', 0),
                        "forks": repo_data.get('forks_count', 0),
                        "size": repo_data.get('size', 0),
                        "lastUpdated": repo_data.get('updated_at', '')
                    }
                )
                
                await tracker.update_progress(
                    current_repo=f"Adding {repo_name} (display only)...",
                    status=ScanStatus.ANALYZING
                )
                
                # Add basic repository info without detailed analysis
                repository_result = {
                    **repo_data,
                    'evaluated_for_scoring': False,
                    'display_only': True,
                    'analyzed_at': datetime.utcnow().isoformat()
                }
                
                display_only_repos.append(repository_result)
                
                await tracker.update_progress(increment=True)
                
            except Exception as e:
                logger.warning(f"Failed to add repository {repo_data['name']}: {e}")
                
                # Emit error
                await progress_emitter.emit_error(
                    error_code="REPO_ADD_ERROR",
                    error_message=f"Failed to add {repo_data['name']}: {str(e)}",
                    recovery_suggestion="Continuing with next repository"
                )
                
                await tracker.update_progress(
                    increment=True,
                    error=f"Failed to add {repo_data['name']}: {str(e)}"
                )
                continue
        
        # Emit generating insights phase
        await progress_emitter.emit_progress(
            phase=ScanPhase.GENERATING_INSIGHTS,
            current_operation={
                "type": "generate_insights",
                "target": username,
                "details": "Generating insights and calculating overall scores",
                "startTime": datetime.utcnow().isoformat()
            },
            phase_progress=0.5
        )
        
        # Calculate overall user scores (only from evaluated repositories)
        overall_scores = acid_evaluator.calculate_user_scores(processed_repos)
        
        # Combine all repositories for storage
        all_repositories = processed_repos + display_only_repos
        
        # Create final scan result
        scan_result = ScanResult(
            user_id=user_id,
            github_url=github_url,
            scan_type=scan_type,
            repositories=all_repositories,
            overall_scores=overall_scores,
            summary={
                'total_repositories': len(all_repositories),
                'evaluated_repositories': len(processed_repos),
                'display_only_repositories': len(display_only_repos),
                'total_stars': sum(repo.get('stargazers_count', 0) for repo in all_repositories),
                'total_forks': sum(repo.get('forks_count', 0) for repo in all_repositories),
                'primary_languages': list(set(repo.get('language') for repo in processed_repos if repo.get('language'))),
                'avg_score': overall_scores.get('overall_score', 0),
                'top_repositories': sorted(processed_repos, key=lambda x: x.get('overall_score', 0), reverse=True)[:5]
            },
            scan_completed_at=datetime.utcnow(),
            task_id=task_id
        )
        
        # Save to database
        await db.scan_results.insert_one(scan_result.dict())
        
        # CRITICAL: Populate user_rankings collection (single source for scores and rankings)
        try:
            # Get user's github_username and profile from database
            from bson import ObjectId
            
            # Use correct internal_users collection
            user_doc = await db[Collections.INTERNAL_USERS].find_one({"user_id": user_id})
            if not user_doc and ObjectId.is_valid(user_id):
                 user_doc = await db[Collections.INTERNAL_USERS].find_one({"_id": ObjectId(user_id)})
                 
            github_username = user_doc.get("github_username") if user_doc else username
            
            # Get user profile for region/university info
            profile = await db.user_profiles.find_one({"user_id": user_id})
            
            if github_username and overall_scores.get('overall_score', 0) > 0:
                logger.info(f"📊 [USER_RANKINGS] Storing scores and rankings for {github_username}")
                
                # Prepare user_rankings document (single collection for everything)
                user_ranking_doc = {
                    "user_id": user_id,
                    "github_username": github_username,
                    "name": profile.get("name") if profile else None,
                    
                    # Profile info
                    "university": profile.get("university") if profile else None,
                    "university_short": profile.get("university_short") if profile else None,
                    "region": profile.get("region") if profile else None,
                    "state": profile.get("state") if profile else None,
                    "district": profile.get("district") if profile else None,
                    
                    # Overall Score
                    "overall_score": round(overall_scores.get('overall_score', 0), 1),
                    
                    # Repository stats
                    "repository_count": len(all_repositories),
                    "evaluated_repository_count": len(processed_repos),
                    
                    # Repository category counts (will be updated after analysis)
                    "flagship_count": 0,
                    "significant_count": 0,
                    "supporting_count": 0,
                    
                    # Regional Ranking (will be calculated by ranking service)
                    "regional_rank": None,
                    "regional_total_users": None,
                    "regional_percentile": None,
                    
                    # University Ranking (will be calculated by ranking service)
                    "university_rank": None,
                    "university_total_users": None,
                    "university_percentile": None,
                    
                    # Metadata
                    "last_scan_date": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # Upsert into user_rankings collection
                await db.user_rankings.update_one(
                    {"user_id": user_id},
                    {"$set": user_ranking_doc},
                    upsert=True
                )
                
                logger.info(f"✅ [USER_RANKINGS] Successfully stored scores")
                logger.info(f"   - Username: {github_username}")
                logger.info(f"   - Overall Score: {round(overall_scores.get('overall_score', 0), 1)}")
                logger.info(f"   - Repository Count: {len(all_repositories)}")
                logger.info(f"   - Region: {profile.get('region') if profile else 'N/A'}")
                logger.info(f"   - University: {profile.get('university') if profile else 'N/A'}")
                
                # CRITICAL: Populate hr_view collection (primary collection for HR dashboard)
                try:
                    from app.services.hr_view_service import HRViewService
                    
                    hr_view_service = HRViewService(db)
                    
                    # Prepare data for hr_view
                    profile_data = {
                        "name": profile.get("name") if profile else None,
                        "bio": profile.get("bio") if profile else None,
                        "avatar_url": profile.get("profile_picture") if profile else None,
                        "location": profile.get("location") if profile else None,
                        "company": profile.get("company") if profile else None,
                        "email": profile.get("email") if profile else None,
                        "blog": profile.get("blog") or profile.get("website") if profile else None,
                        "twitter_username": profile.get("twitter_username") if profile else None,
                        "public_repos": profile.get("public_repos") or profile.get("total_repos", 0) if profile else 0,
                        "followers": profile.get("followers", 0) if profile else 0,
                        "following": profile.get("following", 0) if profile else 0,
                        "created_at": profile.get("github_created_at") or profile.get("created_at") if profile else None,
                        "updated_at": profile.get("github_updated_at") or profile.get("updated_at") if profile else None
                    }
                    
                    scores_data = {
                        "overall_score": overall_scores.get("overall_score", 0.0),
                        "acid_breakdown": overall_scores.get("acid_breakdown", {})
                    }
                    
                    rankings_data = {
                        "regional": {
                            "rank": None,  # Will be populated by ranking service
                            "total": None,
                            "percentile": None,
                            "region": profile.get("region") if profile else None,
                            "state": profile.get("state") if profile else None,
                            "percentile_text": None
                        },
                        "university": {
                            "rank": None,  # Will be populated by ranking service
                            "total": None,
                            "percentile": None,
                            "university": profile.get("university") if profile else None,
                            "university_short": profile.get("university_short") if profile else None,
                            "percentile_text": None
                        }
                    }
                    
                    # Upsert into hr_view
                    hr_result = await hr_view_service.upsert_developer_profile(
                        user_id=user_id,
                        github_username=github_username,
                        profile_data=profile_data,
                        repositories=evaluated_repos,
                        scores=scores_data,
                        rankings=rankings_data,
                        languages=overall_scores.get("languages", []),
                        tech_stack=overall_scores.get("tech_stack", []),
                        pull_requests=None,  # TODO: Add PR data if available
                        issues=None,  # TODO: Add issue data if available
                        contributions=None,  # TODO: Add contribution data if available
                        category_distribution=overall_scores.get("category_distribution", {})
                    )
                    
                    if hr_result.get("success"):
                        logger.info(f"✅ [HR_VIEW] Successfully stored developer profile for {github_username}")
                    else:
                        logger.error(f"❌ [HR_VIEW] Failed to store profile: {hr_result.get('error')}")
                        
                except Exception as hr_error:
                    logger.error(f"❌ [HR_VIEW] Error storing developer profile: {hr_error}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Trigger ranking calculation after populating user_rankings
                try:
                    from app.services.enhanced_ranking_service import EnhancedRankingService
                    
                    logger.info(f"🎯 Calculating rankings after scan completion (batch update)")
                    
                    ranking_service = EnhancedRankingService(db)
                    ranking_result = await ranking_service.update_rankings_for_user(user_id)
                    
                    if ranking_result.get("success"):
                        logger.info(f"✅ Rankings calculated successfully (batch mode)")
                        logger.info(f"   - Regional updated: {ranking_result.get('regional_updated', False)}")
                        logger.info(f"   - University updated: {ranking_result.get('university_updated', False)}")
                        
                        # Log ranking details
                        if ranking_result.get('regional_result'):
                            reg = ranking_result['regional_result']
                            logger.info(f"   - Regional: {reg.get('users_updated', 0)} users updated")
                        if ranking_result.get('university_result'):
                            uni = ranking_result['university_result']
                            logger.info(f"   - University: {uni.get('users_updated', 0)} users updated")
                    else:
                        logger.warning(f"⚠️  Ranking calculation completed with error: {ranking_result.get('error')}")
                        
                except Exception as ranking_error:
                    logger.error(f"❌ Error calculating rankings: {ranking_error}")
                    # Don't fail scan if ranking calculation fails
                    
        except Exception as details_error:
            logger.error(f"❌ [USER_OVERALL_DETAILS] Error storing scan results: {details_error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't fail scan if storage fails
        
        # Invalidate relevant caches
        repository_names = [repo.get('full_name') for repo in processed_repos if repo.get('full_name')]
        await cache_invalidation_service.invalidate_on_scan_completion(user_id, repository_names)
        
        # Emit completion (Requirements: 5.5)
        await progress_emitter.emit_completion(
            summary={
                'total_repositories': len(all_repositories),
                'evaluated_repositories': len(processed_repos),
                'overall_score': overall_scores.get('overall_score', 0)
            }
        )
        
        await tracker.update_progress(
            status=ScanStatus.COMPLETED,
            current_repo="Scan completed successfully"
        )
        
        logger.info(f"Successfully completed scan for user {user_id}")
        
        return {
            'status': 'completed',
            'repositories_processed': len(processed_repos),
            'overall_score': overall_scores.get('overall_score', 0),
            'scan_id': task_id
        }
        
    except Exception as e:
        logger.error(f"Error in repository scan: {e}")
        
        # Emit error event
        await progress_emitter.emit_error(
            error_code="SCAN_ERROR",
            error_message=str(e),
            recovery_suggestion="Please try again or contact support if the issue persists"
        )
        
        await tracker.update_progress(
            status=ScanStatus.ERROR,
            error=str(e)
        )
        raise

@celery_app.task(bind=True, max_retries=2)
def scan_single_repository(self, user_id: str, repo_url: str):
    """
    Task to scan a single repository
    """
    task_id = self.request.id
    logger.info(f"Starting single repository scan: {repo_url}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _scan_single_repository_async(task_id, user_id, repo_url)
            )
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Single repository scan failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30)
        
        raise exc

async def _scan_single_repository_async(task_id: str, user_id: str, repo_url: str):
    """Async implementation of single repository scanning"""
    
    tracker = ScanProgressTracker(task_id, total_repos=1)
    
    try:
        # Initialize services
        github_scanner = GitHubScanner(settings.GITHUB_TOKEN)
        acid_evaluator = EvaluationEngine()
        tech_detector = TechnologyDetector()
        
        # Extract owner and repo from URL
        parts = repo_url.replace('https://github.com/', '').split('/')
        owner, repo_name = parts[0], parts[1]
        repo_full_name = f"{owner}/{repo_name}"
        
        await tracker.update_progress(
            status=ScanStatus.SCANNING,
            current_repo=f"Fetching {repo_name}..."
        )
        
        # Get repository info
        repo_data = await github_scanner.fetch_user_repositories(owner)
        target_repo = next((repo for repo in repo_data if repo['name'] == repo_name), None)
        
        if not target_repo:
            raise ValueError(f"Repository {repo_full_name} not found or not accessible")
        
        await tracker.update_progress(
            status=ScanStatus.ANALYZING,
            current_repo=f"Analyzing {repo_name}..."
        )
        
        # Fetch repository contents
        contents = await github_scanner.fetch_repository_contents(repo_full_name, max_files=100)
        
        # Get commit history
        commit_history = await github_scanner.get_commit_history(repo_full_name, limit=100)
        
        # Analyze repository structure
        structure_analysis = await github_scanner.analyze_repository_structure(repo_full_name)
        
        # Calculate ACID scores
        acid_scores = await acid_evaluator.evaluate_repository(
            target_repo, contents, commit_history, structure_analysis
        )
        
        # Create result
        repository_result = {
            **target_repo,
            'contents': contents,
            'commit_history': commit_history,
            'structure_analysis': structure_analysis,
            'acid_scores': acid_scores,
            'overall_score': acid_scores.get('overall_score', 0),
            'analyzed_at': datetime.utcnow().isoformat()
        }
        
        # Invalidate repository cache
        await cache_invalidation_service.invalidate_repository_data(repo_full_name, user_id)
        
        await tracker.update_progress(
            status=ScanStatus.COMPLETED,
            current_repo="Analysis completed",
            increment=True
        )
        
        return {
            'status': 'completed',
            'repository': repository_result,
            'scan_id': task_id
        }
        
    except Exception as e:
        logger.error(f"Error in single repository scan: {e}")
        await tracker.update_progress(
            status=ScanStatus.ERROR,
            error=str(e)
        )
        raise

@celery_app.task
def cleanup_expired_scans():
    """
    Periodic task to clean up expired scan results and progress records
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_cleanup_expired_scans_async())
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise

async def _cleanup_expired_scans_async():
    """Async cleanup implementation"""
    
    try:
        db = await get_database()
        
        # Clean up old progress records (older than 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        progress_result = await db.scan_progress.delete_many({
            "updated_at": {"$lt": cutoff_time}
        })
        
        # Clean up old scan results (older than 30 days)
        old_cutoff = datetime.utcnow() - timedelta(days=30)
        
        results_result = await db.scan_results.delete_many({
            "scan_completed_at": {"$lt": old_cutoff}
        })
        
        logger.info(f"Cleanup completed: {progress_result.deleted_count} progress records, {results_result.deleted_count} scan results deleted")
        
        return {
            'progress_records_deleted': progress_result.deleted_count,
            'scan_results_deleted': results_result.deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise

# Helper function to get scan progress
async def get_scan_progress(task_id: str) -> Optional[Dict[str, Any]]:
    """Get current scan progress from database"""
    try:
        db = await get_database()
        progress = await db.scan_progress.find_one({"task_id": task_id})
        
        if progress:
            # Remove MongoDB ObjectId
            progress.pop('_id', None)
            return progress
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting scan progress: {e}")
        return None

# Helper function to get scan result
async def get_scan_result(task_id: str) -> Optional[Dict[str, Any]]:
    """Get scan result from database"""
    try:
        db = await get_database()
        result = await db.scan_results.find_one({"task_id": task_id})
        
        if result:
            # Remove MongoDB ObjectId
            result.pop('_id', None)
            return result
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting scan result: {e}")
        return None