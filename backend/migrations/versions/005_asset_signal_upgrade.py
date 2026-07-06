"""asset_signal_upgrade_v2

Revision ID: 005
Revises: 004
Create Date: 2026-07-06 00:00:00.000000

Adds:
  - assets.asset_role (string)
  - signals.signal_category (string)
  - signals.external_refs (jsonb)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- assets ----
    op.add_column("assets", sa.Column("asset_role", sa.String(32), nullable=True))

    # Backfill asset_role from asset_type
    op.execute("""
        UPDATE assets SET asset_role = 'functional_location'
        WHERE asset_type IN ('production_line', 'work_cell', 'equipment_group')
        AND asset_role IS NULL
    """)
    op.execute("""
        UPDATE assets SET asset_role = 'subsystem'
        WHERE asset_type IN ('bearing_assembly', 'seal_system', 'lubrication_system', 'cooling_system')
        AND asset_role IS NULL
    """)
    op.execute("""
        UPDATE assets SET asset_role = 'equipment'
        WHERE asset_role IS NULL
    """)

    # Make NOT NULL after backfill
    op.alter_column("assets", "asset_role", nullable=False, server_default="equipment")

    # ---- signals ----
    op.add_column("signals", sa.Column("signal_category", sa.String(32), nullable=True))

    # Backfill signal_category from signal_type
    op.execute("""
        UPDATE signals SET signal_category = signal_type
        WHERE signal_category IS NULL
    """)
    op.execute("""
        UPDATE signals SET signal_category = 'measurement'
        WHERE signal_category IS NULL
    """)

    op.alter_column("signals", "signal_category", nullable=False, server_default="measurement")

    # external_refs as JSONB for opaque metadata
    op.add_column(
        "signals",
        sa.Column("external_refs", sa.JSON(), nullable=True, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("signals", "external_refs")
    op.drop_column("signals", "signal_category")
    op.drop_column("assets", "asset_role")
