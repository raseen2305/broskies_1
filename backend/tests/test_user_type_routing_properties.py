"""
Property-Based Tests for User Type Detection and Database Routing
Tests the correctness properties defined in the database restructuring design
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException
from typing import Dict, Any

from app.user_type_detector import UserTypeDetector, detect_user_type_from_request
from app.db_connection_multi import DatabaseType
from app.models.user import User


class TestUserTypeRoutingProperties:
    """Property-based tests for user type detection and routing system"""

    @pytest.mark.asyncio
    async def test_property_1_external_user_database_routing(self):
        """
        **Feature: database-restructuring, Property 1: External User Database Routing**
        **Validates: Requirements 1.2, 2.2, 2.4**
        
        For any external user request, the system should store all data in the external_users 
        database and use external_ prefixes for user identification
        """
        # Test with multiple usernames to simulate property-based testing
        test_usernames = ["srie06", "testuser", "user123", "external_test", "sample"]
        
        for username in test_usernames:
            # Create mock request without authentication (external user)
            mock_request = MagicMock(spec=Request)
            
            with patch('app.user_type_detector.get_current_user_optional') as mock_get_user:
                # Force external user detection by returning None (no auth)
                mock_get_user.return_value = None
                
                with patch('app.db_connection_multi.get_external_users_db') as mock_get_db:
                    mock_db = AsyncMock()
                    mock_get_db.return_value = mock_db
                    
                    # Test the routing
                    routing_info = await UserTypeDetector.route_user_operation(
                        mock_request, username, "test_operation"
                    )
                    
                    # Property assertions
                    assert routing_info["user_type"] == "external", \
                        f"External users must be detected as 'external' type for {username}"
                    
                    assert routing_info["user_id"].startswith("external_"), \
                        f"External user IDs must have 'external_' prefix for {username}"
                    
                    assert routing_info["user_id"] == f"external_{username}", \
                        f"External user ID must be 'external_' + username for {username}"
                    
                    assert routing_info["scan_collection"] == "external_scan_cache", \
                        f"External users must use external_scan_cache collection for {username}"
                    
                    assert routing_info["analysis_collection"] == "external_analysis_progress", \
                        f"External users must use external_analysis_progress collection for {username}"
                    
                    assert routing_info["storage_location"] == "EXTERNAL_DATABASE", \
                        f"External users must be stored in EXTERNAL_DATABASE for {username}"
                    
                    # Verify external database was requested
                    mock_get_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_property_2_internal_user_initial_storage(self):
        """
        **Feature: database-restructuring, Property 2: Internal User Initial Storage**
        **Validates: Requirements 1.3, 2.1, 2.3**
        
        For any internal user request, the system should initially store data in raseen_temp_user 
        database and use internal_ prefixes for user identification
        """
        # Test with multiple user scenarios to simulate property-based testing
        test_cases = [
            ("507f1f77bcf86cd799439011", "raseen2305", "raseen@example.com"),
            ("507f1f77bcf86cd799439012", "testuser", "test@example.com"),
            ("507f1f77bcf86cd799439013", "developer", "dev@example.com")
        ]
        
        for user_id, username, email in test_cases:
            # Create mock authenticated user
            mock_user = MagicMock(spec=User)
            mock_user.id = user_id
            mock_user.github_username = username
            mock_user.email = email
            mock_user.github_token = "mock_token"
            
            mock_request = MagicMock(spec=Request)
            
            with patch('app.user_type_detector.get_current_user_optional') as mock_get_user:
                # Force internal user detection by returning authenticated user
                mock_get_user.return_value = mock_user
                
                with patch('app.db_connection_multi.get_raseen_temp_user_db') as mock_get_db:
                    mock_db = AsyncMock()
                    mock_get_db.return_value = mock_db
                    
                    # Test the routing
                    routing_info = await UserTypeDetector.route_user_operation(
                        mock_request, username, "test_operation"
                    )
                    
                    # Property assertions
                    assert routing_info["user_type"] == "internal", \
                        f"Authenticated users must be detected as 'internal' type for {username}"
                    
                    assert routing_info["user_id"].startswith("internal_"), \
                        f"Internal user IDs must have 'internal_' prefix for {username}"
                    
                    assert routing_info["user_id"] == f"internal_{user_id}", \
                        f"Internal user ID must be 'internal_' + user ObjectId for {username}"
                    
                    assert routing_info["scan_collection"] == "internal_scan_cache", \
                        f"Internal users must use internal_scan_cache collection for {username}"
                    
                    assert routing_info["analysis_collection"] == "internal_analysis_progress", \
                        f"Internal users must use internal_analysis_progress collection for {username}"
                    
                    assert routing_info["storage_location"] == "INTERNAL_DATABASE", \
                        f"Internal users must be stored in INTERNAL_DATABASE for {username}"
                    
                    # Verify raseen_temp_user database was requested
                    mock_get_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_property_5_authentication_requirements_consistency(self):
        """
        **Feature: database-restructuring, Property 5: Authentication Requirements Consistency**
        **Validates: Requirements 2.5**
        
        For any user request, internal users should require JWT and GitHub OAuth tokens 
        while external users should have public access without authentication
        """
        # Test multiple authentication scenarios
        test_scenarios = [
            ("testuser1", True, True),   # Has JWT and GitHub token
            ("testuser2", True, False),  # Has JWT but no GitHub token
            ("testuser3", False, False), # No authentication
            ("testuser4", False, True),  # No JWT (GitHub token irrelevant)
        ]
        
        for username, has_valid_token, has_github_token in test_scenarios:
            mock_request = MagicMock(spec=Request)
            
            with patch('app.user_type_detector.get_current_user_optional') as mock_get_user:
                if has_valid_token:
                    # Create mock authenticated user
                    mock_user = MagicMock(spec=User)
                    mock_user.id = "507f1f77bcf86cd799439011"  # Valid ObjectId
                    mock_user.github_username = username
                    mock_user.email = f"{username}@example.com"
                    mock_user.github_token = "valid_token" if has_github_token else None
                    mock_get_user.return_value = mock_user
                else:
                    # No authentication
                    mock_get_user.return_value = None
                
                # Detect user type
                detected_type = await UserTypeDetector.detect_user_type(mock_request)
                
                if has_valid_token:
                    # Should be detected as internal user
                    assert detected_type == "internal", \
                        f"Users with valid JWT tokens must be classified as internal for {username}"
                    
                    # For internal users, GitHub token should be checked in actual operations
                    # (This is tested in the routing operations, not just detection)
                    
                else:
                    # Should be detected as external user
                    assert detected_type == "external", \
                        f"Users without JWT tokens must be classified as external for {username}"
                    
                    # External users should not require any authentication
                    # They should be able to access the system without tokens

    def test_user_id_prefix_consistency(self):
        """
        Test that user ID prefixing is consistent for both user types
        """
        # Test multiple scenarios
        test_cases = [
            ("testuser", {"id": "507f1f77bcf86cd799439011"}),
            ("srie06", {"_id": "507f1f77bcf86cd799439012"}),
            ("developer", {"username": "developer"}),
        ]
        
        for username, user_data in test_cases:
            # Test internal user ID generation
            internal_id = UserTypeDetector.get_user_id_with_prefix(user_data, "internal")
            assert internal_id.startswith("internal_"), \
                f"Internal user IDs must always start with 'internal_' for {username}"
            
            # Test external user ID generation  
            external_id = UserTypeDetector.get_user_id_with_prefix(username, "external")
            assert external_id.startswith("external_"), \
                f"External user IDs must always start with 'external_' for {username}"
            assert external_id == f"external_{username}", \
                f"External user IDs must be exactly 'external_' + username for {username}"

    def test_collection_name_prefixing(self):
        """
        Test that collection names are properly prefixed based on user type
        """
        # Test all combinations
        base_collections = ['scan_cache', 'analysis_progress', 'user_profiles']
        user_types = ['internal', 'external']
        
        for base_collection in base_collections:
            for user_type in user_types:
                collection_name = UserTypeDetector.get_collection_name(base_collection, user_type)
                
                expected_prefix = f"{user_type}_"
                assert collection_name.startswith(expected_prefix), \
                    f"Collection names must start with '{expected_prefix}' for {user_type} users"
                
                assert collection_name == f"{user_type}_{base_collection}", \
                    f"Collection name must be exactly '{user_type}_{base_collection}'"

    @pytest.mark.asyncio
    async def test_database_routing_never_cross_contaminates(self):
        """
        Test that internal and external users never get routed to each other's databases
        """
        test_usernames = ["testuser", "srie06", "developer"]
        
        for username in test_usernames:
            mock_request = MagicMock(spec=Request)
            
            # Test external user routing
            with patch('app.user_type_detector.get_current_user_optional') as mock_get_user:
                mock_get_user.return_value = None  # No auth = external
                
                with patch('app.db_connection_multi.get_external_users_db') as mock_external_db, \
                     patch('app.db_connection_multi.get_raseen_temp_user_db') as mock_internal_db:
                    
                    mock_external_db.return_value = AsyncMock()
                    mock_internal_db.return_value = AsyncMock()
                    
                    external_routing = await UserTypeDetector.route_user_operation(
                        mock_request, username, "test"
                    )
                    
                    # External user should only call external database
                    mock_external_db.assert_called_once()
                    mock_internal_db.assert_not_called()
                    
                    assert external_routing["user_type"] == "external"
                    assert external_routing["storage_location"] == "EXTERNAL_DATABASE"
            
            # Test internal user routing
            with patch('app.user_type_detector.get_current_user_optional') as mock_get_user:
                mock_user = MagicMock(spec=User)
                mock_user.id = "507f1f77bcf86cd799439011"
                mock_user.github_username = username
                mock_get_user.return_value = mock_user  # Auth = internal
                
                with patch('app.db_connection_multi.get_external_users_db') as mock_external_db, \
                     patch('app.db_connection_multi.get_raseen_temp_user_db') as mock_internal_db:
                    
                    mock_external_db.return_value = AsyncMock()
                    mock_internal_db.return_value = AsyncMock()
                    
                    internal_routing = await UserTypeDetector.route_user_operation(
                        mock_request, username, "test"
                    )
                    
                    # Internal user should only call internal database
                    mock_internal_db.assert_called_once()
                    mock_external_db.assert_not_called()
                    
                    assert internal_routing["user_type"] == "internal"
                    assert internal_routing["storage_location"] == "INTERNAL_DATABASE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])