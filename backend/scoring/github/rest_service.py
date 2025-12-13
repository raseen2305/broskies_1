"""
GitHub REST Service
Optimized for Stage 2 deep analysis - extracts code files
Target: <1.5 seconds per repository
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import base64

from ..config import get_config
from ..utils import get_logger


class GitHubRESTService:
    """
    GitHub REST API service for Stage 2 code extraction
    
    Fetches repository file tree and downloads code files
    Performance target: <1.5 seconds per repository
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize REST service
        
        Args:
            logger: Optional logger instance
        """
        self.config = get_config()
        self.logger = logger or get_logger(__name__)
        self.endpoint = self.config.GITHUB_REST_ENDPOINT
        self.max_files = self.config.MAX_FILES_PER_REPO
        self.code_extensions = self.config.CODE_EXTENSIONS
    
    async def get_repository_contents(
        self,
        owner: str,
        repo: str,
        token: str
    ) -> List[Dict[str, Any]]:
        """
        Get repository code files
        
        Args:
            owner: Repository owner
            repo: Repository name
            token: GitHub OAuth token
            
        Returns:
            List of code files with content
            
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If API request fails
        """
        if not owner or not repo or not token:
            raise ValueError("Owner, repo, and token are required")
        
        self.logger.info(f"Fetching code for {owner}/{repo}")
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Get file tree
            file_tree = await self._get_file_tree(owner, repo, token)
            
            # Step 2: Filter code files
            code_files = self._filter_code_files(file_tree)
            
            # Step 3: Limit to max files
            if len(code_files) > self.max_files:
                self.logger.info(
                    f"Limiting from {len(code_files)} to {self.max_files} files"
                )
                code_files = code_files[:self.max_files]
            
            # Step 4: Download file contents in parallel
            files_with_content = await self._download_files(
                owner, repo, code_files, token
            )
            
            # Log performance
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(
                f"Fetched {len(files_with_content)} files in {duration:.2f}s"
            )
            
            return files_with_content
            
        except Exception as e:
            self.logger.error(f"Failed to fetch repository contents: {e}")
            raise RuntimeError(f"Failed to fetch code: {e}")
    
    async def _get_file_tree(
        self,
        owner: str,
        repo: str,
        token: str
    ) -> List[Dict[str, Any]]:
        """
        Get repository file tree using Git Trees API
        
        Args:
            owner: Repository owner
            repo: Repository name
            token: GitHub OAuth token
            
        Returns:
            List of file entries
        """
        # First, get the default branch SHA
        url = f"{self.endpoint}/repos/{owner}/{repo}"
        
        async with aiohttp.ClientSession() as session:
            # Get repository info
            async with session.get(
                url,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/vnd.github.v3+json'
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"Failed to get repo info: {response.status} - {text}"
                    )
                
                repo_data = await response.json()
                default_branch = repo_data.get('default_branch', 'main')
            
            # Get tree for default branch (recursive)
            tree_url = f"{self.endpoint}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
            
            async with session.get(
                tree_url,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/vnd.github.v3+json'
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"Failed to get file tree: {response.status} - {text}"
                    )
                
                tree_data = await response.json()
                return tree_data.get('tree', [])
    
    def _filter_code_files(self, file_tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter for code files only
        
        Args:
            file_tree: Complete file tree
            
        Returns:
            Filtered list of code files
        """
        code_files = []
        
        for entry in file_tree:
            # Only process files (not directories)
            if entry.get('type') != 'blob':
                continue
            
            path = entry.get('path', '')
            
            # Check if it's a code file
            if any(path.endswith(ext) for ext in self.code_extensions):
                # Skip test files and vendor directories
                if self._should_skip_file(path):
                    continue
                
                code_files.append({
                    'path': path,
                    'sha': entry.get('sha'),
                    'size': entry.get('size', 0),
                    'url': entry.get('url')
                })
        
        # Sort by size (smaller files first for faster processing)
        code_files.sort(key=lambda x: x['size'])
        
        return code_files
    
    def _should_skip_file(self, path: str) -> bool:
        """
        Check if file should be skipped
        
        Args:
            path: File path
            
        Returns:
            True if should skip, False otherwise
        """
        skip_patterns = [
            'test/', 'tests/', '__tests__/',
            'vendor/', 'node_modules/', 'venv/',
            '.min.', 'bundle.', 'dist/',
            'build/', 'target/', 'bin/'
        ]
        
        path_lower = path.lower()
        return any(pattern in path_lower for pattern in skip_patterns)
    
    async def _download_files(
        self,
        owner: str,
        repo: str,
        files: List[Dict[str, Any]],
        token: str
    ) -> List[Dict[str, Any]]:
        """
        Download file contents in parallel
        
        Args:
            owner: Repository owner
            repo: Repository name
            files: List of files to download
            token: GitHub OAuth token
            
        Returns:
            List of files with content
        """
        # Download in batches of 10 for optimal performance
        batch_size = 10
        files_with_content = []
        
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            
            # Download batch in parallel
            tasks = [
                self._download_single_file(owner, repo, file, token)
                for file in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.warning(f"Failed to download file: {result}")
                    continue
                
                if result:
                    files_with_content.append(result)
        
        return files_with_content
    
    async def _download_single_file(
        self,
        owner: str,
        repo: str,
        file: Dict[str, Any],
        token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Download a single file
        
        Args:
            owner: Repository owner
            repo: Repository name
            file: File metadata
            token: GitHub OAuth token
            
        Returns:
            File with content or None if failed
        """
        url = f"{self.endpoint}/repos/{owner}/{repo}/contents/{file['path']}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Accept': 'application/vnd.github.v3+json'
                    },
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    # Decode base64 content
                    content = data.get('content', '')
                    if content:
                        try:
                            decoded = base64.b64decode(content).decode('utf-8')
                            return {
                                'path': file['path'],
                                'content': decoded,
                                'size': file['size'],
                                'language': self._detect_language(file['path'])
                            }
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to decode {file['path']}: {e}"
                            )
                            return None
                    
                    return None
                    
        except Exception as e:
            self.logger.warning(f"Failed to download {file['path']}: {e}")
            return None
    
    def _detect_language(self, path: str) -> str:
        """
        Detect programming language from file extension
        
        Args:
            path: File path
            
        Returns:
            Language name
        """
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'JavaScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        
        for ext, lang in extension_map.items():
            if path.endswith(ext):
                return lang
        
        return 'Unknown'
"""
GitHub REST Service for Stage 2 Deep Analysis
Extracts code files from repositories for analysis
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
import base64
import logging

from ..config import get_config
from ..utils import get_logger


class GitHubRESTService:
    """
    GitHub REST API service for Stage 2 code extraction
    
    Performance target: <1.5 seconds per repository
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize REST service
        
        Args:
            logger: Optional logger instance
        """
        self.config = get_config()
        self.logger = logger or get_logger(__name__)
        self.base_url = self.config.GITHUB_REST_ENDPOINT
        self.code_extensions = self.config.CODE_EXTENSIONS
        self.max_files = self.config.MAX_FILES_PER_REPO
    
    async def get_repository_contents(
        self,
        owner: str,
        repo: str,
        token: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch code files from a repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            token: GitHub OAuth token
            
        Returns:
            List of code files with content
            
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If fetching fails
        """
        if not owner or not repo or not token:
            raise ValueError("Owner, repo, and token are required")
        
        self.logger.info(f"Fetching contents for {owner}/{repo}")
        
        try:
            # Step 1: Get file tree
            file_tree = await self._get_file_tree(owner, repo, token)
            
            # Step 2: Filter code files
            code_files = self._filter_code_files(file_tree)
            
            # Step 3: Limit to max files
            if len(code_files) > self.max_files:
                self.logger.info(
                    f"Limiting from {len(code_files)} to {self.max_files} files"
                )
                code_files = code_files[:self.max_files]
            
            # Step 4: Download file contents in parallel
            files_with_content = await self._download_files(
                owner, repo, code_files, token
            )
            
            self.logger.info(
                f"Successfully fetched {len(files_with_content)} code files"
            )
            
            return files_with_content
            
        except Exception as e:
            self.logger.error(f"Failed to fetch repository contents: {e}")
            raise RuntimeError(f"REST API failed: {e}")
    
    async def _get_file_tree(
        self,
        owner: str,
        repo: str,
        token: str,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get repository file tree using Git Trees API with retry logic
        
        Args:
            owner: Repository owner
            repo: Repository name
            token: GitHub OAuth token
            max_retries: Maximum retry attempts (default: 3)
            
        Returns:
            List of file entries
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Get repository info with retry
        repo_data = await self._request_with_retry(url, headers, max_retries)
        default_branch = repo_data.get('default_branch', 'main')
        
        # Get tree for default branch (recursive) with retry
        tree_url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
        tree_data = await self._request_with_retry(tree_url, headers, max_retries)
        
        return tree_data.get('tree', [])
    
    async def _request_with_retry(
        self,
        url: str,
        headers: Dict[str, str],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and exponential backoff
        
        Args:
            url: Request URL
            headers: Request headers
            max_retries: Maximum retry attempts
            
        Returns:
            Response JSON data
            
        Raises:
            RuntimeError: If request fails after all retries
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        
                        # Handle rate limiting
                        if response.status == 429:
                            retry_after = int(response.headers.get('Retry-After', 60))
                            self.logger.warning(
                                f"Rate limited. Retry after {retry_after}s (attempt {attempt + 1}/{max_retries})"
                            )
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_after)
                                continue
                            raise RuntimeError("Rate limit exceeded")
                        
                        if response.status != 200:
                            error_text = await response.text()
                            raise RuntimeError(
                                f"Request failed with status {response.status}: {error_text}"
                            )
                        
                        return await response.json()
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    self.logger.warning(
                        f"Request failed: {e}. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"Request failed after {max_retries} attempts")
                    raise RuntimeError(f"REST request failed after {max_retries} retries: {e}")
            except RuntimeError:
                # Don't retry on RuntimeError (these are application errors)
                raise
        
        # Should not reach here, but just in case
        raise RuntimeError(f"REST request failed: {last_error}")
    
    def _filter_code_files(self, file_tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter for code files only
        
        Args:
            file_tree: Complete file tree
            
        Returns:
            Filtered list of code files
        """
        code_files = []
        
        for entry in file_tree:
            # Only process files (not directories)
            if entry.get('type') != 'blob':
                continue
            
            path = entry.get('path', '')
            
            # Check if it's a code file
            if any(path.endswith(ext) for ext in self.code_extensions):
                # Skip test files and vendor directories
                if self._should_skip_file(path):
                    continue
                
                code_files.append({
                    'path': path,
                    'sha': entry.get('sha'),
                    'size': entry.get('size', 0),
                    'url': entry.get('url')
                })
        
        # Sort by size (smaller files first for faster processing)
        code_files.sort(key=lambda x: x['size'])
        
        return code_files
    
    def _should_skip_file(self, path: str) -> bool:
        """
        Check if file should be skipped
        
        Args:
            path: File path
            
        Returns:
            True if should skip, False otherwise
        """
        skip_patterns = [
            'test/', 'tests/', '__tests__/',
            'vendor/', 'node_modules/', 'venv/',
            '.min.', 'bundle.', 'dist/',
            'build/', 'target/', 'out/'
        ]
        
        path_lower = path.lower()
        return any(pattern in path_lower for pattern in skip_patterns)
    
    async def _download_files(
        self,
        owner: str,
        repo: str,
        files: List[Dict[str, Any]],
        token: str
    ) -> List[Dict[str, Any]]:
        """
        Download file contents in parallel
        
        Args:
            owner: Repository owner
            repo: Repository name
            files: List of files to download
            token: GitHub OAuth token
            
        Returns:
            List of files with content
        """
        # Download in batches of 10 for optimal performance
        batch_size = 10
        files_with_content = []
        
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            
            tasks = [
                self._download_single_file(owner, repo, file, token)
                for file in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out errors
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.warning(f"Failed to download file: {result}")
                    continue
                if result:
                    files_with_content.append(result)
        
        return files_with_content
    
    async def _download_single_file(
        self,
        owner: str,
        repo: str,
        file: Dict[str, Any],
        token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Download a single file's content
        
        Args:
            owner: Repository owner
            repo: Repository name
            file: File metadata
            token: GitHub OAuth token
            
        Returns:
            File with content or None if failed
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file['path']}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    # Decode base64 content
                    content_b64 = data.get('content', '')
                    if not content_b64:
                        return None
                    
                    try:
                        content = base64.b64decode(content_b64).decode('utf-8')
                    except Exception:
                        # Skip files that can't be decoded as UTF-8
                        return None
                    
                    return {
                        'path': file['path'],
                        'content': content,
                        'size': file['size'],
                        'language': self._detect_language(file['path'])
                    }
        
        except Exception as e:
            self.logger.debug(f"Failed to download {file['path']}: {e}")
            return None
    
    def _detect_language(self, path: str) -> str:
        """
        Detect programming language from file extension
        
        Args:
            path: File path
            
        Returns:
            Language name
        """
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'JavaScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        
        for ext, lang in extension_map.items():
            if path.endswith(ext):
                return lang
        
        return 'Unknown'
