"""yfinance_middleware 단위 테스트."""

import pandas as pd
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date


class TestDownloadWithRetry:
    """download_with_retry() 함수 테스트."""

    def test_download_success_first_try(self):
        """정상 호출 시 첫 시도에서 데이터 반환."""
        expected_df = pd.DataFrame({"Close": [100, 101, 102]})

        with patch("yfinance.download") as mock_download:
            mock_download.return_value = expected_df

            from app.collectors.yfinance_middleware import download_with_retry
            result = download_with_retry("AAPL", "2024-01-01", "2024-01-10", base_delay=0)

            assert not result.empty
            assert len(result) == 3
            mock_download.assert_called_once()

    def test_download_retry_on_empty(self):
        """빈 DataFrame 반환 시 재시도 후 성공."""
        empty_df = pd.DataFrame()
        success_df = pd.DataFrame({"Close": [100, 101]})

        with patch("yfinance.download") as mock_download:
            mock_download.side_effect = [empty_df, success_df]

            from app.collectors.yfinance_middleware import download_with_retry
            result = download_with_retry("AAPL", "2024-01-01", "2024-01-10", base_delay=0)

            assert not result.empty
            assert len(result) == 2
            assert mock_download.call_count == 2

    def test_download_retry_on_exception(self):
        """예외 발생 시 재시도 후 성공."""
        success_df = pd.DataFrame({"Close": [100]})

        with patch("yfinance.download") as mock_download:
            mock_download.side_effect = [Exception("Network error"), success_df]

            from app.collectors.yfinance_middleware import download_with_retry
            result = download_with_retry("AAPL", "2024-01-01", "2024-01-10", base_delay=0)

            assert not result.empty
            assert mock_download.call_count == 2

    def test_download_all_retries_exhausted(self):
        """모든 재시도 실패 시 빈 DataFrame 반환 (예외 없음)."""
        with patch("yfinance.download") as mock_download:
            mock_download.side_effect = [
                Exception("Error 1"),
                Exception("Error 2"),
                Exception("Error 3"),
            ]

            from app.collectors.yfinance_middleware import download_with_retry
            result = download_with_retry("AAPL", "2024-01-01", "2024-01-10", max_retries=3, base_delay=0)

            assert result.empty
            assert mock_download.call_count == 3

    def test_download_exponential_backoff(self):
        """재시도 시 exponential backoff 지연 적용."""
        success_df = pd.DataFrame({"Close": [100]})

        with patch("yfinance.download") as mock_download, \
             patch("time.sleep") as mock_sleep:
            mock_download.side_effect = [
                Exception("Error 1"),
                Exception("Error 2"),
                success_df,
            ]

            from app.collectors.yfinance_middleware import download_with_retry
            result = download_with_retry("AAPL", "2024-01-01", "2024-01-10", max_retries=3, base_delay=1.0)

            assert not result.empty
            # First retry: 1.0 * 2^0 = 1.0, Second retry: 1.0 * 2^1 = 2.0
            assert mock_sleep.call_count == 2
            mock_sleep.assert_has_calls([call(1.0), call(2.0)])


class TestKrTickerDetection:
    """_is_kr_ticker() 함수 테스트."""

    def test_kr_ticker_detection(self):
        """KR 티커 판별 테스트."""
        from app.collectors.yfinance_middleware import _is_kr_ticker

        assert _is_kr_ticker("005930.KS") is True
        assert _is_kr_ticker("035720.KQ") is True
        assert _is_kr_ticker("AAPL") is False
        assert _is_kr_ticker("MSFT") is False
        assert _is_kr_ticker(["005930.KS", "035720.KQ"]) is True
        assert _is_kr_ticker(["AAPL", "MSFT"]) is False
        assert _is_kr_ticker(["005930.KS", "AAPL"]) is True  # Mixed — any KR returns True


