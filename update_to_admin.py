from pymongo import MongoClient
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get MongoDB connection string from environment variables
mongodb_url = os.getenv("MONGODB_URL")
database_name = os.getenv("DATABASE_NAME", "ctf_platform")

if not mongodb_url:
    print("Error: MONGODB_URL not found in environment variables!")
    sys.exit(1)

print(f"Connecting to MongoDB Atlas with database: {database_name}")

# Connect to the MongoDB server
client = MongoClient(mongodb_url)
print("Connected to MongoDB Atlas successfully!")

# Select the database
db = client[database_name]

# Get user email from command line or use the last registered user
if len(sys.argv) > 1:
    user_email = sys.argv[1]
    # Find the user by email
    user = db.users.find_one({"email": user_email})
    if not user:
        print(f"User with email {user_email} not found!")
        sys.exit(1)
else:
    # Get the most recently registered user
    user = db.users.find_one({}, sort=[("created_at", -1)])
    if not user:
        print("No users found in the database!")
        sys.exit(1)
    user_email = user["email"]

# Update the user's role to admin
result = db.users.update_one(
    {"email": user_email},
    {"$set": {"role": "admin"}}
)

if result.modified_count > 0:
    print(f"Successfully updated user {user_email} to admin role!")
else:
    print(f"User {user_email} might already be an admin or update failed.")

# Verify the update
user = db.users.find_one({"email": user_email})
print(f"User {user_email} now has role: {user.get('role', 'unknown')}")
