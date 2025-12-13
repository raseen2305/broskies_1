# Multi-Database Architecture Migration Guide

## Overview

The application has been migrated from a single `git_Evaluator` database to a comprehensive multi-database architecture with proper user differentiation, data lifecycle management, and backup strategies.

## New Database Architecture

### 7 Database Structure

1. **external_users** - Public user data (no authentication required)
2. **raseen_temp_user** - Temporary internal user data (24-hour lifecycle)
3. **raseen_main_user** - Main internal user data (long-term storage)
4. **raseen_main_hr** - HR-related data
5. **srie_main_user** - Backup user data
6. **srie_main_hr** - Backup HR data

### Environment Configuration

Replace the old single database configuration:

```bash
# OLD (DEPRECATED)
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=git_Evaluator
```

With the new multi-database configuration:

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

## Code Migration

### Database Connections

**OLD:**
```python
from app.db_connection import get_database
db = await get_database()
```

**NEW:**
```python
from app.db_connection_multi import get_user_database
from app.user_type_detector import detect_user_type_from_request

# Automatic routing based on user type
user_type = detect_user_type_from_request(request)
db = await get_user_database(user_type, "user_data")

# Or specific database access
from app.db_connection_multi import (
    get_external_users_db,
    get_raseen_temp_user_db,
    get_raseen_main_user_db
)

external_db = await get_external_users_db()
temp_db = await get_raseen_temp_user_db()
main_db = await get_raseen_main_user_db()
```

### User Type Detection

The system now automatically detects user types:

```python
from app.user_type_detector import UserTypeDetector

# Route user operations automatically
routing_info = await UserTypeDetector.route_user_operation(
    user_id="srie06",
    operation_type="store",
    data={"scan_results": {...}},
    data_category="user_data"
)

database = routing_info["database"]
collection_name = routing_info["collection_name"]
```

## Health Monitoring

New comprehensive health monitoring endpoints:

- `GET /health/` - Overall system health
- `GET /health/databases` - All databases status
- `GET /health/database/{name}` - Specific database status
- `GET /health/errors` - Error statistics
- `GET /health/ready` - Kubernetes readiness check
- `GET /health/live` - Kubernetes liveness check
- `GET /health/metrics` - System metrics

## Data Migration

### Automatic Data Lifecycle

- **Internal users**: Data starts in `raseen_temp_user`
- **After 24 hours**: Automatically migrated to `raseen_main_user`
- **Backup**: Simultaneously copied to `srie_main_user`
- **External users**: Data stored directly in `external_users`

### User ID Prefixing

- **Internal users**: `internal_507f1f77bcf86cd799439011`
- **External users**: `external_srie06`

## Deprecated Components

The following components are deprecated and should not be used:

### Files
- `app/db_connection.py` - Use `app/db_connection_multi.py`
- `migrate_user_rankings.py` - Use new multi-database system
- Scripts using single database connection

### Functions
- `get_database()` - Use `get_user_database()` or specific database functions
- `get_scores_database()` - Use appropriate database based on user type

## Testing

### Database Initialization Test
```bash
python backend/scripts/test_database_initialization.py
```

### Clear Collections (Multi-Database)
```bash
# List all databases and collections
python backend/scripts/clear_all_collections.py list

# Clear specific database
python backend/scripts/clear_all_collections.py database external_users

# Clear all databases (DANGEROUS)
python backend/scripts/clear_all_collections.py all
```

### Health Check
```bash
curl http://localhost:8000/health/
curl http://localhost:8000/health/databases
```

## Configuration Management

Use the configuration manager for environment setup:

```bash
# Detect current environment
python backend/scripts/config_manager.py detect

# Validate configuration
python backend/scripts/config_manager.py validate

# Generate environment template
python backend/scripts/config_manager.py template production
```

## Troubleshooting

### Common Issues

1. **Environment Variables Not Set**
   - Ensure all 6 database URLs are configured
   - Check `.env` file is loaded properly

2. **Connection Failures**
   - Verify network connectivity to MongoDB cluster
   - Check database URLs and credentials
   - Review firewall settings

3. **User Type Detection Issues**
   - Verify JWT tokens for internal users
   - Check user ID formatting
   - Review authentication headers

### Diagnostic Tools

```bash
# Database connection diagnostics
python backend/diagnose_startup.py

# Health check endpoints
curl http://localhost:8000/health/errors
curl http://localhost:8000/health/metrics
```

## Migration Checklist

- [ ] Update environment variables with 6 database URLs
- [ ] Remove old `MONGODB_URL` and `DATABASE_NAME` variables
- [ ] Update code to use new database connection methods
- [ ] Test user type detection and routing
- [ ] Verify health monitoring endpoints
- [ ] Run database initialization test
- [ ] Update deployment configurations
- [ ] Update documentation and README files

## Support

For issues with the multi-database architecture:

1. Check health endpoints for system status
2. Review error statistics at `/health/errors`
3. Run database initialization test
4. Check environment configuration with config manager
5. Review application logs for detailed error information