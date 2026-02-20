"""Tests for price_fetcher module."""

from datetime import date

import pandas as pd
import pytest

from app.processing.price_fetcher import (
    fetch_prices_batch,
    format_ticker,
    get_direction_from_change,
)


def test_format_ticker_kr():
    """Test formatting Korean stock codes."""
    assert format_ticker("005930", "KR") == "005930.KS"
    assert format_ticker("035720", "KR") == "035720.KS"


def test_format_ticker_us():
    """Test formatting US stock codes."""
    assert format_ticker("AAPL", "US") == "AAPL"
    assert format_ticker("TSLA", "US") == "TSLA"


def test_format_ticker_already_formatted():
    """Test that already formatted tickers are not double-formatted."""
    assert format_ticker("005930.KS", "KR") == "005930.KS"
    assert format_ticker("035720.KQ", "KR") == "035720.KQ"


def test_get_direction_up():
    """Test direction detection for upward price movement."""
    assert get_direction_from_change(2.5) == "up"
    assert get_direction_from_change(1.1) == "up"
    assert get_direction_from_change(10.0) == "up"


def test_get_direction_down():
    """Test direction detection for downward price movement."""
    assert get_direction_from_change(-2.5) == "down"
    assert get_direction_from_change(-1.1) == "down"
    assert get_direction_from_change(-10.0) == "down"


def test_get_direction_neutral():
    """Test direction detection for neutral price movement."""
    assert get_direction_from_change(0.5) == "neutral"
    assert get_direction_from_change(-0.5) == "neutral"
    assert get_direction_from_change(0.0) == "neutral"
    assert get_direction_from_change(0.99) == "neutral"
    assert get_direction_from_change(-0.99) == "neutral"


@pytest.mark.asyncio
async def test_fetch_prices_batch_success(monkeypatch):
    """Test successful batch price fetching with OHLCV data."""
    # Create mock DataFrame with multi-level columns including OHLCV
    data = {
        ("Close", "005930.KS"): [69000.0, 70000.0, 71500.0],
        ("Close", "000660.KS"): [130000.0, 132000.0, 133500.0],
        ("Open", "005930.KS"): [68500.0, 69500.0, 71000.0],
        ("Open", "000660.KS"): [129500.0, 131500.0, 133000.0],
        ("High", "005930.KS"): [69500.0, 70500.0, 72000.0],
        ("High", "000660.KS"): [130500.0, 132500.0, 134000.0],
        ("Low", "005930.KS"): [68000.0, 69000.0, 70500.0],
        ("Low", "000660.KS"): [129000.0, 131000.0, 132500.0],
        ("Volume", "005930.KS"): [5000000, 6000000, 7000000],
        ("Volume", "000660.KS"): [2000000, 2500000, 3000000],
    }
    mock_df = pd.DataFrame(data)
    mock_df.columns = pd.MultiIndex.from_tuples(mock_df.columns)
    mock_df.index = pd.date_range("2026-02-17", periods=3)

    def mock_download(*args, **kwargs):
        return mock_df

    monkeypatch.setattr("yfinance.download", mock_download)

    results = await fetch_prices_batch(
        stock_codes=["005930", "000660"],
        market="KR",
        target_date=date(2026, 2, 19),
    )

    assert len(results) == 2
    assert "005930" in results
    assert "000660" in results

    # Check 005930 basic data
    r = results["005930"]
    assert r is not None
    assert r["previous_close"] == 70000.0
    assert r["current_close"] == 71500.0
    assert abs(r["change_pct"] - 2.1429) < 0.01

    # Check 005930 OHLCV
    assert r["open"] == 71000.0
    assert r["high"] == 72000.0
    assert r["low"] == 70500.0
    assert r["volume"] == 7000000
    assert r["previous_volume"] == 6000000

    # Check 000660 data
    r2 = results["000660"]
    assert r2 is not None
    assert r2["previous_close"] == 132000.0
    assert r2["current_close"] == 133500.0
    assert r2["open"] == 133000.0
    assert r2["high"] == 134000.0
    assert r2["low"] == 132500.0
    assert r2["volume"] == 3000000
    assert r2["previous_volume"] == 2500000


@pytest.mark.asyncio
async def test_fetch_prices_batch_single_stock_ohlcv(monkeypatch):
    """Test single stock fetch includes OHLCV data."""
    data = {
        "Close": [69000.0, 70000.0, 71500.0],
        "Open": [68500.0, 69500.0, 71000.0],
        "High": [69500.0, 70500.0, 72000.0],
        "Low": [68000.0, 69000.0, 70500.0],
        "Volume": [5000000, 6000000, 7000000],
    }
    mock_df = pd.DataFrame(data)
    mock_df.index = pd.date_range("2026-02-17", periods=3)

    def mock_download(*args, **kwargs):
        return mock_df

    monkeypatch.setattr("yfinance.download", mock_download)

    results = await fetch_prices_batch(
        stock_codes=["005930"],
        market="KR",
        target_date=date(2026, 2, 19),
    )

    assert len(results) == 1
    r = results["005930"]
    assert r is not None
    assert r["previous_close"] == 70000.0
    assert r["current_close"] == 71500.0
    assert r["open"] == 71000.0
    assert r["high"] == 72000.0
    assert r["low"] == 70500.0
    assert r["volume"] == 7000000
    assert r["previous_volume"] == 6000000


@pytest.mark.asyncio
async def test_fetch_prices_batch_empty_data(monkeypatch):
    """Test batch fetching with empty DataFrame (data not available)."""
    # Mock empty DataFrame
    mock_df = pd.DataFrame()

    def mock_download(*args, **kwargs):
        return mock_df

    monkeypatch.setattr("yfinance.download", mock_download)

    results = await fetch_prices_batch(
        stock_codes=["005930", "000660"],
        market="KR",
        target_date=date(2026, 2, 19),
    )

    assert len(results) == 2
    assert results["005930"] is None
    assert results["000660"] is None
