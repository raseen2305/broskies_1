"""
Example usage of Scan Orchestrator with database integration

This demonstrates how to use the scan orchestrator in a real application.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scoring.orchestration.scan_orchestrator import ScanOrchestrator
from scoring.storage.scan_storage import ScanStorageService


async def example_without_database():
    """
    Example 1: Quick scan without database storage
    
    Use this when you just want to calculate importance scores
    without persisting the results.
    """
    print("\n" + "=" * 60)
    print("Example 1: Quick Scan Without Database")
    print("=" * 60)
    
    # Create orchestrator without database
    orchestrator = ScanOrchestrator()
    
    # Note: In production, you would get these from OAuth flow
    username = "octocat"  # Example GitHub username
    token = "ghp_xxxxx"   # Example OAuth token
    
    try:
        # Execute quick scan
        result = await orchestrator.execute_quick_scan(
            username=username,
            token=token,
            store_results=False  # Don't store in database
        )
        
        print(f"\nScan completed in {result['scan_time']}s")
        print(f"User: {result['user']['username']}")
        print(f"Repositories: {result['summary']['total']}")
        print(f"  - Flagship: {result['summary']['flagship']}")
        print(f"  - Significant: {result['summary']['significant']}")
        print(f"  - Supporting: {result['summary']['supporting']}")
        
        # Access repositories
        print("\nTop 5 repositories:")
        for repo in result['repositories'][:5]:
            print(
                f"  - {repo['name']}: {repo['importance_score']:.1f} "
                f"({repo['category']})"
            )
        
    except Exception as e:
        print(f"Error: {e}")


async def example_with_database():
    """
    Example 2: Quick scan with database storage
    
    Use this in production to persist scan results.
    """
    print("\n" + "=" * 60)
    print("Example 2: Quick Scan With Database Storage")
    print("=" * 60)
    
    # In production, get database from app.db_connection
    # from app.db_connection import get_database
    # database = await get_database()
    
    # For this example, we'll show the structure
    print("\nIn production, you would:")
    print("1. Get database connection:")
    print("   from app.db_connection import get_database")
    print("   database = await get_database()")
    print()
    print("2. Create orchestrator with database:")
    print("   orchestrator = ScanOrchestrator(database=database)")
    print()
    print("3. Execute scan with storage:")
    print("   result = await orchestrator.execute_quick_scan(")
    print("       username='octocat',")
    print("       token='ghp_xxxxx',")
    print("       user_id='user123',  # From auth system")
    print("       store_results=True")
    print("   )")
    print()
    print("4. Results will be stored in:")
    print("   - user_profiles collection")
    print("   - repositories collection")


async def example_repository_selection():
    """
    Example 3: Selecting repositories for Stage 2 analysis
    
    After Stage 1 completes, use this to select repositories
    for deep analysis.
    """
    print("\n" + "=" * 60)
    print("Example 3: Repository Selection for Analysis")
    print("=" * 60)
    
    orchestrator = ScanOrchestrator()
    
    # Simulate scan results
    repositories = [
        {'name': 'repo1', 'category': 'flagship', 'importance_score': 95.0},
        {'name': 'repo2', 'category': 'flagship', 'importance_score': 85.0},
        {'name': 'repo3', 'category': 'significant', 'importance_score': 65.0},
        {'name': 'repo4', 'category': 'significant', 'importance_score': 55.0},
        {'name': 'repo5', 'category': 'supporting', 'importance_score': 30.0},
    ]
    
    # Select repositories for analysis
    selected = orchestrator.select_repositories_for_analysis(repositories)
    
    print(f"\nSelected {len(selected)} repositories for Stage 2 analysis:")
    for repo in selected:
        print(
            f"  - {repo['name']}: {repo['importance_score']:.1f} "
            f"({repo['category']})"
        )
    
    print("\nNote: Supporting repositories are excluded from analysis")


async def example_storage_service():
    """
    Example 4: Using storage service directly
    
    Shows how to use the storage service for custom operations.
    """
    print("\n" + "=" * 60)
    print("Example 4: Storage Service Direct Usage")
    print("=" * 60)
    
    print("\nThe storage service provides these methods:")
    print()
    print("1. store_scan_results(user_id, user_data, repositories)")
    print("   - Stores complete scan results in parallel")
    print()
    print("2. get_user_repositories(user_id, category=None)")
    print("   - Retrieves repositories for a user")
    print("   - Optional category filter")
    print()
    print("3. get_repositories_for_analysis(user_id)")
    print("   - Gets flagship/significant repos for Stage 2")
    print("   - Limited to 15 repositories")
    print()
    print("4. update_repository_analysis(repo_id, analysis_data)")
    print("   - Updates repository with Stage 2 results")
    print()
    print("5. get_scan_summary(user_id)")
    print("   - Gets scan summary and statistics")


async def example_api_integration():
    """
    Example 5: Integration with FastAPI endpoint
    
    Shows how to use the orchestrator in an API endpoint.
    """
    print("\n" + "=" * 60)
    print("Example 5: FastAPI Endpoint Integration")
    print("=" * 60)
    
    print("\nExample FastAPI endpoint:")
    print("""
from fastapi import APIRouter, Depends, HTTPException
from app.db_connection import get_database
from scoring.orchestration.scan_orchestrator import ScanOrchestrator

router = APIRouter()

@router.post("/api/scan/quick-scan")
async def quick_scan(
    username: str,
    token: str,
    user_id: str,
    database = Depends(get_database)
):
    '''Execute Stage 1 quick scan'''
    try:
        # Create orchestrator with database
        orchestrator = ScanOrchestrator(database=database)
        
        # Execute scan
        result = await orchestrator.execute_quick_scan(
            username=username,
            token=token,
            user_id=user_id,
            store_results=True
        )
        
        return {
            'success': True,
            'user': result['user'],
            'summary': result['summary'],
            'scan_time': result['scan_time']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    """)


async def example_performance_monitoring():
    """
    Example 6: Performance monitoring
    
    Shows how to monitor scan performance.
    """
    print("\n" + "=" * 60)
    print("Example 6: Performance Monitoring")
    print("=" * 60)
    
    print("\nThe orchestrator tracks performance automatically:")
    print()
    print("1. Total scan time is returned in result['scan_time']")
    print()
    print("2. Warnings are logged if scan exceeds 1 second target")
    print()
    print("3. Storage time is tracked separately in storage_result")
    print()
    print("4. Component timings:")
    print("   - GraphQL fetch: ~0.5s")
    print("   - Importance calculation: ~0.25s")
    print("   - Database storage: ~0.2s")
    print("   - Total target: <1.0s")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("Scan Orchestrator Usage Examples")
    print("=" * 60)
    
    # Run examples
    # await example_without_database()  # Commented out - requires real GitHub token
    await example_with_database()
    await example_repository_selection()
    await example_storage_service()
    await example_api_integration()
    await example_performance_monitoring()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
