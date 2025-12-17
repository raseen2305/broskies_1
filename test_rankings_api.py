#!/usr/bin/env python3
"""
Test the rankings API specifically for Srie06
"""
import requests
import json

def test_rankings_api():
    """Test the rankings API that RankingWidget calls"""
    
    # Use the same token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTNjNGMwMGQ0NDY5YzQ5ZDBhODhhNWIiLCJ1c2VyX2lkIjoiNjkzYzRjMDBkNDQ2OWM0OWQwYTg4YTViIiwiZ2l0aHViX3VzZXJuYW1lIjoiU3JpZTA2IiwicHJlZmVycmVkX3VzZXJuYW1lIjoiU3JpZTA2IiwiZW1haWwiOiJzcmllMDZAZXhhbXBsZS5jb20iLCJleHAiOjE3NjU2OTkyMDAsImlhdCI6MTc2NTYxMjgwMCwidXNlcl90eXBlIjoiZGV2ZWxvcGVyIiwidHlwZSI6ImFjY2VzcyJ9.BNATJ4y3Lw-I4aiD8heszXj-efcOzmjAxpb0MVL4h9U"
    
    API_URL = "http://localhost:8000"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("🏆 Testing /rankings endpoint (what RankingWidget calls)...")
    
    try:
        response = requests.get(f"{API_URL}/rankings", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Rankings API Success!")
            print(f"  - Regional ranking: {data.get('regional') is not None}")
            print(f"  - University ranking: {data.get('university') is not None}")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Rankings API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
                
                # Check specific error conditions that RankingWidget looks for
                if response.status_code == 404:
                    print("🔍 This is a 404 - RankingWidget will think user has no profile")
                elif "Profile not found" in str(error_data):
                    print("🔍 'Profile not found' - RankingWidget will set hasProfile=false")
                elif "not available" in str(error_data) or "scan first" in str(error_data):
                    print("🔍 'Not available' - RankingWidget will start polling")
                    
            except:
                print(response.text)
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_rankings_api()