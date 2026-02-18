"""Market Data Collector 단위 테스트"""

import pytest
from unittest.mock import AsyncMock

from src.core.market_data import MarketDataCollector


@pytest.fixture
def mock_market():
    """KiwoomMarket 모킹"""
    market = AsyncMock()
    market.get_price = AsyncMock(
        return_value={
            "current_price": 70000,
            "open": 69500,
            "high": 71000,
            "low": 69000,
            "volume": 1000000,
            "trade_value": 70000000000,
        }
    )
    return market


@pytest.mark.asyncio
async def test_collect_prices(mock_market):
    """시세 수집 동작 확인"""
    collector = MarketDataCollector(market_client=mock_market)
    data = await collector.collect(["005930", "000660"])
    assert len(data) == 2
    assert data["005930"]["current_price"] > 0


def test_calculate_trade_value():
    """거래대금 계산"""
    value = MarketDataCollector.calc_trade_value(price=70000, volume=1000)
    assert value == 70_000_000


def test_calculate_vwap():
    """VWAP 계산"""
    trades = [
        {"price": 70000, "volume": 100},
        {"price": 71000, "volume": 200},
    ]
    vwap = MarketDataCollector.calc_vwap(trades)
    expected = (70000 * 100 + 71000 * 200) / 300
    assert abs(vwap - expected) < 0.01


def test_aggregate_1min_candle():
    """1분봉 집계"""
    ticks = [
        {"time": "09:00:01", "price": 70000},
        {"time": "09:00:30", "price": 70500},
        {"time": "09:00:59", "price": 70200},
    ]
    candle = MarketDataCollector.aggregate_candle(ticks, interval="1m")
    assert candle["open"] == 70000
    assert candle["high"] == 70500
    assert candle["low"] == 70000
    assert candle["close"] == 70200


def test_vwap_empty_trades():
    """빈 거래 목록 VWAP"""
    assert MarketDataCollector.calc_vwap([]) == 0.0


def test_candle_single_tick():
    """단일 틱 캔들"""
    ticks = [{"time": "09:00:01", "price": 70000}]
    candle = MarketDataCollector.aggregate_candle(ticks, interval="1m")
    assert candle["open"] == candle["close"] == 70000
