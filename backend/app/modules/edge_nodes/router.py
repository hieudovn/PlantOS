"""Edge Node — FastAPI router for heartbeat, commands, and fleet management."""

import socket
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Any

from app.db import get_session
from app.modules.edge_nodes.models import (
    EdgeNode, EdgeHeartbeat, EdgeConnector, EdgeCommand, EdgeConfigVersion,
)
from app.modules.edge_nodes.service import build_sync_manifest
from app.modules.edge_nodes.commands import validate_command, ALLOWED_COMMANDS

router = APIRouter()

# ---- Request/Response models ------------------------------------------------

class ConnectorInfo(BaseModel):
    connector_id: str
    type: str = ""
    status: str = "stopped"
    signal_count: int = 0
    last_error: str | None = None


class HeartbeatRequest(BaseModel):
    edge_node_id: str
    status: str = "online"
    backlog_count: int = 0
    hostname: str = ""
    ip_address: str = ""
    signal_count: int = 0
    version: str = ""
    # v2 fields
    center_sync: str | None = None
    disk_usage_mb: float | None = None
    capabilities: list[str] | None = None
    connectors: list[ConnectorInfo] | None = None


class CommandCreateRequest(BaseModel):
    command_type: str
    target: str | None = None
    params: dict[str, Any] | None = None


class CommandResultRequest(BaseModel):
    status: str  # "success" or "failed"
    result_message: str | None = None


# ---- Heartbeat --------------------------------------------------------------

@router.post("/edge-nodes/heartbeat")
async def receive_heartbeat(data: HeartbeatRequest, request: Request):
    """Receive heartbeat from edge node. Supports v1 and v2 formats."""
    from app.core.events import dispatch

    client_ip = data.ip_address or (request.client.host if request.client else "")
    try:
        hostname = data.hostname or socket.gethostbyaddr(client_ip)[0] if client_ip else ""
    except Exception:
        hostname = data.hostname or ""

    now = datetime.now(timezone.utc)

    with get_session() as session:
        # Upsert EdgeNode
        node = session.query(EdgeNode).filter_by(edge_node_id=data.edge_node_id).first()
        if node is None:
            node = EdgeNode(
                edge_node_id=data.edge_node_id,
                name=data.edge_node_id,
                node_type="simulator",
            )
            session.add(node)
        node.status = data.status
        node.last_heartbeat = now
        node.hostname = hostname or None
        node.ip_address = client_ip or None
        node.edge_version = data.version or None
        node.signal_count = data.signal_count
        node.backlog_count = data.backlog_count
        if data.center_sync is not None:
            node.center_sync = data.center_sync
        if data.disk_usage_mb is not None:
            node.disk_usage_mb = int(data.disk_usage_mb)
        if data.capabilities is not None:
            node.capabilities = data.capabilities

        # Insert EdgeHeartbeat record
        heartbeat = EdgeHeartbeat(
            edge_node_id=data.edge_node_id,
            status=data.status,
            backlog_count=data.backlog_count,
            signal_count=data.signal_count,
            hostname=hostname or None,
            ip_address=client_ip or None,
            edge_version=data.version or None,
            center_sync=data.center_sync,
            disk_usage_mb=data.disk_usage_mb,
            received_at=now,
        )
        session.add(heartbeat)

        # Upsert EdgeConnector records from v2 heartbeat
        if data.connectors:
            connectors_json = []
            for ci in data.connectors:
                connectors_json.append(ci.model_dump())
                existing = session.query(EdgeConnector).filter_by(
                    edge_node_id=data.edge_node_id, connector_id=ci.connector_id
                ).first()
                if existing:
                    existing.status = ci.status
                    existing.connector_type = ci.type
                    existing.signal_count = ci.signal_count
                    existing.last_error = ci.last_error
                    existing.last_heartbeat = now
                else:
                    session.add(EdgeConnector(
                        edge_node_id=data.edge_node_id,
                        connector_id=ci.connector_id,
                        connector_type=ci.type,
                        status=ci.status,
                        signal_count=ci.signal_count,
                        last_error=ci.last_error,
                        last_heartbeat=now,
                    ))
            heartbeat.connectors_json = connectors_json

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


