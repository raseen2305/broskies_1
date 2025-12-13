"""
Database Index Checker
Checks and documents existing MongoDB indexes
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()


async def check_indexes():
    """Check all indexes in the database"""
    
    # Connect to MongoDB
    mongodb_url = os.getenv('MONGODB_URL')
    database_name = os.getenv('DATABASE_NAME', 'broskieshub')
    
    if not mongodb_url:
        print("❌ MONGODB_URL not found in environment variables")
        return
    
    print(f"🔗 Connecting to MongoDB...")
    print(f"📊 Database: {database_name}\n")
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client[database_name]
    
    # Collections to check
    collections = [
        'users',
        'user_profiles',
        'repositories',
        'evaluations',
        'regional_scores',
        'university_scores',
        'audit_logs'
    ]
    
    print("=" * 80)
    print("DATABASE INDEX REPORT")
    print("=" * 80)
    print()
    
    all_indexes = {}
    
    for collection_name in collections:
        try:
            collection = db[collection_name]
            
            # Check if collection exists
            collection_names = await db.list_collection_names()
            if collection_name not in collection_names:
                print(f"⚠️  Collection '{collection_name}' does not exist")
                print()
                continue
            
            # Get indexes
            indexes = await collection.index_information()
            all_indexes[collection_name] = indexes
            
            print(f"📁 Collection: {collection_name}")
            print("-" * 80)
            
            if not indexes or len(indexes) == 1:  # Only _id_ index
                print("   ⚠️  No custom indexes found (only default _id_ index)")
            else:
                for index_name, index_info in indexes.items():
                    if index_name == '_id_':
                        continue  # Skip default index
                    
                    keys = index_info.get('key', [])
                    unique = index_info.get('unique', False)
                    sparse = index_info.get('sparse', False)
                    
                    # Format keys
                    key_str = ', '.join([f"{k}: {v}" for k, v in keys])
                    
                    print(f"   ✅ {index_name}")
                    print(f"      Keys: {key_str}")
                    if unique:
                        print(f"      Type: UNIQUE")
                    if sparse:
                        print(f"      Type: SPARSE")
                    print()
            
            print()
            
        except Exception as e:
            print(f"❌ Error checking collection '{collection_name}': {e}")
            print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    total_indexes = sum(len(indexes) - 1 for indexes in all_indexes.values())  # -1 for _id_
    print(f"Total collections checked: {len(collections)}")
    print(f"Total custom indexes found: {total_indexes}")
    print()
    
    # Check for required indexes
    print("=" * 80)
    print("REQUIRED INDEXES CHECK")
    print("=" * 80)
    print()
    
    required_indexes = {
        'repositories': [
            ('user_id + category', ['user_id', 'category']),
            ('user_id + analyzed', ['user_id', 'analyzed']),
        ],
        'user_profiles': [
            ('overall_score', ['overall_score']),
            ('user_id', ['user_id']),
        ],
        'regional_scores': [
            ('region + overall_score', ['region', 'overall_score']),
            ('user_id', ['user_id']),
        ],
        'university_scores': [
            ('university + overall_score', ['university', 'overall_score']),
            ('user_id', ['user_id']),
        ],
        'users': [
            ('github_username', ['github_username']),
        ],
        'evaluations': [
            ('user_id', ['user_id']),
            ('repo_id', ['repo_id']),
        ]
    }
    
    missing_indexes = []
    
    for collection_name, required in required_indexes.items():
        if collection_name not in all_indexes:
            print(f"⚠️  Collection '{collection_name}' not found")
            continue
        
        indexes = all_indexes[collection_name]
        
        for index_desc, index_keys in required:
            # Check if index exists
            found = False
            for index_name, index_info in indexes.items():
                keys = [k for k, v in index_info.get('key', [])]
                if keys == index_keys:
                    found = True
                    break
            
            if found:
                print(f"✅ {collection_name}.{index_desc}")
            else:
                print(f"❌ {collection_name}.{index_desc} - MISSING")
                missing_indexes.append((collection_name, index_desc, index_keys))
    
    print()
    
    if missing_indexes:
        print("=" * 80)
        print("MISSING INDEXES")
        print("=" * 80)
        print()
        print("The following indexes should be created:")
        print()
        
        for collection_name, index_desc, index_keys in missing_indexes:
            keys_str = ', '.join([f'("{k}", 1)' for k in index_keys])
            print(f"db.{collection_name}.create_index([{keys_str}])")
        
        print()
    else:
        print("✅ All required indexes are present!")
        print()
    
    # Close connection
    client.close()


if __name__ == '__main__':
    asyncio.run(check_indexes())
