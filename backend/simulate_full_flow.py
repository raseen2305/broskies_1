
import requests
import time
import sys
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

USERNAME = "raseen2305"
BASE_URL = "http://localhost:8000"

def run_quick_scan():
    print(f"\n🚀 [1/3] Running Quick Scan for {USERNAME}...")
    try:
        url = f"{BASE_URL}/api/scan/quick-scan/{USERNAME}"
        # Quick scan GET is for existing/external users
        response = requests.get(url) 
        if response.status_code == 200:
            print("✅ Quick Scan Successful")
            data = response.json()
            # print(f"   Response: {data}")
            return True
        else:
            print(f"❌ Quick Scan Failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error running Quick Scan: {e}")
        return False

def run_deep_analysis():
    print(f"\n🚀 [2/3] Initiating Deep Analysis for {USERNAME}...")
    try:
        url = f"{BASE_URL}/api/analysis/deep-analyze/{USERNAME}"
        response = requests.post(url, json={"max_repositories": 5}) # Limit repos for speed
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Deep Analysis Started")
            print(f"   Analysis ID: {data.get('analysis_id')}")
            print(f"   Estimated Time: {data.get('estimated_time')}")
            return data.get('analysis_id')
        else:
            print(f"❌ Deep Analysis Failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error initiating Deep Analysis: {e}")
        return None

async def poll_for_score(timeout=120):
    print(f"\n🚀 [3/3] Polling Database for Overall Score...")
    mongo_url = os.getenv("MONGODB_URL")
    if not mongo_url:
        print("❌ MONGODB_URL not found")
        return

    client = AsyncIOMotorClient(mongo_url)
    db = client.broskieshub
    
    start_time = time.time()
    
    while (time.time() - start_time) < timeout:
        # Check both collections
        user = await db.external_users.find_one({"username": {"$regex": f"^{USERNAME}$", "$options": "i"}})
        if not user:
            user = await db.internal_users.find_one({"username": {"$regex": f"^{USERNAME}$", "$options": "i"}})
            
        if user:
            score = user.get('overallScore', 0)
            completed = user.get('deepAnalysisComplete', False)
            
            sys.stdout.write(f"\r⏳ Elapsed: {int(time.time()-start_time)}s | Score: {score} | Complete: {completed}")
            sys.stdout.flush()
            
            if score > 0 or completed:
                print(f"\n\n✅ FINAL RESULT FOUND:")
                print(f"   Overall Score: {score}")
                print(f"   ACID Scores: {user.get('acid_score')}")
                print(f"   Analysis Time: {int(time.time()-start_time)}s")
                return
        
        await asyncio.sleep(2)
        
    print("\n\n❌ Timeout waiting for score.")

if __name__ == "__main__":
    if run_quick_scan():
        analysis_id = run_deep_analysis()
        if analysis_id:
            asyncio.run(poll_for_score())
