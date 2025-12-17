"""
Migration script to fix existing user_overall_details documents
that are missing required fields
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

async def migrate_user_overall_details():
    """Fix existing user_overall_details documents"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URL") or os.getenv("MONGODB_URI")
    db_name = os.getenv("DATABASE_NAME", "devrank")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    print("=" * 80)
    print("MIGRATING user_overall_details COLLECTION")
    print("=" * 80)
    
    # Find documents missing required fields
    docs_to_fix = []
    async for doc in db.user_overall_details.find():
        needs_fix = False
        fixes = []
        
        if doc.get('repository_count') is None:
            needs_fix = True
            fixes.append('repository_count')
        
        if doc.get('evaluated_repository_count') is None:
            needs_fix = True
            fixes.append('evaluated_repository_count')
        
        if doc.get('scan_type') is None:
            needs_fix = True
            fixes.append('scan_type')
        
        if needs_fix:
            docs_to_fix.append({
                'doc': doc,
                'fixes': fixes
            })
    
    if not docs_to_fix:
        print("\n✅ All documents are properly formatted!")
        print("   No migration needed.")
        client.close()
        return
    
    print(f"\n⚠️  Found {len(docs_to_fix)} document(s) that need fixing:")
    
    for item in docs_to_fix:
        doc = item['doc']
        fixes = item['fixes']
        username = doc.get('github_username', 'Unknown')
        print(f"\n📄 User: {username}")
        print(f"   Missing fields: {', '.join(fixes)}")
    
    # Ask for confirmation
    print("\n" + "=" * 80)
    print("MIGRATION PLAN:")
    print("=" * 80)
    print("\nFor each document, we will:")
    print("1. Set repository_count = 0 (if missing)")
    print("2. Set evaluated_repository_count = 0 (if missing)")
    print("3. Set scan_type = 'internal' (if missing)")
    print("4. Update updated_at to current time")
    print("\nNote: Users should re-scan to get accurate counts.")
    
    response = input("\nProceed with migration? (yes/no): ")
    
    if response.lower() != 'yes':
        print("\n❌ Migration cancelled.")
        client.close()
        return
    
    # Perform migration
    print("\n" + "=" * 80)
    print("PERFORMING MIGRATION:")
    print("=" * 80)
    
    updated_count = 0
    
    for item in docs_to_fix:
        doc = item['doc']
        username = doc.get('github_username', 'Unknown')
        user_id = doc.get('user_id')
        
        # Prepare update
        update_fields = {
            'updated_at': datetime.utcnow()
        }
        
        if doc.get('repository_count') is None:
            update_fields['repository_count'] = 0
        
        if doc.get('evaluated_repository_count') is None:
            update_fields['evaluated_repository_count'] = 0
        
        if doc.get('scan_type') is None:
            update_fields['scan_type'] = 'internal'
        
        # Update document
        result = await db.user_overall_details.update_one(
            {'user_id': user_id},
            {'$set': update_fields}
        )
        
        if result.modified_count > 0:
            print(f"\n✅ Updated: {username}")
            print(f"   Fields updated: {', '.join(update_fields.keys())}")
            updated_count += 1
        else:
            print(f"\n⚠️  Failed to update: {username}")
    
    print("\n" + "=" * 80)
    print("MIGRATION COMPLETE")
    print("=" * 80)
    print(f"\n✅ Successfully updated {updated_count} document(s)")
    
    if updated_count > 0:
        print("\n📝 IMPORTANT:")
        print("   - Users should re-scan to get accurate repository counts")
        print("   - The fix is now in place for future scans")
        print("   - All new scans will populate fields correctly")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_user_overall_details())
