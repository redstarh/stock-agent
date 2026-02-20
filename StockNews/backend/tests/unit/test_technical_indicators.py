"""Tests for technical_indicators module."""

import numpy as np
import pandas as pd
import pytest

from app.processing.technical_indicators import (
    calc_bollinger_position,
    calc_ma_ratio,
    calc_market_index_change,
    calc_price_change,
    calc_rsi,
    calc_volatility,
    calc_volume_change,
    compute_all_technical_indicators,
)


@pytest.fixture
def uptrend_closes():
    """상승 추세 종가 시리즈 (30일)."""
    return pd.Series([100 + i * 2 for i in range(30)], dtype=float)


@pytest.fixture
def downtrend_closes():
    """하락 추세 종가 시리즈 (30일)."""
    return pd.Series([200 - i * 2 for i in range(30)], dtype=float)


@pytest.fixture
def flat_closes():
    """횡보 종가 시리즈 (30일)."""
    return pd.Series([100.0] * 30, dtype=float)


@pytest.fixture
def short_closes():
    """데이터 부족 시리즈 (3일)."""
    return pd.Series([100.0, 101.0, 102.0], dtype=float)


# === RSI Tests ===

def test_calc_rsi_uptrend(uptrend_closes):
    """상승 추세에서 RSI > 50."""
    rsi = calc_rsi(uptrend_closes, 14)
    assert rsi is not None
    assert rsi > 50


def test_calc_rsi_downtrend(downtrend_closes):
    """하락 추세에서 RSI < 50."""
    rsi = calc_rsi(downtrend_closes, 14)
    assert rsi is not None
    assert rsi < 50


def test_calc_rsi_insufficient_data(short_closes):
    """데이터 부족 시 None 반환."""
    assert calc_rsi(short_closes, 14) is None


def test_calc_rsi_all_gains():
    """모두 상승일 때 RSI = 100."""
    closes = pd.Series([100 + i for i in range(20)], dtype=float)
    rsi = calc_rsi(closes, 14)
    assert rsi is not None
    assert rsi == 100.0


# === Bollinger Band Tests ===

def test_calc_bollinger_middle(flat_closes):
    """횡보 시 볼린저밴드 위치 ≈ 0.5."""
    bb = calc_bollinger_position(flat_closes, 20)
    assert bb is not None
    assert bb == 0.5


def test_calc_bollinger_range(uptrend_closes):
    """볼린저밴드 위치는 0~1 범위."""
    bb = calc_bollinger_position(uptrend_closes, 20)
    assert bb is not None
    assert 0 <= bb <= 1


def test_calc_bollinger_insufficient_data(short_closes):
    """데이터 부족 시 None 반환."""
    assert calc_bollinger_position(short_closes, 20) is None


# === Volatility Tests ===

def test_calc_volatility_flat(flat_closes):
    """횡보 시 변동성 = 0."""
    vol = calc_volatility(flat_closes, 5)
    assert vol is not None
    assert vol == 0.0


def test_calc_volatility_positive(uptrend_closes):
    """추세 있을 때 변동성 > 0."""
    vol = calc_volatility(uptrend_closes, 5)
    assert vol is not None
    assert vol > 0


def test_calc_volatility_insufficient_data(short_closes):
    """데이터 부족 시 None 반환."""
    assert calc_volatility(short_closes, 5) is None


# === MA Ratio Tests ===

def test_calc_ma_ratio_above(uptrend_closes):
    """상승 추세에서 MA 대비 비율 > 1."""
    ratio = calc_ma_ratio(uptrend_closes, 5)
    assert ratio is not None
    assert ratio > 1.0


def test_calc_ma_ratio_below(downtrend_closes):
    """하락 추세에서 MA 대비 비율 < 1."""
    ratio = calc_ma_ratio(downtrend_closes, 5)
    assert ratio is not None
    assert ratio < 1.0


