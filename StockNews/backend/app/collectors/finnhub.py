"""Finnhub News API 수집기."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import httpx

from app.core.config import settings
from app.core.scope_loader import load_scope
from app.processing.us_stock_mapper import extract_tickers_from_text

logger = logging.getLogger(__name__)

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# Scope에서 기본 카테고리 로드
_scope = load_scope()
_FINNHUB_CATEGORY = _scope.get("us_market", {}).get("finnhub", {}).get("category", "general")


class FinnhubCollector:
    """Finnhub 뉴스 수집기."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.api_key = settings.finnhub_api_key

    async def collect(self, category: str = _FINNHUB_CATEGORY, min_id: int = 0) -> list[dict]:
        """Finnhub general/market news 수집."""
        if not self.api_key:
            logger.warning("Finnhub API key not set, skipping")
            return []

        params = {
            "category": category,
            "token": self.api_key,
            "minId": min_id,
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{FINNHUB_BASE_URL}/news", params=params)
                    resp.raise_for_status()

                raw_items = resp.json()
                items = []
                for raw in raw_items:
                    tickers = extract_tickers_from_text(raw.get("headline", ""))
                    stock_code = tickers[0] if tickers else ""

                    published_at = None
                    if raw.get("datetime"):
                        published_at = datetime.fromtimestamp(
                            raw["datetime"], tz=UTC
                        ).isoformat()

                    items.append({
                        "title": raw.get("headline", ""),
                        "source_url": raw.get("url", ""),
                        "source": f"finnhub:{raw.get('source', '')}",
                        "market": "US",
                        "stock_code": stock_code,
                        "published_at": published_at,
                    })

                return items

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.warning("Finnhub attempt %d failed: %s", attempt + 1, e)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.base_delay * (2 ** attempt))

        logger.error("Finnhub collect failed after %d retries", self.max_retries)
        return []

    async def collect_company_news(
        self, symbol: str, from_date: str | None = None, to_date: str | None = None
    ) -> list[dict]:
        """특정 종목 뉴스 수집."""
        if not self.api_key:
            return []

        today = datetime.now(UTC)
        if not to_date:
            to_date = today.strftime("%Y-%m-%d")
        if not from_date:
            from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")

        params = {
            "symbol": symbol,
            "from": from_date,
            "to": to_date,
            "token": self.api_key,
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"{FINNHUB_BASE_URL}/company-news", params=params
                    )
                    resp.raise_for_status()

                raw_items = resp.json()
                items = []
                for raw in raw_items:
                    published_at = None
                    if raw.get("datetime"):
                        published_at = datetime.fromtimestamp(
                            raw["datetime"], tz=UTC
                        ).isoformat()

                    items.append({
                        "title": raw.get("headline", ""),
                        "source_url": raw.get("url", ""),
                        "source": f"finnhub:{raw.get('source', '')}",
                        "market": "US",
                        "stock_code": symbol,
                        "published_at": published_at,
                    })

                return items

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.warning("Finnhub company news attempt %d failed: %s", attempt + 1, e)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.base_delay * (2 ** attempt))

        return []
