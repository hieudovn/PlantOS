"""Users API — admin-only CRUD for user management."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.security import hash_password
from app.db import get_session
from app.middleware.auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


# ---- Schemas ----

class UserOut(BaseModel):
    id: str
    username: str
    display_name: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=128)
    role: str = Field(default="operator", pattern="^(admin|engineer|operator)$")


class UserUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=128)
    role: str | None = Field(None, pattern="^(admin|engineer|operator)$")
    is_active: bool | None = None
    password: str | None = Field(None, min_length=6, max_length=128)


# ---- Endpoints ----

@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_admin)])
def list_users():
    """List all users (admin only)."""
    with get_session() as session:
        rows = session.execute(
            text("SELECT id, username, display_name, role, is_active, created_at, updated_at FROM users ORDER BY created_at")
        ).fetchall()
        return [
            UserOut(
                id=str(r[0]),
                username=r[1],
                display_name=r[2],
                role=r[3],
                is_active=r[4],
                created_at=r[5].isoformat() if r[5] else "",
                updated_at=r[6].isoformat() if r[6] else "",
            )
            for r in rows
        ]


@router.get("/users/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
def get_user(user_id: str):
    """Get single user by ID (admin only)."""
    with get_session() as session:
        row = session.execute(
            text("SELECT id, username, display_name, role, is_active, created_at, updated_at FROM users WHERE id = :id"),
            {"id": user_id},
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return UserOut(
            id=str(row[0]),
            username=row[1],
            display_name=row[2],
            role=row[3],
            is_active=row[4],
            created_at=row[5].isoformat() if row[5] else "",
            updated_at=row[6].isoformat() if row[6] else "",
        )


@router.post("/users", response_model=UserOut, status_code=201, dependencies=[Depends(require_admin)])
def create_user(body: UserCreate):
    """Create a new user (admin only)."""
    with get_session() as session:
        # Check uniqueness
        existing = session.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": body.username},
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Username already exists")

        now = datetime.now(timezone.utc)
        user_id = str(uuid4())
        pwd_hash = hash_password(body.password)

        session.execute(
            text(
                "INSERT INTO users (id, username, password_hash, display_name, role, is_active, created_at, updated_at) "
                "VALUES (:id, :username, :pwd_hash, :display_name, :role, TRUE, :now, :now)"
            ),
            {
                "id": user_id,
                "username": body.username,
                "pwd_hash": pwd_hash,
                "display_name": body.display_name,
                "role": body.role,
                "now": now,
            },
        )
        session.commit()

        return UserOut(
            id=user_id,
            username=body.username,
            display_name=body.display_name,
            role=body.role,
            is_active=True,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )


@router.put("/users/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
def update_user(user_id: str, body: UserUpdate):
    """Update a user (admin only). Supports partial updates."""
    with get_session() as session:
        row = session.execute(
            text("SELECT id, username, display_name, role, is_active, created_at FROM users WHERE id = :id"),
            {"id": user_id},
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        now = datetime.now(timezone.utc)
        display_name = body.display_name if body.display_name is not None else row[2]
        role = body.role if body.role is not None else row[3]
        is_active = body.is_active if body.is_active is not None else row[4]

        if body.password:
            pwd_hash = hash_password(body.password)
            session.execute(
                text("UPDATE users SET display_name=:dn, role=:r, is_active=:ia, password_hash=:ph, updated_at=:now WHERE id=:id"),
                {"dn": display_name, "r": role, "ia": is_active, "ph": pwd_hash, "now": now, "id": user_id},
            )
        else:
            session.execute(
                text("UPDATE users SET display_name=:dn, role=:r, is_active=:ia, updated_at=:now WHERE id=:id"),
                {"dn": display_name, "r": role, "ia": is_active, "now": now, "id": user_id},
            )
        session.commit()

        return UserOut(
            id=user_id,
            username=row[1],
            display_name=display_name,
            role=role,
            is_active=is_active,
            created_at=row[5].isoformat() if row[5] else "",
            updated_at=now.isoformat(),
        )


@router.delete("/users/{user_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_user(user_id: str):
    """Deactivate a user (admin only). Soft delete — sets is_active=False."""
    with get_session() as session:
        row = session.execute(
            text("SELECT id FROM users WHERE id = :id"),
            {"id": user_id},
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        session.execute(
            text("UPDATE users SET is_active = FALSE, updated_at = :now WHERE id = :id"),
            {"now": datetime.now(timezone.utc), "id": user_id},
        )
        session.commit()
