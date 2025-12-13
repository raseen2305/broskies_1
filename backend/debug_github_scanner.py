#!/usr/bin/env python3
"""
Debug script for GitHub scanner issues
"""

import asyncio
import os
import sys
sys.path.append('.')

from app.services.fast_github_scanner import fast_scan_github_profile
from app.core.config import get_github_token

async def debug_scan():
    """Debug the GitHub scanning issue"""
    username = "raseen2305"
    
    try:
        # Get token from config
        github_token = get_github_token()
        print(f"Token retrieved: {'Yes' if github_token else 'No'}")
        print(f"Token starts with: {github_token[:10]}..." if github_token else "No token")
        
        # Test scan
        print(f"\nTesting scan for user: {username}")
        result = await fast_scan_github_profile(username, github_token)
        
        print(f"\nScan successful!")
        print(f"Keys in result: {list(result.keys())}")
        print(f"Repositories found: {len(result.get('repositories', []))}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_scan())