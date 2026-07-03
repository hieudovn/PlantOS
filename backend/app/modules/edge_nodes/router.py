"""Edge Node — FastAPI router for heartbeat and sync."""

import socket
from fastapi import APIRouter, Request
from pydantic import BaseModel
from datetime import datetime, timezone

from app.modules.edge_nodes.service import build_sync_manifest

router = APIRouter()

_edge_nodes: dict[str, dict] = {}


class HeartbeatRequest(BaseModel):
    edge_node_id: str
    status: str = "online"
    backlog_count: int = 0
    hostname: str = ""
    ip_address: str = ""
    signal_count: int = 0
    version: str = ""


@router.post("/edge-nodes/heartbeat")
def receive_heartbeat(data: HeartbeatRequest, request: Request):
    """Receive heartbeat from edge node."""
    client_ip = data.ip_address or (request.client.host if request.client else "")
    try:
        hostname = data.hostname or socket.gethostbyaddr(client_ip)[0] if client_ip else ""
    except Exception:
        hostname = data.hostname or ""

    _edge_nodes[data.edge_node_id] = {
        "edge_node_id": data.edge_node_id,
        "status": data.status,
        "backlog_count": data.backlog_count,
        "hostname": hostname,
        "ip_address": client_ip,
        "signal_count": data.signal_count,
        "version": data.version,
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
