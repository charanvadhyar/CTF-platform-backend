from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.analytics import AdSlot, AdResponse
from app.models.user import UserInDB
from app.auth import get_current_admin_user
from app.database import get_database
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ads", tags=["advertisements"])

@router.get("/", response_model=List[AdResponse])
async def get_ads(position: str = None):
    """Get advertisements for specified position or all positions"""
    db = get_database()
    
    # Build query
    query = {"is_active": True}
    if position:
        if position not in ["top", "bottom", "sidebar", "banner"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid position. Must be one of: top, bottom, sidebar, banner"
            )
        query["position"] = position
    
    ads = await db.ads.find(query).to_list(length=None)
    
    # Update impression count
    if ads:
        ad_ids = [ad["_id"] for ad in ads]
        await db.ads.update_many(
            {"_id": {"$in": ad_ids}},
            {"$inc": {"impression_count": 1}}
        )
    
    # Convert to response format
    ad_responses = []
    for ad in ads:
        ad_responses.append(AdResponse(
            position=ad["position"],
            content=ad["content"],
            ad_id=str(ad["_id"])
        ))
    
    return ad_responses

@router.post("/click/{ad_id}")
async def track_ad_click(ad_id: str):
    """Track ad click"""
    db = get_database()
    
    # Check if ad exists
    ad = await db.ads.find_one({"_id": ad_id, "is_active": True})
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ad not found"
        )
    
    # Update click count
    await db.ads.update_one(
        {"_id": ad_id},
        {"$inc": {"click_count": 1}}
    )
    
    return {"message": "Click tracked successfully"}

# Admin routes for ad management
@router.post("/admin/create")
async def create_ad(
    position: str,
    content: str,
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """Create or update an advertisement (Admin only)"""
    if position not in ["top", "bottom", "sidebar", "banner"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid position. Must be one of: top, bottom, sidebar, banner"
        )
    
    db = get_database()
    
    # Check if ad with this position already exists
    existing_ad = await db.ads.find_one({"position": position})
    
    if existing_ad:
        # Update existing ad
        result = await db.ads.update_one(
            {"position": position},
            {"$set": {
                "content": content,
                "updated_at": datetime.utcnow()
            }}
        )
        logger.info(f"Admin {current_admin.email} updated ad for position: {position}")
        return {"message": f"Ad for position '{position}' updated successfully", "ad_id": str(existing_ad["_id"])}
    else:
        # Create new ad
        ad_data = {
            "position": position,
            "content": content,
            "is_active": True,
            "click_count": 0,
            "impression_count": 0,
            "created_at": datetime.utcnow()
        }
        
        result = await db.ads.insert_one(ad_data)
        logger.info(f"Admin {current_admin.email} created new ad for position: {position}")
        
        return {"message": "Ad created successfully", "ad_id": str(result.inserted_id)}

@router.get("/admin/list")
async def list_all_ads(
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """List all advertisements with statistics (Admin only)"""
    db = get_database()
    
    ads = await db.ads.find({}).sort("created_at", -1).to_list(length=None)
    
    ad_list = []
    for ad in ads:
        ad_list.append({
            "id": str(ad["_id"]),
            "position": ad["position"],
            "content": ad["content"],
            "is_active": ad["is_active"],
            "click_count": ad["click_count"],
            "impression_count": ad["impression_count"],
            "ctr": (ad["click_count"] / ad["impression_count"]) * 100 if ad["impression_count"] > 0 else 0,
            "created_at": ad.get("created_at", datetime.utcnow())
        })
    
    return {"ads": ad_list}

@router.patch("/admin/{ad_id}/toggle")
async def toggle_ad_status(
    ad_id: str,
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """Toggle ad active status (Admin only)"""
    db = get_database()
    
    # Check if ad exists
    ad = await db.ads.find_one({"_id": ad_id})
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ad not found"
        )
    
    # Toggle status
    new_status = not ad["is_active"]
    await db.ads.update_one(
        {"_id": ad_id},
        {"$set": {"is_active": new_status}}
    )
    
    logger.info(f"Admin {current_admin.email} toggled ad {ad_id} status to {new_status}")
    
    return {"message": f"Ad {'activated' if new_status else 'deactivated'} successfully"}

@router.delete("/admin/{ad_id}")
async def delete_ad(
    ad_id: str,
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """Delete advertisement (Admin only)"""
    db = get_database()
    
    # Check if ad exists
    ad = await db.ads.find_one({"_id": ad_id})
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ad not found"
        )
    
    # Delete ad
    await db.ads.delete_one({"_id": ad_id})
    
    logger.info(f"Admin {current_admin.email} deleted ad: {ad_id}")
    
    return {"message": "Ad deleted successfully"}
