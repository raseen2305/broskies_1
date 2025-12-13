"""
Database migration scripts for comprehensive GitHub integration.
Handles data migration between different schema versions.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.comprehensive_models import (
    GitHubUserProfile, DetailedRepository, ComprehensiveScanResult,
    ScanMetadata, CollaborationMetrics, LanguageStatistics, AchievementMetrics
)

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles database migrations for schema updates"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        
    async def migrate_users_to_comprehensive(self) -> int:
        """Migrate basic user records to comprehensive format"""
        migrated_count = 0
        
        try:
            # Get all users that don't have comprehensive profiles
            users_cursor = self.db.users.find({})
            
            async for user in users_cursor:
                user_id = str(user.get("_id", ""))
                
                # Check if comprehensive profile already exists
                existing_profile = await self.db.github_user_profiles.find_one(
                    {"user_id": user_id}
                )
                
                if not existing_profile and user.get("github_username"):
                    # Create placeholder comprehensive profile
                    github_profile = GitHubUserProfile(
                        user_id=user_id,
                        login=user["github_username"],
                        github_id=0,  # Will be updated during next scan
                        name=None,
                        email=user.get("email"),
                        avatar_url="",
                        html_url=f"https://github.com/{user['github_username']}",
                        github_created_at=user.get("created_at", datetime.utcnow()),
                        github_updated_at=user.get("created_at", datetime.utcnow())
                    )
                    
                    await self.db.github_user_profiles.insert_one(
                        github_profile.model_dump(by_alias=True, exclude={"id"})
                    )
                    migrated_count += 1
                    
            logger.info(f"Migrated {migrated_count} users to comprehensive format")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error migrating users: {e}")
            return 0
    
    async def migrate_repositories_to_detailed(self) -> int:
        """Migrate basic repository records to detailed format"""
        migrated_count = 0
        
        try:
            # Get all repositories that don't have detailed analysis
            repos_cursor = self.db.repositories.find({})
            
            async for repo in repos_cursor:
                repo_id = str(repo.get("_id", ""))
                
                # Check if detailed repository already exists
                existing_detailed = await self.db.detailed_repositories.find_one(
                    {"github_id": repo.get("github_id")}
                )
                
                if not existing_detailed:
                    # Create detailed repository from basic data
                    detailed_repo = DetailedRepository(
                        user_id=repo["user_id"],
                        github_id=repo["github_id"],
                        name=repo["name"],
                        full_name=repo["full_name"],
                        description=repo.get("description"),
                        language=repo.get("language"),
                        languages=repo.get("languages", {}),
                        stars=repo.get("stars", 0),
                        forks=repo.get("forks", 0),
                        size=repo.get("size", 0),
                        created_at=repo["created_at"],
                        updated_at=repo["updated_at"],
                        pushed_at=repo.get("pushed_at"),
                        is_fork=repo.get("is_fork", False),
                        is_private=repo.get("is_private", False),
                        topics=repo.get("topics", []),
                        license=repo.get("license"),
                        default_branch=repo.get("default_branch", "main"),
                        clone_url=repo["clone_url"],
                        html_url=repo["html_url"]
                    )
                    
                    await self.db.detailed_repositories.insert_one(
                        detailed_repo.model_dump(by_alias=True, exclude={"id"})
                    )
                    migrated_count += 1
                    
            logger.info(f"Migrated {migrated_count} repositories to detailed format")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error migrating repositories: {e}")
            return 0
    
    async def migrate_scan_results_to_comprehensive(self) -> int:
        """Migrate basic scan results to comprehensive format"""
        migrated_count = 0
        
        try:
            # Get all scan results that need migration
            scans_cursor = self.db.scan_results.find({}) if hasattr(self.db, 'scan_results') else []
            
            async for scan in scans_cursor:
                user_id = scan.get("user_id")
                
                # Check if comprehensive scan result already exists
                existing_comprehensive = await self.db.comprehensive_scan_results.find_one(
                    {"user_id": user_id, "scan_metadata.task_id": scan.get("task_id")}
                )
                
                if not existing_comprehensive:
                    # Create comprehensive scan result from basic data
                    scan_metadata = ScanMetadata(
                        scan_id=scan.get("task_id", ""),
                        scan_type=scan.get("scan_type", "basic"),
                        total_repositories=len(scan.get("repositories", [])),
                        successful_repositories=len(scan.get("repositories", [])),
                        scan_duration=0.0,
                        scan_started_at=scan.get("scan_completed_at", datetime.utcnow()),
                        scan_completed_at=scan.get("scan_completed_at")
                    )
                    
                    # Create placeholder user profile
                    user_profile = GitHubUserProfile(
                        user_id=user_id,
                        login="unknown",
                        github_id=0,
                        avatar_url="",
                        html_url="",
                        github_created_at=datetime.utcnow(),
                        github_updated_at=datetime.utcnow()
                    )
                    
                    comprehensive_result = ComprehensiveScanResult(
                        user_id=user_id,
                        user_profile=user_profile,
                        repositories=[],
                        collaboration_metrics=CollaborationMetrics(),
                        language_statistics=LanguageStatistics(),
                        achievement_metrics=AchievementMetrics(),
                        scan_metadata=scan_metadata
                    )
                    
                    await self.db.comprehensive_scan_results.insert_one(
                        comprehensive_result.model_dump(by_alias=True, exclude={"id"})
                    )
                    migrated_count += 1
                    
            logger.info(f"Migrated {migrated_count} scan results to comprehensive format")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error migrating scan results: {e}")
            return 0
    
    async def cleanup_old_data(self, days_old: int = 30) -> Dict[str, int]:
        """Clean up old data that's no longer needed"""
        cleanup_results = {}
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        try:
            # Clean up old scan progress records
            scan_progress_result = await self.db.scan_progress.delete_many({
                "last_update": {"$lt": cutoff_date}
            })
            cleanup_results["scan_progress"] = scan_progress_result.deleted_count
            
            # Clean up expired cache metadata
            cache_result = await self.db.cache_metadata.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            cleanup_results["cache_metadata"] = cache_result.deleted_count
            
            # Clean up old scan results (keep only latest per user)
            users_cursor = self.db.users.find({}, {"_id": 1})
            old_scans_deleted = 0
            
            async for user in users_cursor:
                user_id = str(user["_id"])
                
                # Keep only the 3 most recent comprehensive scan results per user
                recent_scans = await self.db.comprehensive_scan_results.find(
                    {"user_id": user_id}
                ).sort("created_at", -1).limit(3).to_list(length=None)
                
                if len(recent_scans) >= 3:
                    keep_ids = [scan["_id"] for scan in recent_scans]
                    delete_result = await self.db.comprehensive_scan_results.delete_many({
                        "user_id": user_id,
                        "_id": {"$nin": keep_ids}
                    })
                    old_scans_deleted += delete_result.deleted_count
            
            cleanup_results["old_scan_results"] = old_scans_deleted
            
            logger.info(f"Cleanup completed: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return cleanup_results
    
    async def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data integrity across collections"""
        validation_results = {
            "users_with_profiles": 0,
            "repositories_with_details": 0,
            "orphaned_profiles": 0,
            "orphaned_repositories": 0,
            "missing_scan_results": 0,
            "issues": []
        }
        
        try:
            # Check users with GitHub profiles
            users_count = await self.db.users.count_documents({})
            profiles_count = await self.db.github_user_profiles.count_documents({})
            validation_results["users_with_profiles"] = profiles_count
            
            if profiles_count < users_count:
                validation_results["issues"].append(
                    f"{users_count - profiles_count} users missing GitHub profiles"
                )
            
            # Check repositories with detailed analysis
            basic_repos_count = await self.db.repositories.count_documents({})
            detailed_repos_count = await self.db.detailed_repositories.count_documents({})
            validation_results["repositories_with_details"] = detailed_repos_count
            
            if detailed_repos_count < basic_repos_count:
                validation_results["issues"].append(
                    f"{basic_repos_count - detailed_repos_count} repositories missing detailed analysis"
                )
            
            # Check for orphaned records
            orphaned_profiles = 0
            profiles_cursor = self.db.github_user_profiles.find({})
            
            async for profile in profiles_cursor:
                user_exists = await self.db.users.find_one({"_id": profile["user_id"]})
                if not user_exists:
                    orphaned_profiles += 1
            
            validation_results["orphaned_profiles"] = orphaned_profiles
            
            if orphaned_profiles > 0:
                validation_results["issues"].append(
                    f"{orphaned_profiles} orphaned GitHub profiles found"
                )
            
            logger.info(f"Data integrity validation completed: {validation_results}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error during data integrity validation: {e}")
            validation_results["issues"].append(f"Validation error: {str(e)}")
            return validation_results

# Migration utility functions
async def run_full_migration(database: AsyncIOMotorDatabase) -> Dict[str, int]:
    """Run complete migration to comprehensive schema"""
    migrator = DatabaseMigrator(database)
    
    results = {
        "users_migrated": await migrator.migrate_users_to_comprehensive(),
        "repositories_migrated": await migrator.migrate_repositories_to_detailed(),
        "scan_results_migrated": await migrator.migrate_scan_results_to_comprehensive()
    }
    
    logger.info(f"Full migration completed: {results}")
    return results

async def cleanup_database(database: AsyncIOMotorDatabase, days_old: int = 30) -> Dict[str, int]:
    """Clean up old database records"""
    migrator = DatabaseMigrator(database)
    return await migrator.cleanup_old_data(days_old)

async def validate_database_integrity(database: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Validate database integrity"""
    migrator = DatabaseMigrator(database)
    return await migrator.validate_data_integrity()