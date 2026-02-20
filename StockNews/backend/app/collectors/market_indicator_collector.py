"""시장 지표 수집기 — VIX, KOSPI, S&P500, USD/KRW.

Library module: training_data_builder에서 import하여 사용.
하루에 1회만 API 호출, 결과 캐시하여 전 종목 공유.
"""

import logging
from datetime import date, timedelta

import pandas as pd

from app.collectors.yfinance_middleware import download_with_retry

logger = logging.getLogger(__name__)


class MarketIndicatorCollector:
    """시장 지표 수집기. 일 1회 호출, 캐시."""

    TICKERS = {
        "kospi": "^KS11",
        "sp500": "^GSPC",
        "vix": "^VIX",
        "usd_krw": "KRW=X",
    }

    def __init__(self):
        self._cache: dict[str, dict] = {}

    def fetch_daily_indicators(self, target_date: date, market: str) -> dict:
        """시장 지표 수집 (캐시 우선).

        Args:
            target_date: 대상 날짜
            market: "KR" or "US"

        Returns:
            {"market_return": float, "vix_change": float, "usd_krw_change": float|None}
        """
        cache_key = f"{target_date}_{market}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = {
            "market_return": 0.0,
            "vix_change": 0.0,
            "usd_krw_change": None,
        }

        # Determine which market index to use
        index_ticker = self.TICKERS["kospi"] if market == "KR" else self.TICKERS["sp500"]

        start = target_date - timedelta(days=10)
        end = target_date + timedelta(days=1)

        # Fetch market index
        index_df = self._fetch_ticker(index_ticker, start, end)
        if index_df is not None and len(index_df) >= 2:
            closes = self._extract_closes(index_df)
            if len(closes) >= 2:
                prev, curr = float(closes.iloc[-2]), float(closes.iloc[-1])
                if prev != 0:
                    result["market_return"] = round(((curr - prev) / prev) * 100, 4)

        # Fetch VIX
        vix_df = self._fetch_ticker(self.TICKERS["vix"], start, end)
        if vix_df is not None and len(vix_df) >= 2:
            closes = self._extract_closes(vix_df)
            if len(closes) >= 2:
                prev, curr = float(closes.iloc[-2]), float(closes.iloc[-1])
                if prev != 0:
                    result["vix_change"] = round(((curr - prev) / prev) * 100, 4)

        # Fetch USD/KRW (for KR market only)
        if market == "KR":
            fx_df = self._fetch_ticker(self.TICKERS["usd_krw"], start, end)
            if fx_df is not None and len(fx_df) >= 2:
                closes = self._extract_closes(fx_df)
                if len(closes) >= 2:
                    prev, curr = float(closes.iloc[-2]), float(closes.iloc[-1])
                    if prev != 0:
                        result["usd_krw_change"] = round(((curr - prev) / prev) * 100, 4)

        self._cache[cache_key] = result
        return result

    def clear_cache(self):
        """캐시 초기화."""
        self._cache.clear()

    def _fetch_ticker(self, ticker: str, start: date, end: date) -> pd.DataFrame | None:
        """단일 티커 데이터 조회."""
        try:
            df = download_with_retry(ticker, start=str(start), end=str(end))
            if df is not None and not df.empty:
                return df
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", ticker, e)
        return None

    @staticmethod
    def _extract_closes(df: pd.DataFrame) -> pd.Series:
        """DataFrame에서 Close 컬럼 추출 (MultiIndex 핸들링)."""
        closes = df["Close"]
        if isinstance(closes, pd.DataFrame):
            closes = closes.iloc[:, 0]
        return closes.dropna()
