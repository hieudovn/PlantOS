"""asset_templates_and_bindings

Revision ID: 006
Revises: 005
Create Date: 2026-07-08 00:00:00.000000

Adds:
  - asset_templates table
  - asset_attribute_bindings table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- asset_templates ----
    op.create_table(
        "asset_templates",
        sa.Column("template_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("asset_type", sa.String(64), nullable=False),
        sa.Column("asset_role", sa.String(32), nullable=False, server_default="equipment"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("attributes_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("domain_type", sa.String(32), nullable=True, server_default="generic"),
        sa.Column("metadata_json", sa.JSON(), nullable=True, server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ---- asset_attribute_bindings ----
    op.create_table(
        "asset_attribute_bindings",
        sa.Column("binding_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("asset_id", sa.String(128), sa.ForeignKey("assets.asset_id", ondelete="CASCADE"), nullable=False),
        sa.Column("template_id", sa.String(64), sa.ForeignKey("asset_templates.template_id"), nullable=True),
        sa.Column("attribute_name", sa.String(128), nullable=False),
        sa.Column("signal_id", sa.String(256), sa.ForeignKey("signals.signal_id", ondelete="SET NULL"), nullable=True),
        sa.Column("binding_type", sa.String(32), nullable=False, server_default="direct"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("validation_status", sa.String(32), nullable=True),
        sa.Column("validation_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("binding_id"),
        sa.UniqueConstraint("asset_id", "attribute_name"),
    )

    op.create_index("idx_bindings_asset", "asset_attribute_bindings", ["asset_id"])
    op.create_index("idx_bindings_signal", "asset_attribute_bindings", ["signal_id"])


def downgrade() -> None:
    op.drop_table("asset_attribute_bindings")
    op.drop_table("asset_templates")
