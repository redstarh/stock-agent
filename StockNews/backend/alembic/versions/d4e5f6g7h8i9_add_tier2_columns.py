"""Add Tier 2 columns: usd_krw_change, has_earnings_disclosure, cross_theme_score.

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-02-20 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "d4e5f6g7h8i9"
down_revision = "c3d4e5f6g7h8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("stock_training_data", sa.Column("usd_krw_change", sa.Float(), nullable=True))
    op.add_column("stock_training_data", sa.Column("has_earnings_disclosure", sa.Boolean(), nullable=True, server_default="0"))
    op.add_column("stock_training_data", sa.Column("cross_theme_score", sa.Float(), nullable=True, server_default="0"))


def downgrade() -> None:
    op.drop_column("stock_training_data", "cross_theme_score")
    op.drop_column("stock_training_data", "has_earnings_disclosure")
    op.drop_column("stock_training_data", "usd_krw_change")
