"""Add ml_model registry table.

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-02-20 13:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6g7h8"
down_revision = "b2c3d4e5f6g7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ml_model",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(20), nullable=False),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("market", sa.String(5), nullable=False),
        sa.Column("feature_tier", sa.Integer(), nullable=False),
        sa.Column("feature_list", sa.Text(), nullable=False),
        sa.Column("train_accuracy", sa.Float(), nullable=True),
        sa.Column("test_accuracy", sa.Float(), nullable=True),
        sa.Column("cv_accuracy", sa.Float(), nullable=True),
        sa.Column("cv_std", sa.Float(), nullable=True),
        sa.Column("train_samples", sa.Integer(), nullable=True),
        sa.Column("test_samples", sa.Integer(), nullable=True),
        sa.Column("train_start_date", sa.Date(), nullable=True),
        sa.Column("train_end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("model_path", sa.String(500), nullable=True),
        sa.Column("model_checksum", sa.String(64), nullable=True),
        sa.Column("hyperparameters", sa.Text(), nullable=True),
        sa.Column("feature_importances", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ml_model_active", "ml_model", ["is_active", "market"])
    op.create_index("ix_ml_model_name_version", "ml_model", ["model_name", "model_version", "market"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_ml_model_name_version", "ml_model")
    op.drop_index("ix_ml_model_active", "ml_model")
    op.drop_table("ml_model")
