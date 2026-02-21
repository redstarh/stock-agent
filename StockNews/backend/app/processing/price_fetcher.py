"""yfinance 기반 주가 데이터 조회."""

import asyncio
import logging
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def format_ticker(stock_code: str, market: str) -> str:
    """Format stock code to yfinance ticker."""
    if market == "KR" and not stock_code.endswith((".KS", ".KQ")):
        return f"{stock_code}.KS"
    return stock_code


def get_direction_from_change(change_pct: float, threshold: float = 1.0) -> str:
    """Map price change percentage to direction."""
    if change_pct > threshold:
        return "up"
    elif change_pct < -threshold:
        return "down"
    return "neutral"


async def fetch_prices_batch(
    stock_codes: list[str],
    market: str,
    target_date: date,
) -> dict[str, dict | None]:
    """Batch fetch stock prices for verification."""
    tickers = [format_ticker(code, market) for code in stock_codes]
    start = target_date - timedelta(days=14)
    end = target_date + timedelta(days=1)

    loop = asyncio.get_event_loop()
    try:
        df = await loop.run_in_executor(
            None,
            lambda: yf.download(
                tickers if len(tickers) > 1 else tickers[0],
                start=str(start),
                end=str(end),
                progress=False,
                threads=True,
            ),
        )
    except Exception as e:
        logger.error("yfinance batch download failed: %s", e)
        return {code: None for code in stock_codes}

    results = {}
    for code, ticker in zip(stock_codes, tickers, strict=False):
        try:
            if len(tickers) == 1:
                stock_df = df
            else:
                stock_df = df.xs(ticker, axis=1, level=1) if isinstance(df.columns, pd.MultiIndex) else df

            closes = stock_df["Close"].dropna()
            if len(closes) < 2:
                results[code] = None
                continue

            prev = float(closes.iloc[-2])
            curr = float(closes.iloc[-1])
            change = ((curr - prev) / prev) * 100 if prev != 0 else 0.0

            # OHLCV extraction
            open_price = None
            high_price = None
            low_price = None
            volume = None
            prev_volume = None

            if "Open" in stock_df.columns:
                opens = stock_df["Open"].dropna()
                if len(opens) >= 1:
                    open_price = float(opens.iloc[-1])

            if "High" in stock_df.columns:
                highs = stock_df["High"].dropna()
                if len(highs) >= 1:
                    high_price = float(highs.iloc[-1])

            if "Low" in stock_df.columns:
                lows = stock_df["Low"].dropna()
                if len(lows) >= 1:
                    low_price = float(lows.iloc[-1])

            if "Volume" in stock_df.columns:
                vols = stock_df["Volume"].dropna()
                if len(vols) >= 1:
                    volume = int(vols.iloc[-1])
                if len(vols) >= 2:
                    prev_volume = int(vols.iloc[-2])

            results[code] = {
                "previous_close": prev,
                "current_close": curr,
                "change_pct": round(change, 4),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "volume": volume,
                "previous_volume": prev_volume,
            }
        except (KeyError, IndexError, TypeError):
            results[code] = None

    return results
