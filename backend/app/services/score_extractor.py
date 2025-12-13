"""
Score Extractor Service

Extracts flagship and significant repositories from scan results
for storage in the scores_comparison database.
"""

import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


class ScoreExtractor:
    """
    Extracts and categorizes repositories into flagship and significant categories
    based on their scores and characteristics.
    """
    
    # Thresholds for categorization
    FLAGSHIP_SCORE_THRESHOLD = 70  # Repos with score >= 70
    SIGNIFICANT_SCORE_THRESHOLD = 50  # Repos with score >= 50
    MIN_STARS_FOR_FLAGSHIP = 5  # Minimum stars to be considered flagship
    
    @staticmethod
    def extract_scores_from_repositories(
        repositories: List[Dict[str, Any]],
        overall_score: float
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract flagship and significant repositories from a list of repositories.
        
        Flagship repositories are:
        - High quality (score >= 70)
        - Have significant community engagement (stars >= 5)
        - Represent the developer's best work
        
        Significant repositories are:
        - Good quality (score >= 50)
        - Show consistent development activity
        - Demonstrate technical skills
        
        Args:
            repositories: List of repository dictionaries with scores
            overall_score: User's overall score
        
        Returns:
            Tuple of (flagship_repos, significant_repos)
        """
        flagship_repos = []
        significant_repos = []
        
        for repo in repositories:
            # Extract score from different possible locations
            score = ScoreExtractor._extract_repo_score(repo)
            
            if score is None:
                continue
            
            # Prepare repository data
            repo_data = {
                "name": repo.get("name", ""),
                "full_name": repo.get("full_name", ""),
                "score": score,
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0) or repo.get("stars", 0),
                "forks": repo.get("forks_count", 0) or repo.get("forks", 0),
                "description": repo.get("description", ""),
                "html_url": repo.get("html_url", ""),
                "topics": repo.get("topics", []),
                "created_at": repo.get("created_at"),
                "updated_at": repo.get("updated_at"),
                "pushed_at": repo.get("pushed_at")
            }
            
            # Categorize as flagship
            if (score >= ScoreExtractor.FLAGSHIP_SCORE_THRESHOLD and 
                repo_data["stars"] >= ScoreExtractor.MIN_STARS_FOR_FLAGSHIP):
                flagship_repos.append(repo_data)
            
            # Categorize as significant
            elif score >= ScoreExtractor.SIGNIFICANT_SCORE_THRESHOLD:
                significant_repos.append(repo_data)
        
        # Sort by score (descending)
        flagship_repos.sort(key=lambda x: x["score"], reverse=True)
        significant_repos.sort(key=lambda x: x["score"], reverse=True)
        
        # Limit to top repositories
        flagship_repos = flagship_repos[:10]  # Top 10 flagship
        significant_repos = significant_repos[:20]  # Top 20 significant
        
        logger.info(
            f"Extracted {len(flagship_repos)} flagship repos and "
            f"{len(significant_repos)} significant repos"
        )
        
        return flagship_repos, significant_repos
    
    @staticmethod
    def _extract_repo_score(repo: Dict[str, Any]) -> float:
        """
        Extract repository score from various possible locations in the repo dict.
        
        Args:
            repo: Repository dictionary
        
        Returns:
            Repository score or None if not found
        """
        # Try different possible score locations
        if "overall_score" in repo:
            return float(repo["overall_score"])
        
        if "analysis" in repo and repo["analysis"]:
            if isinstance(repo["analysis"], dict):
                if "overall_score" in repo["analysis"]:
                    return float(repo["analysis"]["overall_score"])
                if "acid_scores" in repo["analysis"]:
                    acid_scores = repo["analysis"]["acid_scores"]
                    if isinstance(acid_scores, dict) and "overall" in acid_scores:
                        return float(acid_scores["overall"])
        
        if "acid_scores" in repo:
            acid_scores = repo["acid_scores"]
            if isinstance(acid_scores, dict) and "overall" in acid_scores:
                return float(acid_scores["overall"])
        
        if "score" in repo:
            return float(repo["score"])
        
        # No score found
        return None
    
    @staticmethod
    def calculate_overall_score(repositories: List[Dict[str, Any]]) -> float:
        """
        Calculate overall user score from repositories.
        
        Args:
            repositories: List of repository dictionaries with scores
        
        Returns:
            Overall score (0-100)
        """
        scores = []
        
        for repo in repositories:
            score = ScoreExtractor._extract_repo_score(repo)
            if score is not None:
                scores.append(score)
        
        if not scores:
            return 0.0
        
        # Calculate weighted average (top repos have more weight)
        scores.sort(reverse=True)
        
        # Weight: first repo = 1.0, second = 0.9, third = 0.8, etc.
        weighted_sum = 0
        weight_total = 0
        
        for i, score in enumerate(scores[:15]):  # Consider top 15 repos
            weight = 1.0 - (i * 0.05)  # Decrease weight by 5% for each position
            weight = max(weight, 0.5)  # Minimum weight of 0.5
            weighted_sum += score * weight
            weight_total += weight
        
        overall_score = weighted_sum / weight_total if weight_total > 0 else 0
        
        return round(overall_score, 2)
    
    @staticmethod
    def extract_metadata(
        user_info: Dict[str, Any],
        repositories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract metadata about the user and their repositories.
        
        Args:
            user_info: GitHub user information
            repositories: List of repositories
        
        Returns:
            Metadata dictionary
        """
        # Calculate language distribution
        language_stats = {}
        for repo in repositories:
            lang = repo.get("language")
            if lang:
                language_stats[lang] = language_stats.get(lang, 0) + 1
        
        # Get top languages
        top_languages = sorted(
            language_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Calculate total stars and forks
        total_stars = sum(
            repo.get("stargazers_count", 0) or repo.get("stars", 0)
            for repo in repositories
        )
        total_forks = sum(
            repo.get("forks_count", 0) or repo.get("forks", 0)
            for repo in repositories
        )
        
        return {
            "github_username": user_info.get("login"),
            "name": user_info.get("name"),
            "bio": user_info.get("bio"),
            "location": user_info.get("location"),
            "company": user_info.get("company"),
            "blog": user_info.get("blog"),
            "avatar_url": user_info.get("avatar_url"),
            "public_repos": user_info.get("public_repos", 0),
            "followers": user_info.get("followers", 0),
            "following": user_info.get("following", 0),
            "total_repositories_analyzed": len(repositories),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "top_languages": [{"language": lang, "count": count} for lang, count in top_languages],
            "github_created_at": user_info.get("created_at"),
            "github_updated_at": user_info.get("updated_at")
        }
