"""Edge Node — FastAPI router for heartbeat and sync."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

from app.modules.edge_nodes.service import build_sync_manifest

router = APIRouter()

# In-memory store for MVP (replace with PostgreSQL in production)
_edge_nodes: dict[str, dict] = {}


class HeartbeatRequest(BaseModel):
    edge_node_id: str
    status: str = "online"
    backlog_count: int = 0


@router.post("/edge-nodes/heartbeat")
def receive_heartbeat(data: HeartbeatRequest):
    """Receive heartbeat from edge node."""
    _edge_nodes[data.edge_node_id] = {
        "edge_node_id": data.edge_node_id,
        "status": data.status,
        "backlog_count": data.backlog_count,
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
    }
    return {"status": "ok"}


@router.get("/edge-nodes")
def list_edge_nodes():
    """List all known edge nodes."""
    return list(_edge_nodes.values())


@router.get("/edge/sync/manifest")
def get_sync_manifest():
    """Return full asset + signal manifest for edge nodes to sync."""
    manifest = build_sync_manifest()
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["version"] = "1.0"
    return manifest
