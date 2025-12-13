"""
Analysis Orchestrator Service
Orchestrates the complete repository analysis process including scoring, categorization,
evaluation, and overall score calculation.
"""

import logging
import asyncio
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

from app.services.repository_importance_scorer import RepositoryImportanceScorer
from app.services.evaluation_engine import EvaluationEngine
from app.services.analysis_state_storage import AnalysisStateStorage
from app.services.enhanced_evaluation_service import EnhancedEvaluationService
from app.services.score_calculation_service import ScoreCalculationService

logger = logging.getLogger(__name__)
analytics_logger = logging.getLogger("analytics")


class AnalysisStatus(str, Enum):
    """Analysis status enumeration"""
    STARTED = "started"
    SCORING = "scoring"
    CATEGORIZING = "categorizing"
    EVALUATING = "evaluating"
    CALCULATING = "calculating"
    COMPLETE = "complete"
    FAILED = "failed"


class AnalysisOrchestrator:
    """
    Orchestrates the complete repository analysis process.
    
    Analysis phases:
    1. Scoring: Calculate importance scores for all repositories
    2. Categorizing: Classify repositories into flagship/significant/supporting
    3. Evaluating: Deep evaluation of selected repositories
    4. Calculating: Calculate overall developer score
    """
    
    def __init__(self, state_storage: Optional[AnalysisStateStorage] = None):
        """
        Initialize the analysis orchestrator.
        
        Args:
            state_storage: Optional storage backend for analysis state (AnalysisStateStorage)
                          If None, uses InMemoryStateStorage for testing
        """
        self.scorer = RepositoryImportanceScorer()
        self.evaluator = EnhancedEvaluationService()
        self.score_calculator = ScoreCalculationService()
        self.state_storage = state_storage or InMemoryStateStorage()
        
    async def initiate_analysis(
        self, 
        username: str, 
        repositories: List[Dict[str, Any]],
        max_evaluate: int = 15,
        github_token: Optional[str] = None
    ) -> str:
        """
        Initiate repository analysis process.
        
        Args:
            username: GitHub username
            repositories: List of repository dictionaries
            max_evaluate: Maximum number of repositories to evaluate (default: 15)
            github_token: Optional GitHub token for API access
            
        Returns:
            analysis_id: Unique identifier for this analysis
        """
        analysis_id = str(uuid.uuid4())
        
        logger.info(
            f"Initiating analysis for user '{username}': "
            f"{len(repositories)} repositories, max_evaluate={max_evaluate}"
        )
        
        # Log analytics event for analysis initiation
        self._log_analytics_event('analysis_initiated', {
            'analysis_id': analysis_id,
            'username': username,
            'total_repositories': len(repositories),
            'max_evaluate': max_evaluate
        })
        
        # Store initial state
        await self.state_storage.store_state(analysis_id, {
            'analysis_id': analysis_id,
            'username': username,
            'status': AnalysisStatus.STARTED,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'progress': {
                'total_repos': len(repositories),
                'scored': 0,
                'categorized': 0,
                'evaluated': 0,
                'to_evaluate': 0,
                'percentage': 0
            },
            'current_phase': 'started',
            'current_message': 'Analysis initiated',
            'error': None,
            'max_evaluate': max_evaluate
        })
        
        # Start async analysis
        asyncio.create_task(
            self.run_analysis(analysis_id, username, repositories, max_evaluate, github_token)
        )
        
        return analysis_id
    
    async def run_analysis(
        self,
        analysis_id: str,
        username: str,
        repositories: List[Dict[str, Any]],
        max_evaluate: int,
        github_token: Optional[str] = None
    ):
        """
        Run the complete analysis pipeline with performance tracking.
        
        Args:
            analysis_id: Unique analysis identifier
            username: GitHub username
            repositories: List of repository dictionaries
            max_evaluate: Maximum number of repositories to evaluate
            github_token: Optional GitHub token for API access
        """
        import time
        analysis_start_time = time.time()
        phase_times = {}
        
        try:
            total_repos = len(repositories)
            logger.info(f"[{analysis_id}] Starting analysis for {username}: {total_repos} repositories, max_evaluate={max_evaluate}")
            
            # Phase 1: Calculate importance scores
            phase_start = time.time()
            logger.info(f"[{analysis_id}] Phase 1: Calculating importance scores")
            await self._update_status(
                analysis_id,
                AnalysisStatus.SCORING,
                "Calculating importance scores..."
            )
            
            scored_repos = await self._score_repositories(repositories)
            phase_times['scoring'] = time.time() - phase_start
            
            await self._update_progress(analysis_id, {
                'scored': total_repos,
                'percentage': 20
            })
            
            # Phase 2: Categorize repositories
            phase_start = time.time()
            logger.info(f"[{analysis_id}] Phase 2: Categorizing repositories")
            await self._update_status(
                analysis_id,
                AnalysisStatus.CATEGORIZING,
                "Categorizing repositories..."
            )
            
            categorized_dict = self.scorer.categorize_repositories(scored_repos)
            # Store categorized repos as a flat list with category field
            categorized_repos = scored_repos  # Already have category field from categorize_repositories
            phase_times['categorizing'] = time.time() - phase_start
            
            await self._update_progress(analysis_id, {
                'categorized': total_repos,
                'percentage': 30
            })
            
            # Phase 3: Select and evaluate repositories
            phase_start = time.time()
            logger.info(f"[{analysis_id}] Phase 3: Evaluating selected repositories")
            await self._update_status(
                analysis_id,
                AnalysisStatus.EVALUATING,
                "Evaluating repositories..."
            )
            
            selected_repos = self.scorer.select_for_evaluation(categorized_dict, max_evaluate)
            to_evaluate_count = len(selected_repos)
            
            await self._update_progress(analysis_id, {
                'to_evaluate': to_evaluate_count
            })
            
            evaluated_repos = await self._evaluate_repositories(
                analysis_id,
                selected_repos,
                github_token
            )
            
            phase_times['evaluating'] = time.time() - phase_start
            
            # Merge evaluation results back into categorized repos
            # This preserves category and importance_score while adding evaluation data
            final_repos = self._merge_evaluation_results(categorized_repos, evaluated_repos)
            
            # Calculate category distribution for reporting
            category_distribution = self._get_category_distribution(final_repos)
            
            # Phase 4: Calculate overall score
            phase_start = time.time()
            logger.info(f"[{analysis_id}] Phase 4: Calculating overall score")
            await self._update_status(
                analysis_id,
                AnalysisStatus.CALCULATING,
                "Calculating overall score..."
            )
            
            overall_score = self._calculate_overall_score(evaluated_repos)
            phase_times['calculating'] = time.time() - phase_start
            
            await self._update_progress(analysis_id, {
                'percentage': 100
            })
            
            # Calculate total analysis time
            total_time = time.time() - analysis_start_time
            
            # Log performance summary
            logger.info(f"[{analysis_id}] ===== ANALYSIS PERFORMANCE SUMMARY =====")
            logger.info(f"[{analysis_id}] Total time: {total_time:.2f}s")
            logger.info(f"[{analysis_id}] Phase breakdown:")
            logger.info(f"[{analysis_id}]   - Scoring: {phase_times.get('scoring', 0):.2f}s")
            logger.info(f"[{analysis_id}]   - Categorizing: {phase_times.get('categorizing', 0):.2f}s")
            logger.info(f"[{analysis_id}]   - Evaluating: {phase_times.get('evaluating', 0):.2f}s")
            logger.info(f"[{analysis_id}]   - Calculating: {phase_times.get('calculating', 0):.2f}s")
            logger.info(f"[{analysis_id}] Repositories: {total_repos} total, {len(evaluated_repos)} evaluated")
            logger.info(f"[{analysis_id}] Overall score: {overall_score}")
            logger.info(f"[{analysis_id}] ========================================")
            
            # Calculate success/failure rates
            success_rate = (len(evaluated_repos) / to_evaluate_count * 100) if to_evaluate_count > 0 else 0
            failure_count = to_evaluate_count - len(evaluated_repos)
            
            # Log analytics event for analysis completion
            self._log_analytics_event('analysis_completed', {
                'analysis_id': analysis_id,
                'username': username,
                'total_time_seconds': round(total_time, 2),
                'total_repositories': total_repos,
                'evaluated_count': len(evaluated_repos),
                'target_evaluate_count': to_evaluate_count,
                'success_rate_percent': round(success_rate, 2),
                'failure_count': failure_count,
                'flagship_count': category_distribution.get('flagship', 0),
                'significant_count': category_distribution.get('significant', 0),
                'supporting_count': category_distribution.get('supporting', 0),
                'overall_score': overall_score,
                'phase_times': {k: round(v, 2) for k, v in phase_times.items()}
            })
            
            # Store final results with complete repository data
            results_data = {
                'repositories': final_repos,  # Include category, importance_score, evaluated, evaluation
                'overall_scores': {
                    'overall_score': overall_score
                },
                'category_distribution': category_distribution,
                'analyzed': True,
                'analyzedAt': datetime.utcnow().isoformat()
            }
            
            # Store complete results using update_results method
            if hasattr(self.state_storage, 'update_results'):
                await self.state_storage.update_results(analysis_id, results_data)
            
            # Also update the main state with summary info
            await self._store_results(analysis_id, {
                'status': AnalysisStatus.COMPLETE,
                'repositories': final_repos,  # Store complete repos in main state too
                'overall_score': overall_score,
                'evaluated_count': len(evaluated_repos),
                'flagship_count': category_distribution.get('flagship', 0),
                'significant_count': category_distribution.get('significant', 0),
                'supporting_count': category_distribution.get('supporting', 0),
                'completed_at': datetime.utcnow().isoformat(),
                'current_message': f'Analysis complete! {len(evaluated_repos)} repositories evaluated',
                'performance_metrics': {
                    'total_time_seconds': round(total_time, 2),
                    'phase_times': {k: round(v, 2) for k, v in phase_times.items()},
                    'avg_evaluation_time': round(phase_times.get('evaluating', 0) / max(len(evaluated_repos), 1), 2)
                },
                'results': results_data  # Store results object for easy retrieval
            })
            
            # Update user_rankings with category counts
            await self._update_user_rankings_with_categories(
                username, 
                category_distribution, 
                overall_score
            )
            
            if overall_score is not None:
                logger.info(
                    f"[{analysis_id}] Analysis complete: "
                    f"{len(evaluated_repos)} evaluated, overall score: {overall_score:.1f}"
                )
            else:
                logger.info(
                    f"[{analysis_id}] Analysis complete: "
                    f"{len(evaluated_repos)} evaluated, no overall score calculated"
                )
            
        except Exception as e:
            logger.error(f"[{analysis_id}] Analysis failed: {e}", exc_info=True)
            await self._store_error(analysis_id, str(e))
    
    async def _score_repositories(self, repositories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate importance scores for all repositories with performance logging.
        
        Performance optimization: Batch processing with timing metrics.
        
        Args:
            repositories: List of repository dictionaries
            
        Returns:
            List of repositories with importance_score and analyzed fields
        """
        import time
        start_time = time.time()
        
        # Batch process scores (synchronous but fast)
        for repo in repositories:
            repo['importance_score'] = self.scorer.calculate_importance_score(repo)
            repo['analyzed'] = True
        
        elapsed_time = time.time() - start_time
        if len(repositories) > 0:
            logger.info(
                f"Scored {len(repositories)} repositories in {elapsed_time:.2f}s "
                f"(avg {elapsed_time/len(repositories):.4f}s per repo)"
            )
        else:
            logger.info(f"No repositories to score (completed in {elapsed_time:.2f}s)")
        
        return repositories
    
    async def _evaluate_repositories(
        self,
        analysis_id: str,
        repositories: List[Dict[str, Any]],
        github_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluate selected repositories using parallel evaluation for better performance.
        
        Performance optimization: Evaluates repositories in parallel batches to reduce total time.
        
        Args:
            analysis_id: Unique analysis identifier
            repositories: List of repositories to evaluate
            github_token: Optional GitHub token for API access
            
        Returns:
            List of repositories with evaluation data
        """
        import time
        start_time = time.time()
        
        evaluated_repos = []
        total = len(repositories)
        
        # Parallel evaluation with batch size of 3 to avoid overwhelming the system
        batch_size = 3
        completed = 0
        
        logger.info(f"[{analysis_id}] Starting parallel evaluation of {total} repositories (batch size: {batch_size})")
        
        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch = repositories[batch_start:batch_end]
            
            # Create evaluation tasks for this batch
            tasks = []
            for repo in batch:
                task = self._evaluate_single_repository_safe(
                    analysis_id, repo, github_token, completed + len(tasks) + 1, total
                )
                tasks.append(task)
            
            # Execute batch in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(batch_results):
                repo = batch[i]
                if isinstance(result, Exception):
                    logger.error(f"[{analysis_id}] Error evaluating {repo['name']}: {result}")
                    repo['evaluated'] = False
                    repo['evaluation'] = None
                else:
                    repo['evaluation'] = result
                    repo['evaluated'] = True
                    evaluated_repos.append(repo)
                
                completed += 1
                
                # Update progress after each completion
                await self._update_progress(analysis_id, {
                    'evaluated': completed,
                    'percentage': 30 + int((completed / total) * 65),  # 30-95%
                    'current_message': f"Evaluating {completed} of {total} repositories..."
                })
        
        elapsed_time = time.time() - start_time
        if total > 0:
            logger.info(
                f"[{analysis_id}] Parallel evaluation complete: {len(evaluated_repos)}/{total} successful "
                f"in {elapsed_time:.2f}s (avg {elapsed_time/total:.2f}s per repo)"
            )
        else:
            logger.info(f"[{analysis_id}] No repositories to evaluate (completed in {elapsed_time:.2f}s)")
        
        # Final progress update
        await self._update_progress(analysis_id, {
            'evaluated': len(evaluated_repos),
            'percentage': 95
        })
        
        return evaluated_repos
    
    async def _evaluate_single_repository_safe(
        self,
        analysis_id: str,
        repo: Dict[str, Any],
        github_token: Optional[str],
        index: int,
        total: int
    ) -> Dict[str, Any]:
        """
        Safely evaluate a single repository with error handling.
        
        Args:
            analysis_id: Analysis identifier for logging
            repo: Repository dictionary
            github_token: Optional GitHub token
            index: Current repository index (for logging)
            total: Total repositories (for logging)
            
        Returns:
            Evaluation data dictionary
            
        Raises:
            Exception: If evaluation fails (caught by caller)
        """
        logger.debug(f"[{analysis_id}] Evaluating {index}/{total}: {repo['name']}")
        evaluation = await self._evaluate_single_repository(repo, github_token)
        return evaluation
    
    async def _evaluate_single_repository(
        self,
        repo: Dict[str, Any],
        github_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single repository using the enhanced evaluation service.
        
        Args:
            repo: Repository dictionary
            github_token: Optional GitHub token
            
        Returns:
            Evaluation data dictionary
        """
        # Use enhanced evaluation service for metadata-based evaluation
        evaluation = await self.evaluator.evaluate_repository_simple(repo, github_token)
        
        return evaluation
    
    def _calculate_overall_score(self, evaluated_repos: List[Dict[str, Any]]) -> Optional[float]:
        """
        Calculate weighted overall developer score using ScoreCalculationService.
        
        Args:
            evaluated_repos: List of evaluated repositories
            
        Returns:
            Overall score (0-100) or None if no evaluated repositories
        """
        return self.score_calculator.calculate_overall_score(evaluated_repos)
    
    async def _update_status(
        self,
        analysis_id: str,
        status: AnalysisStatus,
        message: str
    ):
        """Update analysis status and message"""
        await self.state_storage.update_state(analysis_id, {
            'status': status,
            'current_phase': status.value,
            'current_message': message,
            'updated_at': datetime.utcnow().isoformat()
        })
    
    async def _update_progress(self, analysis_id: str, progress_updates: Dict[str, Any]):
        """Update analysis progress"""
        state = await self.state_storage.get_state(analysis_id)
        if state:
            progress = state.get('progress', {})
            progress.update(progress_updates)
            
            # Update message if evaluated count changed
            if 'evaluated' in progress_updates and 'to_evaluate' in progress:
                evaluated = progress['evaluated']
                to_evaluate = progress['to_evaluate']
                progress['current_message'] = f"Evaluating {evaluated} of {to_evaluate} repositories..."
            
            await self.state_storage.update_state(analysis_id, {
                'progress': progress,
                'updated_at': datetime.utcnow().isoformat()
            })
    
    async def _store_results(self, analysis_id: str, results: Dict[str, Any]):
        """Store final analysis results"""
        await self.state_storage.update_state(analysis_id, {
            **results,
            'updated_at': datetime.utcnow().isoformat()
        })
    
    async def _update_user_rankings_with_categories(
        self, 
        username: str, 
        category_distribution: Dict[str, int],
        overall_score: float
    ):
        """
        Update user_rankings collection with repository category counts and calculate rankings.
        This method:
        1. Syncs user data from user_profiles and analysis_states to user_rankings
        2. Calculates regional and university rankings
        3. Updates user_rankings with all ranking data
        """
        try:
            from app.db_connection import get_database
            
            db = await get_database()
            if db is None:
                logger.warning("Database not available, skipping user_rankings update")
                return
            
            # Step 1: Sync user data to user_rankings (combines profile + analysis data)
            logger.info(f"🔄 Syncing user_rankings for {username}")
            try:
                from app.services.user_rankings_sync_service import UserRankingsSyncService
                sync_service = UserRankingsSyncService(db)
                sync_result = await sync_service.sync_single_user(username)
                
                if sync_result["success"]:
                    logger.info(f"✅ Synced user_rankings for {username}")
                else:
                    logger.warning(f"⚠️  Sync failed for {username}: {sync_result.get('error')}")
                    # Continue anyway - try to update what we can
            except Exception as sync_error:
                logger.error(f"❌ Sync error for {username}: {sync_error}")
                # Continue anyway - try to update what we can
            
            # Step 2: Update category counts (in case sync didn't get latest)
            update_result = await db.user_rankings.update_one(
                {"github_username": username},
                {
                    "$set": {
                        "flagship_count": category_distribution.get('flagship', 0),
                        "significant_count": category_distribution.get('significant', 0),
                        "supporting_count": category_distribution.get('supporting', 0),
                        "overall_score": round(overall_score, 1) if overall_score else 0,
                        "last_analysis_date": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if update_result.modified_count > 0:
                logger.info(
                    f"✅ Updated user_rankings for {username} with category counts: "
                    f"flagship={category_distribution.get('flagship', 0)}, "
                    f"significant={category_distribution.get('significant', 0)}, "
                    f"supporting={category_distribution.get('supporting', 0)}"
                )
            else:
                logger.warning(f"⚠️  No user_rankings document found for {username}")
                return
            
            # Step 3: Calculate rankings (regional and university)
            logger.info(f"📊 Calculating rankings for {username}")
            try:
                # Get user_id from user_rankings
                ranking_doc = await db.user_rankings.find_one({"github_username": username})
                if not ranking_doc:
                    logger.warning(f"⚠️  Cannot calculate rankings - no user_rankings doc for {username}")
                    return
                
                user_id = ranking_doc.get("user_id")
                if not user_id:
                    logger.warning(f"⚠️  Cannot calculate rankings - no user_id for {username}")
                    return
                
                # Use enhanced ranking service to calculate rankings
                from app.services.enhanced_ranking_service import EnhancedRankingService
                ranking_service = EnhancedRankingService(db)
                ranking_result = await ranking_service.update_rankings_for_user(user_id)
                
                if ranking_result.get("success"):
                    logger.info(f"✅ Rankings calculated for {username}")
                    if ranking_result.get('regional_result'):
                        reg = ranking_result['regional_result']
                        logger.info(f"   - Regional: Rank {reg.get('user_rank')} of {reg.get('total_users')} ({reg.get('percentile', 0):.1f}%)")
                    if ranking_result.get('university_result'):
                        uni = ranking_result['university_result']
                        logger.info(f"   - University: Rank {uni.get('user_rank')} of {uni.get('total_users')} ({uni.get('percentile', 0):.1f}%)")
                else:
                    logger.warning(f"⚠️  Ranking calculation had issues: {ranking_result.get('error')}")
                    
            except Exception as ranking_error:
                logger.error(f"❌ Ranking calculation error for {username}: {ranking_error}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Don't fail the analysis if ranking calculation fails
                
        except Exception as e:
            logger.error(f"Failed to update user_rankings with categories: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't fail the analysis if this update fails
    
    async def _store_error(self, analysis_id: str, error_message: str):
        """Store analysis error"""
        await self.state_storage.update_state(analysis_id, {
            'status': AnalysisStatus.FAILED,
            'error': error_message,
            'current_message': f'Analysis failed: {error_message}',
            'updated_at': datetime.utcnow().isoformat()
        })
        
        # Log analytics event for failure
        self._log_analytics_event('analysis_failed', {
            'analysis_id': analysis_id,
            'error': error_message
        })
    
    def _merge_evaluation_results(
        self,
        categorized_repos: List[Dict[str, Any]],
        evaluated_repos: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge evaluation results back into categorized repositories.
        Preserves category and importance_score while adding evaluation data.
        
        Args:
            categorized_repos: List of repositories with category and importance_score
            evaluated_repos: List of repositories with evaluation data
            
        Returns:
            List of repositories with all fields (category, importance_score, evaluated, evaluation)
        """
        # Create lookup dict for evaluated repos
        evaluated_lookup = {repo['name']: repo for repo in evaluated_repos}
        
        # Merge data
        final_repos = []
        for repo in categorized_repos:
            repo_name = repo['name']
            if repo_name in evaluated_lookup:
                # Merge evaluation data
                evaluated_data = evaluated_lookup[repo_name]
                repo['evaluated'] = True
                repo['evaluation'] = evaluated_data.get('evaluation', {})
            else:
                repo['evaluated'] = False
                repo['evaluation'] = None
            
            final_repos.append(repo)
        
        logger.debug(f"Merged evaluation results: {len(final_repos)} total, {len(evaluated_lookup)} evaluated")
        return final_repos
    
    def _get_category_distribution(self, repositories: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate distribution of repositories across categories.
        
        Args:
            repositories: List of repositories with category field
            
        Returns:
            Dictionary with counts for each category (flagship, significant, supporting)
        """
        distribution = {'flagship': 0, 'significant': 0, 'supporting': 0}
        for repo in repositories:
            category = repo.get('category', 'supporting')
            if category in distribution:
                distribution[category] += 1
            else:
                # Handle unexpected category values
                logger.warning(f"Unexpected category '{category}' for repo {repo.get('name')}, treating as 'supporting'")
                distribution['supporting'] += 1
        
        logger.info(f"Category distribution: {distribution}")
        return distribution
    
    def _log_analytics_event(self, event_type: str, data: Dict[str, Any]):
        """
        Log analytics event with structured data.
        
        Args:
            event_type: Type of analytics event
            data: Event data dictionary
        """
        analytics_logger.info(
            f"ANALYTICS_EVENT: {event_type}",
            extra={
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                **data
            }
        )
    
    async def get_analysis_status(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current analysis status.
        
        Args:
            analysis_id: Unique analysis identifier
            
        Returns:
            Analysis state dictionary or None if not found
        """
        return await self.state_storage.get_state(analysis_id)
    
    async def get_analysis_results(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete analysis results.
        
        Args:
            analysis_id: Unique analysis identifier
            
        Returns:
            Analysis results dictionary or None if not found or not complete
        """
        state = await self.state_storage.get_state(analysis_id)
        
        if not state:
            return None
        
        if state.get('status') != AnalysisStatus.COMPLETE:
            return None
        
        return {
            'analysis_id': analysis_id,
            'username': state.get('username'),
            'analyzed': True,
            'analyzedAt': state.get('completed_at'),
            'overallScore': state.get('overall_score'),  # Frontend expects camelCase
            'evaluatedCount': state.get('evaluated_count'),
            'flagshipCount': state.get('flagship_count'),
            'significantCount': state.get('significant_count'),
            'supportingCount': state.get('supporting_count'),
            'categoryDistribution': {
                'flagship': state.get('flagship_count', 0),
                'significant': state.get('significant_count', 0),
                'supporting': state.get('supporting_count', 0)
            },
            'repositories': state.get('repositories', [])
        }


class InMemoryStateStorage:
    """In-memory storage for analysis state (for development/testing)"""
    
    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}
    
    async def store_state(self, analysis_id: str, state: Dict[str, Any]):
        """Store analysis state"""
        self._storage[analysis_id] = state
    
    async def get_state(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis state"""
        return self._storage.get(analysis_id)
    
    async def update_state(self, analysis_id: str, updates: Dict[str, Any]):
        """Update analysis state"""
        if analysis_id in self._storage:
            self._storage[analysis_id].update(updates)
    
    async def delete_state(self, analysis_id: str):
        """Delete analysis state"""
        if analysis_id in self._storage:
            del self._storage[analysis_id]
