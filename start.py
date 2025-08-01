#!/usr/bin/env python3
"""
Startup script for CTF Platform Backend
Handles database initialization and application startup
"""

import asyncio
import logging
import sys
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
