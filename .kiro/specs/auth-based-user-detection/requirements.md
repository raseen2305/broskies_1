# Authentication-Based User Detection Requirements

## Introduction

This feature enhances the user type detection system to differentiate between internal authenticated users (who connect via GitHub OAuth) and external public users (who enter usernames manually) while using the same API endpoints but with different storage and treatment strategies.

## Glossary

- **Authentication_System**: The GitHub OAuth and JWT-based user authentication mechanism
- **Internal_User**: Users who authenticate via "Connect GitHub" button and have valid JWT tokens
- **External_User**: Users who access the system by typing a username without authentication
- **User_Type_Detector**: The service responsible for determining user type based on authentication status
- **Unified_Endpoints**: API endpoints that serve both internal and external users with different backend behavior
- **Database_Router**: The component that routes user data to appropriate databases based on user type

## Requirements

### Requirement 1

**User Story:** As an internal developer, I want to authenticate via GitHub OAuth when I click "Connect GitHub", so that my data is stored securely in internal databases with full access privileges.

#### Acceptance Criteria

1. WHEN a user clicks "Connect GitHub" on the developer/auth page, THE Authentication_System SHALL initiate GitHub OAuth flow
2. WHEN GitHub OAuth completes successfully, THE Authentication_System SHALL generate a JWT token for the user
3. WHEN a request contains a valid JWT token, THE User_Type_Detector SHALL classify the user as "internal"
4. WHEN an Internal_User makes API requests, THE Database_Router SHALL store their data in raseen_temp_user database
5. WHEN logging Internal_User activities, THE Authentication_System SHALL use 🔐 [INTERNAL] log markers

### Requirement 2

**User Story:** As an external user, I want to analyze GitHub profiles by entering a username, so that I can access the evaluation system without requiring authentication.

#### Acceptance Criteria

1. WHEN a user enters a username in the external interface, THE Authentication_System SHALL process the request without requiring authentication
2. WHEN a request lacks a JWT token, THE User_Type_Detector SHALL classify the user as "external"
3. WHEN an External_User makes API requests, THE Database_Router SHALL store their data in external_users database
4. WHEN processing External_User requests, THE Authentication_System SHALL validate the GitHub username exists
5. WHEN logging External_User activities, THE Authentication_System SHALL use 🌐 [EXTERNAL] log markers

### Requirement 3

**User Story:** As a system architect, I want both user types to use the same API endpoints, so that the frontend can have a unified interface while the backend handles routing appropriately.

#### Acceptance Criteria

1. WHEN Internal_Users or External_Users call scan endpoints, THE Unified_Endpoints SHALL accept both request types
2. WHEN processing scan requests, THE User_Type_Detector SHALL determine user type from JWT presence
3. WHEN routing data storage, THE Database_Router SHALL use different databases based on detected user type
4. WHEN returning responses, THE Unified_Endpoints SHALL provide the same response format for both user types
5. WHEN handling deep analysis requests, THE Unified_Endpoints SHALL apply the same analysis logic regardless of user type

### Requirement 4

**User Story:** As a developer, I want the whitelist system to be removed, so that user type detection is based purely on authentication status rather than hardcoded usernames.

#### Acceptance Criteria

1. WHEN determining user type, THE User_Type_Detector SHALL rely only on JWT token presence
2. WHEN a user has a valid JWT token, THE User_Type_Detector SHALL classify them as "internal" regardless of username
3. WHEN a user lacks a JWT token, THE User_Type_Detector SHALL classify them as "external" regardless of username
4. WHEN the system starts, THE User_Type_Detector SHALL not reference any hardcoded username whitelists
5. WHEN processing requests, THE User_Type_Detector SHALL make authentication-based decisions dynamically

### Requirement 5

**User Story:** As a system administrator, I want proper data isolation between user types, so that internal and external user data never mix or interfere with each other.

#### Acceptance Criteria

1. WHEN storing Internal_User data, THE Database_Router SHALL use internal-prefixed collections in raseen_temp_user database
2. WHEN storing External_User data, THE Database_Router SHALL use external-prefixed collections in external_users database
3. WHEN generating user IDs, THE Database_Router SHALL use "internal_" prefix for authenticated users and "external_" prefix for public users
4. WHEN querying user data, THE Database_Router SHALL ensure queries are scoped to the appropriate user type and database
5. WHEN performing data migrations, THE Database_Router SHALL maintain user type separation throughout the lifecycle

### Requirement 6

**User Story:** As an internal authenticated user, I want exclusive access to profile creation and ranking features, so that these premium features are reserved for users who authenticate via GitHub OAuth.

#### Acceptance Criteria

1. WHEN an Internal_User accesses profile endpoints, THE Authentication_System SHALL allow profile creation and updates
2. WHEN an External_User attempts to access profile endpoints, THE Authentication_System SHALL return 401 Unauthorized error
3. WHEN an Internal_User completes their profile, THE Ranking_System SHALL include them in university and regional rankings
4. WHEN an External_User views scan results, THE Ranking_System SHALL not display any ranking information or widgets
5. WHEN displaying UI components, THE Frontend_System SHALL hide profile setup and ranking widgets for External_Users

### Requirement 7

**User Story:** As an external user, I want to understand that rankings are only available to authenticated users, so that I know how to access these features if desired.

#### Acceptance Criteria

1. WHEN an External_User views scan results, THE Frontend_System SHALL display a clear message explaining that rankings require authentication
2. WHEN showing ranking unavailable message, THE Frontend_System SHALL provide a "Connect GitHub" call-to-action button
3. WHEN External_User clicks "Connect GitHub", THE Authentication_System SHALL initiate the OAuth flow to convert them to Internal_User
4. WHEN explaining ranking features, THE Frontend_System SHALL describe the benefits of authentication (profile, rankings, leaderboards)
5. WHEN External_User completes authentication, THE Frontend_System SHALL immediately show available profile and ranking features