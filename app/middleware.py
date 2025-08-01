from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from app.config import settings
import logging
import re
import time

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Custom security middleware for input sanitization and security headers"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # XSS patterns to detect
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
        ]
        
        # SQL injection patterns
        self.sql_patterns = [
            r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)',
            r'(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+',
            r'[\'";]\s*(OR|AND)\s+[\'"]?\w+[\'"]?\s*=\s*[\'"]?\w+[\'"]?',
        ]
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # CSP header (configurable for challenge 14)
        if request.url.path.startswith("/challenges/14"):
            # Weak CSP for challenge 14
            response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' data:;"
        else:
            # Strong CSP for other pages
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self';"
            )
        
        # Add processing time header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Add flag in header for challenge 9
        if request.url.path.startswith("/challenges/9"):
            response.headers["X-Flag"] = "CTF{information_disclosure_headers}"
        
        return response
    
    def detect_xss(self, text: str) -> bool:
        """Detect potential XSS in input"""
        if not isinstance(text, str):
            return False
        
        text_lower = text.lower()
        for pattern in self.xss_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def detect_sql_injection(self, text: str) -> bool:
        """Detect potential SQL injection in input"""
        if not isinstance(text, str):
            return False
        
        for pattern in self.sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"processed in {process_time:.4f}s"
        )
        
        return response

def setup_cors(app):
    """Setup CORS middleware"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

def setup_rate_limiting(app):
    """Setup rate limiting middleware"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

def setup_security_middleware(app):
    """Setup custom security middleware"""
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(LoggingMiddleware)
