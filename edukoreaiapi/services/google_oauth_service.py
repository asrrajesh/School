"""
Google OAuth 2.0 token verification and code exchange for desktop app.
Handles: code-to-token exchange (backend-only, uses client secret), token verification.
"""

import json
import urllib.parse
import urllib.request
from google.auth.transport import requests
from google.oauth2 import id_token
from config.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


def exchange_code_for_token(code: str) -> dict | None:
    """
    Exchange authorization code for ID token (backend-only, uses client secret).

    Args:
        code: Authorization code from Google OAuth redirect

    Returns:
        Dictionary with 'id_token' and 'access_token' or None if failed
    """
    import sys
    try:
        token_url = "https://oauth2.googleapis.com/token"
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": "http://localhost:8080/callback",
            "grant_type": "authorization_code",
        }

        print(f"[DEBUG] Exchanging code for token...", file=sys.stderr)
        data = urllib.parse.urlencode(params).encode("utf-8")
        response = urllib.request.urlopen(token_url, data)
        response_text = response.read().decode("utf-8")
        print(f"[DEBUG] Token response received, parsing...", file=sys.stderr)

        token_data = json.loads(response_text)

        result = {
            "id_token": token_data.get("id_token"),
            "access_token": token_data.get("access_token"),
        }
        print(f"[DEBUG] Got id_token: {bool(result.get('id_token'))}", file=sys.stderr)
        return result
    except Exception as e:
        import traceback
        print(f"[DEBUG] Token exchange error: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return None


def verify_google_token(token: str) -> dict | None:
    """
    Verify a Google ID token and return user information.

    Args:
        token: ID token from Google OAuth callback

    Returns:
        Dictionary with 'sub' (user ID), 'email', 'name', 'picture' or None if invalid
    """
    import sys
    try:
        print(f"[DEBUG] Verifying token, client_id={GOOGLE_CLIENT_ID}", file=sys.stderr)
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10  # Allow 10 sec tolerance for clock differences
        )

        print(f"[DEBUG] Token verified! Email: {idinfo.get('email')}", file=sys.stderr)
        # Token is valid, extract user info
        return {
            "google_id": idinfo.get("sub"),  # Unique Google user ID
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture"),
        }
    except Exception as e:
        import traceback
        print(f"[DEBUG] Token verification error: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        # Token verification failed (invalid, expired, etc.)
        return None
