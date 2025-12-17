#!/usr/bin/env python3
"""
Create a proper JWT token for frontend testing
"""
import jwt
from datetime import datetime, timedelta

def create_frontend_test_token():
    """Create a JWT token that matches what the frontend expects"""
    # Use the same secret key from backend/.env
    SECRET_KEY = "kJ8mN2pQ9rS5tU7vW0xY3zA6bC9dE2fH5iL8mN1pQ4rS7tU0vW3xY6zA9bC2dE5fH8iL1mN4pQ7r"
    
    # Create a test payload that matches the OAuth response
    payload = {
        "sub": "693c4c00d4469c49d0a88a5b",  # The user_id (using 'sub' as expected by security.py)
        "user_id": "693c4c00d4469c49d0a88a5b",  # Also include user_id for profile endpoints
        "github_username": "Srie06",  # The GitHub username
        "preferred_username": "Srie06",
        "email": "srie06@example.com",
        "exp": datetime.utcnow() + timedelta(hours=24),  # 24 hour expiry
        "iat": datetime.utcnow(),
        "user_type": "developer",
        "type": "access"  # Token type as expected by security.py
    }
    
    # Create the token
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    print("Frontend Test Token:")
    print(token)
    print("\nToken payload:")
    import json
    print(json.dumps(payload, indent=2, default=str))
    
    return token

if __name__ == "__main__":
    create_frontend_test_token()