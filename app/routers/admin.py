from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.challenge import ChallengeCreate, ChallengeUpdate, ChallengeResponse, ChallengeInDB
from app.models.user import UserInDB, UserResponse
from app.models.analytics import ChallengeVisitStats, UserAnalytics, PlatformAnalytics
from app.auth import get_current_admin_user
from app.database import get_database
from datetime import datetime, timedelta
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

# Challenge Management
@router.post("/challenges", response_model=ChallengeResponse)
async def create_challenge(
    challenge: ChallengeCreate,
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """Create a new challenge (Admin only)"""
    db = get_database()
    
    # Check if slug already exists
    existing_challenge = await db.challenges.find_one({"slug": challenge.slug})
    if existing_challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Challenge slug already exists"
        )
    
    # Create challenge data
    challenge_data = {
        **challenge.dict(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "solve_count": 0
    }
    
    result = await db.challenges.insert_one(challenge_data)
    challenge_data["_id"] = result.inserted_id
    
    created_challenge = ChallengeInDB(**challenge_data)
    
    logger.info(f"Admin {current_admin.email} created challenge: {challenge.title}")
    
    return ChallengeResponse(
        id=str(created_challenge.id),
        title=created_challenge.title,
        slug=created_challenge.slug,
        category=created_challenge.category,
        description=created_challenge.description,
        points=created_challenge.points,
        difficulty=created_challenge.difficulty,
        is_active=created_challenge.is_active,
        frontend_hint=created_challenge.frontend_hint,
        frontend_config=created_challenge.frontend_config,
        created_at=created_challenge.created_at,
        solve_count=created_challenge.solve_count
    )

@router.get("/challenges", response_model=List[ChallengeResponse])
async def get_all_challenges_admin(
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """Get all challenges including inactive ones (Admin only)"""
    db = get_database()
    
    challenges = await db.challenges.find({}).sort("created_at", -1).to_list(length=None)
    
    challenge_responses = []
    for challenge in challenges:
        challenge_responses.append(ChallengeResponse(
            id=str(challenge["_id"]),
            title=challenge["title"],
            slug=challenge["slug"],
            category=challenge["category"],
            description=challenge["description"],
            intro=challenge.get("intro"),
            play_instructions=challenge.get("play_instructions"),
            points=challenge["points"],
            difficulty=challenge["difficulty"],
            is_active=challenge["is_active"],
            frontend_hint=challenge.get("frontend_hint"),
            frontend_config=challenge.get("frontend_config", {}),
            created_at=challenge.get("created_at", datetime.utcnow()),
            solve_count=challenge.get("solve_count", 0)
        ))
    
    return challenge_responses

@router.patch("/challenges/{challenge_id}", response_model=ChallengeResponse)
async def update_challenge(
    challenge_id: str,
    challenge_update: ChallengeUpdate,
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """Update a challenge (Admin only)"""
    db = get_database()
    
    try:
        # First try to find by string ID (for numeric IDs)
        existing_challenge = await db.challenges.find_one({"_id": challenge_id})
        
        # If not found, try to convert to ObjectId and search again
        if not existing_challenge and len(challenge_id) >= 12:
            try:
                challenge_object_id = ObjectId(challenge_id)
                existing_challenge = await db.challenges.find_one({"_id": challenge_object_id})
            except:
                # Invalid ObjectId format
                pass
                
        if not existing_challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Challenge not found"
            )
            
        # Use the correct ID format for MongoDB operations
        mongo_id = challenge_id
        
        # Prepare update data
        update_data = {k: v for k, v in challenge_update.dict().items() if v is not None}
        
        # Debug logging
        logger.info(f"Challenge update data: {update_data}")
        update_data["updated_at"] = datetime.utcnow()
        
        # Update challenge
        await db.challenges.update_one(
            {"_id": mongo_id},
            {"$set": update_data}
        )
        
        # Get updated challenge
        updated_challenge = await db.challenges.find_one({"_id": mongo_id})
        
        logger.info(f"Admin {current_admin.email} updated challenge: {challenge_id}")
    except Exception as e:
        logger.error(f"Error updating challenge {challenge_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating challenge: {str(e)}"
        )
    
    return ChallengeResponse(
        id=str(updated_challenge["_id"]),
        title=updated_challenge["title"],
        slug=updated_challenge["slug"],
        category=updated_challenge["category"],
        description=updated_challenge["description"],
        points=updated_challenge["points"],
        difficulty=updated_challenge["difficulty"],
        is_active=updated_challenge["is_active"],
        frontend_hint=updated_challenge.get("frontend_hint"),
        frontend_config=updated_challenge.get("frontend_config", {}),
        created_at=updated_challenge.get("created_at", datetime.utcnow()),
        solve_count=updated_challenge.get("solve_count", 0),
        play_instructions=updated_challenge.get("play_instructions"),
        intro=updated_challenge.get("intro")
    )

@router.delete("/challenges/{challenge_id}")
async def delete_challenge(
    challenge_id: str,
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """Delete a challenge (Admin only)"""
    db = get_database()
    
    try:
        # First try to find by string ID (for numeric IDs)
        existing_challenge = await db.challenges.find_one({"_id": challenge_id})
        
        # If not found, try to convert to ObjectId and search again
        if not existing_challenge and len(challenge_id) >= 12:
            try:
                challenge_object_id = ObjectId(challenge_id)
                existing_challenge = await db.challenges.find_one({"_id": challenge_object_id})
            except:
                # Invalid ObjectId format
                pass
                
        if not existing_challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Challenge not found"
            )
            
        # Use the correct ID format for MongoDB operations
        mongo_id = challenge_id
        
        # Delete challenge
        await db.challenges.delete_one({"_id": mongo_id})
        
        # Clean up related data
        await db.submissions.delete_many({"challenge_id": challenge_id})  # Keep string ID for these collections
        await db.visits.delete_many({"challenge_id": challenge_id})  # Keep string ID for these collections
        
        logger.info(f"Admin {current_admin.email} deleted challenge: {challenge_id}")
    except Exception as e:
        logger.error(f"Error deleting challenge {challenge_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting challenge: {str(e)}"
        )
    
    return {"message": "Challenge deleted successfully"}

# User Management
@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """Get all users (Admin only)"""
    db = get_database()
    
    users = await db.users.find({}).sort("created_at", -1).to_list(length=None)
    
    user_responses = []
    for user in users:
        user_responses.append(UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            username=user["username"],
            role=user["role"],
            score=user["score"],
            solved_challenges=user["solved_challenges"],
            created_at=user.get("created_at", datetime.utcnow()),
            last_login=user.get("last_login")
        ))
    
    return user_responses

@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """Update user role (Admin only)"""
    if role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'user' or 'admin'"
        )
    
    db = get_database()
    
    # Check if user exists
    existing_user = await db.users.find_one({"_id": user_id})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user role
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"role": role}}
    )
    
    logger.info(f"Admin {current_admin.email} updated user {user_id} role to {role}")
    
    return {"message": f"User role updated to {role}"}

