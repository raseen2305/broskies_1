#!/usr/bin/env python3
"""
Test script for the unified ranking system implementation.
This script tests the core functionality of the updated ranking system.
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.ranking_service import RankingService
from app.database.collections import Collections
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_unified_ranking_system():
    """
    Test the unified ranking system functionality
    """
    try:
        # Connect to database
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        
        logger.info("Testing unified ranking system...")
        
        # Initialize ranking service
        ranking_service = RankingService(db)
        
        # Test 1: Get joined user data
        logger.info("\n=== Test 1: Get joined user data ===")
        joined_data = await ranking_service.get_joined_user_data()
        logger.info(f"Found {len(joined_data)} users with complete profile and scan data")
        
        if joined_data:
            sample_user = joined_data[0]
            logger.info(f"Sample user: {sample_user.get('name')} ({sample_user.get('github_username')})")
            logger.info(f"  University: {sample_user.get('university_short')}")
            logger.info(f"  District: {sample_user.get('district')}")
            logger.info(f"  Score: {sample_user.get('overall_score')}")
        
        # Test 2: Get all districts and universities
        logger.info("\n=== Test 2: Get districts and universities ===")
        districts = await ranking_service.get_all_districts()
        universities = await ranking_service.get_all_universities()
        logger.info(f"Found {len(districts)} districts: {districts[:5]}...")
        logger.info(f"Found {len(universities)} universities: {universities[:3]}...")
        
        # Test 3: Update rankings for a sample district (if available)
        if districts:
            sample_district = districts[0]
            logger.info(f"\n=== Test 3: Update regional rankings for {sample_district} ===")
            result = await ranking_service.update_regional_rankings(sample_district)
            logger.info(f"Regional ranking update result: {result}")
        
        # Test 4: Update rankings for a sample university (if available)
        if universities:
            sample_university = universities[0]
            logger.info(f"\n=== Test 4: Update university rankings for {sample_university} ===")
            result = await ranking_service.update_university_rankings(sample_university)
            logger.info(f"University ranking update result: {result}")
        
        # Test 5: Test ranking calculations
        logger.info("\n=== Test 5: Test ranking calculations ===")
        test_scores = [85.5, 92.1, 78.3, 92.1, 67.8, 88.9, 95.2]
        test_user_score = 88.9
        
        percentile = ranking_service.calculate_percentile(test_user_score, test_scores)
        rank = ranking_service.calculate_rank_position(test_user_score, test_scores)
        stats = ranking_service.calculate_statistics(test_scores)
        
        logger.info(f"Test scores: {test_scores}")
        logger.info(f"User score: {test_user_score}")
        logger.info(f"Calculated percentile: {percentile}%")
        logger.info(f"Calculated rank: {rank}")
        logger.info(f"Statistics: {stats}")
        
        # Test 6: Validate data consistency
        logger.info("\n=== Test 6: Validate data consistency ===")
        validation_result = await ranking_service.validate_ranking_data_consistency()
        logger.info(f"Validation result: {validation_result}")
        
        # Test 7: Get sample user rankings
        if joined_data:
            sample_user_id = joined_data[0].get('user_id')
            logger.info(f"\n=== Test 7: Get rankings for user {sample_user_id} ===")
            user_rankings = await ranking_service.get_user_rankings(sample_user_id)
            logger.info(f"User rankings: {user_rankings}")
        
        logger.info("\n✅ All tests completed successfully!")
        
        # Close connection
        client.close()
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        raise


async def main():
    """Main function to run the tests"""
    try:
        await test_unified_ranking_system()
        logger.info("Testing completed successfully!")
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())