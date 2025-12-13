"""
Stage 2 Deep Analysis Orchestrator
Orchestrates code extraction, analysis, scoring, and ranking updates
Target: <35 seconds for 13 repositories
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.services.scoring import (
    ComplexityAnalyzer,
    ACIDScorer,
    OverallScoreCalculator
)
from app.services.storage import (
    UserStorageService,
    RepositoryStorageService,
    AnalysisStorageService,
    RankingStorageService
)
from .progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    Orchestrates Stage 2 deep analysis workflow
    
    Workflow:
    1. Select Flagship and Significant repositories (limit 15)
    2. Extract code from repositories (batch processing)
    3. Analyze code and calculate ACID scores
    4. Calculate overall score
    5. Update rankings
    6. Store all results
    
    Target: <35 seconds for 13 repositories
    """
    
    # Configuration
    BATCH_SIZE = 3  # Process 3 repositories at a time
    MAX_REPOS = 15  # Maximum repositories to analyze
    MAX_FILES_PER_REPO = 50  # Maximum files per repository
    
    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        github_rest_service: Any,  # GitHub REST service for code extraction
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize analysis orchestrator
        
        Args:
            database: MongoDB database instance
            github_rest_service: GitHub REST API service
            logger: Optional logger instance
        """
        self.db = database
        self.github_rest = github_rest_service
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize services
        self.complexity_analyzer = ComplexityAnalyzer()
        self.acid_scorer = ACIDScorer()
        self.overall_calculator = OverallScoreCalculator()
        
        # Initialize storage services
        self.user_storage = UserStorageService(database)
        self.repo_storage = RepositoryStorageService(database)
        self.analysis_storage = AnalysisStorageService(database)
        self.ranking_storage = RankingStorageService(database)
        
        # Initialize progress tracker
        self.progress_tracker = ProgressTracker(database)
    
    async def execute_deep_analysis(
        self,
        user_id: str,
        github_token: str
    ) -> Dict[str, Any]:
        """
        Execute Stage 2 deep analysis
        
        Args:
            user_id: User ID
            github_token: GitHub OAuth token
            
        Returns:
            Dictionary with analysis results
            
        Raises:
            ValueError: If user_id or token is invalid
            RuntimeError: If analysis fails
        """
        if not user_id or not github_token:
            raise ValueError("user_id and github_token are required")
        
        self.logger.info(f"Starting deep analysis for user: {user_id}")
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Select repositories for analysis
            self.logger.info("Step 1: Selecting repositories...")
            repositories = await self._select_repositories(user_id)
            
            if not repositories:
                raise RuntimeError("No repositories selected for analysis")
            
            total_repos = len(repositories)
            self.logger.info(f"Selected {total_repos} repositories for analysis")
            
            # Initialize progress tracking
            await self.progress_tracker.start_analysis(user_id, total_repos)
            
            # Step 2: Analyze repositories in batches
            self.logger.info("Step 2: Analyzing repositories...")
            analyzed_repos = await self._analyze_repositories_batch(
                repositories,
                github_token,
                user_id
            )
            
            # Step 3: Calculate overall score
            self.logger.info("Step 3: Calculating overall score...")
            overall_breakdown = await self._calculate_overall_score(user_id)
            
            # Step 4: Update user scores
            self.logger.info("Step 4: Updating user scores...")
            await self._update_user_scores(user_id, overall_breakdown)
            
            # Step 5: Update rankings
            self.logger.info("Step 5: Updating rankings...")
            await self._update_rankings(user_id)
            
            # Complete progress tracking
            await self.progress_tracker.complete_analysis(user_id)
            
            # Calculate total time
            analysis_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(
                f"Deep analysis completed in {analysis_time:.2f}s "
                f"({total_repos} repositories)"
            )
            
            # Check performance target
            if analysis_time > 35.0:
                self.logger.warning(
                    f"Analysis time {analysis_time:.2f}s exceeded target 35s"
                )
            
            return {
                'success': True,
                'user_id': user_id,
                'repositories_analyzed': total_repos,
                'overall_score': overall_breakdown.overall_score,
                'flagship_average': overall_breakdown.flagship_average,
                'significant_average': overall_breakdown.significant_average,
                'analysis_time': round(analysis_time, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Deep analysis failed: {e}")
            await self.progress_tracker.fail_analysis(user_id, str(e))
            raise RuntimeError(f"Failed to execute deep analysis: {e}")
    
    async def _select_repositories(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Select repositories for analysis
        
        Selects flagship and significant repositories, limited to MAX_REPOS
        
        Args:
            user_id: User ID
            
        Returns:
            List of repository dictionaries
        """
        # Get repositories for analysis from storage
        repos = await self.repo_storage.get_repositories_for_analysis(
            user_id,
            limit=self.MAX_REPOS
        )
        
        # Convert to dictionaries
        repo_dicts = [
            {
                'id': str(repo.id),
                'name': repo.name,
                'full_name': repo.full_name,
                'category': repo.category,
                'importance_score': repo.importance_score,
                'clone_url': repo.clone_url,
                'default_branch': repo.default_branch,
                'language': repo.language,
                'has_readme': getattr(repo, 'has_readme', False),
                'has_license': getattr(repo, 'license', None) is not None,
                'has_tests': getattr(repo, 'has_tests', False),
                'has_ci_cd': getattr(repo, 'has_ci_cd', False)
            }
            for repo in repos
        ]
        
        return repo_dicts
    
    async def _analyze_repositories_batch(
        self,
        repositories: List[Dict[str, Any]],
        github_token: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze repositories in batches
        
        Processes BATCH_SIZE repositories at a time for optimal performance
        
        Args:
            repositories: List of repository dictionaries
            github_token: GitHub OAuth token
            user_id: User ID
            
        Returns:
            List of analyzed repository results
        """
        analyzed = []
        total = len(repositories)
        
        # Process in batches
        for i in range(0, total, self.BATCH_SIZE):
            batch = repositories[i:i + self.BATCH_SIZE]
            batch_num = (i // self.BATCH_SIZE) + 1
            
            self.logger.info(
                f"Processing batch {batch_num} "
                f"({len(batch)} repositories)"
            )
            
            # Analyze batch in parallel
            batch_results = await asyncio.gather(
                *[
                    self._analyze_single_repository(repo, github_token, user_id)
                    for repo in batch
                ],
                return_exceptions=True
            )
            
            # Process results
            for j, result in enumerate(batch_results):
                repo = batch[j]
                
                if isinstance(result, Exception):
                    self.logger.error(
                        f"Failed to analyze {repo['name']}: {result}"
                    )
                    # Continue with other repositories
                else:
                    analyzed.append(result)
                
                # Update progress
                current = i + j + 1
                await self.progress_tracker.update_progress(
                    user_id,
                    current,
                    total,
                    repo['name']
                )
        
        return analyzed
    
    async def _analyze_single_repository(
        self,
        repo: Dict[str, Any],
        github_token: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Analyze a single repository
        
        Args:
            repo: Repository dictionary
            github_token: GitHub OAuth token
            user_id: User ID
            
        Returns:
            Analysis results dictionary
        """
        repo_id = repo['id']
        repo_name = repo['name']
        
        self.logger.info(f"Analyzing repository: {repo_name}")
        
        try:
            # Step 1: Extract code files
            files = await self._extract_code_files(repo, github_token)
            
            if not files:
                self.logger.warning(f"No code files found in {repo_name}")
                return {
                    'repo_id': repo_id,
                    'success': False,
                    'error': 'No code files found'
                }
            
            # Step 2: Analyze complexity
            complexity = self.complexity_analyzer.analyze_repository(files)
            
            # Step 3: Calculate ACID scores
            repo_metadata = {
                'has_readme': repo.get('has_readme', False),
                'has_license': repo.get('has_license', False),
                'has_tests': repo.get('has_tests', False),
                'has_ci_cd': repo.get('has_ci_cd', False)
            }
            
            acid_scores = self.acid_scorer.calculate_acid_scores(
                files,
                repo_metadata
            )
            
            # Step 4: Calculate repository overall score
            repo_overall_score = acid_scores.overall
            
            # Step 5: Store analysis results
            await self._store_analysis_results(
                repo_id,
                user_id,
                acid_scores,
                complexity,
                repo_overall_score,
                files
            )
            
            self.logger.info(
                f"Completed analysis for {repo_name}: "
                f"ACID={acid_scores.overall:.1f}"
            )
            
            return {
                'repo_id': repo_id,
                'repo_name': repo_name,
                'success': True,
                'acid_scores': {
                    'atomicity': acid_scores.atomicity,
                    'consistency': acid_scores.consistency,
                    'isolation': acid_scores.isolation,
                    'durability': acid_scores.durability,
                    'overall': acid_scores.overall
                },
                'overall_score': repo_overall_score
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {repo_name}: {e}")
            return {
                'repo_id': repo_id,
                'repo_name': repo_name,
                'success': False,
                'error': str(e)
            }
    
    async def _extract_code_files(
        self,
        repo: Dict[str, Any],
        github_token: str
    ) -> List[Tuple[str, str, str]]:
        """
        Extract code files from repository
        
        Args:
            repo: Repository dictionary
            github_token: GitHub OAuth token
            
        Returns:
            List of (filename, language, code) tuples
        """
        # This is a placeholder - actual implementation would use GitHub REST API
        # to fetch file tree and download code files
        
        # For now, return empty list
        # In production, this would:
        # 1. Get file tree from GitHub REST API
        # 2. Filter to code files (by extension)
        # 3. Download up to MAX_FILES_PER_REPO files
        # 4. Return list of (filename, language, code) tuples
        
        self.logger.warning(
            f"Code extraction not implemented for {repo['name']} - "
            "using mock data"
        )
        
        # Mock data for testing
        return []
    
    async def _store_analysis_results(
        self,
        repo_id: str,
        user_id: str,
        acid_scores: Any,
        complexity: Any,
        overall_score: float,
        files: List[Tuple[str, str, str]]
    ) -> None:
        """
        Store analysis results in database
        
        Args:
            repo_id: Repository ID
            user_id: User ID
            acid_scores: ACID scores object
            complexity: Complexity metrics object
            overall_score: Overall repository score
            files: List of analyzed files
        """
        from app.models.repository import ACIDScore, QualityMetrics
        
        # Convert to model objects
        acid_score_model = ACIDScore(
            atomicity=acid_scores.atomicity,
            consistency=acid_scores.consistency,
            isolation=acid_scores.isolation,
            durability=acid_scores.durability,
            overall=acid_scores.overall
        )
        
        quality_metrics = QualityMetrics(
            readability=complexity.maintainability_index,
            maintainability=complexity.maintainability_index,
            security=50.0,  # Placeholder
            test_coverage=0.0,  # Placeholder
            documentation=50.0  # Placeholder
        )
        
        # Calculate language stats
        language_stats = {}
        for filename, language, code in files:
            if language not in language_stats:
                language_stats[language] = 0
            language_stats[language] += len(code.split('\n'))
        
        # Store complete evaluation
        await self.analysis_storage.update_complete_evaluation(
            repo_id=repo_id,
            user_id=user_id,
            acid_scores=acid_score_model,
            quality_metrics=quality_metrics,
            complexity_score=complexity.cyclomatic_complexity,
            best_practices_score=acid_scores.overall,
            language_stats=language_stats,
            file_count=len(files),
            total_lines=complexity.lines_of_code
        )
        
        # Update repository with analysis results
        await self.repo_storage.update_repository_analysis(
            repo_id=repo_id,
            acid_scores={
                'atomicity': acid_scores.atomicity,
                'consistency': acid_scores.consistency,
                'isolation': acid_scores.isolation,
                'durability': acid_scores.durability,
                'overall': acid_scores.overall
            },
            complexity_metrics={
                'cyclomatic': complexity.cyclomatic_complexity,
                'cognitive': complexity.cognitive_complexity,
                'maintainability': complexity.maintainability_index,
                'lines_of_code': complexity.lines_of_code,
                'function_count': complexity.function_count,
                'class_count': complexity.class_count
            },
            overall_score=overall_score
        )
    
    async def _calculate_overall_score(
        self,
        user_id: str
    ) -> Any:
        """
        Calculate overall developer score
        
        Args:
            user_id: User ID
            
        Returns:
            OverallScoreBreakdown object
        """
        # Get all analyzed repositories
        repos = await self.repo_storage.get_user_repositories(
            user_id,
            analyzed_only=True
        )
        
        # Convert to dictionaries
        repo_dicts = [
            {
                'category': repo.category,
                'analyzed': repo.analyzed,
                'overall_score': repo.overall_score
            }
            for repo in repos
        ]
        
        # Calculate overall score
        breakdown = self.overall_calculator.calculate_overall_score(repo_dicts)
        
        return breakdown
    
    async def _update_user_scores(
        self,
        user_id: str,
        breakdown: Any
    ) -> None:
        """
        Update user scores in database
        
        Args:
            user_id: User ID
            breakdown: OverallScoreBreakdown object
        """
        await self.user_storage.update_user_scores(
            user_id=user_id,
            overall_score=breakdown.overall_score,
            flagship_count=breakdown.flagship_count,
            significant_count=breakdown.significant_count,
            supporting_count=0  # Not analyzed
        )
    
    async def _update_rankings(
        self,
        user_id: str
    ) -> None:
        """
        Update regional and university rankings
        
        Args:
            user_id: User ID
        """
        # Get user profile
        user = await self.user_storage.get_user_by_id(user_id)
        
        if not user:
            self.logger.warning(f"User not found: {user_id}")
            return
        
        # Update rankings
        await self.ranking_storage.update_all_rankings(
            user_id=user_id,
            github_username=user.github_username,
            name=user.full_name,
            region=user.region,
            state=user.state,
            district=user.district,
            university=user.university,
            university_short=user.university_short,
            overall_score=user.overall_score or 0.0
        )
