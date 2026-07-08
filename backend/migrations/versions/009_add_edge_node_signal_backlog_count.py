"""add_edge_node_signal_backlog_count

Revision ID: 009
Revises: 008
Create Date: 2026-07-08 00:00:00.000000

Adds nullable columns to edge_nodes table:
  - signal_count (INTEGER, default 0)
  - backlog_count (INTEGER, default 0)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("edge_nodes", sa.Column("signal_count", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("edge_nodes", sa.Column("backlog_count", sa.Integer(), nullable=True, server_default="0"))


def downgrade() -> None:
    op.drop_column("edge_nodes", "backlog_count")
    op.drop_column("edge_nodes", "signal_count")
