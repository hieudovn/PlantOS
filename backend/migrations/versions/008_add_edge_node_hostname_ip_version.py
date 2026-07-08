"""add_edge_node_hostname_ip_version

Revision ID: 008
Revises: 007
Create Date: 2026-07-08 00:00:00.000000

Adds nullable columns to edge_nodes table:
  - hostname (VARCHAR 255)
  - ip_address (VARCHAR 45)
  - edge_version (VARCHAR 32)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("edge_nodes", sa.Column("hostname", sa.String(255), nullable=True))
    op.add_column("edge_nodes", sa.Column("ip_address", sa.String(45), nullable=True))
    op.add_column("edge_nodes", sa.Column("edge_version", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("edge_nodes", "edge_version")
    op.drop_column("edge_nodes", "ip_address")
    op.drop_column("edge_nodes", "hostname")
