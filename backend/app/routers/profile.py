"""
Profile and Regional Comparison API Endpoints
Refactored for Single Database Architecture (internal_users)
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from statistics import mean

from app.models.profile import (
    UserProfile, UserProfileCreate, UserProfileUpdate, UserOverallDetails,
    RegionalScore, UniversityScore,
    COUNTRIES, INDIAN_STATES, POPULAR_UNIVERSITIES, get_indian_colleges
)
from app.models.user import User
from app.core.security import get_current_user_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_database, Collections

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)

# Flag to track if indexes have been ensured
_indexes_ensured = False

async def ensure_profile_indexes(db):
    """Ensure required indexes exist on internal_users collection"""
    global _indexes_ensured
    if _indexes_ensured:
        return
    try:
        # Create index on github_username for fast lookups
        await db[Collections.INTERNAL_USERS].create_index("github_username")
        await db[Collections.INTERNAL_USERS_PROFILE].create_index("user_id")
        logger.info("✅ Ensured indexes on internal_users and internal_users_profile")
        _indexes_ensured = True
    except Exception as e:
        logger.warning(f"Failed to ensure indexes: {e}")

async def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    if not credentials:
        return None
    try:
        from app.core.security import verify_token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("user_id") or payload.get("sub") # Unified ID
        user_type = payload.get("user_type")
        return {"user_id": user_id, "user_type": user_type, "token_payload": payload}
    except Exception as e:
        return None

def convert_objectid_to_string(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

def generate_university_short(university: str) -> str:
    remove_words = ["university", "of", "the", "institute", "technology", "college"]
    words = university.lower().split()
    filtered = [w.strip(",") for w in words if w.strip(",") not in remove_words]
    if filtered and len(filtered[0]) <= 4:
        return filtered[0].lower()
    return "-".join(filtered[:3]) if filtered else university.lower()[:20]

def generate_region(nationality: str, state: str) -> str:
    return f"{nationality}-{state}"

@router.post("/setup", response_model=UserProfile)
async def setup_user_profile(
    profile_data: UserProfileCreate,
    current_user_token: dict = Depends(get_current_user_token)
):
    """Create or update user profile in internal_users_profile collection"""
    try:
        logger.info(f"⚡ [PROFILE_SETUP] Starting setup for token: {current_user_token}")
        
        db = await get_database()
        if db is not None:
            await ensure_profile_indexes(db)
        else:
            logger.error("❌ [PROFILE_SETUP] Database connection failed")
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Validate user_id from token
        user_id = current_user_token.get("user_id")
        if not user_id:
             logger.error(f"❌ [PROFILE_SETUP] Missing user_id in token: {current_user_token}")
             raise HTTPException(status_code=400, detail="Invalid token: missing user_id")

        logger.info(f"⚡ [PROFILE_SETUP] Processing for user_id: {user_id} (Type: {type(user_id)})")
        
        # 1. Find the Base User in internal_users to get the stable _id
        # First try to find by user_id (exact match)
        user_doc = await db[Collections.INTERNAL_USERS].find_one({"user_id": user_id})
        
        # If not found by user_id, try by ObjectId (for backward compatibility)
        if not user_doc:
            from bson import ObjectId
            if ObjectId.is_valid(user_id):
                 user_doc = await db[Collections.INTERNAL_USERS].find_one({"_id": ObjectId(user_id)})

        # If still not found, try to find by GitHub username from the profile data
        # This handles cases where the user already has scan data but different user_id
        if not user_doc:
            github_username = profile_data.github_username
            if github_username:
                # Try to find existing user by GitHub username (case-insensitive)
                user_doc = await db[Collections.INTERNAL_USERS].find_one({
                    "username": {"$regex": f"^{github_username}$", "$options": "i"}
                })
                if user_doc:
                    logger.info(f"✅ [PROFILE_SETUP] Found existing user by GitHub username: {github_username}")
                    # Update the user_id to match the current token
                    await db[Collections.INTERNAL_USERS].update_one(
                        {"_id": user_doc["_id"]},
                        {"$set": {"user_id": user_id, "updated_at": datetime.utcnow()}}
                    )
                    user_doc["user_id"] = user_id  # Update local copy

        # If still not found, create a basic internal_users entry
        if not user_doc:
            logger.info(f"⚠️ [PROFILE_SETUP] internal_user not found for {user_id}, constructing basic entry.")
            # Basic fields from token
            username = profile_data.github_username or current_user_token.get("github_username") or current_user_token.get("preferred_username")
            
            base_user_data = {
                "user_id": user_id,
                "username": username,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            # Remove None values
            base_user_data = {k: v for k, v in base_user_data.items() if v is not None}
            
            res = await db[Collections.INTERNAL_USERS].insert_one(base_user_data)
            user_doc = await db[Collections.INTERNAL_USERS].find_one({"_id": res.inserted_id})
        
        if not user_doc:
             raise HTTPException(status_code=500, detail="Could not find or create internal user document")

        # The ID to use for the profile document (1:1 mapping)
        internal_user_oid = user_doc["_id"]
        
        # Ensure github_username is defined
        # PRIORITY 1: Input from Profile Setup Form
        github_username = profile_data.github_username
        
        # PRIORITY 2: Existing in User Doc
        if not github_username:
            github_username = user_doc.get("github_username") or user_doc.get("username")
            
        # PRIORITY 3: Token
        if not github_username:
            github_username = current_user_token.get("github_username") or current_user_token.get("preferred_username") or ""
            
        logger.info(f"✅ [PROFILE_SETUP] Mapping profile to internal_user _id: {internal_user_oid}, username: {github_username}")

        # 2. Prepare Profile Data (Cleanup & Generation)
        profile_dict = profile_data.dict()
        if not profile_dict.get("university_short"):
             profile_dict["university_short"] = generate_university_short(profile_dict.get("university", ""))
        if not profile_dict.get("region"):
             profile_dict["region"] = generate_region(profile_dict.get("nationality", ""), profile_dict.get("state", ""))
             
        # 3. Upsert into internal_users_profile
        # We use _id = internal_user_oid to enforce the mapping
        profile_update_op = {
            "$set": {
                **profile_dict,
                "user_id": user_id,  # Store user_id string for reference/redundancy
                "internal_user_id": user_id, # Explicit link if usually user_id is the string ID
                "github_username": github_username, # Required for UserProfile model
                "profile_completed": True,
                "profile_updated_at": datetime.utcnow()
            }
        }
        
        await db[Collections.INTERNAL_USERS_PROFILE].update_one(
            {"_id": internal_user_oid},
            profile_update_op,
            upsert=True
        )
        
        # Fetch the saved profile to return
        saved_profile_doc = await db[Collections.INTERNAL_USERS_PROFILE].find_one({"_id": internal_user_oid})
        
        # Trigger ranking calculations after profile completion
        try:
            from app.services.ranking_service import RankingService
            ranking_service = RankingService(db)
            
            # Trigger ranking calculations for this user (async, don't wait)
            import asyncio
            asyncio.create_task(ranking_service.update_all_rankings_for_user(user_id))
            logger.info(f"✅ [PROFILE_SETUP] Triggered ranking calculations for user {user_id}")
        except Exception as ranking_error:
            # Don't fail profile setup if ranking calculation fails
            logger.warning(f"⚠️ [PROFILE_SETUP] Failed to trigger ranking calculations: {ranking_error}")
        
        # Merge back ID string if needed for Pydantic model
        if saved_profile_doc:
             saved_profile_doc["_id"] = str(saved_profile_doc["_id"])
             # Ensure the returned object matches expected schema
             return UserProfile(**saved_profile_doc)
        
        return UserProfile(**profile_dict)

    except Exception as e:
        import traceback
        logger.error(f"❌ [PROFILE_SETUP] Failed to setup user profile: {e}")
        logger.error(f"❌ [PROFILE_SETUP] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me", response_model=UserProfile)
async def get_my_profile(current_user_token: dict = Depends(get_current_user_token)):
    try:
        db = await get_database()
        user_id = current_user_token["user_id"]
        
        if db is not None:
            # 1. Resolve User Object ID
            user_doc = await db[Collections.INTERNAL_USERS].find_one({"user_id": user_id})
            if not user_doc:
                from bson import ObjectId
                if ObjectId.is_valid(user_id):
                     user_doc = await db[Collections.INTERNAL_USERS].find_one({"_id": ObjectId(user_id)})
            
            if not user_doc:
                raise HTTPException(status_code=404, detail="User not found")
                
            internal_user_oid = user_doc["_id"]

            # 2. Fetch Profile
            doc = await db[Collections.INTERNAL_USERS_PROFILE].find_one({"_id": internal_user_oid})
            
            if not doc or not doc.get("profile_completed"):
                raise HTTPException(status_code=404, detail="Profile not found")
            
            # Ensure github_username is present (fallback to user_doc if missing in profile)
            if not doc.get("github_username"):
                 doc["github_username"] = user_doc.get("github_username") or user_doc.get("username", "")
                 
            profile = UserProfile(**convert_objectid_to_string(doc))
        else:
            raise HTTPException(status_code=404, detail="DB not connected")
            
        return profile
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update", response_model=UserProfile)
async def update_user_profile(
    profile_updates: UserProfileUpdate,
    current_user_token: dict = Depends(get_current_user_token)
):
    try:
        db = await get_database()
        user_id = current_user_token["user_id"]
        
        update_data = {k: v for k, v in profile_updates.dict().items() if v is not None}
        update_data["profile_updated_at"] = datetime.utcnow()
        
        if db is not None:
            # 1. Resolve User Object ID
            user_doc = await db[Collections.INTERNAL_USERS].find_one({"user_id": user_id})
            if not user_doc:
                from bson import ObjectId
                if ObjectId.is_valid(user_id):
                     user_doc = await db[Collections.INTERNAL_USERS].find_one({"_id": ObjectId(user_id)})
            
            if not user_doc:
                 raise HTTPException(status_code=404, detail="User not found")
                 
            internal_user_oid = user_doc["_id"]

            await db[Collections.INTERNAL_USERS_PROFILE].update_one(
                {"_id": internal_user_oid},
                {"$set": update_data}
            )
            updated_doc = await db[Collections.INTERNAL_USERS_PROFILE].find_one({"_id": internal_user_oid})
            
            # Ensure github_username is present
            if updated_doc and not updated_doc.get("github_username"):
                 updated_doc["github_username"] = user_doc.get("github_username") or user_doc.get("username", "")

            profile = UserProfile(**convert_objectid_to_string(updated_doc))
        else:
            profile = UserProfile(**update_data)
            
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_profile_status(current_user_token: dict = Depends(get_current_user_token)):
    try:
        db = await get_database()
        user_id = current_user_token["user_id"]
        if db is not None:
            # 1. Check if user exists (optional, but safer)
            user_doc = await db[Collections.INTERNAL_USERS].find_one({"user_id": user_id})
            if not user_doc:
                from bson import ObjectId
                if ObjectId.is_valid(user_id):
                     user_doc = await db[Collections.INTERNAL_USERS].find_one({"_id": ObjectId(user_id)})
            
            if user_doc:
                internal_user_oid = user_doc["_id"]
                # 2. Check profile in new collection
                profile_doc = await db[Collections.INTERNAL_USERS_PROFILE].find_one({"_id": internal_user_oid})
                has_profile = profile_doc.get("profile_completed", False) if profile_doc else False
            else:
                has_profile = False
        else:
            has_profile = False
        return {"has_profile": has_profile, "user_id": user_id}
    except Exception as e:
        import traceback
        logger.error(f"❌ [PROFILE_STATUS] Error: {e}")
        logger.error(f"❌ [PROFILE_STATUS] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/countries")
async def get_countries():
    return {"countries": list(COUNTRIES.keys())}
    
@router.get("/data/states")
async def get_states(country: str = Query("IN")):
    if country == "IN": return {"states": INDIAN_STATES}
    return {"states": []}

@router.get("/data/universities")
async def get_universities():
    return {"universities": get_indian_colleges()}

# Legacy Sync Endpoint (Updated to use correct collection if feasible)
@router.get("/dashboard-data")
async def get_dashboard_data(current_user_token: dict = Depends(get_current_user_token)):
    """
    Get existing dashboard data for authenticated user from database
    Returns scan results, profile data, and rankings if available
    """
    try:
        logger.info(f"🔍 [DASHBOARD_DATA] Starting dashboard data fetch")
        
        db = await get_database()
        if db is None:
            logger.error("❌ [DASHBOARD_DATA] Database connection unavailable")
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        
        user_id = current_user_token["user_id"]
        logger.info(f"🔍 [DASHBOARD_DATA] Fetching dashboard data for user: {user_id}")
        
        # 1. Get user document from internal_users
        user_doc = await db[Collections.INTERNAL_USERS].find_one({"user_id": user_id})
        
        if not user_doc:
            from bson import ObjectId
            if ObjectId.is_valid(user_id):
                user_doc = await db[Collections.INTERNAL_USERS].find_one({"_id": ObjectId(user_id)})
        
        # If still not found, try to find by GitHub username from token
        if not user_doc:
            github_username = current_user_token.get("github_username") or current_user_token.get("preferred_username")
            if github_username:
                user_doc = await db[Collections.INTERNAL_USERS].find_one({
                    "username": {"$regex": f"^{github_username}$", "$options": "i"}
                })
        
        if not user_doc:
            logger.info(f"❌ [DASHBOARD_DATA] No user document found for user_id: {user_id}")
            return {
                "has_data": False,
                "message": "No scan data found. Please scan your repositories first."
            }
        
        # 2. Get profile data from internal_users_profile
        internal_user_oid = user_doc["_id"]
        profile_doc = await db[Collections.INTERNAL_USERS_PROFILE].find_one({"_id": internal_user_oid})
        
        # 3. Get rankings data
        regional_ranking = await db[Collections.REGIONAL_RANKINGS].find_one({"user_id": user_id})
        university_ranking = await db[Collections.UNIVERSITY_RANKINGS].find_one({"user_id": user_id})
        
        # 4. Check if we have scan data (overall_score indicates completed scan)
        overall_score = user_doc.get("overall_score", 0)
        has_scan_data = overall_score is not None and overall_score > 0
        has_profile = profile_doc and profile_doc.get("profile_completed", False)
        has_rankings = regional_ranking is not None or university_ranking is not None
        
        logger.info(f"🔍 [DASHBOARD_DATA] Data check - scan_data: {has_scan_data}, profile: {has_profile}, rankings: {has_rankings}")
        
        if not has_scan_data:
            return {
                "has_data": False,
                "message": "No scan data found. Please scan your repositories first."
            }
        
        # 5. Construct dashboard data in the format expected by the frontend
        dashboard_data = {
            "has_data": True,
            "userInfo": {
                "login": user_doc.get("username") or user_doc.get("github_username"),
                "name": profile_doc.get("full_name") if profile_doc else None,
                "bio": user_doc.get("bio"),
                "location": profile_doc.get("district") if profile_doc else None,
                "company": user_doc.get("company"),
                "public_repos": user_doc.get("repository_count", 0),
                "followers": user_doc.get("followers", 0),
                "following": user_doc.get("following", 0),
                "created_at": user_doc.get("created_at"),
                "avatar_url": user_doc.get("avatar_url")
            },
            "repositories": user_doc.get("repositories", []),
            "evaluation": {
                "overall_score": user_doc.get("overall_score", 0),
                "acid_scores": user_doc.get("acid_scores", {}),
                "evaluation_method": user_doc.get("evaluation_method", "standard")
            },
            "scanType": "self",
            "targetUsername": user_doc.get("username") or user_doc.get("github_username"),
            "repositoryCount": user_doc.get("repository_count", 0),
            "overallScore": user_doc.get("overall_score", 0),
            "languages": user_doc.get("languages", []),
            "techStack": user_doc.get("tech_stack", []),
            "roadmap": user_doc.get("roadmap", []),
            "lastScanDate": user_doc.get("updated_at"),
            # Add these fields to make the frontend think it's evaluated data
            "evaluatedCount": len([r for r in user_doc.get("repositories", []) if r.get("analysis")]),
            "analyzed": True,  # Mark as analyzed since we have data from database
            "profile": {
                "completed": has_profile,
                "data": convert_objectid_to_string(profile_doc) if profile_doc else None
            },
            "rankings": {
                "available": has_rankings,
                "regional": convert_objectid_to_string(regional_ranking) if regional_ranking else None,
                "university": convert_objectid_to_string(university_ranking) if university_ranking else None
            }
        }
        
        logger.info(f"✅ Dashboard data found for user {user_id}: scan_data={has_scan_data}, profile={has_profile}, rankings={has_rankings}")
        return dashboard_data
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"❌ [DASHBOARD_DATA] Failed to get dashboard data: {e}")
        logger.error(f"❌ [DASHBOARD_DATA] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")

@router.post("/sync-score")
async def sync_user_score(current_user_token: dict = Depends(get_current_user_token)):
    """Legacy Sync - Simply confirms data is in internal_users"""
    return {"message": "Data is automatically synchronized in Single Database Architecture."}