#!/usr/bin/env python3
"""
Test script for the unified ranking system core logic without database.
This script tests the ranking calculations and validation logic with random data.
"""

import logging
import random
from datetime import datetime
from typing import List, Dict, Any

# Import the ranking service
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ranking_service import RankingService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample data for generating random users
SAMPLE_NAMES = [
    "Arjun Kumar", "Priya Sharma", "Rahul Patel", "Sneha Reddy", "Vikram Singh",
    "Ananya Gupta", "Karthik Nair", "Meera Iyer", "Rohan Joshi", "Kavya Menon",
    "Aditya Agarwal", "Riya Bansal", "Siddharth Rao", "Pooja Verma", "Nikhil Shah"
]

SAMPLE_UNIVERSITIES = [
    ("IIT Madras", "iit-madras"),
    ("IIT Delhi", "iit-delhi"),
    ("Anna University", "anna-university"),
    ("VIT Vellore", "vit-vellore"),
    ("Kalasalingam Institute", "kalasalingam-institute")
]

SAMPLE_DISTRICTS = [
    ("Chennai", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Coimbatore", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Madurai", "Tamil Nadu", "IN-Tamil Nadu"),
    ("Bangalore", "Karnataka", "IN-Karnataka"),
    ("Hyderabad", "Telangana", "IN-Telangana")
]

SAMPLE_GITHUB_USERNAMES = [
    "dev_arjun", "priya_codes", "rahul_dev", "sneha_tech", "vikram_py",
    "ananya_js", "karthik_react", "meera_ml", "rohan_backend", "kavya_frontend"
]


