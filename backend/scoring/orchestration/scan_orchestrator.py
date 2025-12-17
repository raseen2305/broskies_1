"""
Stage 1 Quick Scan Orchestrator
Orchestrates OAuth to GraphQL query flow with parallel importance calculation
Target: <1 second total execution time
"""

import asyncio
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..github.graphql_service import GitHubGraphQLService
from ..scoring.importance_scorer import ImportanceScorer
from ..storage.scan_storage import ScanStorageService
from ..config import get_config
from ..utils import get_logger


class ScanOrchestrator:
    """
    Orchestrates Stage 1 quick scan workflow
    
    Workflow:
    1. Fetch user + repositories via GraphQL (0.5s)
    2. Calculate importance scores in parallel (0.25s)
    3. Categorize repositories (instant)
    4. Return results for database storage (0.2s)
    
    Total target: <1 second
    """
    
    def __init__(
        self,
        database: Optional[AsyncIOMotorDatabase] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize scan orchestrator
        
        Args:
            database: MongoDB database instance (optional)
            logger: Optional logger instance
        """
        self.config = get_config()
        self.logger = logger or get_logger(__name__)
        self.graphql_service = GitHubGraphQLService(logger=self.logger)
        self.importance_scorer = ImportanceScorer(logger=self.logger)
        self.storage_service = None
        
        if database:
            self.storage_service = ScanStorageService(database, logger=self.logger)
    
    async def execute_quick_scan(
        self,
        username: str,
        token: str,
        user_id: Optional[str] = None,
        store_results: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Stage 1 quick scan
        
        Args:
            username: GitHub username
            token: GitHub OAuth token
            user_id: User ID for database storage (required if store_results=True)
            store_results: Whether to store results in database
            
        Returns:
            Dictionary containing:
                - user: User profile data
                - repositories: List of repositories with importance scores
                - summary: Summary statistics
                - scan_time: Total execution time
                - storage_result: Storage results (if stored)
                
        Raises:
            ValueError: If username or token is invalid
            RuntimeError: If scan fails
        """
        if not username or not token:
            raise ValueError("Username and token are required")
        
        if store_results and not user_id:
            raise ValueError("user_id is required when store_results=True")
        
        self.logger.info(f"Starting quick scan for user: {username}")
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Fetch user and repositories via GraphQL (target: 0.5s)
            self.logger.info("Step 1: Fetching user and repositories...")
            user_data, repos_data = await self.graphql_service.get_user_and_repositories(
                username, token
            )
            
            # Step 2: Calculate importance scores in parallel (target: 0.25s)
            self.logger.info(f"Step 2: Calculating importance for {len(repos_data)} repositories...")
            repos_with_scores = await self._calculate_importance_parallel(repos_data)
            
            # Step 3: Categorize repositories (instant)
            self.logger.info("Step 3: Categorizing repositories...")
            categorized_repos = self._categorize_repositories(repos_with_scores)
            
            # Step 4: Generate summary
            summary = self._generate_summary(categorized_repos)
            
            # Step 5: Store results in database (target: 0.2s) - if enabled
            storage_result = None
            if store_results and self.storage_service:
                self.logger.info("Step 4: Storing results in database...")
                storage_result = await self.storage_service.store_scan_results(
                    user_id, user_data, categorized_repos
                )
            
            # Calculate total execution time
            scan_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(
                f"Quick scan completed in {scan_time:.2f}s "
                f"({summary['flagship']} flagship, {summary['significant']} significant, "
                f"{summary['supporting']} supporting)"
            )
            
            # Check performance target
            if scan_time > self.config.STAGE1_TARGET_SECONDS:
                self.logger.warning(
                    f"Scan time {scan_time:.2f}s exceeded target "
                    f"{self.config.STAGE1_TARGET_SECONDS}s"
                )
            
            result = {
                'user': user_data,
                'repositories': categorized_repos,
                'summary': summary,
                'scan_time': round(scan_time, 2)
            }
            
            if storage_result:
                result['storage_result'] = storage_result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Quick scan failed: {e}")
            raise RuntimeError(f"Failed to execute quick scan: {e}")
    
    async def _calculate_importance_parallel(
        self,
        repositories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate importance scores for all repositories in parallel
        
        Args:
            repositories: List of repository data
            
        Returns:
            List of repositories with importance scores added
        """
        if not repositories:
            return []
        
        # Create tasks for parallel execution
        tasks = [
            self._calculate_single_importance(repo)
            for repo in repositories
        ]
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out any errors and log them
        repos_with_scores = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    f"Failed to calculate importance for repository "
                    f"{repositories[i].get('name', 'unknown')}: {result}"
                )
                # Add repository with default score
                repo = repositories[i].copy()
                repo['importance_score'] = 0.0
                repos_with_scores.append(repo)
            else:
                repos_with_scores.append(result)
        
        return repos_with_scores
    
    async def _calculate_single_importance(
        self,
        repo: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate importance score for a single repository
        
        Args:
            repo: Repository data
            
        Returns:
            Repository data with importance_score added
        """
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        importance_score = await loop.run_in_executor(
            None,
            self.importance_scorer.calculate_score,
            repo
        )
        
        # Add score to repository data
        repo_with_score = repo.copy()
        repo_with_score['importance_score'] = importance_score
        
        return repo_with_score
    
    def _categorize_repositories(
        self,
        repositories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Categorize repositories based on importance scores
        
        Args:
            repositories: List of repositories with importance scores
            
        Returns:
            List of repositories with category added
        """
        categorized = []
        
        for repo in repositories:
            importance_score = repo.get('importance_score', 0.0)
            category = self.importance_scorer.categorize(importance_score)
            
            repo_categorized = repo.copy()
            repo_categorized['category'] = category
            categorized.append(repo_categorized)
        
        return categorized
    
    def _generate_summary(
        self,
        repositories: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Generate summary statistics
        
        Args:
            repositories: List of categorized repositories
            
        Returns:
            Dictionary with counts per category
        """
        summary = {
            'total': len(repositories),
            'flagship': 0,
            'significant': 0,
            'supporting': 0
        }
        
        for repo in repositories:
            category = repo.get('category', 'supporting')
            if category in summary:
                summary[category] += 1
        
        return summary
    
    def get_repositories_by_category(
        self,
        repositories: List[Dict[str, Any]],
        category: str
    ) -> List[Dict[str, Any]]:
        """
        Filter repositories by category
        
        Args:
            repositories: List of repositories
            category: Category to filter by
            
        Returns:
            List of repositories in the specified category
        """
        return [
            repo for repo in repositories
            if repo.get('category') == category
        ]
    
    def select_repositories_for_analysis(
        self,
        repositories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Select repositories for Stage 2 deep analysis
        
        Selection criteria:
        - All Flagship repositories
        - All Significant repositories
        - Maximum 15 repositories total
        - If >15, select top 15 by importance score
        
        Args:
            repositories: List of categorized repositories
            
        Returns:
            List of repositories selected for analysis
        """
        # Get flagship and significant repositories
        flagship = self.get_repositories_by_category(repositories, 'flagship')
        significant = self.get_repositories_by_category(repositories, 'significant')
        
        # Combine and sort by importance score
        selected = flagship + significant
        selected.sort(key=lambda r: r.get('importance_score', 0), reverse=True)
        
        # Limit to max repositories
        max_repos = self.config.MAX_REPOS_TO_ANALYZE
        if len(selected) > max_repos:
            self.logger.info(
                f"Limiting analysis to top {max_repos} repositories "
                f"(out of {len(selected)} flagship/significant)"
            )
            selected = selected[:max_repos]
        
        return selected
