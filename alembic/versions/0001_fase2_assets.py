"""fase 2: assets, asset_identifiers, users, favorites

Revision ID: 0001_fase2_assets
Revises:
Create Date: 2026-08-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_fase2_assets"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


asset_type_enum = sa.Enum("stock", "etf", "fund", name="assettype")


def upgrade() -> None:
    asset_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("asset_type", asset_type_enum, nullable=False),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column("ticker", sa.String(length=20), nullable=True),
        sa.Column("exchange", sa.String(length=50), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("featured_order", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("isin", name="uq_assets_isin"),
    )
    op.create_index("ix_assets_name", "assets", ["name"])
    op.create_index("ix_assets_asset_type", "assets", ["asset_type"])
    op.create_index("ix_assets_isin", "assets", ["isin"])
    op.create_index("ix_assets_ticker", "assets", ["ticker"])
    op.create_index("ix_assets_is_featured", "assets", ["is_featured"])

    op.create_table(
        "asset_identifiers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "asset_id",
            sa.Integer(),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_symbol", sa.String(length=50), nullable=False),
        sa.UniqueConstraint("asset_id", "provider", name="uq_asset_provider"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "asset_id", sa.Integer(), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
        ),
        sa.UniqueConstraint("user_id", "asset_id", name="uq_user_asset_favorite"),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
    op.create_index("ix_favorites_asset_id", "favorites", ["asset_id"])


def downgrade() -> None:
    op.drop_table("favorites")
    op.drop_table("users")
    op.drop_table("asset_identifiers")
    op.drop_table("assets")
    asset_type_enum.drop(op.get_bind(), checkfirst=True)
