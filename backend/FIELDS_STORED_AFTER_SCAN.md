# Fields Stored in Database After Scanning

## Database Location
- **Cluster**: `online-evaluation`
- **Database**: `git_Evaluator`
- **Collection**: `scores_comparison`

---

## 📋 Complete Field List (15 Root Fields)

### 1. Basic User Information (3 fields)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `username` | string | GitHub username | `"torvalds"` |
| `user_id` | string | Internal user ID | `"external_torvalds"` or `"507f1f77..."` |
| `most_used_language` | string | Most frequently used language | `"Python"` |

---

### 2. Score Fields (4 fields)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `overall_score` | float | Overall developer score (0-100) | `87.5` |
| `avg_flagship_score` | float | Average score of flagship repos | `91.85` |
| `avg_significant_score` | float | Average score of significant repos | `72.3` |
| `last_updated` | datetime | Last update timestamp | `2025-11-15T11:45:05` |

---

### 3. Repository Count Fields (2 fields)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `total_flagship_repos` | int | Count of flagship repositories | `5` |
| `total_significant_repos` | int | Count of significant repositories | `15` |

---

### 4. Flagship Repositories Array (1 field, array of objects)

**Field**: `flagship_repositories`  
**Type**: `array[object]`  
**Max Items**: 10  
**Criteria**: Score >= 70 AND Stars >= 5

#### Each flagship repository contains (7 sub-fields):

```json
{
  "repo_name": "awesome-project",
  "full_name": "user/awesome-project",
  "score": 92.0,
  "language": "Python",
  "stars": 150,
  "description": "An awesome project",
  "url": "https://github.com/user/awesome-project"
}
```

| Sub-field | Type | Description |
|-----------|------|-------------|
| `repo_name` | string | Repository name |
| `full_name` | string | Full name (owner/repo) |
| `score` | float | Repository score |
| `language` | string | Primary language |
| `stars` | int | Star count |
| `description` | string | Repository description |
| `url` | string | GitHub URL |

---

### 5. Significant Repositories Array (1 field, array of objects)

**Field**: `significant_repositories`  
**Type**: `array[object]`  
**Max Items**: 20  
**Criteria**: Score >= 50

#### Each significant repository contains (7 sub-fields):

```json
{
  "repo_name": "good-project",
  "full_name": "user/good-project",
  "score": 65.0,
  "language": "JavaScript",
  "stars": 25,
  "description": "A good project",
  "url": "https://github.com/user/good-project"
}
```

| Sub-field | Type | Description |
|-----------|------|-------------|
| `repo_name` | string | Repository name |
| `full_name` | string | Full name (owner/repo) |
| `score` | float | Repository score |
| `language` | string | Primary language |
| `stars` | int | Star count |
| `description` | string | Repository description |
| `url` | string | GitHub URL |

---

### 6. Metadata Object (1 field, nested object)

**Field**: `metadata`  
**Type**: `object`

#### Metadata contains (13+ sub-fields):

```json
{
  "github_username": "johndoe",
  "name": "John Doe",
  "bio": "Software Developer",
  "location": "San Francisco, CA",
  "company": "Tech Corp",
  "blog": "https://johndoe.com",
  "avatar_url": "https://avatars.githubusercontent.com/...",
  "public_repos": 50,
  "followers": 100,
  "following": 50,
  "total_repositories_analyzed": 50,
  "total_stars": 500,
  "total_forks": 100,
  "top_languages": [
    {"language": "Python", "count": 20},
    {"language": "JavaScript", "count": 15}
  ],
  "github_created_at": "2015-01-01T00:00:00Z",
  "github_updated_at": "2025-11-15T10:00:00Z"
}
```

| Sub-field | Type | Description |
|-----------|------|-------------|
| `github_username` | string | GitHub username |
| `name` | string | Full name |
| `bio` | string | User bio |
| `location` | string | Location |
| `company` | string | Company |
| `blog` | string | Blog URL |
| `avatar_url` | string | Avatar URL |
| `public_repos` | int | Public repository count |
| `followers` | int | Follower count |
| `following` | int | Following count |
| `total_repositories_analyzed` | int | Total repos analyzed |
| `total_stars` | int | Total stars across all repos |
| `total_forks` | int | Total forks across all repos |
| `top_languages` | array[object] | Top 5 programming languages |
| `github_created_at` | string | GitHub account creation date |
| `github_updated_at` | string | Last GitHub profile update |

---

## 📊 Field Count Summary

| Category | Field Count |
|----------|-------------|
| **Root Level Fields** | 15 |
| **Flagship Repo Sub-fields** | 7 per repo (max 10 repos) |
| **Significant Repo Sub-fields** | 7 per repo (max 20 repos) |
| **Metadata Sub-fields** | 13+ |
| **Top Languages Sub-fields** | 2 per language (max 5 languages) |

**Total Possible Fields**: ~100+ fields (depending on number of repos and languages)

---

## 🎯 Complete Example Document

