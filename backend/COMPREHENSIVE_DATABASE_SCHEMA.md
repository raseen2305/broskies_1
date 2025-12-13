# Comprehensive Database Schema - Multi-Database Architecture

## Database Architecture Overview

### Database Distribution:
1. **`external_users`** - External user scans (public access)
2. **`raseen_temp_user`** - Internal users temporary data (24-hour cycle)
3. **`raseen_main_user`** - Internal users permanent data
4. **`srie_main_user`** - Backup for internal users permanent data
5. **`raseen_main_hr`** - HR dashboard data
6. **`srie_main_hr`** - Backup for HR dashboard data

### Data Flow:
- **External Users**: Direct storage in `external_users`
- **Internal Users**: `raseen_temp_user` → (24h) → `raseen_main_user` + `srie_main_user`
- **HR Data**: Direct storage in `raseen_main_hr` + `srie_main_hr`

---

## 1. EXTERNAL_USERS Database

### Collection: `user_details`
**Purpose**: Store external user scan data (first scan)

```javascript
{
  _id: ObjectId,
  github_username: "external_user",
  email: "user@example.com", // Optional
  description: "User bio/description",
  links: {
    blog: "https://blog.com",
    twitter: "@username",
    linkedin: "https://linkedin.com/in/username"
  },
  bio: "Developer bio",
  company: "@company",
  scan_date: ISODate,
  scan_time: 45.2, // seconds
  repos_fetched: 25,
  public_repos: 25,
  displayed_repos: 20,
  followers: 100,
  following: 50,
  activity_score: 8.5,
  language_count: 8,
  languages: {
    "JavaScript": 15420,
    "Python": 8900,
    "TypeScript": 6700
  },
  language_used_in_repo_count: {
    "JavaScript": 12,
    "Python": 8,
    "TypeScript": 5
  },
  longest_streak: 45,
  github_created_on: ISODate,
  github_updated_on: ISODate,
  profile_pic: "https://avatars.githubusercontent.com/...",
  total_stars: 1247,
  total_forks: 234,
  total_commits: 1500,
  code_metrics: {
    total_lines: 125000,
    total_files: 450,
    total_repos: 25
  },
  importance_score: 7.8,
  repo1: {
    name: "main-project",
    importance_score: 9.2
  },
  
  // Updated after second scan (initially empty)
  acid_scoring: {
    atomicity: 0,
    consistency: 0,
    isolation: 0,
    durability: 0,
    overall_score: 0
  },
  repo_count: 0,
  repo_evaluated: 0,
  primary_language: "",
  repositories: [],
  total_flagship_repo: 0,
  total_significant_repo: 0,
  total_supporting_repo: 0
}
```

**Indexes**:
```javascript
// Primary indexes
db.user_details.createIndex({ "github_username": 1 }, { unique: true })
db.user_details.createIndex({ "email": 1 })
db.user_details.createIndex({ "scan_date": -1 })

// Performance indexes
db.user_details.createIndex({ "total_stars": -1 })
db.user_details.createIndex({ "activity_score": -1 })
db.user_details.createIndex({ "importance_score": -1 })
db.user_details.createIndex({ "primary_language": 1 })
db.user_details.createIndex({ "company": 1 })

// Compound indexes
db.user_details.createIndex({ "github_username": 1, "scan_date": -1 })
db.user_details.createIndex({ "total_stars": -1, "total_forks": -1 })

// Text search
db.user_details.createIndex({ 
  "github_username": "text", 
  "bio": "text", 
  "company": "text",
  "description": "text"
})
```

### Collection: `external_scan_cache`
**Purpose**: Cache external scan results

```javascript
{
  _id: ObjectId,
  username: "external_user",
  user_id: "external_external_user",
  user_type: "external",
  storage_location: "EXTERNAL_DATABASE",
  scan_date: ISODate,
  // ... complete scan result data
}
```

