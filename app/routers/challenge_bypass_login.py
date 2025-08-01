"""
Backend endpoints for Bypass Login Challenge (Challenge #1)
"""
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.auth import get_current_user
from app.database import get_database
from app.models.user import UserInDB

# Create router for this challenge
router = APIRouter(
    prefix="/challenge-1",
    tags=["challenge-1"],
)

# Login request model
class LoginRequest(BaseModel):
    username: str
    password: str

# Login response model
class LoginResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None

@router.post("/login", response_model=LoginResponse)
async def challenge_login(login_data: LoginRequest):
    """
    Login endpoint for Challenge #1 - Bypass Login
    This is intentionally vulnerable to demonstrate authentication bypass
    """
    # Log the attempt (optional)
    db = get_database()
    await db.challenge_attempts.insert_one({
        "challenge_id": 1,
        "attempt_type": "login",
        "username": login_data.username,
        "password": login_data.password  # Note: In a real app, never log passwords!
    })
    
    # Simulate vulnerable authentication logic
    # The vulnerability is intentional for educational purposes
    if login_data.username == "admin" and login_data.password == "admin123":
        return LoginResponse(
            success=True,
            message="Login successful",
            access_token="fake-secure-token-for-demo"
        )
    
    # Return failure response
    return LoginResponse(
        success=False,
        message="Invalid credentials",
        access_token=None
    )

@router.get("/admin-check")
async def check_admin_token(token: Optional[str] = None):
    """
    Check if the provided token is valid for admin access
    This is part of Challenge #1 - Bypass Login
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )
    
    # Very insecure token validation (intentional)
    if token == "fake-secure-token-for-demo":
        return {
            "success": True,
            "message": "You have admin access",
            "flag": "CTF{insecure_auth_logic_bypass}"
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )
