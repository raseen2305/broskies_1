#!/usr/bin/env python3
"""
Test script for the unified ranking system with random generated data.
This script creates sample data and tests all ranking functionality.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Import the ranking service
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ranking_service import RankingService
from app.database.collections import Collections

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample data for generating random users
SAMPLE_NAMES = [
    "Arjun Kumar", "Priya Sharma", "Rahul Patel", "Sneha Reddy", "Vikram Singh",
    "Ananya Gupta", "Karthik Nair", "Meera Iyer", "Rohan Joshi", "Kavya Menon",
    "Aditya Agarwal", "Riya Bansal", "Siddharth Rao", "Pooja Verma", "Nikhil Shah",
    "Divya Pillai", "Aryan Malhotra", "Shreya Kapoor", "Varun Sinha", "Nisha Tiwari"
]

SAMPLE_UNIVERSITIES = [
    ("IIT Madras", "iit-madras"),
    ("IIT Delhi", "iit-delhi"),
    ("IIT Bombay", "iit-bombay"),
    ("NIT Trichy", "nit-trichy"),
    ("Anna University", "anna-university"),
    ("VIT Vellore", "vit-vellore"),
    ("SRM University", "srm-university"),
    ("Kalasalingam Institute", "kalasalingam-institute"),
    ("PSG College", "psg-college"),
    ("Coimbatore Institute", "coimbatore-institute")
]

SAMPLE_DISTRICTS = [
    ("Chennai", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Coimbatore", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Madurai", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Trichy", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Salem", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Tirunelveli", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Vellore", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Erode", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Dindigul", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Thanjavur", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Bangalore", "Karnataka", "IN-Karnataka"),
    ("Mysore", "Karnataka", "IN-Karnataka"),
    ("Mangalore", "Karnataka", "IN-Karnataka"),
    ("Hyderabad", "Telangana", "IN-Telangana"),
    ("Warangal", "Telangana", "IN-Telangana")
]

SAMPLE_GITHUB_USERNAMES = [
    "dev_arjun", "priya_codes", "rahul_dev", "sneha_tech", "vikram_py",
    "ananya_js", "karthik_react", "meera_ml", "rohan_backend", "kavya_frontend",
    "aditya_fullstack", "riya_data", "sid_algorithms", "pooja_web", "nikhil_mobile",
    "divya_cloud", "aryan_ai", "shreya_blockchain", "varun_devops", "nisha_security"
]


class RankingSystemTester:
    def __init__(self):
        self.client = None
        self.db = None
        self.ranking_service = None
        self.test_user_ids = []
        
    async def connect_database(self):
        """Connect to MongoDB database"""
        try:
            # Use simple local connection for testing
            mongodb_url = "mongodb://localhost:27017"
            database_name = "test_ranking_system"
            
            self.client = AsyncIOMotorClient(mongodb_url)
            self.db = self.client[database_name]
            self.ranking_service = RankingService(self.db)
            
            # Test connection
            await self.client.admin.command('ping')
            
            logger.info(f"Connected to database: {database_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            logger.error("Make sure MongoDB is running on localhost:27017")
            return False
    
    async def cleanup_test_data(self):
        """Clean up any existing test data"""
        try:
            logger.info("Cleaning up existing test data...")
            
            # Drop test collections
            await self.db[Collections.INTERNAL_USERS].delete_many({})
            await self.db[Collections.INTERNAL_USERS_PROFILE].delete_many({})
            await self.db[Collections.REGIONAL_RANKINGS].delete_many({})
            await self.db[Collections.UNIVERSITY_RANKINGS].delete_many({})
            
            logger.info("Test data cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def generate_test_data(self, num_users: int = 50):
        """Generate random test data for users"""
        try:
            logger.info(f"Generating {num_users} test users...")
            
            internal_users = []
            profile_users = []
            
            for i in range(num_users):
                # Generate a unique ObjectId for linking
                user_object_id = ObjectId()
                user_id = str(user_object_id)
                
                # Generate random user data
                name = random.choice(SAMPLE_NAMES)
                github_username = random.choice(SAMPLE_GITHUB_USERNAMES) + f"_{i}"
                university, university_short = random.choice(SAMPLE_UNIVERSITIES)
                district, state, region = random.choice(SAMPLE_DISTRICTS)
                
                # Generate random score (20-100 range with some clustering around good scores)
                if random.random() < 0.3:  # 30% high performers
                    score = random.uniform(80, 100)
                elif random.random() < 0.5:  # 50% medium performers
                    score = random.uniform(60, 80)
                else:  # 20% lower performers
                    score = random.uniform(20, 60)
                
                score = round(score, 1)
                
                # Create internal_users document (GitHub scan data)
                internal_user = {
                    "_id": user_object_id,
                    "user_id": user_id,
                    "username": github_username.lower(),
                    "overall_score": score,
                    "scan_completed": True,
                    "repositories_analyzed": random.randint(5, 25),
                    "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 30))
                }
                
                # Create internal_users_profile document (Profile form data)
                profile_user = {
                    "_id": user_object_id,  # Same ObjectId for linking
                    "name": name,
                    "github_username": github_username,
                    "university": university,
                    "university_short": university_short,
                    "district": district,
                    "state": state,
                    "region": region,
                    "nationality": "Indian",
                    "profile_completed": True,
                    "profile_updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 15))
                }
                
                internal_users.append(internal_user)
                profile_users.append(profile_user)
                self.test_user_ids.append(user_id)
            
            # Insert test data
            logger.info("Inserting internal_users data...")
            await self.db[Collections.INTERNAL_USERS].insert_many(internal_users)
            
            logger.info("Inserting internal_users_profile data...")
            await self.db[Collections.INTERNAL_USERS_PROFILE].insert_many(profile_users)
            
            logger.info(f"Successfully generated {num_users} test users")
            
            # Log some statistics
            districts_used = list(set([u['district'] for u in profile_users]))
            universities_used = list(set([u['university_short'] for u in profile_users]))
            
            logger.info(f"Test data spans {len(districts_used)} districts: {districts_used}")
            logger.info(f"Test data spans {len(universities_used)} universities: {universities_used}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating test data: {e}")
            return False
    
    async def test_data_joining(self):
        """Test the data joining functionality"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 1: Data Joining Functionality")
            logger.info("="*60)
            
            # Test get_joined_user_data
            joined_data = await self.ranking_service.get_joined_user_data()
            
            logger.info(f"✓ Successfully joined {len(joined_data)} users")
            
            if joined_data:
                sample = joined_data[0]
                logger.info(f"✓ Sample joined user:")
                logger.info(f"  - Name: {sample.get('name')}")
                logger.info(f"  - GitHub Username: {sample.get('github_username')}")
                logger.info(f"  - University: {sample.get('university')} ({sample.get('university_short')})")
                logger.info(f"  - Location: {sample.get('district')}, {sample.get('state')}")
                logger.info(f"  - Score: {sample.get('overall_score')}")
                
                # Validate required fields are present
                required_fields = ['user_id', 'name', 'github_username', 'university', 'district', 'overall_score']
                missing_fields = [field for field in required_fields if not sample.get(field)]
                
                if missing_fields:
                    logger.error(f"✗ Missing required fields: {missing_fields}")
                    return False
                else:
                    logger.info(f"✓ All required fields present in joined data")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Data joining test failed: {e}")
            return False
    
    async def test_ranking_calculations(self):
        """Test ranking calculation methods"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 2: Ranking Calculations")
            logger.info("="*60)
            
            # Test with sample scores
            test_scores = [95.5, 87.2, 92.1, 78.3, 87.2, 65.8, 88.9, 92.1, 73.4, 85.0]
            test_user_score = 87.2
            
            logger.info(f"Test scores: {sorted(test_scores, reverse=True)}")
            logger.info(f"User score: {test_user_score}")
            
            # Test percentile calculation
            percentile = self.ranking_service.calculate_percentile(test_user_score, test_scores)
            logger.info(f"✓ Calculated percentile: {percentile}%")
            
            # Test rank calculation
            rank = self.ranking_service.calculate_rank_position(test_user_score, test_scores)
            logger.info(f"✓ Calculated rank: {rank}")
            
            # Test statistics
            stats = self.ranking_service.calculate_statistics(test_scores)
            logger.info(f"✓ Statistics: {stats}")
            
            # Validate calculations
            expected_rank = 4  # There are 3 scores higher than 87.2 (95.5, 92.1, 92.1)
            if rank != expected_rank:
                logger.error(f"✗ Rank calculation error: expected {expected_rank}, got {rank}")
                return False
            
            # Validate percentile (should be around 30% - user scored better than 3 out of 10)
            expected_percentile = 30.0
            if abs(percentile - expected_percentile) > 1.0:
                logger.error(f"✗ Percentile calculation error: expected ~{expected_percentile}%, got {percentile}%")
                return False
            
            logger.info("✓ Ranking calculations are correct")
            return True
            
        except Exception as e:
            logger.error(f"✗ Ranking calculations test failed: {e}")
            return False
    
    async def test_regional_rankings(self):
        """Test regional ranking updates"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 3: Regional Rankings")
            logger.info("="*60)
            
            # Get all districts
            districts = await self.ranking_service.get_all_districts()
            logger.info(f"✓ Found {len(districts)} districts: {districts}")
            
            if not districts:
                logger.error("✗ No districts found")
                return False
            
            # Test updating rankings for first district
            test_district = districts[0]
            logger.info(f"Testing regional rankings for: {test_district}")
            
            result = await self.ranking_service.update_regional_rankings(test_district)
            logger.info(f"✓ Regional ranking update result: {result}")
            
            if not result.get("success"):
                logger.error(f"✗ Regional ranking update failed: {result.get('error')}")
                return False
            
            # Verify rankings were created
            rankings = await self.db[Collections.REGIONAL_RANKINGS].find({"district": test_district}).to_list(None)
            logger.info(f"✓ Created {len(rankings)} regional rankings for {test_district}")
            
            if rankings:
                # Check ranking data completeness
                sample_ranking = rankings[0]
                required_fields = ['user_id', 'name', 'district', 'overall_score', 'rank', 'percentile']
                missing_fields = [field for field in required_fields if field not in sample_ranking]
                
                if missing_fields:
                    logger.error(f"✗ Missing fields in ranking: {missing_fields}")
                    return False
                
                logger.info(f"✓ Sample ranking: {sample_ranking['name']} - Rank {sample_ranking['rank']}, Score {sample_ranking['overall_score']}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Regional rankings test failed: {e}")
            return False
    
    async def test_university_rankings(self):
        """Test university ranking updates"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 4: University Rankings")
            logger.info("="*60)
            
            # Get all universities
            universities = await self.ranking_service.get_all_universities()
            logger.info(f"✓ Found {len(universities)} universities: {universities}")
            
            if not universities:
                logger.error("✗ No universities found")
                return False
            
            # Test updating rankings for first university
            test_university = universities[0]
            logger.info(f"Testing university rankings for: {test_university}")
            
            result = await self.ranking_service.update_university_rankings(test_university)
            logger.info(f"✓ University ranking update result: {result}")
            
            if not result.get("success"):
                logger.error(f"✗ University ranking update failed: {result.get('error')}")
                return False
            
            # Verify rankings were created
            rankings = await self.db[Collections.UNIVERSITY_RANKINGS].find({"university_short": test_university}).to_list(None)
            logger.info(f"✓ Created {len(rankings)} university rankings for {test_university}")
            
            if rankings:
                # Check ranking data completeness
                sample_ranking = rankings[0]
                required_fields = ['user_id', 'name', 'university', 'overall_score', 'rank', 'percentile']
                missing_fields = [field for field in required_fields if field not in sample_ranking]
                
                if missing_fields:
                    logger.error(f"✗ Missing fields in ranking: {missing_fields}")
                    return False
                
                logger.info(f"✓ Sample ranking: {sample_ranking['name']} - Rank {sample_ranking['rank']}, Score {sample_ranking['overall_score']}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ University rankings test failed: {e}")
            return False
    
    async def test_batch_processing(self):
        """Test batch processing functionality"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 5: Batch Processing")
            logger.info("="*60)
            
            # Get districts and universities
            districts = await self.ranking_service.get_all_districts()
            universities = await self.ranking_service.get_all_universities()
            
            # Test batch regional updates
            if len(districts) > 1:
                test_districts = districts[:3]  # Test with first 3 districts
                logger.info(f"Testing batch regional updates for: {test_districts}")
                
                result = await self.ranking_service.batch_update_regional_rankings(test_districts, batch_size=2)
                logger.info(f"✓ Batch regional update result: {result}")
                
                if not result.get("success"):
                    logger.error(f"✗ Batch regional update failed")
                    return False
            
            # Test batch university updates
            if len(universities) > 1:
                test_universities = universities[:3]  # Test with first 3 universities
                logger.info(f"Testing batch university updates for: {test_universities}")
                
                result = await self.ranking_service.batch_update_university_rankings(test_universities, batch_size=2)
                logger.info(f"✓ Batch university update result: {result}")
                
                if not result.get("success"):
                    logger.error(f"✗ Batch university update failed")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Batch processing test failed: {e}")
            return False
    
    async def test_user_rankings_retrieval(self):
        """Test retrieving rankings for specific users"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 6: User Rankings Retrieval")
            logger.info("="*60)
            
            if not self.test_user_ids:
                logger.error("✗ No test user IDs available")
                return False
            
            # Test with first few users
            test_users = self.test_user_ids[:3]
            
            for user_id in test_users:
                logger.info(f"Testing rankings for user: {user_id}")
                
                # Get user rankings
                rankings = await self.ranking_service.get_user_rankings(user_id)
                logger.info(f"✓ User rankings: {rankings}")
                
                # Check if user has rankings
                has_regional = rankings.get("has_regional", False)
                has_university = rankings.get("has_university", False)
                
                logger.info(f"  - Has regional ranking: {has_regional}")
                logger.info(f"  - Has university ranking: {has_university}")
                
                if not has_regional and not has_university:
                    logger.warning(f"  - User {user_id} has no rankings (may need ranking update)")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ User rankings retrieval test failed: {e}")
            return False
    
    async def test_data_consistency(self):
        """Test data consistency validation"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 7: Data Consistency Validation")
            logger.info("="*60)
            
            # Run consistency validation
            result = await self.ranking_service.validate_ranking_data_consistency()
            logger.info(f"✓ Consistency validation result: {result}")
            
            total_inconsistencies = result.get("total_inconsistencies", 0)
            logger.info(f"✓ Found {total_inconsistencies} data inconsistencies")
            
            if total_inconsistencies > 0:
                logger.info("Inconsistencies found (expected for new test data):")
                for inconsistency in result.get("inconsistencies", [])[:5]:  # Show first 5
                    logger.info(f"  - {inconsistency}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Data consistency test failed: {e}")
            return False
    
    async def test_leaderboards(self):
        """Test leaderboard functionality"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 8: Leaderboard Functionality")
            logger.info("="*60)
            
            # Get sample district and university
            districts = await self.ranking_service.get_all_districts()
            universities = await self.ranking_service.get_all_universities()
            
            if districts:
                test_district = districts[0]
                logger.info(f"Testing regional leaderboard for: {test_district}")
                
                leaderboard = await self.ranking_service.get_regional_leaderboard(test_district, limit=5)
                logger.info(f"✓ Regional leaderboard ({len(leaderboard)} entries):")
                
                for i, entry in enumerate(leaderboard[:3], 1):
                    logger.info(f"  {i}. {entry.get('name', 'Unknown')} - Score: {entry.get('overall_score', 0)}")
            
            if universities:
                test_university = universities[0]
                logger.info(f"Testing university leaderboard for: {test_university}")
                
                leaderboard = await self.ranking_service.get_university_leaderboard(test_university, limit=5)
                logger.info(f"✓ University leaderboard ({len(leaderboard)} entries):")
                
                for i, entry in enumerate(leaderboard[:3], 1):
                    logger.info(f"  {i}. {entry.get('name', 'Unknown')} - Score: {entry.get('overall_score', 0)}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Leaderboard test failed: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Run all tests"""
        try:
            logger.info("🚀 Starting Comprehensive Unified Ranking System Test")
            logger.info("="*80)
            
            # Connect to database
            if not await self.connect_database():
                return False
            
            # Clean up and generate test data
            await self.cleanup_test_data()
            if not await self.generate_test_data(num_users=30):
                return False
            
            # Run all tests
            tests = [
                ("Data Joining", self.test_data_joining),
                ("Ranking Calculations", self.test_ranking_calculations),
                ("Regional Rankings", self.test_regional_rankings),
                ("University Rankings", self.test_university_rankings),
                ("Batch Processing", self.test_batch_processing),
                ("User Rankings Retrieval", self.test_user_rankings_retrieval),
                ("Data Consistency", self.test_data_consistency),
                ("Leaderboards", self.test_leaderboards)
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_func in tests:
                try:
                    if await test_func():
                        passed_tests += 1
                        logger.info(f"✅ {test_name}: PASSED")
                    else:
                        logger.error(f"❌ {test_name}: FAILED")
                except Exception as e:
                    logger.error(f"❌ {test_name}: ERROR - {e}")
            
            # Final results
            logger.info("\n" + "="*80)
            logger.info("🏁 TEST RESULTS SUMMARY")
            logger.info("="*80)
            logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
            logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            if passed_tests == total_tests:
                logger.info("🎉 ALL TESTS PASSED! Unified Ranking System is working correctly.")
                return True
            else:
                logger.error(f"⚠️  {total_tests - passed_tests} tests failed. Please review the errors above.")
                return False
            
        except Exception as e:
            logger.error(f"💥 Comprehensive test failed: {e}")
            return False
        
        finally:
            if self.client:
                self.client.close()
                logger.info("Database connection closed")


async def main():
    """Main function to run the comprehensive test"""
    tester = RankingSystemTester()
    success = await tester.run_comprehensive_test()
    
    if success:
        logger.info("✅ Testing completed successfully!")
        exit(0)
    else:
        logger.error("❌ Testing failed!")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())