class TestFinanceDataReaderFallback:
    """FinanceDataReader fallback 테스트."""

    def test_fallback_attempted_for_kr(self):
        """KR 티커 실패 시 FinanceDataReader fallback 시도."""
        fallback_df = pd.DataFrame({"Close": [50000, 51000]})

        with patch("yfinance.download") as mock_yf, \
             patch("app.collectors.yfinance_middleware._financedatareader_fallback") as mock_fallback:
            mock_yf.return_value = pd.DataFrame()  # Empty result
            mock_fallback.return_value = fallback_df

            from app.collectors.yfinance_middleware import download_with_retry
            result = download_with_retry("005930.KS", "2024-01-01", "2024-01-10", max_retries=2, base_delay=0)

            assert not result.empty
            assert len(result) == 2
            mock_fallback.assert_called_once_with("005930.KS", "2024-01-01", "2024-01-10")

    def test_no_fallback_for_us(self):
        """US 티커 실패 시 FinanceDataReader fallback 시도 안 함."""
        with patch("yfinance.download") as mock_yf, \
             patch("app.collectors.yfinance_middleware._financedatareader_fallback") as mock_fallback:
            mock_yf.return_value = pd.DataFrame()  # Empty result

            from app.collectors.yfinance_middleware import download_with_retry
            result = download_with_retry("AAPL", "2024-01-01", "2024-01-10", max_retries=2, base_delay=0)

            assert result.empty
            mock_fallback.assert_not_called()

    def test_fallback_not_installed(self):
        """FinanceDataReader 미설치 시 None 반환."""
        # Mock the import to raise ImportError
        import sys
        original_modules = sys.modules.copy()

        # Remove FinanceDataReader from modules if present
        if "FinanceDataReader" in sys.modules:
            del sys.modules["FinanceDataReader"]

        # Prevent import
        sys.modules["FinanceDataReader"] = None

        try:
            from app.collectors.yfinance_middleware import _financedatareader_fallback

            result = _financedatareader_fallback("005930.KS", "2024-01-01", "2024-01-10")
            assert result is None
        finally:
            # Restore modules
            sys.modules.clear()
            sys.modules.update(original_modules)

    def test_fallback_success(self):
        """FinanceDataReader fallback 성공."""
        fallback_df = pd.DataFrame({"Close": [50000, 51000]})
        mock_fdr = MagicMock()
        mock_fdr.DataReader.return_value = fallback_df

        with patch.dict("sys.modules", {"FinanceDataReader": mock_fdr}):
            from app.collectors.yfinance_middleware import _financedatareader_fallback

            result = _financedatareader_fallback("005930.KS", "2024-01-01", "2024-01-10")

            assert result is not None
            assert not result.empty
            mock_fdr.DataReader.assert_called_once_with("005930", "2024-01-01", "2024-01-10")

    def test_fallback_failure(self):
        """FinanceDataReader fallback 실패 시 None."""
        mock_fdr = MagicMock()
        mock_fdr.DataReader.side_effect = Exception("Connection error")

        with patch.dict("sys.modules", {"FinanceDataReader": mock_fdr}):
            from app.collectors.yfinance_middleware import _financedatareader_fallback

            result = _financedatareader_fallback("005930.KS", "2024-01-01", "2024-01-10")

            assert result is None


class TestEdgeCases:
    """엣지 케이스 테스트."""

    def test_none_return_from_yfinance(self):
        """yfinance가 None 반환 시 재시도."""
        success_df = pd.DataFrame({"Close": [100]})

        with patch("yfinance.download") as mock_download:
            mock_download.side_effect = [None, success_df]

            from app.collectors.yfinance_middleware import download_with_retry
            result = download_with_retry("AAPL", "2024-01-01", "2024-01-10", base_delay=0)

            assert not result.empty
            assert mock_download.call_count == 2

    def test_custom_kwargs_passed_through(self):
        """커스텀 kwargs가 yfinance.download에 전달됨."""
        success_df = pd.DataFrame({"Close": [100]})

        with patch("yfinance.download") as mock_download:
            mock_download.return_value = success_df

            from app.collectors.yfinance_middleware import download_with_retry
            download_with_retry(
                "AAPL",
                "2024-01-01",
                "2024-01-10",
                interval="1h",
                auto_adjust=False,
            )

            call_kwargs = mock_download.call_args[1]
            assert call_kwargs["interval"] == "1h"
            assert call_kwargs["auto_adjust"] is False

    def test_date_objects_converted_to_string(self):
        """date 객체를 문자열로 변환."""
        success_df = pd.DataFrame({"Close": [100]})

        with patch("yfinance.download") as mock_download:
            mock_download.return_value = success_df

            from app.collectors.yfinance_middleware import download_with_retry
            download_with_retry(
                "AAPL",
                date(2024, 1, 1),
                date(2024, 1, 10),
            )

            call_kwargs = mock_download.call_args[1]
            assert call_kwargs["start"] == "2024-01-01"
            assert call_kwargs["end"] == "2024-01-10"
