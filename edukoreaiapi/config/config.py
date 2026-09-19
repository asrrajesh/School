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


# ─────────────────────────────────────────────────────────────────────
# OCR CONFIGURATION
# ─────────────────────────────────────────────────────────────────────
# Selects the OCR backend used to turn scanned images into text, decoupled
# from the LLM used afterwards for question generation.
# "easyocr"    — local, free, works with any LLM_PROVIDER (including
#                text-only models like qwen3:8b on Ollama).
# "llm_vision" — send images to the configured LLM_PROVIDER (must be a
#                vision-capable model, e.g. claude/openai/gemini/llava).
OCR_ENGINE = os.getenv("OCR_ENGINE", "easyocr").strip().lower()
OCR_LANGUAGES = [lang.strip() for lang in os.getenv("OCR_LANGUAGES", "en").split(",") if lang.strip()]
OCR_USE_GPU = get_env_bool("OCR_USE_GPU", False)


# ─────────────────────────────────────────────────────────────────────
# LLM PROVIDER CONFIGURATION
# ─────────────────────────────────────────────────────────────────────
# Selects which LLM backend the llm.factory module builds. Switching
# providers only requires changing LLM_PROVIDER (and that provider's
# settings below) — no code changes needed.
# One of: "claude" | "ollama" | "openai" | "gemini"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").strip().lower()

LLM_MAX_TOKENS = get_env_int("LLM_MAX_TOKENS", 4096)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))

# -- Anthropic Claude --
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

# -- OpenAI --
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# -- Google Gemini --
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

# -- Ollama (local models) --
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llava")
OLLAMA_REQUEST_TIMEOUT = get_env_int("OLLAMA_REQUEST_TIMEOUT", 120)


# ─────────────────────────────────────────────────────────────────────
# GOOGLE OAUTH CONFIGURATION
# ─────────────────────────────────────────────────────────────────────

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_OAUTH_SCOPES = os.getenv(
    "GOOGLE_OAUTH_SCOPES",
    "openid,https://www.googleapis.com/auth/userinfo.profile,https://www.googleapis.com/auth/userinfo.email"
).split(",")


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
