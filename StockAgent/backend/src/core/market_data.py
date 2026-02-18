"""Market Data Collector: 시세 수집, VWAP/캔들 계산"""

import logging
from typing import Any

logger = logging.getLogger("stockagent.core.market_data")


class MarketDataCollector:
    """다중 종목 시세 수집 + 기술 계산"""

    def __init__(self, market_client):
        self._market = market_client

    async def collect(self, stock_codes: list[str]) -> dict[str, dict]:
        """여러 종목의 현재가를 동시 수집"""
        result = {}
        for code in stock_codes:
            try:
                data = await self._market.get_price(code)
                result[code] = data
            except Exception as e:
                logger.error("시세 수집 실패: %s - %s", code, e)
        return result

    @staticmethod
    def calc_trade_value(price: int, volume: int) -> int:
        """거래대금 = 가격 × 거래량"""
        return price * volume

    @staticmethod
    def calc_vwap(trades: list[dict]) -> float:
        """VWAP (거래량가중평균가격) 계산"""
        if not trades:
            return 0.0
        total_value = sum(t["price"] * t["volume"] for t in trades)
        total_volume = sum(t["volume"] for t in trades)
        return total_value / total_volume if total_volume > 0 else 0.0

    @staticmethod
    def aggregate_candle(ticks: list[dict], interval: str = "1m") -> dict:
        """틱 데이터를 캔들(OHLC)로 집계"""
        if not ticks:
            return {"open": 0, "high": 0, "low": 0, "close": 0, "volume": 0}
        prices = [t["price"] for t in ticks]
        return {
            "open": prices[0],
            "high": max(prices),
            "low": min(prices),
            "close": prices[-1],
        }