class RankingLogicTester:
    def __init__(self):
        # Create a mock ranking service (without database)
        self.ranking_service = RankingService(None)  # Pass None for database
        self.test_users = []
    
    def generate_test_users(self, num_users: int = 20) -> List[Dict[str, Any]]:
        """Generate random test user data"""
        users = []
        
        for i in range(num_users):
            name = random.choice(SAMPLE_NAMES)
            github_username = random.choice(SAMPLE_GITHUB_USERNAMES) + f"_{i}"
            university, university_short = random.choice(SAMPLE_UNIVERSITIES)
            district, state, region = random.choice(SAMPLE_DISTRICTS)
            
            # Generate random score with realistic distribution
            if random.random() < 0.3:  # 30% high performers
                score = random.uniform(80, 100)
            elif random.random() < 0.5:  # 50% medium performers
                score = random.uniform(60, 80)
            else:  # 20% lower performers
                score = random.uniform(20, 60)
            
            score = round(score, 1)
            
            user = {
                "user_id": f"user_{i}",
                "name": name,
                "github_username": github_username,
                "university": university,
                "university_short": university_short,
                "district": district,
                "state": state,
                "region": region,
                "overall_score": score,
                "profile_completed": True,
                "nationality": "Indian"
            }
            
            users.append(user)
        
        self.test_users = users
        return users
    
    def test_user_validation(self) -> bool:
        """Test user data validation logic"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 1: User Data Validation")
            logger.info("="*60)
            
            # Test with valid user
            valid_user = {
                "user_id": "test_user_1",
                "name": "Test User",
                "github_username": "test_user",
                "university": "Test University",
                "university_short": "test-uni",
                "district": "Test District",
                "state": "Test State",
                "overall_score": 85.5,
                "profile_completed": True
            }
            
            is_valid = self.ranking_service.validate_user_completeness(valid_user)
            logger.info(f"✓ Valid user validation: {is_valid}")
            
            if not is_valid:
                logger.error("✗ Valid user was marked as invalid")
                return False
            
            # Test with invalid user (missing fields)
            invalid_user = {
                "user_id": "test_user_2",
                "name": "",  # Empty name
                "github_username": "test_user_2",
                "university": "Test University",
                "district": None,  # Missing district
                "overall_score": 85.5,
                "profile_completed": False  # Incomplete profile
            }
            
            is_invalid = self.ranking_service.validate_user_completeness(invalid_user)
            logger.info(f"✓ Invalid user validation: {is_invalid}")
            
            if is_invalid:
                logger.error("✗ Invalid user was marked as valid")
                return False
            
            logger.info("✓ User validation logic working correctly")
            return True
            
        except Exception as e:
            logger.error(f"✗ User validation test failed: {e}")
            return False
    
    def test_percentile_calculations(self) -> bool:
        """Test percentile calculation logic"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 2: Percentile Calculations")
            logger.info("="*60)
            
            # Test with known scores
            test_scores = [95.5, 87.2, 92.1, 78.3, 87.2, 65.8, 88.9, 92.1, 73.4, 85.0]
            sorted_scores = sorted(test_scores, reverse=True)
            
            logger.info(f"Test scores (sorted): {sorted_scores}")
            
            # Test specific cases
            test_cases = [
                (95.5, 90.0),  # Top score should be ~90% (9 out of 10 users scored lower)
                (65.8, 10.0),  # Bottom score should be ~10% (1 out of 10 users scored lower)
                (87.2, 50.0),  # Middle score should be around 50%
            ]
            
            for user_score, expected_percentile in test_cases:
                calculated_percentile = self.ranking_service.calculate_percentile(user_score, test_scores)
                logger.info(f"Score {user_score}: {calculated_percentile}% (expected ~{expected_percentile}%)")
                
                # Allow some tolerance in percentile calculation
                if abs(calculated_percentile - expected_percentile) > 20:
                    logger.error(f"✗ Percentile calculation error for score {user_score}")
                    return False
            
            # Test edge cases
            single_score = [85.0]
            single_percentile = self.ranking_service.calculate_percentile(85.0, single_score)
            logger.info(f"Single user percentile: {single_percentile}% (should be 100%)")
            
            if single_percentile != 100.0:
                logger.error("✗ Single user percentile should be 100%")
                return False
            
            empty_scores = []
            empty_percentile = self.ranking_service.calculate_percentile(85.0, empty_scores)
            logger.info(f"Empty scores percentile: {empty_percentile}% (should be 0%)")
            
            if empty_percentile != 0.0:
                logger.error("✗ Empty scores percentile should be 0%")
                return False
            
            logger.info("✓ Percentile calculations working correctly")
            return True
            
        except Exception as e:
            logger.error(f"✗ Percentile calculation test failed: {e}")
            return False
    
    def test_rank_calculations(self) -> bool:
        """Test rank position calculation logic"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 3: Rank Position Calculations")
            logger.info("="*60)
            
            # Test with known scores
            test_scores = [95.5, 87.2, 92.1, 78.3, 87.2, 65.8, 88.9, 92.1, 73.4, 85.0]
            
            # Test specific cases
            test_cases = [
                (95.5, 1),   # Highest score should be rank 1
                (92.1, 2),   # Second highest (tied) should be rank 2
                (88.9, 4),   # Next score should be rank 4 (after 2 tied at rank 2)
                (65.8, 10),  # Lowest score should be rank 10
            ]
            
            for user_score, expected_rank in test_cases:
                calculated_rank = self.ranking_service.calculate_rank_position(user_score, test_scores)
                logger.info(f"Score {user_score}: Rank {calculated_rank} (expected {expected_rank})")
                
                if calculated_rank != expected_rank:
                    logger.error(f"✗ Rank calculation error for score {user_score}")
                    return False
            
            # Test tie handling
            tied_scores = [90.0, 85.0, 85.0, 85.0, 70.0]
            
            # All users with score 85.0 should get rank 2
            for score in [85.0]:
                rank = self.ranking_service.calculate_rank_position(score, tied_scores)
                logger.info(f"Tied score {score}: Rank {rank} (should be 2)")
                
                if rank != 2:
                    logger.error(f"✗ Tie handling error for score {score}")
                    return False
            
            # User with score 70.0 should get rank 5 (after 3 tied users at rank 2)
            rank_70 = self.ranking_service.calculate_rank_position(70.0, tied_scores)
            logger.info(f"Score 70.0: Rank {rank_70} (should be 5)")
            
            if rank_70 != 5:
                logger.error(f"✗ Rank calculation after ties error")
                return False
            
            logger.info("✓ Rank calculations working correctly")
            return True
            
        except Exception as e:
            logger.error(f"✗ Rank calculation test failed: {e}")
            return False
    
    def test_statistics_calculations(self) -> bool:
        """Test statistical calculations"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 4: Statistics Calculations")
            logger.info("="*60)
            
            # Test with known scores
            test_scores = [80.0, 85.0, 90.0, 75.0, 95.0]  # Simple scores for easy verification
            
            stats = self.ranking_service.calculate_statistics(test_scores)
            logger.info(f"Statistics for {test_scores}: {stats}")
            
            # Verify calculations
            expected_avg = 85.0  # (80+85+90+75+95)/5 = 85
            expected_median = 85.0  # Middle value when sorted: [75, 80, 85, 90, 95]
            expected_min = 75.0
            expected_max = 95.0
            expected_total = 5
            
            if abs(stats["avg_score"] - expected_avg) > 0.1:
                logger.error(f"✗ Average calculation error: {stats['avg_score']} != {expected_avg}")
                return False
            
            if abs(stats["median_score"] - expected_median) > 0.1:
                logger.error(f"✗ Median calculation error: {stats['median_score']} != {expected_median}")
                return False
            
            if stats["min_score"] != expected_min:
                logger.error(f"✗ Min calculation error: {stats['min_score']} != {expected_min}")
                return False
            
            if stats["max_score"] != expected_max:
                logger.error(f"✗ Max calculation error: {stats['max_score']} != {expected_max}")
                return False
            
            if stats["total_users"] != expected_total:
                logger.error(f"✗ Total users error: {stats['total_users']} != {expected_total}")
                return False
            
            # Test empty scores
            empty_stats = self.ranking_service.calculate_statistics([])
            logger.info(f"Empty scores statistics: {empty_stats}")
            
            if empty_stats["total_users"] != 0:
                logger.error("✗ Empty scores should have 0 total users")
                return False
            
            logger.info("✓ Statistics calculations working correctly")
            return True
            
        except Exception as e:
            logger.error(f"✗ Statistics calculation test failed: {e}")
            return False
    
    def test_realistic_scenario(self) -> bool:
        """Test with realistic user data"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST 5: Realistic Scenario Test")
            logger.info("="*60)
            
            # Generate test users
            users = self.generate_test_users(15)
            logger.info(f"Generated {len(users)} test users")
            
            # Group users by district for regional ranking simulation
            districts = {}
            for user in users:
                district = user["district"]
                if district not in districts:
                    districts[district] = []
                districts[district].append(user)
            
            logger.info(f"Users distributed across {len(districts)} districts: {list(districts.keys())}")
            
            # Test ranking calculations for each district
            for district, district_users in districts.items():
                if len(district_users) < 2:
                    continue  # Skip districts with only 1 user
                
                logger.info(f"\nTesting rankings for {district} ({len(district_users)} users):")
                
                scores = [u["overall_score"] for u in district_users]
                sorted_users = sorted(district_users, key=lambda x: x["overall_score"], reverse=True)
                
                # Calculate rankings for each user
                for i, user in enumerate(sorted_users[:3]):  # Show top 3
                    percentile = self.ranking_service.calculate_percentile(user["overall_score"], scores)
                    rank = self.ranking_service.calculate_rank_position(user["overall_score"], scores)
                    
                    logger.info(f"  {rank}. {user['name']} - Score: {user['overall_score']}, Percentile: {percentile}%")
                    
                    # Validate that rank matches position in sorted list
                    expected_rank = i + 1
                    if rank != expected_rank:
                        # Check for ties
                        tied_users = [u for u in sorted_users if u["overall_score"] == user["overall_score"]]
                        if len(tied_users) == 1:  # No ties, rank should match position
                            logger.error(f"✗ Rank mismatch for {user['name']}: got {rank}, expected {expected_rank}")
                            return False
            
            # Test university grouping
            universities = {}
            for user in users:
                university = user["university_short"]
                if university not in universities:
                    universities[university] = []
                universities[university].append(user)
            
            logger.info(f"\nUsers distributed across {len(universities)} universities: {list(universities.keys())}")
            
            # Validate that all users have complete data
            valid_users = 0
            for user in users:
                if self.ranking_service.validate_user_completeness(user):
                    valid_users += 1
            
            logger.info(f"✓ {valid_users}/{len(users)} users have complete data")
            
            if valid_users != len(users):
                logger.error("✗ Some generated users have incomplete data")
                return False
            
            logger.info("✓ Realistic scenario test passed")
            return True
            
        except Exception as e:
            logger.error(f"✗ Realistic scenario test failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all ranking logic tests"""
        try:
            logger.info("🚀 Starting Unified Ranking System Logic Tests")
            logger.info("="*80)
            
            tests = [
                ("User Data Validation", self.test_user_validation),
                ("Percentile Calculations", self.test_percentile_calculations),
                ("Rank Position Calculations", self.test_rank_calculations),
                ("Statistics Calculations", self.test_statistics_calculations),
                ("Realistic Scenario", self.test_realistic_scenario)
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_func in tests:
                try:
                    if test_func():
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
                logger.info("🎉 ALL TESTS PASSED! Ranking logic is working correctly.")
                return True
            else:
                logger.error(f"⚠️  {total_tests - passed_tests} tests failed.")
                return False
            
        except Exception as e:
            logger.error(f"💥 Test execution failed: {e}")
            return False


def main():
    """Main function to run the logic tests"""
    tester = RankingLogicTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("✅ All ranking logic tests passed!")
        exit(0)
    else:
        logger.error("❌ Some tests failed!")
        exit(1)


if __name__ == "__main__":
    main()