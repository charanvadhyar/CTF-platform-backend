from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.models.challenge import (
    ChallengeResponse, 
    ChallengeSubmission, 
    SubmissionResult,
    SubmissionInDB
)
from app.models.user import UserInDB
from app.models.analytics import VisitInDB
from app.auth import get_current_user
from app.database import get_database
from app.challenge_validators import CHALLENGE_VALIDATORS
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/challenges", tags=["challenges"])

@router.get("/", response_model=List[ChallengeResponse])
async def get_challenges(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    current_user: Optional[UserInDB] = Depends(get_current_user)
):
    """Get all active challenges with optional filtering"""
    db = get_database()
    
    # Build query
    query = {"is_active": True}
    if category:
        query["category"] = category
    if difficulty:
        query["difficulty"] = difficulty
    
    challenges = await db.challenges.find(query).sort("id", 1).to_list(length=None)
    
    # Convert to response format and add solved status
    challenge_responses = []
    for challenge in challenges:
        challenge_response = ChallengeResponse(
            id=str(challenge["_id"]),
            title=challenge["title"],
            slug=challenge["slug"],
            category=challenge["category"],
            description=challenge["description"],
            points=challenge["points"],
            difficulty=challenge["difficulty"],
            is_active=challenge["is_active"],
            frontend_hint=challenge.get("frontend_hint"),
            frontend_config=challenge.get("frontend_config", {}),
            created_at=challenge.get("created_at", datetime.utcnow()),
            solve_count=challenge.get("solve_count", 0)
        )
        
        # Add solved status if user is authenticated
        if current_user:
            challenge_response.is_solved = str(challenge["_id"]) in current_user.solved_challenges
        
        challenge_responses.append(challenge_response)
    
    return challenge_responses

@router.get("/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(
    challenge_id: str,
    request: Request,
    current_user: Optional[UserInDB] = Depends(get_current_user)
):
    """Get specific challenge by ID"""
    db = get_database()
    
    # Get challenge
    challenge = await db.challenges.find_one({"_id": challenge_id, "is_active": True})
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )
    
    # Track visit
    visit_data = {
        "user_id": str(current_user.id) if current_user else None,
        "challenge_id": challenge_id,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent", ""),
        "timestamp": datetime.utcnow()
    }
    await db.visits.insert_one(visit_data)
    
    # Create response
    challenge_response = ChallengeResponse(
        id=str(challenge["_id"]),
        title=challenge["title"],
        slug=challenge["slug"],
        category=challenge["category"],
        description=challenge["description"],
        intro=challenge.get("intro"),  # Include intro field
        play_instructions=challenge.get("play_instructions"),  # Include play_instructions field
        points=challenge["points"],
        difficulty=challenge["difficulty"],
        is_active=challenge["is_active"],
        frontend_hint=challenge.get("frontend_hint"),
        frontend_config=challenge.get("frontend_config", {}),
        created_at=challenge.get("created_at", datetime.utcnow()),
        solve_count=challenge.get("solve_count", 0)
    )
    
    # Add solved status if user is authenticated
    if current_user:
        challenge_response.is_solved = challenge_id in current_user.solved_challenges
    
    return challenge_response

@router.post("/{challenge_id}/submit", response_model=SubmissionResult)
async def submit_challenge(
    challenge_id: str,
    submission: ChallengeSubmission,
    current_user: UserInDB = Depends(get_current_user)
):
    """Submit solution for a challenge"""
    db = get_database()
    
    # Get challenge
    challenge = await db.challenges.find_one({"_id": challenge_id, "is_active": True})
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )
    
    # Check if already solved
    if challenge_id in current_user.solved_challenges:
        return SubmissionResult(
            success=False,
            message="Challenge already solved!",
            points_earned=0
        )
    
    # Get challenge number from title or use a mapping
    challenge_number = int(challenge.get("challenge_number", 1))
    
    # Validate submission using appropriate validator
    validator = CHALLENGE_VALIDATORS.get(challenge_number)
    if not validator:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Challenge validator not found"
        )
    
    try:
        result = validator(submission.submission_data)
    except Exception as e:
        logger.error(f"Challenge validation error: {e}")
        result = SubmissionResult(
            success=False,
            message="Validation error occurred",
            points_earned=0
        )
    
    # Store submission
    submission_data = {
        "user_id": str(current_user.id),
        "challenge_id": challenge_id,
        "is_correct": result.success,
        "submitted_data": submission.submission_data,
        "result_message": result.message,
        "points_earned": result.points_earned or 0,
        "timestamp": datetime.utcnow()
    }
    await db.submissions.insert_one(submission_data)
    
    # If correct, update user progress and challenge solve count
    if result.success:
        # Update user
        await db.users.update_one(
            {"_id": current_user.id},
            {
                "$addToSet": {"solved_challenges": challenge_id},
                "$inc": {"score": result.points_earned or 0}
            }
        )
        
        # Update challenge solve count
        await db.challenges.update_one(
            {"_id": challenge_id},
            {"$inc": {"solve_count": 1}}
        )
        
        logger.info(f"User {current_user.email} solved challenge {challenge_id}")
    
    return result

@router.get("/categories/list")
async def get_challenge_categories():
    """Get list of all challenge categories"""
    db = get_database()
    categories = await db.challenges.distinct("category", {"is_active": True})
    return {"categories": categories}

@router.get("/difficulties/list")
async def get_challenge_difficulties():
    """Get list of all challenge difficulties"""
    return {"difficulties": ["easy", "medium", "hard"]}

@router.get("/{challenge_id}/submissions")
async def get_challenge_submissions(
    challenge_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get user's submissions for a specific challenge"""
    db = get_database()
    
    submissions = await db.submissions.find({
        "user_id": str(current_user.id),
        "challenge_id": challenge_id
    }).sort("timestamp", -1).to_list(length=10)  # Last 10 submissions
    
    return {"submissions": submissions}
