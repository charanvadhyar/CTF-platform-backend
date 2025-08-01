from typing import List, Optional
from fastapi import APIRouter, Depends
from app.models.user import UserInDB, UserProgress
from app.auth import get_current_user
from app.database import get_database
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@router.get("/")
async def get_leaderboard(
    limit: int = 50,
    current_user: Optional[UserInDB] = Depends(get_current_user)
):
    """Get leaderboard with top users by score"""
    db = get_database()
    
    # Get top users
    users = await db.users.find(
        {"is_active": True},
        {"username": 1, "score": 1, "solved_challenges": 1, "created_at": 1}
    ).sort("score", -1).limit(limit).to_list(length=limit)
    
    # Get total challenges count
    total_challenges = await db.challenges.count_documents({"is_active": True})
    
    leaderboard = []
    for i, user in enumerate(users, 1):
        solved_count = len(user.get("solved_challenges", []))
        progress_percentage = (solved_count / total_challenges) * 100 if total_challenges > 0 else 0
        
        user_entry = {
            "rank": i,
            "username": user["username"],
            "score": user["score"],
            "solved_challenges": solved_count,
            "progress_percentage": round(progress_percentage, 1),
            "is_current_user": str(user["_id"]) == str(current_user.id) if current_user else False
        }
        leaderboard.append(user_entry)
    
    # Get current user's rank if not in top list
    current_user_rank = None
    if current_user:
        higher_score_users = await db.users.count_documents({
            "score": {"$gt": current_user.score},
            "is_active": True
        })
        current_user_rank = higher_score_users + 1
    
    return {
        "leaderboard": leaderboard,
        "total_users": await db.users.count_documents({"is_active": True}),
        "current_user_rank": current_user_rank
    }

@router.get("/progress")
async def get_user_progress(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get current user's progress statistics"""
    db = get_database()
    
    # Get total challenges
    total_challenges = await db.challenges.count_documents({"is_active": True})
    solved_challenges = len(current_user.solved_challenges)
    progress_percentage = (solved_challenges / total_challenges) * 100 if total_challenges > 0 else 0
    
    # Get user's rank
    higher_score_users = await db.users.count_documents({
        "score": {"$gt": current_user.score},
        "is_active": True
    })
    user_rank = higher_score_users + 1
    
    # Get recent submissions
    recent_submissions = await db.submissions.find({
        "user_id": str(current_user.id),
        "is_correct": True
    }).sort("timestamp", -1).limit(5).to_list(length=5)
    
    # Get challenge details for recent submissions
    recent_solves = []
    for submission in recent_submissions:
        challenge = await db.challenges.find_one({"_id": submission["challenge_id"]})
        if challenge:
            recent_solves.append({
                "challenge_title": challenge["title"],
                "points_earned": submission["points_earned"],
                "solved_at": submission["timestamp"]
            })
    
    return UserProgress(
        user_id=str(current_user.id),
        total_challenges=total_challenges,
        solved_challenges=solved_challenges,
        total_score=current_user.score,
        progress_percentage=round(progress_percentage, 1)
    ), {
        "rank": user_rank,
        "recent_solves": recent_solves
    }
