"""Tests for price_collector module."""

from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from app.collectors.price_collector import (
    PriceCollector,
    fetch_recent_price_change,
)


@pytest.fixture
def mock_yfinance():
    """Mock yfinance Ticker."""
    with patch("app.collectors.price_collector.yf.Ticker") as mock_ticker:
        yield mock_ticker


@pytest.fixture
def sample_price_data():
    """샘플 주가 데이터."""
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    return pd.DataFrame(
        {
            "Open": [100 + i for i in range(30)],
            "High": [105 + i for i in range(30)],
            "Low": [95 + i for i in range(30)],
            "Close": [100 + i * 0.5 for i in range(30)],
            "Volume": [1000000 + i * 10000 for i in range(30)],
        },
        index=pd.DatetimeIndex(dates),
    )


class TestPriceCollector:
    """PriceCollector 테스트."""

    def test_fetch_price_history_kr_stock(self, mock_yfinance, sample_price_data):
        """한국 종목 주가 조회."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_yfinance.return_value = mock_ticker_instance

        collector = PriceCollector()
        df = collector.fetch_price_history("005930", period="1mo")

        assert df is not None
        assert len(df) == 30
        assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]
        mock_yfinance.assert_called_once_with("005930.KS")

    def test_fetch_price_history_us_stock(self, mock_yfinance, sample_price_data):
        """미국 종목 주가 조회."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_yfinance.return_value = mock_ticker_instance

        collector = PriceCollector()
        df = collector.fetch_price_history("AAPL", period="3mo")

        assert df is not None
        assert len(df) == 30
        mock_yfinance.assert_called_once_with("AAPL")

    def test_fetch_price_history_empty_data(self, mock_yfinance):
        """데이터가 없는 경우."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_yfinance.return_value = mock_ticker_instance

        collector = PriceCollector()
        df = collector.fetch_price_history("INVALID")

        assert df is None

    def test_fetch_price_history_api_error(self, mock_yfinance):
        """API 에러 처리."""
        mock_yfinance.side_effect = Exception("Network error")

        collector = PriceCollector()
        df = collector.fetch_price_history("005930")

        assert df is None

    def test_cache_mechanism(self, mock_yfinance, sample_price_data):
        """캐시 동작 확인."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_yfinance.return_value = mock_ticker_instance

        collector = PriceCollector(cache_ttl=300)

        # 첫 번째 호출
        df1 = collector.fetch_price_history("005930", period="1mo")
        # 두 번째 호출 (캐시에서 가져옴)
        df2 = collector.fetch_price_history("005930", period="1mo")

        assert df1 is not None
        assert df2 is not None
        assert len(df1) == len(df2)
        # API는 한 번만 호출되어야 함
        mock_yfinance.assert_called_once()

    def test_clear_cache(self, mock_yfinance, sample_price_data):
        """캐시 초기화."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_yfinance.return_value = mock_ticker_instance

        collector = PriceCollector()

        # 캐시에 데이터 저장
        collector.fetch_price_history("005930")

        # 캐시 초기화
        collector.clear_cache()

        # 다시 호출하면 API가 다시 호출되어야 함
        collector.fetch_price_history("005930")

        assert mock_yfinance.call_count == 2

    def test_format_ticker_kr_stock(self):
        """한국 종목 티커 포맷."""
        collector = PriceCollector()
        assert collector._format_ticker("005930") == "005930.KS"
        assert collector._format_ticker("035720") == "035720.KS"

    def test_format_ticker_us_stock(self):
        """미국 종목 티커 포맷."""
        collector = PriceCollector()
        assert collector._format_ticker("AAPL") == "AAPL"
        assert collector._format_ticker("TSLA") == "TSLA"

    def test_format_ticker_already_formatted(self):
        """이미 포맷된 티커."""
        collector = PriceCollector()
        assert collector._format_ticker("005930.KS") == "005930.KS"
        assert collector._format_ticker("035720.KQ") == "035720.KQ"


class TestFetchRecentPriceChange:
    """fetch_recent_price_change 함수 테스트."""

    def test_fetch_recent_price_change_success(self, mock_yfinance, sample_price_data):
        """정상 케이스."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_yfinance.return_value = mock_ticker_instance

        result = fetch_recent_price_change("005930", days=5)

        assert "change_pct" in result
        assert "volume_change_pct" in result
        assert "ma_ratio" in result
        assert isinstance(result["change_pct"], float)

    def test_fetch_recent_price_change_no_data(self, mock_yfinance):
        """데이터가 없는 경우."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_yfinance.return_value = mock_ticker_instance

        result = fetch_recent_price_change("INVALID", days=5)

        assert result["change_pct"] == 0.0
        assert result["volume_change_pct"] == 0.0
        assert result["ma_ratio"] == 1.0

    def test_fetch_recent_price_change_with_collector(
        self, mock_yfinance, sample_price_data
    ):
        """collector 인스턴스 전달."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_yfinance.return_value = mock_ticker_instance

        collector = PriceCollector()
        result = fetch_recent_price_change("005930", days=5, collector=collector)

        assert result["change_pct"] != 0.0
        # 캐시가 사용되었는지 확인 가능