**Indexes**:
```javascript
db.external_scan_cache.createIndex({ "username": 1 })
db.external_scan_cache.createIndex({ "user_id": 1 })
db.external_scan_cache.createIndex({ "scan_date": -1 })
db.external_scan_cache.createIndex({ "user_type": 1 })
```

---

## 2. RASEEN_TEMP_USER Database (24-hour cycle)

### Collection: `internal_users_data`
**Purpose**: Store internal user scan data (temporary - 24 hours)

```javascript
{
  _id: ObjectId,
  github_username: "internal_user",
  description: "User description",
  official_name: "Full Legal Name",
  university: "University Name",
  nationality: "Country",
  state: "State/Province",
  district: "District/City",
  email: "user@company.com",
  links: {
    blog: "https://blog.com",
    twitter: "@username",
    linkedin: "https://linkedin.com/in/username",
    portfolio: "https://portfolio.com"
  },
  bio: "Developer bio",
  company: "@company",
  scan_date: ISODate,
  scan_time: 45.2,
  repos_fetched: 25,
  public_repos: 25,
  displayed_repos: 20,
  followers: 100,
  following: 50,
  activity_score: 8.5,
  language_count: 8,
  languages: {
    "JavaScript": 15420,
    "Python": 8900,
    "TypeScript": 6700
  },
  language_used_in_repo_count: {
    "JavaScript": 12,
    "Python": 8,
    "TypeScript": 5
  },
  longest_streak: 45,
  github_created_on: ISODate,
  github_updated_on: ISODate,
  profile_pic: "https://avatars.githubusercontent.com/...",
  total_stars: 1247,
  total_forks: 234,
  total_commits: 1500,
  code_metrics: {
    total_lines: 125000,
    total_files: 450,
    total_repos: 25
  },
  importance_score: 7.8,
  repo1: {
    name: "main-project",
    importance_score: 9.2
  },
  
  // Updated after second scan
  acid_scoring: {
    atomicity: 8.5,
    consistency: 7.2,
    isolation: 6.8,
    durability: 9.1,
    overall_score: 7.9
  },
  repo_count: 25,
  repo_evaluated: 15,
  primary_language: "JavaScript",
  repositories: [
    {
      name: "project-1",
      description: "Main project description",
      languages_used: ["JavaScript", "CSS", "HTML"],
      forks: 12,
      stars: 45,
      watch_count: 8,
      importance_score: 9.2,
      importance_category: "flagship",
      pull_requests: 25,
      issues: 8,
      license: "MIT",
      categories: ["web", "frontend"]
    }
  ],
  total_flagship_repo: 3,
  total_significant_repo: 8,
  total_supporting_repo: 14,
  
  // Metadata
  created_at: ISODate,
  expires_at: ISODate // TTL - 24 hours
}
```

**Indexes**:
```javascript
// Primary indexes
db.internal_users_data.createIndex({ "github_username": 1 }, { unique: true })
db.internal_users_data.createIndex({ "email": 1 })
db.internal_users_data.createIndex({ "official_name": 1 })

// Geographic indexes
db.internal_users_data.createIndex({ "nationality": 1 })
db.internal_users_data.createIndex({ "state": 1 })
db.internal_users_data.createIndex({ "district": 1 })
db.internal_users_data.createIndex({ "university": 1 })

// Performance indexes
db.internal_users_data.createIndex({ "scan_date": -1 })
db.internal_users_data.createIndex({ "total_stars": -1 })
db.internal_users_data.createIndex({ "activity_score": -1 })
db.internal_users_data.createIndex({ "acid_scoring.overall_score": -1 })
db.internal_users_data.createIndex({ "importance_score": -1 })
db.internal_users_data.createIndex({ "primary_language": 1 })

// TTL index for 24-hour expiry
db.internal_users_data.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 })

// Compound indexes
db.internal_users_data.createIndex({ "github_username": 1, "scan_date": -1 })
db.internal_users_data.createIndex({ "nationality": 1, "state": 1 })
db.internal_users_data.createIndex({ "university": 1, "nationality": 1 })

// Text search
db.internal_users_data.createIndex({ 
  "github_username": "text", 
  "official_name": "text",
  "bio": "text", 
  "company": "text",
  "university": "text"
})
```

