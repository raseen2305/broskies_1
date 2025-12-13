"""
Database Index Creator
Creates required MongoDB indexes for optimal performance
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


async def create_indexes():
    """Create all required indexes"""
    
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
    
    print("=" * 80)
    print("CREATING DATABASE INDEXES")
    print("=" * 80)
    print()
    
    # Define indexes to create
    indexes_to_create = [
        # Internal Users collection
        {
            'collection': 'internal_users',
            'indexes': [
                {
                    'name': 'username_unique',
                    'keys': [('username', 1)],
                    'unique': True
                },
                {
                    'name': 'user_id_unique',
                    'keys': [('user_id', 1)],
                    'unique': True
                },
                {
                    'name': 'email',
                    'keys': [('email', 1)]
                },
                {
                    'name': 'overall_score',
                    'keys': [('overall_score', -1)]  # Descending for rankings
                },
                {
                    'name': 'deep_analysis_complete',
                    'keys': [('deepAnalysisComplete', 1)]
                }
            ]
        },
        
        # External Users collection
        {
            'collection': 'external_users',
            'indexes': [
                {
                    'name': 'username_unique',
                    'keys': [('username', 1)],
                    'unique': True
                },
                {
                    'name': 'user_id_unique',
                    'keys': [('user_id', 1)],
                    'unique': True
                },
                {
                    'name': 'overall_score',
                    'keys': [('overall_score', -1)]  # Descending for rankings
                },
                {
                    'name': 'deep_analysis_complete',
                    'keys': [('deepAnalysisComplete', 1)]
                }
            ]
        },
        

        
        # Repositories collection
        {
            'collection': 'repositories',
            'indexes': [
                {
                    'name': 'user_id',
                    'keys': [('user_id', 1)]
                },
                {
                    'name': 'user_id_category',
                    'keys': [('user_id', 1), ('category', 1)]
                },
                {
                    'name': 'user_id_analyzed',
                    'keys': [('user_id', 1), ('analyzed', 1)]
                },
                {
                    'name': 'user_id_importance_score',
                    'keys': [('user_id', 1), ('importance_score', -1)]
                },
                {
                    'name': 'category_importance_score',
                    'keys': [('category', 1), ('importance_score', -1)]
                },
                {
                    'name': 'full_name',
                    'keys': [('full_name', 1)]
                }
            ]
        },
        
        # Evaluations collection
        {
            'collection': 'evaluations',
            'indexes': [
                {
                    'name': 'user_id',
                    'keys': [('user_id', 1)]
                },
                {
                    'name': 'repo_id',
                    'keys': [('repo_id', 1)]
                },
                {
                    'name': 'user_id_created_at',
                    'keys': [('user_id', 1), ('created_at', -1)]
                }
            ]
        },
        
        # Regional scores collection
        {
            'collection': 'regional_scores',
            'indexes': [
                {
                    'name': 'user_id',
                    'keys': [('user_id', 1)],
                    'unique': True
                },
                {
                    'name': 'region_overall_score',
                    'keys': [('region', 1), ('overall_score', -1)]
                },
                {
                    'name': 'state_overall_score',
                    'keys': [('state', 1), ('overall_score', -1)]
                },
                {
                    'name': 'district_overall_score',
                    'keys': [('district', 1), ('overall_score', -1)]
                },
                {
                    'name': 'github_username',
                    'keys': [('github_username', 1)]
                }
            ]
        },
        
        # University scores collection
        {
            'collection': 'university_scores',
            'indexes': [
                {
                    'name': 'user_id',
                    'keys': [('user_id', 1)],
                    'unique': True
                },
                {
                    'name': 'university_overall_score',
                    'keys': [('university', 1), ('overall_score', -1)]
                },
                {
                    'name': 'university_short_overall_score',
                    'keys': [('university_short', 1), ('overall_score', -1)]
                },
                {
                    'name': 'github_username',
                    'keys': [('github_username', 1)]
                }
            ]
        },
        
        # Audit logs collection
        {
            'collection': 'audit_logs',
            'indexes': [
                {
                    'name': 'user_id_timestamp',
                    'keys': [('user_id', 1), ('timestamp', -1)]
                },
                {
                    'name': 'operation_timestamp',
                    'keys': [('operation', 1), ('timestamp', -1)]
                },
                {
                    'name': 'resource_type_resource_id',
                    'keys': [('resource_type', 1), ('resource_id', 1)]
                },
                {
                    'name': 'timestamp',
                    'keys': [('timestamp', -1)]
                }
            ]
        }
    ]
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    for collection_config in indexes_to_create:
        collection_name = collection_config['collection']
        collection = db[collection_name]
        
        print(f"📁 Collection: {collection_name}")
        print("-" * 80)
        
        for index_config in collection_config['indexes']:
            index_name = index_config['name']
            keys = index_config['keys']
            unique = index_config.get('unique', False)
            sparse = index_config.get('sparse', False)
            
            try:
                # Check if index already exists
                existing_indexes = await collection.index_information()
                
                if index_name in existing_indexes:
                    print(f"   ⏭️  {index_name} - Already exists")
                    skipped_count += 1
                    continue
                
                # Create index
                kwargs = {}
                if unique:
                    kwargs['unique'] = True
                if sparse:
                    kwargs['sparse'] = True
                
                await collection.create_index(keys, name=index_name, **kwargs)
                
                # Format keys for display
                keys_str = ', '.join([f"{k}: {v}" for k, v in keys])
                
                print(f"   ✅ {index_name} - Created")
                print(f"      Keys: {keys_str}")
                if unique:
                    print(f"      Type: UNIQUE")
                if sparse:
                    print(f"      Type: SPARSE")
                
                created_count += 1
                
            except Exception as e:
                print(f"   ❌ {index_name} - Error: {e}")
                error_count += 1
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"✅ Indexes created: {created_count}")
    print(f"⏭️  Indexes skipped (already exist): {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print()
    
    if error_count == 0:
        print("🎉 All indexes created successfully!")
    else:
        print("⚠️  Some indexes failed to create. Check errors above.")
    
    print()
    
    # Close connection
    client.close()


if __name__ == '__main__':
    asyncio.run(create_indexes())
