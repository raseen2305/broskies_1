import sys
import os
import requests
import json
from datetime import timedelta

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.security import create_access_token

def debug_profile_setup():
    # User ID found in previous steps (Deep Analysis success)
    user_id = "693affe4683ac9712ab6940a"
    username = "raseen2305"
    
    print(f"🔹 Creating token for user_id: {user_id}")
    
    # Create token payload matching what get_current_user_token expects
    access_token = create_access_token(
        data={"sub": user_id, "user_type": "developer", "github_username": username},
        expires_delta=timedelta(minutes=30)
    )
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "full_name": "Raseen Test",
        "email": "raseen@example.com",
        "university": "Test University",
        "graduation_year": 2025,
        "course": "Computer Science",
        "nationality": "India",
        "state": "Kerala",
        "district": "Kozhikode",
        "linkedin_url": "https://linkedin.com/in/raseen",
        "github_username": username
    }
    
    print("🔹 Sending POST /profile/setup request...")
    try:
        response = requests.post(
            "http://localhost:8000/profile/setup",
            headers=headers,
            json=payload
        )
        
        print(f"🔸 Status Code: {response.status_code}")
        try:
            print(f"🔸 Response: {response.json()}")
        except:
            print(f"🔸 Response Text: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    debug_profile_setup()
