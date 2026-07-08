"""calculated_signals_and_kpis

Revision ID: 007
Revises: 006
Create Date: 2026-07-08 00:00:00.000000

Adds:
  - calculated_signals table
  - kpi_definitions table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calculated_signals",
        sa.Column("calc_signal_id", sa.String(128), primary_key=True),
        sa.Column("asset_id", sa.String(128), sa.ForeignKey("assets.asset_id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("formula", sa.Text(), nullable=False),
        sa.Column("formula_meta_json", sa.JSON(), nullable=True, server_default="{}"),
        sa.Column("inputs_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("output_signal_id", sa.String(256), nullable=True),
        sa.Column("output_unit", sa.String(64), nullable=True),
        sa.Column("execution_mode", sa.String(32), nullable=True, server_default="manual"),
        sa.Column("schedule_interval", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), nullable=True, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=True, server_default="1"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_status", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "kpi_definitions",
        sa.Column("kpi_id", sa.String(128), primary_key=True),
        sa.Column("scope_type", sa.String(32), nullable=False),
        sa.Column("scope_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("kpi_category", sa.String(32), nullable=True, server_default="operation"),
        sa.Column("formula", sa.Text(), nullable=False),
        sa.Column("formula_meta_json", sa.JSON(), nullable=True, server_default="{}"),
        sa.Column("inputs_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("unit", sa.String(64), nullable=True),
        sa.Column("aggregation_window", sa.String(32), nullable=True),
        sa.Column("target", sa.Float(), nullable=True),
        sa.Column("warning_limit", sa.Float(), nullable=True),
        sa.Column("critical_limit", sa.Float(), nullable=True),
        sa.Column("display_priority", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("show_in_process_view", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("status", sa.String(32), nullable=True, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=True, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("kpi_definitions")
    op.drop_table("calculated_signals")
