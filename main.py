from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

# Import database and auth
from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.auth import create_admin_user_data
from app.config import settings

# Import routers
from app.routers import auth, challenges, admin, ads, static, leaderboard, analytics
from app.routers import challenge_bypass_login, challenge_sql_injection, challenge_reflected_xss, challenge_cookie_manipulation

# Import middleware
from app.middleware import setup_cors, setup_rate_limiting, setup_security_middleware, limiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting CTF Platform Backend...")
    
    # Connect to database
    await connect_to_mongo()
    
    # Create admin user if it doesn't exist
    await create_default_admin()
    
    # Initialize default challenges
    await initialize_default_challenges()
    
    # Initialize default ads
    await initialize_default_ads()
    
    logger.info("CTF Platform Backend started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CTF Platform Backend...")
    await close_mongo_connection()
    logger.info("CTF Platform Backend shut down successfully!")

# Create FastAPI app
app = FastAPI(
    title="CTF Platform Backend",
    description="Backend API for Capture The Flag challenges platform",
    version="1.0.0",
    lifespan=lifespan
)

# Setup middleware - CORS must be first to handle OPTIONS requests
setup_cors(app)

# Add explicit OPTIONS handler for problematic endpoints
@app.options("/auth/register")
@app.options("/analytics/visits")
async def handle_options():
    return {"message": "OK"}

setup_rate_limiting(app)
setup_security_middleware(app)

# Include routers
app.include_router(auth.router)
app.include_router(challenges.router)
app.include_router(admin.router)
app.include_router(ads.router)
app.include_router(static.router)
app.include_router(leaderboard.router)
app.include_router(analytics.router)
app.include_router(challenge_bypass_login.router)
app.include_router(challenge_sql_injection.router)
app.include_router(challenge_reflected_xss.router)
app.include_router(challenge_cookie_manipulation.router)

# Mount static files
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Rate limited endpoints
@app.get("/")
@limiter.limit(f"{settings.rate_limit_requests}/minute")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "CTF Platform Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = get_database()
        # Test database connection
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

async def create_default_admin():
    """Create default admin user if it doesn't exist"""
    try:
        db = get_database()
        
        # Check if admin exists by email or username
        admin_exists = await db.users.find_one({
            "$or": [
                {"email": settings.admin_email},
                {"username": "admin"}
            ]
        })
        if not admin_exists:
            admin_data = create_admin_user_data(
                email=settings.admin_email,
                password=settings.admin_password,
                username="admin"
            )
            await db.users.insert_one(admin_data)
            logger.info(f"Default admin user created: {settings.admin_email}")
        else:
            logger.info("Admin user already exists")
            
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")

