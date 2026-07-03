"""Auth API — login endpoint with JWT token generation."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.security import create_access_token, verify_password

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    display_name: str


# Pre-computed bcrypt hash for "admin" (passlib bcrypt, rounds=12)
_ADMIN_HASH = "$2b$12$HJXc8NpIHObx5vbmcF2VHubD4aNzWVFunOz8US9rEi9ZUckEGgseG"
_ENG_HASH = "$2b$12$m/pXatm.5tgpMKhCaY/TWul1hC7e3Zkk9hZQHmqhmdC.kVq4rpJeu"

_USERS = {
    "admin": {"password": _ADMIN_HASH, "role": "admin", "display_name": "Administrator"},
    "engineer": {"password": _ENG_HASH, "role": "engineer", "display_name": "Engineer"},
}


@router.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """Authenticate user with username/password and return JWT token."""
    user = _USERS.get(body.username)
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(body.username, body.username)
    return LoginResponse(
        access_token=token,
        username=body.username,
        role=user["role"],
        display_name=user["display_name"],
    )
