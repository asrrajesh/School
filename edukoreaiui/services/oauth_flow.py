"""
Google OAuth 2.0 desktop app flow orchestration.
Frontend gets auth code, sends it to backend for secure exchange.
"""

import webbrowser
import urllib.parse
from services.oauth_server import start_oauth_server, wait_for_oauth_callback, stop_oauth_server
from config.config import GOOGLE_CLIENT_ID, GOOGLE_OAUTH_PORT, GOOGLE_OAUTH_SCOPES


def get_google_auth_url() -> str:
    """Generate Google OAuth authorization URL."""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"http://localhost:{GOOGLE_OAUTH_PORT}/callback",
        "response_type": "code",
        "scope": " ".join(GOOGLE_OAUTH_SCOPES),
        "access_type": "offline",
    }
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    return f"{base_url}?{urllib.parse.urlencode(params)}"


async def authenticate_with_google() -> str | None:
    """
    Orchestrate complete Google OAuth flow for desktop app.
    Returns auth code to be sent to backend for secure token exchange.
    """
    import sys

    # Step 1: Start local server to receive OAuth callback (non-blocking)
    if not start_oauth_server():
        print("[DEBUG] Failed to start OAuth server", file=sys.stderr)
        return None

    print("[DEBUG] OAuth server started", file=sys.stderr)

    # Step 2: Open browser to Google login page
    auth_url = get_google_auth_url()
    print(f"[DEBUG] Opening browser with auth URL", file=sys.stderr)
    webbrowser.open(auth_url)

    # Step 3: Wait for callback with timeout
    auth_code, error = wait_for_oauth_callback(timeout=600)
    if error or not auth_code:
        print(f"[DEBUG] OAuth callback error: {error}", file=sys.stderr)
        return None

    print(f"[DEBUG] Got auth code, returning to send to backend", file=sys.stderr)
    return auth_code
