
import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
load_dotenv()

async def check_score():
    # Get MongoDB URL directly from env or use the one from config if needed
    mongo_url = os.getenv("MONGODB_URL")
    if not mongo_url:
        print("❌ MONGODB_URL not found in .env")
        return

    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongo_url)
    db = client.broskieshub

    username = "raseen2305"
    print(f"🔍 Searching for user: {username}")

    # Check external_users first
    print("Checking 'external_users' collection...")
    user = await db.external_users.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})
    
    if not user:
        print("Checking 'internal_users' collection...")
        user = await db.internal_users.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})

    if user:
        print(f"✅ User found in collection!")
        print(f"   ID: {user.get('_id')}")
        print(f"   Overall Score: {user.get('overallScore')}")
        print(f"   Deep Analysis Complete: {user.get('deepAnalysisComplete')}")
        print(f"   ACID Scores: {user.get('acid_score')}")
        print(f"   Analysis ID: {user.get('analysis_id')}")
        if 'scan_date' in user:
             print(f"   Scan Date: {user.get('scan_date')}")
    else:
        print(f"❌ User {username} not found in any collection.")

if __name__ == "__main__":
    asyncio.run(check_score())
