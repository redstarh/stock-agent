"""Add Tier 3 columns (foreign_net_ratio, sector_index_change).

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-02-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e5f6g7h8i9j0"
down_revision = "d4e5f6g7h8i9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("stock_training_data", sa.Column("foreign_net_ratio", sa.Float(), nullable=True))
    op.add_column("stock_training_data", sa.Column("sector_index_change", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("stock_training_data", "sector_index_change")
    op.drop_column("stock_training_data", "foreign_net_ratio")
