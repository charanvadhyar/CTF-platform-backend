from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime

from app.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])

class VisitRequest(BaseModel):
    page: str
    user_agent: str
    ip: Optional[str] = None

@router.post("/visits")
async def track_page_visit(visit_data: VisitRequest, request: Request):
    """Track a page visit for analytics"""
    try:
        db = get_database()
        
        # Get client IP from request
        client_ip = request.client.host if request.client else "unknown"
        if visit_data.ip and visit_data.ip != "client":
            client_ip = visit_data.ip
        
        # Create visit record
        visit_record = {
            "page": visit_data.page,
            "ip": client_ip,
            "user_agent": visit_data.user_agent,
            "timestamp": datetime.utcnow(),
            "user_id": None  # Anonymous visit for now
        }
        
        # Insert visit record
        await db.visits.insert_one(visit_record)
        
        logger.info(f"Page visit tracked: {visit_data.page} from {client_ip}")
        return {"message": "Visit tracked successfully"}
        
    except Exception as e:
        logger.error(f"Failed to track page visit: {e}")
        raise HTTPException(status_code=500, detail="Failed to track visit")

@router.get("/visits/stats")
async def get_visit_stats():
    """Get basic visit statistics"""
    try:
        db = get_database()
        
        total_visits = await db.visits.count_documents({})
        
        # Get top pages
        pipeline = [
            {"$group": {"_id": "$page", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        top_pages = await db.visits.aggregate(pipeline).to_list(length=None)
        
        return {
            "total_visits": total_visits,
            "top_pages": [{"page": item["_id"], "visits": item["count"]} for item in top_pages]
        }
        
    except Exception as e:
        logger.error(f"Failed to get visit stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get visit statistics")