```json
{
  "_id": ObjectId("..."),
  "username": "johndoe",
  "user_id": "external_johndoe",
  "overall_score": 87.5,
  "total_flagship_repos": 3,
  "total_significant_repos": 8,
  "avg_flagship_score": 91.2,
  "avg_significant_score": 68.5,
  "most_used_language": "Python",
  "last_updated": ISODate("2025-11-15T11:45:05.108Z"),
  
  "flagship_repositories": [
    {
      "repo_name": "ml-framework",
      "full_name": "johndoe/ml-framework",
      "score": 95.0,
      "language": "Python",
      "stars": 250,
      "description": "Machine learning framework",
      "url": "https://github.com/johndoe/ml-framework"
    },
    {
      "repo_name": "web-app",
      "full_name": "johndoe/web-app",
      "score": 88.5,
      "language": "JavaScript",
      "stars": 120,
      "description": "Modern web application",
      "url": "https://github.com/johndoe/web-app"
    },
    {
      "repo_name": "api-server",
      "full_name": "johndoe/api-server",
      "score": 90.0,
      "language": "Go",
      "stars": 80,
      "description": "High-performance API server",
      "url": "https://github.com/johndoe/api-server"
    }
  ],
  
  "significant_repositories": [
    {
      "repo_name": "cli-tool",
      "full_name": "johndoe/cli-tool",
      "score": 72.0,
      "language": "Python",
      "stars": 45,
      "description": "Command-line utility",
      "url": "https://github.com/johndoe/cli-tool"
    },
    {
      "repo_name": "data-processor",
      "full_name": "johndoe/data-processor",
      "score": 68.5,
      "language": "Python",
      "stars": 30,
      "description": "Data processing pipeline",
      "url": "https://github.com/johndoe/data-processor"
    }
    // ... up to 20 repos
  ],
  
  "metadata": {
    "github_username": "johndoe",
    "name": "John Doe",
    "bio": "Full-stack developer passionate about ML",
    "location": "San Francisco, CA",
    "company": "Tech Corp",
    "blog": "https://johndoe.com",
    "avatar_url": "https://avatars.githubusercontent.com/u/123456",
    "public_repos": 50,
    "followers": 150,
    "following": 75,
    "total_repositories_analyzed": 50,
    "total_stars": 525,
    "total_forks": 120,
    "top_languages": [
      {"language": "Python", "count": 20},
      {"language": "JavaScript", "count": 15},
      {"language": "Go", "count": 8},
      {"language": "TypeScript", "count": 5},
      {"language": "Rust", "count": 2}
    ],
    "github_created_at": "2015-01-01T00:00:00Z",
    "github_updated_at": "2025-11-15T10:00:00Z"
  }
}
```

---

## 🔍 Field Validation Rules

| Field | Required | Unique | Indexed | Validation |
|-------|----------|--------|---------|------------|
| `username` | ✅ Yes | ✅ Yes | ✅ Yes | Non-empty string |
| `user_id` | ✅ Yes | ❌ No | ✅ Yes | Non-empty string |
| `overall_score` | ✅ Yes | ❌ No | ✅ Yes (DESC) | Float, 0-100 |
| `flagship_repositories` | ✅ Yes | ❌ No | ❌ No | Array, max 10 items |
| `significant_repositories` | ✅ Yes | ❌ No | ❌ No | Array, max 20 items |
| `metadata` | ✅ Yes | ❌ No | ❌ No | Object |
| `last_updated` | ✅ Yes | ❌ No | ✅ Yes (DESC) | Valid datetime |

---

## 📈 Storage Size Estimate

### Per User Document

| Component | Estimated Size |
|-----------|----------------|
| Basic fields | ~200 bytes |
| Flagship repos (10 max) | ~2 KB |
| Significant repos (20 max) | ~4 KB |
| Metadata | ~1 KB |
| **Total per user** | **~7 KB** |

### For 1000 Users
- **Total Storage**: ~7 MB
- **With indexes**: ~10 MB

---

## 🎯 Quick Reference

### What Gets Stored?
✅ Username and user ID  
✅ Overall score (0-100)  
✅ Top 10 flagship repositories (score >= 70, stars >= 5)  
✅ Top 20 significant repositories (score >= 50)  
✅ User profile metadata (name, bio, location, etc.)  
✅ Repository statistics (total stars, forks, etc.)  
✅ Top 5 programming languages  
✅ Average scores for flagship and significant repos  
✅ Last updated timestamp  

### What Doesn't Get Stored?
❌ Full repository code  
❌ Commit history  
❌ All repositories (only top scored ones)  
❌ Private repository data  
❌ Sensitive user information  

---

## 🔧 How to Inspect

```bash
# Run inspection script
cd backend
python inspect_stored_scores.py
```

This will show:
- Complete document structure
- All fields with types and values
- Sample data from actual stored documents

---

## 📚 Related Documentation

- **Complete Field Documentation**: `DATABASE_FIELDS_DOCUMENTATION.md`
- **Score Storage Coverage**: `SCORE_STORAGE_COVERAGE.md`
- **Implementation Details**: `SCORE_STORAGE_IMPLEMENTATION.md`
