"""alarm_tables

Revision ID: 002
Revises: 001
Create Date: 2026-06-30 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # alarm_rules
    op.create_table(
        "alarm_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rule_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_type", sa.String(32), nullable=False),
        sa.Column("signal_id", sa.String(256), nullable=False),
        sa.Column("asset_id", sa.String(128), nullable=True),
        sa.Column("condition", sa.String(8), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("hysteresis", sa.Float(), nullable=False),
        sa.Column("delay_seconds", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("message_template", sa.Text(), nullable=True),
        sa.Column("auto_clear", sa.Boolean(), nullable=False),
        sa.Column("clear_threshold", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_id"),
    )
    op.create_index(op.f("ix_alarm_rules_rule_id"), "alarm_rules", ["rule_id"])

    # alarm_events
    op.create_table(
        "alarm_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("alarm_id", sa.String(64), nullable=False),
        sa.Column("rule_id_fk", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.String(128), nullable=True),
        sa.Column("signal_id", sa.String(256), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("trigger_value", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alarm_id"),
        sa.ForeignKeyConstraint(["rule_id_fk"], ["alarm_rules.id"]),
    )
    op.create_index(op.f("ix_alarm_events_alarm_id"), "alarm_events", ["alarm_id"])


def downgrade() -> None:
    op.drop_table("alarm_events")
    op.drop_table("alarm_rules")
