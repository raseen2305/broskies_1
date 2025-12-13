"""
Environment Management System
Provides comprehensive environment detection, configuration loading, and validation
for different deployment environments (development, staging, production, test)
"""

import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Supported environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"

class EnvironmentManager:
    """Manages environment detection, configuration loading, and validation"""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent.parent
        self.current_environment: Optional[Environment] = None
        self.loaded_env_file: Optional[str] = None
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def detect_environment(self) -> Environment:
        """
        Detect the current environment based on various indicators
        
        Priority order:
        1. ENVIRONMENT environment variable
        2. VERCEL_ENV environment variable (for Vercel deployments)
        3. NODE_ENV environment variable (for compatibility)
        4. Presence of test indicators
        5. Default to development
        """
        # Check explicit ENVIRONMENT variable
        env_var = os.getenv("ENVIRONMENT", "").lower()
        if env_var in [e.value for e in Environment]:
            self.current_environment = Environment(env_var)
            logger.info(f"Environment detected from ENVIRONMENT variable: {self.current_environment.value}")
            return self.current_environment
        
        # Check Vercel environment
        vercel_env = os.getenv("VERCEL_ENV", "").lower()
        if vercel_env == "production":
            self.current_environment = Environment.PRODUCTION
            logger.info(f"Environment detected from VERCEL_ENV: {self.current_environment.value}")
            return self.current_environment
        elif vercel_env in ["preview", "development"]:
            self.current_environment = Environment.STAGING
            logger.info(f"Environment detected from VERCEL_ENV (preview): {self.current_environment.value}")
            return self.current_environment
        
        # Check NODE_ENV for compatibility
        node_env = os.getenv("NODE_ENV", "").lower()
        if node_env == "production":
            self.current_environment = Environment.PRODUCTION
        elif node_env == "test":
            self.current_environment = Environment.TEST
        elif node_env in ["development", "dev"]:
            self.current_environment = Environment.DEVELOPMENT
        
        # Check for test indicators
        if (os.getenv("PYTEST_CURRENT_TEST") or 
            os.getenv("TESTING") or 
            "pytest" in os.getenv("_", "")):
            self.current_environment = Environment.TEST
            logger.info("Environment detected as TEST (pytest indicators)")
            return self.current_environment
        
        # Default to development if nothing else detected
        if not self.current_environment:
            self.current_environment = Environment.DEVELOPMENT
            logger.info("Environment defaulted to DEVELOPMENT")
        
        return self.current_environment
    
    def load_environment_config(self, force_reload: bool = False) -> bool:
        """
        Load environment-specific configuration files
        
        Args:
            force_reload: Force reload even if already loaded
            
        Returns:
            True if configuration was loaded successfully
        """
        if self.loaded_env_file and not force_reload:
            logger.debug(f"Environment config already loaded from: {self.loaded_env_file}")
            return True
        
        # Detect environment if not already done
        if not self.current_environment:
            self.detect_environment()
        
        # Define environment file priority order
        env_files = self._get_env_file_candidates()
        
        loaded = False
        for env_file in env_files:
            if env_file.exists():
                logger.info(f"Loading environment configuration from: {env_file}")
                load_dotenv(env_file, override=True)
                self.loaded_env_file = str(env_file)
                loaded = True
                break
        
        if not loaded:
            logger.warning(f"No environment file found for {self.current_environment.value}")
            logger.info(f"Searched for: {[str(f) for f in env_files]}")
            # Load default .env if it exists
            default_env = self.base_path / ".env"
            if default_env.exists():
                logger.info(f"Loading default .env file: {default_env}")
                load_dotenv(default_env, override=False)  # Don't override existing vars
                self.loaded_env_file = str(default_env)
                loaded = True
        
        return loaded
    
    def _get_env_file_candidates(self) -> List[Path]:
        """Get list of environment file candidates in priority order"""
        env_files = []
        
        # Environment-specific file
        env_specific = self.base_path / f".env.{self.current_environment.value}"
        env_files.append(env_specific)
        
        # Local override file (for development)
        if self.current_environment == Environment.DEVELOPMENT:
            env_local = self.base_path / ".env.local"
            env_files.append(env_local)
        
        # Default .env file
        env_default = self.base_path / ".env"
        env_files.append(env_default)
        
        return env_files
    
    def validate_configuration(self) -> bool:
        """
        Validate the current configuration for the detected environment
        
        Returns:
            True if configuration is valid, False otherwise
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        # Ensure environment is detected
        if not self.current_environment:
            self.detect_environment()
        
        # Validate required environment variables
        self._validate_required_variables()
        
        # Validate database configuration
        self._validate_database_configuration()
        
        # Validate security configuration
        self._validate_security_configuration()
        
        # Validate OAuth configuration
        self._validate_oauth_configuration()
        
        # Environment-specific validations
        if self.current_environment == Environment.PRODUCTION:
            self._validate_production_configuration()
        elif self.current_environment == Environment.TEST:
            self._validate_test_configuration()
        
        # Log results
        if self.validation_errors:
            logger.error(f"Configuration validation failed with {len(self.validation_errors)} errors:")
            for error in self.validation_errors:
                logger.error(f"  - {error}")
        
        if self.validation_warnings:
            logger.warning(f"Configuration validation completed with {len(self.validation_warnings)} warnings:")
            for warning in self.validation_warnings:
                logger.warning(f"  - {warning}")
        
        if not self.validation_errors and not self.validation_warnings:
            logger.info("✅ Configuration validation passed")
        
        return len(self.validation_errors) == 0
    
    def _validate_required_variables(self):
        """Validate that required environment variables are set"""
        required_vars = [
            "SECRET_KEY",
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                self.validation_errors.append(f"Required environment variable {var} is not set")
    
    def _validate_database_configuration(self):
        """Validate database configuration"""
        # Validate Single Database URL
        db_url = os.getenv("MONGODB_URL")
        
        if not db_url:
            self.validation_errors.append("Database URL MONGODB_URL is not configured")
        elif not db_url.startswith(("mongodb://", "mongodb+srv://")):
            self.validation_errors.append("Invalid MongoDB URL format for MONGODB_URL")
            
        # Redis configuration
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            self.validation_warnings.append("REDIS_URL is not configured - caching will be disabled")
        elif not redis_url.startswith("redis://"):
            self.validation_errors.append("Invalid Redis URL format")
    
    def _validate_security_configuration(self):
        """Validate security-related configuration"""
        secret_key = os.getenv("SECRET_KEY")
        if secret_key:
            if len(secret_key) < 32:
                if self.current_environment == Environment.PRODUCTION:
                    self.validation_errors.append("SECRET_KEY must be at least 32 characters in production")
                else:
                    self.validation_warnings.append("SECRET_KEY should be at least 32 characters")
            
            # Check if using default/example key
            if "your-super-secret" in secret_key.lower() or "change-in-production" in secret_key.lower():
                if self.current_environment == Environment.PRODUCTION:
                    self.validation_errors.append("SECRET_KEY appears to be a default/example value - change it in production")
                else:
                    self.validation_warnings.append("SECRET_KEY appears to be a default/example value")
    
    def _validate_oauth_configuration(self):
        """Validate OAuth configuration"""
        # GitHub OAuth
        github_client_id = os.getenv("GITHUB_CLIENT_ID")
        github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        
        if self.current_environment == Environment.PRODUCTION:
            if not github_client_id:
                self.validation_errors.append("GITHUB_CLIENT_ID is required in production")
            if not github_client_secret:
                self.validation_errors.append("GITHUB_CLIENT_SECRET is required in production")
        
        # Check for test/example values
        if github_client_id and ("test" in github_client_id.lower() or "example" in github_client_id.lower()):
            if self.current_environment == Environment.PRODUCTION:
                self.validation_errors.append("GITHUB_CLIENT_ID appears to be a test/example value")
            elif self.current_environment != Environment.TEST:
                self.validation_warnings.append("GITHUB_CLIENT_ID appears to be a test/example value")
    
    def _validate_production_configuration(self):
        """Additional validation for production environment"""
        # Ensure debug is disabled
        debug = os.getenv("DEBUG", "false").lower()
        if debug in ["true", "1", "yes"]:
            self.validation_errors.append("DEBUG should be disabled in production")
        
        # Ensure proper logging level
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level == "DEBUG":
            self.validation_warnings.append("LOG_LEVEL is set to DEBUG in production - consider INFO or WARNING")
        
        # Check for development URLs
        frontend_url = os.getenv("FRONTEND_URL", "")
        if "localhost" in frontend_url or "127.0.0.1" in frontend_url:
            self.validation_errors.append("FRONTEND_URL contains localhost in production")
    
    def _validate_test_configuration(self):
        """Additional validation for test environment"""
        # Ensure test databases are used
        db_urls = [
            "MONGODB_URL"
        ]
        
        for db_url_var in db_urls:
            url = os.getenv(db_url_var, "")
            if url and "test" not in url.lower():
                self.validation_warnings.append(f"{db_url_var} should contain 'test' in test environment")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration"""
        return {
            "environment": self.current_environment.value if self.current_environment else "unknown",
            "loaded_env_file": self.loaded_env_file,
            "validation_errors": len(self.validation_errors),
            "validation_warnings": len(self.validation_warnings),
            "database_urls_configured": 1 if os.getenv("MONGODB_URL") else 0,
            "redis_configured": bool(os.getenv("REDIS_URL")),
            "github_oauth_configured": bool(os.getenv("GITHUB_CLIENT_ID") and os.getenv("GITHUB_CLIENT_SECRET")),
            "google_oauth_configured": bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))
        }
    
    def create_environment_template(self, target_env: Environment, output_path: Optional[str] = None) -> str:
        """
        Create an environment template file for the specified environment
        
        Args:
            target_env: Target environment to create template for
            output_path: Optional custom output path
            
        Returns:
            Path to the created template file
        """
        if not output_path:
            output_path = self.base_path / f".env.{target_env.value}.template"
        
        template_content = self._generate_template_content(target_env)
        
        with open(output_path, 'w') as f:
            f.write(template_content)
        
        logger.info(f"Created environment template: {output_path}")
        return str(output_path)
    
    def _generate_template_content(self, env: Environment) -> str:
        """Generate template content for the specified environment"""
        content = f"""# {env.value.title()} Environment Configuration
# Generated template - replace placeholder values with actual configuration

# Core Application
APP_NAME=Broskies Hub ({env.value.title()})
VERSION=1.0.0
DEBUG={'true' if env == Environment.DEVELOPMENT else 'false'}
ENVIRONMENT={env.value}
"""
        
        if env == Environment.PRODUCTION:
            content += "VERCEL_ENV=production\n"
        elif env == Environment.STAGING:
            content += "VERCEL_ENV=preview\n"
        
        content += """
# Database Configuration
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority&appName=your-app
DATABASE_NAME=broskies_hub

# Redis Configuration
REDIS_URL=redis://username:password@redis-cluster:6379/0

# Security
SECRET_KEY=your-secure-secret-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OAuth Providers
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_TOKEN=your_github_token

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Frontend/API URLs
"""
        
        if env == Environment.PRODUCTION:
            content += """FRONTEND_URL=https://your-domain.com
API_BASE_URL=https://your-domain.com/api
"""
        elif env == Environment.STAGING:
            content += """FRONTEND_URL=https://staging.your-domain.com
API_BASE_URL=https://staging.your-domain.com/api
"""
        else:
            content += """FRONTEND_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000
"""
        
        content += f"""
# CORS Configuration
CORS_ORIGINS=["https://your-domain.com"]
CORS_ALLOW_CREDENTIALS=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE={'100' if env == Environment.PRODUCTION else '200'}

# Logging
LOG_LEVEL={'INFO' if env == Environment.PRODUCTION else 'DEBUG'}
JSON_LOGGING={'true' if env == Environment.PRODUCTION else 'false'}

# HR Configuration
GOOGLE_HR_CLIENT_ID=your_google_hr_client_id
GOOGLE_HR_CLIENT_SECRET=your_google_hr_client_secret
GOOGLE_HR_REDIRECT_URI=https://your-domain.com/hr/auth
GOOGLE_FORM_URL=https://docs.google.com/forms/d/your-form-id/viewform

# Development/Testing Configuration
ENABLE_DEV_LOGIN={'true' if env in [Environment.DEVELOPMENT, Environment.TEST] else 'false'}

# Health Check Configuration
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL=30
"""
        
        return content

# Global instance
environment_manager = EnvironmentManager()

# Convenience functions
def detect_environment() -> Environment:
    """Detect the current environment"""
    return environment_manager.detect_environment()

def load_environment_config(force_reload: bool = False) -> bool:
    """Load environment-specific configuration"""
    return environment_manager.load_environment_config(force_reload)

def validate_configuration() -> bool:
    """Validate the current configuration"""
    return environment_manager.validate_configuration()

def get_configuration_summary() -> Dict[str, Any]:
    """Get configuration summary"""
    return environment_manager.get_configuration_summary()

def get_current_environment() -> Optional[Environment]:
    """Get the current environment"""
    return environment_manager.current_environment