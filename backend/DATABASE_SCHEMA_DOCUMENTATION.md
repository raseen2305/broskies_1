# GitHub Comprehensive Database Schema Documentation

## Overview

This document describes the comprehensive database schema for the GitHub integration system. The schema is designed to store detailed GitHub user profiles, repository analysis, contribution data, and comprehensive scan results.

## Database Structure

### Core Collections

#### 1. Users Collection (`users`)
**Purpose**: Store basic user account information

```javascript
{
  _id: ObjectId,
  email: "user@example.com",
  github_username: "username",
  github_token: "encrypted_token", // Optional
  user_type: "developer", // "developer" or "hr"
  created_at: ISODate,
  last_scan: ISODate, // Optional
  profile_visibility: "public", // "public" or "private"
  is_active: true
}
```

**Indexes**:
- `email` (unique)
- `github_username`
- `user_type`
- `created_at` (descending)
- `last_scan` (descending)
- `is_active`

#### 2. HR Users Collection (`hr_users`)
**Purpose**: Store HR user information

```javascript
{
  _id: ObjectId,
  email: "hr@company.com",
  company: "Company Name",
  role: "Technical Recruiter",
  hiring_needs: "Full-stack developers", // Optional
  created_at: ISODate,
  access_level: "basic", // "basic", "premium", "enterprise"
  is_active: true
}
```

**Indexes**:
- `email` (unique)
- `company`
- `access_level`
- `created_at` (descending)

#### 3. GitHub User Profiles Collection (`github_user_profiles`)
**Purpose**: Store comprehensive GitHub profile data

```javascript
{
  _id: ObjectId,
  user_id: "user_object_id", // Reference to users collection
  login: "github_username",
  github_id: 12345678,
  name: "Full Name", // Optional
  email: "public@email.com", // Optional
  bio: "Developer bio", // Optional
  company: "@company", // Optional
  location: "City, Country", // Optional
  blog: "https://blog.com", // Optional
  twitter_username: "twitter_handle", // Optional
  public_repos: 25,
  public_gists: 5,
  followers: 100,
  following: 50,
  avatar_url: "https://avatars.githubusercontent.com/...",
  html_url: "https://github.com/username",
  hireable: true, // Optional
  github_created_at: ISODate,
  github_updated_at: ISODate,
  last_updated: ISODate,
  data_freshness: ISODate
}
```

**Indexes**:
- `user_id` (unique)
- `login` (unique)
- `github_id` (unique)
- `last_updated` (descending)
- `data_freshness` (descending)
- `public_repos` (descending)
- `followers` (descending)
- Text search on `name`, `bio`, `company`, `location`

### Repository Collections

#### 4. Basic Repositories Collection (`repositories`)
**Purpose**: Store basic repository information

```javascript
{
  _id: ObjectId,
  user_id: "user_object_id",
  github_id: 123456789,
  name: "repository-name",
  full_name: "username/repository-name",
  description: "Repository description", // Optional
  language: "JavaScript", // Optional
  languages: {
    "JavaScript": 15420,
    "CSS": 2341,
    "HTML": 1205
  },
  stars: 42,
  forks: 7,
  size: 1024, // KB
  created_at: ISODate,
  updated_at: ISODate,
  pushed_at: ISODate, // Optional
  is_fork: false,
  is_private: false,
  topics: ["web", "frontend", "react"],
  license: "MIT", // Optional
  default_branch: "main",
  clone_url: "https://github.com/username/repo.git",
  html_url: "https://github.com/username/repo"
}
```

**Indexes**:
- `user_id`
- `github_id` (unique)
- `full_name` (unique)
- `name`
- `language`
- `stars` (descending)
- `forks` (descending)
- `created_at` (descending)
- `updated_at` (descending)
- `is_private`
- `is_fork`
- `topics`
- Compound: `user_id` + `name` (unique)
- Text search on `name`, `description`, `topics`

#### 5. Detailed Repositories Collection (`detailed_repositories`)
**Purpose**: Store comprehensive repository analysis

