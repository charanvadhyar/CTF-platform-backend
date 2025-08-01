"""
API endpoint to clean up duplicate ads and enforce uniqueness constraints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
from ..dependencies import get_current_admin_user, get_database

# Create router
router = APIRouter(
    prefix="/ads/admin",
    tags=["ads", "admin"],
    responses={404: {"description": "Not found"}},
)

@router.post("/cleanup", response_model=dict)
async def cleanup_ads(db: AsyncIOMotorClient = Depends(get_database), 
                     current_user: dict = Depends(get_current_admin_user)):
    """
    Admin-only endpoint to clean up duplicate ads in the database.
    Keeps only the most recent ad for each position and creates a unique index.
    """
    try:
        # Get the ads collection
        ads_collection = db.ads
        
        # Find all unique positions in the ads collection
        positions = await ads_collection.distinct("position")
        
        # Track statistics
        total_removed = 0
        processed_positions = []
        
        # For each position, keep the most recent ad and delete others
        for position in positions:
            # Find all ads for this position, sorted by creation date (newest first)
            ads_cursor = ads_collection.find({"position": position}).sort("created_at", DESCENDING)
            ads_list = await ads_cursor.to_list(length=None)
            
            if len(ads_list) <= 1:
                processed_positions.append({"position": position, "duplicates_removed": 0})
                continue
            
            # Keep the first (most recent) ad
            most_recent_ad = ads_list[0]
            
            # Get IDs of all other ads to delete
            duplicate_ids = [ad.get("_id") for ad in ads_list[1:]]
            
            # Delete all duplicates
            result = await ads_collection.delete_many({"_id": {"$in": duplicate_ids}})
            
            processed_positions.append({
                "position": position,
                "duplicates_removed": result.deleted_count
            })
            
            total_removed += result.deleted_count
        
        # Create unique index on position field to prevent future duplicates
        # This might fail if there are still duplicates somehow
        try:
            await ads_collection.create_index("position", unique=True)
            index_created = True
        except Exception as e:
            index_created = False
        
        return {
            "success": True,
            "total_duplicates_removed": total_removed,
            "positions_processed": processed_positions,
            "unique_index_created": index_created
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clean up duplicate ads: {str(e)}"
        )
