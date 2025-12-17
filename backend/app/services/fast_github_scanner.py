#!/usr/bin/env python3
"""
Fast GitHub Scanner for Quick Profile Analysis
Optimized for speed with minimal API calls and intelligent caching
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import json

from app.services.repository_importance_scorer import RepositoryImportanceScorer

logger = logging.getLogger(__name__)

@dataclass
class FastScanConfig:
    """Configuration for fast scanning"""
    max_repos: int = 100  # Fetch all repos (up to 100)
    max_repos_evaluated: int = 15  # Top 15 repos for detailed evaluation
    max_repos_displayed: int = 35  # Total repos to display (15 evaluated + 20 display-only)
    max_concurrent: int = 6  # Concurrent API calls
    timeout: int = 8  # Request timeout
    cache_duration: int = 300  # 5 minutes cache
    essential_only: bool = True  # Skip non-essential metrics
    
class FastGitHubScanner:
    """Optimized GitHub scanner for fast profile analysis"""
    
    def __init__(self, github_token: str, config: Optional[FastScanConfig] = None):
        self.github_token = github_token
        self.config = config or FastScanConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        
        # Essential metrics only for speed
        self.essential_metrics = {
            'repositories_count',
            'total_commits',
            'languages',
            'recent_activity',
            'account_age',
            'followers_count',
            'public_repos'
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent,
            limit_per_host=self.config.max_concurrent,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'BrokiesV2-FastScanner/1.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_cache_key(self, endpoint: str, params: Dict = None) -> str:
        """Generate cache key for endpoint"""
        key = endpoint
        if params:
            key += '_' + '_'.join(f"{k}={v}" for k, v in sorted(params.items()))
        return key
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached result if valid"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.config.cache_duration):
                return data
            else:
                del self.cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Set cache with timestamp"""
        self.cache[key] = (data, datetime.now())
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make cached API request"""
        cache_key = self._get_cache_key(endpoint, params)
        
        # Check cache first
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        url = f"https://api.github.com{endpoint}"
        
        try:
            async with self.session.get(url, params=params or {}) as response:
                if response.status == 200:
                    data = await response.json()
                    self._set_cache(cache_key, data)
                    return data
                elif response.status == 404:
                    logger.warning(f"Resource not found: {endpoint}")
                    return None
                elif response.status == 403:
                    logger.error(f"Rate limit or forbidden: {endpoint}")
                    return None
                else:
                    logger.error(f"API error {response.status}: {endpoint}")
                    return None
        except asyncio.TimeoutError:
            logger.warning(f"Timeout for endpoint: {endpoint}")
            return None
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            return None
    
    async def get_user_profile_fast(self, username: str) -> Dict[str, Any]:
        """Get user profile with essential info only"""
        logger.info(f"🚀 Fast scanning user: {username}")
        start_time = time.time()
        
        try:
            # Get basic user info
            user_data = await self._make_request(f"/users/{username}")
            if not user_data:
                raise ValueError(f"User {username} not found")
            
            # Get repositories (limited for speed)
            repos_data = await self._make_request(
                f"/users/{username}/repos",
                {'sort': 'updated', 'per_page': self.config.max_repos, 'type': 'owner'}
            )
            
            if not repos_data:
                repos_data = []
            
            # Select repositories for evaluation and display
            repos_to_evaluate, repos_display_only = self._select_important_repos(repos_data)
            
            # Analyze top 15 repositories concurrently (detailed evaluation)
            evaluated_repo_analyses = await self._analyze_repos_concurrent(username, repos_to_evaluate)
            
            # Get basic info for display-only repos (no detailed analysis)
            display_only_analyses = self._get_basic_repo_info(repos_display_only)
            
            # Calculate fast metrics with both evaluated and display-only repos
            result = self._calculate_fast_metrics(
                user_data, 
                repos_data, 
                evaluated_repo_analyses,
                display_only_analyses
            )
            
            elapsed = time.time() - start_time
            logger.info(f"⚡ Fast scan completed in {elapsed:.2f}s for {username}")
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ Fast scan failed after {elapsed:.2f}s for {username}: {e}")
            raise
    
    def _select_important_repos(self, repos_data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Select repositories for evaluation and display
        Returns: (repos_to_evaluate, repos_to_display_only)
        """
        if not repos_data:
            return [], []
        
        # Filter out forks and sort by importance
        non_forks = [repo for repo in repos_data if not repo.get('fork', False)]
        
        # Sort by a combination of stars, forks, and recent activity
        def repo_importance(repo):
            stars = repo.get('stargazers_count', 0)
            forks = repo.get('forks_count', 0)
            
            # Recent activity bonus
            updated_at = repo.get('updated_at', '')
            try:
                updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                days_since_update = (datetime.now(updated_date.tzinfo) - updated_date).days
                recency_bonus = max(0, 30 - days_since_update) / 30  # 0-1 bonus for recent activity
            except:
                recency_bonus = 0
            
            return stars * 2 + forks * 3 + recency_bonus * 10
        
        # Sort by importance
        sorted_repos = sorted(non_forks, key=repo_importance, reverse=True)
        
        # Split into evaluated and display-only
        repos_to_evaluate = sorted_repos[:min(self.config.max_repos_evaluated, len(sorted_repos))]
        repos_to_display = sorted_repos[:min(self.config.max_repos_displayed, len(sorted_repos))]
        repos_display_only = [r for r in repos_to_display if r not in repos_to_evaluate]
        
        return repos_to_evaluate, repos_display_only
    
    def _get_basic_repo_info(self, repos: List[Dict]) -> List[Dict]:
        """Get basic repository info without detailed analysis (for display-only repos)"""
        basic_info = []
        for repo in repos:
            basic_info.append({
                'id': repo.get('id'),
                'name': repo.get('name'),
                'full_name': repo.get('full_name'),
                'description': repo.get('description'),
                'language': repo.get('language'),
                'stargazers_count': repo.get('stargazers_count', 0),
                'forks_count': repo.get('forks_count', 0),
                'watchers_count': repo.get('watchers_count', 0),
                'size': repo.get('size', 0),
                'updated_at': repo.get('updated_at'),
                'created_at': repo.get('created_at'),
                'pushed_at': repo.get('pushed_at'),
                'html_url': repo.get('html_url'),
                'clone_url': repo.get('clone_url'),
                'topics': repo.get('topics', []),
                'license': repo.get('license'),
                'is_fork': repo.get('fork', False),
                'evaluate_for_scoring': False,  # Mark as display-only
                'has_complete_data': False  # Basic data only
            })
        return basic_info
    
    async def _analyze_repos_concurrent(self, username: str, repos: List[Dict]) -> List[Dict]:
        """Analyze repositories concurrently"""
        if not repos:
            return []
        
        tasks = []
        for repo in repos:
            task = self._analyze_repo_fast(username, repo['name'])
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful analyses
        valid_analyses = []
        for result in results:
            if isinstance(result, dict):
                valid_analyses.append(result)
            else:
                logger.warning(f"Repository analysis failed: {result}")
        
        return valid_analyses
    
    async def _analyze_repo_fast(self, username: str, repo_name: str) -> Dict[str, Any]:
        """Fast repository analysis with essential metrics only"""
        try:
            # Get basic repo info
            repo_data = await self._make_request(f"/repos/{username}/{repo_name}")
            if not repo_data:
                return {}
            
            # Get languages (cached and fast)
            languages = await self._make_request(f"/repos/{username}/{repo_name}/languages")
            
            # Get recent commits (limited)
            commits = await self._make_request(
                f"/repos/{username}/{repo_name}/commits",
                {'per_page': 10, 'author': username}
            )
            
            # Generate basic ACID scores for the repository
            stars = repo_data.get('stargazers_count', 0)
            forks = repo_data.get('forks_count', 0)
            description = repo_data.get('description') or ''
            has_description = bool(description.strip()) if description else False
            has_topics = bool(repo_data.get('topics', []))
            commits_count = len(commits) if commits else 0
            
            # Basic ACID scoring based on available data
            atomicity_score = min(100, 40 + (20 if has_description else 0) + (15 if has_topics else 0) + (10 if commits_count > 5 else 0))
            consistency_score = min(100, 45 + (15 if commits_count > 10 else 0) + (20 if stars > 0 else 0) + (10 if not repo_data.get('fork', False) else 0))
            isolation_score = min(100, 50 + (15 if not repo_data.get('fork', False) else 0) + (10 if forks > 0 else 0) + (10 if has_topics else 0))
            durability_score = min(100, 35 + (25 if commits_count > 5 else 0) + (15 if stars > 0 else 0) + (10 if has_description else 0))
            overall_acid = (atomicity_score + consistency_score + isolation_score + durability_score) / 4
            
            # Note: open_issues_count from GitHub API includes both issues AND pull requests
            open_issues_count = repo_data.get('open_issues_count', 0)
            
            return {
                'id': repo_data.get('id', repo_name),
                'name': repo_name,
                'full_name': repo_data.get('full_name', f"{username}/{repo_name}"),
                'description': description,
                'language': repo_data.get('language'),
                'languages': languages or {},
                'stargazers_count': stars,
                'forks_count': forks,
                'watchers_count': repo_data.get('watchers_count', 0),
                'open_issues_count': open_issues_count,
                'size': repo_data.get('size', 0),
                'updated_at': repo_data.get('updated_at'),
                'created_at': repo_data.get('created_at'),
                'pushed_at': repo_data.get('pushed_at'),
                'html_url': repo_data.get('html_url', ''),
                'clone_url': repo_data.get('clone_url', ''),
                'topics': repo_data.get('topics', []),
                'license': repo_data.get('license'),
                'is_fork': repo_data.get('fork', False),
                'commits_count': commits_count,
                'has_issues': repo_data.get('has_issues', False),
                'has_projects': repo_data.get('has_projects', False),
                'has_wiki': repo_data.get('has_wiki', False),
                'analysis': {
                    'acid_scores': {
                        'atomicity': round(atomicity_score, 1),
                        'consistency': round(consistency_score, 1),
                        'isolation': round(isolation_score, 1),
                        'durability': round(durability_score, 1),
                        'overall': round(overall_acid, 1)
                    },
                    'quality_metrics': {
                        'readability': round(60 + (15 if has_description else 0) + (10 if has_topics else 0), 1),
                        'maintainability': round(50 + (20 if commits_count > 10 else 0) + (15 if not repo_data.get('fork', False) else 0), 1),
                        'security': round(50 + (15 if stars > 5 else 0) + (10 if repo_data.get('license') else 0), 1),
                        'test_coverage': round(40 + (15 if stars > 5 else 0) + (10 if forks > 0 else 0), 1),
                        'documentation': round(45 + (25 if has_description else 0) + (15 if has_topics else 0), 1)
                    },
                    'overall_score': round(overall_acid, 1)
                },
                'code_metrics': {
                    'lines_of_code': repo_data.get('size', 0) * 50,  # Rough estimate
                    'files_count': max(1, repo_data.get('size', 0) // 100),  # Rough estimate
                    'complexity_score': round(50 + (commits_count / 10), 1)
                },
                'evaluate_for_scoring': True,  # Mark as evaluated
                'has_complete_data': True  # Has detailed analysis
            }
            
        except Exception as e:
            logger.warning(f"Fast repo analysis failed for {repo_name}: {e}")
            return {}
    
    def _extract_tech_stack(self, repositories: List[Dict], languages: Dict[str, int]) -> List[Dict[str, Any]]:
        """Extract tech stack from repositories and languages"""
        tech_stack = []
        
        # Add languages as tech stack items
        total_bytes = sum(languages.values()) if languages else 1
        for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (bytes_count / total_bytes) * 100 if total_bytes > 0 else 0
            tech_stack.append({
                'name': lang,
                'type': 'language',
                'usage_percentage': round(percentage, 1),
                'repository_count': sum(1 for r in repositories if r.get('language') == lang)
            })
        
        # Extract frameworks and tools from topics
        framework_keywords = {
            'react', 'vue', 'angular', 'svelte', 'next', 'nuxt', 'gatsby',
            'django', 'flask', 'fastapi', 'express', 'nestjs', 'spring',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp',
            'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch'
        }
        
        topic_counts = {}
        for repo in repositories:
            topics = repo.get('topics', [])
            for topic in topics:
                topic_lower = topic.lower()
                if any(keyword in topic_lower for keyword in framework_keywords):
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Add top frameworks/tools
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            tech_stack.append({
                'name': topic,
                'type': 'framework',
                'repository_count': count
            })
        
        return tech_stack
    
    def _calculate_fast_metrics(self, user_data: Dict, repos_data: List[Dict], 
                                evaluated_analyses: List[Dict], display_only_analyses: List[Dict] = None) -> Dict[str, Any]:
        """Calculate essential metrics quickly with evaluated and display-only repos"""
        
        if display_only_analyses is None:
            display_only_analyses = []
        
        # Initialize importance scorer
        importance_scorer = RepositoryImportanceScorer()
        
        # Calculate importance scores and categorize all repositories
        all_repo_analyses = evaluated_analyses + display_only_analyses
        logger.info(f"📊 [CATEGORIZATION] Processing {len(all_repo_analyses)} repositories for categorization")
        logger.info(f"📊 [CATEGORIZATION] Evaluated: {len(evaluated_analyses)}, Display-only: {len(display_only_analyses)}")
        
        for repo in all_repo_analyses:
            # Calculate importance score
            importance_score = importance_scorer.calculate_importance_score(repo)
            repo['importance_score'] = importance_score
            logger.debug(f"📊 [CATEGORIZATION] {repo.get('name')}: importance_score={importance_score}")
        
        # Categorize repositories
        categorized = importance_scorer.categorize_repositories(all_repo_analyses)
        logger.info(f"📊 [CATEGORIZATION] Categories: Flagship={len(categorized.get('flagship', []))}, Significant={len(categorized.get('significant', []))}, Supporting={len(categorized.get('supporting', []))}")
        
        # Update all_repo_analyses with categorized repos (now includes category field)
        all_repo_analyses = categorized['all']
        
        # Log sample repository data
        if all_repo_analyses:
            sample_repo = all_repo_analyses[0]
            logger.info(f"📊 [CATEGORIZATION] Sample repo data: name={sample_repo.get('name')}, category={sample_repo.get('category')}, importance={sample_repo.get('importance_score')}, language={sample_repo.get('language')}, topics={sample_repo.get('topics', [])}")
        
        # Basic user metrics
        account_created = datetime.fromisoformat(user_data['created_at'].replace('Z', '+00:00'))
        account_age_days = (datetime.now().replace(tzinfo=account_created.tzinfo) - account_created).days
        
        # Repository metrics (from all repos)
        total_stars = sum(repo.get('stargazers_count', 0) for repo in repos_data)
        total_forks = sum(repo.get('forks_count', 0) for repo in repos_data)
        total_open_issues = sum(repo.get('open_issues_count', 0) for repo in repos_data)
        
        # Aggregate PR and issue data from analyzed repos
        total_commits = sum(analysis.get('commits_count', 0) for analysis in all_repo_analyses)
        repos_with_issues = sum(1 for repo in repos_data if repo.get('has_issues', False))
        
        # Language analysis (only from evaluated repos for scoring)
        languages = {}
        for analysis in evaluated_analyses:
            repo_languages = analysis.get('languages', {})
            for lang, bytes_count in repo_languages.items():
                languages[lang] = languages.get(lang, 0) + bytes_count
        
        # Sort languages by usage
        sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        primary_language = sorted_languages[0][0] if sorted_languages else 'Unknown'
        
        # ACID scores should be 0 until deep analysis is complete
        # Quick scan only categorizes repositories, doesn't calculate final scores
        activity_score = 0
        consistency_score = 0
        innovation_score = 0
        delivery_score = 0
        acid_score = 0
        
        # Calculate category summary
        summary = {
            'flagship': len(categorized.get('flagship', [])),
            'significant': len(categorized.get('significant', [])),
            'supporting': len(categorized.get('supporting', []))
        }
        
        logger.info(f"📊 [CATEGORIZATION] Final summary: {summary}")
        logger.info(f"📊 [CATEGORIZATION] Total repositories in response: {len(all_repo_analyses)}")
        
        return {
            'userId': user_data['login'],
            'username': user_data['login'],
            'name': user_data.get('name', user_data['login']),
            'bio': user_data.get('bio', ''),
            'location': user_data.get('location', ''),
            'company': user_data.get('company', ''),
            'blog': user_data.get('blog', ''),
            'email': user_data.get('email', ''),
            'hireable': user_data.get('hireable', False),
            'public_repos': user_data.get('public_repos', 0),
            'followers': user_data.get('followers', 0),
            'following': user_data.get('following', 0),
            'created_at': user_data['created_at'],
            'updated_at': user_data['updated_at'],
            'avatar_url': user_data.get('avatar_url', ''),
            
            # Repository data (all repos for display with categorization)
            'repositories': all_repo_analyses,
            'repositoriesCount': len(repos_data),
            'repositoriesEvaluated': len(evaluated_analyses),
            'repositoriesDisplayOnly': len(display_only_analyses),
            'totalStars': total_stars,
            'totalForks': total_forks,
            'totalCommits': total_commits,
            'totalOpenIssues': total_open_issues,
            'repositoriesWithIssues': repos_with_issues,
            'summary': summary,  # Category summary
            
            # Language analysis
            'languages': dict(sorted_languages[:10]),  # Top 10 languages
            'primaryLanguage': primary_language,
            'languageCount': len(languages),
            
            # Tech stack (derived from languages and topics)
            'techStack': self._extract_tech_stack(all_repo_analyses, languages),
            
            # ACID Scores (based on evaluated repos only)
            'activityScore': round(activity_score, 2),
            'consistencyScore': round(consistency_score, 2),
            'innovationScore': round(innovation_score, 2),
            'deliveryScore': round(delivery_score, 2),
            'overallScore': round(acid_score, 2),
            
            # Metadata
            'scanDate': datetime.now().isoformat(),
            'scanType': 'fast',
            'processingTime': 0.0,  # Will be set by the router
            'accountAge': account_age_days,
            'analyzed': True,  # Repositories are categorized and can be displayed
            'analyzedAt': datetime.now().isoformat(),
            'deepAnalysisComplete': False,  # Deep analysis not done yet
            'needsDeepAnalysis': True,  # User should run deep analysis for scores
            'deepAnalysisMessage': 'Run deep analysis to calculate your overall developer score and get detailed code insights',
            
            # Fast scan indicators
            'isFastScan': True,
            'limitedAnalysis': False,  # Now fetching all repos
            'maxReposAnalyzed': self.config.max_repos_evaluated,
            'maxReposDisplayed': self.config.max_repos_displayed,
            'evaluationStrategy': f'Top {self.config.max_repos_evaluated} evaluated, up to {self.config.max_repos_displayed} displayed'
        }

# Fast scanning function for external use
async def fast_scan_github_profile(username: str, github_token: str) -> Dict[str, Any]:
    """Quick GitHub profile scan for immediate results"""
    logger.info(f"🔄 [FAST_SCAN] ========================================")
    logger.info(f"🔄 [FAST_SCAN] Starting fast_scan_github_profile for: {username}")
    logger.info(f"🔄 [FAST_SCAN] Token provided: {'Yes' if github_token else 'No'}")
    logger.info(f"🔄 [FAST_SCAN] ========================================")
    
    config = FastScanConfig(
        max_repos=100,  # Fetch all repos (up to 100)
        max_repos_evaluated=15,  # Evaluate top 15
        max_repos_displayed=35,  # Display up to 35
        max_concurrent=6,  # 6 concurrent requests
        timeout=8,  # 8 second timeout
        essential_only=True
    )
    
    logger.info(f"⚙️ [FAST_SCAN] Config: max_repos={config.max_repos}, max_evaluated={config.max_repos_evaluated}")
    
    try:
        async with FastGitHubScanner(github_token, config) as scanner:
            logger.info(f"🔄 [FAST_SCAN] Scanner initialized, calling get_user_profile_fast...")
            result = await scanner.get_user_profile_fast(username)
            logger.info(f"✅ [FAST_SCAN] ========================================")
            logger.info(f"✅ [FAST_SCAN] Scan completed successfully for {username}")
            logger.info(f"✅ [FAST_SCAN] Repositories found: {len(result.get('repositories', []))}")
            logger.info(f"✅ [FAST_SCAN] Overall score: {result.get('overallScore', 0)}")
            logger.info(f"✅ [FAST_SCAN] ========================================")
            return result
    except Exception as e:
        logger.error(f"❌ [FAST_SCAN] ========================================")
        logger.error(f"❌ [FAST_SCAN] Failed for {username}: {e}")
        import traceback
        logger.error(f"❌ [FAST_SCAN] Traceback: {traceback.format_exc()}")
        logger.error(f"❌ [FAST_SCAN] ========================================")
        raise

# Test function
async def test_fast_scan(username: str = "raseen2305"):
    """Test the fast scanner"""
    import os
    
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment")
        return None
    
    print(f"🚀 Testing fast scan with {username}...")
    start_time = time.time()
    
    try:
        result = await fast_scan_github_profile(username, github_token)
        elapsed = time.time() - start_time
        
        print(f"✅ Fast scan completed in {elapsed:.2f} seconds!")
        print(f"📊 Overall Score: {result.get('overallScore', 0):.1f}")
        print(f"🏆 ACID Scores:")
        print(f"   Activity: {result.get('activityScore', 0):.1f}")
        print(f"   Consistency: {result.get('consistencyScore', 0):.1f}")
        print(f"   Innovation: {result.get('innovationScore', 0):.1f}")
        print(f"   Delivery: {result.get('deliveryScore', 0):.1f}")
        print(f"📈 Repositories: {result.get('repositoriesCount', 0)}")
        print(f"⭐ Total Stars: {result.get('totalStars', 0)}")
        print(f"🍴 Total Forks: {result.get('totalForks', 0)}")
        print(f"💻 Primary Language: {result.get('primaryLanguage', 'Unknown')}")
        
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Fast scan failed after {elapsed:.2f} seconds: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(test_fast_scan())