"""
Unit tests for environment configuration loading and validation
**Validates: Requirements 4.1, 4.3, 4.5**
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.core.environment_manager import EnvironmentManager, Environment
from app.core.config import validate_configuration


class TestEnvironmentConfigurationLoading:
    """Unit tests for environment configuration loading"""

    def test_startup_with_missing_environment_variables(self):
        """
        Test startup behavior when environment variables are missing
        **Validates: Requirements 4.1, 4.3**
        """
        # Test with completely empty environment
        with patch.dict(os.environ, {}, clear=True):
            manager = EnvironmentManager()
            
            # Should detect development as default
            env = manager.detect_environment()
            assert env == Environment.DEVELOPMENT
            
            # Validation should fail due to missing required variables
            is_valid = manager.validate_configuration()
            assert not is_valid
            assert len(manager.validation_errors) > 0
            
            # Should have errors for missing database URLs
            error_messages = " ".join(manager.validation_errors)
            assert "SECRET_KEY" in error_messages
            assert "EXTERNAL_USERS_DB_URL" in error_messages

    def test_configuration_validation_logic(self):
        """
        Test configuration validation logic with various scenarios
        **Validates: Requirements 4.1, 4.3**
        """
        # Test with minimal valid configuration
        valid_config = {
            "ENVIRONMENT": "development",
            "SECRET_KEY": "test-secret-key-at-least-32-chars-long",
            "EXTERNAL_USERS_DB_URL": "mongodb+srv://user:pass@host/external_users",
            "RASEEN_TEMP_USER_DB_URL": "mongodb+srv://user:pass@host/raseen_temp_user",
            "RASEEN_MAIN_USER_DB_URL": "mongodb+srv://user:pass@host/raseen_main_user",
            "RASEEN_MAIN_HR_DB_URL": "mongodb+srv://user:pass@host/raseen_main_hr",
            "SRIE_MAIN_USER_DB_URL": "mongodb+srv://user:pass@host/srie_main_user",
            "SRIE_MAIN_HR_DB_URL": "mongodb+srv://user:pass@host/srie_main_hr"
        }
        
        with patch.dict(os.environ, valid_config, clear=True):
            manager = EnvironmentManager()
            manager.detect_environment()
            
            is_valid = manager.validate_configuration()
            assert is_valid
            assert len(manager.validation_errors) == 0

    def test_environment_switching_scenarios(self):
        """
        Test environment switching scenarios
        **Validates: Requirements 4.5**
        """
        base_config = {
            "SECRET_KEY": "test-secret-key-at-least-32-chars-long",
            "EXTERNAL_USERS_DB_URL": "mongodb+srv://user:pass@host/external_users",
            "RASEEN_TEMP_USER_DB_URL": "mongodb+srv://user:pass@host/raseen_temp_user",
            "RASEEN_MAIN_USER_DB_URL": "mongodb+srv://user:pass@host/raseen_main_user",
            "RASEEN_MAIN_HR_DB_URL": "mongodb+srv://user:pass@host/raseen_main_hr",
            "SRIE_MAIN_USER_DB_URL": "mongodb+srv://user:pass@host/srie_main_user",
            "SRIE_MAIN_HR_DB_URL": "mongodb+srv://user:pass@host/srie_main_hr"
        }
        
        # Test development environment
        dev_config = {**base_config, "ENVIRONMENT": "development"}
        with patch.dict(os.environ, dev_config, clear=True):
            manager = EnvironmentManager()
            env = manager.detect_environment()
            assert env == Environment.DEVELOPMENT
        
        # Test production environment
        prod_config = {**base_config, "ENVIRONMENT": "production"}
        with patch.dict(os.environ, prod_config, clear=True):
            manager = EnvironmentManager()
            env = manager.detect_environment()
            assert env == Environment.PRODUCTION
        
        # Test staging environment
        staging_config = {**base_config, "ENVIRONMENT": "staging"}
        with patch.dict(os.environ, staging_config, clear=True):
            manager = EnvironmentManager()
            env = manager.detect_environment()
            assert env == Environment.STAGING
        
        # Test test environment
        test_config = {**base_config, "ENVIRONMENT": "test"}
        with patch.dict(os.environ, test_config, clear=True):
            manager = EnvironmentManager()
            env = manager.detect_environment()
            assert env == Environment.TEST

    def test_vercel_environment_detection(self):
        """
        Test Vercel environment detection
        **Validates: Requirements 4.5**
        """
        base_config = {
            "SECRET_KEY": "test-secret-key-at-least-32-chars-long",
            "EXTERNAL_USERS_DB_URL": "mongodb+srv://user:pass@host/external_users"
        }
        
        # Test Vercel production
        vercel_prod_config = {**base_config, "VERCEL_ENV": "production"}
        with patch.dict(os.environ, vercel_prod_config, clear=True):
            manager = EnvironmentManager()
            env = manager.detect_environment()
            assert env == Environment.PRODUCTION
        
        # Test Vercel preview (should map to staging)
        vercel_preview_config = {**base_config, "VERCEL_ENV": "preview"}
        with patch.dict(os.environ, vercel_preview_config, clear=True):
            manager = EnvironmentManager()
            env = manager.detect_environment()
            assert env == Environment.STAGING

    def test_pytest_environment_detection(self):
        """
        Test pytest environment detection
        **Validates: Requirements 4.5**
        """
        base_config = {
            "SECRET_KEY": "test-secret-key-at-least-32-chars-long"
        }
        
        # Test pytest detection
        pytest_config = {**base_config, "PYTEST_CURRENT_TEST": "test_something.py::test_function"}
        with patch.dict(os.environ, pytest_config, clear=True):
            manager = EnvironmentManager()
            env = manager.detect_environment()
            assert env == Environment.TEST

    def test_invalid_database_urls(self):
        """
        Test validation of invalid database URLs
        **Validates: Requirements 4.1, 4.3**
        """
        invalid_config = {
            "ENVIRONMENT": "development",
            "SECRET_KEY": "test-secret-key-at-least-32-chars-long",
            "EXTERNAL_USERS_DB_URL": "invalid://not-mongodb-url",
            "RASEEN_TEMP_USER_DB_URL": "http://wrong-protocol",
            "RASEEN_MAIN_USER_DB_URL": "",  # Empty URL
            "RASEEN_MAIN_HR_DB_URL": "mongodb+srv://user:pass@host/raseen_main_hr",
            "SRIE_MAIN_USER_DB_URL": "mongodb+srv://user:pass@host/srie_main_user",
            "SRIE_MAIN_HR_DB_URL": "mongodb+srv://user:pass@host/srie_main_hr"
        }
        
        with patch.dict(os.environ, invalid_config, clear=True):
            manager = EnvironmentManager()
            manager.detect_environment()
            
            is_valid = manager.validate_configuration()
            assert not is_valid
            assert len(manager.validation_errors) > 0
            
            # Should have specific errors for invalid URLs
            error_messages = " ".join(manager.validation_errors)
            assert "Invalid MongoDB URL format" in error_messages

    def test_production_security_validation(self):
        """
        Test production-specific security validation
        **Validates: Requirements 4.1, 4.3**
        """
        # Test with weak secret key in production
        weak_prod_config = {
            "ENVIRONMENT": "production",
            "SECRET_KEY": "weak",  # Too short
            "DEBUG": "true",  # Should be false in production
            "FRONTEND_URL": "http://localhost:3000",  # Should not be localhost in prod
            "EXTERNAL_USERS_DB_URL": "mongodb+srv://user:pass@host/external_users",
            "RASEEN_TEMP_USER_DB_URL": "mongodb+srv://user:pass@host/raseen_temp_user",
            "RASEEN_MAIN_USER_DB_URL": "mongodb+srv://user:pass@host/raseen_main_user",
            "RASEEN_MAIN_HR_DB_URL": "mongodb+srv://user:pass@host/raseen_main_hr",
            "SRIE_MAIN_USER_DB_URL": "mongodb+srv://user:pass@host/srie_main_user",
            "SRIE_MAIN_HR_DB_URL": "mongodb+srv://user:pass@host/srie_main_hr"
        }
        
        with patch.dict(os.environ, weak_prod_config, clear=True):
            manager = EnvironmentManager()
            manager.detect_environment()
            
            is_valid = manager.validate_configuration()
            assert not is_valid
            
            error_messages = " ".join(manager.validation_errors)
            assert "SECRET_KEY must be at least 32 characters" in error_messages
            assert "DEBUG should be disabled" in error_messages
            assert "localhost in production" in error_messages

    def test_test_environment_validation(self):
        """
        Test test environment-specific validation
        **Validates: Requirements 4.1, 4.3**
        """
        # Test environment should use test databases
        test_config = {
            "ENVIRONMENT": "test",
            "SECRET_KEY": "test-secret-key-at-least-32-chars-long",
            "EXTERNAL_USERS_DB_URL": "mongodb://localhost:27017/external_users_test",
            "RASEEN_TEMP_USER_DB_URL": "mongodb://localhost:27017/raseen_temp_user_test",
            "RASEEN_MAIN_USER_DB_URL": "mongodb://localhost:27017/raseen_main_user_test",
            "RASEEN_MAIN_HR_DB_URL": "mongodb://localhost:27017/raseen_main_hr_test",
            "SRIE_MAIN_USER_DB_URL": "mongodb://localhost:27017/srie_main_user_test",
            "SRIE_MAIN_HR_DB_URL": "mongodb://localhost:27017/srie_main_hr_test"
        }
        
        with patch.dict(os.environ, test_config, clear=True):
            manager = EnvironmentManager()
            manager.detect_environment()
            
            is_valid = manager.validate_configuration()
            assert is_valid  # Should be valid
            # Should have minimal warnings (Redis URL missing is acceptable in test)

    def test_configuration_summary(self):
        """
        Test configuration summary generation
        **Validates: Requirements 4.1**
        """
        complete_config = {
            "ENVIRONMENT": "development",
            "SECRET_KEY": "test-secret-key-at-least-32-chars-long",
            "EXTERNAL_USERS_DB_URL": "mongodb+srv://user:pass@host/external_users",
            "RASEEN_TEMP_USER_DB_URL": "mongodb+srv://user:pass@host/raseen_temp_user",
            "RASEEN_MAIN_USER_DB_URL": "mongodb+srv://user:pass@host/raseen_main_user",
            "RASEEN_MAIN_HR_DB_URL": "mongodb+srv://user:pass@host/raseen_main_hr",
            "SRIE_MAIN_USER_DB_URL": "mongodb+srv://user:pass@host/srie_main_user",
            "SRIE_MAIN_HR_DB_URL": "mongodb+srv://user:pass@host/srie_main_hr",
            "REDIS_URL": "redis://localhost:6379",
            "GITHUB_CLIENT_ID": "test_client_id",
            "GITHUB_CLIENT_SECRET": "test_client_secret",
            "GOOGLE_CLIENT_ID": "test_google_id",
            "GOOGLE_CLIENT_SECRET": "test_google_secret"
        }
        
        with patch.dict(os.environ, complete_config, clear=True):
            manager = EnvironmentManager()
            manager.detect_environment()
            manager.validate_configuration()
            
            summary = manager.get_configuration_summary()
            
            assert summary["environment"] == "development"
            assert summary["database_urls_configured"] == 6
            assert summary["redis_configured"] is True
            assert summary["github_oauth_configured"] is True
            assert summary["google_oauth_configured"] is True

    def test_environment_file_loading_priority(self):
        """
        Test environment file loading priority
        **Validates: Requirements 4.5**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test environment files
            env_dev = temp_path / ".env.development"
            env_dev.write_text("TEST_VAR=development\nSECRET_KEY=dev-secret")
            
            env_default = temp_path / ".env"
            env_default.write_text("TEST_VAR=default\nSECRET_KEY=default-secret")
            
            # Test that environment-specific file takes priority
            with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
                manager = EnvironmentManager(base_path=str(temp_path))
                manager.detect_environment()
                loaded = manager.load_environment_config()
                
                assert loaded is True
                assert os.getenv("TEST_VAR") == "development"
                assert manager.loaded_env_file == str(env_dev)

    @pytest.mark.asyncio
    async def test_enhanced_validate_configuration_integration(self):
        """
        Test integration with enhanced validate_configuration function
        **Validates: Requirements 4.1, 4.3, 4.5**
        """
        valid_config = {
            "ENVIRONMENT": "development",
            "SECRET_KEY": "test-secret-key-at-least-32-chars-long",
            "EXTERNAL_USERS_DB_URL": "mongodb+srv://user:pass@host/external_users",
            "RASEEN_TEMP_USER_DB_URL": "mongodb+srv://user:pass@host/raseen_temp_user",
            "RASEEN_MAIN_USER_DB_URL": "mongodb+srv://user:pass@host/raseen_main_user",
            "RASEEN_MAIN_HR_DB_URL": "mongodb+srv://user:pass@host/raseen_main_hr",
            "SRIE_MAIN_USER_DB_URL": "mongodb+srv://user:pass@host/srie_main_user",
            "SRIE_MAIN_HR_DB_URL": "mongodb+srv://user:pass@host/srie_main_hr"
        }
        
        with patch.dict(os.environ, valid_config, clear=True):
            # Should not raise an exception
            validate_configuration()
        
        # Test with invalid configuration
        invalid_config = {
            "ENVIRONMENT": "production",
            "SECRET_KEY": "weak"  # Too short for production
        }
        
        with patch.dict(os.environ, invalid_config, clear=True):
            with pytest.raises(ValueError, match="Configuration validation failed"):
                validate_configuration()


class TestEnvironmentTemplateGeneration:
    """Test environment template generation functionality"""

    def test_template_generation_for_all_environments(self):
        """
        Test template generation for all supported environments
        **Validates: Requirements 4.5**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = EnvironmentManager(base_path=temp_dir)
            
            for env in Environment:
                template_path = manager.create_environment_template(env)
                
                assert Path(template_path).exists()
                
                # Read and verify template content
                with open(template_path, 'r') as f:
                    content = f.read()
                
                assert f"ENVIRONMENT={env.value}" in content
                assert "EXTERNAL_USERS_DB_URL=" in content
                assert "SECRET_KEY=" in content
                
                # Environment-specific checks
                if env == Environment.PRODUCTION:
                    assert "DEBUG=false" in content
                    assert "VERCEL_ENV=production" in content
                elif env == Environment.DEVELOPMENT:
                    assert "DEBUG=true" in content
                    assert "localhost" in content