#!/usr/bin/env python3
"""
Startup script for CTF Platform Backend
Handles database initialization and application startup
"""

import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if available)
load_dotenv()

# Print important environment variables for debugging
mongodb_url = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
logging.info(f"Using MongoDB URL: {mongodb_url.replace('://','://**:**@').split('@')[1] if '@' in mongodb_url else 'localhost:27017'}")

# Set any missing environment variables from Railway
os.environ["MONGODB_URL"] = mongodb_url

from app.database import connect_to_mongo, get_database
from app.auth import create_admin_user_data
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database with default data"""
    try:
        await connect_to_mongo()
        db = get_database()
        
        # Create admin user
        admin_exists = await db.users.find_one({"email": settings.admin_email})
        if not admin_exists:
            admin_data = create_admin_user_data(
                email=settings.admin_email,
                password=settings.admin_password,
                username="admin"
            )
            await db.users.insert_one(admin_data)
            logger.info(f"Created admin user: {settings.admin_email}")
        
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Initialize the database
    asyncio.run(init_database())
    
    # Start the FastAPI app with uvicorn
    import os
    import uvicorn
    
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
