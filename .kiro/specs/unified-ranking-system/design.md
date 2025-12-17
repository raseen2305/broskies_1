# Design Document

## Overview

The unified ranking system combines GitHub analysis data from the `internal_users` collection with profile information from the `internal_users_profile` collection to generate comprehensive university and regional rankings. The system uses MongoDB aggregation pipelines to efficiently join data, calculate rankings, and maintain synchronized ranking collections for optimal query performance.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│  internal_users │    │ internal_users_profile│    │   Ranking Service   │
│                 │    │                      │    │                     │
│ - username      │    │ - github_username    │    │ - Data Joining      │
│ - overall_score │◄──►│ - university         │◄──►│ - Rank Calculation  │
│ - scan_data     │    │ - district           │    │ - Batch Updates     │
│ - updated_at    │    │ - state              │    │ - Synchronization   │
└─────────────────┘    └──────────────────────┘    └─────────────────────┘
                                                              │
                                                              ▼
                       ┌─────────────────────────────────────────────────────┐
                       │              Ranking Collections                    │
                       │                                                     │
                       │  ┌─────────────────┐    ┌─────────────────────┐   │
                       │  │university_rankings│    │ regional_rankings   │   │
                       │  │                 │    │                     │   │
                       │  │ - user_id       │    │ - user_id           │   │
                       │  │ - rank          │    │ - rank              │   │
                       │  │ - percentile    │    │ - percentile        │   │
                       │  │ - university    │    │ - district          │   │
                       │  └─────────────────┘    └─────────────────────┘   │
                       └─────────────────────────────────────────────────────┘
```

### Data Flow

1. **Data Collection**: Users complete GitHub scans (stored in `internal_users`) and profile forms (stored in `internal_users_profile`)
2. **Data Joining**: System joins collections using `username` ↔ `github_username` mapping
3. **Ranking Calculation**: Batch processes calculate rankings for university and regional groups
4. **Data Synchronization**: Results are stored in optimized ranking collections
5. **API Access**: Endpoints serve ranking data from optimized collections

## Components and Interfaces

### UnifiedRankingService

Primary service responsible for coordinating ranking operations:

```python
class UnifiedRankingService:
    async def calculate_all_rankings(self) -> Dict[str, Any]
    async def calculate_university_rankings(self, university: str) -> Dict[str, Any]
    async def calculate_regional_rankings(self, district: str) -> Dict[str, Any]
    async def get_user_rankings(self, user_id: str) -> Dict[str, Any]
    async def trigger_user_ranking_update(self, user_id: str) -> Dict[str, Any]
```

### DataJoiningService

Handles the complex logic of joining user data from multiple collections:

```python
class DataJoiningService:
    async def get_complete_user_profiles(self) -> List[Dict[str, Any]]
    async def get_users_by_university(self, university: str) -> List[Dict[str, Any]]
    async def get_users_by_district(self, district: str) -> List[Dict[str, Any]]
    async def validate_user_completeness(self, user_data: Dict) -> bool
```

### RankingCalculator

Performs mathematical ranking calculations:

```python
class RankingCalculator:
    def calculate_percentile(self, user_score: float, all_scores: List[float]) -> float
    def calculate_rank_position(self, user_score: float, all_scores: List[float]) -> int
    def calculate_statistics(self, scores: List[float]) -> Dict[str, float]
    def handle_tied_scores(self, scores: List[float]) -> Dict[float, int]
```

### RankingSynchronizer

Manages data consistency across ranking collections:

```python
class RankingSynchronizer:
    async def sync_university_rankings(self, university_data: List[Dict]) -> bool
    async def sync_regional_rankings(self, regional_data: List[Dict]) -> bool
    async def validate_data_consistency(self) -> Dict[str, Any]
    async def resolve_data_conflicts(self) -> Dict[str, Any]
```

## Data Models

### Joined User Profile

```python
class JoinedUserProfile:
    user_id: str
    github_username: str
    overall_score: float
    
    # From internal_users_profile
    name: str
    university: str
    university_short: str
    district: str
    state: str
    region: str
    
    # From internal_users
    scan_date: datetime
    updated_at: datetime
    
    # Computed fields
    profile_complete: bool
    scan_complete: bool
    ranking_eligible: bool
