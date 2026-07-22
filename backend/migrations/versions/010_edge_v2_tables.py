"""edge_v2_tables — heartbeat history, connectors, commands, config versions

Revision ID: 010
Revises: 009
Create Date: 2026-07-08 00:00:00.000000

Adds:
  - edge_heartbeats — heartbeat history log
  - edge_connectors — per-connector status
  - edge_commands — command queue (pull-based)
  - edge_config_versions — config version history
  - EdgeNode columns: capabilities (JSONB), workspace_id, center_sync, disk_usage_mb
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to edge_nodes
    op.add_column("edge_nodes", sa.Column("capabilities", sa.JSON(), nullable=True))
    op.add_column("edge_nodes", sa.Column("workspace_id", sa.String(128), nullable=True))
    op.add_column("edge_nodes", sa.Column("center_sync", sa.String(32), nullable=True))
    op.add_column("edge_nodes", sa.Column("disk_usage_mb", sa.Integer(), nullable=True))

    # edge_heartbeats
    op.create_table(
        "edge_heartbeats",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("edge_node_id", sa.String(128), sa.ForeignKey("edge_nodes.edge_node_id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="online"),
        sa.Column("backlog_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("signal_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hostname", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("edge_version", sa.String(32), nullable=True),
        sa.Column("center_sync", sa.String(32), nullable=True),
        sa.Column("disk_usage_mb", sa.Integer(), nullable=True),
        sa.Column("connectors_json", sa.JSON(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_edge_heartbeats_node_rcv", "edge_heartbeats", ["edge_node_id", "received_at"])
    op.create_index("ix_edge_heartbeats_received_at", "edge_heartbeats", ["received_at"])

    # edge_connectors
    op.create_table(
        "edge_connectors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("edge_node_id", sa.String(128), sa.ForeignKey("edge_nodes.edge_node_id"), nullable=False),
        sa.Column("connector_id", sa.String(128), nullable=False),
        sa.Column("connector_type", sa.String(64), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="stopped"),
        sa.Column("signal_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("edge_node_id", "connector_id", name="uq_edge_connector_per_node"),
    )
    op.create_index("ix_edge_connectors_node", "edge_connectors", ["edge_node_id"])

    # edge_commands
    op.create_table(
        "edge_commands",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("edge_node_id", sa.String(128), sa.ForeignKey("edge_nodes.edge_node_id"), nullable=False),
        sa.Column("command_type", sa.String(64), nullable=False),
        sa.Column("target", sa.String(128), nullable=True),
        sa.Column("params_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("result_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_edge_commands_node_status", "edge_commands", ["edge_node_id", "status"])
    op.create_index("ix_edge_commands_pending", "edge_commands", ["status"])

    # edge_config_versions
    op.create_table(
        "edge_config_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("edge_node_id", sa.String(128), sa.ForeignKey("edge_nodes.edge_node_id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("config_hash", sa.String(64), nullable=False, server_default=""),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="applied"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_edge_cfgver_node", "edge_config_versions", ["edge_node_id"])


def downgrade() -> None:
    op.drop_table("edge_config_versions")
    op.drop_table("edge_commands")
    op.drop_table("edge_connectors")
    op.drop_table("edge_heartbeats")
    op.drop_column("edge_nodes", "disk_usage_mb")
    op.drop_column("edge_nodes", "center_sync")
    op.drop_column("edge_nodes", "workspace_id")
    op.drop_column("edge_nodes", "capabilities")
