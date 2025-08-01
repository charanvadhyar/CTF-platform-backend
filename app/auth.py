from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import get_database
from app.models.user import UserInDB, TokenData
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer(auto_error=True)

# Optional JWT token scheme - allows unauthenticated requests
optional_security = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user by email from database"""
    db = get_database()
    user_data = await db.users.find_one({"email": email})
    if user_data:
        return UserInDB(**user_data)
    return None

async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with email and password"""
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """Get current user from JWT token"""
    from app.config import settings
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # Check if this is the virtual admin user
    if token_data.email == "admin@ctfplatform.com":
        # Return the virtual admin user for admin token authentication
        from bson import ObjectId
        return UserInDB(
            id=ObjectId(),
            email="admin@ctfplatform.com",
            username="admin",
            hashed_password="",
            role="admin",
            score=0,
            solved_challenges=[],
            created_at=datetime.utcnow(),
            is_active=True
        )
    
    # Regular user authentication
    user = await get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

async def get_current_admin_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Get current user and verify admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def create_admin_user_data(email: str, password: str, username: str = "admin") -> dict:
    """Create admin user data for database insertion"""
    return {
        "email": email,
        "username": username,
        "hashed_password": get_password_hash(password),
        "role": "admin",
        "score": 0,
        "solved_challenges": [],
        "created_at": datetime.utcnow(),
        "is_active": True
    }

async def verify_admin_token(admin_token: str) -> bool:
    """Verify admin token against configured admin token"""
    from app.config import settings
    return admin_token == settings.admin_token

async def get_admin_user_by_token(admin_token: str) -> UserInDB:
    """Get admin user using secure admin token"""
    if not await verify_admin_token(admin_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return a virtual admin user for token-based access
    from bson import ObjectId
    return UserInDB(
        id=ObjectId(),  # Generate a valid ObjectId
        email="admin@ctfplatform.com",  # Use .com instead of .local
        username="admin",
        hashed_password="",  # Not needed for token auth
        role="admin",
        score=0,
        solved_challenges=[],
        created_at=datetime.utcnow(),
        is_active=True
    )
