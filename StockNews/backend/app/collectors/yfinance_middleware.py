"""yfinance 호출 래퍼 — 재시도 + 폴백."""

import logging
import time
from datetime import date
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def download_with_retry(
    tickers: str | list[str],
    start: str | date,
    end: str | date,
    max_retries: int = 3,
    base_delay: float = 1.0,
    progress: bool = False,
    threads: bool = True,
    **kwargs: Any,
) -> pd.DataFrame:
    """yfinance.download() with exponential backoff retry.

    Args:
        tickers: Ticker symbol(s)
        start: Start date
        end: End date
        max_retries: Maximum retry attempts (default 3)
        base_delay: Base delay in seconds for exponential backoff
        progress: Show progress bar (default False)
        threads: Use threads for multiple tickers
        **kwargs: Additional yfinance.download() kwargs

    Returns:
        DataFrame from yfinance, or empty DataFrame on all failures

    Raises:
        Nothing — returns empty DataFrame on failure (logs warnings)
    """
    import yfinance as yf

    last_error = None
    for attempt in range(max_retries):
        try:
            df = yf.download(
                tickers,
                start=str(start),
                end=str(end),
                progress=progress,
                threads=threads,
                **kwargs,
            )
            if df is not None and not df.empty:
                return df
            # Empty result — might succeed on retry
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "yfinance returned empty for %s (attempt %d/%d), retrying in %.1fs",
                    tickers, attempt + 1, max_retries, delay,
                )
                time.sleep(delay)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "yfinance failed for %s (attempt %d/%d): %s, retrying in %.1fs",
                    tickers, attempt + 1, max_retries, e, delay,
                )
                time.sleep(delay)

    # All retries exhausted — try FinanceDataReader fallback for KR
    if _is_kr_ticker(tickers):
        logger.info("Attempting FinanceDataReader fallback for %s", tickers)
        fallback_df = _financedatareader_fallback(tickers, start, end)
        if fallback_df is not None and not fallback_df.empty:
            return fallback_df

    if last_error:
        logger.error("yfinance failed after %d retries for %s: %s", max_retries, tickers, last_error)
    else:
        logger.error("yfinance returned empty after %d retries for %s", max_retries, tickers)

    return pd.DataFrame()


def _is_kr_ticker(tickers: str | list[str]) -> bool:
    """Check if ticker(s) are Korean market."""
    if isinstance(tickers, str):
        return tickers.endswith((".KS", ".KQ"))
    return any(t.endswith((".KS", ".KQ")) for t in tickers)


def _financedatareader_fallback(
    tickers: str | list[str],
    start: str | date,
    end: str | date,
) -> pd.DataFrame | None:
    """FinanceDataReader fallback for KR stocks.

    Returns None if FinanceDataReader is not installed.
    """
    try:
        import FinanceDataReader as fdr
    except ImportError:
        logger.debug("FinanceDataReader not installed, skipping fallback")
        return None

    try:
        ticker = tickers if isinstance(tickers, str) else tickers[0]
        # Remove .KS/.KQ suffix for FDR
        code = ticker.replace(".KS", "").replace(".KQ", "")
        df = fdr.DataReader(code, str(start), str(end))
        if df is not None and not df.empty:
            logger.info("FinanceDataReader fallback succeeded for %s", code)
            return df
    except Exception as e:
        logger.warning("FinanceDataReader fallback failed: %s", e)

    return None