### Collection: `internal_scan_cache`
**Purpose**: Cache internal scan results (temporary)

```javascript
{
  _id: ObjectId,
  username: "internal_user",
  user_id: "internal_507f1f77bcf86cd799439011",
  user_type: "internal",
  storage_location: "INTERNAL_DATABASE",
  scan_date: ISODate,
  expires_at: ISODate, // TTL - 24 hours
  // ... complete scan result data
}
```

**Indexes**:
```javascript
db.internal_scan_cache.createIndex({ "username": 1 })
db.internal_scan_cache.createIndex({ "user_id": 1 })
db.internal_scan_cache.createIndex({ "scan_date": -1 })
db.internal_scan_cache.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 })
```

---

## 3. RASEEN_MAIN_USER Database (Permanent storage)

### Collection: `internal_users_data`
**Purpose**: Permanent storage for internal users (copied from temp after 24h)

```javascript
// Same structure as raseen_temp_user.internal_users_data
// but without expires_at field and with additional metadata
{
  // ... all fields from temp database ...
  
  // Additional permanent storage fields
  migrated_from_temp: ISODate,
  data_retention_policy: "permanent",
  last_profile_update: ISODate,
  profile_completeness: 85.5, // percentage
  ranking_eligible: true,
  ranking_score: 8.7,
  ranking_position: 42,
  ranking_category: "senior_developer"
}
```

**Indexes**: Same as temp database plus:
```javascript
db.internal_users_data.createIndex({ "migrated_from_temp": -1 })
db.internal_users_data.createIndex({ "ranking_score": -1 })
db.internal_users_data.createIndex({ "ranking_position": 1 })
db.internal_users_data.createIndex({ "ranking_eligible": 1 })
db.internal_users_data.createIndex({ "profile_completeness": -1 })
```

---

## 4. SRIE_MAIN_USER Database (Backup)

### Collection: `internal_users_data`
**Purpose**: Backup copy of raseen_main_user data

```javascript
// Identical structure to raseen_main_user.internal_users_data
// with additional backup metadata
{
  // ... all fields from main database ...
  
  // Backup metadata
  backup_source: "raseen_main_user",
  backup_date: ISODate,
  backup_version: "v1.0",
  sync_status: "synchronized"
}
```

**Indexes**: Same as main database plus backup-specific indexes:
```javascript
db.internal_users_data.createIndex({ "backup_date": -1 })
db.internal_users_data.createIndex({ "sync_status": 1 })
```

---

## 5. RASEEN_MAIN_HR Database

### Collection: `hr_users`
**Purpose**: Store HR user information from Google Forms

```javascript
{
  _id: ObjectId,
  name: "HR Manager Name",
  email: "hr@company.com",
  google_id: "google_oauth_id_12345",
  company: "Tech Company Inc",
  role: "Technical Recruiter",
  date_filled: ISODate,
  time_filled: "14:30:00",
  
  // HR approval workflow
  approved: false,
  approved_by: {
    hr_name: "Senior HR Manager",
    email: "senior.hr@company.com",
    google_id: "google_oauth_id_67890",
    company: "Tech Company Inc",
    role: "HR Director",
    approval_date: ISODate,
    approval_time: "16:45:00"
  },
  
  // Additional HR metadata
  access_level: "basic", // "basic", "premium", "enterprise"
  departments: ["Engineering", "Product"],
  hiring_focus: ["Full-stack", "Backend", "Frontend"],
  company_size: "100-500",
  location: "San Francisco, CA",
  timezone: "America/Los_Angeles",
  
  // Activity tracking
  last_login: ISODate,
  profile_views: 0,
  searches_performed: 0,
  candidates_shortlisted: 0,
  
  // Status
  is_active: true,
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes**:
```javascript
// Primary indexes
db.hr_users.createIndex({ "email": 1 }, { unique: true })
db.hr_users.createIndex({ "google_id": 1 }, { unique: true })

