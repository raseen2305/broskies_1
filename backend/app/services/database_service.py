"""
Database service layer for comprehensive GitHub integration.
Provides high-level database operations and business logic.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.comprehensive_models import (
    GitHubUserProfile, DetailedRepository, ComprehensiveScanResult,
    ContributionCalendar, PullRequestAnalysis, IssueAnalysis,
    ScanProgressState, CacheMetadata
)
from app.database.utils import DatabaseUtils, convert_object_ids
from app.database.migrations import DatabaseMigrator
from app.services.performance_service import performance_service

logger = logging.getLogger(__name__)

class DatabaseService:
    """High-level database service for comprehensive GitHub integration"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.utils = DatabaseUtils(database)
        self.migrator = DatabaseMigrator(database)
    
    # ========================================================================
    # User Profile Operations
    # ========================================================================
    
    async def save_github_user_profile(self, profile: GitHubUserProfile) -> str:
        """Save or update GitHub user profile (optimized)"""
        try:
            async with performance_service.track_database_performance("upsert", "github_user_profiles", "upsert"):
                # Optimized: Only dump necessary fields, exclude None values
                profile_data = profile.model_dump(
                    by_alias=True, 
                    exclude={"id"}, 
                    exclude_none=True  # Reduce document size
                )
                
                return await self.utils.upsert_document(
                    "github_user_profiles",
                    {"user_id": profile.user_id},
                    profile_data
                )
            
        except Exception as e:
            logger.error(f"Error saving GitHub user profile: {e}")
            raise
    
    async def save_github_user_profiles_batch(self, profiles: List[GitHubUserProfile]) -> List[str]:
        """Optimized: Batch save multiple GitHub user profiles"""
        try:
            if not profiles:
                return []
            
            # Prepare bulk operations
            operations = []
            for profile in profiles:
                profile_data = profile.model_dump(
                    by_alias=True, 
                    exclude={"id"}, 
                    exclude_none=True
                )
                operations.append({
                    "filter": {"user_id": profile.user_id},
                    "update": {"$set": profile_data},
                    "upsert": True
                })
            
            # Execute bulk write
            from pymongo import UpdateOne
            bulk_ops = [UpdateOne(op["filter"], op["update"], upsert=op["upsert"]) for op in operations]
            result = await self.db.github_user_profiles.bulk_write(bulk_ops, ordered=False)
            
            logger.info(f"Batch saved {len(profiles)} user profiles")
            return [str(profile.user_id) for profile in profiles]
            
        except Exception as e:
            logger.error(f"Error batch saving GitHub user profiles: {e}")
            raise
    
    async def get_github_user_profile(self, user_id: str) -> Optional[GitHubUserProfile]:
        """Get GitHub user profile by user ID"""
        try:
            profile_data = await self.db.github_user_profiles.find_one({"user_id": user_id})
            
            if profile_data:
                profile_data = await convert_object_ids(profile_data)
                return GitHubUserProfile(**profile_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting GitHub user profile: {e}")
            return None
    
    async def update_user_last_scan(self, user_id: str) -> bool:
        """Update user's last scan timestamp"""
        try:
            result = await self.db.users.update_one(
                {"_id": user_id},
                {"$set": {"last_scan": datetime.utcnow()}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating user last scan: {e}")
            return False
    
    # ========================================================================
    # Repository Operations
    # ========================================================================
    
    async def save_detailed_repository(self, repository: DetailedRepository) -> str:
        """Save or update detailed repository"""
        try:
            repo_data = repository.model_dump(by_alias=True, exclude={"id"})
            
            return await self.utils.upsert_document(
                "detailed_repositories",
                {"github_id": repository.github_id},
                repo_data
            )
            
        except Exception as e:
            logger.error(f"Error saving detailed repository: {e}")
            raise
    
    async def get_user_repositories(self, 
                                   user_id: str, 
                                   include_private: bool = True,
                                   sort_by: str = "stars",
                                   limit: Optional[int] = None) -> List[DetailedRepository]:
        """Get detailed repositories for a user"""
        try:
            repo_data_list = await self.utils.get_user_repositories(
                user_id, include_private, sort_by, limit
            )
            
            repositories = []
            for repo_data in repo_data_list:
                repo_data = await convert_object_ids(repo_data)
                repositories.append(DetailedRepository(**repo_data))
            
            return repositories
            
        except Exception as e:
            logger.error(f"Error getting user repositories: {e}")
            return []
    
    async def get_repository_by_github_id(self, github_id: int) -> Optional[DetailedRepository]:
        """Get repository by GitHub ID"""
        try:
            repo_data = await self.db.detailed_repositories.find_one({"github_id": github_id})
            
            if repo_data:
                repo_data = await convert_object_ids(repo_data)
                return DetailedRepository(**repo_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting repository by GitHub ID: {e}")
            return None
    
    async def update_repository_analysis(self, 
                                       github_id: int, 
                                       analysis_data: Dict[str, Any]) -> bool:
        """Update repository analysis data"""
        try:
            analysis_data["last_analyzed"] = datetime.utcnow()
            
            result = await self.db.detailed_repositories.update_one(
                {"github_id": github_id},
                {"$set": analysis_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating repository analysis: {e}")
            return False
    
    # ========================================================================
    # Scan Result Operations
    # ========================================================================
    
    async def save_comprehensive_scan_result(self, scan_result: ComprehensiveScanResult) -> str:
        """Save comprehensive scan result"""
        try:
            scan_data = scan_result.model_dump(by_alias=True, exclude={"id"})
            
            return await self.utils.upsert_document(
                "comprehensive_scan_results",
                {"scan_metadata.scan_id": scan_result.scan_metadata.scan_id},
                scan_data
            )
            
        except Exception as e:
            logger.error(f"Error saving comprehensive scan result: {e}")
            raise
    
    async def get_latest_scan_result(self, user_id: str) -> Optional[ComprehensiveScanResult]:
        """Get latest comprehensive scan result for user"""
        try:
            scan_data = await self.db.comprehensive_scan_results.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            
            if scan_data:
                scan_data = await convert_object_ids(scan_data)
                return ComprehensiveScanResult(**scan_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest scan result: {e}")
            return None
    
    async def get_scan_result_by_id(self, scan_id: str) -> Optional[ComprehensiveScanResult]:
        """Get scan result by scan ID"""
        try:
            scan_data = await self.db.comprehensive_scan_results.find_one(
                {"scan_metadata.scan_id": scan_id}
            )
            
            if scan_data:
                scan_data = await convert_object_ids(scan_data)
                return ComprehensiveScanResult(**scan_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting scan result by ID: {e}")
            return None
    
    # ========================================================================
    # Contribution Calendar Operations
    # ========================================================================
    
    async def save_contribution_calendar(self, calendar: ContributionCalendar) -> str:
        """Save or update contribution calendar"""
        try:
            calendar_data = calendar.model_dump(by_alias=True, exclude={"id"})
            
            return await self.utils.upsert_document(
                "contribution_calendars",
                {
                    "user_id": calendar.user_id,
                    "calendar_year": calendar.calendar_year
                },
                calendar_data
            )
            
        except Exception as e:
            logger.error(f"Error saving contribution calendar: {e}")
            raise
    
    async def get_contribution_calendar(self, 
                                      user_id: str, 
                                      year: Optional[int] = None) -> Optional[ContributionCalendar]:
        """Get contribution calendar for user and year"""
        try:
            query = {"user_id": user_id}
            if year:
                query["calendar_year"] = year
            
            calendar_data = await self.db.contribution_calendars.find_one(
                query,
                sort=[("calendar_year", -1)]
            )
            
            if calendar_data:
                calendar_data = await convert_object_ids(calendar_data)
                return ContributionCalendar(**calendar_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting contribution calendar: {e}")
            return None
    
    # ========================================================================
    # Pull Request and Issue Analysis Operations
    # ========================================================================
    
    async def save_pull_request_analysis(self, analysis: PullRequestAnalysis) -> str:
        """Save pull request analysis"""
        try:
            analysis_data = analysis.model_dump(by_alias=True, exclude={"id"})
            
            return await self.utils.upsert_document(
                "pull_request_analysis",
                {"repository_id": analysis.repository_id},
                analysis_data
            )
            
        except Exception as e:
            logger.error(f"Error saving pull request analysis: {e}")
            raise
    
    async def save_issue_analysis(self, analysis: IssueAnalysis) -> str:
        """Save issue analysis"""
        try:
            analysis_data = analysis.model_dump(by_alias=True, exclude={"id"})
            
            return await self.utils.upsert_document(
                "issue_analysis",
                {"repository_id": analysis.repository_id},
                analysis_data
            )
            
        except Exception as e:
            logger.error(f"Error saving issue analysis: {e}")
            raise
    
    async def get_repository_pull_request_analysis(self, repository_id: str) -> Optional[PullRequestAnalysis]:
        """Get pull request analysis for repository"""
        try:
            analysis_data = await self.db.pull_request_analysis.find_one(
                {"repository_id": repository_id}
            )
            
            if analysis_data:
                analysis_data = await convert_object_ids(analysis_data)
                return PullRequestAnalysis(**analysis_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting pull request analysis: {e}")
            return None
    
    async def get_repository_issue_analysis(self, repository_id: str) -> Optional[IssueAnalysis]:
        """Get issue analysis for repository"""
        try:
            analysis_data = await self.db.issue_analysis.find_one(
                {"repository_id": repository_id}
            )
            
            if analysis_data:
                analysis_data = await convert_object_ids(analysis_data)
                return IssueAnalysis(**analysis_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting issue analysis: {e}")
            return None
    
    # ========================================================================
    # Scan Progress Operations
    # ========================================================================
    
    async def save_scan_progress(self, progress: ScanProgressState) -> str:
        """Save scan progress state"""
        try:
            progress_data = progress.model_dump(by_alias=True, exclude={"id"})
            
            return await self.utils.upsert_document(
                "scan_progress",
                {"scan_id": progress.scan_id},
                progress_data,
                update_timestamp=False  # We manage last_update manually
            )
            
        except Exception as e:
            logger.error(f"Error saving scan progress: {e}")
            raise
    
    async def get_scan_progress(self, scan_id: str) -> Optional[ScanProgressState]:
        """Get scan progress by scan ID"""
        try:
            progress_data = await self.db.scan_progress.find_one({"scan_id": scan_id})
            
            if progress_data:
                progress_data = await convert_object_ids(progress_data)
                return ScanProgressState(**progress_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting scan progress: {e}")
            return None
    
    async def update_scan_progress(self, 
                                  scan_id: str, 
                                  updates: Dict[str, Any]) -> bool:
        """Update scan progress with specific fields"""
        try:
            updates["last_update"] = datetime.utcnow()
            
            result = await self.db.scan_progress.update_one(
                {"scan_id": scan_id},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating scan progress: {e}")
            return False
    
    # ========================================================================
    # Cache Operations
    # ========================================================================
    
    async def save_cache_metadata(self, cache_meta: CacheMetadata) -> str:
        """Save cache metadata"""
        try:
            cache_data = cache_meta.model_dump(by_alias=True, exclude={"id"})
            
            return await self.utils.upsert_document(
                "cache_metadata",
                {"cache_key": cache_meta.cache_key},
                cache_data
            )
            
        except Exception as e:
            logger.error(f"Error saving cache metadata: {e}")
            raise
    
    async def get_cache_metadata(self, cache_key: str) -> Optional[CacheMetadata]:
        """Get cache metadata by key"""
        try:
            cache_data = await self.db.cache_metadata.find_one({"cache_key": cache_key})
            
            if cache_data:
                cache_data = await convert_object_ids(cache_data)
                return CacheMetadata(**cache_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cache metadata: {e}")
            return None
    
    async def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries"""
        try:
            result = await self.db.cache_metadata.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} expired cache entries")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")
            return 0
    
    # ========================================================================
    # Analytics and Reporting Operations
    # ========================================================================
    
    async def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user analytics"""
        try:
            # Get repository analytics
            repo_analytics = await self.utils.get_repository_analytics(user_id)
            
            # Get latest scan result
            latest_scan = await self.get_latest_scan_result(user_id)
            
            # Get contribution calendar
            contribution_calendar = await self.get_contribution_calendar(user_id)
            
            analytics = {
                "repository_analytics": repo_analytics,
                "latest_scan_date": latest_scan.created_at if latest_scan else None,
                "overall_acid_score": latest_scan.overall_acid_score if latest_scan else 0.0,
                "overall_quality_score": latest_scan.overall_quality_score if latest_scan else 0.0,
                "developer_level": latest_scan.developer_level if latest_scan else "beginner",
                "total_contributions": contribution_calendar.total_contributions if contribution_calendar else 0,
                "current_streak": contribution_calendar.current_streak if contribution_calendar else 0,
                "longest_streak": contribution_calendar.longest_streak if contribution_calendar else 0
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return {}
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        try:
            stats = await self.utils.get_collection_statistics()
            
            # Add some computed statistics
            total_users = stats.get("users", {}).get("document_count", 0)
            total_repos = stats.get("detailed_repositories", {}).get("document_count", 0)
            total_scans = stats.get("comprehensive_scan_results", {}).get("document_count", 0)
            
            # Calculate average repositories per user
            avg_repos_per_user = total_repos / total_users if total_users > 0 else 0
            
            system_stats = {
                "collection_statistics": stats,
                "summary": {
                    "total_users": total_users,
                    "total_repositories": total_repos,
                    "total_scans": total_scans,
                    "avg_repositories_per_user": round(avg_repos_per_user, 2)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return system_stats
            
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return {}
    
    # ========================================================================
    # Maintenance Operations
    # ========================================================================
    
    async def run_maintenance(self) -> Dict[str, Any]:
        """Run database maintenance tasks"""
        try:
            maintenance_results = {}
            
            # Clean up expired data
            cleanup_results = await self.utils.cleanup_expired_data()
            maintenance_results["cleanup"] = cleanup_results
            
            # Clean up expired cache
            cache_cleanup = await self.cleanup_expired_cache()
            maintenance_results["cache_cleanup"] = cache_cleanup
            
            # Validate data integrity
            integrity_results = await self.migrator.validate_data_integrity()
            maintenance_results["integrity_check"] = integrity_results
            
            maintenance_results["timestamp"] = datetime.utcnow().isoformat()
            maintenance_results["success"] = True
            
            logger.info(f"Database maintenance completed: {maintenance_results}")
            return maintenance_results
            
        except Exception as e:
            logger.error(f"Error during database maintenance: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }