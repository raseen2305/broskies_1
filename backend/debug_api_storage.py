#!/usr/bin/env python3
"""
Debug API storage flow
"""

import asyncio
import sys
sys.path.append('.')

from app.user_type_detector import UserTypeDetector
from app.db_connection_multi import get_external_users_db, get_raseen_temp_user_db
from datetime import datetime
from fastapi import Request
from unittest.mock import Mock

async def test_api_storage_flow():
    """Test the exact storage flow used by the API"""
    
    print("🔍 Testing API Storage Flow...")
    print("=" * 50)
    
    try:
        # Simulate external user request
        print("🌐 Testing External User Flow...")
        
        # Mock request object (no authentication)
        mock_request = Mock()
        mock_request.headers = {}
        
        # Get routing info like the API does
        routing_info = await UserTypeDetector.route_user_operation(mock_request, "srie06", "quick_scan")
        
        print(f"   User Type: {routing_info['user_type']}")
        print(f"   User ID: {routing_info['user_id']}")
        print(f"   Storage Location: {routing_info['storage_location']}")
        print(f"   Scan Collection: {routing_info['scan_collection']}")
        
        # Get database like the API does
        database = routing_info['database']
        scan_collection = routing_info['scan_collection']
        
        # Try to store data like the API does
        cache_data = {
            'username': 'srie06',
            'user_id': routing_info['user_id'],
            'user_type': routing_info['user_type'],
            'storage_location': routing_info['storage_location'],
            'scan_date': datetime.utcnow(),
            'test_api_flow': True
        }
        
        try:
            result = await database[scan_collection].insert_one(cache_data)
            print(f"   ✅ API flow storage successful: {result.inserted_id}")
        except Exception as storage_error:
            print(f"   ❌ API flow storage failed: {storage_error}")
        
        # Test internal user flow (would need authentication in real API)
        print(f"\n🔐 Testing Internal User Flow (simulated)...")
        
        # For internal users, we'd need a real authenticated request
        # But we can test the database connection
        internal_db = await get_raseen_temp_user_db()
        
        cache_data_internal = {
            'username': 'raseen2305',
            'user_id': 'internal_raseen2305',
            'user_type': 'internal',
            'storage_location': 'INTERNAL_DATABASE',
            'scan_date': datetime.utcnow(),
            'test_api_flow': True
        }
        
        try:
            result = await internal_db.internal_scan_cache.insert_one(cache_data_internal)
            print(f"   ✅ Internal API flow storage successful: {result.inserted_id}")
        except Exception as storage_error:
            print(f"   ❌ Internal API flow storage failed: {storage_error}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_storage_flow())