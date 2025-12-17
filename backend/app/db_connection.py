from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging
import asyncio
import os
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ServerlessDatabase:
    """Optimized database connection for serverless environments"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.connection_pool = None
        self.last_activity = 0
        self.connection_timeout = 300  # 5 minutes timeout for serverless
        self.retry_count = 0
        self.max_retries = 3
        self.is_connecting = False
        self._connection_lock = asyncio.Lock()

db = ServerlessDatabase()

async def get_database():
    """Get database connection optimized for serverless with lazy loading and connection pooling"""
    # Fast path: return existing valid connection
    if db.database is not None and time.time() - db.last_activity < db.connection_timeout:
        db.last_activity = time.time()
        return db.database
    
    # Slow path: need to check/establish connection
    if db.database is None or await _is_connection_stale():
        async with db._connection_lock:
            # Double-check after acquiring lock (avoid race condition)
            if db.database is None or await _is_connection_stale():
                logger.info("Establishing database connection for serverless function...")
                await connect_to_mongo_serverless()
    
    # Update last activity timestamp
    db.last_activity = time.time()
    return db.database


async def get_scores_database():
    """
    ⚠️  DEPRECATED: Use the new multi-database architecture instead.
    
    Get the git_Evaluator database connection for storing user scores.
    
    The scores_comparison collection is inside the git_Evaluator database.
    
    Returns:
        AsyncIOMotorDatabase: git_Evaluator database connection
    """
    # Ensure we have a database connection
    main_db = await get_database()
    
    if main_db is None:
        logger.error("No database connection available for scores_comparison")
        return None
    
    # Return the same database (git_Evaluator) - DEPRECATED
    # The scores_comparison is a collection inside this database
    logger.debug("Connected to git_Evaluator database for scores_comparison collection (DEPRECATED)")
    return main_db

async def _is_connection_stale() -> bool:
    """Check if the database connection is stale for serverless environment"""
    if db.client is None or db.database is None:
        return True
    
    # Check if connection has been idle too long
    if time.time() - db.last_activity > db.connection_timeout:
        logger.info("Database connection idle timeout reached, will reconnect")
        return True
    
    # Quick ping test for connection health
    try:
        await asyncio.wait_for(db.client.admin.command('ping'), timeout=2.0)
        return False
    except Exception as e:
        logger.warning(f"Database connection health check failed: {e}")
        return True

async def safe_db_operation(operation_func, fallback_result=None, operation_name="database operation"):
    """Safely execute database operations with serverless-optimized retry logic"""
    max_operation_retries = 2
    
    for attempt in range(max_operation_retries):
        try:
            database = await get_database()
            if database is None:
                logger.warning(f"No database available for {operation_name}, using fallback")
                return fallback_result
            
            # Execute the operation with timeout for serverless
            result = await asyncio.wait_for(
                operation_func(database), 
                timeout=30.0  # 30 second timeout for database operations
            )
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Database operation '{operation_name}' timed out (attempt {attempt + 1})")
            if attempt < max_operation_retries - 1:
                await asyncio.sleep(1)  # Brief delay before retry
                continue
            return fallback_result
            
        except Exception as e:
            logger.error(f"Database operation '{operation_name}' failed (attempt {attempt + 1}): {e}")
            
            # Check if it's a connection-related error
            connection_errors = ['timeout', 'connection', 'network', 'ssl', 'serverselection', 'pymongo']
            is_connection_error = any(error_type in str(e).lower() for error_type in connection_errors)
            
            if is_connection_error and attempt < max_operation_retries - 1:
                logger.info(f"Connection error detected, attempting reconnection for {operation_name}")
                await _cleanup_stale_connections()
                await asyncio.sleep(1)  # Brief delay before retry
                continue
            elif is_connection_error:
                logger.warning(f"Persistent connection issues, switching to fallback for {operation_name}")
                await handle_connection_error()
                
                # Try once more with fallback
                try:
                    database = await get_database()
                    if database is not None:
                        return await operation_func(database)
                except Exception as fallback_error:
                    logger.error(f"Fallback operation also failed: {fallback_error}")
            
            return fallback_result
    
    return fallback_result

async def connect_to_mongo_serverless():
    """Optimized database connection for serverless environments with better error handling"""
    if db.is_connecting:
        # Wait for existing connection attempt
        max_wait = 30  # Maximum 3 seconds wait
        wait_count = 0
        while db.is_connecting and wait_count < max_wait:
            await asyncio.sleep(0.1)
            wait_count += 1
        
        if wait_count >= max_wait:
            logger.warning("Connection attempt timed out, proceeding with fallback")
            await setup_fallback_database()
        return
    
    db.is_connecting = True
    
    try:
        logger.info("Establishing serverless MongoDB connection...")
        
        # Close any existing stale connections
        await _cleanup_stale_connections()
        
        # Try connection with exponential backoff
        success = await _connect_with_retry()
        
        if success:
            logger.info("✅ Serverless MongoDB connection established")
            db.last_activity = time.time()
            db.retry_count = 0
            
            # Create indexes only if needed (avoid on every cold start)
            if not await _indexes_exist():
                try:
                    await create_basic_indexes()
                    logger.info("✅ Database indexes verified/created")
                except Exception as schema_error:
                    logger.warning(f"Index creation warning: {schema_error}")
        else:
            logger.warning("MongoDB connection failed after retries, using fallback")
            await setup_fallback_database()
        
    except asyncio.TimeoutError:
        logger.error("MongoDB connection timed out, using fallback database")
        await setup_fallback_database()
    except Exception as e:
        logger.error(f"Serverless database connection error: {e}")
        await setup_fallback_database()
    finally:
        db.is_connecting = False

async def _cleanup_stale_connections():
    """Clean up any stale database connections"""
    if db.client:
        try:
            db.client.close()
        except Exception as e:
            logger.debug(f"Error closing stale connection: {e}")
        finally:
            db.client = None
            db.database = None

async def _connect_with_retry():
    """Connect to MongoDB with exponential backoff retry logic"""
    base_delay = 1  # Start with 1 second
    
    for attempt in range(db.max_retries):
        try:
            logger.info(f"Connection attempt {attempt + 1}/{db.max_retries}")
            
            # Get connection configuration
            connection_config = _get_serverless_connection_config()
            
            # Log connection details for debugging
            logger.info(f"Connecting to: {connection_config['url'][:50]}...")
            logger.info(f"Database: {connection_config['database_name']}")
            logger.info(f"Connection params: {list(connection_config['params'].keys())}")
            
            # Create client with serverless-optimized settings
            client = AsyncIOMotorClient(
                connection_config["url"],
                **connection_config["params"]
            )
            
            # Test connection with longer timeout for replica set discovery
            await asyncio.wait_for(
                client.admin.command('ping'), 
                timeout=15.0  # Increased timeout for replica set discovery
            )
            
            # Success! Set up the connection
            db.client = client
            db.database = client[connection_config["database_name"]]
            
            logger.info(f"✅ Connected to MongoDB: {connection_config['database_name']}")
            return True
            
        except Exception as e:
            error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
            logger.warning(f"Connection attempt {attempt + 1} failed: {error_msg}")
            logger.debug(f"Exception type: {type(e)}")
            logger.debug(f"Exception args: {e.args}")
            
            if attempt < db.max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            
            try:
                if 'client' in locals():
                    client.close()
            except:
                pass
    
    return False

def _get_serverless_connection_config() -> Dict[str, Any]:
    """Get optimized connection configuration for serverless environment with better timeout handling"""
    
    # Determine database URL and name from environment
    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME", "git_Evaluator")  # Legacy database
    
    # Default to the primary MongoDB Atlas connection (without database name in URL)
    if not mongodb_url:
        mongodb_url = "mongodb+srv://thoshifraseen4_db_user:iojkJvAoEhBOLbmM@online-evaluation.lkxqo8m.mongodb.net/?retryWrites=true&w=majority&appName=online-evaluation"
    
    # Clean up the URL - remove any existing database name that might be incorrectly formatted
    if "mongodb+srv://" in mongodb_url:
        # For Atlas URLs, ensure clean format without database in URL
        # Database name will be specified separately to the client
        base_url = mongodb_url.split('?')[0]  # Get URL without query parameters
        query_params = mongodb_url.split('?')[1] if '?' in mongodb_url else ""
        
        # Remove any database name from the base URL
        if base_url.count('/') > 2:  # mongodb+srv://user:pass@host/database
            base_url = '/'.join(base_url.split('/')[:-1])  # Remove the database part
        
        # Reconstruct URL without database name
        mongodb_url = f"{base_url}?{query_params}" if query_params else base_url
    
    # Optimized connection parameters with longer timeouts for network issues
    connection_params = {
        "serverSelectionTimeoutMS": 30000,  # Increased from 10s to 30s
        "connectTimeoutMS": 30000,  # Increased from 10s to 30s
        "socketTimeoutMS": 45000,  # Added socket timeout
        "maxPoolSize": 1,  # Keep minimal for serverless
        "minPoolSize": 0,  # No minimum connections
        "retryWrites": True,
        "retryReads": True,  # Added retry reads
        "maxIdleTimeMS": 60000,  # Close idle connections after 60s
        "heartbeatFrequencyMS": 30000,  # Heartbeat every 30s
        "tlsAllowInvalidCertificates": False,  # Ensure SSL is properly configured
    }
    
    # For regular mongodb:// connections (not Atlas), add database to URL if needed
    if not mongodb_url.startswith("mongodb+srv://") and database_name not in mongodb_url:
        # For regular mongodb:// connections, add database to URL
        if "?" in mongodb_url:
            mongodb_url = mongodb_url.replace("?", f"/{database_name}?")
        else:
            mongodb_url = f"{mongodb_url}/{database_name}"
    
    return {
        "url": mongodb_url,
        "params": connection_params,
        "database_name": database_name,
        "test_timeout": 25.0  # Increased from 8s to 25s for connection test
    }

async def _indexes_exist() -> bool:
    """Check if basic indexes already exist to avoid recreating them"""
    if db.database is None or (hasattr(db.database, 'collections') and type(db.database).__name__ == 'MockDatabase'):
        return True  # Skip index check for mock database
    
    try:
        # Check if users collection has email index
        indexes = await db.database.users.list_indexes().to_list(length=None)
        email_index_exists = any(
            'email' in idx.get('key', {}) for idx in indexes
        )
        return email_index_exists
    except Exception:
        return False  # Assume indexes don't exist if we can't check

# Keep the original connect_to_mongo for backward compatibility
async def connect_to_mongo():
    """Legacy function - redirects to serverless connection"""
    await connect_to_mongo_serverless()

async def try_multiple_connection_methods():
    """Try multiple MongoDB connection methods"""
    database_name = "git_Evaluator"  # Legacy database
    
    # Connection methods to try in order with enhanced network resilience
    connection_methods = [
        {
            "name": "MongoDB Cloud (Enhanced Resilience)",
            "url": "mongodb+srv://thoshifraseen4_db_user:iojkJvAoEhBOLbmM@online-evaluation.lkxqo8m.mongodb.net/?retryWrites=true&w=majority&appName=online-evaluation&ssl=true&tlsAllowInvalidCertificates=false",
            "timeout": 30,
            "enhanced": True
        },
        {
            "name": "MongoDB Cloud (Standard)",
            "url": "mongodb+srv://thoshifraseen4_db_user:iojkJvAoEhBOLbmM@online-evaluation.lkxqo8m.mongodb.net/?retryWrites=true&w=majority&appName=online-evaluation",
            "timeout": 20
        },
        {
            "name": "MongoDB Cloud (Alternative)",
            "url": "mongodb+srv://sriemathi06112004_db_user:ZXvUQeu7v2UekO4a@github-evaluation.lttiwte.mongodb.net/?retryWrites=true&w=majority&appName=Github-Evaluation",
            "timeout": 15,
            "database": "github_comprehensive_data"
        },
        {
            "name": "Local MongoDB",
            "url": "mongodb://localhost:27017/",
            "timeout": 5
        }
    ]
    
    for method in connection_methods:
        try:
            logger.info(f"Trying {method['name']}...")
            
            # Enhanced connection parameters for network resilience
            connection_params = {
                "serverSelectionTimeoutMS": method["timeout"] * 1000,
                "connectTimeoutMS": method["timeout"] * 1000,
                "socketTimeoutMS": method["timeout"] * 1000,
                "maxPoolSize": 5,  # Reduced pool size for stability
                "minPoolSize": 0,  # No minimum connections
                "maxIdleTimeMS": 45000,  # Close idle connections after 45s
                "heartbeatFrequencyMS": 30000,  # More frequent heartbeat
                "retryWrites": True,
                "retryReads": True,
                "maxConnecting": 2,  # Limit concurrent connections
            }
            
            # Enhanced parameters for problematic connections
            if method.get("enhanced", False):
                connection_params.update({
                    "serverSelectionTimeoutMS": 45000,  # Longer timeout for initial connection
                    "connectTimeoutMS": 30000,
                    "socketTimeoutMS": 45000,
                    "heartbeatFrequencyMS": 10000,  # Very frequent heartbeat
                    "maxIdleTimeMS": 60000,
                    "waitQueueTimeoutMS": 10000,  # Timeout for getting connection from pool
                    "compressors": "zlib",  # Enable compression to reduce network load
                })
            
            client = AsyncIOMotorClient(method["url"], **connection_params)
            
            # Test connection
            await asyncio.wait_for(
                client.admin.command('ping'), 
                timeout=method["timeout"]
            )
            
            # Success! Set up the global database connection
            db.client = client
            # Use method-specific database name if provided, otherwise use default
            method_database = method.get("database", database_name)
            db.database = client[method_database]
            
            logger.info(f"✅ Connected using {method['name']}")
            
            # Test basic operations
            collections = await db.database.list_collection_names()
            method_database = method.get("database", database_name)
            logger.info(f"📊 Database: {method_database} ({len(collections)} collections)")
            
            return True
            
        except Exception as e:
            logger.debug(f"❌ {method['name']} failed: {str(e)[:100]}...")
            try:
                client.close()
            except:
                pass
    
    return False

async def setup_fallback_database():
    """Set up an in-memory fallback database system"""
    logger.info("🔄 Setting up in-memory fallback database...")
    
    # Create a mock database object that stores data in memory
    class MockDatabase:
        def __init__(self):
            self.collections = {}
            self.is_mock = True
        
        def __getattr__(self, name):
            if name not in self.collections:
                self.collections[name] = MockCollection(name)
            return self.collections[name]
        
        async def list_collection_names(self):
            return list(self.collections.keys())
        
        async def command(self, cmd):
            if cmd == 'ping':
                return {'ok': 1}
            return {'ok': 1}
    
    class MockCollection:
        def __init__(self, name):
            self.name = name
            self.documents = []
            self.indexes = []
        
        async def insert_one(self, document):
            import uuid
            doc_id = str(uuid.uuid4())
            document['_id'] = doc_id
            self.documents.append(document)
            
            class InsertResult:
                def __init__(self, doc_id):
                    self.inserted_id = doc_id
            
            return InsertResult(doc_id)
        
        async def find_one(self, filter_dict=None, sort=None):
            if not filter_dict:
                return self.documents[0] if self.documents else None
            
            for doc in self.documents:
                match = True
                for key, value in filter_dict.items():
                    if key not in doc or doc[key] != value:
                        match = False
                        break
                if match:
                    return doc
            return None
        
        async def find(self, filter_dict=None):
            if not filter_dict:
                return MockCursor(self.documents)
            
            filtered = []
            for doc in self.documents:
                match = True
                for key, value in filter_dict.items():
                    if key not in doc or doc[key] != value:
                        match = False
                        break
                if match:
                    filtered.append(doc)
            
            return MockCursor(filtered)
        
        async def update_one(self, filter_dict, update_dict, upsert=False):
            for doc in self.documents:
                match = True
                for key, value in filter_dict.items():
                    if key not in doc or doc[key] != value:
                        match = False
                        break
                if match:
                    if '$set' in update_dict:
                        doc.update(update_dict['$set'])
                    
                    class UpdateResult:
                        def __init__(self):
                            self.modified_count = 1
                    
                    return UpdateResult()
            
            # If no match found and upsert is True, insert new document
            if upsert:
                new_doc = dict(filter_dict)
                if '$set' in update_dict:
                    new_doc.update(update_dict['$set'])
                
                import uuid
                new_doc['_id'] = str(uuid.uuid4())
                self.documents.append(new_doc)
                
                class UpdateResult:
                    def __init__(self):
                        self.modified_count = 0
                        self.upserted_id = new_doc['_id']
                
                return UpdateResult()
            
            class UpdateResult:
                def __init__(self):
                    self.modified_count = 0
            
            return UpdateResult()
        
        async def delete_many(self, filter_dict):
            deleted_count = 0
            i = 0
            while i < len(self.documents):
                doc = self.documents[i]
                match = True
                for key, value in filter_dict.items():
                    if key not in doc or doc[key] != value:
                        match = False
                        break
                if match:
                    del self.documents[i]
                    deleted_count += 1
                else:
                    i += 1
            
            class DeleteResult:
                def __init__(self, count):
                    self.deleted_count = count
            
            return DeleteResult(deleted_count)
        
        async def delete_one(self, filter_dict):
            for i, doc in enumerate(self.documents):
                match = True
                for key, value in filter_dict.items():
                    if key not in doc or doc[key] != value:
                        match = False
                        break
                if match:
                    del self.documents[i]
                    
                    class DeleteResult:
                        def __init__(self):
                            self.deleted_count = 1
                    
                    return DeleteResult()
            
            class DeleteResult:
                def __init__(self):
                    self.deleted_count = 0
            
            return DeleteResult()
        
        async def create_index(self, keys, **kwargs):
            self.indexes.append({'keys': keys, 'options': kwargs})
            return f"index_{len(self.indexes)}"
        
        async def count_documents(self, filter_dict=None):
            if not filter_dict:
                return len(self.documents)
            
            count = 0
            for doc in self.documents:
                match = True
                for key, value in filter_dict.items():
                    if key not in doc or doc[key] != value:
                        match = False
                        break
                if match:
                    count += 1
            return count
    
    class MockCursor:
        def __init__(self, documents):
            self.documents = documents
        
        async def to_list(self, length=None):
            if length is None:
                return self.documents
            return self.documents[:length]
        
        def sort(self, key, direction=1):
            if isinstance(key, str):
                self.documents.sort(key=lambda x: x.get(key, ''), reverse=(direction == -1))
            return self
        
        def limit(self, count):
            self.documents = self.documents[:count]
            return self
        
        def skip(self, count):
            self.documents = self.documents[count:]
            return self
    
    # Set up the mock database
    db.client = None
    db.database = MockDatabase()
    
    logger.info("✅ In-memory fallback database ready")
    logger.info("📝 Note: Data will not persist between restarts")
    logger.info("🔄 All operations will work normally with temporary storage")

async def create_basic_indexes():
    """Create basic indexes for the database"""
    if db.database is None:
        return
    
    try:
        # Users collection indexes
        if db.database is not None:
            await db.database.users.create_index("email", unique=True)
            await db.database.users.create_index("github_username")
            
            # Repositories collection indexes
            await db.database.repositories.create_index("user_id")
            await db.database.repositories.create_index("name")
            
            # GitHub profiles indexes
            await db.database.github_user_profiles.create_index("user_id", unique=True)
            await db.database.github_user_profiles.create_index("login", unique=True)
        
        logger.info("Basic database indexes created")
        
    except Exception as e:
        logger.warning(f"Error creating basic indexes: {e}")
        # Don't raise, just log the warning

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        try:
            db.client.close()
            logger.info("Disconnected from MongoDB")
        except Exception as e:
            logger.warning(f"Error closing MongoDB connection: {e}")
        finally:
            db.client = None
            db.database = None

async def handle_connection_error():
    """Handle persistent connection errors by switching to fallback"""
    logger.warning("Handling persistent MongoDB connection errors...")
    await close_mongo_connection()
    await setup_fallback_database()
    logger.info("Switched to fallback database due to connection issues")

async def create_indexes():
    """Legacy function - now handled by basic index creation"""
    logger.info("Creating basic database indexes")
    if db.database is not None:
        await create_basic_indexes()

# Removed old alternative connections function - now using try_multiple_connection_methods

async def monitor_connection_health():
    """Lightweight connection monitoring for serverless environment"""
    # In serverless, we don't need continuous monitoring
    # Instead, we check connection health on-demand in get_database()
    logger.info("Serverless mode: Using on-demand connection health checks")
    
    # Optional: Set up a cleanup task for idle connections
    asyncio.create_task(_cleanup_idle_connections())

async def _cleanup_idle_connections():
    """Clean up idle connections in serverless environment"""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            if (db.client and 
                time.time() - db.last_activity > db.connection_timeout and
                not hasattr(db.database, 'is_mock')):
                
                logger.info("Closing idle database connection in serverless environment")
                await _cleanup_stale_connections()
                
        except Exception as e:
            logger.debug(f"Idle connection cleanup error: {e}")
            await asyncio.sleep(30)

async def get_db_health():
    """Get database health information"""
    if db.database is not None:
        try:
            # Check if it's a mock database
            if type(db.database).__name__ == 'MockDatabase':
                return {
                    "healthy": True, 
                    "message": "In-memory fallback database active",
                    "type": "fallback",
                    "note": "Data will not persist between restarts"
                }
            
            # Real MongoDB connection
            if db.client is not None:
                await asyncio.wait_for(db.client.admin.command('ping'), timeout=8.0)
                return {
                    "healthy": True, 
                    "message": "MongoDB connection successful",
                    "type": "mongodb"
                }
            
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return {"healthy": False, "error": str(e), "type": "mongodb"}
    
    return {"healthy": False, "error": "No database connection", "type": "none"}

async def diagnose_connection_issues():
    """Comprehensive database connection diagnostics"""
    diagnostics = {
        "timestamp": time.time(),
        "environment": {},
        "connection_attempts": [],
        "network_tests": [],
        "recommendations": []
    }
    
    # Check environment variables
    diagnostics["environment"] = {
        "MONGODB_URL": "SET" if os.getenv("MONGODB_URL") else "MISSING",
        "DATABASE_NAME": os.getenv("DATABASE_NAME", "git_Evaluator"),  # Legacy
        "connection_config": _get_serverless_connection_config()
    }
    
    # Test different connection methods
    test_urls = [
        {
            "name": "Primary Atlas (Correct Format)",
            "url": "mongodb+srv://thoshifraseen4_db_user:iojkJvAoEhBOLbmM@online-evaluation.lkxqo8m.mongodb.net/?retryWrites=true&w=majority&appName=online-evaluation"
        },
        {
            "name": "Environment URL",
            "url": os.getenv("MONGODB_URL", "NOT_SET")
        }
    ]
    
    for test_config in test_urls:
        if test_config["url"] == "NOT_SET":
            continue
            
        attempt_result = {
            "name": test_config["name"],
            "url_masked": test_config["url"].replace(
                test_config["url"].split("://")[1].split("@")[0], 
                "***:***"
            ) if "://" in test_config["url"] else test_config["url"],
            "success": False,
            "error": None,
            "duration": 0
        }
        
        start_time = time.time()
        try:
            # Quick connection test
            test_client = AsyncIOMotorClient(
                test_config["url"],
                serverSelectionTimeoutMS=15000,
                connectTimeoutMS=10000,
                socketTimeoutMS=15000
            )
            
            await asyncio.wait_for(
                test_client.admin.command('ping'), 
                timeout=12.0
            )
            
            attempt_result["success"] = True
            attempt_result["duration"] = time.time() - start_time
            
            # Test database access
            test_db = test_client[diagnostics["environment"]["DATABASE_NAME"]]
            collections = await test_db.list_collection_names()
            attempt_result["collections_count"] = len(collections)
            
            test_client.close()
            
        except Exception as e:
            attempt_result["error"] = str(e)
            attempt_result["duration"] = time.time() - start_time
            
            try:
                test_client.close()
            except:
                pass
        
        diagnostics["connection_attempts"].append(attempt_result)
    
    # Network connectivity tests
    import socket
    network_tests = [
        ("DNS Resolution", "online-evaluation.lkxqo8m.mongodb.net", 27017),
        ("Google DNS", "8.8.8.8", 53),
    ]
    
    for test_name, host, port in network_tests:
        test_result = {
            "name": test_name,
            "host": host,
            "port": port,
            "success": False,
            "error": None
        }
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            test_result["success"] = result == 0
            if result != 0:
                test_result["error"] = f"Connection failed with code {result}"
                
        except Exception as e:
            test_result["error"] = str(e)
        
        diagnostics["network_tests"].append(test_result)
    
    # Generate recommendations
    successful_connections = [a for a in diagnostics["connection_attempts"] if a["success"]]
    failed_connections = [a for a in diagnostics["connection_attempts"] if not a["success"]]
    
    if not successful_connections:
        diagnostics["recommendations"].extend([
            "No successful database connections found",
            "Check MongoDB Atlas network access settings",
            "Verify IP whitelist includes 0.0.0.0/0 for Vercel",
            "Confirm database credentials are correct",
            "Check if MongoDB Atlas cluster is running"
        ])
    
    if any("timeout" in str(a.get("error", "")).lower() for a in failed_connections):
        diagnostics["recommendations"].append("Network timeouts detected - consider increasing timeout values")
    
    if any("authentication" in str(a.get("error", "")).lower() for a in failed_connections):
        diagnostics["recommendations"].append("Authentication issues detected - verify username/password")
    
    network_failures = [t for t in diagnostics["network_tests"] if not t["success"]]
    if network_failures:
        diagnostics["recommendations"].append("Network connectivity issues detected")
    
    return diagnostics