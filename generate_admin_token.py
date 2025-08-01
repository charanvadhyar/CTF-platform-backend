from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import jwt
import sys
from pymongo import MongoClient

# Load environment variables from .env file
load_dotenv()

# Get MongoDB connection string and JWT settings from environment variables
mongodb_url = os.getenv("MONGODB_URL")
database_name = os.getenv("DATABASE_NAME", "ctf_platform")
secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM", "HS256")
expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

if not all([mongodb_url, secret_key]):
    print("Error: Required environment variables not found!")
    sys.exit(1)

def get_admin_user_email():
    """Get the email of a user with admin role"""
    client = MongoClient(mongodb_url)
    db = client[database_name]
    
    # First, try to find the specific admin user we updated
    admin_user = db.users.find_one({"email": "admin@ctf.com"})
    
    if admin_user and admin_user.get("role") == "admin":
        return admin_user["email"]
    
    # If not found, try to find any user with admin role
    admin_user = db.users.find_one({"role": "admin"})
    
    if admin_user:
        return admin_user["email"]
    
    print("Error: No admin users found in the database!")
    sys.exit(1)

def create_access_token(data: dict, expires_delta: timedelta):
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt

def main():
    # Get admin user email
    admin_email = get_admin_user_email()
    print(f"Found admin user: {admin_email}")
    
    # Generate token
    access_token_expires = timedelta(minutes=expire_minutes)
    token = create_access_token(
        data={"sub": admin_email}, 
        expires_delta=access_token_expires
    )
    
    print("\nAdmin JWT Token:")
    print(token)
    print("\nUse this token in localStorage for admin access:")
    print(f"localStorage.setItem('token', '{token}')")

if __name__ == "__main__":
    main()
