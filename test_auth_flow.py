#!/usr/bin/env python3
"""
Test script to simulate the authentication flow and test dashboard data
"""
import requests
import json
import sys
from datetime import datetime, timedelta
import jwt

API_URL = "http://localhost:8000"

def create_test_token():
    """Create a test JWT token for testing"""
    # Use the same secret key from backend/.env
    SECRET_KEY = "kJ8mN2pQ9rS5tU7vW0xY3zA6bC9dE2fH5iL8mN1pQ4rS7tU0vW3xY6zA9bC2dE5fH8iL1mN4pQ7r"
    
    # Create a test payload
    payload = {
        "sub": "693c4c00d4469c49d0a88a5b",  # The user_id (using 'sub' as expected by security.py)
        "user_id": "693c4c00d4469c49d0a88a5b",  # Also include user_id for profile endpoints
        "github_username": "Srie06",  # The GitHub username
        "preferred_username": "Srie06",
        "email": "srie06@example.com",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "user_type": "developer",
        "type": "access"  # Token type as expected by security.py
    }
    
    # Create the token
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def test_dashboard_data_with_auth():
    """Test the dashboard data endpoint with authentication"""
    
    print("🔍 Testing dashboard data endpoint with authentication...")
    
    # Create a test token
    token = create_test_token()
    print(f"🔑 Created test token: {token[:50]}...")
    
    # Test the dashboard data endpoint
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("\n📊 Testing /profile/dashboard-data...")
        response = requests.get(f"{API_URL}/profile/dashboard-data", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Dashboard data:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Also test profile status
    try:
        print("\n📋 Testing /profile/status...")
        response = requests.get(f"{API_URL}/profile/status", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Profile status:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)
                
    except Exception as e:
        print(f"❌ Profile status request failed: {e}")

if __name__ == "__main__":
    test_dashboard_data_with_auth()