def test_calc_ma_ratio_flat(flat_closes):
    """횡보 시 MA 대비 비율 = 1."""
    ratio = calc_ma_ratio(flat_closes, 5)
    assert ratio is not None
    assert ratio == 1.0


def test_calc_ma_ratio_insufficient_data(short_closes):
    """데이터 부족 시 None 반환."""
    assert calc_ma_ratio(short_closes, 20) is None


# === Price Change Tests ===

def test_calc_price_change_positive():
    """양의 등락률."""
    closes = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 110.0], dtype=float)
    change = calc_price_change(closes, 5)
    assert change is not None
    assert change == 10.0


def test_calc_price_change_negative():
    """음의 등락률."""
    closes = pd.Series([100.0, 99.0, 98.0, 97.0, 96.0, 90.0], dtype=float)
    change = calc_price_change(closes, 5)
    assert change is not None
    assert change == -10.0


def test_calc_price_change_insufficient_data():
    """데이터 부족 시 None 반환."""
    closes = pd.Series([100.0, 101.0], dtype=float)
    assert calc_price_change(closes, 5) is None


# === Volume Change Tests ===

def test_calc_volume_change_increase():
    """거래량 증가."""
    vols = pd.Series([1000, 1000, 1000, 1000, 1000, 2000], dtype=float)
    change = calc_volume_change(vols, 5)
    assert change is not None
    assert change == 100.0


def test_calc_volume_change_decrease():
    """거래량 감소."""
    vols = pd.Series([2000, 2000, 2000, 2000, 2000, 1000], dtype=float)
    change = calc_volume_change(vols, 5)
    assert change is not None
    assert change == -50.0


def test_calc_volume_change_insufficient_data():
    """데이터 부족 시 None."""
    vols = pd.Series([1000, 2000], dtype=float)
    assert calc_volume_change(vols, 5) is None


# === Market Index Change Tests ===

def test_calc_market_index_change_mock(monkeypatch):
    """시장 지수 등락률 mock 테스트."""
    from datetime import date

    import yfinance as yf

    mock_df = pd.DataFrame(
        {"Close": [2800.0, 2850.0, 2900.0]},
        index=pd.date_range("2026-02-17", periods=3),
    )

    def mock_download(*args, **kwargs):
        return mock_df

    monkeypatch.setattr("app.processing.technical_indicators.yf.download", mock_download)

    change = calc_market_index_change("KR", date(2026, 2, 19))
    assert change is not None
    assert abs(change - 1.7544) < 0.01


def test_calc_market_index_change_empty(monkeypatch):
    """빈 데이터 시 None 반환."""
    import yfinance as yf

    from datetime import date

    def mock_download(*args, **kwargs):
        return pd.DataFrame()

    monkeypatch.setattr("app.processing.technical_indicators.yf.download", mock_download)

    assert calc_market_index_change("KR", date(2026, 2, 19)) is None


# === Compute All Tests ===

def test_compute_all_technical_indicators(uptrend_closes):
    """모든 지표 한번에 계산."""
    volumes = pd.Series([1000 + i * 100 for i in range(30)], dtype=float)

    result = compute_all_technical_indicators(uptrend_closes, volumes)

    assert "rsi_14" in result
    assert "bb_position" in result
    assert "volatility_5d" in result
    assert "ma5_ratio" in result
    assert "ma20_ratio" in result
    assert "price_change_5d" in result
    assert "volume_change_5d" in result

    # All should have values with 30 data points
    assert result["rsi_14"] is not None
    assert result["bb_position"] is not None
    assert result["volatility_5d"] is not None
    assert result["ma5_ratio"] is not None
    assert result["ma20_ratio"] is not None
    assert result["price_change_5d"] is not None
    assert result["volume_change_5d"] is not None


def test_compute_all_no_volumes(uptrend_closes):
    """거래량 없이 계산."""
    result = compute_all_technical_indicators(uptrend_closes)
    assert result["volume_change_5d"] is None
    assert result["rsi_14"] is not None
