#!/usr/bin/env python3
"""
Test script to verify database separation between internal and external users
"""

import asyncio
import sys
sys.path.append('.')

from app.db_connection_multi import get_external_users_db, get_raseen_temp_user_db
from datetime import datetime

async def test_database_separation():
    """Test that internal and external users are stored in different databases"""
    
    print("🔍 Testing Database Separation...")
    print("=" * 50)
    
    try:
        # Get both databases
        external_db = await get_external_users_db()
        internal_db = await get_raseen_temp_user_db()
        
        print(f"✅ External DB: {external_db.name}")
        print(f"✅ Internal DB: {internal_db.name}")
        
        # Check external scan cache
        external_scans = await external_db.external_scan_cache.find({}).to_list(length=5)
        print(f"\n🌐 External scan cache entries: {len(external_scans)}")
        
        if external_scans:
            latest_external = external_scans[0]
            print(f"   Latest external scan: {latest_external.get('username')} - {latest_external.get('user_id')}")
            print(f"   Storage location: {latest_external.get('storage_location')}")
            print(f"   User type: {latest_external.get('user_type')}")
        
        # Check internal scan cache
        internal_scans = await internal_db.internal_scan_cache.find({}).to_list(length=5)
        print(f"\n🔐 Internal scan cache entries: {len(internal_scans)}")
        
        if internal_scans:
            latest_internal = internal_scans[0]
            print(f"   Latest internal scan: {latest_internal.get('username')} - {latest_internal.get('user_id')}")
            print(f"   Storage location: {latest_internal.get('storage_location')}")
            print(f"   User type: {latest_internal.get('user_type')}")
        
        # Verify separation
        print(f"\n✅ Database Separation Verification:")
        print(f"   External DB name: {external_db.name}")
        print(f"   Internal DB name: {internal_db.name}")
        print(f"   Databases are separate: {external_db.name != internal_db.name}")
        
        # Check for cross-contamination
        external_internal_data = await external_db.internal_scan_cache.count_documents({})
        internal_external_data = await internal_db.external_scan_cache.count_documents({})
        
        print(f"\n🔍 Cross-contamination check:")
        print(f"   Internal data in external DB: {external_internal_data} (should be 0)")
        print(f"   External data in internal DB: {internal_external_data} (should be 0)")
        
        if external_internal_data == 0 and internal_external_data == 0:
            print("✅ No cross-contamination detected!")
        else:
            print("⚠️ Cross-contamination detected!")
        
    except Exception as e:
        print(f"❌ Error testing database separation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_separation())