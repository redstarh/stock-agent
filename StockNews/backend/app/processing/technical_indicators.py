"""기술적 지표 계산 유틸리티 — yfinance DataFrame 기반."""

import logging
from datetime import date, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def calc_rsi(closes: pd.Series, period: int = 14) -> float | None:
    """RSI(Relative Strength Index) 계산.

    Args:
        closes: 종가 시리즈 (최소 period+1 개)
        period: RSI 기간 (기본 14)

    Returns:
        RSI 값 (0~100) 또는 None
    """
    if len(closes) < period + 1:
        return None

    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    last_avg_gain = avg_gain.iloc[-1]
    last_avg_loss = avg_loss.iloc[-1]

    if last_avg_loss == 0:
        return 100.0

    rs = last_avg_gain / last_avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi), 2)


def calc_bollinger_position(closes: pd.Series, period: int = 20) -> float | None:
    """볼린저밴드 내 위치 (0~1).

    0 = 하단밴드, 0.5 = 중심선, 1 = 상단밴드.

    Args:
        closes: 종가 시리즈 (최소 period 개)
        period: 볼린저밴드 기간 (기본 20)

    Returns:
        밴드 내 위치 (0~1) 또는 None
    """
    if len(closes) < period:
        return None

    sma = closes.rolling(window=period).mean().iloc[-1]
    std = closes.rolling(window=period).std().iloc[-1]

    if std == 0 or pd.isna(std):
        return 0.5

    upper = sma + 2 * std
    lower = sma - 2 * std
    band_width = upper - lower

    if band_width == 0:
        return 0.5

    position = (closes.iloc[-1] - lower) / band_width
    return round(float(np.clip(position, 0, 1)), 4)


def calc_volatility(closes: pd.Series, period: int = 5) -> float | None:
    """일간 수익률의 표준편차(변동성).

    Args:
        closes: 종가 시리즈 (최소 period+1 개)
        period: 변동성 기간 (기본 5)

    Returns:
        변동성 (%) 또는 None
    """
    if len(closes) < period + 1:
        return None

    returns = closes.pct_change().dropna()
    if len(returns) < period:
        return None

    vol = returns.iloc[-period:].std() * 100
    return round(float(vol), 4)


def calc_ma_ratio(closes: pd.Series, period: int) -> float | None:
    """이동평균선 대비 현재가 비율.

    Args:
        closes: 종가 시리즈 (최소 period 개)
        period: 이동평균 기간

    Returns:
        현재가 / MA 비율 (1.0 = 이평선 위) 또는 None
    """
    if len(closes) < period:
        return None

    ma = closes.rolling(window=period).mean().iloc[-1]
    if ma == 0 or pd.isna(ma):
        return None

    ratio = closes.iloc[-1] / ma
    return round(float(ratio), 4)


def calc_price_change(closes: pd.Series, period: int = 5) -> float | None:
    """N일 등락률 (%).

    Args:
        closes: 종가 시리즈
        period: 기간 (기본 5일)

    Returns:
        등락률 (%) 또는 None
    """
    if len(closes) < period + 1:
        return None

    old = float(closes.iloc[-(period + 1)])
    current = float(closes.iloc[-1])

    if old == 0:
        return None

    change = ((current - old) / old) * 100
    return round(change, 4)


def calc_volume_change(volumes: pd.Series, period: int = 5) -> float | None:
    """N일 거래량 변화율 (%).

    최근 거래량 vs period일 전 평균 거래량 비교.

    Args:
        volumes: 거래량 시리즈
        period: 기간 (기본 5일)

    Returns:
        거래량 변화율 (%) 또는 None
    """
    if len(volumes) < period + 1:
        return None

    past_avg = float(volumes.iloc[-(period + 1):-1].mean())
    current = float(volumes.iloc[-1])

    if past_avg == 0:
        return None

    change = ((current - past_avg) / past_avg) * 100
    return round(change, 4)


def calc_market_index_change(market: str, target_date: date) -> float | None:
    """시장 지수(KOSPI/S&P500) 전일 등락률.

    Args:
        market: "KR" 또는 "US"
        target_date: 대상 날짜

    Returns:
        전일 등락률 (%) 또는 None
    """
    ticker = "^KS11" if market == "KR" else "^GSPC"
    start = target_date - timedelta(days=14)
    end = target_date + timedelta(days=1)

    try:
        df = yf.download(ticker, start=str(start), end=str(end), progress=False)
        if df.empty or len(df) < 2:
            return None

        closes = df["Close"]
        if isinstance(closes, pd.DataFrame):
            closes = closes.iloc[:, 0]
        closes = closes.dropna()

        if len(closes) < 2:
            return None

        prev = float(closes.iloc[-2])
        curr = float(closes.iloc[-1])

        if prev == 0:
            return None

        change = ((curr - prev) / prev) * 100
        return round(change, 4)
    except Exception as e:
        logger.warning("Failed to fetch market index for %s: %s", market, e)
        return None


def compute_all_technical_indicators(
    closes: pd.Series,
    volumes: pd.Series | None = None,
) -> dict:
    """모든 기술적 지표를 한번에 계산.

    Args:
        closes: 종가 시리즈
        volumes: 거래량 시리즈 (선택)

    Returns:
        {
            "rsi_14": float | None,
            "bb_position": float | None,
            "volatility_5d": float | None,
            "ma5_ratio": float | None,
            "ma20_ratio": float | None,
            "price_change_5d": float | None,
            "volume_change_5d": float | None,
        }
    """
    result = {
        "rsi_14": calc_rsi(closes, 14),
        "bb_position": calc_bollinger_position(closes, 20),
        "volatility_5d": calc_volatility(closes, 5),
        "ma5_ratio": calc_ma_ratio(closes, 5),
        "ma20_ratio": calc_ma_ratio(closes, 20),
        "price_change_5d": calc_price_change(closes, 5),
        "volume_change_5d": None,
    }

    if volumes is not None and len(volumes) > 0:
        result["volume_change_5d"] = calc_volume_change(volumes, 5)

    return result
