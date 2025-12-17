#!/usr/bin/env python3
"""
BroskiesHub Backend Cache Viewer
Shows all cached data from MongoDB and other backend storage
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}\n")

def print_section(text: str):
    """Print formatted section"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'─'*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.GREEN}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'─'*80}{Colors.ENDC}")

def print_info(label: str, value: Any):
    """Print formatted info"""
    print(f"{Colors.CYAN}{label}:{Colors.ENDC} {value}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def format_size(size_bytes: int) -> str:
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def format_timestamp(timestamp) -> str:
    """Format timestamp to readable string"""
    if isinstance(timestamp, datetime):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return str(timestamp)

def get_age(timestamp) -> str:
    """Get age of timestamp"""
    if not isinstance(timestamp, datetime):
        return "Unknown"
    
    age = datetime.utcnow() - timestamp
    
    if age.days > 365:
        years = age.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif age.days > 30:
        months = age.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif age.days > 0:
        return f"{age.days} day{'s' if age.days > 1 else ''} ago"
    elif age.seconds > 3600:
        hours = age.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif age.seconds > 60:
        minutes = age.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return f"{age.seconds} second{'s' if age.seconds > 1 else ''} ago"

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB objects"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class CacheViewer:
    def __init__(self):
        self.mongo_client = None
        self.db = None
        self.stats = {
            'total_collections': 0,
            'total_documents': 0,
            'total_size': 0,
            'collections': {}
        }
    
    def connect_mongodb(self) -> bool:
        """Connect to MongoDB"""
        try:
            print_info("Connecting to", "MongoDB Atlas...")
            
            # Try to get connection string from environment
            mongo_uri = os.getenv('MONGODB_URI') or os.getenv('MONGO_URI')
            
            if not mongo_uri:
                # Fallback to hardcoded (from your files)
                mongo_uri = "mongodb+srv://thoshifraseen4_db_user:iojkJvAoEhBOLbmM@online-evaluation.lkxqo8m.mongodb.net/?appName=online-evaluation"
            
            self.mongo_client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            self.mongo_client.server_info()
            
            # Get database name from env or use default
            db_name = os.getenv('MONGODB_DB_NAME', 'github_evaluation')
            self.db = self.mongo_client[db_name]
            
            print_success(f"Connected to MongoDB: {db_name}")
            return True
            
        except Exception as e:
            print_error(f"MongoDB connection failed: {e}")
            return False
    
    def get_collection_stats(self, collection_name: str) -> Dict:
        """Get statistics for a collection"""
        try:
            collection = self.db[collection_name]
            count = collection.count_documents({})
            
            # Get collection size
            stats = self.db.command("collStats", collection_name)
            size = stats.get('size', 0)
            
            # Get sample document
            sample = collection.find_one()
            
            # Get recent documents
            recent = list(collection.find().sort('_id', -1).limit(5))
            
            return {
                'count': count,
                'size': size,
                'sample': sample,
                'recent': recent
            }
        except Exception as e:
            print_warning(f"Could not get stats for {collection_name}: {e}")
            return {'count': 0, 'size': 0, 'sample': None, 'recent': []}
    
    def show_mongodb_cache(self):
        """Show all MongoDB cached data"""
        print_header("📊 MongoDB Cache Data")
        
        if not self.connect_mongodb():
            return
        
        try:
            # Get all collections
            collections = self.db.list_collection_names()
            
            print_info("Database", self.db.name)
            print_info("Collections", len(collections))
            print()
            
            total_docs = 0
            total_size = 0
            
            # Analyze each collection
            for collection_name in collections:
                stats = self.get_collection_stats(collection_name)
                
                total_docs += stats['count']
                total_size += stats['size']
                
                self.stats['collections'][collection_name] = stats
                
                print_section(f"📁 Collection: {collection_name}")
                print_info("  Documents", f"{stats['count']:,}")
                print_info("  Size", format_size(stats['size']))
                
                # Show sample document structure
                if stats['sample']:
                    print_info("  Sample Keys", list(stats['sample'].keys()))
                    
                    # Show creation time if available
                    if '_id' in stats['sample']:
                        created = stats['sample']['_id'].generation_time
                        print_info("  Oldest Doc", f"{format_timestamp(created)} ({get_age(created)})")
                
                # Show recent documents
                if stats['recent']:
                    print(f"\n  {Colors.BOLD}Recent Documents:{Colors.ENDC}")
                    for i, doc in enumerate(stats['recent'][:3], 1):
                        doc_id = doc.get('_id', 'N/A')
                        created = doc_id.generation_time if isinstance(doc_id, ObjectId) else None
                        
                        # Try to get meaningful info
                        info = []
                        if 'username' in doc:
                            info.append(f"user: {doc['username']}")
                        if 'github_username' in doc:
                            info.append(f"github: {doc['github_username']}")
                        if 'email' in doc:
                            info.append(f"email: {doc['email']}")
                        if 'repository_name' in doc:
                            info.append(f"repo: {doc['repository_name']}")
                        if 'overall_score' in doc:
                            info.append(f"score: {doc['overall_score']}")
                        
                        info_str = ", ".join(info) if info else "..."
                        age_str = f"({get_age(created)})" if created else ""
                        
                        print(f"    {i}. {doc_id} - {info_str} {age_str}")
                
                print()
            
            # Summary
            self.stats['total_collections'] = len(collections)
            self.stats['total_documents'] = total_docs
            self.stats['total_size'] = total_size
            
            print_section("📈 Summary Statistics")
            print_info("Total Collections", self.stats['total_collections'])
            print_info("Total Documents", f"{self.stats['total_documents']:,}")
            print_info("Total Size", format_size(self.stats['total_size']))
            
        except Exception as e:
            print_error(f"Error reading MongoDB cache: {e}")
    
    def show_user_cache(self):
        """Show cached user data"""
        print_header("👤 User Cache Data")
        
        if self.db is None:
            print_warning("Not connected to database")
            return
        
        try:
            users = self.db['users']
            total_users = users.count_documents({})
            
            print_info("Total Users", total_users)
            
            # Get recent users
            recent_users = list(users.find().sort('_id', -1).limit(10))
            
            print(f"\n{Colors.BOLD}Recent Users:{Colors.ENDC}")
            for i, user in enumerate(recent_users, 1):
                username = user.get('username', 'N/A')
                github = user.get('github_username', 'N/A')
                email = user.get('email', 'N/A')
                created = user['_id'].generation_time if '_id' in user else None
                
                print(f"  {i}. {username} (GitHub: {github})")
                print(f"     Email: {email}")
                if created:
                    print(f"     Created: {format_timestamp(created)} ({get_age(created)})")
                print()
            
        except Exception as e:
            print_error(f"Error reading user cache: {e}")
    
    def show_scan_cache(self):
        """Show cached scan results"""
        print_header("🔍 Scan Results Cache")
        
        if self.db is None:
            print_warning("Not connected to database")
            return
        
        try:
            # Check for scan results collections
            scan_collections = [
                'scan_results',
                'repository_evaluations',
                'user_scans',
                'analysis_results'
            ]
            
            for coll_name in scan_collections:
                if coll_name in self.db.list_collection_names():
                    collection = self.db[coll_name]
                    count = collection.count_documents({})
                    
                    if count > 0:
                        print_section(f"📊 {coll_name}")
                        print_info("Total Scans", count)
                        
                        # Get recent scans
                        recent = list(collection.find().sort('_id', -1).limit(5))
                        
                        print(f"\n{Colors.BOLD}Recent Scans:{Colors.ENDC}")
                        for i, scan in enumerate(recent, 1):
                            scan_id = scan.get('_id', 'N/A')
                            username = scan.get('username') or scan.get('github_username', 'N/A')
                            repo_count = len(scan.get('repositories', []))
                            score = scan.get('overall_score') or scan.get('overallScore', 'N/A')
                            created = scan_id.generation_time if isinstance(scan_id, ObjectId) else None
                            
                            print(f"  {i}. User: {username}")
                            print(f"     Repos: {repo_count}, Score: {score}")
                            if created:
                                print(f"     Scanned: {format_timestamp(created)} ({get_age(created)})")
                            print()
            
        except Exception as e:
            print_error(f"Error reading scan cache: {e}")
    
    def export_cache_data(self, output_file: str = "cache_export.json"):
        """Export all cache data to JSON file"""
        print_header("💾 Exporting Cache Data")
        
        try:
            export_data = {
                'exported_at': datetime.utcnow().isoformat(),
                'stats': self.stats,
                'collections': {}
            }
            
            if self.db:
                for coll_name in self.db.list_collection_names():
                    collection = self.db[coll_name]
                    documents = list(collection.find().limit(100))  # Limit to 100 per collection
                    export_data['collections'][coll_name] = documents
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2, cls=JSONEncoder)
            
            file_size = os.path.getsize(output_file)
            print_success(f"Exported to {output_file} ({format_size(file_size)})")
            
        except Exception as e:
            print_error(f"Export failed: {e}")
    
    def show_all(self):
        """Show all cache data"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("╔════════════════════════════════════════════════════════════════════════════╗")
        print("║                    BroskiesHub Backend Cache Viewer                        ║")
        print("║                         MongoDB Data Inspector                             ║")
        print("╚════════════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}\n")
        
        self.show_mongodb_cache()
        self.show_user_cache()
        self.show_scan_cache()
        
        print_header("✨ Cache Viewer Complete")
        print_info("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Cleanup
        if self.mongo_client:
            self.mongo_client.close()

def main():
    """Main function"""
    viewer = CacheViewer()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'export':
            viewer.show_all()
            output_file = sys.argv[2] if len(sys.argv) > 2 else "cache_export.json"
            viewer.export_cache_data(output_file)
        elif command == 'users':
            viewer.connect_mongodb()
            viewer.show_user_cache()
        elif command == 'scans':
            viewer.connect_mongodb()
            viewer.show_scan_cache()
        elif command == 'help':
            print_header("📖 Cache Viewer Help")
            print("Usage: python cache_viewer.py [command] [options]")
            print("\nCommands:")
            print("  (none)        Show all cache data")
            print("  users         Show only user cache")
            print("  scans         Show only scan results cache")
            print("  export [file] Export cache data to JSON file")
            print("  help          Show this help message")
        else:
            print_error(f"Unknown command: {command}")
            print("Use 'python cache_viewer.py help' for usage information")
    else:
        # Show all by default
        viewer.show_all()

if __name__ == "__main__":
    main()
