"""NewsAPI 뉴스 수집기."""

import asyncio
import logging

import httpx

from app.core.config import settings
from app.processing.us_stock_mapper import extract_tickers_from_text

logger = logging.getLogger(__name__)

NEWSAPI_BASE_URL = "https://newsapi.org/v2"


class NewsAPICollector:
    """NewsAPI.org 수집기."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.api_key = settings.newsapi_api_key

    async def collect(
        self,
        query: str = "stock market",
        language: str = "en",
        page_size: int = 20,
    ) -> list[dict]:
        """뉴스 검색."""
        if not self.api_key:
            logger.warning("NewsAPI key not set, skipping")
            return []

        params = {
            "q": query,
            "language": language,
            "pageSize": page_size,
            "sortBy": "publishedAt",
            "apiKey": self.api_key,
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"{NEWSAPI_BASE_URL}/everything", params=params
                    )
                    resp.raise_for_status()

                data = resp.json()
                articles = data.get("articles", [])
                items = []
                for article in articles:
                    title = article.get("title", "")
                    tickers = extract_tickers_from_text(title)
                    stock_code = tickers[0] if tickers else ""

                    items.append({
                        "title": title,
                        "source_url": article.get("url", ""),
                        "source": f"newsapi:{article.get('source', {}).get('name', '')}",
                        "market": "US",
                        "stock_code": stock_code,
                        "published_at": article.get("publishedAt"),
                    })

                return items

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.warning("NewsAPI attempt %d failed: %s", attempt + 1, e)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.base_delay * (2 ** attempt))

        logger.error("NewsAPI collect failed after %d retries", self.max_retries)
        return []
