"""initial_metadata_tables

Revision ID: 001
Revises:
Create Date: 2026-06-30 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # plants
    op.create_table(
        "plants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plant_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plant_id"),
    )
    op.create_index(op.f("ix_plants_plant_id"), "plants", ["plant_id"])

    # areas
    op.create_table(
        "areas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("area_id", sa.String(64), nullable=False),
        sa.Column("plant_id_fk", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("area_type", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("area_id"),
        sa.ForeignKeyConstraint(["plant_id_fk"], ["plants.id"]),
    )
    op.create_index(op.f("ix_areas_area_id"), "areas", ["area_id"])

    # assets
    op.create_table(
        "assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.String(128), nullable=False),
        sa.Column("asset_code", sa.String(128), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("asset_type", sa.String(64), nullable=False),
        sa.Column("area_id_fk", sa.Uuid(), nullable=True),
        sa.Column("parent_asset_id_fk", sa.Uuid(), nullable=True),
        sa.Column("criticality", sa.String(32), nullable=False),
        sa.Column("lifecycle_status", sa.String(32), nullable=False),
        sa.Column("location_lat", sa.Float(), nullable=True),
        sa.Column("location_lng", sa.Float(), nullable=True),
        sa.Column("manufacturer", sa.String(255), nullable=True),
        sa.Column("model", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id"),
        sa.ForeignKeyConstraint(["area_id_fk"], ["areas.id"]),
        sa.ForeignKeyConstraint(["parent_asset_id_fk"], ["assets.id"]),
    )
    op.create_index(op.f("ix_assets_asset_id"), "assets", ["asset_id"])

    # signals
    op.create_table(
        "signals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("signal_id", sa.String(256), nullable=False),
        sa.Column("asset_id_fk", sa.Uuid(), nullable=False),
        sa.Column("signal_name", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("signal_type", sa.String(32), nullable=False),
        sa.Column("data_type", sa.String(32), nullable=False),
        sa.Column("engineering_unit", sa.String(64), nullable=True),
        sa.Column("min_value", sa.Float(), nullable=True),
        sa.Column("max_value", sa.Float(), nullable=True),
        sa.Column("uns_path", sa.String(512), nullable=True),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("source_ref", sa.String(512), nullable=True),
        sa.Column("quality_policy", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("signal_id"),
        sa.ForeignKeyConstraint(["asset_id_fk"], ["assets.id"]),
    )
    op.create_index(op.f("ix_signals_signal_id"), "signals", ["signal_id"])

    # edge_nodes
    op.create_table(
        "edge_nodes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("edge_node_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("node_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("edge_node_id"),
    )
    op.create_index(op.f("ix_edge_nodes_edge_node_id"), "edge_nodes", ["edge_node_id"])


def downgrade() -> None:
    op.drop_table("edge_nodes")
    op.drop_table("signals")
    op.drop_table("assets")
    op.drop_table("areas")
    op.drop_table("plants")
