"""
Backend endpoints for Cookie Manipulation Challenge (Challenge #4)
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Cookie, Response
from pydantic import BaseModel
from app.database import get_database

# Create router for this challenge
router = APIRouter(
    prefix="/challenge-4",
    tags=["challenge-4"],
)

# Login request model
class LoginRequest(BaseModel):
    username: str
    password: str

# Login response model
class LoginResponse(BaseModel):
    success: bool
    message: str
    username: Optional[str] = None
    role: Optional[str] = None

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, response: Response):
    """
    Login endpoint for Challenge #4 - Cookie Manipulation
    Sets cookies that can be manipulated for the challenge
    """
    # Log the login attempt
    db = get_database()
    await db.challenge_attempts.insert_one({
        "challenge_id": 4,
        "attempt_type": "login",
        "username": login_data.username,
        "password": login_data.password  # Note: In a real app, never log passwords!
    })
    
    # Validate credentials
    if login_data.username == "user" and login_data.password == "password":
        # Set cookies - intentionally insecure
        response.set_cookie(key="logged_in", value="true", max_age=3600)
        response.set_cookie(key="username", value=login_data.username, max_age=3600)
        response.set_cookie(key="user_role", value="user", max_age=3600)
        
        return LoginResponse(
            success=True,
            message="Login successful",
            username=login_data.username,
            role="user"
        )
    
    # Invalid credentials
    return LoginResponse(
        success=False,
        message="Invalid credentials",
        username=None,
        role=None
    )

@router.get("/profile")
async def get_profile(
    logged_in: Optional[str] = Cookie(None),
    username: Optional[str] = Cookie(None),
    user_role: Optional[str] = Cookie(None)
):
    """
    Get user profile based on cookies
    This endpoint is intentionally vulnerable to cookie manipulation
    """
    # Check if logged in
    if not logged_in or logged_in != "true":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Get user profile data
    user_data = {
        "username": username or "unknown",
        "role": user_role or "guest"
    }
    
    # If admin, add flag
    if user_role == "admin":
        user_data["flag"] = "CTF{cookie_manipulation_admin}"
        user_data["is_admin"] = True
    else:
        user_data["is_admin"] = False
    
    return user_data

@router.post("/logout")
async def logout(response: Response):
    """Log out by clearing cookies"""
    response.delete_cookie(key="logged_in")
    response.delete_cookie(key="username")
    response.delete_cookie(key="user_role")
    
    return {
        "success": True,
        "message": "Logged out successfully"
    }
