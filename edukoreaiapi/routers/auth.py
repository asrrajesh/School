from fastapi import APIRouter

from database.db import login_user, register_user, request_password_reset
from schemas import LoginRequest, SignupRequest, ForgotPasswordRequest

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
