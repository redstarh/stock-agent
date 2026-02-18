"""T-B2: DB 스키마 + ORM 모델 테스트"""

import pytest
from datetime import date, datetime
from decimal import Decimal


def test_trade_log_model_fields():
    """trade_log 모델에 필수 필드가 존재하는지 확인"""
    from src.models.db_models import TradeLog

    columns = {c.name for c in TradeLog.__table__.columns}
    required = {
        "trade_id", "date", "stock_code", "stock_name", "side",
        "entry_time", "exit_time", "entry_price", "exit_price",
        "quantity", "pnl", "pnl_pct", "news_score", "volume_rank",
        "strategy_tag", "created_at",
    }
    assert required.issubset(columns)


def test_learning_metrics_model_fields():
    """learning_metrics 모델 필드 확인"""
    from src.models.db_models import LearningMetrics

    columns = {c.name for c in LearningMetrics.__table__.columns}
    required = {
        "id", "date", "total_trades", "win_count", "win_rate",
        "avg_return", "max_drawdown", "total_pnl",
        "best_pattern", "worst_pattern", "created_at",
    }
    assert required.issubset(columns)


def test_positions_model_fields():
    """positions 모델 필드 확인"""
    from src.models.db_models import Position

    columns = {c.name for c in Position.__table__.columns}
    required = {
        "id", "stock_code", "stock_name", "quantity", "avg_price",
        "current_price", "unrealized_pnl", "stop_loss_price",
        "entry_time", "updated_at",
    }
    assert required.issubset(columns)


def test_orders_model_fields():
    """orders 모델 필드 확인"""
    from src.models.db_models import Order

    columns = {c.name for c in Order.__table__.columns}
    required = {
        "order_id", "stock_code", "side", "order_type",
        "quantity", "price", "filled_quantity", "filled_price",
        "status", "kiwoom_order_id", "created_at", "updated_at",
    }
    assert required.issubset(columns)


def test_trade_log_table_name():
    """테이블명 확인"""
    from src.models.db_models import TradeLog

    assert TradeLog.__tablename__ == "trade_log"


def test_learning_metrics_date_unique():
    """learning_metrics.date는 unique 제약"""
    from src.models.db_models import LearningMetrics

    date_col = LearningMetrics.__table__.c.date
    assert date_col.unique is True
