"""단위 테스트: 미국 종목 매핑."""

from app.processing.us_stock_mapper import (
    ticker_to_name,
    name_to_ticker,
    extract_tickers_from_text,
    US_STOCK_MAP,
)


class TestUSStockMapper:
    def test_ticker_to_name(self):
        assert ticker_to_name("AAPL") == "Apple"
        assert ticker_to_name("NVDA") == "NVIDIA"
        assert ticker_to_name("aapl") == "Apple"  # case insensitive

    def test_ticker_not_found(self):
        assert ticker_to_name("XXXX") is None

    def test_name_to_ticker(self):
        assert name_to_ticker("Apple") == "AAPL"
        assert name_to_ticker("apple") == "AAPL"  # case insensitive

    def test_name_not_found(self):
        assert name_to_ticker("Unknown Corp") is None

    def test_extract_tickers_from_text(self):
        text = "NVDA and AAPL both reported strong earnings"
        tickers = extract_tickers_from_text(text)
        assert "NVDA" in tickers
        assert "AAPL" in tickers

    def test_extract_no_tickers(self):
        text = "No stock tickers in this text"
        assert extract_tickers_from_text(text) == []

    def test_map_has_50_entries(self):
        assert len(US_STOCK_MAP) == 50
