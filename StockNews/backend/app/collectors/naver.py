"""네이버 뉴스 검색 크롤러."""

import asyncio
import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

NAVER_SEARCH_URL = "https://search.naver.com/search.naver"


class NaverCollector:
    """네이버 뉴스 검색 수집기."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def collect(
        self,
        query: str,
        stock_code: str | None = None,
        market: str = "KR",
    ) -> list[dict]:
        """뉴스 검색 후 파싱된 리스트 반환."""
        params = {"where": "news", "query": query, "sm": "tab_jum"}

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(NAVER_SEARCH_URL, params=params)
                    resp.raise_for_status()

                soup = BeautifulSoup(resp.text, "html.parser")
                seen_urls: set[str] = set()
                items = []

                for a_tag in soup.find_all("a", attrs={"data-heatmap-target": ".tit"}):
                    href = a_tag.get("href", "")
                    title = a_tag.get_text(strip=True)
                    if not title or not href or href in seen_urls:
                        continue
                    seen_urls.add(href)
                    items.append({
                        "title": title,
                        "source_url": href,
                        "source": "naver",
                        "market": market,
                        "stock_code": stock_code or "",
                    })

                return items

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.warning("Naver collect attempt %d failed: %s", attempt + 1, e)
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                continue

        logger.error("Naver collect failed after %d retries", self.max_retries)
        return []
