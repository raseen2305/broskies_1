
import requests
import json
import sys

def check_endpoint():
    try:
        url = "http://localhost:8000/api/scan/quick-scan/raseen2305"
        print(f"🚀 Hitting endpoint: {url}")
        
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Handle wrapped response format
            if 'data' in data:
                inner_data = data['data']
            else:
                inner_data = data
                
            print(f"✅ Response received!")
            print(f"   Success: {data.get('success')}")
            print(f"   Processing Time: {data.get('processingTime')}")
            print(f"   Overall Score: {inner_data.get('overallScore')}")
            print(f"   Scan Type: {inner_data.get('scanType')}")
            print(f"   Deep Analysis Complete: {inner_data.get('deepAnalysisComplete')}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_endpoint()
