"""Tests for market_indicator_collector module."""

from datetime import date
from unittest.mock import patch

import pandas as pd
import pytest

from app.collectors.market_indicator_collector import MarketIndicatorCollector


@pytest.fixture
def collector():
    return MarketIndicatorCollector()


def _make_price_df(closes: list[float], start_date: str = "2026-02-10") -> pd.DataFrame:
    """Helper: Close 데이터로 DataFrame 생성."""
    return pd.DataFrame(
        {"Close": closes, "Volume": [1000000] * len(closes)},
        index=pd.date_range(start_date, periods=len(closes)),
    )


class TestFetchDailyIndicators:
    def test_kr_market_return(self, collector):
        """KR 시장: KOSPI 등락률 반환."""
        kospi_df = _make_price_df([2500.0, 2550.0])  # +2%
        vix_df = _make_price_df([20.0, 21.0])  # +5%
        fx_df = _make_price_df([1300.0, 1310.0])  # +0.77%

        with patch.object(collector, "_fetch_ticker") as mock:
            mock.side_effect = [kospi_df, vix_df, fx_df]
            result = collector.fetch_daily_indicators(date(2026, 2, 15), "KR")

        assert abs(result["market_return"] - 2.0) < 0.01
        assert abs(result["vix_change"] - 5.0) < 0.01
        assert result["usd_krw_change"] is not None
        assert abs(result["usd_krw_change"] - 0.7692) < 0.01

    def test_us_market_return(self, collector):
        """US 시장: S&P500 등락률 반환, usd_krw 없음."""
        sp500_df = _make_price_df([5000.0, 5100.0])  # +2%
        vix_df = _make_price_df([18.0, 17.0])  # -5.56%

        with patch.object(collector, "_fetch_ticker") as mock:
            mock.side_effect = [sp500_df, vix_df]
            result = collector.fetch_daily_indicators(date(2026, 2, 15), "US")

        assert abs(result["market_return"] - 2.0) < 0.01
        assert result["vix_change"] < 0  # VIX decreased
        assert result["usd_krw_change"] is None  # Not fetched for US

    def test_cache_hit(self, collector):
        """같은 날짜+시장 재호출 시 캐시 반환."""
        df = _make_price_df([100.0, 102.0])

        with patch.object(collector, "_fetch_ticker") as mock:
            mock.return_value = df
            result1 = collector.fetch_daily_indicators(date(2026, 2, 15), "KR")
            result2 = collector.fetch_daily_indicators(date(2026, 2, 15), "KR")

        assert result1 == result2
        # _fetch_ticker should only be called for the first request
        first_call_count = mock.call_count
        # Second call should use cache, so call count should not increase
        # First KR call: 3 fetches (kospi, vix, fx), second call: 0 (cached)
        assert first_call_count == 3

    def test_clear_cache(self, collector):
        """캐시 초기화 후 재호출."""
        collector._cache["2026-02-15_KR"] = {"market_return": 1.0, "vix_change": 0.5, "usd_krw_change": 0.1}
        collector.clear_cache()
        assert len(collector._cache) == 0

    def test_fetch_failure_returns_defaults(self, collector):
        """데이터 조회 실패 시 기본값(0.0) 반환."""
        with patch.object(collector, "_fetch_ticker") as mock:
            mock.return_value = None
            result = collector.fetch_daily_indicators(date(2026, 2, 15), "KR")

        assert result["market_return"] == 0.0
        assert result["vix_change"] == 0.0
        assert result["usd_krw_change"] is None

    def test_insufficient_data_returns_defaults(self, collector):
        """데이터가 1개 이하면 기본값."""
        single_df = _make_price_df([100.0])

        with patch.object(collector, "_fetch_ticker") as mock:
            mock.return_value = single_df
            result = collector.fetch_daily_indicators(date(2026, 2, 15), "US")

        assert result["market_return"] == 0.0
        assert result["vix_change"] == 0.0


class TestExtractCloses:
    def test_simple_dataframe(self, collector):
        """일반 DataFrame Close 추출."""
        df = _make_price_df([100.0, 101.0, 102.0])
        closes = collector._extract_closes(df)
        assert len(closes) == 3

    def test_multiindex_dataframe(self, collector):
        """MultiIndex DataFrame Close 추출."""
        idx = pd.date_range("2026-02-10", periods=3)
        df = pd.DataFrame(
            {("Close", "^KS11"): [2500.0, 2550.0, 2600.0]},
            index=idx,
        )
        closes = collector._extract_closes(df)
        assert len(closes) == 3
