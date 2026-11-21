"""
Configuration module for CivicResolve.
Handles environment variables, security flags, paths, and admin credential hashing.
"""

import os
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base application configuration."""

    # Security: Secret Key
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        # Fallback for local convenience; production should always set SECRET_KEY
        SECRET_KEY = "civicresolve-fallback-dev-secret-key-change-in-production"

    # Database
    DB_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "civicresolve.db"))

    # File Uploads: 5 MB limit, allowed extensions
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 Megabytes
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Admin Authentication (Hashed Storage)
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    
    # Secure Password Handling: Always hashed with Werkzeug pbkdf2/scrypt
    _raw_admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")
    if not ADMIN_PASSWORD_HASH:
        ADMIN_PASSWORD_HASH = generate_password_hash(_raw_admin_password, method="scrypt")

    # Optional AI Engine
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

    # Rate Limiter defaults
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"

    # Pagination
    ITEMS_PER_PAGE = 10

    @classmethod
    def verify_admin(cls, username: str, password: str) -> bool:
        """Verifies administrative credentials in constant time using password hash."""
        if not username or not password:
            return False
        if username.strip() != cls.ADMIN_USERNAME:
            return False
        return check_password_hash(cls.ADMIN_PASSWORD_HASH, password.strip())

class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production Cloud Run environment configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing environment configuration."""
    DEBUG = False
    TESTING = True
    WTF_CSRF_ENABLED = False
    DB_PATH = os.path.join(BASE_DIR, "test_civicresolve.db")
    RATELIMIT_ENABLED = False