```javascript
{
  _id: ObjectId,
  user_id: "user_object_id",
  github_id: 123456789,
  // ... all basic repository fields ...
  
  // Enhanced analysis data
  code_analysis: {
    total_files: 45,
    total_lines: 2500,
    code_lines: 2000,
    comment_lines: 300,
    blank_lines: 200,
    function_count: 25,
    class_count: 8,
    complexity_score: 7.5,
    language_breakdown: {
      "JavaScript": {
        name: "JavaScript",
        bytes: 15420,
        percentage: 65.2,
        files_count: 12,
        complexity_score: 6.8
      }
    },
    documentation_coverage: 85.0,
    test_coverage: 72.0,
    maintainability_index: 78.5,
    security_analysis: {
      vulnerability_count: 0,
      security_score: 95.0,
      issues: [],
      dependencies_analyzed: 15,
      outdated_dependencies: 2,
      security_best_practices: {
        has_security_md: true,
        has_dependabot: false,
        has_code_scanning: true
      }
    }
  },
  
  acid_scores: {
    atomicity: 8.5,
    consistency: 7.2,
    isolation: 6.8,
    durability: 9.1,
    overall: 7.9,
    detailed_breakdown: {
      // Detailed scoring explanation
    },
    scoring_methodology: "enhanced_v2",
    confidence_score: 0.85
  },
  
  commit_history: [
    {
      sha: "abc123...",
      message: "Add new feature",
      author_name: "Developer Name",
      author_email: "dev@email.com",
      author_date: ISODate,
      committer_name: "Developer Name",
      committer_email: "dev@email.com",
      committer_date: ISODate,
      additions: 25,
      deletions: 5,
      changed_files: 3,
      url: "https://github.com/user/repo/commit/abc123"
    }
  ],
  
  contributors: [
    {
      login: "contributor1",
      id: 12345,
      avatar_url: "https://avatars.githubusercontent.com/...",
      contributions: 42,
      type: "User"
    }
  ],
  
  total_commits: 156,
  last_analyzed: ISODate,
  analysis_version: "comprehensive_v1",
  analysis_duration: 45.2 // seconds
}
```

**Indexes**:
- All basic repository indexes
- `last_analyzed` (descending)
- `analysis_version`
- `acid_scores.overall` (descending)
- `code_analysis.total_lines` (descending)
- `code_analysis.complexity_score` (descending)
- `total_commits` (descending)
- Compound: `is_private` + `user_id`

### Analysis Collections

#### 6. Repository Evaluations Collection (`evaluations`)
**Purpose**: Store repository evaluation results

```javascript
{
  _id: ObjectId,
  repo_id: "repository_object_id",
  user_id: "user_object_id",
  acid_score: {
    atomicity: 8.5,
    consistency: 7.2,
    isolation: 6.8,
    durability: 9.1,
    overall: 7.9
  },
  quality_metrics: {
    readability: 8.2,
    maintainability: 7.5,
    security: 9.0,
    test_coverage: 72.0,
    documentation: 85.0
  },
  language_stats: {
    "JavaScript": 15420,
    "CSS": 2341
  },
  complexity_score: 7.5,
  best_practices_score: 8.1,
  file_count: 45,
  total_lines: 2500,
  created_at: ISODate
}
```

**Indexes**:
- `repo_id`
- `user_id`
- `created_at` (descending)
- `acid_score.overall` (descending)
- `quality_metrics.maintainability` (descending)
- `complexity_score` (descending)
- Compound: `user_id` + `repo_id`

#### 7. Contribution Calendars Collection (`contribution_calendars`)
**Purpose**: Store GitHub contribution calendar data

```javascript
{
  _id: ObjectId,
  user_id: "user_object_id",
  github_username: "username",
  total_contributions: 1247,
  contribution_days: [
    {
      date: "2024-01-01",
      contribution_count: 5,
      level: 2 // 0-4 intensity level
    }
  ],
  current_streak: 15,
  longest_streak: 45,
  most_active_day: "Tuesday",
  contribution_patterns: {
    "Monday": 120,
    "Tuesday": 180,
    // ... other days
  },
  weekly_average: 24.0,
  monthly_totals: {
    "2024-01": 89,
    "2024-02": 76,
    // ... other months
  },
  calendar_year: 2024,
  last_updated: ISODate,
  data_source: "graphql"
}
```

**Indexes**:
- `user_id`
- `github_username`
- `calendar_year`
- `total_contributions` (descending)
- `current_streak` (descending)
- `longest_streak` (descending)
- `last_updated` (descending)
- Compound: `user_id` + `calendar_year` (unique)

#### 8. Pull Request Analysis Collection (`pull_request_analysis`)
**Purpose**: Store pull request analysis data

```javascript
{
  _id: ObjectId,
  repository_id: "repository_object_id",
  user_id: "user_object_id",
  pull_requests: [
    {
      id: 123,
      number: 45,
      title: "Add new feature",
      body: "Description of changes",
      state: "merged", // "open", "closed", "merged"
      created_at: ISODate,
      updated_at: ISODate,
      closed_at: ISODate,
      merged_at: ISODate,
      author_login: "developer",
      author_id: 12345,
      additions: 150,
      deletions: 25,
      changed_files: 8,
      commits: 3,
      reviews: [
        {
          id: 456,
          user_login: "reviewer",
          state: "APPROVED",
          submitted_at: ISODate,
          body: "Looks good!"
        }
      ],
      review_comments: 5,
      labels: ["enhancement", "frontend"],
      assignees: ["developer"],
      html_url: "https://github.com/user/repo/pull/45",
      diff_url: "https://github.com/user/repo/pull/45.diff"
    }
  ],
  total_prs: 25,
  open_prs: 3,
  closed_prs: 22,
  merged_prs: 20,
  merge_rate: 0.8,
  average_review_time: 24.5, // hours
  average_merge_time: 48.2, // hours
  unique_reviewers: 8,
  review_participation_rate: 0.75,
  last_updated: ISODate,
  analysis_period: "all_time"
}
```