```

### University Ranking Entry

```python
class UniversityRankingEntry:
    user_id: str
    github_username: str
    name: str
    university: str
    university_short: str
    overall_score: float
    rank: int
    total_users: int
    percentile: float
    avg_score: float
    median_score: float
    updated_at: datetime
```

### Regional Ranking Entry

```python
class RegionalRankingEntry:
    user_id: str
    github_username: str
    name: str
    district: str
    state: str
    region: str
    overall_score: float
    rank: int
    total_users: int
    percentile: float
    avg_score: float
    median_score: float
    updated_at: datetime
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After reviewing all properties identified in the prework analysis, I've identified several areas where properties can be consolidated:

- Properties 1.2 and 1.3 both test exclusion logic and can be combined into a comprehensive exclusion property
- Properties 3.3 and 4.3 both test calculation correctness and can be unified into a general calculation property
- Properties 3.4 and 4.4 both test data persistence and can be combined
- Properties 6.1 and 6.2 both test leaderboard functionality and can be unified
- Properties 9.1, 9.2, 9.3, and 9.4 all test logging behavior and can be consolidated

### Core Properties

**Property 1: Data joining consistency**
*For any* user with data in both internal_users and internal_users_profile collections, joining on username/github_username should produce a complete profile with all required fields populated
**Validates: Requirements 1.1, 1.4**

**Property 2: User exclusion for incomplete data**
*For any* user missing either GitHub scan data or profile information, that user should not appear in any ranking calculations or results
**Validates: Requirements 1.2, 1.3**

**Property 3: Score-based ranking order**
*For any* group of users, ranking by overall_score should produce a descending order where higher scores receive better (lower) rank positions
**Validates: Requirements 2.1, 5.3**

**Property 4: Invalid score handling**
*For any* user with null, zero, or out-of-range overall_score, that user should be excluded from rankings or have their score clamped to valid bounds
**Validates: Requirements 2.2, 2.3**

**Property 5: Percentile calculation accuracy**
*For any* user in a ranking group, their percentile should equal (users_with_lower_score / total_users) × 100, where 100% represents top performance
**Validates: Requirements 5.1**

**Property 6: Tied score handling**
*For any* group of users with identical scores, all users should receive the same rank position
**Validates: Requirements 5.2**

**Property 7: Grouping consistency**
*For any* university or district, all users with that identifier should be grouped together for ranking calculations
**Validates: Requirements 3.1, 4.1**

**Property 8: Ranking completeness**
*For any* ranking calculation, the result should include rank position, percentile, total users, average score, and median score
**Validates: Requirements 3.3, 4.3, 7.3**

**Property 9: Data persistence consistency**
*For any* calculated ranking, the data should be consistently stored in both university_rankings and regional_rankings collections as appropriate
**Validates: Requirements 3.4, 4.4, 10.1**

**Property 10: Leaderboard ordering**
*For any* leaderboard request, results should be ordered by rank position with the best performers first
**Validates: Requirements 6.1, 6.2**

**Property 11: Batch update efficiency**
*For any* ranking update operation, the system should use batch operations and only update affected groups
**Validates: Requirements 8.1, 8.2**

**Property 12: Logging completeness**
*For any* ranking operation, appropriate log entries should be created for start, completion, and any errors encountered
**Validates: Requirements 9.1, 9.2, 9.3, 9.4**

**Property 13: Data synchronization consistency**
*For any* ranking calculation, the results should be synchronized across all relevant collections with consistent timestamps
**Validates: Requirements 10.2, 10.4**

## Error Handling

### Data Validation Errors

- **Missing Profile Data**: Users without complete profile information are excluded from rankings with appropriate logging
- **Invalid Scores**: Out-of-range scores are clamped to valid bounds (0-100) with warnings logged
- **Duplicate Usernames**: System uses most recently updated record and logs warnings about duplicates

### Calculation Errors

