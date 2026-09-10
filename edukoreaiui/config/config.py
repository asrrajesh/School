"""
Configuration module for EduKoreAI application.
Loads all application settings from .env file using python-dotenv.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (skip if unavailable, e.g. in a
# packaged mobile build where dotenv's stack-based file lookup can't work).
# The project configuration takes precedence over stale terminal variables.
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
# API SERVER CONFIGURATION
# ─────────────────────────────────────────────────────────────────────

# Base URL of the edukoreaiapi backend (see ../edukoreaiapi).
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


# ─────────────────────────────────────────────────────────────────────
# APPLICATION SETTINGS
# ─────────────────────────────────────────────────────────────────────

APP_TITLE = os.getenv("APP_TITLE", "EduKoreAI")
THEME_COLOR = os.getenv("THEME_COLOR", "#3949AB")


# ─────────────────────────────────────────────────────────────────────
# WINDOW CONFIGURATION
# ─────────────────────────────────────────────────────────────────────

WINDOW_WIDTH = get_env_int("WINDOW_WIDTH", 400)
WINDOW_HEIGHT = get_env_int("WINDOW_HEIGHT", 780)
WINDOW_RESIZABLE = get_env_bool("WINDOW_RESIZABLE", True)
BACKGROUND_COLOR = os.getenv("BACKGROUND_COLOR", "#F5F5F5")