**Indexes**:
- `repository_id` (unique)
- `user_id`
- `total_prs` (descending)
- `merge_rate` (descending)
- `average_review_time`
- `last_updated` (descending)

#### 9. Issue Analysis Collection (`issue_analysis`)
**Purpose**: Store issue analysis data

```javascript
{
  _id: ObjectId,
  repository_id: "repository_object_id",
  user_id: "user_object_id",
  issues: [
    {
      id: 789,
      number: 12,
      title: "Bug in login system",
      body: "Description of the issue",
      state: "closed", // "open", "closed"
      created_at: ISODate,
      updated_at: ISODate,
      closed_at: ISODate,
      author_login: "user",
      author_id: 67890,
      comments: 8,
      labels: ["bug", "high-priority"],
      assignees: ["developer"],
      milestone: "v1.2.0",
      resolution_time: 72, // hours
      html_url: "https://github.com/user/repo/issues/12"
    }
  ],
  total_issues: 45,
  open_issues: 8,
  closed_issues: 37,
  resolution_rate: 0.82,
  average_resolution_time: 48.5, // hours
  issue_categories: {
    "bug": 15,
    "enhancement": 12,
    "documentation": 8,
    "question": 10
  },
  last_updated: ISODate,
  analysis_period: "all_time"
}
```

**Indexes**:
- `repository_id` (unique)
- `user_id`
- `total_issues` (descending)
- `resolution_rate` (descending)
- `average_resolution_time`
- `last_updated` (descending)

### Scan and Progress Collections

#### 10. Scan Progress Collection (`scan_progress`)
**Purpose**: Track real-time scanning progress

```javascript
{
  _id: ObjectId,
  scan_id: "unique_scan_id",
  user_id: "user_object_id",
  current_phase: "fetching_repositories", // Enum values
  progress_percentage: 45,
  current_repository: "username/repo-name",
  total_repositories: 25,
  processed_repositories: 11,
  status_message: "Analyzing repository structure...",
  estimated_completion: ISODate,
  errors: [
    {
      error_type: "rate_limit",
      error_message: "GitHub API rate limit exceeded",
      repository: "username/private-repo",
      timestamp: ISODate,
      recoverable: true
    }
  ],
  warnings: ["Some repositories are private and cannot be analyzed"],
  start_time: ISODate,
  last_update: ISODate,
  api_calls_remaining: 4500,
  repositories_found: 25,
  repositories_analyzed: 11
}
```

**Indexes**:
- `scan_id` (unique)
- `user_id`
- `current_phase`
- `start_time` (descending)
- `last_update` (descending) - TTL index (24 hours)
- `progress_percentage` (descending)

#### 11. Comprehensive Scan Results Collection (`comprehensive_scan_results`)
**Purpose**: Store complete scan results

```javascript
{
  _id: ObjectId,
  user_id: "user_object_id",
  user_profile: {
    // Complete GitHubUserProfile object
  },
  repositories: [
    // Array of DetailedRepository objects
  ],
  contribution_calendar: {
    // ContributionCalendar object
  },
  collaboration_metrics: {
    total_collaborators: 15,
    repositories_contributed_to: 8,
    pull_requests_created: 45,
    pull_requests_reviewed: 32,
    issues_created: 12,
    issues_resolved: 8,
    code_review_participation: 0.75,
    mentoring_score: 7.2
  },
  language_statistics: {
    primary_languages: ["JavaScript", "Python", "TypeScript"],
    language_diversity_score: 8.5,
    total_bytes_by_language: {
      "JavaScript": 125000,
      "Python": 89000,
      "TypeScript": 67000
    },
    repositories_by_language: {
      "JavaScript": 12,
      "Python": 8,
      "TypeScript": 5
    },
    language_trends: {
      "JavaScript": [10, 12, 15, 18, 20], // Monthly usage
      "Python": [5, 6, 8, 8, 9]
    }
  },
  achievement_metrics: {
    total_stars_earned: 1247,
    total_forks_earned: 234,
    longest_commit_streak: 45,
    most_productive_month: "2024-03",
    repository_milestones: [
      {
        repository: "username/popular-repo",
        milestone: "100_stars",
        achieved_at: ISODate
      }
    ],
    contribution_consistency: 0.85
  },
  overall_acid_score: 7.8,
  overall_quality_score: 8.2,
  developer_level: "advanced", // "beginner", "intermediate", "advanced", "expert"
  scan_metadata: {
    scan_id: "unique_scan_id",
    scan_type: "comprehensive",
    total_repositories: 25,
    successful_repositories: 23,
    failed_repositories: 2,
    scan_duration: 245.7, // seconds
    api_calls_made: 156,
    rate_limits_hit: 1,
    errors: [
      // Array of ScanError objects
    ],
    data_sources: ["rest", "graphql"],
    scan_started_at: ISODate,
    scan_completed_at: ISODate
  },
  created_at: ISODate,
  last_updated: ISODate,
  data_version: "comprehensive_v1"
}
```

