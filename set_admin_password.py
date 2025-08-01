import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

# Get MongoDB connection string from environment variables
mongodb_url = os.getenv("MONGODB_URL")
database_name = os.getenv("DATABASE_NAME", "ctf_platform")

if not mongodb_url:
    print("Error: MONGODB_URL not found in environment variables!")
    sys.exit(1)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Connect to MongoDB
client = MongoClient(mongodb_url)
db = client[database_name]

# Admin email and new password
admin_email = "admin@ctf.com"
new_password = "admin123"  # Simple password for testing

# Hash the password
hashed_password = pwd_context.hash(new_password)

# Update the admin user with the new password
result = db.users.update_one(
    {"email": admin_email},
    {"$set": {"hashed_password": hashed_password}}
)

if result.modified_count > 0:
    print(f"Password updated for admin user {admin_email}")
    print(f"You can now log in with:")
    print(f"Email: {admin_email}")
    print(f"Password: {new_password}")
else:
    print(f"Failed to update password for {admin_email}. User may not exist.")

# Close connection
client.close()
