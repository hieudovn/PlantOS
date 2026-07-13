"""Edge Users API — assign users to edge nodes and push sync."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.db import get_session
from app.middleware.auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


# ---- Schemas ----

class EdgeUserAssignRequest(BaseModel):
    user_id: str

class EdgeUserOut(BaseModel):
    user_id: str
    username: str
    display_name: str
    role: str
    is_active: bool


# ---- Endpoints ----

@router.get("/edges/{edge_node_id}/users", response_model=list[EdgeUserOut],
            dependencies=[Depends(require_admin)])
def list_edge_users(edge_node_id: str):
    """List users assigned to an edge node (admin only)."""
    with get_session() as session:
        rows = session.execute(
            text("""
                SELECT u.id, u.username, u.display_name, u.role, u.is_active
                FROM users u
                JOIN edge_user_assignments eua ON u.id::text = eua.user_id
                WHERE eua.edge_node_id = :eid
                ORDER BY u.username
            """),
            {"eid": edge_node_id},
        ).fetchall()
        return [
            EdgeUserOut(
                user_id=str(r[0]),
                username=r[1],
                display_name=r[2],
                role=r[3],
                is_active=r[4],
            )
            for r in rows
        ]


@router.post("/edges/{edge_node_id}/users", status_code=201,
             dependencies=[Depends(require_admin)])
def assign_user_to_edge(edge_node_id: str, body: EdgeUserAssignRequest):
    """Assign a user to an edge node (admin only)."""
    with get_session() as session:
        # Verify user exists
        user = session.execute(
            text("SELECT id, username FROM users WHERE id = :uid"),
            {"uid": body.user_id},
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if already assigned
        existing = session.execute(
            text("SELECT id FROM edge_user_assignments WHERE edge_node_id = :eid AND user_id = :uid"),
            {"eid": edge_node_id, "uid": body.user_id},
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="User already assigned to this edge")

        session.execute(
            text("INSERT INTO edge_user_assignments (id, edge_node_id, user_id) VALUES (:id, :eid, :uid)"),
            {"id": str(uuid4()), "eid": edge_node_id, "uid": body.user_id},
        )
        session.commit()
    return {"status": "ok", "message": f"User {user[1]} assigned to edge {edge_node_id}"}


@router.delete("/edges/{edge_node_id}/users/{user_id}", status_code=204,
               dependencies=[Depends(require_admin)])
def remove_user_from_edge(edge_node_id: str, user_id: str):
    """Remove a user assignment from an edge node (admin only)."""
    with get_session() as session:
        result = session.execute(
            text("DELETE FROM edge_user_assignments WHERE edge_node_id = :eid AND user_id = :uid"),
            {"eid": edge_node_id, "uid": user_id},
        )
        session.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Assignment not found")


@router.post("/edges/{edge_node_id}/users/sync",
             dependencies=[Depends(require_admin)])
def push_users_to_edge(edge_node_id: str):
    """Push assigned users to an edge node. Returns sync payload."""
    with get_session() as session:
        rows = session.execute(
            text("""
                SELECT u.username, u.password_hash, u.display_name, u.role, u.is_active
                FROM users u
                JOIN edge_user_assignments eua ON u.id::text = eua.user_id
                WHERE eua.edge_node_id = :eid AND u.is_active = TRUE
            """),
            {"eid": edge_node_id},
        ).fetchall()

        if not rows:
            return {"users": [], "synced_at": datetime.now(timezone.utc).isoformat(),
                    "message": "No users assigned to this edge"}

        users = [
            {
                "username": r[0],
                "password_hash": r[1],
                "display_name": r[2],
                "role": r[3],
                "is_active": r[4],
            }
            for r in rows
        ]
        return {
            "users": users,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/edges/{edge_node_id}/users/export",
            dependencies=[Depends(require_admin)])
def export_edge_users(edge_node_id: str):
    """Export user list for edge pull (same as push but GET for edge-initiated sync)."""
    with get_session() as session:
        rows = session.execute(
            text("""
                SELECT u.username, u.password_hash, u.display_name, u.role, u.is_active
                FROM users u
                JOIN edge_user_assignments eua ON u.id::text = eua.user_id
                WHERE eua.edge_node_id = :eid AND u.is_active = TRUE
            """),
            {"eid": edge_node_id},
        ).fetchall()

        users = [
            {
                "username": r[0],
                "password_hash": r[1],
                "display_name": r[2],
                "role": r[3],
                "is_active": r[4],
            }
            for r in rows
        ]
        return {
            "users": users,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
