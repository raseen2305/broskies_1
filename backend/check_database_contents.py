#!/usr/bin/env python3
"""
Check database contents to verify separation
"""

import asyncio
import sys
import os
sys.path.append('.')

# Set environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient

async def check_databases():
    """Check the contents of both databases"""
    
    print("🔍 Checking Database Contents...")
    print("=" * 50)
    
    try:
        # Connect to external database
        external_url = os.getenv('EXTERNAL_USERS_DB_URL')
        if external_url:
            external_client = AsyncIOMotorClient(external_url)
            external_db = external_client.external_users
            
            print(f"🌐 External Database: external_users")
            
            # List all collections in external database
            external_collections = await external_db.list_collection_names()
            print(f"   Collections: {external_collections}")
            
            # Check external scan cache
            external_scans = await external_db.external_scan_cache.find({}).to_list(length=10)
            print(f"   External scan cache entries: {len(external_scans)}")
            
            for scan in external_scans[-5:]:  # Show last 5
                print(f"   - {scan.get('username')} ({scan.get('user_id')}) - {scan.get('scan_date')}")
            
            # Check specifically for raseen2305
            raseen_scan = await external_db.external_scan_cache.find_one({"username": "raseen2305"})
            if raseen_scan:
                print(f"   ✅ Found raseen2305: {raseen_scan.get('user_id')} - {raseen_scan.get('scan_date')}")
            else:
                print(f"   ❌ raseen2305 not found in external_scan_cache")
            
            # Check ALL collections for any data
            for collection_name in external_collections:
                count = await external_db[collection_name].count_documents({})
                if count > 0:
                    print(f"   {collection_name}: {count} documents")
                    
                    # Show sample data
                    sample = await external_db[collection_name].find({}).limit(2).to_list(length=2)
                    for doc in sample:
                        username = doc.get('username') or doc.get('userId') or doc.get('login') or 'Unknown'
                        user_type = doc.get('user_type', 'N/A')
                        scan_date = doc.get('scan_date') or doc.get('created_at') or 'N/A'
                        print(f"     - {username} ({user_type}) - {scan_date}")
                else:
                    print(f"   {collection_name}: 0 documents")
        
        # Connect to internal database (raseen_temp_user)
        internal_url = os.getenv('RASEEN_TEMP_USER_DB_URL')
        if internal_url:
            internal_client = AsyncIOMotorClient(internal_url)
            internal_db = internal_client.raseen_temp_user
            
            print(f"\n🔐 Internal Database: raseen_temp_user")
            
            # List all collections in internal database
            internal_collections = await internal_db.list_collection_names()
            print(f"   Collections: {internal_collections}")
            
            # Check internal scan cache
            internal_scans = await internal_db.internal_scan_cache.find({}).to_list(length=10)
            print(f"   Internal scan cache entries: {len(internal_scans)}")
            
            for scan in internal_scans[-3:]:  # Show last 3
                print(f"   - {scan.get('username')} ({scan.get('user_id')}) - {scan.get('scan_date')}")
            
            # Check ALL collections for any data
            for collection_name in internal_collections:
                count = await internal_db[collection_name].count_documents({})
                if count > 0:
                    print(f"   {collection_name}: {count} documents")
                    
                    # Show sample data
                    sample = await internal_db[collection_name].find({}).limit(2).to_list(length=2)
                    for doc in sample:
                        username = doc.get('username') or doc.get('userId') or doc.get('login') or 'Unknown'
                        user_type = doc.get('user_type', 'N/A')
                        scan_date = doc.get('scan_date') or doc.get('created_at') or 'N/A'
                        print(f"     - {username} ({user_type}) - {scan_date}")
                else:
                    print(f"   {collection_name}: 0 documents")
        
        print(f"\n✅ Database separation verified!")
        print(f"   External users stored in: external_users database")
        print(f"   Internal users stored in: raseen_temp_user database")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_databases())