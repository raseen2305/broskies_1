// MongoDB initialization script for GitHub Evaluator
print('Initializing GitHub Comprehensive Database...');

// Switch to the application database
db = db.getSiblingDB('github_comprehensive_data');

// Create application user
db.createUser({
  user: 'github_app_user',
  pwd: 'github_app_password',
  roles: [
    {
      role: 'readWrite',
      db: 'github_comprehensive_data'
    }
  ]
});

// Create basic collections with validation
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['email', 'user_type', 'created_at'],
      properties: {
        email: {
          bsonType: 'string',
          description: 'must be a string and is required'
        },
        github_username: {
          bsonType: 'string',
          description: 'must be a string if provided'
        },
        user_type: {
          enum: ['developer', 'hr'],
          description: 'must be either developer or hr'
        },
        created_at: {
          bsonType: 'date',
          description: 'must be a date and is required'
        }
      }
    }
  }
});

db.createCollection('github_user_profiles');
db.createCollection('repositories');
db.createCollection('detailed_repositories');
db.createCollection('comprehensive_scan_results');
db.createCollection('contribution_calendars');
db.createCollection('scan_progress');
db.createCollection('cache_metadata');

// Create basic indexes
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ github_username: 1 });
db.github_user_profiles.createIndex({ user_id: 1 }, { unique: true });
db.github_user_profiles.createIndex({ login: 1 }, { unique: true });
db.repositories.createIndex({ user_id: 1 });
db.repositories.createIndex({ github_id: 1 }, { unique: true });
db.detailed_repositories.createIndex({ user_id: 1 });
db.detailed_repositories.createIndex({ github_id: 1 }, { unique: true });
db.comprehensive_scan_results.createIndex({ user_id: 1 });
db.scan_progress.createIndex({ scan_id: 1 }, { unique: true });

print('✅ GitHub Comprehensive Database initialized successfully');
print('📊 Collections created with validation and indexes');
print('🔐 Application user created with readWrite permissions');