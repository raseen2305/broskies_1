"""
Debug endpoints for ranking system issues
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
import logging

from app.core.security import get_current_user_token
from app.services.ranking_service import RankingService
from app.database import get_database, Collections

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/user-data")
async def debug_user_data(
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Debug endpoint to check user data linking issues
    """
    try:
        db = await get_database()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        debug_info = {
            "user_id": user_id,
            "timestamp": "2024-12-12T12:00:00Z"
        }
        
        # 1. Check internal_users collection
        internal_users = await db[Collections.INTERNAL_USERS].find(
            {"user_id": user_id}
        ).to_list(None)
        
        debug_info["internal_users"] = {
            "count": len(internal_users),
            "records": []
        }
        
        for user in internal_users:
            debug_info["internal_users"]["records"].append({
                "_id": str(user.get('_id')),
                "user_id": user.get('user_id'),
                "username": user.get('username'),
                "overall_score": user.get('overall_score'),
                "updated_at": str(user.get('updated_at'))
            })
        
        # 2. Check internal_users_profile collection
        profile_users = await db[Collections.INTERNAL_USERS_PROFILE].find(
            {"user_id": user_id}
        ).to_list(None)
        
        debug_info["profile_users"] = {
            "count": len(profile_users),
            "records": []
        }
        
        for user in profile_users:
            debug_info["profile_users"]["records"].append({
                "_id": str(user.get('_id')),
                "user_id": user.get('user_id'),
                "github_username": user.get('github_username'),
                "full_name": user.get('full_name'),
                "profile_completed": user.get('profile_completed'),
                "university": user.get('university'),
                "district": user.get('district')
            })
        
        # 3. Check _id matching
        if internal_users and profile_users:
            internal_ids = [str(u['_id']) for u in internal_users]
            profile_ids = [str(u['_id']) for u in profile_users]
            matching_ids = list(set(internal_ids) & set(profile_ids))
            
            debug_info["id_matching"] = {
                "internal_ids": internal_ids,
                "profile_ids": profile_ids,
                "matching_ids": matching_ids,
                "has_match": len(matching_ids) > 0
            }
        
        # 4. Test RankingService join
        ranking_service = RankingService(db)
        joined_data = await ranking_service.get_joined_user_data({"user_id": user_id})
        
        debug_info["joined_data"] = {
            "count": len(joined_data),
            "records": []
        }
        
        for user_data in joined_data:
            debug_info["joined_data"]["records"].append({
                "user_id": user_data.get('user_id'),
                "github_username": user_data.get('github_username'),
                "name": user_data.get('name'),
                "overall_score": user_data.get('overall_score'),
                "university": user_data.get('university'),
                "district": user_data.get('district'),
                "profile_completed": user_data.get('profile_completed')
            })
        
        # 5. Check existing rankings
        regional_rankings = await db[Collections.REGIONAL_RANKINGS].find(
            {"user_id": user_id}
        ).to_list(None)
        
        university_rankings = await db[Collections.UNIVERSITY_RANKINGS].find(
            {"user_id": user_id}
        ).to_list(None)
        
        debug_info["existing_rankings"] = {
            "regional_count": len(regional_rankings),
            "university_count": len(university_rankings)
        }
        
        # 6. Diagnosis
        diagnosis = []
        
        if not internal_users:
            diagnosis.append("❌ No scan data found - user needs to complete repository scan")
        elif not profile_users:
            diagnosis.append("❌ No profile data found - user needs to complete profile setup")
        elif internal_users and profile_users:
            if not debug_info["id_matching"]["has_match"]:
                diagnosis.append("❌ _id mismatch - data linking issue")
            elif not joined_data:
                diagnosis.append("❌ Data join failed - check profile_completed status")
            elif joined_data:
                diagnosis.append("✅ Data join successful - should have rankings")
        
        debug_info["diagnosis"] = diagnosis
        
        return debug_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug failed: {str(e)}"
        )

@router.post("/fix-data-linking")
async def fix_data_linking(
    current_user_token: dict = Depends(get_current_user_token)
):
    """
    Attempt to fix data linking issues for the current user
    """
    try:
        db = await get_database()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable"
            )
        
        user_id = current_user_token["user_id"]
        
        # Get data
        internal_users = await db[Collections.INTERNAL_USERS].find(
            {"user_id": user_id}
        ).to_list(None)
        
        profile_users = await db[Collections.INTERNAL_USERS_PROFILE].find(
            {"user_id": user_id}
        ).to_list(None)
        
        if not internal_users:
            return {
                "success": False,
                "error": "No scan data found - complete repository scan first"
            }
        
        if not profile_users:
            return {
                "success": False,
                "error": "No profile data found - complete profile setup first"
            }
        
        fixes_applied = []
        
        # Fix 1: _id mismatch
        internal_user = internal_users[0]
        profile_user = profile_users[0]
        
        if internal_user['_id'] != profile_user['_id']:
            # Update profile to use scan record's _id
            await db[Collections.INTERNAL_USERS_PROFILE].update_one(
                {"user_id": user_id},
                {"$set": {"_id": internal_user['_id']}}
            )
            fixes_applied.append("Fixed _id mismatch")
        
        # Fix 2: Profile completion status
        if not profile_user.get('profile_completed'):
            await db[Collections.INTERNAL_USERS_PROFILE].update_one(
                {"user_id": user_id},
                {"$set": {"profile_completed": True}}
            )
            fixes_applied.append("Set profile_completed = True")
        
        # Fix 3: Trigger ranking calculation
        ranking_service = RankingService(db)
        result = await ranking_service.update_all_rankings_for_user(user_id)
        
        if result["success"]:
            fixes_applied.append("Calculated rankings")
        
        return {
            "success": True,
            "fixes_applied": fixes_applied,
            "ranking_result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fix endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fix failed: {str(e)}"
        )