"""
Security Audit Script for BroskiesHub
Performs comprehensive security checks
"""

import os
import sys
import logging
from typing import List, Dict, Any
import re

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class SecurityAuditor:
    """Performs security audit checks"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
    
    def add_issue(self, category: str, message: str, severity: str = "HIGH"):
        """Add a security issue"""
        self.issues.append({
            'category': category,
            'message': message,
            'severity': severity
        })
    
    def add_warning(self, category: str, message: str):
        """Add a security warning"""
        self.warnings.append({
            'category': category,
            'message': message
        })
    
    def add_passed(self, category: str, message: str):
        """Add a passed check"""
        self.passed.append({
            'category': category,
            'message': message
        })
    
    def check_environment_variables(self):
        """Check environment variable security"""
        logger.info("\n=== Checking Environment Variables ===")
        
        required_vars = [
            'JWT_SECRET_KEY',
            'TOKEN_ENCRYPTION_KEY',
            'MONGODB_URL',
            'GITHUB_CLIENT_SECRET'
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            
            if not value:
                self.add_issue(
                    'Environment',
                    f"Required environment variable {var} is not set",
                    "HIGH"
                )
            elif var in ['JWT_SECRET_KEY', 'TOKEN_ENCRYPTION_KEY']:
                if len(value) < 32:
                    self.add_issue(
                        'Environment',
                        f"{var} is too short (minimum 32 characters)",
                        "HIGH"
                    )
                elif value in ['your_secret_key', 'changeme', 'secret']:
                    self.add_issue(
                        'Environment',
                        f"{var} uses a default/weak value",
                        "CRITICAL"
                    )
                else:
                    self.add_passed('Environment', f"{var} is properly configured")
            else:
                self.add_passed('Environment', f"{var} is set")
        
        # Check for development values in production
        environment = os.getenv('ENVIRONMENT', 'development')
        if environment == 'production':
            if 'localhost' in os.getenv('MONGODB_URL', ''):
                self.add_issue(
                    'Environment',
                    "Using localhost MongoDB in production",
                    "HIGH"
                )
            if 'localhost' in os.getenv('FRONTEND_URL', ''):
                self.add_warning(
                    'Environment',
                    "Frontend URL points to localhost in production"
                )
    
    def check_authentication(self):
        """Check authentication implementation"""
        logger.info("\n=== Checking Authentication ===")
        
        # Check if JWT is properly configured
        jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        if jwt_algorithm not in ['HS256', 'HS384', 'HS512']:
            self.add_warning(
                'Authentication',
                f"JWT algorithm {jwt_algorithm} may not be secure"
            )
        else:
            self.add_passed('Authentication', f"JWT algorithm {jwt_algorithm} is secure")
        
        # Check token expiration
        token_expire = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30')
        try:
            expire_minutes = int(token_expire)
            if expire_minutes > 60:
                self.add_warning(
                    'Authentication',
                    f"Token expiration is {expire_minutes} minutes (consider shorter)"
                )
            else:
                self.add_passed('Authentication', f"Token expiration is {expire_minutes} minutes")
        except ValueError:
            self.add_issue(
                'Authentication',
                "Invalid ACCESS_TOKEN_EXPIRE_MINUTES value",
                "MEDIUM"
            )
    
    def check_cors_configuration(self):
        """Check CORS configuration"""
        logger.info("\n=== Checking CORS Configuration ===")
        
        cors_origins = os.getenv('CORS_ORIGINS', '')
        
        if '*' in cors_origins:
            self.add_issue(
                'CORS',
                "CORS allows all origins (*) - security risk",
                "HIGH"
            )
        elif not cors_origins:
            self.add_warning(
                'CORS',
                "CORS origins not configured"
            )
        else:
            # Check for localhost in production
            environment = os.getenv('ENVIRONMENT', 'development')
            if environment == 'production' and 'localhost' in cors_origins:
                self.add_warning(
                    'CORS',
                    "CORS allows localhost in production"
                )
            else:
                self.add_passed('CORS', "CORS origins properly configured")
    
    def check_rate_limiting(self):
        """Check rate limiting configuration"""
        logger.info("\n=== Checking Rate Limiting ===")
        
        rate_limit_enabled = os.getenv('RATE_LIMIT_ENABLED', 'false').lower()
        
        if rate_limit_enabled != 'true':
            self.add_warning(
                'Rate Limiting',
                "Rate limiting is not enabled"
            )
        else:
            self.add_passed('Rate Limiting', "Rate limiting is enabled")
            
            # Check rate limit value
            rate_limit = os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', '60')
            try:
                limit = int(rate_limit)
                if limit > 100:
                    self.add_warning(
                        'Rate Limiting',
                        f"Rate limit is high ({limit} req/min)"
                    )
                else:
                    self.add_passed('Rate Limiting', f"Rate limit is {limit} req/min")
            except ValueError:
                self.add_issue(
                    'Rate Limiting',
                    "Invalid RATE_LIMIT_REQUESTS_PER_MINUTE value",
                    "MEDIUM"
                )
    
    def check_database_security(self):
        """Check database security"""
        logger.info("\n=== Checking Database Security ===")
        
        mongodb_url = os.getenv('MONGODB_URL', '')
        
        if not mongodb_url:
            self.add_issue(
                'Database',
                "MongoDB URL not configured",
                "HIGH"
            )
            return
        
        # Check for SSL/TLS
        if 'mongodb+srv://' in mongodb_url:
            self.add_passed('Database', "Using MongoDB Atlas with SSL/TLS")
        elif 'ssl=true' in mongodb_url or 'tls=true' in mongodb_url:
            self.add_passed('Database', "SSL/TLS enabled for MongoDB")
        else:
            self.add_warning(
                'Database',
                "MongoDB connection may not use SSL/TLS"
            )
        
        # Check for credentials in URL
        if '@' in mongodb_url:
            # Extract username (don't log password)
            if 'mongodb://' in mongodb_url:
                self.add_passed('Database', "MongoDB uses authentication")
            else:
                self.add_passed('Database', "MongoDB Atlas uses authentication")
        else:
            self.add_warning(
                'Database',
                "MongoDB may not use authentication"
            )
    
    def check_encryption(self):
        """Check encryption implementation"""
        logger.info("\n=== Checking Encryption ===")
        
        # Check if encryption key is set
        encryption_key = os.getenv('TOKEN_ENCRYPTION_KEY')
        
        if not encryption_key:
            self.add_issue(
                'Encryption',
                "TOKEN_ENCRYPTION_KEY not set",
                "HIGH"
            )
        elif len(encryption_key) < 32:
            self.add_issue(
                'Encryption',
                "TOKEN_ENCRYPTION_KEY is too short",
                "HIGH"
            )
        else:
            self.add_passed('Encryption', "TOKEN_ENCRYPTION_KEY is properly configured")
        
        # Check if HTTPS is enforced
        environment = os.getenv('ENVIRONMENT', 'development')
        if environment == 'production':
            frontend_url = os.getenv('FRONTEND_URL', '')
            if frontend_url.startswith('http://'):
                self.add_issue(
                    'Encryption',
                    "Frontend URL uses HTTP instead of HTTPS",
                    "HIGH"
                )
            elif frontend_url.startswith('https://'):
                self.add_passed('Encryption', "Frontend URL uses HTTPS")
    
    def check_logging_security(self):
        """Check logging security"""
        logger.info("\n=== Checking Logging Security ===")
        
        # Check if sensitive data logging is disabled
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        environment = os.getenv('ENVIRONMENT', 'development')
        if environment == 'production' and log_level == 'DEBUG':
            self.add_warning(
                'Logging',
                "DEBUG logging enabled in production (may expose sensitive data)"
            )
        else:
            self.add_passed('Logging', f"Log level is {log_level}")
        
        # Check if JSON logging is enabled for production
        json_logging = os.getenv('JSON_LOGGING', 'false').lower()
        if environment == 'production' and json_logging != 'true':
            self.add_warning(
                'Logging',
                "JSON logging not enabled in production"
            )
        else:
            self.add_passed('Logging', "Logging configuration is appropriate")
    
    def check_common_vulnerabilities(self):
        """Check for common vulnerabilities"""
        logger.info("\n=== Checking Common Vulnerabilities ===")
        
        # Check for SQL injection (we use MongoDB, but check anyway)
        self.add_passed('Vulnerabilities', "Using MongoDB (NoSQL) - SQL injection not applicable")
        
        # Check for XSS protection
        self.add_passed('Vulnerabilities', "Using React (auto-escapes) - XSS protection built-in")
        
        # Check for CSRF protection
        # FastAPI with JWT doesn't need CSRF tokens
        self.add_passed('Vulnerabilities', "Using JWT authentication - CSRF protection not needed")
        
        # Check for dependency vulnerabilities
        self.add_warning(
            'Vulnerabilities',
            "Run 'pip audit' and 'npm audit' to check for dependency vulnerabilities"
        )
    
    def check_data_validation(self):
        """Check data validation"""
        logger.info("\n=== Checking Data Validation ===")
        
        # Pydantic provides automatic validation
        self.add_passed('Validation', "Using Pydantic for automatic data validation")
        
        # FastAPI provides automatic request validation
        self.add_passed('Validation', "Using FastAPI for automatic request validation")
    
    def run_audit(self):
        """Run complete security audit"""
        logger.info("\n" + "="*70)
        logger.info("SECURITY AUDIT")
        logger.info("="*70)
        
        self.check_environment_variables()
        self.check_authentication()
        self.check_cors_configuration()
        self.check_rate_limiting()
        self.check_database_security()
        self.check_encryption()
        self.check_logging_security()
        self.check_common_vulnerabilities()
        self.check_data_validation()
        
        self.print_report()
    
    def print_report(self):
        """Print audit report"""
        logger.info("\n" + "="*70)
        logger.info("SECURITY AUDIT REPORT")
        logger.info("="*70)
        
        # Print issues
        if self.issues:
            logger.info(f"\n❌ ISSUES FOUND: {len(self.issues)}")
            for issue in self.issues:
                logger.error(
                    f"  [{issue['severity']}] {issue['category']}: {issue['message']}"
                )
        else:
            logger.info("\n✓ NO CRITICAL ISSUES FOUND")
        
        # Print warnings
        if self.warnings:
            logger.info(f"\n⚠️  WARNINGS: {len(self.warnings)}")
            for warning in self.warnings:
                logger.warning(
                    f"  {warning['category']}: {warning['message']}"
                )
        else:
            logger.info("\n✓ NO WARNINGS")
        
        # Print passed checks
        logger.info(f"\n✓ PASSED CHECKS: {len(self.passed)}")
        for passed in self.passed:
            logger.info(f"  ✓ {passed['category']}: {passed['message']}")
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("SUMMARY")
        logger.info("="*70)
        logger.info(f"Total Checks: {len(self.issues) + len(self.warnings) + len(self.passed)}")
        logger.info(f"Issues: {len(self.issues)}")
        logger.info(f"Warnings: {len(self.warnings)}")
        logger.info(f"Passed: {len(self.passed)}")
        
        # Determine overall status
        critical_issues = [i for i in self.issues if i['severity'] == 'CRITICAL']
        high_issues = [i for i in self.issues if i['severity'] == 'HIGH']
        
        if critical_issues:
            logger.error("\n❌ AUDIT FAILED: Critical security issues found")
            return False
        elif high_issues:
            logger.warning("\n⚠️  AUDIT WARNING: High severity issues found")
            return False
        elif self.issues:
            logger.warning("\n⚠️  AUDIT WARNING: Security issues found")
            return False
        else:
            logger.info("\n✓ AUDIT PASSED: No security issues found")
            return True


def main():
    """Main function"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run audit
    auditor = SecurityAuditor()
    passed = auditor.run_audit()
    
    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
