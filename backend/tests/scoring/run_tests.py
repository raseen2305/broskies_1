"""
Test runner for scoring system tests
"""

import sys
import pytest


def run_all_tests():
    """Run all scoring system tests"""
    print("=" * 70)
    print("Running Scoring System Tests")
    print("=" * 70)
    
    # Run tests with verbose output
    args = [
        'backend/tests/scoring/',
        '-v',
        '--tb=short',
        '--color=yes'
    ]
    
    exit_code = pytest.main(args)
    
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 70)
    
    return exit_code


def run_specific_test(test_file):
    """Run a specific test file"""
    print(f"Running tests from: {test_file}")
    exit_code = pytest.main([test_file, '-v'])
    return exit_code


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific test file
        exit_code = run_specific_test(sys.argv[1])
    else:
        # Run all tests
        exit_code = run_all_tests()
    
    sys.exit(exit_code)
