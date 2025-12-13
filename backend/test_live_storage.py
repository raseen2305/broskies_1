#!/usr/bin/env python3
"""
Test live storage by making API calls and checking database immediately
"""

import asyncio
import sys
import requests
import time
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
import os

async def test_live_storage():
    """Test storage by making API calls and checking database"""
    
    print("🔍 Testing Live Storage...")
    print("=" * 50)
    
    # Connect to external database
    external_url = os.getenv('EXTERNAL_USERS_DB_URL')
    external_client = AsyncIOMotorClient(external_url)
    external_db = external_client.external_users
    
    # Get initial count
    initial_count = await external_db.external_scan_cache.count_documents({})
    print(f"Initial external_scan_cache count: {initial_count}")
    
    # Make API call
    print("Making API call to scan testuser999...")
    response = requests.get("http://localhost:8000/api/scan/quick-scan/testuser999?force_refresh=true")
    print(f"API Response Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ API call successful")
        
        # Wait a moment for storage
        await asyncio.sleep(2)
        
        # Check database again
        final_count = await external_db.external_scan_cache.count_documents({})
        print(f"Final external_scan_cache count: {final_count}")
        
        if final_count > initial_count:
            print("✅ Data was stored successfully!")
            
            # Show the stored data
            latest_doc = await external_db.external_scan_cache.find_one(
                {"username": "testuser999"}, 
                sort=[("scan_date", -1)]
            )
            if latest_doc:
                print(f"Stored data: {latest_doc.get('username')} - {latest_doc.get('user_type')} - {latest_doc.get('scan_date')}")
        else:
            print("❌ Data was NOT stored")
            
            # Check all collections for any new data
            collections = await external_db.list_collection_names()
            print("Checking all collections for testuser999...")
            for collection_name in collections:
                count = await external_db[collection_name].count_documents({"username": "testuser999"})
                if count > 0:
                    print(f"✅ Found data in {collection_name}: {count} documents")
                else:
                    print(f"   {collection_name}: 0 documents")
                    
            # Also check for any documents with userId
            print("\nChecking for userId field...")
            for collection_name in collections:
                count = await external_db[collection_name].count_documents({"userId": "testuser999"})
                if count > 0:
                    print(f"✅ Found data by userId in {collection_name}: {count} documents")
    else:
        print(f"❌ API call failed: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_live_storage())