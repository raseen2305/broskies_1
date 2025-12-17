# MongoDB Cleaner - Quick Reference

## Commands

```bash
# List all collections
python scripts/clear_all_collections.py list

# Clear all collections (requires: DELETE ALL)
python scripts/clear_all_collections.py all

# Clear specific collections (requires: DELETE)
python scripts/clear_all_collections.py specific collection1,collection2
```

## Common Collections

```bash
# Cache only
python scripts/clear_all_collections.py specific fast_scan_cache

# User data
python scripts/clear_all_collections.py specific users,user_profiles,user_rankings

# Scan data
python scripts/clear_all_collections.py specific scans,fast_scan_cache,analysis_progress

# Repository data
python scripts/clear_all_collections.py specific repositories,repository_details

# HR data
python scripts/clear_all_collections.py specific hr_users,hr_candidates,hr_saved_candidates
```

## Workflow

```bash
# 1. Check current state
python scripts/clear_all_collections.py list

# 2. Clear what you need
python scripts/clear_all_collections.py specific fast_scan_cache

# 3. Verify
python scripts/clear_all_collections.py list
```

## Safety

- ✅ Requires confirmation
- ✅ Shows counts before deletion
- ✅ Verifies after deletion
- ⚠️ No undo - be careful!
