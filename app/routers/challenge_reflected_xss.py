"""
Backend endpoints for Reflected XSS Challenge (Challenge #3)
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.database import get_database

# Create router for this challenge
router = APIRouter(
    prefix="/challenge-3",
    tags=["challenge-3"],
)

# Comment model
class Comment(BaseModel):
    name: str
    content: str

# Comment response
class CommentResponse(BaseModel):
    id: str
    name: str
    content: str
    timestamp: str

@router.post("/comments", response_model=CommentResponse)
async def post_comment(comment: Comment):
    """
    Create a new comment - intentionally vulnerable to XSS
    This endpoint doesn't sanitize inputs before reflecting them back
    """
    # Log the attempt
    db = get_database()
    result = await db.challenge_attempts.insert_one({
        "challenge_id": 3,
        "attempt_type": "comment",
        "name": comment.name,
        "content": comment.content
    })
    
    # Create comment document
    comment_id = str(result.inserted_id)
    
    import datetime
    timestamp = datetime.datetime.now().isoformat()
    
    # Note: Intentionally not sanitizing the comment before returning it
    # This simulates the reflected XSS vulnerability
    return CommentResponse(
        id=comment_id,
        name=comment.name, 
        content=comment.content,  # Vulnerable: content is reflected without sanitization
        timestamp=timestamp
    )

@router.get("/comments", response_model=List[CommentResponse])
async def get_comments():
    """Get all comments for this challenge"""
    db = get_database()
    
    # Find all comments for this challenge
    cursor = db.challenge_attempts.find({"challenge_id": 3, "attempt_type": "comment"})
    comments = await cursor.to_list(length=100)
    
    # Format comments for response
    comment_responses = []
    for comment in comments:
        comment_responses.append(
            CommentResponse(
                id=str(comment["_id"]),
                name=comment["name"],
                content=comment["content"],  # Vulnerable: content is reflected without sanitization
                timestamp=comment.get("timestamp", "2025-07-31T00:00:00")
            )
        )
    
    return comment_responses

@router.get("/admin-cookie")
async def get_admin_cookie():
    """
    Simulated admin cookie endpoint - this would never exist in a real app!
    It's only here to help confirm XSS attack success on the frontend
    """
    return {
        "cookie": "admin=true; flag=CTF{reflected_xss_cookie_theft}; sessionId=938a77b4c98d0965"
    }
