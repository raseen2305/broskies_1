# Database Management Scripts

This directory contains scripts for managing the multi-database MongoDB architecture for optimal performance and maintenance.

## Scripts

### 1. test_database_initialization.py
Tests the multi-database initialization system and verifies all connections.

**Usage:**
```bash
cd backend
python scripts/test_database_initialization.py
```

**Output:**
- Tests connection to all 6 databases
- Verifies health check system
- Reports database status and metrics
- Validates system initialization

### 2. clear_all_collections.py
Manages data cleanup across the multi-database architecture.

**Usage:**
```bash
cd backend
# List all databases and collections
python scripts/clear_all_collections.py list

# Clear specific database
python scripts/clear_all_collections.py database external_users

# Clear all databases (DANGEROUS)
python scripts/clear_all_collections.py all
```

**Features:**
- Works with all 6 databases in the architecture
- Safe confirmation prompts
- Detailed progress reporting
- Verification of deletion

### 3. config_manager.py
Manages environment configuration for different deployment environments.

**Usage:**
```bash
cd backend
# Detect current environment
python scripts/config_manager.py detect

# Validate configuration
python scripts/config_manager.py validate

# Generate environment template
python scripts/config_manager.py template production
```

**Features:**
- Environment detection (development, staging, production, test)
- Configuration validation with detailed error reporting
- Template generation for different environments
- Multi-database URL validation

### 4. check_indexes.py (Legacy)
Checks and documents all existing indexes in the old single database.

⚠️ **DEPRECATED**: Use the new multi-database health monitoring instead.

### 5. create_indexes.py (Legacy)
Creates all required indexes for the old single database system.

⚠️ **DEPRECATED**: Index creation is now handled automatically by the database initialization system.

## Required Indexes

### users
- `github_username` (unique, sparse) - For user lookup
- `email` (unique, sparse) - For email lookup

### user_profiles
- `user_id` (unique) - Primary lookup
- `overall_score` (descending) - For rankings
- `github_username` - For username lookup
- `scan_completed` - For filtering scanned users
- `analysis_completed` - For filtering analyzed users

### repositories
- `user_id` - For user's repositories
- `user_id + category` - For categorized repository queries
- `user_id + analyzed` - For analyzed repository queries
- `user_id + importance_score` - For sorted repository lists
- `category + importance_score` - For category-based rankings
- `full_name` - For repository lookup

### evaluations
- `user_id` - For user's evaluations
- `repo_id` - For repository evaluations
- `user_id + created_at` - For recent evaluations

### regional_scores
- `user_id` (unique) - Primary lookup
- `region + overall_score` - For regional rankings
- `state + overall_score` - For state rankings
- `district + overall_score` - For district rankings
- `github_username` - For username lookup

### university_scores
- `user_id` (unique) - Primary lookup
- `university + overall_score` - For university rankings
- `university_short + overall_score` - For short name rankings
- `github_username` - For username lookup

### audit_logs
- `user_id + timestamp` - For user audit trail
- `operation + timestamp` - For operation-based queries
- `resource_type + resource_id` - For resource audit trail
- `timestamp` - For time-based queries

## Performance Benefits

Proper indexing provides:
- **Faster queries**: 10-100x improvement for indexed fields
- **Efficient sorting**: Rankings and leaderboards
- **Quick lookups**: User and repository searches
- **Optimized joins**: Related data retrieval

## Maintenance

### Check Index Usage
```javascript
// In MongoDB shell
db.repositories.aggregate([{ $indexStats: {} }])
```

### Monitor Query Performance
```javascript
// Explain query plan
db.repositories.find({ user_id: "123" }).explain("executionStats")
```

### Drop Unused Indexes
```javascript
// Only if confirmed unused
db.collection.dropIndex("index_name")
```

## Best Practices

1. **Run check_indexes.py** before deployment to verify all indexes exist
2. **Run create_indexes.py** during initial setup and after schema changes
3. **Monitor index usage** in production to identify optimization opportunities
4. **Keep indexes minimal** - only create indexes that are actually used
5. **Test queries** with `.explain()` to verify index usage

## Environment Variables

The multi-database architecture requires these environment variables:

### Required Database URLs
```bash
# External Users Database
EXTERNAL_USERS_DB_URL=mongodb+srv://user:pass@cluster.mongodb.net/external_users?retryWrites=true&w=majority&appName=online-evaluation

# Raseen Region Databases
RASEEN_TEMP_USER_DB_URL=mongodb+srv://user:pass@cluster.mongodb.net/raseen_temp_user?retryWrites=true&w=majority&appName=online-evaluation
RASEEN_MAIN_USER_DB_URL=mongodb+srv://user:pass@cluster.mongodb.net/raseen_main_user?retryWrites=true&w=majority&appName=online-evaluation
RASEEN_MAIN_HR_DB_URL=mongodb+srv://user:pass@cluster.mongodb.net/raseen_main_hr?retryWrites=true&w=majority&appName=online-evaluation

# SRIE Region Databases (Backup)
SRIE_MAIN_USER_DB_URL=mongodb+srv://user:pass@cluster.mongodb.net/srie_main_user?retryWrites=true&w=majority&appName=online-evaluation
SRIE_MAIN_HR_DB_URL=mongodb+srv://user:pass@cluster.mongodb.net/srie_main_hr?retryWrites=true&w=majority&appName=online-evaluation
```

### Legacy Variables (Deprecated)
- `MONGODB_URL` - Old single database connection (still supported for backward compatibility)
- `DATABASE_NAME` - Old database name (default: 'git_Evaluator')

Set these in your `.env` file.

## Troubleshooting

### "Index already exists" error
This is normal - the script skips existing indexes. No action needed.

### "Duplicate key error"
An existing document violates the unique constraint. Clean up duplicates before creating the index.

### "Connection timeout"
Check your MongoDB connection string and network connectivity.

### Performance still slow
1. Run `check_indexes.py` to verify indexes exist
2. Use `.explain()` to check if queries use indexes
3. Consider adding compound indexes for common query patterns
4. Check if indexes need to be rebuilt: `db.collection.reIndex()`
