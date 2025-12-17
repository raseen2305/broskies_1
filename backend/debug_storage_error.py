#!/usr/bin/env python3
"""
Debug the exact storage error by reproducing the API logic
"""

import asyncio
import sys
from datetime import datetime
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

from app.user_type_detector import UserTypeDetector
from fastapi import Request
from unittest.mock import Mock

async def debug_storage_error():
    """Debug the storage error by reproducing the exact API flow"""
    
    print("🔍 Debugging Storage Error...")
    print("=" * 50)
    
    try:
        # Mock request object (no authentication) - exactly like the API
        mock_request = Mock()
        mock_request.headers = {}
        
        username = "srie06"
        
        # Get routing info exactly like the API does
        print(f"Getting routing info for {username}...")
        routing_info = await UserTypeDetector.route_user_operation(mock_request, username, "quick_scan")
        
        user_type = routing_info["user_type"]
        user_id = routing_info["user_id"]
        database = routing_info["database"]
        scan_collection = routing_info["scan_collection"]
        storage_location = routing_info["storage_location"]
        
        print(f"✅ Routing successful:")
        print(f"   User Type: {user_type}")
        print(f"   User ID: {user_id}")
        print(f"   Storage Location: {storage_location}")
        print(f"   Collection: {scan_collection}")
        print(f"   Database: {database}")
        
        # Create cache data exactly like the API does
        current_time = datetime.utcnow()
        
        # Simulate scan result (minimal)
        scan_result = {
            'userId': username,
            'username': username,
            'name': 'Test User',
            'repositories': [],
            'scanDate': current_time.isoformat(),
            'processingTime': 1.0
        }
        
        cache_data = {
            'scan_id': f"{user_id}_{int(current_time.timestamp())}",  # Unique scan ID
            'username': username,
            'user_id': user_id,
            'user_type': user_type,
            'storage_location': storage_location,
            'scan_date': current_time,
            **scan_result
        }
        
        print(f"\n💾 Attempting to store data...")
        print(f"   Collection: {scan_collection}")
        print(f"   Data keys: {list(cache_data.keys())}")
        
        # Try to store exactly like the API does
        try:
            result = await database[scan_collection].insert_one(cache_data)
            print(f"✅ Storage successful! Document ID: {result.inserted_id}")
        except Exception as storage_error:
            print(f"❌ Storage failed: {storage_error}")
            print(f"   Error type: {type(storage_error)}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error in debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_storage_error())