async def initialize_default_challenges():
    """Initialize default CTF challenges"""
    try:
        db = get_database()
        
        # Check if challenges already exist
        challenge_count = await db.challenges.count_documents({})
        if challenge_count > 0:
            logger.info(f"Challenges already exist ({challenge_count} found)")
            return
        
        # Default challenges data
        default_challenges = [
            {
                "_id": "1",
                "challenge_number": 1,
                "title": "Bypass the Login",
                "slug": "bypass-login",
                "category": "Authentication",
                "description": "Can you bypass this login form? Sometimes the logic isn't as secure as it appears.",
                "points": 10,
                "difficulty": "easy",
                "solution_type": "input",
                "expected_flag": "CTF{insecure_auth_logic_bypass}",
                "frontend_hint": "Try different combinations of username and password. Look for logical flaws.",
                "backend_validation_script": "validate_challenge_1",
                "frontend_config": {
                    "form_fields": ["username", "password"],
                    "submit_endpoint": "/challenges/1/submit"
                },
                "is_active": True,
                "solve_count": 0
            },
            {
                "_id": "2",
                "challenge_number": 2,
                "title": "SQL Injection",
                "slug": "sql-injection",
                "category": "SQLi",
                "description": "This search form looks vulnerable to SQL injection. Can you extract the flag from the database?",
                "points": 10,
                "difficulty": "medium",
                "solution_type": "input",
                "expected_flag": "CTF{sql_injection_union_attack}",
                "frontend_hint": "Try using UNION SELECT to extract data from other tables.",
                "backend_validation_script": "validate_challenge_2",
                "frontend_config": {
                    "form_fields": ["input"],
                    "placeholder": "Search for products...",
                    "submit_endpoint": "/challenges/2/submit"
                },
                "is_active": True,
                "solve_count": 0
            },
            {
                "_id": "3",
                "challenge_number": 3,
                "title": "Reflected XSS",
                "slug": "reflected-xss",
                "category": "XSS",
                "description": "This page reflects user input without proper sanitization. Can you steal the admin's cookie?",
                "points": 10,
                "difficulty": "medium",
                "solution_type": "input",
                "expected_flag": "CTF{xss_cookie_theft}",
                "frontend_hint": "Inject JavaScript to steal cookies. The admin cookie contains the flag.",
                "backend_validation_script": "validate_challenge_3",
                "frontend_config": {
                    "form_fields": ["payload", "cookie"],
                    "submit_endpoint": "/challenges/3/submit",
                    "admin_cookie": "admin_session=CTF{xss_cookie_theft}"
                },
                "is_active": True,
                "solve_count": 0
            },
            {
                "_id": "4",
                "challenge_number": 4,
                "title": "Hidden in the Cookie",
                "slug": "cookie-manipulation",
                "category": "Cookie Manipulation",
                "description": "This application uses cookies to determine user privileges. Can you become an admin?",
                "points": 10,
                "difficulty": "easy",
                "solution_type": "cookie",
                "expected_flag": "CTF{cookie_manipulation_admin}",
                "frontend_hint": "Check your browser's developer tools and modify the cookie value.",
                "backend_validation_script": "validate_challenge_4",
                "frontend_config": {
                    "default_cookie": "user_role=guest",
                    "submit_endpoint": "/challenges/4/submit"
                },
                "is_active": True,
                "solve_count": 0
            },
            {
                "_id": "5",
                "challenge_number": 5,
                "title": "Guess the Admin Panel",
                "slug": "admin-panel-discovery",
                "category": "Obscurity",
                "description": "There's a hidden admin panel somewhere on this site. Can you find it?",
                "points": 10,
                "difficulty": "easy",
                "solution_type": "path",
                "expected_flag": "CTF{security_through_obscurity_fail}",
                "frontend_hint": "Try common admin paths or use directory enumeration techniques.",
                "backend_validation_script": "validate_challenge_5",
                "frontend_config": {
                    "submit_endpoint": "/challenges/5/submit",
                    "check_paths": ["/admin", "/administrator", "/super/secret/flag", "/admin/hidden/flag"]
                },
                "is_active": True,
                "solve_count": 0
            }
        ]
        
        # Add more challenges (6-15) with similar structure
        additional_challenges = [
            {
                "_id": str(i),
                "challenge_number": i,
                "title": f"Challenge {i}",
                "slug": f"challenge-{i}",
                "category": "Web Security",
                "description": f"This is challenge {i}. Complete the objective to get the flag.",
                "points": 10,
                "difficulty": "medium",
                "solution_type": "input",
                "expected_flag": f"CTF{{challenge_{i}_flag}}",
                "frontend_hint": f"Solve challenge {i} using web security techniques.",
                "backend_validation_script": f"validate_challenge_{i}",
                "frontend_config": {"submit_endpoint": f"/challenges/{i}/submit"},
                "is_active": True,
                "solve_count": 0
            }
            for i in range(6, 16)
        ]
        
        all_challenges = default_challenges + additional_challenges
        
        # Insert challenges
        await db.challenges.insert_many(all_challenges)
        logger.info(f"Initialized {len(all_challenges)} default challenges")
        
    except Exception as e:
        logger.error(f"Failed to initialize challenges: {e}")

async def initialize_default_ads():
    """Initialize default advertisements"""
    try:
        db = get_database()
        
        # Check if ads already exist
        ad_count = await db.ads.count_documents({})
        if ad_count > 0:
            logger.info(f"Ads already exist ({ad_count} found)")
            return
        
        default_ads = [
            {
                "position": "top",
                "content": "🔐 Learn Cybersecurity with our CTF Platform! Master web security through hands-on challenges.",
                "is_active": True,
                "click_count": 0,
                "impression_count": 0
            },
            {
                "position": "sidebar",
                "content": "💡 Stuck on a challenge? Check out our hints and walkthroughs!",
                "is_active": True,
                "click_count": 0,
                "impression_count": 0
            },
            {
                "position": "bottom",
                "content": "🏆 Compete with other hackers on our leaderboard! Solve challenges to earn points.",
                "is_active": True,
                "click_count": 0,
                "impression_count": 0
            }
        ]
        
        await db.ads.insert_many(default_ads)
        logger.info(f"Initialized {len(default_ads)} default ads")
        
    except Exception as e:
        logger.error(f"Failed to initialize ads: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
