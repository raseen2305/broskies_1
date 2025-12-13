"""
HR Service Layer
Business logic for candidate data processing and recruitment insights
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math

from app.models.hr_candidate import (
    CandidateCard, CandidateProfile, ScoredRepository,
    CandidateFilters, PaginatedCandidates, AggregateInsights,
    TrendingLanguages
)
from app.services.hr_data_handler import store_hr_data, retrieve_hr_data, HRDataType

logger = logging.getLogger(__name__)


class HRService:
    """Service for HR candidate operations"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_candidates_paginated(
        self,
        page: int = 1,
        limit: int = 10,
        filters: Optional[CandidateFilters] = None,
        sort_by: str = "score"
    ) -> PaginatedCandidates:
        """
        Get paginated candidates with filters and sorting from HR database
        
        Args:
            page: Page number (1-indexed)
            limit: Number of candidates per page
            filters: Optional filters for language, score, role, search
            sort_by: Sort field ("score", "upvotes", "recent")
            
        Returns:
            PaginatedCandidates: Paginated list of candidate cards
        """
        try:
            # Build query from filters
            query = {}
            
            if filters:
                # Score range filter
                if filters.min_score is not None or filters.max_score is not None:
                    query["overall_score"] = {}
                    if filters.min_score is not None:
                        query["overall_score"]["$gte"] = filters.min_score
                    if filters.max_score is not None:
                        query["overall_score"]["$lte"] = filters.max_score
                
                # Search filter (username or name)
                if filters.search:
                    search_regex = {"$regex": filters.search, "$options": "i"}
                    query["$or"] = [
                        {"github_username": search_regex},
                        {"profile.full_name": search_regex}
                    ]
            
            # Try to get candidates from HR database first
            hr_candidates = await retrieve_hr_data(query, hr_data_type=HRDataType.CANDIDATE_PROFILE)
            
            # If no HR candidates found, fall back to user_rankings
            if not hr_candidates:
                logger.debug("🏢 No candidates in HR database, falling back to user_rankings")
                
                # Determine sort order
                sort_field = "overall_score"
                sort_direction = -1  # Descending
                
                if sort_by == "upvotes":
                    sort_field = "upvotes"
                elif sort_by == "recent":
                    sort_field = "last_updated"
                
                # Get total count
                total = await self.db.user_rankings.count_documents(query)
                
                # Calculate pagination
                skip = (page - 1) * limit
                total_pages = math.ceil(total / limit) if total > 0 else 1
                
                # Fetch candidates from user_rankings
                cursor = self.db.user_rankings.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
                candidates_data = await cursor.to_list(length=limit)
                
                # Store candidates in HR database for future use
                for data in candidates_data:
                    hr_candidate_data = {
                        **data,
                        "source": "user_rankings",
                        "migrated_to_hr": datetime.utcnow()
                    }
                    await store_hr_data(hr_candidate_data, HRDataType.CANDIDATE_PROFILE, "candidate_migration")
                
            else:
                logger.debug(f"🏢 Found {len(hr_candidates)} candidates in HR database")
                candidates_data = hr_candidates
                total = len(hr_candidates)
                
                # Apply sorting to HR data
                if sort_by == "upvotes":
                    candidates_data.sort(key=lambda x: x.get("upvotes", 0), reverse=True)
                elif sort_by == "recent":
                    candidates_data.sort(key=lambda x: x.get("last_updated", datetime.min), reverse=True)
                else:
                    candidates_data.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
                
                # Apply pagination to HR data
                skip = (page - 1) * limit
                candidates_data = candidates_data[skip:skip + limit]
                total_pages = math.ceil(total / limit) if total > 0 else 1
            
            # Convert to CandidateCard models
            candidates = []
            for data in candidates_data:
                candidate_card = await self._convert_ranking_to_candidate_card(data)
                if candidate_card:
                    candidates.append(candidate_card)
            
            return PaginatedCandidates(
                candidates=candidates,
                total=total,
                page=page,
                limit=limit,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Failed to get paginated candidates: {e}")
            raise
    
    async def get_candidate_profile(self, username: str) -> Optional[CandidateProfile]:
        """
        Get complete candidate profile from HR database with fallback to user_rankings
        
        Args:
            username: GitHub username
            
        Returns:
            CandidateProfile: Complete profile or None if not found
        """
        try:
            # Try to get candidate from HR database first
            hr_candidates = await retrieve_hr_data(
                {"github_username": username}, 
                hr_data_type=HRDataType.CANDIDATE_PROFILE
            )
            
            candidate_data = None
            if hr_candidates:
                candidate_data = hr_candidates[0]
                logger.debug(f"🏢 Found candidate {username} in HR database")
            else:
                # Fall back to user_rankings
                logger.debug(f"🏢 Candidate {username} not in HR database, checking user_rankings")
                candidate_data = await self.db.user_rankings.find_one({"github_username": username})
                
                if candidate_data:
                    # Store in HR database for future use
                    hr_candidate_data = {
                        **candidate_data,
                        "source": "user_rankings",
                        "migrated_to_hr": datetime.utcnow()
                    }
                    await store_hr_data(hr_candidate_data, HRDataType.CANDIDATE_PROFILE, "candidate_profile_migration")
                    logger.debug(f"🏢 Migrated candidate {username} to HR database")
            
            if not candidate_data:
                return None
            
            # Get profile data
            profile_data = candidate_data.get("profile", {})
            full_name = candidate_data.get("name") or profile_data.get("full_name")
            region = candidate_data.get("region") or profile_data.get("region")
            
            # Get repository category counts
            flagship_count = candidate_data.get("flagship_count", 0)
            significant_count = candidate_data.get("significant_count", 0)
            supporting_count = candidate_data.get("supporting_count", 0)
            total_repos = flagship_count + significant_count + supporting_count
            
            # Build profile with available fields
            profile = CandidateProfile(
                username=username,
                full_name=full_name,
                bio=f"Flagship: {flagship_count} | Significant: {significant_count} | Supporting: {supporting_count}",
                location=region,
                profile_picture=f"https://github.com/{username}.png",
                email=profile_data.get("email"),
                github_url=f"https://github.com/{username}",
                overall_score=candidate_data.get("overall_score", 0.0),
                upvotes=candidate_data.get("upvotes", 0),
                repositories_count=total_repos if total_repos > 0 else candidate_data.get("repository_count", 0),
                total_stars=candidate_data.get("total_stars", 0),
                total_forks=candidate_data.get("total_forks", 0),
                language_proficiency=candidate_data.get("language_proficiency", {}),
                scored_repositories=candidate_data.get("scored_repositories", []),
                account_created=candidate_data.get("account_created"),
                last_active=candidate_data.get("last_updated")
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get candidate profile for {username}: {e}")
            raise
    
    def categorize_candidate(self, languages: Dict[str, int]) -> str:
        """
        Determine candidate role category from language usage
        
        Args:
            languages: Dictionary of language names to usage counts
            
        Returns:
            str: Role category (e.g., "Full-Stack Developer")
        """
        if not languages:
            return "Software Developer"
        
        # Define language categories
        frontend_langs = {'JavaScript', 'TypeScript', 'HTML', 'CSS', 'React', 'Vue', 'Angular', 'Svelte'}
        backend_langs = {'Python', 'Java', 'Go', 'Ruby', 'PHP', 'C#', 'Rust', 'Kotlin', 'Scala'}
        mobile_langs = {'Swift', 'Kotlin', 'Dart', 'Objective-C', 'React Native', 'Flutter'}
        devops_langs = {'Shell', 'Bash', 'PowerShell', 'Dockerfile', 'YAML', 'HCL'}
        data_langs = {'Python', 'R', 'Julia', 'SQL', 'Scala'}
        
        # Calculate scores for each category
        frontend_score = sum(languages.get(lang, 0) for lang in frontend_langs)
        backend_score = sum(languages.get(lang, 0) for lang in backend_langs)
        mobile_score = sum(languages.get(lang, 0) for lang in mobile_langs)
        devops_score = sum(languages.get(lang, 0) for lang in devops_langs)
        data_score = sum(languages.get(lang, 0) for lang in data_langs)
        
        # Determine category
        if frontend_score > 0 and backend_score > 0 and frontend_score + backend_score > mobile_score:
            return "Full-Stack Developer"
        elif mobile_score > frontend_score and mobile_score > backend_score:
            return "Mobile Developer"
        elif frontend_score > backend_score:
            return "Frontend Developer"
        elif backend_score > frontend_score:
            return "Backend Developer"
        elif devops_score > frontend_score and devops_score > backend_score:
            return "DevOps Engineer"
        elif data_score > 0 and 'Python' in languages and 'R' in languages:
            return "Data Scientist"
        else:
            return "Software Developer"
    
    async def calculate_aggregate_insights(self) -> AggregateInsights:
        """
        Calculate dashboard aggregate insights from user_rankings
        
        Returns:
            AggregateInsights: Dashboard insights including totals, averages, distributions
        """
        try:
            # Get all candidates from user_rankings
            candidates_cursor = self.db.user_rankings.find({})
            candidates_data = await candidates_cursor.to_list(length=None)
            
            total_candidates = len(candidates_data)
            
            if total_candidates == 0:
                return AggregateInsights(
                    total_candidates=0,
                    average_score=0.0,
                    top_languages=[],
                    skill_distribution={},
                    top_performers=[]
                )
            
            # Calculate average score
            total_score = sum(c.get("overall_score", 0) for c in candidates_data)
            average_score = total_score / total_candidates
            
            # Calculate skill distribution
            skill_distribution = {
                "Beginner (0-4)": 0,
                "Intermediate (4-6)": 0,
                "Advanced (6-8)": 0,
                "Expert (8-10)": 0
            }
            
            for candidate in candidates_data:
                score = candidate.get("overall_score", 0)
                if score < 4:
                    skill_distribution["Beginner (0-4)"] += 1
                elif score < 6:
                    skill_distribution["Intermediate (4-6)"] += 1
                elif score < 8:
                    skill_distribution["Advanced (6-8)"] += 1
                else:
                    skill_distribution["Expert (8-10)"] += 1
            
            # Get top performers (score >= 8.0)
            top_performers_data = [c for c in candidates_data if c.get("overall_score", 0) >= 8.0]
            top_performers_data.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
            top_performers_data = top_performers_data[:5]  # Top 5
            
            top_performers = []
            for data in top_performers_data:
                candidate_card = await self._convert_ranking_to_candidate_card(data)
                if candidate_card:
                    top_performers.append(candidate_card)
            
            return AggregateInsights(
                total_candidates=total_candidates,
                average_score=round(average_score, 2),
                top_languages=[],  # Not available in user_rankings
                skill_distribution=skill_distribution,
                top_performers=top_performers
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate aggregate insights: {e}")
            raise
    
    async def get_language_distribution(self) -> Dict[str, int]:
        """
        Get language usage distribution across candidates from user_rankings
        
        Returns:
            dict: Language name to count mapping (empty for now as user_rankings doesn't store language data)
        """
        try:
            # user_rankings doesn't have language data, return empty dict
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get language distribution: {e}")
            raise
    
    # Helper methods
    
    async def _convert_to_candidate_card(self, data: dict) -> CandidateCard:
        """Convert database document to CandidateCard model"""
        username = data.get("username", "")
        metadata = data.get("metadata", {})
        
        # Get top 3 languages from metadata
        top_languages = metadata.get("top_languages", [])
        primary_languages = [lang.get("language", "") for lang in top_languages[:3]]
        
        # Convert top_languages to dict for categorization
        languages_dict = {lang.get("language", ""): lang.get("count", 0) for lang in top_languages}
        
        # Determine role category
        role_category = self.categorize_candidate(languages_dict)
        
        return CandidateCard(
            username=username,
            full_name=metadata.get("name"),
            profile_picture=metadata.get("avatar_url"),
            role_category=role_category,
            overall_score=data.get("overall_score", 0.0),
            upvotes=data.get("upvotes", 0),
            primary_languages=primary_languages,
            github_url=f"https://github.com/{username}"
        )
    
    async def _convert_ranking_to_candidate_card(self, data: dict) -> Optional[CandidateCard]:
        """Convert user_rankings document to CandidateCard model"""
        try:
            username = data.get("github_username", "")
            if not username:
                return None
            
            # Get name from profile or direct field
            full_name = data.get("name") or data.get("profile", {}).get("full_name")
            
            # Get primary languages (top 3)
            # Languages might be in different formats, try to extract them
            primary_languages = []
            
            # Try to get from profile or other fields
            # This is a simplified version - adjust based on actual data structure
            
            # Determine role category based on available data
            role_category = "Developer"  # Default
            
            # Get repository category counts
            flagship_count = data.get("flagship_count", 0)
            significant_count = data.get("significant_count", 0)
            supporting_count = data.get("supporting_count", 0)
            
            return CandidateCard(
                username=username,
                full_name=full_name,
                profile_picture=f"https://github.com/{username}.png",
                role_category=role_category,
                overall_score=data.get("overall_score", 0.0),
                upvotes=0,  # user_rankings doesn't have upvotes
                primary_languages=primary_languages,
                github_url=f"https://github.com/{username}",
                # Add category counts as additional info (if the model supports it)
                # Otherwise, these will be available in the detailed profile
            )
        except Exception as e:
            logger.error(f"Failed to convert ranking to candidate card: {e}")
            return None
    
    def _calculate_language_proficiency(self, languages: Dict[str, int]) -> Dict[str, float]:
        """Calculate language proficiency percentages"""
        if not languages:
            return {}
        
        total = sum(languages.values())
        if total == 0:
            return {}
        
        proficiency = {}
        for lang, count in languages.items():
            percentage = (count / total) * 100
            proficiency[lang] = round(percentage, 2)
        
        return proficiency


# Singleton instance
_hr_service = None


def get_hr_service(db):
    """Get or create HRService instance"""
    global _hr_service
    if _hr_service is None or _hr_service.db != db:
        _hr_service = HRService(db)
    return _hr_service
