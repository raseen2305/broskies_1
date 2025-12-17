# PR/Issue/Roadmap Data Model Migration

## Overview
This migration adds support for Pull Request, Issue, and Roadmap data to existing repository documents in the database.

## Requirements
- Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.3

## New Fields Added

### Repository Model Enhancements

#### 1. Pull Requests Field (`pull_requests`)
Type: `Optional[PRStatistics]`

Structure:
```python
{
    "total": int,
    "open": int,
    "closed": int,
    "merged": int,
    "recent_prs": List[PullRequest],
    "avg_time_to_merge_hours": Optional[float],
    "avg_additions": Optional[float],
    "avg_deletions": Optional[float]
}
```

#### 2. Issues Field (`issues`)
Type: `Optional[IssueStatistics]`

Structure:
```python
{
    "total": int,
    "open": int,
    "closed": int,
    "recent_issues": List[Issue],
    "avg_time_to_close_hours": Optional[float],
    "labels_distribution": Dict[str, int]
}
```

#### 3. Roadmap Field (`roadmap`)
Type: `Optional[Roadmap]`

Structure:
```python
{
    "milestones": List[Milestone],
    "projects": List[Project],
    "total_milestones": int,
    "open_milestones": int,
    "closed_milestones": int,
    "total_projects": int,
    "open_projects": int,
    "closed_projects": int
}
```

## Migration Script

### Location
`backend/app/database/migrate_pr_issue_roadmap.py`

### Features
- Migrates `scan_results` collection
- Migrates `repositories` collection
- Migrates `detailed_repositories` collection
- Adds default `None` values for missing fields
- Includes verification step
- Provides detailed statistics

### Running the Migration

#### Option 1: Direct Execution
```bash
cd backend
python -m app.database.migrate_pr_issue_roadmap
```

#### Option 2: Programmatic Execution
```python
from app.database.migrate_pr_issue_roadmap import run_migration
import asyncio

result = asyncio.run(run_migration())
print(result)
```

### Migration Process

1. **Scan Results Migration**
   - Finds all scan results
   - Iterates through repositories in each scan
   - Adds missing fields with `None` values
   - Updates scan document with migrated repositories

2. **Repositories Collection Migration**
   - Finds repositories missing new fields
   - Adds `pull_requests`, `issues`, and `roadmap` fields
   - Sets values to `None` by default

3. **Detailed Repositories Migration**
   - Same process as repositories collection
   - Ensures consistency across all repository collections

4. **Verification**
   - Counts total documents in each collection
   - Counts documents with new fields
   - Reports missing fields

### Expected Output

```
============================================================
Starting PR/Issue/Roadmap Migration
============================================================
Starting migration of scan_results collection...
Updated scan scan_id_1 with 10 repositories
Updated scan scan_id_2 with 5 repositories
Scan results migration completed: {
    'total_scans': 2,
    'scans_updated': 2,
    'repositories_updated': 15,
    'errors': 0
}

Starting migration of repositories collection...
Repositories collection migration completed: {
    'total_repositories': 20,
    'repositories_updated': 20,
    'errors': 0
}

Starting migration of detailed_repositories collection...
Detailed repositories migration completed: {
    'total_repositories': 15,
    'repositories_updated': 15,
    'errors': 0
}

============================================================
Migration Summary:
  Total documents updated: 37
  Total errors: 0
  Status: completed
============================================================

Verifying migration...
Verification completed:
  Scan results: 2/2 migrated
  Repositories: 20/20 migrated
  Detailed repositories: 15/15 migrated
```

## Backward Compatibility

### Safe Migration
- Adds fields with `None` values
- Does not remove or modify existing fields
- Existing queries continue to work
- New scans will populate these fields automatically

### Handling Null Values
When querying repositories, check for null values:

```python
# Check if PR data exists
if repository.get('pull_requests'):
    pr_stats = repository['pull_requests']
    total_prs = pr_stats['total']
else:
    # Handle legacy repository without PR data
    total_prs = 0
```

## Data Population

### Automatic Population
New scans automatically populate PR/Issue/Roadmap data:
- Fetched during repository analysis
- Stored in scan results
- Available immediately after scan completion

### Manual Population
To populate data for existing repositories:

```python
from app.services.github_api_service import GitHubAPIService
from app.database import get_database

async def populate_pr_data(repo_full_name):
    github_api = GitHubAPIService(settings.GITHUB_TOKEN)
    owner, repo = repo_full_name.split('/')
    
    # Fetch PRs
    prs = await github_api.get_pull_requests(owner, repo, state='all')
    
    # Calculate statistics
    pr_statistics = {
        'total': len(prs),
        'open': len([pr for pr in prs if pr['state'] == 'open']),
        # ... more calculations
    }
    
    # Update database
    db = await get_database()
    await db.repositories.update_one(
        {'full_name': repo_full_name},
        {'$set': {'pull_requests': pr_statistics}}
    )
```

## Testing

### Test Script
`backend/test_pr_issue_roadmap_migration.py`

### Running Tests
```bash
python backend/test_pr_issue_roadmap_migration.py
```

### Test Coverage
- ✅ Scan results migration
- ✅ Repositories collection migration
- ✅ Detailed repositories migration
- ✅ Full migration workflow
- ✅ Verification process
- ✅ Error handling

## Rollback

If needed, remove the new fields:

```python
from app.database import get_database

async def rollback_migration():
    db = await get_database()
    
    # Remove fields from scan_results
    await db.scan_results.update_many(
        {},
        {
            '$unset': {
                'repositories.$[].pull_requests': '',
                'repositories.$[].issues': '',
                'repositories.$[].roadmap': ''
            }
        }
    )
    
    # Remove fields from repositories
    await db.repositories.update_many(
        {},
        {
            '$unset': {
                'pull_requests': '',
                'issues': '',
                'roadmap': ''
            }
        }
    )
    
    # Remove fields from detailed_repositories
    await db.detailed_repositories.update_many(
        {},
        {
            '$unset': {
                'pull_requests': '',
                'issues': '',
                'roadmap': ''
            }
        }
    )
```

## Performance Considerations

### Migration Performance
- Processes documents in batches
- Uses bulk updates where possible
- Minimal memory footprint
- Can run on production without downtime

### Query Performance
- New fields are optional
- No impact on existing queries
- Indexed fields remain unchanged
- Consider adding indexes for PR/Issue queries:

```python
# Add indexes for better query performance
await db.repositories.create_index([
    ('pull_requests.total', 1),
    ('issues.total', 1)
])
```

## Monitoring

### Migration Logs
Monitor migration progress:
```bash
tail -f logs/migration.log
```

### Verification
After migration, verify data integrity:
```python
from app.database.migrate_pr_issue_roadmap import PRIssueRoadmapMigration

migrator = PRIssueRoadmapMigration(db)
verification = await migrator.verify_migration()
print(verification)
```

## Troubleshooting

### Common Issues

#### Issue: Migration fails with connection error
**Solution:** Check database connection settings in `.env`

#### Issue: Some documents not migrated
**Solution:** Run verification to identify missing documents, then re-run migration

#### Issue: Memory issues with large collections
**Solution:** Modify migration script to process in smaller batches

## Next Steps

After migration:
1. ✅ Verify all documents migrated successfully
2. ✅ Run new scans to populate PR/Issue/Roadmap data
3. ✅ Update frontend to display new data
4. ✅ Monitor API rate limits when fetching PR/Issue data
5. ✅ Consider caching strategies for frequently accessed data

## Support

For issues or questions:
- Check logs in `logs/migration.log`
- Review verification results
- Contact development team
