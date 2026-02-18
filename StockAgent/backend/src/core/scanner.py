"""Opening Scanner: 장초 모멘텀 종목 스캐닝"""

import logging
from typing import Any

logger = logging.getLogger("stockagent.core.scanner")


class Scanner:
    """장초 거래대금/거래량 기반 종목 스캔"""

    @staticmethod
    def rank_by_trade_value(stocks: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
        """거래대금 기준 상위 N개 종목 반환

        Args:
            stocks: 종목 리스트 (각 항목은 'code', 'trade_value' 포함)
            top_n: 반환할 상위 개수

        Returns:
            거래대금 기준 내림차순 정렬된 상위 N개 종목
        """
        sorted_stocks = sorted(stocks, key=lambda x: x["trade_value"], reverse=True)
        return sorted_stocks[:top_n]

    @staticmethod
    def detect_volume_surge(today_volume: int, prev_volume: int, threshold: float) -> bool:
        """전일 대비 거래량 급증 감지

        Args:
            today_volume: 당일 거래량
            prev_volume: 전일 거래량
            threshold: 급증 판단 배수 (예: 3.0 = 3배 이상)

        Returns:
            급증 여부 (today_volume / prev_volume >= threshold)
        """
        if prev_volume == 0:
            return False
        ratio = today_volume / prev_volume
        return ratio >= threshold

    @staticmethod
    def calc_opening_range(candles: list[dict[str, Any]]) -> dict[str, int]:
        """장초 Range 계산 (09:00~09:30 고/저)

        Args:
            candles: 캔들 리스트 (각 항목은 'time', 'high', 'low' 포함)

        Returns:
            {'high': 최고가, 'low': 최저가}
        """
        if not candles:
            return {"high": 0, "low": 0}

        high = max(candle["high"] for candle in candles)
        low = min(candle["low"] for candle in candles)

        return {"high": high, "low": low}
