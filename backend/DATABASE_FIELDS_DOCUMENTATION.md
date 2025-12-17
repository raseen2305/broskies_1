# Database Fields Documentation

## Collection: `scores_comparison`
**Database**: `git_Evaluator`  
**Purpose**: Store user scores for HR to query and sort developer profiles

---

## Complete Field Structure

### Root Level Fields

| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| `username` | string | GitHub username | `"torvalds"` |
| `user_id` | string | Internal user ID | `"external_torvalds"` |
| `overall_score` | float | Overall developer score (0-100) | `95.8` |
| `total_flagship_repos` | int | Count of flagship repositories | `2` |
| `total_significant_repos` | int | Count of significant repositories | `1` |
| `avg_flagship_score` | float | Average score of flagship repos | `91.85` |
| `avg_significant_score` | float | Average score of significant repos | `72.0` |
| `last_updated` | datetime | Last update timestamp | `2025-11-15T11:45:05` |
| `most_used_language` | string | Most frequently used language | `"C"` |

---

### Flagship Repositories Array

**Field**: `flagship_repositories`  
**Type**: `array[object]`  
**Criteria**: Score >= 70 AND Stars >= 5  
**Limit**: Top 10 repositories

#### Object Structure:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `repo_name` | string | Repository name | `"linux"` |
| `full_name` | string | Full name (owner/repo) | `"torvalds/linux"` |
| `score` | float | Repository score | `98.5` |
| `language` | string | Primary language | `"C"` |
| `stars` | int | Star count | `180000` |
| `description` | string | Repository description | `"Linux kernel source tree"` |
| `url` | string | GitHub URL | `"https://github.com/torvalds/linux"` |

**Example**:
```json
{
  "repo_name": "linux",
  "full_name": "torvalds/linux",
  "score": 98.5,
  "language": "C",
  "stars": 180000,
  "description": "Linux kernel source tree",
  "url": "https://github.com/torvalds/linux"
}
```

---

### Significant Repositories Array

**Field**: `significant_repositories`  
**Type**: `array[object]`  
**Criteria**: Score >= 50  
**Limit**: Top 20 repositories

#### Object Structure:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `repo_name` | string | Repository name | `"test-tlb"` |
| `full_name` | string | Full name (owner/repo) | `"torvalds/test-tlb"` |
| `score` | float | Repository score | `72.0` |
| `language` | string | Primary language | `"C"` |
| `stars` | int | Star count | `150` |
| `description` | string | Repository description | `"TLB testing"` |
| `url` | string | GitHub URL | `"https://github.com/torvalds/test-tlb"` |

**Example**:
```json
{
  "repo_name": "test-tlb",
  "full_name": "torvalds/test-tlb",
  "score": 72.0,
  "language": "C",
  "stars": 150,
  "description": "TLB testing",
  "url": "https://github.com/torvalds/test-tlb"
}
```

---

### Metadata Object

**Field**: `metadata`  
**Type**: `object`  
**Purpose**: Store user profile information and statistics

#### Object Structure:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `github_username` | string | GitHub username | `"torvalds"` |
| `name` | string | Full name | `"Linus Torvalds"` |
| `bio` | string | User bio | `"Creator of Linux and Git"` |
| `location` | string | Location | `"Portland, OR"` |
| `company` | string | Company | `"Linux Foundation"` |
| `blog` | string | Blog URL | `"https://example.com"` |
| `avatar_url` | string | Avatar URL | `"https://avatars.githubusercontent.com/..."` |
| `public_repos` | int | Public repository count | `8` |
| `followers` | int | Follower count | `150000` |
| `following` | int | Following count | `0` |
| `total_repositories_analyzed` | int | Total repos analyzed | `8` |
| `total_stars` | int | Total stars across all repos | `185000` |
| `total_forks` | int | Total forks across all repos | `55000` |
| `top_languages` | array[object] | Top programming languages | See below |
| `github_created_at` | string | GitHub account creation date | `"2011-09-03T15:26:22Z"` |
| `github_updated_at` | string | Last GitHub profile update | `"2025-11-15T10:00:00Z"` |

#### Top Languages Array Structure:

```json
{
  "language": "C",
  "count": 5
}
```