# ---- Edge Node List & Detail -------------------------------------------------

@router.get("/edge-nodes")
def list_edge_nodes():
    """List all known edge nodes from PostgreSQL."""
    with get_session() as session:
        nodes = session.query(EdgeNode).order_by(EdgeNode.last_heartbeat.desc().nullslast()).all()
        return [
            {
                "edge_node_id": n.edge_node_id,
                "node_type": n.node_type,
                "status": n.status,
                "last_heartbeat": n.last_heartbeat.isoformat() if n.last_heartbeat else None,
                "hostname": n.hostname,
                "ip_address": n.ip_address,
                "version": n.edge_version,
                "signal_count": n.signal_count,
                "backlog_count": n.backlog_count,
                "center_sync": n.center_sync,
                "disk_usage_mb": n.disk_usage_mb,
                "workspace_id": n.workspace_id,
            }
            for n in nodes
        ]


@router.get("/edge-nodes/{edge_node_id}")
def get_edge_node(edge_node_id: str):
    """Get edge node detail with latest info."""
    with get_session() as session:
        node = session.query(EdgeNode).filter_by(edge_node_id=edge_node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Edge node not found")

        # Latest heartbeat
        latest_hb = session.query(EdgeHeartbeat).filter_by(
            edge_node_id=edge_node_id
        ).order_by(EdgeHeartbeat.received_at.desc()).first()

        # Connector count
        connector_count = session.query(EdgeConnector).filter_by(
            edge_node_id=edge_node_id
        ).count()

        # Recent command count
        recent_cmd_count = session.query(EdgeCommand).filter_by(
            edge_node_id=edge_node_id
        ).count()

        return {
            "edge_node_id": node.edge_node_id,
            "node_type": node.node_type,
            "status": node.status,
            "last_heartbeat": node.last_heartbeat.isoformat() if node.last_heartbeat else None,
            "hostname": node.hostname,
            "ip_address": node.ip_address,
            "version": node.edge_version,
            "signal_count": node.signal_count,
            "backlog_count": node.backlog_count,
            "center_sync": node.center_sync,
            "disk_usage_mb": node.disk_usage_mb,
            "capabilities": node.capabilities,
            "workspace_id": node.workspace_id,
            "latest_heartbeat": {
                "received_at": latest_hb.received_at.isoformat() if latest_hb else None,
                "status": latest_hb.status if latest_hb else None,
                "backlog_count": latest_hb.backlog_count if latest_hb else 0,
                "signal_count": latest_hb.signal_count if latest_hb else 0,
                "connectors": latest_hb.connectors_json if latest_hb else [],
            } if latest_hb else None,
            "connector_count": connector_count,
            "recent_command_count": recent_cmd_count,
        }


# ---- Connector Status --------------------------------------------------------

@router.get("/edge-nodes/{edge_node_id}/connectors")
def list_edge_connectors(edge_node_id: str):
    """List connector status for an edge node."""
    with get_session() as session:
        connectors = session.query(EdgeConnector).filter_by(
            edge_node_id=edge_node_id
        ).all()
        return [
            {
                "connector_id": c.connector_id,
                "type": c.connector_type,
                "status": c.status,
                "signal_count": c.signal_count,
                "last_error": c.last_error,
                "last_heartbeat": c.last_heartbeat.isoformat() if c.last_heartbeat else None,
            }
            for c in connectors
        ]


@router.get("/edge-nodes/{edge_node_id}/heartbeats")
def list_edge_heartbeats(edge_node_id: str, limit: int = 100):
    """List recent heartbeats for an edge node (paginated)."""
    with get_session() as session:
        hbs = session.query(EdgeHeartbeat).filter_by(
            edge_node_id=edge_node_id
        ).order_by(EdgeHeartbeat.received_at.desc()).limit(limit).all()
        return [
            {
                "id": str(hb.id),
                "status": hb.status,
                "backlog_count": hb.backlog_count,
                "signal_count": hb.signal_count,
                "hostname": hb.hostname,
                "ip_address": hb.ip_address,
                "edge_version": hb.edge_version,
                "center_sync": hb.center_sync,
                "disk_usage_mb": hb.disk_usage_mb,
                "connectors": hb.connectors_json,
                "received_at": hb.received_at.isoformat() if hb.received_at else None,
            }
            for hb in hbs
        ]


# ---- Commands ----------------------------------------------------------------

@router.post("/edge-nodes/{edge_node_id}/commands")
def create_command(edge_node_id: str, data: CommandCreateRequest):
    """Create a command for an edge node."""
    errors = validate_command(data.command_type, data.target)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    with get_session() as session:
        node = session.query(EdgeNode).filter_by(edge_node_id=edge_node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Edge node not found")

        cmd = EdgeCommand(
            edge_node_id=edge_node_id,
            command_type=data.command_type,
            target=data.target,
            params_json=data.params,
            status="pending",
        )
        session.add(cmd)
        session.commit()
        session.refresh(cmd)

        return {
            "command_id": str(cmd.id),
            "edge_node_id": cmd.edge_node_id,
            "command_type": cmd.command_type,
            "target": cmd.target,
            "status": cmd.status,
            "created_at": cmd.created_at.isoformat() if cmd.created_at else None,
        }


@router.get("/edge-nodes/{edge_node_id}/commands/pending")
def get_pending_commands(edge_node_id: str):
    """Poll for pending commands (Edge pulls this)."""
    with get_session() as session:
        cmds = session.query(EdgeCommand).filter_by(
            edge_node_id=edge_node_id, status="pending"
        ).order_by(EdgeCommand.created_at.asc()).all()

        results = []
        for cmd in cmds:
            # Atomically mark as executing
            cmd.status = "executing"
            cmd.started_at = datetime.now(timezone.utc)
            results.append({
                "command_id": str(cmd.id),
                "command_type": cmd.command_type,
                "target": cmd.target,
                "params": cmd.params_json,
                "created_at": cmd.created_at.isoformat() if cmd.created_at else None,
            })
        session.commit()
        return results


@router.post("/edge-nodes/{edge_node_id}/commands/{cmd_id}/result")
def report_command_result(edge_node_id: str, cmd_id: str, data: CommandResultRequest):
    """Report command execution result from edge."""
    from uuid import UUID
    with get_session() as session:
        cmd = session.query(EdgeCommand).filter_by(
            id=UUID(cmd_id), edge_node_id=edge_node_id
        ).first()
        if not cmd:
            raise HTTPException(status_code=404, detail="Command not found")

        cmd.status = data.status
        cmd.result_message = data.result_message
        cmd.finished_at = datetime.now(timezone.utc)
        session.commit()
        return {"status": "ok"}


@router.get("/edge-nodes/{edge_node_id}/commands")
def list_edge_commands(edge_node_id: str, limit: int = 100):
    """List command history for an edge node."""
    with get_session() as session:
        cmds = session.query(EdgeCommand).filter_by(
            edge_node_id=edge_node_id
        ).order_by(EdgeCommand.created_at.desc()).limit(limit).all()
        return [
            {
                "command_id": str(c.id),
                "command_type": c.command_type,
                "target": c.target,
                "status": c.status,
                "result_message": c.result_message,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "started_at": c.started_at.isoformat() if c.started_at else None,
                "finished_at": c.finished_at.isoformat() if c.finished_at else None,
            }
            for c in cmds
        ]


@router.get("/edge/commands/allowed")
def list_allowed_commands():
    """Return list of allowed command types."""
    return [
        {"type": k, "description": v["description"], "requires_target": v["requires_target"]}
        for k, v in ALLOWED_COMMANDS.items()
    ]


# ---- Sync Manifest -----------------------------------------------------------

@router.get("/edge/sync/manifest")
def get_sync_manifest():
    """Return full asset + signal manifest for edge nodes to sync."""
    manifest = build_sync_manifest()
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["version"] = "1.0"
    return manifest
