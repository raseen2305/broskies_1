# Database Restructuring Requirements

## Introduction

This feature implements a comprehensive database restructuring to replace the current git evaluator databases with a new multi-database architecture that provides proper user differentiation, data lifecycle management, and backup strategies for both internal authenticated users and external public users.

## Glossary

- **Database_System**: The MongoDB-based data storage infrastructure for the online evaluation platform
- **Internal_User**: Authenticated users with JWT tokens and GitHub OAuth (e.g., raseen2305)
- **External_User**: Public users accessing the system without authentication (e.g., srie06)
- **Temp_Database**: Temporary storage for 24-hour data retention before migration to main storage
- **Main_Database**: Primary long-term storage for user data and analysis results
- **HR_Database**: Human resources backup database for employment-related data
- **Data_Lifecycle**: The automated process of moving data from temporary to permanent storage

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to restructure the database architecture to use separate databases for different user types and data lifecycles, so that I can ensure proper data isolation and backup strategies.

#### Acceptance Criteria

1. WHEN the system starts, THE Database_System SHALL connect to seven distinct MongoDB databases using the online-evaluation cluster
2. WHEN an External_User accesses the system, THE Database_System SHALL store their data in the external_users database
3. WHEN an Internal_User accesses the system, THE Database_System SHALL initially store their data in the raseen_temp_user database
4. WHEN data has been in raseen_temp_user for 24 hours, THE Database_System SHALL automatically migrate it to raseen_main_user database
5. WHEN data is migrated to raseen_main_user, THE Database_System SHALL also replicate it to srie_main_user for backup purposes

### Requirement 2

**User Story:** As a developer, I want the system to maintain strict user type differentiation, so that internal and external users are never confused or treated incorrectly.

#### Acceptance Criteria

1. WHEN processing an Internal_User request, THE Database_System SHALL use the internal_ prefix for user identification and log with 🔐 [INTERNAL] markers
2. WHEN processing an External_User request, THE Database_System SHALL use the external_ prefix for user identification and log with 🌐 [EXTERNAL] markers
3. WHEN storing data for Internal_Users, THE Database_System SHALL use separate collections with internal_ prefixes
4. WHEN storing data for External_Users, THE Database_System SHALL use separate collections with external_ prefixes
5. WHEN authenticating users, THE Database_System SHALL require JWT and GitHub OAuth tokens for Internal_Users and allow public access for External_Users

### Requirement 3

**User Story:** As a system administrator, I want automated data lifecycle management, so that temporary data is properly migrated and backed up without manual intervention.

#### Acceptance Criteria

1. WHEN data reaches 24 hours in raseen_temp_user, THE Database_System SHALL automatically move it to raseen_main_user
2. WHEN data is moved to raseen_main_user, THE Database_System SHALL simultaneously copy it to srie_main_user as backup
3. WHEN HR-related data is processed, THE Database_System SHALL store it in raseen_main_hr and backup to srie_main_hr
4. WHEN the migration process completes, THE Database_System SHALL remove the data from the temporary database
5. WHEN any migration fails, THE Database_System SHALL log the error and retry the operation

### Requirement 4

**User Story:** As a developer, I want the database configuration to be environment-driven, so that different environments can use appropriate database connections without code changes.

#### Acceptance Criteria

1. WHEN the application starts, THE Database_System SHALL read database URLs from environment variables
2. WHEN connecting to databases, THE Database_System SHALL use the appropriate connection string for each database type
3. WHEN environment variables are missing, THE Database_System SHALL fail gracefully with clear error messages
4. WHEN database connections fail, THE Database_System SHALL retry with exponential backoff
5. WHEN switching between environments, THE Database_System SHALL use the correct database cluster without code modifications