"""Edge Node Registry — SQLAlchemy model for EdgeNode."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f"<EdgeNode {self.edge_node_id}>"
