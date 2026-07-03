"""Auth API — login endpoint with JWT token generation."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from app.core.security import create_access_token, verify_password
from app.db import get_session

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


@router.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """Authenticate user with username/password and return JWT token."""
    with get_session() as session:
        row = session.execute(
            text("SELECT username, password_hash, role, display_name, is_active FROM users WHERE username = :username"),
            {"username": body.username},
        ).fetchone()

        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        username, pwd_hash, role, display_name, is_active = row

        if not is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        if not verify_password(body.password, pwd_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(username, username, role)
        return LoginResponse(
            access_token=token,
            username=username,
            role=role,
            display_name=display_name,
        )
