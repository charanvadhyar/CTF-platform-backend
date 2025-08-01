from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse, PlainTextResponse
from app.models.user import UserInDB
from app.auth import get_current_user
from app.config import settings
import os
import aiofiles
import hashlib
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/static", tags=["static"])

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """Upload a file (for challenge 11 - File Upload)"""
    
    # Check file size
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.max_file_size} bytes"
        )
    
    # Generate unique filename
    file_hash = hashlib.md5(f"{current_user.id}_{file.filename}".encode()).hexdigest()
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{file_hash}{file_extension}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    try:
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"User {current_user.email} uploaded file: {file.filename}")
        
        return {
            "message": "File uploaded successfully",
            "filename": unique_filename,
            "original_filename": file.filename,
            "size": file.size,
            "url": f"/static/files/{unique_filename}"
        }
    
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed"
        )

@router.get("/files/{filename}")
async def get_file(filename: str):
    """Serve uploaded files"""
    file_path = os.path.join(settings.upload_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(file_path)

@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    """Serve robots.txt (for challenge 12)"""
    robots_content = """User-agent: *
Disallow: /admin/
Disallow: /api/admin/
Disallow: /admin/staging-area/
Disallow: /admin/staging-area/flag.txt

# Hidden admin areas
Disallow: /super/secret/
Disallow: /hidden/admin/
"""
    return robots_content

@router.get("/admin/staging-area/flag.txt", response_class=PlainTextResponse)
async def staging_flag():
    """Hidden flag endpoint (for challenge 12)"""
    return "CTF{robots_txt_information_disclosure}"

@router.get("/super/secret/flag", response_class=PlainTextResponse)
async def secret_flag():
    """Secret admin flag endpoint (for challenge 5)"""
    return "CTF{security_through_obscurity_fail}"

@router.get("/admin/hidden/flag", response_class=PlainTextResponse)
async def hidden_flag():
    """Another hidden flag endpoint (for challenge 5)"""
    return "CTF{security_through_obscurity_fail}"

@router.get("/csp-violation")
async def csp_violation_page():
    """CSP violation reporting endpoint (for challenge 14)"""
    return {"message": "CSP violation reported"}

@router.post("/csp-violation")
async def report_csp_violation():
    """Handle CSP violation reports (for challenge 14)"""
    return {"message": "CSP violation report received"}

@router.get("/sourcemap/{filename}")
async def serve_sourcemap(filename: str):
    """Serve source maps with embedded flags (for challenge 15)"""
    if filename == "main.js.map":
        sourcemap_content = {
            "version": 3,
            "sources": ["main.js"],
            "names": [],
            "mappings": "AAAA,QAAQ,GAAG,CAAC,6BAA6B",
            "sourcesContent": [
                "// Main application file\n// FLAG: CTF{hardcoded_secrets_in_source}\nconst app = {};"
            ]
        }
        return sourcemap_content
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Source map not found"
    )

@router.get("/js/{filename}")
async def serve_javascript(filename: str):
    """Serve JavaScript files with embedded secrets (for challenge 15)"""
    if filename == "app.js":
        js_content = """
// Application JavaScript
const config = {
    apiUrl: '/api',
    // TODO: Remove this before production
    // FLAG: CTF{hardcoded_secrets_in_source}
    debugMode: true
};

function initApp() {
    console.log('App initialized');
}
"""
        return PlainTextResponse(js_content, media_type="application/javascript")
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="JavaScript file not found"
    )

@router.get("/redirect")
async def open_redirect(url: Optional[str] = None):
    """Open redirect endpoint (for challenge 8)"""
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL parameter required"
        )
    
    # Vulnerable redirect - no validation
    if "flag.php" in url or "admin/flag" in url:
        return {"message": "Redirecting to flag", "flag": "CTF{open_redirect_to_flag}"}
    
    return {"message": f"Redirecting to {url}", "redirect_url": url}
