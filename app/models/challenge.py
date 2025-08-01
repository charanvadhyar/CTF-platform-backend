from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId
from app.models.user import PyObjectId

class ChallengeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1)
    intro: Optional[str] = None
    play_instructions: Optional[str] = None
    points: int = Field(default=10, ge=1, le=100)
    difficulty: str = Field(default="easy", pattern="^(easy|medium|hard)$")
    is_active: bool = Field(default=True)

class ChallengeCreate(ChallengeBase):
    solution_type: str = Field(..., pattern="^(flag|input|cookie|header|file)$")
    expected_flag: str = Field(..., min_length=1)
    frontend_hint: Optional[str] = None
    backend_validation_script: str = Field(..., min_length=1)
    frontend_config: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChallengeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    intro: Optional[str] = None
    play_instructions: Optional[str] = None
    points: Optional[int] = Field(None, ge=1, le=100)
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    is_active: Optional[bool] = None
    frontend_hint: Optional[str] = None
    backend_validation_script: Optional[str] = None
    frontend_config: Optional[Dict[str, Any]] = None

class ChallengeInDB(ChallengeBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    solution_type: str
    expected_flag: str
    frontend_hint: Optional[str] = None
    backend_validation_script: str
    frontend_config: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    solve_count: int = Field(default=0)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ChallengeResponse(ChallengeBase):
    id: str
    frontend_hint: Optional[str]
    frontend_config: Dict[str, Any]
    created_at: datetime
    solve_count: int
    is_solved: Optional[bool] = None  # Will be set based on user context

class ChallengeSubmission(BaseModel):
    challenge_id: str
    submission_data: Dict[str, Any]  # Can contain flag, cookies, headers, files, etc.

class SubmissionResult(BaseModel):
    success: bool
    message: str
    flag: Optional[str] = None
    points_earned: Optional[int] = None

class SubmissionInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    challenge_id: str
    is_correct: bool
    submitted_data: Dict[str, Any]
    result_message: str
    points_earned: int = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
