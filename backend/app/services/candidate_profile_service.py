"""
Candidate Profile Service

This service handles fetching and aggregating candidate profile data
from the database for HR users to view instantly.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class CandidateProfileService:
    """Service for managing candidate profile data retrieval"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def check_profile_exists(self, username: str) -> Dict[str, Any]:
        """
        Quick check if a candidate profile exists in the database
        
        Args:
            username: GitHub username (case-sensitive)
            
        Returns:
            Dict with exists flag, last_scan_date, and data_age_days
        """
        try:
            # Check comprehensive_scans collection
            scan = await self.db.comprehensive_scans.find_one(
                {"github_username": username},
                {"scan_date": 1, "_id": 0}
            )
            
            if not scan:
                return {
                    "exists": False,
                    "last_scan_date": None,
                    "data_age_days": None
                }
            
            # Calculate data age
            scan_date = scan.get("scan_date")
            if isinstance(scan_date, str):
                scan_date = datetime.fromisoformat(scan_date.replace('Z', '+00:00'))
            
            data_age = (datetime.utcnow() - scan_date).days if scan_date else None
            
            return {
                "exists": True,
                "last_scan_date": scan_date.isoformat() if scan_date else None,
                "data_age_days": data_age
            }
            
        except Exception as e:
            logger.error(f"Error checking profile existence for {username}: {e}")
            raise
    
    async def get_profile_freshness(self, username: str) -> int:
        """
        Calculate how many days old the profile data is
        
        Args:
            username: GitHub username (case-sensitive)
            
        Returns:
            Number of days since last scan, or None if no scan found
        """
        try:
            scan = await self.db.comprehensive_scans.find_one(
                {"github_username": username},
                {"scan_date": 1, "_id": 0}
            )
            
            if not scan or not scan.get("scan_date"):
                return None
            
            scan_date = scan.get("scan_date")
            if isinstance(scan_date, str):
                scan_date = datetime.fromisoformat(scan_date.replace('Z', '+00:00'))
            
            return (datetime.utcnow() - scan_date).days
            
        except Exception as e:
            logger.error(f"Error getting profile freshness for {username}: {e}")
            return None
    
    async def get_candidate_profile(self, username: str) -> Dict[str, Any]:
        """
        Fetch complete candidate profile data from analysis_states and user_rankings collections
        
        This method joins data from:
        - analysis_states collection (where username == github_username)
        - user_rankings collection (where github_username == username)
        
        This provides the most accurate and up-to-date data for HR overlay and dashboard.
        
        Args:
            username: GitHub username (case-sensitive)
            
        Returns:
            Complete candidate profile data
            
        Raises:
            ValueError: If profile not found
            Exception: For database errors
        """
        try:
            logger.info(f"Fetching candidate profile for: {username}")
            
            # PRIMARY: Query analysis_states collection for analysis data
            analysis_data = await self.db.analysis_states.find_one(
                {"username": username, "status": "complete"}
            )
            
            # SECONDARY: Query user_rankings collection for ranking and profile data
            ranking_data = await self.db.user_rankings.find_one(
                {"github_username": username}
            )
            
            if not analysis_data and not ranking_data:
                logger.warning(f"❌ No profile found for username: {username}")
                raise ValueError(f"Profile not found for username: {username}")
            
            logger.info(f"Found data for {username}:")
            logger.info(f"  - Analysis data: {'✅' if analysis_data else '❌'}")
            logger.info(f"  - Ranking data: {'✅' if ranking_data else '❌'}")
            
            # Calculate data freshness
            last_updated = None
            if analysis_data:
                last_updated = analysis_data.get("completed_at") or analysis_data.get("updated_at")
            elif ranking_data:
                last_updated = ranking_data.get("last_analysis_date") or ranking_data.get("updated_at")
            
            if isinstance(last_updated, str):
                last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            data_age_days = (datetime.utcnow() - last_updated).days if last_updated else 0
            
            # Build profile response from joined data
            profile = self._build_profile_from_joined_data(analysis_data, ranking_data, data_age_days)
            
            logger.info(f"✅ Successfully fetched profile for: {username}")
            return profile
            
        except ValueError:
            # Re-raise ValueError for not found
            raise
        except Exception as e:
            logger.error(f"Error fetching candidate profile for {username}: {e}")
            raise
    
    def _build_profile_from_joined_data(
        self,
        analysis_data: Optional[Dict[str, Any]],
        ranking_data: Optional[Dict[str, Any]],
        data_age_days: int
    ) -> Dict[str, Any]:
        """
        Build profile response from joined analysis_states and user_rankings data
        
        Args:
            analysis_data: Data from analysis_states collection
            ranking_data: Data from user_rankings collection
            data_age_days: Age of the data in days
            
        Returns:
            Formatted profile response
        """
        # Determine username from available data
        github_username = None
        if analysis_data:
            github_username = analysis_data.get("username")
        elif ranking_data:
            github_username = ranking_data.get("github_username")
        
        # Extract user info from ranking_data (has profile information)
        user_info = {}
        if ranking_data:
            user_info = {
                "login": github_username,
                "name": ranking_data.get("name"),
                "avatar_url": f"https://github.com/{github_username}.png",  # Default GitHub avatar
                "bio": None,  # Not available in user_rankings
                "location": ranking_data.get("region"),
                "company": None,  # Not available in user_rankings
                "email": None,  # Not available in user_rankings
                "blog": None,  # Not available in user_rankings
                "public_repos": ranking_data.get("repository_count", 0),
                "followers": 0,  # Not available in user_rankings
                "following": 0,  # Not available in user_rankings
                "created_at": None,  # Not available in user_rankings
                "updated_at": ranking_data.get("updated_at")
            }
        
        # Extract repositories and scores from analysis_data
        repositories = []
        overall_score = 0.0
        acid_breakdown = {}
        languages = []
        tech_stack = []
        
        if analysis_data:
            results = analysis_data.get("results", {})
            repositories = results.get("repositories", [])
            
            # Get overall score
            overall_scores = results.get("overall_scores", {})
            overall_score = overall_scores.get("overall_score", 0.0)
            
            # Get ACID breakdown
            acid_breakdown = overall_scores.get("acid_scores", {})
            
            # Extract languages from repositories
            language_stats = {}
            for repo in repositories:
                repo_languages = repo.get("languages", {})
                for lang, bytes_count in repo_languages.items():
                    language_stats[lang] = language_stats.get(lang, 0) + bytes_count
            
            # Convert to percentage format
            total_bytes = sum(language_stats.values())
            if total_bytes > 0:
                languages = [
                    {
                        "name": lang,
                        "percentage": round((bytes_count / total_bytes) * 100, 1)
                    }
                    for lang, bytes_count in sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
                ][:10]  # Top 10 languages
            
            # Extract tech stack from repositories
            tech_set = set()
            for repo in repositories:
                repo_languages = repo.get("languages", {})
                tech_set.update(repo_languages.keys())
            tech_stack = list(tech_set)[:20]  # Top 20 technologies
        
        # Use ranking data for overall score if analysis data is not available
        if not analysis_data and ranking_data:
            overall_score = ranking_data.get("overall_score", 0.0)
        
        # Build rankings section from ranking_data
        rankings = None
        if ranking_data:
            rankings = {
                "regional": {
                    "rank": ranking_data.get("regional_rank"),
                    "total": ranking_data.get("regional_total_users"),
                    "percentile": ranking_data.get("regional_percentile"),
                    "region": ranking_data.get("region"),
                    "percentile_text": f"Top {100 - ranking_data.get('regional_percentile', 0):.1f}%" if ranking_data.get("regional_percentile") else None
                },
                "university": {
                    "rank": ranking_data.get("university_rank"),
                    "total": ranking_data.get("university_total_users"),
                    "percentile": ranking_data.get("university_percentile"),
                    "university": ranking_data.get("university"),
                    "university_short": ranking_data.get("university_short"),
                    "percentile_text": f"Top {100 - ranking_data.get('university_percentile', 0):.1f}%" if ranking_data.get("university_percentile") else None
                }
            }
        
        # Get category distribution from analysis_data or ranking_data
        category_distribution = {}
        if analysis_data:
            category_distribution = analysis_data.get("results", {}).get("category_distribution", {})
        elif ranking_data:
            category_distribution = {
                "flagship": ranking_data.get("flagship_count", 0),
                "significant": ranking_data.get("significant_count", 0),
                "supporting": ranking_data.get("supporting_count", 0)
            }
        
        # Get last scan date
        last_scan_date = None
        if analysis_data:
            last_scan_date = analysis_data.get("completed_at") or analysis_data.get("updated_at")
        elif ranking_data:
            last_scan_date = ranking_data.get("last_analysis_date")
        
        # Build profile response
        profile = {
            "github_username": github_username,
            "profile": user_info,
            "repositories": repositories,
            "repository_count": len(repositories),
            "scores": {
                "overall_score": overall_score,
                "acid_breakdown": acid_breakdown
            },
            "rankings": rankings,
            "languages": languages,
            "tech_stack": tech_stack,
            "last_scan_date": last_scan_date,
            "data_age_days": data_age_days,
            "analyzed": analysis_data is not None,
            "analysis_type": "comprehensive" if analysis_data else "basic",
            
            # Include additional data
            "category_distribution": category_distribution,
            "comprehensive_data": analysis_data.get("results", {}) if analysis_data else {},
        }
        
        return profile

    def _build_profile_from_data(
        self,
        user_data: Dict[str, Any],
        data_age_days: int,
        source: str = "hr_view"
    ) -> Dict[str, Any]:
        """
        Build profile response from hr_view or user_rankings data
        
        Args:
            user_data: Complete data from hr_view or user_rankings collection
            data_age_days: Age of the data in days
            source: Data source ("hr_view" or "user_rankings")
            
        Returns:
            Formatted profile response
        """
        github_username = user_data.get("github_username")
        
        # Extract user info directly from user_data
        user_info = {
            "login": github_username,
            "name": user_data.get("name"),
            "avatar_url": user_data.get("profile_picture") or f"https://github.com/{github_username}.png",
            "bio": user_data.get("bio"),
            "location": user_data.get("location"),
            "company": user_data.get("company"),
            "email": user_data.get("email"),
            "blog": user_data.get("blog") or user_data.get("website"),
            "public_repos": user_data.get("public_repos") or user_data.get("total_repos", 0),
            "followers": user_data.get("followers", 0),
            "following": user_data.get("following", 0),
            "created_at": user_data.get("github_created_at") or user_data.get("created_at"),
            "updated_at": user_data.get("github_updated_at") or user_data.get("updated_at")
        }
        
        # Get repositories directly from user_data
        repositories = user_data.get("repositories", [])
        
        # Get scores
        overall_score = user_data.get("overall_score", 0.0)
        
        # Get ACID breakdown
        acid_breakdown = user_data.get("acid_scores", {})
        
        # Get languages
        languages = user_data.get("languages", [])
        if not languages:
            # Fallback to primary_language if languages array is empty
            primary_lang = user_data.get("primary_language")
            if primary_lang:
                languages = [{"name": primary_lang, "percentage": 100}]
        
        # Get tech stack
        tech_stack = user_data.get("tech_stack", [])
        
        # Build rankings section from user_data
        rankings = {
            "regional": {
                "rank": user_data.get("regional_rank"),
                "total": user_data.get("total_regional_users"),
                "percentile": user_data.get("regional_percentile"),
                "region": user_data.get("region"),
                "percentile_text": user_data.get("regional_percentile_text")
            },
            "university": {
                "rank": user_data.get("university_rank"),
                "total": user_data.get("total_university_users"),
                "percentile": user_data.get("university_percentile"),
                "university": user_data.get("university"),
                "university_short": user_data.get("university_short"),
                "percentile_text": user_data.get("university_percentile_text")
            }
        }
        
        # Get last scan date
        last_scan_date = user_data.get("last_scan_date") or user_data.get("last_updated")
        
        # Build profile response
        profile = {
            "github_username": github_username,
            "profile": {
                "name": user_info.get("name"),
                "bio": user_info.get("bio"),
                "avatar_url": user_info.get("avatar_url"),
                "location": user_info.get("location"),
                "company": user_info.get("company"),
                "email": user_info.get("email"),
                "blog": user_info.get("blog"),
                "public_repos": user_info.get("public_repos", 0),
                "followers": user_info.get("followers", 0),
                "following": user_info.get("following", 0),
                "created_at": user_info.get("created_at"),
                "updated_at": user_info.get("updated_at")
            },
            "repositories": repositories,
            "repository_count": len(repositories),
            "scores": {
                "overall_score": overall_score,
                "acid_breakdown": acid_breakdown
            },
            "rankings": rankings,
            "languages": languages,
            "tech_stack": tech_stack,
            "last_scan_date": last_scan_date,
            "data_age_days": data_age_days,
            "analyzed": user_data.get("analyzed", False),
            "analysis_type": user_data.get("analysis_type", "basic"),
            
            # Include additional data
            "category_distribution": user_data.get("category_distribution", {}),
            "comprehensive_data": user_data.get("comprehensive_data", {}),
        }
        
        return profile
    
    async def _build_profile_response(
        self, 
        scan_data: Dict[str, Any], 
        ranking_data: Optional[Dict[str, Any]],
        data_age_days: Optional[int]
    ) -> Dict[str, Any]:
        """
        Build the unified profile response from scan and ranking data
        
        Args:
            scan_data: Data from comprehensive_scans collection
            ranking_data: Data from user_rankings collection (optional)
            data_age_days: Age of the data in days
            
        Returns:
            Formatted profile response
        """
        # Extract user info
        user_info = scan_data.get("userInfo", {})
        github_username = scan_data.get("github_username", user_info.get("login"))
        
        # Extract repositories
        repositories = scan_data.get("repositories", [])
        
        # Extract scores
        overall_score = scan_data.get("overall_score")
        
        # Build ACID breakdown if available
        acid_breakdown = {}
        if scan_data.get("acid_scores"):
            acid_breakdown = scan_data.get("acid_scores", {})
        
        # Extract languages
        languages = scan_data.get("languages", [])
        
        # Extract tech stack
        tech_stack = scan_data.get("tech_stack", [])
        
        # Build rankings section
        rankings = None
        if ranking_data:
            rankings = {
                "regional": {
                    "rank": ranking_data.get("regional_rank"),
                    "total": ranking_data.get("total_regional_users"),
                    "percentile": ranking_data.get("regional_percentile"),
                    "region": ranking_data.get("region"),
                    "percentile_text": ranking_data.get("regional_percentile_text")
                },
                "university": {
                    "rank": ranking_data.get("university_rank"),
                    "total": ranking_data.get("total_university_users"),
                    "percentile": ranking_data.get("university_percentile"),
                    "university": ranking_data.get("university"),
                    "university_short": ranking_data.get("university_short"),
                    "percentile_text": ranking_data.get("university_percentile_text")
                }
            }
        
        # Build profile response
        profile = {
            "github_username": github_username,
            "profile": {
                "name": user_info.get("name"),
                "bio": user_info.get("bio"),
                "avatar_url": user_info.get("avatar_url"),
                "location": user_info.get("location"),
                "company": user_info.get("company"),
                "email": user_info.get("email"),
                "blog": user_info.get("blog"),
                "public_repos": user_info.get("public_repos", 0),
                "followers": user_info.get("followers", 0),
                "following": user_info.get("following", 0),
                "created_at": user_info.get("created_at"),
                "updated_at": user_info.get("updated_at")
            },
            "repositories": repositories,
            "repository_count": len(repositories),
            "scores": {
                "overall_score": overall_score,
                "acid_breakdown": acid_breakdown
            },
            "rankings": rankings,
            "languages": languages,
            "tech_stack": tech_stack,
            "last_scan_date": scan_data.get("scan_date"),
            "data_age_days": data_age_days,
            "analyzed": scan_data.get("analyzed", False),
            "analysis_type": scan_data.get("analysis_type"),
            
            # Include additional data that might be useful
            "category_distribution": scan_data.get("categoryDistribution", {}),
            "comprehensive_data": scan_data.get("comprehensiveData", {}),
        }
        
        return profile
