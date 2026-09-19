from fastapi import APIRouter

from database.db import login_user, register_user, request_password_reset, login_or_create_google_user
from services.google_oauth_service import verify_google_token
from schemas import LoginRequest, SignupRequest, ForgotPasswordRequest, GoogleLoginRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest):
    return login_user(payload.username, payload.password)


@router.post("/signup")
def signup(payload: SignupRequest):
    return register_user(payload.username, payload.password)


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    return request_password_reset(payload.username)


@router.post("/google-callback")
def google_callback(code: str):
    """
    Handle Google OAuth callback: exchange code for token (backend-only, uses client secret).
    Frontend sends the auth code, backend exchanges it securely and creates/links user.
    """
    from services.google_oauth_service import exchange_code_for_token

    # Exchange code for token (using client secret - backend only!)
    token_info = exchange_code_for_token(code)
    if token_info is None:
        return {"success": False, "error": "Failed to exchange auth code for token."}

    # Verify the token
    verified_info = verify_google_token(token_info.get("id_token"))
    if verified_info is None:
        return {"success": False, "error": "Invalid or expired Google token."}

    # Create or link user
    result = login_or_create_google_user(
        google_id=verified_info["google_id"],
        email=verified_info["email"],
        name=verified_info.get("name", "")
    )

    if result["success"]:
        return {"success": True, "user": result["user"]}
    else:
        return result


@router.post("/google-login")
def google_login(payload: GoogleLoginRequest):
    """Handle Google OAuth login: verify token and create/link user."""
    token_info = verify_google_token(payload.token)
    if token_info is None:
        return {"success": False, "error": "Invalid or expired Google token."}

    result = login_or_create_google_user(
        google_id=token_info["google_id"],
        email=token_info["email"],
        name=token_info.get("name", "")
    )

    if result["success"]:
        return {"success": True, "user": result["user"]}
    else:
        return result
