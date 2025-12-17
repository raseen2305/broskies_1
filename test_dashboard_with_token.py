#!/usr/bin/env python3
"""
Test dashboard data endpoint with the proper frontend token
"""
import requests
import json

def test_dashboard_with_frontend_token():
    """Test the dashboard data endpoint with the frontend token"""
    
    # Use the token we just generated
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTNjNGMwMGQ0NDY5YzQ5ZDBhODhhNWIiLCJ1c2VyX2lkIjoiNjkzYzRjMDBkNDQ2OWM0OWQwYTg4YTViIiwiZ2l0aHViX3VzZXJuYW1lIjoiU3JpZTA2IiwicHJlZmVycmVkX3VzZXJuYW1lIjoiU3JpZTA2IiwiZW1haWwiOiJzcmllMDZAZXhhbXBsZS5jb20iLCJleHAiOjE3NjU2OTkyMDAsImlhdCI6MTc2NTYxMjgwMCwidXNlcl90eXBlIjoiZGV2ZWxvcGVyIiwidHlwZSI6ImFjY2VzcyJ9.BNATJ4y3Lw-I4aiD8heszXj-efcOzmjAxpb0MVL4h9U"
    
    API_URL = "http://localhost:8000"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Testing dashboard data endpoint with frontend token...")
    
    try:
        response = requests.get(f"{API_URL}/profile/dashboard-data", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Dashboard data summary:")
            print(f"  - Has data: {data.get('has_data')}")
            print(f"  - Overall Score: {data.get('overallScore')}")
            print(f"  - Repository Count: {data.get('repositoryCount')}")
            print(f"  - Target Username: {data.get('targetUsername')}")
            print(f"  - Profile Completed: {data.get('profile', {}).get('completed')}")
            print(f"  - Rankings Available: {data.get('rankings', {}).get('available')}")
            print(f"  - Evaluated Count: {data.get('evaluatedCount')}")
            print(f"  - Analyzed: {data.get('analyzed')}")
            
            # This is the key data that should be passed to setScanResults()
            print("\n📊 This data should be passed to setScanResults() in the frontend")
            
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_dashboard_with_frontend_token()