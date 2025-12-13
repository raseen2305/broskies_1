"""
Scan Storage Service
Handles database storage for Stage 1 quick scan results
Target: <0.2 seconds for parallel writes
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..config import get_config
from ..utils import get_logger


class ScanStorageService:
    """
    Storage service for Stage 1 quick scan results
    
    Handles:
    - User profile storage in user_profiles collection
    - Repository storage in repositories collection
    - Parallel writes for performance
    
    Target: <0.2 seconds total
    """
    
    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize scan storage service
        
        Args:
            database: MongoDB database instance
            logger: Optional logger instance
        """
        self.db = database
        self.config = get_config()
        self.logger = logger or get_logger(__name__)
    
    async def store_scan_results(
        self,
        user_id: str,
        user_data: Dict[str, Any],
        repositories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Store complete scan results in parallel
        
        Args:
            user_id: User ID from auth system
            user_data: User profile data
            repositories: List of repositories with importance scores
            
        Returns:
            Dictionary with storage results
            
        Raises:
            RuntimeError: If storage fails
        """
        self.logger.info(
            f"Storing scan results for user {user_id}: "
            f"{len(repositories)} repositories"
        )
        start_time = datetime.utcnow()
        
        try:
            # Execute storage operations in parallel
            user_result, repos_result = await asyncio.gather(
                self._store_user_profile(user_id, user_data, repositories),
                self._store_repositories(user_id, repositories),
                return_exceptions=True
            )
            
            # Check for errors
            if isinstance(user_result, Exception):
                raise RuntimeError(f"Failed to store user profile: {user_result}")
            
            if isinstance(repos_result, Exception):
                raise RuntimeError(f"Failed to store repositories: {repos_result}")
            
            # Calculate storage time
            storage_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(
                f"Stored scan results in {storage_time:.2f}s "
                f"(user: {user_result}, repos: {repos_result})"
            )
            
            # Check performance target
            if storage_time > 0.2:
                self.logger.warning(
                    f"Storage time {storage_time:.2f}s exceeded target 0.2s"
                )
            
            return {
                'user_stored': user_result,
                'repositories_stored': repos_result,
                'storage_time': round(storage_time, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to store scan results: {e}")
            raise RuntimeError(f"Storage failed: {e}")
    
    async def _store_user_profile(
        self,
        user_id: str,
        user_data: Dict[str, Any],
        repositories: List[Dict[str, Any]]
    ) -> str:
        """
        Store or update user profile
        
        Args:
            user_id: User ID
            user_data: User profile data
            repositories: List of repositories (for counts)
            
        Returns:
            User profile ID
        """
        # Calculate repository counts by category
        flagship_count = sum(
            1 for r in repositories if r.get('category') == 'flagship'
        )
        significant_count = sum(
            1 for r in repositories if r.get('category') == 'significant'
        )
        supporting_count = sum(
            1 for r in repositories if r.get('category') == 'supporting'
        )
        
        # Prepare user profile document
        profile_doc = {
            'user_id': user_id,
            'github_username': user_data.get('username'),
            'name': user_data.get('name'),
            'bio': user_data.get('bio'),
            'avatar_url': user_data.get('avatar_url'),
            'email': user_data.get('email'),
            'location': user_data.get('location'),
            'company': user_data.get('company'),
            'website': user_data.get('website'),
            'twitter': user_data.get('twitter'),
            'followers': user_data.get('followers', 0),
            'following': user_data.get('following', 0),
            'public_repos': len(repositories),
            'scan_completed': True,
            'scanned_at': datetime.utcnow(),
            'flagship_count': flagship_count,
            'significant_count': significant_count,
            'supporting_count': supporting_count,
            'updated_at': datetime.utcnow()
        }
        
        # Upsert user profile
        result = await self.db.user_profiles.update_one(
            {'user_id': user_id},
            {'$set': profile_doc, '$setOnInsert': {'created_at': datetime.utcnow()}},
            upsert=True
        )
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            # Find the existing document
            existing = await self.db.user_profiles.find_one({'user_id': user_id})
            return str(existing['_id']) if existing else user_id
    
    async def _store_repositories(
        self,
        user_id: str,
        repositories: List[Dict[str, Any]]
    ) -> int:
        """
        Store repositories with importance scores
        
        Uses bulk operations for performance
        
        Args:
            user_id: User ID
            repositories: List of repositories with importance scores
            
        Returns:
            Number of repositories stored
        """
        if not repositories:
            return 0
        
        # Prepare bulk operations
        operations = []
        
        for repo in repositories:
            # Prepare repository document
            repo_doc = {
                'user_id': user_id,
                'github_id': repo.get('github_id', repo.get('id')),
                'name': repo.get('name'),
                'full_name': repo.get('full_name'),
                'description': repo.get('description'),
                'url': repo.get('url'),
                'homepage': repo.get('homepage'),
                'stars': repo.get('stars', 0),
                'forks': repo.get('forks', 0),
                'watchers': repo.get('watchers', 0),
                'size': repo.get('size', 0),
                'language': repo.get('language'),
                'languages': repo.get('languages', {}),
                'topics': repo.get('topics', []),
                'created_at': repo.get('created_at'),
                'updated_at': repo.get('updated_at'),
                'pushed_at': repo.get('pushed_at'),
                'has_issues': repo.get('has_issues', False),
                'has_wiki': repo.get('has_wiki', False),
                'license': repo.get('license'),
                'commit_count': repo.get('commit_count', 0),
                'open_issues': repo.get('open_issues', 0),
                'open_prs': repo.get('open_prs', 0),
                'is_fork': repo.get('is_fork', False),
                'is_private': repo.get('is_private', False),
                'has_readme': repo.get('has_readme', False),
                'has_license_file': repo.get('has_license_file', False),
                'has_tests': repo.get('has_tests', False),
                'has_ci_cd': repo.get('has_ci_cd', False),
                # Importance scoring fields
                'importance_score': repo.get('importance_score', 0.0),
                'category': repo.get('category', 'supporting'),
                # Analysis status
                'analyzed': False,
                'analyzed_at': None,
                # Metadata
                'updated_at': datetime.utcnow()
            }
            
            # Create update operation
            from pymongo import UpdateOne
            operations.append(
                UpdateOne(
                    {
                        'user_id': user_id,
                        'github_id': repo_doc['github_id']
                    },
                    {
                        '$set': repo_doc,
                        '$setOnInsert': {'created_at': datetime.utcnow()}
                    },
                    upsert=True
                )
            )
        
        # Execute bulk write
        result = await self.db.repositories.bulk_write(operations, ordered=False)
        
        # Return total count (upserted + modified)
        total_stored = result.upserted_count + result.modified_count
        
        self.logger.info(
            f"Stored {total_stored} repositories "
            f"({result.upserted_count} new, {result.modified_count} updated)"
        )
        
        return total_stored
    
    async def get_user_repositories(
        self,
        user_id: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get repositories for a user
        
        Args:
            user_id: User ID
            category: Optional category filter
            
        Returns:
            List of repositories
        """
        query = {'user_id': user_id}
        
        if category:
            query['category'] = category
        
        cursor = self.db.repositories.find(query).sort('importance_score', -1)
        repositories = await cursor.to_list(length=None)
        
        return repositories
    
    async def get_repositories_for_analysis(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get repositories selected for Stage 2 analysis
        
        Returns flagship and significant repositories, limited to 15
        
        Args:
            user_id: User ID
            
        Returns:
            List of repositories for analysis
        """
        cursor = self.db.repositories.find({
            'user_id': user_id,
            'category': {'$in': ['flagship', 'significant']}
        }).sort('importance_score', -1).limit(self.config.MAX_REPOS_TO_ANALYZE)
        
        repositories = await cursor.to_list(length=None)
        
        return repositories
    
    async def update_repository_analysis(
        self,
        repo_id: str,
        analysis_data: Dict[str, Any]
    ) -> bool:
        """
        Update repository with analysis results
        
        Args:
            repo_id: Repository ID
            analysis_data: Analysis results
            
        Returns:
            True if updated successfully
        """
        update_doc = {
            'analyzed': True,
            'analyzed_at': datetime.utcnow(),
            **analysis_data
        }
        
        result = await self.db.repositories.update_one(
            {'_id': repo_id},
            {'$set': update_doc}
        )
        
        return result.modified_count > 0
    
    async def get_scan_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get scan summary for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with scan summary
        """
        # Get user profile
        profile = await self.db.user_profiles.find_one({'user_id': user_id})
        
        if not profile:
            return {
                'scan_completed': False,
                'repositories': 0
            }
        
        # Get repository counts
        total_repos = await self.db.repositories.count_documents({'user_id': user_id})
        flagship = await self.db.repositories.count_documents({
            'user_id': user_id,
            'category': 'flagship'
        })
        significant = await self.db.repositories.count_documents({
            'user_id': user_id,
            'category': 'significant'
        })
        supporting = await self.db.repositories.count_documents({
            'user_id': user_id,
            'category': 'supporting'
        })
        
        return {
            'scan_completed': profile.get('scan_completed', False),
            'scanned_at': profile.get('scanned_at'),
            'repositories': total_repos,
            'flagship': flagship,
            'significant': significant,
            'supporting': supporting
        }
