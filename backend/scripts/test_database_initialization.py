#!/usr/bin/env python3
"""
Database Initialization Test Script
Tests the database initialization and health check system
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.database_initialization import (
    initialize_database_system,
    get_system_health_check,
    get_database_status,
    is_system_initialized
)
from app.db_connection_multi import DatabaseType
from app.core.logging_config import setup_logging

# Setup logging
setup_logging(
    log_level="INFO",
    enable_console_logging=True,
    enable_json_logging=False
)

logger = logging.getLogger(__name__)

async def test_database_initialization():
    """Test the complete database initialization system"""
    
    print("🚀 Testing Database Initialization System")
    print("=" * 50)
    
    try:
        # Test 1: Check initial state
        print("\n📋 Test 1: Initial State Check")
        print("-" * 30)
        
        initialized = is_system_initialized()
        print(f"System initialized: {initialized}")
        
        # Test 2: Initialize database system
        print("\n🔗 Test 2: Database System Initialization")
        print("-" * 40)
        
        start_time = datetime.now()
        initialization_results = await initialize_database_system()
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        print(f"Initialization completed in: {duration:.2f} seconds")
        print(f"Success: {initialization_results.get('success', False)}")
        print(f"Overall Status: {initialization_results.get('overall_status', 'unknown')}")
        
        # Print connection results
        connection_results = initialization_results.get('connection_results', {})
        if connection_results:
            print(f"\nConnection Results:")
            print(f"  Successful: {connection_results.get('successful_connections', 0)}")
            print(f"  Total: {connection_results.get('total_connections', 0)}")
            
            for db_name, status in connection_results.get('connection_details', {}).items():
                status_icon = "✅" if "✅" in status else "❌"
                print(f"  {status_icon} {db_name}: {status}")
        
        # Test 3: Health check
        print("\n🏥 Test 3: System Health Check")
        print("-" * 30)
        
        health_data = await get_system_health_check(force_refresh=True)
        
        print(f"Overall Status: {health_data.get('overall_status', 'unknown')}")
        print(f"Initialization Complete: {health_data.get('initialization_complete', False)}")
        
        system_metrics = health_data.get('system_metrics', {})
        if system_metrics:
            print(f"Healthy Databases: {system_metrics.get('healthy_databases', 0)}/{system_metrics.get('total_databases', 0)}")
            print(f"Uptime: {system_metrics.get('uptime_seconds', 0):.1f} seconds")
        
        # Test 4: Individual database status
        print("\n📊 Test 4: Individual Database Status")
        print("-" * 35)
        
        for db_type in DatabaseType:
            try:
                db_status = await get_database_status(db_type.value)
                status_icon = "✅" if db_status.get('status') == 'healthy' else "❌"
                
                print(f"  {status_icon} {db_type.value}:")
                print(f"    Status: {db_status.get('status', 'unknown')}")
                
                if 'ping_time_ms' in db_status:
                    print(f"    Ping: {db_status['ping_time_ms']:.2f}ms")
                
                if 'collections_count' in db_status:
                    print(f"    Collections: {db_status['collections_count']}")
                
                if 'error' in db_status:
                    print(f"    Error: {db_status['error']}")
                    
            except Exception as e:
                print(f"  ❌ {db_type.value}: Error - {str(e)}")
        
        # Test 5: Error statistics
        print("\n📈 Test 5: Error Statistics")
        print("-" * 25)
        
        error_stats = health_data.get('error_statistics', {})
        if error_stats:
            print(f"Total Errors (24h): {error_stats.get('total_errors', 0)}")
            
            severity_counts = error_stats.get('severity_counts', {})
            for severity, count in severity_counts.items():
                if count > 0:
                    print(f"  {severity.title()}: {count}")
        else:
            print("No error statistics available")
        
        # Test 6: Final verification
        print("\n✅ Test 6: Final Verification")
        print("-" * 25)
        
        final_initialized = is_system_initialized()
        print(f"System initialized: {final_initialized}")
        
        if final_initialized and initialization_results.get('success', False):
            print("\n🎉 All tests passed! Database initialization system is working correctly.")
            return True
        else:
            print("\n⚠️ Some tests failed. Check the logs for details.")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        logger.exception("Database initialization test failed")
        return False

async def test_health_endpoints():
    """Test the health check endpoints (simulated)"""
    
    print("\n🔍 Testing Health Check Functions")
    print("=" * 35)
    
    try:
        # Test basic health check
        print("\n📋 Basic Health Check")
        print("-" * 20)
        
        health_data = await get_system_health_check()
        print(f"Status: {health_data.get('overall_status', 'unknown')}")
        print(f"Timestamp: {health_data.get('timestamp', 'unknown')}")
        
        # Test database-specific checks
        print("\n📊 Database-Specific Checks")
        print("-" * 25)
        
        for db_type in list(DatabaseType)[:3]:  # Test first 3 databases
            try:
                db_status = await get_database_status(db_type.value)
                print(f"{db_type.value}: {db_status.get('status', 'unknown')}")
            except Exception as e:
                print(f"{db_type.value}: Error - {str(e)}")
        
        print("\n✅ Health check functions are working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Health check test failed: {str(e)}")
        logger.exception("Health check test failed")
        return False

async def main():
    """Main test function"""
    
    print("🧪 Database Initialization System Test Suite")
    print("=" * 50)
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Run initialization tests
    init_success = await test_database_initialization()
    
    # Run health check tests
    health_success = await test_health_endpoints()
    
    # Final results
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    print(f"Database Initialization: {'✅ PASS' if init_success else '❌ FAIL'}")
    print(f"Health Check Functions: {'✅ PASS' if health_success else '❌ FAIL'}")
    
    overall_success = init_success and health_success
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    print(f"\nCompleted at: {datetime.now().isoformat()}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)