"""
Security Configuration Checker
Validates security settings and configurations
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SecurityConfigChecker:
    """
    Checks and validates security configurations
    
    Ensures HTTPS, secure connections, and proper security settings
    """
    
    @staticmethod
    def check_https_configuration() -> Dict[str, Any]:
        """
        Check HTTPS configuration
        
        Returns:
            Dictionary with HTTPS configuration status
        """
        results = {
            'https_enabled': False,
            'force_https': False,
            'warnings': [],
            'recommendations': []
        }
        
        # Check if running in production
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        is_production = environment == 'production'
        
        # Check HTTPS settings
        https_enabled = os.getenv('HTTPS_ENABLED', 'false').lower() == 'true'
        force_https = os.getenv('FORCE_HTTPS', 'false').lower() == 'true'
        
        results['https_enabled'] = https_enabled
        results['force_https'] = force_https
        
        # Validate production settings
        if is_production:
            if not https_enabled:
                results['warnings'].append(
                    "HTTPS is not enabled in production. This is a security risk!"
                )
                results['recommendations'].append(
                    "Set HTTPS_ENABLED=true in production environment"
                )
            
            if not force_https:
                results['warnings'].append(
                    "HTTPS is not enforced in production. HTTP connections are allowed."
                )
                results['recommendations'].append(
                    "Set FORCE_HTTPS=true to redirect all HTTP traffic to HTTPS"
                )
        
        return results
    
    @staticmethod
    def check_database_security() -> Dict[str, Any]:
        """
        Check database security configuration
        
        Returns:
            Dictionary with database security status
        """
        results = {
            'ssl_enabled': False,
            'connection_encrypted': False,
            'warnings': [],
            'recommendations': []
        }
        
        # Check MongoDB connection string
        mongodb_url = os.getenv('MONGODB_URL', '')
        
        # Check for SSL/TLS in connection string
        if 'ssl=true' in mongodb_url.lower() or 'tls=true' in mongodb_url.lower():
            results['ssl_enabled'] = True
            results['connection_encrypted'] = True
        else:
            results['warnings'].append(
                "Database connection is not using SSL/TLS encryption"
            )
            results['recommendations'].append(
                "Add ssl=true or tls=true to MongoDB connection string"
            )
        
        # Check for authentication
        if '@' not in mongodb_url:
            results['warnings'].append(
                "Database connection string does not include authentication"
            )
            results['recommendations'].append(
                "Use authenticated MongoDB connection with username and password"
            )
        
        return results
    
    @staticmethod
    def check_token_encryption() -> Dict[str, Any]:
        """
        Check token encryption configuration
        
        Returns:
            Dictionary with token encryption status
        """
        results = {
            'encryption_key_set': False,
            'warnings': [],
            'recommendations': []
        }
        
        # Check if encryption key is set
        encryption_key = os.getenv('TOKEN_ENCRYPTION_KEY')
        
        if encryption_key:
            results['encryption_key_set'] = True
            
            # Check key strength
            if len(encryption_key) < 32:
                results['warnings'].append(
                    "Token encryption key is weak (less than 32 characters)"
                )
                results['recommendations'].append(
                    "Use a strong encryption key with at least 32 characters"
                )
        else:
            results['warnings'].append(
                "TOKEN_ENCRYPTION_KEY is not set. Using temporary key."
            )
            results['recommendations'].append(
                "Set TOKEN_ENCRYPTION_KEY environment variable with a strong key"
            )
        
        return results
    
    @staticmethod
    def check_cors_configuration() -> Dict[str, Any]:
        """
        Check CORS configuration
        
        Returns:
            Dictionary with CORS configuration status
        """
        results = {
            'cors_configured': False,
            'allow_all_origins': False,
            'warnings': [],
            'recommendations': []
        }
        
        # Check CORS origins
        cors_origins = os.getenv('CORS_ORIGINS', '')
        
        if cors_origins:
            results['cors_configured'] = True
            
            # Check for wildcard
            if '*' in cors_origins:
                results['allow_all_origins'] = True
                results['warnings'].append(
                    "CORS is configured to allow all origins (*). This is insecure!"
                )
                results['recommendations'].append(
                    "Specify exact allowed origins instead of using wildcard"
                )
        else:
            results['warnings'].append(
                "CORS_ORIGINS is not configured"
            )
            results['recommendations'].append(
                "Set CORS_ORIGINS to specify allowed frontend origins"
            )
        
        return results
    
    @staticmethod
    def check_jwt_configuration() -> Dict[str, Any]:
        """
        Check JWT configuration
        
        Returns:
            Dictionary with JWT configuration status
        """
        results = {
            'secret_key_set': False,
            'algorithm_secure': False,
            'warnings': [],
            'recommendations': []
        }
        
        # Check JWT secret
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        
        if jwt_secret:
            results['secret_key_set'] = True
            
            # Check key strength
            if len(jwt_secret) < 32:
                results['warnings'].append(
                    "JWT secret key is weak (less than 32 characters)"
                )
                results['recommendations'].append(
                    "Use a strong JWT secret key with at least 32 characters"
                )
        else:
            results['warnings'].append(
                "JWT_SECRET_KEY is not set"
            )
            results['recommendations'].append(
                "Set JWT_SECRET_KEY environment variable with a strong key"
            )
        
        # Check algorithm
        jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        
        if jwt_algorithm in ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']:
            results['algorithm_secure'] = True
        else:
            results['warnings'].append(
                f"JWT algorithm '{jwt_algorithm}' may not be secure"
            )
            results['recommendations'].append(
                "Use a secure JWT algorithm like HS256, HS512, or RS256"
            )
        
        return results
    
    @classmethod
    def run_all_checks(cls) -> Dict[str, Any]:
        """
        Run all security checks
        
        Returns:
            Dictionary with all security check results
        """
        logger.info("Running security configuration checks...")
        
        results = {
            'https': cls.check_https_configuration(),
            'database': cls.check_database_security(),
            'token_encryption': cls.check_token_encryption(),
            'cors': cls.check_cors_configuration(),
            'jwt': cls.check_jwt_configuration()
        }
        
        # Collect all warnings
        all_warnings = []
        all_recommendations = []
        
        for category, check_results in results.items():
            all_warnings.extend(check_results.get('warnings', []))
            all_recommendations.extend(check_results.get('recommendations', []))
        
        results['summary'] = {
            'total_warnings': len(all_warnings),
            'total_recommendations': len(all_recommendations),
            'all_warnings': all_warnings,
            'all_recommendations': all_recommendations
        }
        
        # Log warnings
        if all_warnings:
            logger.warning(f"Security configuration warnings: {len(all_warnings)}")
            for warning in all_warnings:
                logger.warning(f"  - {warning}")
        else:
            logger.info("No security configuration warnings found")
        
        return results
    
    @classmethod
    def validate_production_security(cls) -> bool:
        """
        Validate security configuration for production
        
        Returns:
            True if production security requirements are met, False otherwise
        """
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        
        if environment != 'production':
            logger.info("Not in production environment, skipping strict validation")
            return True
        
        logger.info("Validating production security configuration...")
        
        results = cls.run_all_checks()
        
        # Check critical requirements for production
        critical_checks = [
            results['https']['https_enabled'],
            results['https']['force_https'],
            results['database']['ssl_enabled'],
            results['token_encryption']['encryption_key_set'],
            results['jwt']['secret_key_set']
        ]
        
        if not all(critical_checks):
            logger.error("Production security validation FAILED!")
            logger.error("Critical security requirements not met:")
            
            if not results['https']['https_enabled']:
                logger.error("  - HTTPS is not enabled")
            if not results['https']['force_https']:
                logger.error("  - HTTPS is not enforced")
            if not results['database']['ssl_enabled']:
                logger.error("  - Database SSL/TLS is not enabled")
            if not results['token_encryption']['encryption_key_set']:
                logger.error("  - Token encryption key is not set")
            if not results['jwt']['secret_key_set']:
                logger.error("  - JWT secret key is not set")
            
            return False
        
        logger.info("Production security validation PASSED")
        return True


# Convenience function
def check_security_configuration() -> Dict[str, Any]:
    """
    Check security configuration
    
    Returns:
        Dictionary with security check results
    """
    return SecurityConfigChecker.run_all_checks()


def validate_production_security() -> bool:
    """
    Validate production security configuration
    
    Returns:
        True if valid, False otherwise
    """
    return SecurityConfigChecker.validate_production_security()
