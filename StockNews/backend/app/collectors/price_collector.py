"""주가 데이터 수집 모듈 (yfinance 기반)."""

import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf
from loguru import logger


class PriceCollector:
    """yfinance 기반 주가 데이터 수집기."""

    def __init__(self, cache_ttl: int = 300):
        """초기화.

        Args:
            cache_ttl: 캐시 유지 시간 (초)
        """
        self._cache: dict[str, tuple[pd.DataFrame, float]] = {}
        self._cache_ttl = cache_ttl

    def fetch_price_history(
        self, stock_code: str, period: str = "3mo"
    ) -> Optional[pd.DataFrame]:
        """주가 히스토리 조회.

        Args:
            stock_code: 종목 코드 (KR 종목은 .KS 접미사 자동 추가)
            period: 조회 기간 (1mo, 3mo, 6mo, 1y 등)

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
            실패 시 None
        """
        # 캐시 확인
        cache_key = f"{stock_code}:{period}"
        if cache_key in self._cache:
            df, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for {cache_key}")
                return df.copy()

        # 티커 포맷 변환
        ticker = self._format_ticker(stock_code)

        try:
            logger.info(f"Fetching price data for {ticker} (period={period})")
            yf_ticker = yf.Ticker(ticker)
            hist = yf_ticker.history(period=period)

            if hist.empty:
                logger.warning(f"No price data for {ticker}")
                return None

            # DataFrame 정리
            df = pd.DataFrame(
                {
                    "date": hist.index.date,
                    "open": hist["Open"].values,
                    "high": hist["High"].values,
                    "low": hist["Low"].values,
                    "close": hist["Close"].values,
                    "volume": hist["Volume"].values,
                }
            )

            # 캐시 저장
            self._cache[cache_key] = (df.copy(), time.time())

            logger.info(f"Fetched {len(df)} price records for {ticker}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch price data for {ticker}: {e}")
            return None

    def _format_ticker(self, stock_code: str) -> str:
        """종목 코드를 yfinance 티커 포맷으로 변환.

        Args:
            stock_code: 종목 코드 (예: "005930" 또는 "AAPL")

        Returns:
            yfinance 티커 (예: "005930.KS" 또는 "AAPL")
        """
        # 이미 .KS 또는 .KQ 접미사가 있으면 그대로 반환
        if stock_code.endswith((".KS", ".KQ")):
            return stock_code

        # 숫자로만 구성된 경우 KR 종목으로 간주
        if stock_code.isdigit():
            return f"{stock_code}.KS"

        # 그 외는 US 종목
        return stock_code

    def clear_cache(self):
        """캐시 초기화."""
        self._cache.clear()
        logger.debug("Price cache cleared")


def fetch_recent_price_change(
    stock_code: str, days: int = 5, collector: Optional[PriceCollector] = None
) -> dict[str, float]:
    """최근 N일간 주가 변동률 계산.

    Args:
        stock_code: 종목 코드
        days: 조회 일수
        collector: PriceCollector 인스턴스 (None이면 새로 생성)

    Returns:
        {"change_pct": float, "volume_change_pct": float, "ma_ratio": float}
    """
    if collector is None:
        collector = PriceCollector()

    # 충분한 기간 데이터 가져오기
    period = "1mo" if days <= 30 else "3mo"
    df = collector.fetch_price_history(stock_code, period=period)

    if df is None or len(df) < 2:
        return {"change_pct": 0.0, "volume_change_pct": 0.0, "ma_ratio": 1.0}

    # 최근 N일 데이터
    recent = df.tail(days)

    # 가격 변동률 (첫날 대비 마지막날)
    if len(recent) >= 2:
        change_pct = (
            (recent.iloc[-1]["close"] - recent.iloc[0]["close"])
            / recent.iloc[0]["close"]
            * 100
        )
    else:
        change_pct = 0.0

    # 거래량 변동률 (최근 평균 vs 이전 평균)
    if len(df) >= days * 2:
        recent_volume = recent["volume"].mean()
        prev_volume = df.iloc[-(days * 2) : -days]["volume"].mean()
        volume_change_pct = (
            (recent_volume - prev_volume) / prev_volume * 100 if prev_volume > 0 else 0.0
        )
    else:
        volume_change_pct = 0.0

    # 이동평균 대비 현재가 비율
    ma = recent["close"].mean()
    current = recent.iloc[-1]["close"]
    ma_ratio = current / ma if ma > 0 else 1.0

    return {
        "change_pct": round(change_pct, 2),
        "volume_change_pct": round(volume_change_pct, 2),
        "ma_ratio": round(ma_ratio, 4),
    }