**Indexes**:
- `user_id`
- `scan_metadata.scan_id` (unique)
- `scan_metadata.scan_type`
- `created_at` (descending)
- `last_updated` (descending)
- `overall_acid_score` (descending)
- `overall_quality_score` (descending)
- `developer_level`
- `data_version`
- `scan_metadata.successful_repositories` (descending)

### Cache and Metadata Collections

#### 12. Cache Metadata Collection (`cache_metadata`)
**Purpose**: Manage cache invalidation and metadata

```javascript
{
  _id: ObjectId,
  cache_key: "user_profile_12345",
  cache_type: "user_profile", // "user_profile", "repository", "scan_result"
  user_id: "user_object_id", // Optional
  repository_id: "repository_object_id", // Optional
  created_at: ISODate,
  expires_at: ISODate, // TTL field
  last_accessed: ISODate,
  access_count: 42,
  data_size: 2048, // bytes
  cache_hit_rate: 0.85,
  invalidation_triggers: ["user_profile_update", "repository_scan"],
  source_updated_at: ISODate,
  needs_refresh: false
}
```

**Indexes**:
- `cache_key` (unique)
- `cache_type`
- `user_id`
- `repository_id`
- `expires_at` - TTL index
- `created_at` (descending)
- `last_accessed` (descending)
- `needs_refresh`
- `cache_hit_rate` (descending)

## Index Strategy

### Primary Indexes
- **Unique Indexes**: Ensure data integrity for critical fields
- **Compound Indexes**: Optimize complex queries
- **Text Indexes**: Enable full-text search capabilities
- **TTL Indexes**: Automatic cleanup of temporary data

### Performance Optimization
- **Read-Heavy Workloads**: Optimized for dashboard queries
- **Write Optimization**: Efficient bulk operations for scan results
- **Memory Usage**: Balanced index strategy to minimize memory footprint

## Data Relationships

### One-to-One Relationships
- `users` ↔ `github_user_profiles`
- `repositories` ↔ `detailed_repositories`

### One-to-Many Relationships
- `users` → `repositories`
- `users` → `comprehensive_scan_results`
- `detailed_repositories` → `pull_request_analysis`
- `detailed_repositories` → `issue_analysis`

### Many-to-Many Relationships
- `users` ↔ `repositories` (through contributions)
- `repositories` ↔ `contributors`

## Data Lifecycle Management

### Automatic Cleanup
- **Scan Progress**: Removed after 24 hours
- **Cache Metadata**: Removed when expired
- **Old Scan Results**: Keep only latest 3 per user

### Data Freshness
- **User Profiles**: Refreshed every 24 hours
- **Repository Data**: Refreshed on demand
- **Contribution Calendars**: Refreshed weekly

## Migration Strategy

### Version Control
- **Schema Versioning**: Track schema changes
- **Backward Compatibility**: Support multiple data versions
- **Migration Scripts**: Automated data transformation

### Data Migration
1. **Basic to Comprehensive**: Transform existing data
2. **Schema Updates**: Add new fields and indexes
3. **Data Validation**: Ensure integrity after migration

## Security Considerations

### Data Protection
- **Sensitive Data**: Encrypted GitHub tokens
- **Access Control**: User-based data isolation
- **Audit Trail**: Track data access and modifications

### Privacy Compliance
- **Data Retention**: Configurable retention policies
- **User Consent**: Respect user privacy preferences
- **Data Anonymization**: Remove PII when required

## Performance Monitoring

### Key Metrics
- **Query Performance**: Monitor slow queries
- **Index Usage**: Track index effectiveness
- **Storage Growth**: Monitor collection sizes
- **Cache Hit Rates**: Optimize caching strategy

### Optimization Strategies
- **Query Optimization**: Regular query analysis
- **Index Maintenance**: Periodic index rebuilding
- **Data Archiving**: Move old data to cold storage
- **Connection Pooling**: Efficient database connections