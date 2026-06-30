"""event_tables

Revision ID: 003
Revises: 002
Create Date: 2026-06-30 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # state_events
    op.create_table(
        "state_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.String(128), nullable=False),
        sa.Column("asset_id", sa.String(128), nullable=False),
        sa.Column("signal_id", sa.String(256), nullable=True),
        sa.Column("previous_state", sa.String(64), nullable=True),
        sa.Column("current_state", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index(op.f("ix_state_events_event_id"), "state_events", ["event_id"])
    op.create_index(op.f("ix_state_events_asset_id"), "state_events", ["asset_id"])

    # downtime_events
    op.create_table(
        "downtime_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.String(128), nullable=False),
        sa.Column("asset_id", sa.String(128), nullable=False),
        sa.Column("downtime_type", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index(op.f("ix_downtime_events_event_id"), "downtime_events", ["event_id"])
    op.create_index(op.f("ix_downtime_events_asset_id"), "downtime_events", ["asset_id"])

    # production_events
    op.create_table(
        "production_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.String(128), nullable=False),
        sa.Column("asset_id", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(64), nullable=True),
        sa.Column("batch_id", sa.String(128), nullable=True),
        sa.Column("product", sa.String(255), nullable=True),
        sa.Column("is_quality_good", sa.Boolean(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index(op.f("ix_production_events_event_id"), "production_events", ["event_id"])
    op.create_index(op.f("ix_production_events_asset_id"), "production_events", ["asset_id"])


def downgrade() -> None:
    op.drop_table("production_events")
    op.drop_table("downtime_events")
    op.drop_table("state_events")
