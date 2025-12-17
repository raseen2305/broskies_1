#!/usr/bin/env python3
"""
Clear All Collections Script
Deletes all data from all collections in the multi-database architecture
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def clear_all_databases():
    """Delete all data from all collections in all databases"""
    
    # Import the new multi-database system
    from app.db_connection_multi import (
        get_external_users_db, get_raseen_temp_user_db, get_raseen_main_user_db,
        get_raseen_main_hr_db, get_srie_main_user_db, get_srie_main_hr_db,
        DatabaseType
    )
    
    print(f"🔗 Connecting to Multi-Database Architecture...")
    print()
    
    # Database functions mapping
    db_functions = {
        'external_users': get_external_users_db,
        'raseen_temp_user': get_raseen_temp_user_db,
        'raseen_main_user': get_raseen_main_user_db,
        'raseen_main_hr': get_raseen_main_hr_db,
        'srie_main_user': get_srie_main_user_db,
        'srie_main_hr': get_srie_main_hr_db
    }
    
    try:
        # Get all databases and their collections
        all_collections = {}
        total_documents = 0
        
        for db_name, db_func in db_functions.items():
            try:
                db = await db_func()
                if db is None:
                    print(f"⚠️  Could not connect to {db_name}")
                    continue
                
                collection_names = await db.list_collection_names()
                if collection_names:
                    collections_info = {}
                    for coll_name in collection_names:
                        count = await db[coll_name].count_documents({})
                        collections_info[coll_name] = count
                        total_documents += count
                    all_collections[db_name] = collections_info
                    
            except Exception as e:
                print(f"❌ Error accessing {db_name}: {e}")
        
        if not all_collections:
            print(f"ℹ️  No collections found in any database")
            return
        
        print(f"📊 Found collections across {len(all_collections)} databases:")
        print()
        
        for db_name, collections in all_collections.items():
            print(f"  🗄️  {db_name}:")
            for coll_name, count in collections.items():
                print(f"     - {coll_name}: {count:,} documents")
            print()
        
        print(f"📈 Total: {total_documents:,} documents across all databases")
        print()
        
        # Confirm deletion
        print(f"⚠️  WARNING: This will DELETE ALL DATA from ALL collections in ALL databases!")
        print(f"⚠️  Databases: {len(all_collections)}")
        print(f"⚠️  Total Documents: {total_documents:,}")
        print()
        
        confirmation = input("Type 'DELETE ALL DATABASES' to confirm: ")
        
        if confirmation != 'DELETE ALL DATABASES':
            print(f"❌ Deletion cancelled")
            return
        
        print()
        print(f"🗑️  Starting deletion across all databases...")
        print()
        
        # Delete all documents from each collection in each database
        total_deleted = 0
        
        for db_name, collections in all_collections.items():
            print(f"  🗄️  Clearing {db_name}...")
            
            try:
                db = await db_functions[db_name]()
                if db is None:
                    print(f"     ❌ Could not reconnect to {db_name}")
                    continue
                
                for collection_name in collections.keys():
                    try:
                        result = await db[collection_name].delete_many({})
                        deleted_count = result.deleted_count
                        total_deleted += deleted_count
                        print(f"     ✅ {collection_name}: Deleted {deleted_count:,} documents")
                    except Exception as e:
                        print(f"     ❌ {collection_name}: Error - {e}")
                        
            except Exception as e:
                print(f"     ❌ Database {db_name}: Error - {e}")
            
            print()
        
        print(f"✅ Deletion complete!")
        print(f"   Total documents deleted: {total_deleted:,}")
        print(f"   Databases processed: {len(all_collections)}")
        print()
        
        # Verify deletion
        print(f"🔍 Verifying deletion...")
        for db_name, collections in all_collections.items():
            try:
                db = await db_functions[db_name]()
                if db is None:
                    continue
                    
                for collection_name in collections.keys():
                    count = await db[collection_name].count_documents({})
                    if count == 0:
                        print(f"   ✅ {db_name}.{collection_name}: 0 documents (verified)")
                    else:
                        print(f"   ⚠️  {db_name}.{collection_name}: {count} documents remaining")
            except Exception as e:
                print(f"   ❌ {db_name}: Verification error - {e}")
        
        print()
        print(f"✅ All databases cleared successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def clear_specific_database(database_name: str):
    """Delete all data from collections in a specific database"""
    
    from app.db_connection_multi import (
        get_external_users_db, get_raseen_temp_user_db, get_raseen_main_user_db,
        get_raseen_main_hr_db, get_srie_main_user_db, get_srie_main_hr_db
    )
    
    # Database functions mapping
    db_functions = {
        'external_users': get_external_users_db,
        'raseen_temp_user': get_raseen_temp_user_db,
        'raseen_main_user': get_raseen_main_user_db,
        'raseen_main_hr': get_raseen_main_hr_db,
        'srie_main_user': get_srie_main_user_db,
        'srie_main_hr': get_srie_main_hr_db
    }
    
    if database_name not in db_functions:
        print(f"❌ Unknown database: {database_name}")
        print(f"Available databases: {', '.join(db_functions.keys())}")
        return
    
    print(f"🔗 Connecting to {database_name} database...")
    print()
    
    try:
        db = await db_functions[database_name]()
        if db is None:
            print(f"❌ Could not connect to {database_name}")
            return
        
        # Get all collection names
        collection_names = await db.list_collection_names()
        
        if not collection_names:
            print(f"ℹ️  No collections found in database '{database_name}'")
            return
        
        print(f"📊 Collections in '{database_name}':")
        total_documents = 0
        for name in collection_names:
            count = await db[name].count_documents({})
            total_documents += count
            print(f"   - {name}: {count:,} documents")
        print()
        print(f"Total: {total_documents:,} documents")
        print()
        
        # Confirm deletion
        print(f"⚠️  WARNING: This will DELETE ALL DATA from '{database_name}' database!")
        print(f"⚠️  Collections: {len(collection_names)}")
        print(f"⚠️  Documents: {total_documents:,}")
        print()
        
        confirmation = input(f"Type 'DELETE {database_name.upper()}' to confirm: ")
        
        if confirmation != f'DELETE {database_name.upper()}':
            print(f"❌ Deletion cancelled")
            return
        
        print()
        print(f"🗑️  Starting deletion from {database_name}...")
        print()
        
        # Delete all documents from each collection
        total_deleted = 0
        for collection_name in collection_names:
            try:
                result = await db[collection_name].delete_many({})
                deleted_count = result.deleted_count
                total_deleted += deleted_count
                print(f"   ✅ {collection_name}: Deleted {deleted_count:,} documents")
            except Exception as e:
                print(f"   ❌ {collection_name}: Error - {e}")
        
        print()
        print(f"✅ Deletion complete!")
        print(f"   Total documents deleted: {total_deleted:,}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def list_all_databases():
    """List all databases and their collections with document counts"""
    
    from app.db_connection_multi import (
        get_external_users_db, get_raseen_temp_user_db, get_raseen_main_user_db,
        get_raseen_main_hr_db, get_srie_main_user_db, get_srie_main_hr_db
    )
    
    print(f"🔗 Connecting to Multi-Database Architecture...")
    print()
    
    # Database functions mapping
    db_functions = {
        'external_users': get_external_users_db,
        'raseen_temp_user': get_raseen_temp_user_db,
        'raseen_main_user': get_raseen_main_user_db,
        'raseen_main_hr': get_raseen_main_hr_db,
        'srie_main_user': get_srie_main_user_db,
        'srie_main_hr': get_srie_main_hr_db
    }
    
    try:
        total_documents = 0
        total_collections = 0
        
        for db_name, db_func in db_functions.items():
            try:
                db = await db_func()
                if db is None:
                    print(f"❌ {db_name}: Could not connect")
                    continue
                
                collection_names = await db.list_collection_names()
                
                if not collection_names:
                    print(f"🗄️  {db_name}: No collections")
                    continue
                
                print(f"🗄️  {db_name}:")
                db_total = 0
                
                for name in sorted(collection_names):
                    count = await db[name].count_documents({})
                    db_total += count
                    print(f"     {name:35} {count:>10,} documents")
                
                print(f"     {'SUBTOTAL':35} {db_total:>10,} documents")
                print()
                
                total_documents += db_total
                total_collections += len(collection_names)
                
            except Exception as e:
                print(f"❌ {db_name}: Error - {e}")
                print()
        
        print(f"📊 SUMMARY:")
        print(f"   Total Databases:     {len(db_functions)}")
        print(f"   Total Collections:   {total_collections:,}")
        print(f"   Total Documents:     {total_documents:,}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def print_usage():
    """Print usage instructions"""
    print()
    print("Multi-Database Collection Cleaner")
    print("=" * 60)
    print()
    print("Usage:")
    print("  python clear_all_collections.py [command] [options]")
    print()
    print("Commands:")
    print("  all                    - Clear ALL collections in ALL databases")
    print("  list                   - List all databases and collections")
    print("  database <name>        - Clear specific database")
    print()
    print("Examples:")
    print("  python clear_all_collections.py all")
    print("  python clear_all_collections.py list")
    print("  python clear_all_collections.py database external_users")
    print()
    print("Available Databases:")
    print("  - external_users       - External user data")
    print("  - raseen_temp_user     - Temporary internal user data")
    print("  - raseen_main_user     - Main internal user data")
    print("  - raseen_main_hr       - HR data")
    print("  - srie_main_user       - Backup user data")
    print("  - srie_main_hr         - Backup HR data")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "all":
        asyncio.run(clear_all_databases())
    elif command == "list":
        asyncio.run(list_all_databases())
    elif command == "database":
        if len(sys.argv) < 3:
            print("❌ Error: Please specify database name")
            print("   Example: python clear_all_collections.py database external_users")
            sys.exit(1)
        
        database_name = sys.argv[2]
        asyncio.run(clear_specific_database(database_name))
    else:
        print(f"❌ Unknown command: {command}")
        print_usage()
        sys.exit(1)