#!/usr/bin/env python3
"""
Test script to verify quick_scan response structure
"""

import asyncio
import json
from app.services.fast_github_scanner import fast_scan_github_profile
from app.core.config import get_github_token

async def test_scan():
    """Test the scan and print response structure"""
    username = "raseen2305"
    github_token = get_github_token()
    
    if not github_token:
        print("❌ GitHub token not configured")
        return
    
    print(f"🔄 Testing scan for {username}...")
    print("=" * 80)
    
    try:
        result = await fast_scan_github_profile(username, github_token)
        
        print(f"\n✅ Scan completed successfully!")
        print(f"\n📊 Response Structure:")
        print(f"   - Total repositories: {len(result.get('repositories', []))}")
        print(f"   - Has summary: {bool(result.get('summary'))}")
        print(f"   - Summary: {result.get('summary')}")
        
        # Check first repository
        repos = result.get('repositories', [])
        if repos:
            first_repo = repos[0]
            print(f"\n📦 First Repository:")
            print(f"   - Name: {first_repo.get('name')}")
            print(f"   - Language: {first_repo.get('language')}")
            print(f"   - Topics: {first_repo.get('topics', [])}")
            print(f"   - Has importance_score: {bool(first_repo.get('importance_score'))}")
            print(f"   - Importance score: {first_repo.get('importance_score')}")
            print(f"   - Has category: {bool(first_repo.get('category'))}")
            print(f"   - Category: {first_repo.get('category')}")
            
            # Count categories
            flagship = sum(1 for r in repos if r.get('category') == 'flagship')
            significant = sum(1 for r in repos if r.get('category') == 'significant')
            supporting = sum(1 for r in repos if r.get('category') == 'supporting')
            no_category = sum(1 for r in repos if not r.get('category'))
            
            print(f"\n📊 Category Distribution:")
            print(f"   - Flagship: {flagship}")
            print(f"   - Significant: {significant}")
            print(f"   - Supporting: {supporting}")
            print(f"   - No category: {no_category}")
            
            # Print full structure of first repo
            print(f"\n📋 Full First Repository Structure:")
            print(json.dumps(first_repo, indent=2, default=str))
        
    except Exception as e:
        print(f"\n❌ Scan failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scan())
