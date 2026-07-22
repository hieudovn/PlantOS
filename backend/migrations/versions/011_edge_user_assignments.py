"""edge_user_assignments

Revision ID: 010
Revises: 009
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "edge_user_assignments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("edge_node_id", sa.String(128), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_eua_edge_node", "edge_user_assignments", ["edge_node_id"])
    op.create_index("ix_eua_user", "edge_user_assignments", ["user_id"])
    op.create_unique_constraint("uq_eua_edge_user", "edge_user_assignments",
                                ["edge_node_id", "user_id"])

    # Seed: assign all 3 default users to EDGEV2-PC-01
    op.execute("""
        INSERT INTO edge_user_assignments (id, edge_node_id, user_id)
        SELECT gen_random_uuid(), 'EDGEV2-PC-01', id FROM users
    """)


def downgrade() -> None:
    op.drop_table("edge_user_assignments")
