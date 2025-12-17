"""
GitHub GraphQL Service
Optimized for Stage 1 quick scan - fetches user + all repos in ONE request
Target: <0.5 seconds
"""

import aiohttp
from typing import Dict, List, Tuple, Any, Optional
import logging
from datetime import datetime

from ..config import get_config
from ..utils import get_logger


class GitHubGraphQLService:
    """
    GitHub GraphQL API service for Stage 1 quick scan
    
    Fetches user profile and all repositories in a single optimized query
    Performance target: <0.5 seconds
    """
    
    # Optimized GraphQL query - gets everything in ONE request
    QUERY = """
    query GetUserAndRepos($username: String!) {
      user(login: $username) {
        id
        login
        name
        bio
        avatarUrl
        email
        location
        company
        websiteUrl
        twitterUsername
        createdAt
        updatedAt
        
        followers { totalCount }
        following { totalCount }
        
        repositories(
          first: 100
          orderBy: {field: UPDATED_AT, direction: DESC}
          ownerAffiliations: OWNER
        ) {
          totalCount
          nodes {
            id
            name
            nameWithOwner
            description
            url
            homepageUrl
            
            stargazerCount
            forkCount
            watchers { totalCount }
            
            diskUsage
            
            primaryLanguage {
              name
              color
            }
            
            languages(first: 10) {
              edges {
                size
                node {
                  name
                  color
                }
              }
            }
            
            repositoryTopics(first: 10) {
              nodes {
                topic {
                  name
                }
              }
            }
            
            createdAt
            updatedAt
            pushedAt
            
            hasIssuesEnabled
            hasWikiEnabled
            
            licenseInfo {
              name
              spdxId
            }
            
            defaultBranchRef {
              name
              target {
                ... on Commit {
                  history(first: 1) {
                    totalCount
                  }
                }
              }
            }
            
            issues(states: OPEN) {
              totalCount
            }
            
            pullRequests(states: OPEN) {
              totalCount
            }
            
            # Check for README without downloading
            readme: object(expression: "HEAD:README.md") {
              ... on Blob {
                id
              }
            }
            
            # Check for LICENSE
            license: object(expression: "HEAD:LICENSE") {
              ... on Blob {
                id
              }
            }
            
            # Check for tests directory
            tests: object(expression: "HEAD:test") {
              ... on Tree {
                id
              }
            }
            
            # Check for CI/CD
            githubActions: object(expression: "HEAD:.github/workflows") {
              ... on Tree {
                id
              }
            }
          }
        }
      }
    }
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize GraphQL service
        
        Args:
            logger: Optional logger instance
        """
        self.config = get_config()
        self.logger = logger or get_logger(__name__)
        self.endpoint = self.config.GITHUB_GRAPHQL_ENDPOINT
    
    async def get_user_and_repositories(
        self,
        username: str,
        token: str
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get user profile and all repositories in ONE request
        
        Args:
            username: GitHub username
            token: GitHub OAuth token
            
        Returns:
            Tuple of (user_data, repositories_data)
            
        Raises:
            ValueError: If username or token is invalid
            RuntimeError: If GraphQL query fails
        """
        if not username or not token:
            raise ValueError("Username and token are required")
        
        self.logger.info(f"Fetching data for user: {username}")
        start_time = datetime.utcnow()
        
        try:
            # Execute GraphQL query
            data = await self._execute_query(username, token)
            
            # Transform response
            user_data, repos_data = self._transform_response(data['user'])
            
            # Log performance
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(
                f"Fetched {len(repos_data)} repositories in {duration:.2f}s"
            )
            
            return user_data, repos_data
            
        except Exception as e:
            self.logger.error(f"GraphQL query failed: {e}")
            raise RuntimeError(f"Failed to fetch GitHub data: {e}")
    
    async def _execute_query(self, username: str, token: str) -> Dict[str, Any]:
        """
        Execute GraphQL query
        
        Args:
            username: GitHub username
            token: GitHub OAuth token
            
        Returns:
            GraphQL response data
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.endpoint,
                json={
                    'query': self.QUERY,
                    'variables': {'username': username}
                },
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GraphQL request failed with status {response.status}: {text}"
                    )
                
                result = await response.json()
                
                if 'errors' in result:
                    errors = result['errors']
                    raise RuntimeError(f"GraphQL errors: {errors}")
                
                if 'data' not in result or not result['data']:
                    raise RuntimeError("No data returned from GraphQL")
                
                return result['data']
    
    def _transform_response(
        self,
        user_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Transform GraphQL response to our internal format
        
        Args:
            user_data: Raw user data from GraphQL
            
        Returns:
            Tuple of (transformed_user, transformed_repositories)
        """
        # Transform user profile
        user = {
            'id': user_data['id'],
            'username': user_data['login'],
            'name': user_data.get('name'),
            'bio': user_data.get('bio'),
            'avatar_url': user_data['avatarUrl'],
            'email': user_data.get('email'),
            'location': user_data.get('location'),
            'company': user_data.get('company'),
            'website': user_data.get('websiteUrl'),
            'twitter': user_data.get('twitterUsername'),
            'followers': user_data['followers']['totalCount'],
            'following': user_data['following']['totalCount'],
            'created_at': user_data['createdAt'],
            'updated_at': user_data['updatedAt']
        }
        
        # Transform repositories
        repos = []
        for repo in user_data['repositories']['nodes']:
            # Calculate language breakdown
            languages = {}
            total_size = 0
            for edge in repo['languages']['edges']:
                lang_name = edge['node']['name']
                lang_size = edge['size']
                languages[lang_name] = lang_size
                total_size += lang_size
            
            # Calculate language percentages
            language_percentages = {}
            if total_size > 0:
                for lang, size in languages.items():
                    language_percentages[lang] = (size / total_size) * 100
            
            # Get commit count
            commit_count = 0
            if repo.get('defaultBranchRef') and repo['defaultBranchRef'].get('target'):
                commit_count = repo['defaultBranchRef']['target']['history']['totalCount']
            
            repos.append({
                'id': repo['id'],
                'name': repo['name'],
                'full_name': repo['nameWithOwner'],
                'description': repo.get('description'),
                'url': repo['url'],
                'homepage': repo.get('homepageUrl'),
                'stars': repo['stargazerCount'],
                'forks': repo['forkCount'],
                'watchers': repo['watchers']['totalCount'],
                'size': repo['diskUsage'],  # in KB
                'language': repo['primaryLanguage']['name'] if repo.get('primaryLanguage') else None,
                'languages': language_percentages,
                'topics': [t['topic']['name'] for t in repo['repositoryTopics']['nodes']],
                'created_at': repo['createdAt'],
                'updated_at': repo['updatedAt'],
                'pushed_at': repo.get('pushedAt'),
                'has_issues': repo['hasIssuesEnabled'],
                'has_wiki': repo['hasWikiEnabled'],
                'license': repo['licenseInfo']['name'] if repo.get('licenseInfo') else None,
                'commit_count': commit_count,
                'open_issues': repo['issues']['totalCount'],
                'open_prs': repo['pullRequests']['totalCount'],
                # Production indicators (detected without code!)
                'has_readme': bool(repo.get('readme')),
                'has_license_file': bool(repo.get('license')),
                'has_tests': bool(repo.get('tests')),
                'has_ci_cd': bool(repo.get('githubActions'))
            })
        
        return user, repos
"""
GitHub GraphQL Service for Stage 1 Quick Scan
Fetches user profile and all repositories in a single optimized query
"""

import aiohttp
import asyncio
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import logging

from ..config import get_config
from ..utils import get_logger


class GitHubGraphQLService:
    """
    GitHub GraphQL API service optimized for Stage 1 quick scan
    
    Performance target: <0.5 seconds for user + all repositories
    """
    
    # Optimized GraphQL query to fetch everything in one request
    USER_AND_REPOS_QUERY = """
    query GetUserAndRepos($username: String!) {
      user(login: $username) {
        id
        login
        name
        bio
        avatarUrl
        email
        location
        company
        websiteUrl
        twitterUsername
        createdAt
        updatedAt
        
        followers { totalCount }
        following { totalCount }
        
        repositories(
          first: 100
          orderBy: {field: UPDATED_AT, direction: DESC}
          ownerAffiliations: OWNER
        ) {
          totalCount
          nodes {
            id
            name
            nameWithOwner
            description
            url
            homepageUrl
            
            stargazerCount
            forkCount
            watchers { totalCount }
            
            diskUsage
            
            primaryLanguage {
              name
              color
            }
            
            languages(first: 10) {
              edges {
                size
                node {
                  name
                  color
                }
              }
            }
            
            repositoryTopics(first: 10) {
              nodes {
                topic {
                  name
                }
              }
            }
            
            createdAt
            updatedAt
            pushedAt
            
            hasIssuesEnabled
            hasWikiEnabled
            
            licenseInfo {
              name
              spdxId
            }
            
            defaultBranchRef {
              name
              target {
                ... on Commit {
                  history(first: 1) {
                    totalCount
                  }
                }
              }
            }
            
            issues(states: OPEN) {
              totalCount
            }
            
            pullRequests(states: OPEN) {
              totalCount
            }
            
            # Check for README without downloading
            readme: object(expression: "HEAD:README.md") {
              ... on Blob {
                id
              }
            }
            
            # Check for LICENSE
            license: object(expression: "HEAD:LICENSE") {
              ... on Blob {
                id
              }
            }
            
            # Check for tests directory
            tests: object(expression: "HEAD:test") {
              ... on Tree {
                id
              }
            }
            
            # Check for CI/CD
            githubActions: object(expression: "HEAD:.github/workflows") {
              ... on Tree {
                id
              }
            }
            
            isFork
            isPrivate
          }
        }
      }
    }
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize GraphQL service
        
        Args:
            logger: Optional logger instance
        """
        self.config = get_config()
        self.logger = logger or get_logger(__name__)
        self.endpoint = self.config.GITHUB_GRAPHQL_ENDPOINT
    
    async def get_user_and_repositories(
        self,
        username: str,
        token: str
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Fetch user profile and all repositories in ONE request
        
        Args:
            username: GitHub username
            token: GitHub OAuth token
            
        Returns:
            Tuple of (user_data, repositories_data)
            
        Raises:
            ValueError: If username or token is invalid
            RuntimeError: If GraphQL query fails
        """
        if not username or not token:
            raise ValueError("Username and token are required")
        
        self.logger.info(f"Fetching user and repositories for: {username}")
        
        try:
            # Execute GraphQL query
            response_data = await self._execute_query(
                self.USER_AND_REPOS_QUERY,
                {"username": username},
                token
            )
            
            # Transform response to our format
            user_data, repos_data = self._transform_response(response_data)
            
            self.logger.info(
                f"Successfully fetched user and {len(repos_data)} repositories"
            )
            
            return user_data, repos_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch user and repositories: {e}")
            raise RuntimeError(f"GraphQL query failed: {e}")
    
    async def _execute_query(
        self,
        query: str,
        variables: Dict[str, Any],
        token: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query with retry logic
        
        Args:
            query: GraphQL query string
            variables: Query variables
            token: GitHub OAuth token
            max_retries: Maximum retry attempts (default: 3)
            
        Returns:
            Response data
            
        Raises:
            RuntimeError: If query fails after all retries
        """
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {
            'query': query,
            'variables': variables
        }
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.endpoint,
                        json=payload,
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
                                f"GraphQL request failed with status {response.status}: {error_text}"
                            )
                        
                        data = await response.json()
                        
                        # Check for GraphQL errors
                        if 'errors' in data:
                            errors = data['errors']
                            error_messages = [e.get('message', str(e)) for e in errors]
                            raise RuntimeError(f"GraphQL errors: {', '.join(error_messages)}")
                        
                        if 'data' not in data:
                            raise RuntimeError("No data in GraphQL response")
                        
                        return data['data']
                        
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
                    raise RuntimeError(f"GraphQL query failed after {max_retries} retries: {e}")
            except RuntimeError:
                # Don't retry on RuntimeError (these are application errors)
                raise
        
        # Should not reach here, but just in case
        raise RuntimeError(f"GraphQL query failed: {last_error}")
    
    def _transform_response(
        self,
        data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Transform GraphQL response to our internal format
        
        Args:
            data: GraphQL response data
            
        Returns:
            Tuple of (user_data, repositories_data)
        """
        user_raw = data.get('user')
        if not user_raw:
            raise RuntimeError("No user data in response")
        
        # Transform user data
        user_data = {
            'github_id': user_raw['id'],
            'username': user_raw['login'],
            'name': user_raw.get('name'),
            'bio': user_raw.get('bio'),
            'avatar_url': user_raw['avatarUrl'],
            'email': user_raw.get('email'),
            'location': user_raw.get('location'),
            'company': user_raw.get('company'),
            'website': user_raw.get('websiteUrl'),
            'twitter': user_raw.get('twitterUsername'),
            'followers': user_raw['followers']['totalCount'],
            'following': user_raw['following']['totalCount'],
            'created_at': self._parse_datetime(user_raw['createdAt']),
            'updated_at': self._parse_datetime(user_raw['updatedAt'])
        }
        
        # Transform repositories
        repos_raw = user_raw.get('repositories', {}).get('nodes', [])
        repositories = []
        
        for repo in repos_raw:
            # Calculate language breakdown
            languages = {}
            total_size = 0
            
            for edge in repo.get('languages', {}).get('edges', []):
                lang_name = edge['node']['name']
                lang_size = edge['size']
                languages[lang_name] = lang_size
                total_size += lang_size
            
            # Calculate language percentages
            language_percentages = {}
            if total_size > 0:
                language_percentages = {
                    lang: (size / total_size * 100)
                    for lang, size in languages.items()
                }
            
            # Get primary language
            primary_language = None
            if repo.get('primaryLanguage'):
                primary_language = repo['primaryLanguage']['name']
            
            # Get topics
            topics = [
                t['topic']['name']
                for t in repo.get('repositoryTopics', {}).get('nodes', [])
            ]
            
            # Get commit count
            commit_count = 0
            if repo.get('defaultBranchRef'):
                target = repo['defaultBranchRef'].get('target', {})
                history = target.get('history', {})
                commit_count = history.get('totalCount', 0)
            
            # Get license
            license_name = None
            if repo.get('licenseInfo'):
                license_name = repo['licenseInfo']['name']
            
            # Transform repository
            repo_data = {
                'github_id': repo['id'],
                'name': repo['name'],
                'full_name': repo['nameWithOwner'],
                'description': repo.get('description'),
                'url': repo['url'],
                'homepage': repo.get('homepageUrl'),
                'stars': repo['stargazerCount'],
                'forks': repo['forkCount'],
                'watchers': repo['watchers']['totalCount'],
                'size': repo['diskUsage'],  # in KB
                'language': primary_language,
                'languages': language_percentages,
                'topics': topics,
                'created_at': self._parse_datetime(repo['createdAt']),
                'updated_at': self._parse_datetime(repo['updatedAt']),
                'pushed_at': self._parse_datetime(repo.get('pushedAt')),
                'has_issues': repo.get('hasIssuesEnabled', False),
                'has_wiki': repo.get('hasWikiEnabled', False),
                'license': license_name,
                'commit_count': commit_count,
                'open_issues': repo.get('issues', {}).get('totalCount', 0),
                'open_prs': repo.get('pullRequests', {}).get('totalCount', 0),
                'is_fork': repo.get('isFork', False),
                'is_private': repo.get('isPrivate', False),
                # Production indicators (detected without downloading code!)
                'has_readme': bool(repo.get('readme')),
                'has_license_file': bool(repo.get('license')),
                'has_tests': bool(repo.get('tests')),
                'has_ci_cd': bool(repo.get('githubActions'))
            }
            
            repositories.append(repo_data)
        
        return user_data, repositories
    
    def _parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        """
        Parse ISO datetime string
        
        Args:
            dt_string: ISO datetime string
            
        Returns:
            datetime object or None
        """
        if not dt_string:
            return None
        
        try:
            # Remove 'Z' and parse
            if dt_string.endswith('Z'):
                dt_string = dt_string[:-1] + '+00:00'
            return datetime.fromisoformat(dt_string)
        except Exception as e:
            self.logger.warning(f"Failed to parse datetime '{dt_string}': {e}")
            return None
