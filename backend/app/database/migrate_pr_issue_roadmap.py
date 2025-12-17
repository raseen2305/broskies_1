"""
Migration script to add PR/Issue/Roadmap fields to existing repositories.

This migration adds the following fields to existing repository documents:
- pull_requests: PRStatistics
- issues: IssueStatistics  
- roadmap: Roadmap

Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.3
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.core.config import settings

logger = logging.getLogger(__name__)


class PRIssueRoadmapMigration:
    """Migrates existing repositories to include PR/Issue/Roadmap fields"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        
    async def migrate_scan_results(self) -> Dict[str, int]:
        """
        Add PR/Issue/Roadmap fields to repositories in scan_results collection.
        
        Returns:
            Dictionary with migration statistics
        """
        stats = {
            "total_scans": 0,
            "scans_updated": 0,
            "repositories_updated": 0,
            "errors": 0
        }
        
        try:
            logger.info("Starting migration of scan_results collection...")
            
            # Find all scan results
            scan_results = await self.db.scan_results.find({}).to_list(length=None)
            stats["total_scans"] = len(scan_results)
            
            for scan in scan_results:
                try:
                    scan_id = scan.get("_id")
                    repositories = scan.get("repositories", [])
                    
                    if not repositories:
                        continue
                    
                    # Check if any repository is missing the new fields
                    needs_update = False
                    updated_repos = []
                    
                    for repo in repositories:
                        # Check if PR/Issue/Roadmap fields exist
                        if "pull_requests" not in repo or "issues" not in repo or "roadmap" not in repo:
                            needs_update = True
                            
                            # Add default null values for new fields if missing
                            if "pull_requests" not in repo:
                                repo["pull_requests"] = None
                            if "issues" not in repo:
                                repo["issues"] = None
                            if "roadmap" not in repo:
                                repo["roadmap"] = None
                            
                            stats["repositories_updated"] += 1
                        
                        updated_repos.append(repo)
                    
                    # Update the scan result if needed
                    if needs_update:
                        await self.db.scan_results.update_one(
                            {"_id": scan_id},
                            {
                                "$set": {
                                    "repositories": updated_repos,
                                    "migrated_at": datetime.utcnow()
                                }
                            }
                        )
                        stats["scans_updated"] += 1
                        logger.info(f"Updated scan {scan_id} with {len(updated_repos)} repositories")
                
                except Exception as e:
                    logger.error(f"Error updating scan {scan.get('_id')}: {e}")
                    stats["errors"] += 1
            
            logger.info(f"Scan results migration completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during scan results migration: {e}")
            stats["errors"] += 1
            return stats
    
    async def migrate_repositories_collection(self) -> Dict[str, int]:
        """
        Add PR/Issue/Roadmap fields to documents in repositories collection.
        
        Returns:
            Dictionary with migration statistics
        """
        stats = {
            "total_repositories": 0,
            "repositories_updated": 0,
            "errors": 0
        }
        
        try:
            logger.info("Starting migration of repositories collection...")
            
            # Find all repositories that don't have the new fields
            query = {
                "$or": [
                    {"pull_requests": {"$exists": False}},
                    {"issues": {"$exists": False}},
                    {"roadmap": {"$exists": False}}
                ]
            }
            
            repositories = await self.db.repositories.find(query).to_list(length=None)
            stats["total_repositories"] = len(repositories)
            
            for repo in repositories:
                try:
                    repo_id = repo.get("_id")
                    
                    # Prepare update fields
                    update_fields = {}
                    
                    if "pull_requests" not in repo:
                        update_fields["pull_requests"] = None
                    if "issues" not in repo:
                        update_fields["issues"] = None
                    if "roadmap" not in repo:
                        update_fields["roadmap"] = None
                    
                    if update_fields:
                        update_fields["migrated_at"] = datetime.utcnow()
                        
                        await self.db.repositories.update_one(
                            {"_id": repo_id},
                            {"$set": update_fields}
                        )
                        stats["repositories_updated"] += 1
                
                except Exception as e:
                    logger.error(f"Error updating repository {repo.get('_id')}: {e}")
                    stats["errors"] += 1
            
            logger.info(f"Repositories collection migration completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during repositories migration: {e}")
            stats["errors"] += 1
            return stats
    
    async def migrate_detailed_repositories(self) -> Dict[str, int]:
        """
        Add PR/Issue/Roadmap fields to detailed_repositories collection.
        
        Returns:
            Dictionary with migration statistics
        """
        stats = {
            "total_repositories": 0,
            "repositories_updated": 0,
            "errors": 0
        }
        
        try:
            logger.info("Starting migration of detailed_repositories collection...")
            
            # Find all detailed repositories that don't have the new fields
            query = {
                "$or": [
                    {"pull_requests": {"$exists": False}},
                    {"issues": {"$exists": False}},
                    {"roadmap": {"$exists": False}}
                ]
            }
            
            repositories = await self.db.detailed_repositories.find(query).to_list(length=None)
            stats["total_repositories"] = len(repositories)
            
            for repo in repositories:
                try:
                    repo_id = repo.get("_id")
                    
                    # Prepare update fields
                    update_fields = {}
                    
                    if "pull_requests" not in repo:
                        update_fields["pull_requests"] = None
                    if "issues" not in repo:
                        update_fields["issues"] = None
                    if "roadmap" not in repo:
                        update_fields["roadmap"] = None
                    
                    if update_fields:
                        update_fields["migrated_at"] = datetime.utcnow()
                        
                        await self.db.detailed_repositories.update_one(
                            {"_id": repo_id},
                            {"$set": update_fields}
                        )
                        stats["repositories_updated"] += 1
                
                except Exception as e:
                    logger.error(f"Error updating detailed repository {repo.get('_id')}: {e}")
                    stats["errors"] += 1
            
            logger.info(f"Detailed repositories migration completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during detailed repositories migration: {e}")
            stats["errors"] += 1
            return stats
    
    async def run_full_migration(self) -> Dict[str, Any]:
        """
        Run complete migration across all collections.
        
        Returns:
            Dictionary with comprehensive migration statistics
        """
        logger.info("=" * 60)
        logger.info("Starting PR/Issue/Roadmap Migration")
        logger.info("=" * 60)
        
        results = {
            "scan_results": await self.migrate_scan_results(),
            "repositories": await self.migrate_repositories_collection(),
            "detailed_repositories": await self.migrate_detailed_repositories(),
            "migration_completed_at": datetime.utcnow().isoformat()
        }
        
        # Calculate totals
        total_updated = (
            results["scan_results"]["scans_updated"] +
            results["repositories"]["repositories_updated"] +
            results["detailed_repositories"]["repositories_updated"]
        )
        
        total_errors = (
            results["scan_results"]["errors"] +
            results["repositories"]["errors"] +
            results["detailed_repositories"]["errors"]
        )
        
        results["summary"] = {
            "total_documents_updated": total_updated,
            "total_errors": total_errors,
            "status": "completed" if total_errors == 0 else "completed_with_errors"
        }
        
        logger.info("=" * 60)
        logger.info("Migration Summary:")
        logger.info(f"  Total documents updated: {total_updated}")
        logger.info(f"  Total errors: {total_errors}")
        logger.info(f"  Status: {results['summary']['status']}")
        logger.info("=" * 60)
        
        return results
    
    async def verify_migration(self) -> Dict[str, Any]:
        """
        Verify that migration was successful.
        
        Returns:
            Dictionary with verification results
        """
        logger.info("Verifying migration...")
        
        verification = {
            "scan_results": {
                "total": 0,
                "with_new_fields": 0,
                "missing_fields": 0
            },
            "repositories": {
                "total": 0,
                "with_new_fields": 0,
                "missing_fields": 0
            },
            "detailed_repositories": {
                "total": 0,
                "with_new_fields": 0,
                "missing_fields": 0
            }
        }
        
        try:
            # Verify scan_results
            total_scans = await self.db.scan_results.count_documents({})
            verification["scan_results"]["total"] = total_scans
            
            # Count scans where all repos have new fields
            scans_with_fields = 0
            async for scan in self.db.scan_results.find({}):
                repos = scan.get("repositories", [])
                if repos and all(
                    "pull_requests" in repo and "issues" in repo and "roadmap" in repo
                    for repo in repos
                ):
                    scans_with_fields += 1
            
            verification["scan_results"]["with_new_fields"] = scans_with_fields
            verification["scan_results"]["missing_fields"] = total_scans - scans_with_fields
            
            # Verify repositories collection
            total_repos = await self.db.repositories.count_documents({})
            verification["repositories"]["total"] = total_repos
            
            repos_with_fields = await self.db.repositories.count_documents({
                "pull_requests": {"$exists": True},
                "issues": {"$exists": True},
                "roadmap": {"$exists": True}
            })
            verification["repositories"]["with_new_fields"] = repos_with_fields
            verification["repositories"]["missing_fields"] = total_repos - repos_with_fields
            
            # Verify detailed_repositories collection
            total_detailed = await self.db.detailed_repositories.count_documents({})
            verification["detailed_repositories"]["total"] = total_detailed
            
            detailed_with_fields = await self.db.detailed_repositories.count_documents({
                "pull_requests": {"$exists": True},
                "issues": {"$exists": True},
                "roadmap": {"$exists": True}
            })
            verification["detailed_repositories"]["with_new_fields"] = detailed_with_fields
            verification["detailed_repositories"]["missing_fields"] = total_detailed - detailed_with_fields
            
            logger.info("Verification completed:")
            logger.info(f"  Scan results: {scans_with_fields}/{total_scans} migrated")
            logger.info(f"  Repositories: {repos_with_fields}/{total_repos} migrated")
            logger.info(f"  Detailed repositories: {detailed_with_fields}/{total_detailed} migrated")
            
            return verification
            
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            return verification


async def run_migration():
    """Main migration function"""
    try:
        # Get database connection
        db = await get_database()
        
        # Create migrator
        migrator = PRIssueRoadmapMigration(db)
        
        # Run migration
        results = await migrator.run_full_migration()
        
        # Verify migration
        verification = await migrator.verify_migration()
        
        return {
            "migration_results": results,
            "verification": verification
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run migration
    print("\n" + "=" * 60)
    print("PR/Issue/Roadmap Migration Script")
    print("=" * 60 + "\n")
    
    result = asyncio.run(run_migration())
    
    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60 + "\n")
    
    print("Results:")
    print(f"  Migration: {result['migration_results']['summary']}")
    print(f"  Verification: {result['verification']}")
