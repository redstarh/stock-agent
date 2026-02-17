"""네이버 뉴스 검색 크롤러."""

import asyncio
import logging
from html.parser import HTMLParser

import httpx

logger = logging.getLogger(__name__)

NAVER_SEARCH_URL = "https://search.naver.com/search.naver"


class _NewsListParser(HTMLParser):
    """네이버 뉴스 검색 결과 HTML에서 뉴스 항목 추출."""

    def __init__(self):
        super().__init__()
        self.items: list[dict] = []
        self._in_news_tit = False
        self._current: dict = {}

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "a" and "news_tit" in attr_dict.get("class", ""):
            self._in_news_tit = True
            self._current = {
                "source_url": attr_dict.get("href", ""),
                "title": attr_dict.get("title", ""),
            }

    def handle_endtag(self, tag):
        if tag == "a" and self._in_news_tit:
            self._in_news_tit = False
            if self._current.get("title"):
                self.items.append(self._current)
            self._current = {}


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

                parser = _NewsListParser()
                parser.feed(resp.text)

                items = []
                for raw in parser.items:
                    item = {
                        "title": raw["title"],
                        "source_url": raw["source_url"],
                        "source": "naver",
                        "market": market,
                        "stock_code": stock_code or "",
                    }
                    items.append(item)

                return items

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.warning("Naver collect attempt %d failed: %s", attempt + 1, e)
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                continue

        logger.error("Naver collect failed after %d retries", self.max_retries)
        return []
