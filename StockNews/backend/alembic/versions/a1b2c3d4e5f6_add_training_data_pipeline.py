"""Add training data pipeline tables and OHLCV columns.

Revision ID: a1b2c3d4e5f6
Revises: 9f69148009e7
Create Date: 2026-02-19

"""
from alembic import op
from sqlalchemy import inspect, text
import sqlalchemy as sa

# revision identifiers
revision = "a1b2c3d4e5f6"
down_revision = "9f69148009e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)

    # Add OHLCV columns to daily_prediction_result (skip if already exists)
    existing_cols = {c["name"] for c in insp.get_columns("daily_prediction_result")}
    new_columns = [
        ("actual_open_price", sa.Float()),
        ("actual_high_price", sa.Float()),
        ("actual_low_price", sa.Float()),
        ("actual_volume", sa.Integer()),
        ("previous_volume", sa.Integer()),
        ("actual_trading_value", sa.Float()),
    ]
    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            with op.batch_alter_table("daily_prediction_result") as batch_op:
                batch_op.add_column(sa.Column(col_name, col_type, nullable=True))

    # Create stock_training_data table (skip if already exists)
    if "stock_training_data" not in insp.get_table_names():
        op.create_table(
            "stock_training_data",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("prediction_date", sa.Date(), nullable=False),
            sa.Column("stock_code", sa.String(length=20), nullable=False),
            sa.Column("stock_name", sa.String(length=100), nullable=True),
            sa.Column("market", sa.String(length=5), nullable=False),
            sa.Column("news_score", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("sentiment_score", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("news_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("news_count_3d", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("avg_score_3d", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("disclosure_ratio", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("sentiment_trend", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("theme", sa.String(length=50), nullable=True),
            sa.Column("prev_close", sa.Float(), nullable=True),
            sa.Column("prev_change_pct", sa.Float(), nullable=True),
            sa.Column("prev_volume", sa.Integer(), nullable=True),
            sa.Column("price_change_5d", sa.Float(), nullable=True),
            sa.Column("volume_change_5d", sa.Float(), nullable=True),
            sa.Column("ma5_ratio", sa.Float(), nullable=True),
            sa.Column("ma20_ratio", sa.Float(), nullable=True),
            sa.Column("volatility_5d", sa.Float(), nullable=True),
            sa.Column("rsi_14", sa.Float(), nullable=True),
            sa.Column("bb_position", sa.Float(), nullable=True),
            sa.Column("market_index_change", sa.Float(), nullable=True),
            sa.Column("day_of_week", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("predicted_direction", sa.String(length=10), nullable=False),
            sa.Column("predicted_score", sa.Float(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("actual_close", sa.Float(), nullable=True),
            sa.Column("actual_change_pct", sa.Float(), nullable=True),
            sa.Column("actual_direction", sa.String(length=10), nullable=True),
            sa.Column("actual_volume", sa.Integer(), nullable=True),
            sa.Column("is_correct", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # Indexes (skip if already exists)
    existing_indexes = {idx["name"] for idx in insp.get_indexes("stock_training_data")}
    index_defs = [
        ("ix_stock_training_data_prediction_date", ["prediction_date"], False),
        ("ix_stock_training_data_stock_code", ["stock_code"], False),
        ("ix_stock_training_data_market", ["market"], False),
        ("idx_training_date_stock", ["prediction_date", "stock_code"], True),
        ("idx_training_market_date", ["market", "prediction_date"], False),
    ]
    for idx_name, columns, unique in index_defs:
        if idx_name not in existing_indexes:
            op.create_index(idx_name, "stock_training_data", columns, unique=unique)


def downgrade() -> None:
    op.drop_table("stock_training_data")

    with op.batch_alter_table("daily_prediction_result") as batch_op:
        batch_op.drop_column("actual_trading_value")
        batch_op.drop_column("previous_volume")
        batch_op.drop_column("actual_volume")
        batch_op.drop_column("actual_low_price")
        batch_op.drop_column("actual_high_price")
        batch_op.drop_column("actual_open_price")
