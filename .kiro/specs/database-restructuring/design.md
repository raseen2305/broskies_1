# Database Restructuring Design

## Overview

This design implements a multi-database architecture that replaces the current git evaluator databases with a structured approach featuring user type differentiation, automated data lifecycle management, and comprehensive backup strategies. The system uses seven MongoDB databases within the online-evaluation cluster to handle different user types and data retention policies.

## Architecture

The system follows a hub-and-spoke database architecture with the following components:

- **External Users Hub**: Single database for public user data
- **Internal Users Lifecycle**: Three-tier system (temp → main → backup)
- **HR Data Management**: Dedicated databases with backup replication
- **Connection Manager**: Centralized database connection handling
- **Migration Service**: Automated data lifecycle management

## Components and Interfaces

### Database Connection Manager
- **Purpose**: Manages connections to all seven databases
- **Interface**: Provides database instances based on user type and data category
- **Methods**: 
  - `get_external_db()`: Returns external users database
  - `get_raseen_temp_db()`: Returns temporary internal user database
  - `get_raseen_main_db()`: Returns main internal user database
  - `get_raseen_hr_db()`: Returns HR database
  - `get_srie_main_db()`: Returns backup user database
  - `get_srie_hr_db()`: Returns backup HR database

### User Type Detector
- **Purpose**: Identifies user type based on authentication context
- **Interface**: Analyzes request headers and tokens
- **Methods**:
  - `is_internal_user(request)`: Returns boolean for internal user detection
  - `get_user_id_with_prefix(user_data, user_type)`: Returns prefixed user ID
  - `get_appropriate_database(user_type, data_category)`: Returns correct database

### Data Migration Service
- **Purpose**: Handles automated 24-hour data lifecycle
- **Interface**: Background service with scheduled operations
- **Methods**:
  - `migrate_expired_data()`: Moves 24-hour old data from temp to main
  - `backup_to_srie()`: Replicates data to backup databases
  - `cleanup_temp_data()`: Removes migrated data from temporary storage

### Logging Service
- **Purpose**: Provides differentiated logging for user types
- **Interface**: Enhanced logging with visual markers
- **Methods**:
  - `log_internal_operation(message, user_id)`: Logs with 🔐 [INTERNAL] prefix
  - `log_external_operation(message, user_id)`: Logs with 🌐 [EXTERNAL] prefix

## Data Models

### User Data Structure
```python
{
    "user_id": "internal_507f1f77bcf86cd799439011" | "external_srie06",
    "user_type": "internal" | "external",
    "created_at": datetime,
    "last_accessed": datetime,
    "data_location": "temp" | "main" | "external",
    "scan_cache": {...},
    "analysis_progress": {...},
    "metadata": {
        "storage_location": "RASEEN_TEMP" | "RASEEN_MAIN" | "EXTERNAL",
        "backup_status": "pending" | "completed" | "failed"
    }
}
```

### Migration Record
```python
{
    "migration_id": ObjectId,
    "user_id": str,
    "source_db": "raseen_temp_user",
    "target_db": "raseen_main_user",
    "backup_db": "srie_main_user",
    "migration_date": datetime,
    "status": "pending" | "completed" | "failed",
    "data_size": int,
    "retry_count": int
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: External User Database Routing
*For any* external user request, the system should store all data in the external_users database and use external_ prefixes for user identification
**Validates: Requirements 1.2, 2.2, 2.4**

### Property 2: Internal User Initial Storage
*For any* internal user request, the system should initially store data in raseen_temp_user database and use internal_ prefixes for user identification
**Validates: Requirements 1.3, 2.1, 2.3**

### Property 3: Data Migration and Backup Consistency
*For any* data that has been in temporary storage for 24 hours, migrating it should result in the data appearing in both raseen_main_user and srie_main_user databases while being removed from raseen_temp_user
**Validates: Requirements 1.4, 1.5, 3.1, 3.2, 3.4**

### Property 4: HR Data Routing and Backup
*For any* HR-related data, the system should store it in raseen_main_hr and simultaneously backup to srie_main_hr
**Validates: Requirements 3.3**

### Property 5: Authentication Requirements Consistency
*For any* user request, internal users should require JWT and GitHub OAuth tokens while external users should have public access without authentication
**Validates: Requirements 2.5**

### Property 6: Migration Retry on Failure
*For any* failed migration operation, the system should log the error and retry the operation with appropriate backoff
**Validates: Requirements 3.5**

### Property 7: Database Connection String Correctness
*For any* database type, the system should use the appropriate connection string from environment variables without cross-wiring connections
**Validates: Requirements 4.2, 4.5**

### Property 8: Connection Retry with Exponential Backoff
*For any* database connection failure, the system should retry with exponential backoff until successful or maximum retries reached
**Validates: Requirements 4.4**

## Error Handling

### Database Connection Failures
- Implement exponential backoff retry mechanism
- Log connection failures with appropriate user type markers
- Graceful degradation for non-critical operations
- Circuit breaker pattern for persistent failures

### Migration Failures
- Retry failed migrations up to 3 times
- Maintain migration logs for audit purposes
- Alert administrators for persistent migration failures
- Preserve data integrity during partial failures

### User Type Misidentification
- Validate user type at multiple checkpoints
- Log warnings for ambiguous user contexts
- Default to external user treatment for safety
- Maintain audit trail for user type decisions

## Testing Strategy

### Unit Testing
- Test database connection manager with mock databases
- Verify user type detection logic with various authentication contexts
- Test migration service with controlled time scenarios
- Validate logging service output formatting

### Property-Based Testing
The system will use **pytest** with **hypothesis** library for property-based testing. Each property-based test will run a minimum of 100 iterations to ensure comprehensive coverage.

- **Property 1 Test**: Generate random user requests and verify consistent user type treatment
- **Property 2 Test**: Generate various user operations and verify correct database routing
- **Property 3 Test**: Generate time-shifted data scenarios and verify complete migration cycles
- **Property 4 Test**: Generate authentication contexts and verify proper access control
- **Property 5 Test**: Generate environment configurations and verify connection establishment

### Integration Testing
- Test complete user workflows from request to database storage
- Verify data migration processes with real MongoDB instances
- Test backup and replication mechanisms
- Validate cross-database consistency during migrations