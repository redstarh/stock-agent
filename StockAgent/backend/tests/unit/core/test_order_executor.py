"""B-15: Order Executor 고도화 테스트 (분할매수, 재시도, 슬리피지)"""

import pytest
from unittest.mock import AsyncMock
from src.core.order_executor import OrderExecutor


@pytest.fixture
def mock_order():
    """Mock KiwoomOrder client"""
    order = AsyncMock()
    order.buy = AsyncMock(return_value={"status": "submitted", "order_id": "ORD001", "order_time": "090100"})
    order.sell = AsyncMock(return_value={"status": "submitted", "order_id": "ORD002", "order_time": "090200"})
    return order


@pytest.fixture
def executor(mock_order):
    """OrderExecutor with default config"""
    return OrderExecutor(order_client=mock_order, split_size=20, max_retries=3, max_slippage_pct=0.005)


@pytest.mark.asyncio
async def test_split_order(executor):
    """분할 매수 (총 100주를 20주씩)"""
    results = await executor.execute_split_buy("005930", qty=100, price=70000)
    assert len(results) == 5
    for r in results:
        assert r["status"] == "submitted"


@pytest.mark.asyncio
async def test_split_order_remainder(executor):
    """분할 매수 나머지 처리 (90주를 20주씩 → 4+10)"""
    results = await executor.execute_split_buy("005930", qty=90, price=70000)
    assert len(results) == 5  # 20+20+20+20+10


@pytest.mark.asyncio
async def test_retry_on_failure(mock_order):
    """주문 실패 시 재시도"""
    mock_order.buy = AsyncMock(side_effect=[
        {"status": "failed", "message": "server error"},
        {"status": "submitted", "order_id": "ORD001", "order_time": "090100"},
    ])
    executor = OrderExecutor(order_client=mock_order, max_retries=3)
    result = await executor.execute_buy("005930", qty=10, price=70000)
    assert result["order_id"] == "ORD001"
    assert mock_order.buy.call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted(mock_order):
    """재시도 모두 소진"""
    mock_order.buy = AsyncMock(return_value={"status": "failed", "message": "error"})
    executor = OrderExecutor(order_client=mock_order, max_retries=2)
    result = await executor.execute_buy("005930", qty=10, price=70000)
    assert result["status"] == "failed"
    assert mock_order.buy.call_count == 2


@pytest.mark.asyncio
async def test_slippage_protection(mock_order):
    """슬리피지 한도 초과 시 주문 취소"""
    executor = OrderExecutor(order_client=mock_order, max_slippage_pct=0.005)
    result = await executor.execute_buy("005930", qty=10, price=70000, market_price=70500)
    assert result["status"] == "cancelled_slippage"
    mock_order.buy.assert_not_called()


@pytest.mark.asyncio
async def test_slippage_within_limit(executor):
    """슬리피지 범위 내 주문 실행"""
    result = await executor.execute_buy("005930", qty=10, price=70000, market_price=70030)
    assert result["status"] == "submitted"


@pytest.mark.asyncio
async def test_sell_order_success(executor):
    """매도 주문 성공"""
    result = await executor.execute_sell("005930", qty=10, price=70000)
    assert result["status"] == "submitted"
    assert result["order_id"] == "ORD002"


@pytest.mark.asyncio
async def test_sell_with_slippage_protection(mock_order):
    """매도 시 슬리피지 보호"""
    executor = OrderExecutor(order_client=mock_order, max_slippage_pct=0.005)
    result = await executor.execute_sell("005930", qty=10, price=70000, market_price=69500)
    assert result["status"] == "cancelled_slippage"
    mock_order.sell.assert_not_called()


@pytest.mark.asyncio
async def test_sell_retry_on_failure(mock_order):
    """매도 실패 시 재시도"""
    mock_order.sell = AsyncMock(side_effect=[
        {"status": "failed", "message": "network error"},
        {"status": "submitted", "order_id": "ORD003", "order_time": "090300"},
    ])
    executor = OrderExecutor(order_client=mock_order, max_retries=3)
    result = await executor.execute_sell("005930", qty=10, price=70000)
    assert result["order_id"] == "ORD003"
    assert mock_order.sell.call_count == 2
