"""fase 3: asset_prices, data_sources, data_quality_logs

Revision ID: 0002_fase3_prices
Revises: 0001_fase2_assets
Create Date: 2026-08-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_fase3_prices"
down_revision: Union[str, None] = "0001_fase2_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

issue_type_enum = sa.Enum(
    "null_value",
    "negative_price",
    "absurd_change",
    "duplicate_date",
    "stale_data",
    "source_mismatch",
    "provider_unavailable",
    name="dataqualityissuetype",
)


def upgrade() -> None:
    issue_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "asset_prices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "asset_id", sa.Integer(), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(18, 6), nullable=True),
        sa.Column("high", sa.Numeric(18, 6), nullable=True),
        sa.Column("low", sa.Numeric(18, 6), nullable=True),
        sa.Column("close", sa.Numeric(18, 6), nullable=False),
        sa.Column("adjusted_close", sa.Numeric(18, 6), nullable=True),
        sa.Column("volume", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("asset_id", "date", name="uq_asset_date"),
    )
    op.create_index("ix_asset_prices_asset_id", "asset_prices", ["asset_id"])
    op.create_index("ix_asset_prices_date", "asset_prices", ["date"])

    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_detail", sa.Text(), nullable=True),
        sa.UniqueConstraint("name", name="uq_data_sources_name"),
    )

    op.create_table(
        "data_quality_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "asset_id", sa.Integer(), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=True
        ),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("issue_type", issue_type_enum, nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_data_quality_logs_asset_id", "data_quality_logs", ["asset_id"])

    op.bulk_insert(
        sa.table(
            "data_sources",
            sa.column("name", sa.String),
            sa.column("priority", sa.Integer),
            sa.column("is_active", sa.Boolean),
        ),
        [
            {"name": "yahoo_finance", "priority": 1, "is_active": True},
            {"name": "stooq", "priority": 2, "is_active": True},
        ],
    )


def downgrade() -> None:
    op.drop_table("data_quality_logs")
    op.drop_table("data_sources")
    op.drop_table("asset_prices")
    issue_type_enum.drop(op.get_bind(), checkfirst=True)
