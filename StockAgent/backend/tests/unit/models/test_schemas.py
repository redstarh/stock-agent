"""T-B2: Pydantic 스키마 테스트"""

import pytest
from pydantic import ValidationError


def test_trade_log_schema_validation():
    """TradeLogResponse 정상 생성"""
    from src.models.schemas import TradeLogResponse

    data = TradeLogResponse(
        trade_id="test-uuid",
        date="2026-01-01",
        stock_code="005930",
        stock_name="삼성전자",
        side="buy",
        entry_price=70000,
        exit_price=71000,
        quantity=10,
        pnl=10000,
        pnl_pct=1.43,
        strategy_tag="volume_leader",
    )
    assert data.pnl == 10000
    assert data.stock_code == "005930"


def test_trade_log_schema_rejects_invalid():
    """유효하지 않은 데이터 거부"""
    from src.models.schemas import TradeLogResponse

    with pytest.raises(ValidationError):
        TradeLogResponse(
            trade_id="",
            date="invalid-date",
            stock_code="",
            entry_price=-1,
        )


def test_position_schema():
    """PositionResponse 정상 생성"""
    from src.models.schemas import PositionResponse

    pos = PositionResponse(
        stock_code="005930",
        stock_name="삼성전자",
        quantity=10,
        avg_price=70000,
        current_price=71000,
        unrealized_pnl=10000,
    )
    assert pos.quantity == 10


def test_account_balance_schema():
    """AccountBalanceResponse 정상 생성"""
    from src.models.schemas import AccountBalanceResponse

    bal = AccountBalanceResponse(
        cash=10000000,
        total_eval=15000000,
        daily_pnl=250000,
    )
    assert bal.cash == 10000000


def test_order_schema():
    """OrderResponse 정상 생성"""
    from src.models.schemas import OrderResponse

    order = OrderResponse(
        order_id="order-uuid",
        stock_code="005930",
        side="buy",
        order_type="limit",
        quantity=10,
        price=70000,
        status="pending",
    )
    assert order.status == "pending"
