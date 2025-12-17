from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List
import os
import logging
from app.core.environment_manager import environment_manager, Environment

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Environment Detection (Enhanced)
    environment: str = Field(default="development", env="ENVIRONMENT")
    vercel_env: Optional[str] = Field(default=None, env="VERCEL_ENV")
    vercel_url: Optional[str] = Field(default=None, env="VERCEL_URL")
    
    # Environment Manager Integration
    def __init__(self, **kwargs):
        # Load environment-specific configuration before initializing
        environment_manager.load_environment_config()
        super().__init__(**kwargs)
    
    # Database Configuration (Single DB)
    mongodb_url: str = Field(
        default="mongodb+srv://thoshifraseen4_db_user:iojkJvAoEhBOLbmM@online-evaluation.lkxqo8m.mongodb.net/?appName=online-evaluation",
        env="MONGODB_URL"
    )
    database_name: str = Field(default="broskies_hub", env="DATABASE_NAME")
    
    # Security Configuration
    secret_key: str = Field(
        default="kJ8mN2pQ9rS5tU7vW0xY3zA6bC9dE2fH5iL8mN1pQ4rS7tU0vW3xY6zA9bC2dE5fH8iL1mN4pQ7rS0tU3vW6xY9zA",
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # GitHub OAuth Configuration
    github_client_id: Optional[str] = Field(default=None, env="GITHUB_CLIENT_ID")
    github_client_secret: Optional[str] = Field(default=None, env="GITHUB_CLIENT_SECRET")
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    
    # Google OAuth Configuration
    google_client_id: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    
    # Redis Configuration
    redis_url: str = Field(
        default="redis://default:H2fhJw9TnGHT2Q1aAWlrEtxgDVslpFtG@redis-11883.c330.asia-south1-1.gce.redns.redis-cloud.com:11883",
        env="REDIS_URL"
    )
    
    # Frontend/API URLs (Environment-aware)
    frontend_url: Optional[str] = Field(default=None, env="FRONTEND_URL")
    api_base_url: Optional[str] = Field(default=None, env="API_BASE_URL")
    
    # CORS Configuration
    cors_origins: List[str] = Field(default_factory=list, env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # API Settings
    api_v1_str: str = "/api/v1"
    project_name: str = "BroskiesHub - GitHub Repository Evaluator"
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests_per_minute: int = Field(default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    json_logging: bool = Field(default=False, env="JSON_LOGGING")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables
    
    @validator("mongodb_url")
    def validate_mongodb_url(cls, v):
        """Validate MongoDB URL format"""
        if not v or not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("Invalid MongoDB URL format")
        return v
    
    @validator("secret_key")
    def validate_secret_key(cls, v, values):
        """Validate secret key strength in production"""
        environment = values.get("environment", "development")
        vercel_env = values.get("vercel_env")
        
        if (environment == "production" or vercel_env == "production") and len(v) < 32:
            logger.warning("Secret key should be at least 32 characters in production")
        
        return v
    
    def get_frontend_url(self) -> str:
        """Get the appropriate frontend URL based on environment"""
        if self.frontend_url:
            return self.frontend_url
        
        # Vercel environment
        if self.vercel_env in ["production", "preview"] and self.vercel_url:
            return f"https://{self.vercel_url}"
        
        # Production fallback
        if self.vercel_env == "production":
            return "https://broskies.vercel.app"
        
        # Development fallback
        return "http://localhost:3000"
    
    def get_api_base_url(self) -> str:
        """Get the appropriate API base URL based on environment"""
        if self.api_base_url:
            return self.api_base_url
        
        # Vercel environment - API is served from /api
        if self.vercel_env in ["production", "preview"]:
            frontend_url = self.get_frontend_url()
            return f"{frontend_url}/api"
        
        # Development environment
        return "http://localhost:8000"
    
    def get_github_redirect_uri(self) -> str:
        """Get GitHub OAuth redirect URI"""
        base_url = self.get_api_base_url()
        return f"{base_url}/auth/github/callback"
    
    def get_github_redirect_uris(self) -> List[str]:
        """Get all valid GitHub OAuth redirect URIs for different environments"""
        uris = []
        
        # Production URI
        uris.append("https://broskies.vercel.app/api/auth/github/callback")
        
        # Preview/staging URIs (Vercel generates these automatically)
        if self.vercel_url:
            uris.append(f"https://{self.vercel_url}/api/auth/github/callback")
        
        # Development URI
        uris.append("http://localhost:8000/auth/github/callback")
        
        return uris
    
    def get_google_redirect_uri(self) -> str:
        """Get Google OAuth redirect URI"""
        base_url = self.get_api_base_url()
        return f"{base_url}/auth/google/callback"
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production" or self.vercel_env == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development" and not self.vercel_env

# Create settings instance
settings = Settings()

# Validation and logging
def validate_configuration():
    """Enhanced configuration validation using environment manager"""
    # Use the enhanced environment manager for validation
    is_valid = environment_manager.validate_configuration()
    
    # Get configuration summary
    summary = environment_manager.get_configuration_summary()
    
    # Log enhanced configuration status
    logger.info(f"Environment: {summary['environment']}")
    logger.info(f"Loaded from: {summary['loaded_env_file']}")
    logger.info(f"Frontend URL: {settings.get_frontend_url()}")
    logger.info(f"API Base URL: {settings.get_api_base_url()}")
    logger.info(f"Database URL configured: {summary['database_urls_configured']}")
    logger.info(f"Redis configured: {summary['redis_configured']}")
    logger.info(f"GitHub OAuth configured: {summary['github_oauth_configured']}")
    logger.info(f"Google OAuth configured: {summary['google_oauth_configured']}")
    
    if summary['validation_errors'] > 0:
        logger.error(f"Configuration has {summary['validation_errors']} errors")
    if summary['validation_warnings'] > 0:
        logger.warning(f"Configuration has {summary['validation_warnings']} warnings")
    
    if not is_valid:
        raise ValueError("Configuration validation failed - check logs for details")
    
    logger.info("✅ Enhanced configuration validation passed")

def get_github_token() -> str:
    """Get GitHub token from settings or environment"""
    token = settings.github_token or os.getenv("GITHUB_TOKEN")
    if not token:
        logger.warning("GitHub token not configured.")
        return None
    return token