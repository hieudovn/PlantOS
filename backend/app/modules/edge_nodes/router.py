"""Edge Node — FastAPI router for heartbeat and sync."""

import socket
from fastapi import APIRouter, Request
from pydantic import BaseModel
from datetime import datetime, timezone

from app.db import get_session
from app.modules.edge_nodes.models import EdgeNode
from app.modules.edge_nodes.service import build_sync_manifest

router = APIRouter()


class HeartbeatRequest(BaseModel):
    edge_node_id: str
    status: str = "online"
    backlog_count: int = 0
    hostname: str = ""
    ip_address: str = ""
    signal_count: int = 0
    version: str = ""


@router.post("/edge-nodes/heartbeat")
async def receive_heartbeat(data: HeartbeatRequest, request: Request):
    """Receive heartbeat from edge node. Persists to PostgreSQL."""
    from app.core.events import dispatch

    client_ip = data.ip_address or (request.client.host if request.client else "")
    try:
        hostname = data.hostname or socket.gethostbyaddr(client_ip)[0] if client_ip else ""
    except Exception:
        hostname = data.hostname or ""

    # Upsert into EdgeNode PostgreSQL table
    with get_session() as session:
        node = session.query(EdgeNode).filter_by(edge_node_id=data.edge_node_id).first()
        if node is None:
            node = EdgeNode(
                edge_node_id=data.edge_node_id,
                name=data.edge_node_id,
                node_type="simulator",
            )
            session.add(node)
        node.status = data.status
        node.last_heartbeat = datetime.now(timezone.utc)
        node.hostname = hostname or None
        node.ip_address = client_ip or None
        node.edge_version = data.version or None
        node.signal_count = data.signal_count
        node.backlog_count = data.backlog_count
        session.commit()

    # Dispatch EdgeHeartbeat event
    edge_data = {
        "edge_node_id": data.edge_node_id,
        "status": data.status,
        "ip_address": client_ip,
        "signal_count": data.signal_count,
        "version": data.version,
    }
    await dispatch("edge.heartbeat", {"edge": edge_data})

    return {"status": "ok"}


@router.get("/edge-nodes")
def list_edge_nodes():
    """List all known edge nodes from PostgreSQL."""
    with get_session() as session:
        nodes = session.query(EdgeNode).order_by(EdgeNode.last_heartbeat.desc().nullslast()).all()
        return [
            {
                "edge_node_id": n.edge_node_id,
                "status": n.status,
                "last_heartbeat": n.last_heartbeat.isoformat() if n.last_heartbeat else None,
                "hostname": n.hostname,
                "ip_address": n.ip_address,
                "version": n.edge_version,
                "signal_count": n.signal_count,
                "backlog_count": n.backlog_count,
            }
            for n in nodes
        ]


@router.get("/edge/sync/manifest")
def get_sync_manifest():
    """Return full asset + signal manifest for edge nodes to sync."""
    manifest = build_sync_manifest()
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["version"] = "1.0"
    return manifest
