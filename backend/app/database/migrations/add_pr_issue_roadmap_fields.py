"""
Migration: Add PR/Issue/Roadmap fields to existing repositories

This migration adds the new pull_requests, issues, and roadmap fields
to existing repository documents in the database.

Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.3
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from app.database import get_database

logger = logging.getLogger(__name__)


async def migrate_add_pr_issue_roadmap_fields():
    """
    Add pull_requests, issues, and roadmap fields to existing repositories.
    
    This migration:
    1. Finds all repositories without the new fields
    2. Adds default null values for pull_requests, issues, and roadmap
    3. Logs the number of documents updated
    """
    
    try:
        db = await get_database()
        
        logger.info("Starting migration: add_pr_issue_roadmap_fields")
        
        # Count repositories that need migration
        repos_without_fields = await db.repositories.count_documents({
            "$or": [
                {"pull_requests": {"$exists": False}},
                {"issues": {"$exists": False}},
                {"roadmap": {"$exists": False}}
            ]
        })
        
        logger.info(f"Found {repos_without_fields} repositories to migrate")
        
        if repos_without_fields == 0:
            logger.info("No repositories need migration")
            return {
                "status": "success",
                "message": "No repositories need migration",
                "updated_count": 0
            }
        
        # Update repositories with missing fields
        result = await db.repositories.update_many(
            {
                "$or": [
                    {"pull_requests": {"$exists": False}},
                    {"issues": {"$exists": False}},
                    {"roadmap": {"$exists": False}}
                ]
            },
            {
                "$set": {
                    "pull_requests": None,
                    "issues": None,
                    "roadmap": None,
                    "migration_updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Migration completed: {result.modified_count} repositories updated")
        
        return {
            "status": "success",
            "message": f"Successfully migrated {result.modified_count} repositories",
            "updated_count": result.modified_count,
            "matched_count": result.matched_count
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return {
            "status": "error",
            "message": f"Migration failed: {str(e)}",
            "updated_count": 0
        }


async def migrate_scan_results_add_pr_issue_roadmap_fields():
    """
    Add pull_requests, issues, and roadmap fields to repositories in scan_results.
    
    This migration updates the repositories array within scan_results documents.
    """
    
    try:
        db = await get_database()
        
        logger.info("Starting migration: add_pr_issue_roadmap_fields to scan_results")
        
        # Get all scan results
        scan_results = await db.scan_results.find({}).to_list(length=None)
        
        logger.info(f"Found {len(scan_results)} scan results to check")
        
        updated_count = 0
        
        for scan_result in scan_results:
            repositories = scan_result.get('repositories', [])
            needs_update = False
            
            # Check if any repository needs the new fields
            for repo in repositories:
                if 'pull_requests' not in repo or 'issues' not in repo or 'roadmap' not in repo:
                    repo['pull_requests'] = None
                    repo['issues'] = None
                    repo['roadmap'] = None
                    needs_update = True
            
            # Update the scan result if needed
            if needs_update:
                await db.scan_results.update_one(
                    {"_id": scan_result["_id"]},
                    {
                        "$set": {
                            "repositories": repositories,
                            "migration_updated_at": datetime.utcnow()
                        }
                    }
                )
                updated_count += 1
        
        logger.info(f"Migration completed: {updated_count} scan results updated")
        
        return {
            "status": "success",
            "message": f"Successfully migrated {updated_count} scan results",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return {
            "status": "error",
            "message": f"Migration failed: {str(e)}",
            "updated_count": 0
        }


async def rollback_pr_issue_roadmap_fields():
    """
    Rollback migration by removing the new fields.
    
    WARNING: This will remove all PR/issue/roadmap data!
    """
    
    try:
        db = await get_database()
        
        logger.warning("Starting rollback: remove_pr_issue_roadmap_fields")
        
        # Remove fields from repositories
        result1 = await db.repositories.update_many(
            {},
            {
                "$unset": {
                    "pull_requests": "",
                    "issues": "",
                    "roadmap": "",
                    "migration_updated_at": ""
                }
            }
        )
        
        # Remove fields from scan_results
        scan_results = await db.scan_results.find({}).to_list(length=None)
        updated_count = 0
        
        for scan_result in scan_results:
            repositories = scan_result.get('repositories', [])
            
            for repo in repositories:
                repo.pop('pull_requests', None)
                repo.pop('issues', None)
                repo.pop('roadmap', None)
            
            await db.scan_results.update_one(
                {"_id": scan_result["_id"]},
                {
                    "$set": {"repositories": repositories},
                    "$unset": {"migration_updated_at": ""}
                }
            )
            updated_count += 1
        
        logger.warning(f"Rollback completed: {result1.modified_count} repositories, {updated_count} scan results")
        
        return {
            "status": "success",
            "message": f"Rollback completed: {result1.modified_count} repositories, {updated_count} scan results",
            "repositories_updated": result1.modified_count,
            "scan_results_updated": updated_count
        }
        
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        return {
            "status": "error",
            "message": f"Rollback failed: {str(e)}"
        }


def run_migration():
    """Run the migration synchronously"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run repository migration
        result1 = loop.run_until_complete(migrate_add_pr_issue_roadmap_fields())
        print(f"Repository migration: {result1}")
        
        # Run scan results migration
        result2 = loop.run_until_complete(migrate_scan_results_add_pr_issue_roadmap_fields())
        print(f"Scan results migration: {result2}")
        
        return {
            "repositories": result1,
            "scan_results": result2
        }
    finally:
        loop.close()


def run_rollback():
    """Run the rollback synchronously"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(rollback_pr_issue_roadmap_fields())
        print(f"Rollback: {result}")
        return result
    finally:
        loop.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        print("Running rollback...")
        run_rollback()
    else:
        print("Running migration...")
        run_migration()
