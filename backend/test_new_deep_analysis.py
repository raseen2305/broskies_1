#!/usr/bin/env python3
"""
Test script for new optimized deep analysis endpoint
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_new_deep_analysis():
    """Test the new optimized deep analysis endpoint"""
    
    username = "raseen2305"
    
    print("🧪 Testing NEW Optimized Deep Analysis Endpoint")
    print("=" * 60)
    print()
    
    # Step 1: Initiate analysis
    print("1️⃣ Initiating analysis...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/analysis/quick-analyze/{username}",
            json={"max_evaluate": 15},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Analysis initiated successfully")
            print(f"   📊 Analysis ID: {data.get('analysis_id')}")
            print(f"   📊 Status: {data.get('status')}")
            print(f"   📊 Message: {data.get('message')}")
            print(f"   📊 Estimated time: {data.get('estimated_time')}")
            print()
            
            analysis_id = data.get('analysis_id')
            
            # Step 2: Poll for status
            print("2️⃣ Checking status...")
            for i in range(10):
                time.sleep(2)
                
                status_response = requests.get(
                    f"{BASE_URL}/api/analysis/quick-analyze-status/{username}/{analysis_id}",
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status_val = status_data.get('status')
                    progress = status_data.get('progress', {})
                    percentage = progress.get('percentage', 0)
                    
                    print(f"   📊 Status: {status_val} - {percentage}%")
                    
                    if status_val == 'complete':
                        print(f"   ✅ Analysis complete!")
                        print()
                        
                        # Step 3: Get results
                        print("3️⃣ Fetching results...")
                        results_response = requests.get(
                            f"{BASE_URL}/api/analysis/quick-analyze-results/{username}/{analysis_id}",
                            timeout=10
                        )
                        
                        if results_response.status_code == 200:
                            results = results_response.json()
                            print(f"   ✅ Results retrieved successfully")
                            print(f"   📊 Overall Score: {results.get('overallScore')}")
                            print(f"   📊 Evaluated: {results.get('evaluatedCount')} repos")
                            print(f"   📊 Flagship: {results.get('flagshipCount')}")
                            print(f"   📊 Significant: {results.get('significantCount')}")
                            print(f"   📊 Supporting: {results.get('supportingCount')}")
                        else:
                            print(f"   ❌ Failed to get results: {results_response.status_code}")
                            print(f"   {results_response.text}")
                        
                        break
                    elif status_val == 'failed':
                        print(f"   ❌ Analysis failed: {status_data.get('error')}")
                        break
                else:
                    print(f"   ❌ Status check failed: {status_response.status_code}")
                    break
            
        else:
            print(f"   ❌ Failed to initiate analysis: {response.status_code}")
            print(f"   {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("🧪 Test complete")


def compare_endpoints():
    """Compare old vs new endpoint responses"""
    
    username = "raseen2305"
    
    print("🔍 Comparing OLD vs NEW Endpoints")
    print("=" * 60)
    print()
    
    # Test OLD endpoint
    print("📍 OLD Endpoint: /scan/scan-external-user/{username}/analyze")
    try:
        old_response = requests.post(
            f"{BASE_URL}/scan/scan-external-user/{username}/analyze",
            json={"max_evaluate": 15},
            timeout=10
        )
        print(f"   Status: {old_response.status_code}")
        if old_response.status_code == 200:
            print(f"   Response keys: {list(old_response.json().keys())}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test NEW endpoint
    print("📍 NEW Endpoint: /api/analysis/quick-analyze/{username}")
    try:
        new_response = requests.post(
            f"{BASE_URL}/api/analysis/quick-analyze/{username}",
            json={"max_evaluate": 15},
            timeout=10
        )
        print(f"   Status: {new_response.status_code}")
        if new_response.status_code == 200:
            print(f"   Response keys: {list(new_response.json().keys())}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        compare_endpoints()
    else:
        test_new_deep_analysis()