// Query optimization indexes
db.hr_users.createIndex({ "company": 1 })
db.hr_users.createIndex({ "role": 1 })
db.hr_users.createIndex({ "approved": 1 })
db.hr_users.createIndex({ "is_active": 1 })
db.hr_users.createIndex({ "access_level": 1 })

// Performance indexes
db.hr_users.createIndex({ "date_filled": -1 })
db.hr_users.createIndex({ "last_login": -1 })
db.hr_users.createIndex({ "created_at": -1 })

// Compound indexes
db.hr_users.createIndex({ "company": 1, "role": 1 })
db.hr_users.createIndex({ "approved": 1, "is_active": 1 })
db.hr_users.createIndex({ "company": 1, "approved": 1 })

// Text search
db.hr_users.createIndex({ 
  "name": "text", 
  "company": "text", 
  "role": "text",
  "departments": "text"
})
```

---

## 6. SRIE_MAIN_HR Database (Backup)

### Collection: `hr_users`
**Purpose**: Backup copy of HR data

```javascript
// Identical structure to raseen_main_hr.hr_users
// with backup metadata
{
  // ... all fields from main HR database ...
  
  // Backup metadata
  backup_source: "raseen_main_hr",
  backup_date: ISODate,
  backup_version: "v1.0",
  sync_status: "synchronized"
}
```

**Indexes**: Same as main HR database plus backup indexes.

---

## Data Migration Scripts

### Daily Migration Process (24-hour cycle)

```javascript
// Migration from temp to main databases
async function migrateTemporaryData() {
  const tempData = await db.raseen_temp_user.internal_users_data.find({
    created_at: { $lt: new Date(Date.now() - 24 * 60 * 60 * 1000) }
  });
  
  for (const user of tempData) {
    // Add migration metadata
    user.migrated_from_temp = new Date();
    user.data_retention_policy = "permanent";
    delete user.expires_at;
    
    // Insert to main database
    await db.raseen_main_user.internal_users_data.insertOne(user);
    
    // Insert to backup database
    user.backup_source = "raseen_main_user";
    user.backup_date = new Date();
    user.sync_status = "synchronized";
    await db.srie_main_user.internal_users_data.insertOne(user);
    
    // Remove from temp database
    await db.raseen_temp_user.internal_users_data.deleteOne({ _id: user._id });
  }
}
```

### HR Profile View Integration

```javascript
// Function to fetch user profile for HR dashboard
async function getUserProfileForHR(github_username) {
  // Primary source: raseen_main_user
  let userProfile = await db.raseen_main_user.internal_users_data.findOne({
    github_username: github_username
  });
  
  // Fallback to backup: srie_main_user
  if (!userProfile) {
    userProfile = await db.srie_main_user.internal_users_data.findOne({
      github_username: github_username
    });
  }
  
  return userProfile;
}
```

---

## Performance Optimization

### Index Strategy
- **Unique indexes** on critical fields (username, email)
- **Compound indexes** for common query patterns
- **Text indexes** for search functionality
- **TTL indexes** for automatic cleanup
- **Descending indexes** for sorting by scores/dates

### Query Optimization
- Use appropriate indexes for all queries
- Implement pagination for large result sets
- Cache frequently accessed data
- Use aggregation pipelines for complex analytics

### Storage Optimization
- Regular index maintenance
- Data archiving for old records
- Compression for large text fields
- Efficient data types for numeric fields

This schema provides a comprehensive foundation for your multi-database architecture with proper separation of external users, internal users (with temp/permanent cycle), and HR data, along with appropriate indexing for optimal performance.