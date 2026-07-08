"""Edge Node Registry — SQLAlchemy models for Edge v2."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return uuid.uuid4()


class EdgeNode(Base):
    __tablename__ = "edge_nodes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    edge_node_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    node_type: Mapped[str] = mapped_column(String(64), default="simulator")
    status: Mapped[str] = mapped_column(String(32), default="offline")
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, default=None)
    edge_version: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    signal_count: Mapped[int] = mapped_column(Integer, default=0)
    backlog_count: Mapped[int] = mapped_column(Integer, default=0)
    capabilities: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)
    workspace_id: Mapped[str | None] = mapped_column(String(128), nullable=True, default=None)
    center_sync: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    disk_usage_mb: Mapped[float | None] = mapped_column(Integer, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    heartbeats = relationship("EdgeHeartbeat", back_populates="edge_node", lazy="dynamic")
    connectors = relationship("EdgeConnector", back_populates="edge_node", lazy="dynamic")
    commands = relationship("EdgeCommand", back_populates="edge_node", lazy="dynamic")
    config_versions = relationship("EdgeConfigVersion", back_populates="edge_node", lazy="dynamic")

    def __repr__(self):
        return f"<EdgeNode {self.edge_node_id}>"


class EdgeHeartbeat(Base):
    __tablename__ = "edge_heartbeats"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    edge_node_id: Mapped[str] = mapped_column(String(128), ForeignKey("edge_nodes.edge_node_id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="online")
    backlog_count: Mapped[int] = mapped_column(Integer, default=0)
    signal_count: Mapped[int] = mapped_column(Integer, default=0)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    edge_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    center_sync: Mapped[str | None] = mapped_column(String(32), nullable=True)
    disk_usage_mb: Mapped[float | None] = mapped_column(Integer, nullable=True)
    connectors_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    edge_node = relationship("EdgeNode", back_populates="heartbeats")


class EdgeConnector(Base):
    __tablename__ = "edge_connectors"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    edge_node_id: Mapped[str] = mapped_column(String(128), ForeignKey("edge_nodes.edge_node_id"), nullable=False, index=True)
    connector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="stopped")
    signal_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    edge_node = relationship("EdgeNode", back_populates="connectors")

    __table_args__ = (
        UniqueConstraint("edge_node_id", "connector_id", name="uq_edge_node_connector"),
    )


class EdgeCommand(Base):
    __tablename__ = "edge_commands"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    edge_node_id: Mapped[str] = mapped_column(String(128), ForeignKey("edge_nodes.edge_node_id"), nullable=False, index=True)
    command_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target: Mapped[str | None] = mapped_column(String(128), nullable=True)
    params_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, executing, success, failed
    result_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    edge_node = relationship("EdgeNode", back_populates="commands")


class EdgeConfigVersion(Base):
    __tablename__ = "edge_config_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    edge_node_id: Mapped[str] = mapped_column(String(128), ForeignKey("edge_nodes.edge_node_id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    config_hash: Mapped[str] = mapped_column(String(64), default="")
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    status: Mapped[str] = mapped_column(String(32), default="applied")

    edge_node = relationship("EdgeNode", back_populates="config_versions")
