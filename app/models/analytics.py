from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.models.user import PyObjectId

class VisitInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: Optional[str] = None  # None for anonymous visits
    challenge_id: str
    ip_address: str
    user_agent: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ChallengeVisitStats(BaseModel):
    challenge_id: str
    challenge_title: str
    total_visits: int
    unique_visitors: int
    solve_rate: float
    avg_time_to_solve: Optional[float] = None

class UserAnalytics(BaseModel):
    total_users: int
    active_users_today: int
    active_users_week: int
    new_registrations_today: int
    top_scorers: list

class PlatformAnalytics(BaseModel):
    total_challenges: int
    total_submissions: int
    total_visits: int
    success_rate: float
    most_popular_challenges: list
    most_difficult_challenges: list

class AdSlot(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    position: str = Field(..., pattern="^(top|bottom|sidebar|banner)$")
    content: str
    is_active: bool = Field(default=True)
    click_count: int = Field(default=0)
    impression_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AdResponse(BaseModel):
    position: str
    content: str
    ad_id: str
