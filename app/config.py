from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "ctf_platform"
    
    # JWT
    secret_key: str = "your-super-secret-jwt-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS - Parse comma-separated string
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Admin - Secure admin token (remove demo credentials)
    admin_email: str = "admin@ctfplatform.local"
    admin_password: str = "CTF_Admin_2025_SecurePass!@#"
    admin_token: str = "ctf_admin_token_2025_secure_access_key_xyz789"
    
    # File Upload
    max_file_size: int = 5242880  # 5MB
    upload_dir: str = "./uploads"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()
