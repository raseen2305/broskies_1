#!/usr/bin/env python3
"""
Simple test script to check if rankings endpoints are working
"""

import asyncio
import httpx
import json

async def test_rankings_endpoints():
    """Test the rankings endpoints"""
    
    base_url = "http://localhost:8000"
    
    # Test endpoints without authentication first
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Rankings Endpoints")
        print("=" * 50)
        
        # Test basic health check
        try:
            response = await client.get(f"{base_url}/health")
            print(f"✅ Health Check: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"❌ Health Check Failed: {e}")
        
        # Test rankings endpoint (should return 401 without auth)
        try:
            response = await client.get(f"{base_url}/rankings")
            print(f"📊 Rankings Endpoint: {response.status_code}")
            if response.status_code == 401:
                print("✅ Rankings endpoint exists (requires authentication)")
            elif response.status_code == 404:
                print("❌ Rankings endpoint not found (404)")
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"❌ Rankings Endpoint Error: {e}")
        
        # Test rankings status endpoint
        try:
            response = await client.get(f"{base_url}/rankings/status")
            print(f"📊 Rankings Status Endpoint: {response.status_code}")
            if response.status_code == 401:
                print("✅ Rankings status endpoint exists (requires authentication)")
            elif response.status_code == 404:
                print("❌ Rankings status endpoint not found (404)")
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"❌ Rankings Status Endpoint Error: {e}")
        
        # Test profile endpoints
        try:
            response = await client.get(f"{base_url}/profile/data/universities")
            print(f"🎓 Universities Endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Universities loaded: {len(data.get('universities', []))} universities")
        except Exception as e:
            print(f"❌ Universities Endpoint Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_rankings_endpoints())