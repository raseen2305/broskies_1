#!/usr/bin/env python3
"""
Create JWT token for the correct user_id: thoshifraseen4
"""
import sys
import os
import requests
import json
from datetime import timedelta

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.security import create_access_token

def create_correct_token():
    # Correct user_id found in database
    user_id = "thoshifraseen4"
    username = "raseen2305"
    
    print(f"🔹 Creating JWT token for correct user_id: {user_id}")
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": user_id, "user_type": "developer", "github_username": username},
        expires_delta=timedelta(hours=24)  # 24 hour token
    )
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"🔸 JWT Token: {access_token}")
    
    # Test debug endpoint
    print(f"\n🔹 Testing debug endpoint with correct user_id...")
    try:
        response = requests.get(
            "http://localhost:8000/debug/rankings/user-data",
            headers=headers
        )
        
        print(f"🔸 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! Found data for user_id: {user_id}")
            print(f"🔸 Internal users count: {data.get('internal_users', {}).get('count', 0)}")
            print(f"🔸 Profile users count: {data.get('profile_users', {}).get('count', 0)}")
            print(f"🔸 Joined data count: {data.get('joined_data', {}).get('count', 0)}")
            print(f"🔸 ID matching: {data.get('id_matching', {}).get('has_match', False)}")
            
            if data.get('diagnosis'):
                print("🔸 Diagnosis:")
                for d in data['diagnosis']:
                    print(f"   {d}")
        else:
            error_data = response.json()
            print(f"❌ Error: {error_data}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test rankings endpoint
    print(f"\n🔹 Testing rankings endpoint...")
    try:
        response = requests.get(
            "http://localhost:8000/rankings",
            headers=headers
        )
        
        print(f"🔸 Rankings Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Rankings SUCCESS!")
            print(f"🔸 Status: {data.get('status')}")
            print(f"🔸 Has Regional: {data.get('regional_ranking') is not None}")
            print(f"🔸 Has University: {data.get('university_ranking') is not None}")
            
            if data.get('regional_ranking'):
                regional = data['regional_ranking']
                print(f"🔸 Regional Rank: #{regional.get('rank_in_region')} of {regional.get('total_users_in_region')}")
                print(f"🔸 Regional Percentile: {regional.get('percentile_region'):.1f}%")
            
            if data.get('university_ranking'):
                university = data['university_ranking']
                print(f"🔸 University Rank: #{university.get('rank_in_university')} of {university.get('total_users_in_university')}")
                print(f"🔸 University Percentile: {university.get('percentile_university'):.1f}%")
                
        else:
            error_data = response.json()
            print(f"❌ Rankings Error: {error_data}")
            
    except Exception as e:
        print(f"❌ Rankings request failed: {e}")
    
    print(f"\n✅ Correct JWT Token for frontend:")
    print(f"localStorage.setItem('auth_token', '{access_token}');")
    
    return access_token

if __name__ == "__main__":
    create_correct_token()