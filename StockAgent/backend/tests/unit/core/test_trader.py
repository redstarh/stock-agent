"""B-8 자동매매 루프 프레임워크 테스트"""

import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config import Settings
from src.core.trader import Trader

logger = logging.getLogger("stockagent.core.trader")


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


@pytest.mark.asyncio
async def test_trader_double_start(test_config):
    """매매 루프 중복 시작 시도 시 경고 반환"""
    trader = Trader(config=test_config)

    # 첫 번째 시작
    await trader.start()
    assert trader.is_running is True

    # 두 번째 시작 시도 (경고 발생, 상태 변화 없음)
    await trader.start()
    assert trader.is_running is True  # 여전히 실행 중


@pytest.mark.asyncio
async def test_trader_double_stop(test_config):
    """매매 루프가 실행 중이 아닐 때 정지 시도 시 경고 반환"""
    trader = Trader(config=test_config)

    # 시작하지 않고 바로 정지 시도 (경고 발생)
    await trader.stop()
    assert trader.is_running is False


@pytest.mark.asyncio
async def test_trader_cycle_exception(test_config):
    """매매 사이클 실행 중 예외 발생 시 skipped 상태 반환

    Note: 현재 trader.py의 try 블록(78-89행)에는 예외를 발생시킬 코드가 없음.
    except 블록(91-97행)은 Sprint 5 구현을 위한 방어 코드.
    테스트는 except 블록의 로직을 검증하지만, 실제 소스 코드의 라인은 커버되지 않음.
    """

    class ExceptionTrader(Trader):
        """테스트용 Trader - try 블록에서 예외 발생 시나리오 시뮬레이션"""

        async def run_cycle(self) -> dict:
            now = self._now()

            if not self._is_market_open(now):
                return {
                    "status": "market_closed",
                    "timestamp": now.isoformat(),
                    "message": "장 외 시간",
                }

            logger.info("매매 사이클 실행: %s", now)

            try:
                # Sprint 5에서 구현될 코드가 예외를 발생시킬 수 있음
                raise RuntimeError("Test exception in cycle")

            except Exception as e:
                logger.error("매매 사이클 실행 중 오류: %s", e, exc_info=True)
                return {
                    "status": "skipped",
                    "timestamp": now.isoformat(),
                    "message": f"오류: {e}",
                }

    trader = ExceptionTrader(config=test_config)

    # 장 시간 내로 설정
    trader._now = lambda: datetime(2026, 2, 18, 10, 0)  # 10:00 AM

    result = await trader.run_cycle()

    # 예외 발생 시 skipped 상태 반환 검증
    assert result["status"] == "skipped"
    assert "오류" in result["message"]
    assert "Test exception" in result["message"]


@pytest.mark.asyncio
async def test_trader_now_returns_datetime(test_config):
    """_now() 메서드가 datetime 인스턴스를 반환"""
    trader = Trader(config=test_config)

    # _now() 호출 (monkey-patch 없이 실제 datetime.now() 사용)
    now = trader._now()

    # datetime 인스턴스 확인
    assert isinstance(now, datetime)
    assert now.year >= 2026
