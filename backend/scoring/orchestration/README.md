# Stage 1 Quick Scan Orchestration

This module implements the Stage 1 quick scan orchestration for the GitHub Developer Scoring System.

## Overview

The scan orchestrator coordinates the complete Stage 1 workflow:

1. **Fetch Data** (0.5s): Single GraphQL query to get user + all repositories
2. **Calculate Importance** (0.25s): Parallel importance score calculation
3. **Categorize** (instant): Classify repositories as flagship/significant/supporting
4. **Store Results** (0.2s): Parallel database writes

**Total Target**: <1 second

## Components

### ScanOrchestrator

Main orchestration service that coordinates the entire Stage 1 workflow.

**Key Methods**:

- `execute_quick_scan()`: Execute complete Stage 1 scan
- `select_repositories_for_analysis()`: Select repos for Stage 2

### ScanStorageService

Handles database storage for scan results with parallel writes.

**Key Methods**:

- `store_scan_results()`: Store user profile and repositories
- `get_user_repositories()`: Retrieve repositories
- `get_repositories_for_analysis()`: Get repos for Stage 2
- `update_repository_analysis()`: Update with Stage 2 results
- `get_scan_summary()`: Get scan statistics

## Usage

### Basic Usage (Without Database)

```python
from scoring.orchestration.scan_orchestrator import ScanOrchestrator

# Create orchestrator
orchestrator = ScanOrchestrator()

# Execute scan
result = await orchestrator.execute_quick_scan(
    username='octocat',
    token='ghp_xxxxx',
    store_results=False
)

print(f"Scan completed in {result['scan_time']}s")
print(f"Repositories: {result['summary']['total']}")
```

### Production Usage (With Database)

```python
from app.db_connection import get_database
from scoring.orchestration.scan_orchestrator import ScanOrchestrator

# Get database connection
database = await get_database()

# Create orchestrator with database
orchestrator = ScanOrchestrator(database=database)

# Execute scan with storage
result = await orchestrator.execute_quick_scan(
    username='octocat',
    token='ghp_xxxxx',
    user_id='user123',
    store_results=True
)

# Results are automatically stored in database
```

### FastAPI Integration

```python
from fastapi import APIRouter, Depends, HTTPException
from app.db_connection import get_database
from scoring.orchestration.scan_orchestrator import ScanOrchestrator

router = APIRouter()

@router.post("/api/scan/quick-scan")
async def quick_scan(
    username: str,
    token: str,
    user_id: str,
    database = Depends(get_database)
):
    orchestrator = ScanOrchestrator(database=database)
    
    result = await orchestrator.execute_quick_scan(
        username=username,
        token=token,
        user_id=user_id,
        store_results=True
    )
    
    return {
        'success': True,
        'user': result['user'],
        'summary': result['summary'],
        'scan_time': result['scan_time']
    }
```

## Data Flow

```
User Request
    │
    ▼
┌─────────────────────────────────────┐
│ 1. GraphQL Query (0.5s)             │
│    - Fetch user profile             │
│    - Fetch all repositories         │
│    - Get metadata                   │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 2. Calculate Importance (0.25s)     │
│    - Parallel processing            │
│    - Community score (40%)          │
│    - Activity score (30%)           │
│    - Size score (20%)               │
│    - Quality score (10%)            │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 3. Categorize (instant)             │
│    - Flagship: score >= 70          │
│    - Significant: score 50-69       │
│    - Supporting: score < 50         │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 4. Store Results (0.2s)             │
│    - user_profiles collection       │
│    - repositories collection        │
│    - Parallel writes                │
└─────────────────────────────────────┘
    │
    ▼
Return Results (<1s total)
```

## Database Schema

### user_profiles Collection

```javascript
{
  user_id: String,
  github_username: String,
  name: String,
  bio: String,
  avatar_url: String,
  email: String,
  location: String,
  company: String,
  followers: Number,
  following: Number,
  public_repos: Number,
  scan_completed: Boolean,
  scanned_at: Date,
  flagship_count: Number,
  significant_count: Number,
  supporting_count: Number,
  created_at: Date,
  updated_at: Date
}
```

### repositories Collection

```javascript
{
  user_id: String,
  github_id: String,
  name: String,
  full_name: String,
  description: String,
  stars: Number,
  forks: Number,
  size: Number,
  language: String,
  languages: Object,
  topics: Array,
  importance_score: Number,  // 0-100
  category: String,          // flagship|significant|supporting
  analyzed: Boolean,
  analyzed_at: Date,
  created_at: Date,
  updated_at: Date
}
```

## Performance

### Target Metrics

- **Total Time**: <1 second
- **GraphQL Fetch**: <0.5s
- **Importance Calculation**: <0.25s
- **Database Storage**: <0.2s

### Optimization Techniques

1. **Single GraphQL Query**: Fetch everything in one request
2. **Parallel Processing**: Calculate importance scores concurrently
3. **Parallel Writes**: Store user and repositories simultaneously
4. **Bulk Operations**: Use MongoDB bulk writes for repositories

### Performance Monitoring

The orchestrator automatically:
- Tracks total execution time
- Logs warnings if target is exceeded
- Reports component timings
- Monitors storage performance

## Repository Selection

For Stage 2 deep analysis, repositories are selected as follows:

1. Include all **Flagship** repositories (score >= 70)
2. Include all **Significant** repositories (score 50-69)
3. Exclude all **Supporting** repositories (score < 50)
4. Limit to maximum 15 repositories
5. If >15, select top 15 by importance score

```python
# Select repositories for Stage 2
selected = orchestrator.select_repositories_for_analysis(repositories)

# selected will contain:
# - All flagship repos
# - All significant repos
# - Maximum 15 total
# - Sorted by importance score
```

## Error Handling

The orchestrator handles errors gracefully:

- **GraphQL Errors**: Raises RuntimeError with details
- **Calculation Errors**: Logs error, assigns default score (0.0)
- **Storage Errors**: Raises RuntimeError with details
- **Validation Errors**: Raises ValueError for invalid input

## Testing

Run the test suite:

```bash
# Manual tests
python backend/tests/scoring/test_scan_manual.py

# View examples
python backend/tests/scoring/example_usage.py
```

## Configuration

Configuration is managed in `scoring/config.py`:

```python
# Importance Score Weights
IMPORTANCE_COMMUNITY_WEIGHT = 0.40
IMPORTANCE_ACTIVITY_WEIGHT = 0.30
IMPORTANCE_SIZE_WEIGHT = 0.20
IMPORTANCE_QUALITY_WEIGHT = 0.10

# Categorization Thresholds
FLAGSHIP_THRESHOLD = 70.0
SIGNIFICANT_THRESHOLD = 50.0

# Performance Targets
STAGE1_TARGET_SECONDS = 1.0

# Analysis Limits
MAX_REPOS_TO_ANALYZE = 15
```

## Requirements

- Python 3.8+
- motor (async MongoDB driver)
- aiohttp (async HTTP client)
- MongoDB 4.0+

## Related Modules

- `scoring/github/graphql_service.py`: GraphQL API client
- `scoring/scoring/importance_scorer.py`: Importance calculation
- `scoring/storage/scan_storage.py`: Database storage
- `scoring/config.py`: Configuration

## Next Steps

After Stage 1 completes:

1. User sees categorized repositories
2. User clicks "Analyze Repositories"
3. Stage 2 deep analysis begins
4. Selected repositories are analyzed for ACID scores
5. Overall score is calculated
6. Rankings are updated

See `scoring/orchestration/analysis_orchestrator.py` for Stage 2 implementation.
