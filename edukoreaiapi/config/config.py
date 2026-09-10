"""
Configuration module for the EduKoreAI API server.
Loads all application settings from .env file using python-dotenv.
"""

import os
from dotenv import load_dotenv

try:
    load_dotenv(override=True)
except Exception:
    pass


def get_env_bool(key: str, default: bool) -> bool:
    """Convert environment variable to boolean."""
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


def get_env_int(key: str, default: int) -> int:
    """Convert environment variable to integer."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


# ─────────────────────────────────────────────────────────────────────
# DATABASE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "MySchool")
DB_CONNECTION_TIMEOUT = get_env_int("DB_CONNECTION_TIMEOUT", 5000)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")


# ─────────────────────────────────────────────────────────────────────
# SECURITY SETTINGS
# ─────────────────────────────────────────────────────────────────────

PASSWORD_MIN_LENGTH = get_env_int("PASSWORD_MIN_LENGTH", 8)


# ─────────────────────────────────────────────────────────────────────
# VALIDATION SETTINGS
# ─────────────────────────────────────────────────────────────────────

EMAIL_PATTERN = os.getenv(
    "EMAIL_PATTERN",
    r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$"
)
MOBILE_PATTERN = os.getenv(
    "MOBILE_PATTERN",
    r"^\+?[0-9]{10,15}$"
)


# ─────────────────────────────────────────────────────────────────────
# SERVER CONFIGURATION
# ─────────────────────────────────────────────────────────────────────

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = get_env_int("API_PORT", 8000)

# Comma-separated list of allowed CORS origins, "*" to allow all.
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",")]
