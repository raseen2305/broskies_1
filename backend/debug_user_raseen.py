#!/usr/bin/env python3
"""
Debug script to create JWT token and test user data for raseen2305
"""
import sys
import os
import requests
import json
from datetime import timedelta

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.security import create_access_token

def debug_user_raseen():
    # Try different user_id formats that might exist for raseen2305
    possible_user_ids = [
        "raseen2305",  # Username as user_id
        "693adb52388fdecda6b1b4f5",  # ObjectId from profile data
        "693affe4683ac9712ab6940a"   # ObjectId from previous debug
    ]
    
    username = "raseen2305"
    
    for user_id in possible_user_ids:
        print(f"\n🔹 Testing user_id: {user_id}")
        
        # Create JWT token
        access_token = create_access_token(
            data={"sub": user_id, "user_type": "developer", "github_username": username},
            expires_delta=timedelta(minutes=30)
        )
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        print(f"🔸 JWT Token: {access_token[:50]}...")
        
        # Test debug endpoint
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
                
                # If this user_id works, test rankings endpoint
                print(f"\n🔹 Testing rankings endpoint with user_id: {user_id}")
                rankings_response = requests.get(
                    "http://localhost:8000/rankings",
                    headers=headers
                )
                print(f"🔸 Rankings Status Code: {rankings_response.status_code}")
                if rankings_response.status_code == 200:
                    rankings_data = rankings_response.json()
                    print(f"🔸 Rankings Status: {rankings_data.get('status')}")
                    print(f"🔸 Has Regional: {rankings_data.get('regional_ranking') is not None}")
                    print(f"🔸 Has University: {rankings_data.get('university_ranking') is not None}")
                else:
                    try:
                        error_data = rankings_response.json()
                        print(f"🔸 Rankings Error: {error_data}")
                    except:
                        print(f"🔸 Rankings Error Text: {rankings_response.text}")
                
                return user_id, access_token  # Return successful user_id and token
                
            else:
                try:
                    error_data = response.json()
                    print(f"❌ Error: {error_data}")
                except:
                    print(f"❌ Error Text: {response.text}")
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    print(f"\n❌ No working user_id found for {username}")
    return None, None

if __name__ == "__main__":
    user_id, token = debug_user_raseen()
    if user_id and token:
        print(f"\n✅ Working configuration found:")
        print(f"User ID: {user_id}")
        print(f"JWT Token: {token}")
        print(f"\nTo use in frontend, set localStorage:")
        print(f"localStorage.setItem('auth_token', '{token}');")