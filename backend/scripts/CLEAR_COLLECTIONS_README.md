# MongoDB Collection Cleaner

Scripts to clear data from MongoDB collections in the `git_evaluator` database.

## Files

- `clear_all_collections.py` - Python script with full functionality
- `clear_collections.bat` - Windows batch wrapper

## Prerequisites

- Python 3.7+
- MongoDB running
- Environment variables configured in `.env`:
  - `MONGODB_URL` - MongoDB connection string
  - `DATABASE_NAME` - Database name (default: `git_evaluator`)

## Usage

### List All Collections

Shows all collections and their document counts:

```bash
# Python
python scripts/clear_all_collections.py list

# Windows
scripts\clear_collections.bat list
```

**Output:**
```
📊 Collections in 'git_evaluator':

   users                                        125 documents
   repositories                               1,234 documents
   scans                                        456 documents
   user_profiles                                125 documents
   fast_scan_cache                               89 documents
   
   TOTAL                                      2,029 documents
   Collections                                    5
```

### Clear All Collections

Deletes ALL data from ALL collections (requires confirmation):

```bash
# Python
python scripts/clear_all_collections.py all

# Windows
scripts\clear_collections.bat all
```

**Confirmation Required:**
```
⚠️  WARNING: This will DELETE ALL DATA from ALL collections!
⚠️  Database: git_evaluator
⚠️  Collections: 15

Type 'DELETE ALL' to confirm: 
```

### Clear Specific Collections

Deletes data from specific collections only:

```bash
# Python
python scripts/clear_all_collections.py specific users,repositories,scans

# Windows
scripts\clear_collections.bat specific users,repositories,scans
```

**Confirmation Required:**
```
⚠️  WARNING: This will DELETE ALL DATA from these collections!

Type 'DELETE' to confirm:
```

## Common Collections

### User Data
- `users` - User accounts and authentication
- `user_profiles` - User profile information
- `user_rankings` - User ranking data

### Repository Data
- `repositories` - Repository information
- `repository_details` - Detailed repository analysis

### Scan Data
- `scans` - Scan results
- `fast_scan_cache` - Quick scan cache (5-minute TTL)
- `analysis_progress` - Analysis progress tracking
- `analysis_state` - Analysis state storage

### HR Data
- `hr_users` - HR user accounts
- `hr_candidates` - Candidate profiles
- `hr_saved_candidates` - Saved candidate lists

### Other
- `sessions` - User sessions
- `oauth_states` - OAuth state tracking

## Safety Features

### Confirmation Required
- **All collections:** Must type `DELETE ALL` exactly
- **Specific collections:** Must type `DELETE` exactly
- No accidental deletions

### Verification
After deletion, the script verifies:
- Document counts are zero
- All collections were cleared successfully

### Error Handling
- Connection errors are caught and reported
- Individual collection errors don't stop the process
- Full error traceback for debugging

## Examples

### Example 1: Clear Cache Only
```bash
python scripts/clear_all_collections.py specific fast_scan_cache
```

### Example 2: Clear All User Data
```bash
python scripts/clear_all_collections.py specific users,user_profiles,user_rankings
```

### Example 3: Clear All Scan Data
```bash
python scripts/clear_all_collections.py specific scans,fast_scan_cache,analysis_progress
```

### Example 4: Fresh Start (Clear Everything)
```bash
python scripts/clear_all_collections.py all
```

## Output Examples

### Successful Deletion
```
🗑️  Starting deletion...

   ✅ users: Deleted 125 documents
   ✅ repositories: Deleted 1,234 documents
   ✅ scans: Deleted 456 documents
   ✅ user_profiles: Deleted 125 documents
   ✅ fast_scan_cache: Deleted 89 documents

✅ Deletion complete!
   Total documents deleted: 2,029
   Collections cleared: 5

🔍 Verifying deletion...
   ✅ users: 0 documents (verified)
   ✅ repositories: 0 documents (verified)
   ✅ scans: 0 documents (verified)
   ✅ user_profiles: 0 documents (verified)
   ✅ fast_scan_cache: 0 documents (verified)

✅ All collections cleared successfully!
```

### Cancelled Deletion
```
⚠️  WARNING: This will DELETE ALL DATA from ALL collections!

Type 'DELETE ALL' to confirm: no

❌ Deletion cancelled
```

## Troubleshooting

### Connection Error
```
❌ Error: [Errno 111] Connection refused
```
**Solution:** Make sure MongoDB is running

### Authentication Error
```
❌ Error: Authentication failed
```
**Solution:** Check `MONGODB_URL` in `.env` file

### Collection Not Found
```
⚠️  Collections not found: invalid_collection
```
**Solution:** Use `list` command to see available collections

## Best Practices

### Before Clearing
1. **Backup important data** if needed
2. **Stop the application** to prevent new data being written
3. **List collections** to see what will be deleted
4. **Use specific collections** instead of clearing all when possible

### After Clearing
1. **Verify deletion** with the `list` command
2. **Restart the application** if it was stopped
3. **Re-scan profiles** to populate data again

### Development Workflow
```bash
# 1. List current data
python scripts/clear_all_collections.py list

# 2. Clear cache for fresh scan
python scripts/clear_all_collections.py specific fast_scan_cache

# 3. Clear test data
python scripts/clear_all_collections.py specific users,scans

# 4. Verify
python scripts/clear_all_collections.py list
```

## Environment Variables

The script uses these environment variables from `.env`:

```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=git_evaluator
```

## Notes

- **TTL Collections:** Some collections like `fast_scan_cache` have TTL indexes and auto-expire
- **Indexes:** Clearing collections does NOT drop indexes
- **Schema:** Collection schemas remain intact
- **Performance:** Deletion is fast (uses `delete_many({})`)

## Security

⚠️ **WARNING:** This script has the power to delete ALL data. Use with caution!

- Never run in production without proper backups
- Always verify the database name before confirming
- Use specific collections when possible
- Keep confirmation strings secure

## Support

If you encounter issues:
1. Check MongoDB is running: `mongosh`
2. Verify connection string in `.env`
3. Check Python dependencies: `pip install motor python-dotenv`
4. Review error traceback for details
