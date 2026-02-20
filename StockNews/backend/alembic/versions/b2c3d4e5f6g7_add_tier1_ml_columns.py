"""Add Tier 1 ML columns: market_return, vix_change.

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-20 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6g7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("stock_training_data", sa.Column("market_return", sa.Float(), nullable=True))
    op.add_column("stock_training_data", sa.Column("vix_change", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("stock_training_data", "vix_change")
    op.drop_column("stock_training_data", "market_return")
