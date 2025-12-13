#!/usr/bin/env python3
"""
Debug database storage issues
"""

import asyncio
import sys
import os
from datetime import datetime
sys.path.append('.')

# Set environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient

async def test_database_storage():
    """Test if we can store data in both databases"""
    
    print("🔍 Testing Database Storage...")
    print("=" * 50)
    
    try:
        # Test external database storage
        external_url = os.getenv('EXTERNAL_USERS_DB_URL')
        if external_url:
            external_client = AsyncIOMotorClient(external_url)
            external_db = external_client.external_users
            
            print(f"🌐 Testing External Database Storage...")
            
            # Try to insert a test document
            test_doc = {
                'username': 'test_external_user',
                'user_id': 'external_test123',
                'user_type': 'external',
                'storage_location': 'EXTERNAL_DATABASE',
                'scan_date': datetime.utcnow(),
                'test': True
            }
            
            try:
                result = await external_db.external_scan_cache.insert_one(test_doc)
                print(f"   ✅ Successfully inserted document with ID: {result.inserted_id}")
                
                # Verify it was stored
                stored_doc = await external_db.external_scan_cache.find_one({'username': 'test_external_user'})
                if stored_doc:
                    print(f"   ✅ Document verified in database")
                else:
                    print(f"   ❌ Document not found after insertion")
                    
            except Exception as e:
                print(f"   ❌ Failed to insert: {e}")
        
        # Test internal database storage
        internal_url = os.getenv('RASEEN_TEMP_USER_DB_URL')
        if internal_url:
            internal_client = AsyncIOMotorClient(internal_url)
            internal_db = internal_client.raseen_temp_user
            
            print(f"\n🔐 Testing Internal Database Storage...")
            
            # Try to insert a test document
            test_doc = {
                'username': 'test_internal_user',
                'user_id': 'internal_test123',
                'user_type': 'internal',
                'storage_location': 'INTERNAL_DATABASE',
                'scan_date': datetime.utcnow(),
                'test': True
            }
            
            try:
                result = await internal_db.internal_scan_cache.insert_one(test_doc)
                print(f"   ✅ Successfully inserted document with ID: {result.inserted_id}")
                
                # Verify it was stored
                stored_doc = await internal_db.internal_scan_cache.find_one({'username': 'test_internal_user'})
                if stored_doc:
                    print(f"   ✅ Document verified in database")
                else:
                    print(f"   ❌ Document not found after insertion")
                    
            except Exception as e:
                print(f"   ❌ Failed to insert: {e}")
        
        print(f"\n✅ Database storage test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_storage())