**Complete Metadata Example**:
```json
{
  "github_username": "torvalds",
  "name": "Linus Torvalds",
  "bio": "Creator of Linux and Git",
  "location": "Portland, OR",
  "company": "Linux Foundation",
  "total_repositories_analyzed": 8,
  "total_stars": 185000,
  "total_forks": 55000,
  "top_languages": [
    {"language": "C", "count": 5},
    {"language": "C++", "count": 2}
  ]
}
```

---

## Complete Document Example

```json
{
  "username": "torvalds",
  "user_id": "external_torvalds",
  "overall_score": 95.8,
  "flagship_repositories": [
    {
      "repo_name": "linux",
      "full_name": "torvalds/linux",
      "score": 98.5,
      "language": "C",
      "stars": 180000,
      "description": "Linux kernel source tree",
      "url": "https://github.com/torvalds/linux"
    },
    {
      "repo_name": "subsurface",
      "full_name": "torvalds/subsurface",
      "score": 85.2,
      "language": "C++",
      "stars": 2500,
      "description": "Subsurface divelog",
      "url": "https://github.com/torvalds/subsurface"
    }
  ],
  "significant_repositories": [
    {
      "repo_name": "test-tlb",
      "full_name": "torvalds/test-tlb",
      "score": 72.0,
      "language": "C",
      "stars": 150,
      "description": "TLB testing",
      "url": "https://github.com/torvalds/test-tlb"
    }
  ],
  "metadata": {
    "github_username": "torvalds",
    "name": "Linus Torvalds",
    "bio": "Creator of Linux and Git",
    "location": "Portland, OR",
    "company": "Linux Foundation",
    "total_repositories_analyzed": 8,
    "total_stars": 185000,
    "total_forks": 55000,
    "top_languages": [
      {"language": "C", "count": 5},
      {"language": "C++", "count": 2}
    ]
  },
  "last_updated": "2025-11-15T11:45:05.108000",
  "total_flagship_repos": 2,
  "total_significant_repos": 1,
  "avg_flagship_score": 91.85,
  "avg_significant_score": 72.0,
  "most_used_language": "C"
}
```

---

## Indexes

The collection has the following indexes for efficient querying:

| Index | Type | Purpose |
|-------|------|---------|
| `overall_score` | Descending | Sort users by score |
| `username` | Unique | Fast user lookup |
| `user_id` | Standard | User ID lookup |
| `last_updated` | Descending | Filter by date |

---

## Query Examples

### Get Top 10 Developers
```javascript
db.scores_comparison.find()
  .sort({ overall_score: -1 })
  .limit(10)
```

### Get Developers with Score 80-90
```javascript
db.scores_comparison.find({
  overall_score: { $gte: 80, $lte: 90 }
}).sort({ overall_score: -1 })
```

### Get Specific User
```javascript
db.scores_comparison.findOne({ username: "torvalds" })
```

### Get Users by Language
```javascript
db.scores_comparison.find({
  "metadata.top_languages.language": "Python"
}).sort({ overall_score: -1 })
```

---

## API Endpoints

### Get Top Users
```bash
GET /api/scores/top-users?limit=100
```

### Get Specific User
```bash
GET /api/scores/user/torvalds
```

### Get Users by Score Range
```bash
GET /api/scores/by-score-range?min_score=80&max_score=90
```

### Get Statistics
```bash
GET /api/scores/statistics
```

---

## Field Validation Rules

| Field | Required | Validation |
|-------|----------|------------|
| `username` | Yes | Non-empty string, unique |
| `user_id` | Yes | Non-empty string |
| `overall_score` | Yes | Float, 0-100 |
| `flagship_repositories` | Yes | Array, max 10 items |
| `significant_repositories` | Yes | Array, max 20 items |
| `metadata` | Yes | Object with required fields |
| `last_updated` | Yes | Valid datetime |

---

## Notes

- **Flagship Repos**: High-quality repositories (score >= 70, stars >= 5)
- **Significant Repos**: Good repositories (score >= 50)
- **Overall Score**: Weighted average of top 15 repositories
- **Automatic Updates**: Scores updated after each scan/analysis
- **Non-Blocking**: Score storage failures don't affect scans

---

## Inspection Script

To inspect the database fields:

```bash
cd backend
python inspect_stored_scores.py
```

This will show:
- Sample document structure
- All fields with types
- All users in collection
- Complete field documentation