# Analytics
@router.get("/analytics/challenge-visits", response_model=List[ChallengeVisitStats])
async def get_challenge_visit_analytics(
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """Get challenge visit analytics (Admin only)"""
    db = get_database()
    
    # Aggregate visit statistics
    pipeline = [
        {
            "$group": {
                "_id": "$challenge_id",
                "total_visits": {"$sum": 1},
                "unique_visitors": {"$addToSet": "$user_id"}
            }
        },
        {
            "$project": {
                "challenge_id": "$_id",
                "total_visits": 1,
                "unique_visitors": {"$size": "$unique_visitors"}
            }
        }
    ]
    
    visit_stats = await db.visits.aggregate(pipeline).to_list(length=None)
    
    # Get challenge details and solve rates
    result = []
    for stat in visit_stats:
        challenge = await db.challenges.find_one({"_id": stat["challenge_id"]})
        if challenge:
            solve_count = challenge.get("solve_count", 0)
            solve_rate = (solve_count / stat["total_visits"]) * 100 if stat["total_visits"] > 0 else 0
            
            result.append(ChallengeVisitStats(
                challenge_id=stat["challenge_id"],
                challenge_title=challenge["title"],
                total_visits=stat["total_visits"],
                unique_visitors=stat["unique_visitors"],
                solve_rate=solve_rate
            ))
    
    return result

@router.get("/analytics/users", response_model=UserAnalytics)
async def get_user_analytics(
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """Get user analytics (Admin only)"""
    db = get_database()
    
    # Get user statistics
    total_users = await db.users.count_documents({})
    
    # Active users today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    active_today = await db.users.count_documents({
        "last_login": {"$gte": today}
    })
    
    # Active users this week
    week_ago = today - timedelta(days=7)
    active_week = await db.users.count_documents({
        "last_login": {"$gte": week_ago}
    })
    
    # New registrations today
    new_today = await db.users.count_documents({
        "created_at": {"$gte": today}
    })
    
    # Top scorers
    top_scorers = await db.users.find({}).sort("score", -1).limit(10).to_list(length=10)
    top_scorers_list = [
        {"username": user["username"], "score": user["score"]}
        for user in top_scorers
    ]
    
    return UserAnalytics(
        total_users=total_users,
        active_users_today=active_today,
        active_users_week=active_week,
        new_registrations_today=new_today,
        top_scorers=top_scorers_list
    )

@router.get("/analytics/platform", response_model=PlatformAnalytics)
async def get_platform_analytics(
    current_admin: UserInDB = Depends(get_current_admin_user)
):
    """Get platform analytics (Admin only)"""
    db = get_database()
    
    # Basic counts
    total_challenges = await db.challenges.count_documents({"is_active": True})
    total_submissions = await db.submissions.count_documents({})
    total_visits = await db.visits.count_documents({})
    
    # Success rate
    correct_submissions = await db.submissions.count_documents({"is_correct": True})
    success_rate = (correct_submissions / total_submissions) * 100 if total_submissions > 0 else 0
    
    # Most popular challenges (by visits)
    popular_pipeline = [
        {"$group": {"_id": "$challenge_id", "visit_count": {"$sum": 1}}},
        {"$sort": {"visit_count": -1}},
        {"$limit": 5}
    ]
    popular_challenges = await db.visits.aggregate(popular_pipeline).to_list(length=5)
    
    # Most difficult challenges (lowest solve rate)
    difficult_pipeline = [
        {
            "$lookup": {
                "from": "challenges",
                "localField": "challenge_id",
                "foreignField": "_id",
                "as": "challenge"
            }
        },
        {"$unwind": "$challenge"},
        {
            "$group": {
                "_id": "$challenge_id",
                "title": {"$first": "$challenge.title"},
                "total_visits": {"$sum": 1},
                "solve_count": {"$first": "$challenge.solve_count"}
            }
        },
        {
            "$project": {
                "title": 1,
                "solve_rate": {
                    "$multiply": [
                        {"$divide": ["$solve_count", "$total_visits"]},
                        100
                    ]
                }
            }
        },
        {"$sort": {"solve_rate": 1}},
        {"$limit": 5}
    ]
    difficult_challenges = await db.visits.aggregate(difficult_pipeline).to_list(length=5)
    
    return PlatformAnalytics(
        total_challenges=total_challenges,
        total_submissions=total_submissions,
        total_visits=total_visits,
        success_rate=success_rate,
        most_popular_challenges=popular_challenges,
        most_difficult_challenges=difficult_challenges
    )
