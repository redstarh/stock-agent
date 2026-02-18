"""B-8 자동매매 루프 프레임워크 테스트"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config import Settings
from src.core.trader import Trader


@pytest.fixture
def test_config():
    """테스트용 설정"""
    return Settings(
        KIWOOM_APP_KEY="test_key",
        KIWOOM_APP_SECRET="test_secret",
        KIWOOM_ACCOUNT_NO="12345678",
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test",
    )


@pytest.fixture
def mock_kiwoom():
    """키움 API 모킹"""
    mock = MagicMock()
    mock.buy = AsyncMock(return_value={"status": "submitted", "order_id": "ORD123"})
    mock.sell = AsyncMock(return_value={"status": "submitted", "order_id": "ORD124"})
    return mock


@pytest.mark.asyncio
async def test_trader_starts_and_stops(test_config):
    """매매 루프 시작/정지"""
    trader = Trader(config=test_config)

    # 초기 상태
    assert trader.is_running is False

    # 시작
    await trader.start()
    assert trader.is_running is True

    # 정지
    await trader.stop()
    assert trader.is_running is False


@pytest.mark.asyncio
async def test_trader_executes_cycle(test_config, mock_kiwoom):
    """매매 사이클 1회 실행"""
    trader = Trader(config=test_config)

    # 장 시간 내로 설정
    trader._now = lambda: datetime(2026, 2, 18, 10, 0)  # 10:00 AM

    result = await trader.run_cycle()

    # 결과 검증
    assert result is not None
    assert "status" in result
    assert result["status"] in ("executed", "no_signal", "skipped", "market_closed")


@pytest.mark.asyncio
async def test_trader_respects_market_hours(test_config):
    """장 외 시간에는 매매하지 않음"""
    trader = Trader(config=test_config)

    # 장 전 시간
    trader._now = lambda: datetime(2026, 2, 18, 7, 0)  # 07:00 AM
    result = await trader.run_cycle()
    assert result["status"] == "market_closed"

    # 장 후 시간
    trader._now = lambda: datetime(2026, 2, 18, 16, 0)  # 04:00 PM
    result = await trader.run_cycle()
    assert result["status"] == "market_closed"

    # 주말
    trader._now = lambda: datetime(2026, 2, 21, 10, 0)  # Saturday 10:00 AM
    result = await trader.run_cycle()
    assert result["status"] == "market_closed"


@pytest.mark.asyncio
async def test_trader_cycle_during_market_hours(test_config):
    """장 시간 내에는 매매 사이클 실행"""
    trader = Trader(config=test_config)

    # 장 시작 직후
    trader._now = lambda: datetime(2026, 2, 18, 9, 5)  # 09:05 AM
    result = await trader.run_cycle()
    assert result["status"] != "market_closed"

    # 장 중반
    trader._now = lambda: datetime(2026, 2, 18, 12, 0)  # 12:00 PM
    result = await trader.run_cycle()
    assert result["status"] != "market_closed"

    # 장 마감 직전
    trader._now = lambda: datetime(2026, 2, 18, 15, 25)  # 03:25 PM
    result = await trader.run_cycle()
    assert result["status"] != "market_closed"


@pytest.mark.asyncio
async def test_trader_multiple_cycles(test_config):
    """연속 사이클 실행"""
    trader = Trader(config=test_config)
    trader._now = lambda: datetime(2026, 2, 18, 10, 0)  # 10:00 AM

    # 여러 사이클 실행
    results = []
    for _ in range(3):
        result = await trader.run_cycle()
        results.append(result)

    # 모든 사이클이 정상 실행됨
    assert len(results) == 3
    for result in results:
        assert "status" in result
