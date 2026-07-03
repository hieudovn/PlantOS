"""users_table

Revision ID: 004
Revises: 003
Create Date: 2026-07-03 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="operator"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"])

    # Seed 3 default users (passwords: PlantOS@2026!)
    op.execute(
        "INSERT INTO users (id, username, password_hash, display_name, role) VALUES "
        "(gen_random_uuid(), 'admin', '$2b$12$HJXc8NpIHObx5vbmcF2VHubD4aNzWVFunOz8US9rEi9ZUckEGgseG', 'Administrator', 'admin'),"
        "(gen_random_uuid(), 'engineer', '$2b$12$5ju68S5JJDoYDn1.QmtiS.VzLmVSyJqgnVnuHtR0a9OOQtyp2PGuK', 'Engineer', 'engineer'),"
        "(gen_random_uuid(), 'operator', '$2b$12$DlEKJmrAXfVvGDB5f70V9.8giqvN5zE0AZfIszn0Arq1ScA8dQbu2', 'Operator', 'operator')"
    )


def downgrade() -> None:
    op.drop_table("users")
