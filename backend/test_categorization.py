#!/usr/bin/env python3
"""
Test script to verify repository categorization is working
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

async def test_categorization():
    """Test the categorization functionality"""
    from app.services.fast_github_scanner import fast_scan_github_profile
    
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment")
        return
    
    username = "raseen2305"  # Test with your username
    
    print(f"🔄 Testing categorization for user: {username}")
    print("=" * 60)
    
    try:
        result = await fast_scan_github_profile(username, github_token)
        
        print(f"\n✅ Scan completed successfully!")
        print(f"📊 Total repositories: {result.get('repositoriesCount', 0)}")
        print(f"📊 Repositories in response: {len(result.get('repositories', []))}")
        
        # Check if summary exists
        summary = result.get('summary', {})
        print(f"\n📊 Category Summary:")
        print(f"   🚀 Flagship: {summary.get('flagship', 0)}")
        print(f"   ⭐ Significant: {summary.get('significant', 0)}")
        print(f"   📦 Supporting: {summary.get('supporting', 0)}")
        
        # Check repositories
        repositories = result.get('repositories', [])
        print(f"\n📋 Repository Details:")
        for i, repo in enumerate(repositories[:5], 1):  # Show first 5
            name = repo.get('name', 'Unknown')
            language = repo.get('language', 'None')
            topics = repo.get('topics', [])
            importance = repo.get('importance_score', 0)
            category = repo.get('category', 'unknown')
            
            print(f"\n{i}. {name}")
            print(f"   Language: {language}")
            print(f"   Topics: {', '.join(topics) if topics else 'None'}")
            print(f"   Importance Score: {importance}")
            print(f"   Category: {category}")
        
        if len(repositories) > 5:
            print(f"\n... and {len(repositories) - 5} more repositories")
        
        # Verify all repos have required fields
        print(f"\n🔍 Verification:")
        missing_importance = [r.get('name') for r in repositories if 'importance_score' not in r]
        missing_category = [r.get('name') for r in repositories if 'category' not in r]
        missing_language = [r.get('name') for r in repositories if 'language' not in r]
        
        if missing_importance:
            print(f"   ❌ Repos missing importance_score: {', '.join(missing_importance)}")
        else:
            print(f"   ✅ All repos have importance_score")
        
        if missing_category:
            print(f"   ❌ Repos missing category: {', '.join(missing_category)}")
        else:
            print(f"   ✅ All repos have category")
        
        if missing_language:
            print(f"   ⚠️  Repos with no language: {', '.join(missing_language)}")
        else:
            print(f"   ✅ All repos have language")
        
        print(f"\n✅ Test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_categorization())
