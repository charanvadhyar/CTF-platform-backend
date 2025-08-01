from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import UserCreate, UserLogin, UserResponse, Token, UserInDB
from app.auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    get_current_user,
    get_user_by_email
)
from app.database import get_database
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    """Register a new user"""
    db = get_database()
    
    # Check if user already exists - if so, log them in instead of error
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        # User exists, return their info (auto-login behavior)
        from datetime import datetime
        return UserResponse(
            id=str(existing_user["_id"]),
            email=existing_user["email"],
            username=existing_user["username"],
            role=existing_user.get("role", "user"),
            score=existing_user.get("score", 0),
            solved_challenges=existing_user.get("solved_challenges", []),
            created_at=existing_user.get("created_at", datetime.utcnow()),
            last_login=existing_user.get("last_login")
        )
    
    existing_username = await db.users.find_one({"username": user.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Handle passwordless registration - generate a default password if none provided
    password_to_hash = user.password if user.password else f"ctf_{user.username}_{user.email.split('@')[0]}"
    hashed_password = get_password_hash(password_to_hash)
    
    # Create new user
    user_data = {
        "email": user.email,
        "username": user.username,
        "hashed_password": hashed_password,
        "role": user.role,
        "score": 0,
        "solved_challenges": [],
        "is_active": True
    }
    
    result = await db.users.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    
    created_user = UserInDB(**user_data)
    
    logger.info(f"New user registered: {user.email}")
    
    return UserResponse(
        id=str(created_user.id),
        email=created_user.email,
        username=created_user.username,
        role=created_user.role,
        score=created_user.score,
        solved_challenges=created_user.solved_challenges,
        created_at=created_user.created_at,
        last_login=created_user.last_login
    )

@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    """Authenticate user and return JWT token"""
    user = await authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    db = get_database()
    await db.users.update_one(
        {"_id": user.id},
        {"$set": {"last_login": user.created_at.__class__.utcnow()}}
    )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in: {user.email}")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token endpoint"""
    user = await authenticate_user(form_data.username, form_data.password)  # username is email
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        role=current_user.role,
        score=current_user.score,
        solved_challenges=current_user.solved_challenges,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.get("/verify-token")
async def verify_token(current_user: UserInDB = Depends(get_current_user)):
    """Verify if token is valid"""
    return {"valid": True, "user_id": str(current_user.id), "role": current_user.role}

from pydantic import BaseModel

class AdminTokenRequest(BaseModel):
    admin_token: str

@router.post("/admin-login", response_model=Token)
async def admin_login_with_token(request: AdminTokenRequest):
    """Admin login using secure admin token"""
    from app.auth import get_admin_user_by_token
    
    # Verify admin token and get admin user
    admin_user = await get_admin_user_by_token(request.admin_token)
    
    # Create JWT token for admin user
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": admin_user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