- **Empty Groups**: Graceful handling of universities or districts with no eligible users
- **Single User Groups**: Proper assignment of rank 1 and percentile 100% for solo users
- **Mathematical Edge Cases**: Safe division and percentage calculations with fallback values

### System Errors

- **Database Connection Issues**: Retry logic with exponential backoff for transient failures
- **Transaction Failures**: Rollback mechanisms to maintain data consistency
- **Performance Degradation**: Circuit breaker patterns to prevent system overload

## Frontend Display Requirements

### University Rankings Display

The frontend should display university ranking data in the following contexts:

**Developer Dashboard - Rankings Section:**
- University rank position and percentile (e.g., "Rank 5 of 120 students (Top 4.2%)")
- University name and comparison context
- Score comparison with university average and median
- Visual progress indicators for percentile position

**University Leaderboard Page:**
- Top performers in the same university (anonymized except current user)
- University statistics (total students, average score, score distribution)
- Current user's position highlighted in the leaderboard
- Filtering and sorting options for different metrics

**Profile/Statistics View:**
- Detailed university ranking breakdown
- Historical ranking trends (if available)
- Comparison with other universities (aggregated data)

### Regional Rankings Display

**Developer Dashboard - Rankings Section:**
- Regional rank position and percentile (e.g., "Rank 12 of 85 in Tamil Nadu (Top 14.1%)")
- District, state, and region context information
- Score comparison with regional average and median
- Geographic visualization of ranking position

**Regional Leaderboard Page:**
- Top performers in the same district/state (anonymized except current user)
- Regional statistics (total users, average score, score distribution)
- Geographic filtering options (district, state, region)
- Interactive maps showing regional performance (optional)

**Comparative Analytics:**
- Side-by-side university vs regional performance
- Performance gaps and insights
- Recommendations for improvement based on ranking position

### API Response Format for Frontend

```typescript
interface RankingResponse {
  university_ranking?: {
    rank: number;
    total_users: number;
    percentile: number;
    university: string;
    university_short: string;
    avg_score: number;
    median_score: number;
    display_text: string; // "Top 4.2% in MIT"
  };
  regional_ranking?: {
    rank: number;
    total_users: number;
    percentile: number;
    district: string;
    state: string;
    region: string;
    avg_score: number;
    median_score: number;
    display_text: string; // "Top 14.1% in Tamil Nadu"
  };
  user_info: {
    github_username: string;
    name: string;
    overall_score: number;
  };
  last_updated: string;
}
```

### UI/UX Considerations

- **Performance Indicators**: Use visual elements like progress bars, badges, and color coding to make rankings easily digestible
- **Contextual Information**: Always provide context about what the ranking means and how it's calculated
- **Privacy Protection**: Ensure other users' personal information is anonymized in leaderboards
- **Responsive Design**: Rankings should display well on both desktop and mobile devices
- **Real-time Updates**: Consider WebSocket connections for live ranking updates when scores change

## Testing Strategy

### Unit Testing

The system will include comprehensive unit tests for:

- Mathematical calculations (percentiles, rankings, statistics)
- Data validation and sanitization logic
- Error handling and edge cases
- Individual service methods and utilities

### Property-Based Testing

Property-based tests will verify universal properties using **Hypothesis** (Python property-based testing library). Each property-based test will run a minimum of 100 iterations with randomly generated test data.

Key property tests include:

- **Data Joining Properties**: Verify consistent joining behavior across various username formats
- **Ranking Calculation Properties**: Ensure mathematical correctness of percentile and rank calculations
- **Grouping Properties**: Validate consistent grouping behavior for universities and districts
- **Synchronization Properties**: Verify data consistency across collections

### Integration Testing

Integration tests will validate:

- End-to-end ranking calculation workflows
- Database transaction handling and rollback scenarios
- API endpoint responses and error handling
- Cross-collection data consistency
- Frontend-backend integration for ranking displays

### Performance Testing

Performance tests will ensure:

- Batch operations complete within acceptable time limits
- Memory usage remains stable during large dataset processing
- Database query optimization effectiveness
- API response times meet performance requirements
- Frontend rendering performance with large datasets

The testing strategy ensures both correctness through property-based testing and reliability through comprehensive unit and integration testing.