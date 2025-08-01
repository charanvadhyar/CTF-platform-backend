#!/usr/bin/env python3
"""
Script to clean up duplicate ads in the database and enforce uniqueness.
This script:
1. Finds all distinct ad positions
2. For each position, keeps only the most recent ad
3. Deletes all older duplicate ads
4. Creates a unique index on 'position' field to enforce uniqueness going forward
"""

import asyncio
import os
import sys
import dotenv
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
dotenv.load_dotenv(Path(__file__).parent.parent / ".env")

# Database configuration from environment variables
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ctf_platform")

logger.info(f"Using MongoDB URL: {MONGODB_URL}")
logger.info(f"Using database: {DB_NAME}")

# Validate we have a MongoDB URL
if not MONGODB_URL:
    logger.error("MONGODB_URL environment variable is not set")
    sys.exit(1)

async def remove_duplicate_ads():
    """Remove duplicate ads, keeping only the most recent one for each position."""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DB_NAME]
        
        # Get the ads collection
        ads_collection = db.ads
        
        logger.info("Connected to MongoDB database")
        
        # Find all unique positions in the ads collection
        positions = await ads_collection.distinct("position")
        logger.info(f"Found {len(positions)} unique ad positions: {positions}")
        
        # For each position, keep the most recent ad and delete others
        total_removed = 0
        
        for position in positions:
            # Find all ads for this position, sorted by creation date (newest first)
            ads_cursor = ads_collection.find({"position": position}).sort("created_at", DESCENDING)
            ads_list = await ads_cursor.to_list(length=None)
            
            if len(ads_list) <= 1:
                logger.info(f"Position '{position}' has no duplicates")
                continue
            
            # Keep the first (most recent) ad
            most_recent_ad = ads_list[0]
            most_recent_id = most_recent_ad.get("_id")
            
            # Get IDs of all other ads to delete
            duplicate_ids = [ad.get("_id") for ad in ads_list[1:]]
            
            # Delete all duplicates
            result = await ads_collection.delete_many({"_id": {"$in": duplicate_ids}})
            
            logger.info(f"Position '{position}': Kept ad {most_recent_id}, removed {result.deleted_count} duplicates")
            total_removed += result.deleted_count
        
        logger.info(f"Total duplicates removed: {total_removed}")
        
        # Create unique index on position field to prevent future duplicates
        await ads_collection.create_index("position", unique=True)
        logger.info("Created unique index on 'position' field to prevent future duplicates")
        
        return {
            "success": True,
            "message": f"Removed {total_removed} duplicate ads and created unique index on position field",
            "positions_processed": len(positions)
        }
    
    except Exception as e:
        logger.error(f"Error removing duplicate ads: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        # Close MongoDB connection
        client.close()
        logger.info("MongoDB connection closed")

async def main():
    """Main function to run the script."""
    result = await remove_duplicate_ads()
    if result["success"]:
        logger.info(f"SUCCESS: {result['message']}")
    else:
        logger.error(f"FAILED: {result['error']}")

if __name__ == "__main__":
    # Run the async function
    asyncio.run(main())
