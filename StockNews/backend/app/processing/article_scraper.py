"""기사 본문 스크래핑 모듈.

source_url을 따라가서 기사 본문 텍스트를 추출.
beautifulsoup4 + httpx 기반.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MAX_BODY_LENGTH = 3000
REQUEST_TIMEOUT = 10.0
MAX_CONCURRENT_REQUESTS = 5
SKIP_SOURCES = {"dart"}

# 주요 뉴스 사이트별 본문 CSS 선택자
SITE_SELECTORS: dict[str, str] = {
    "news.naver.com": "#dic_area",
    "n.news.naver.com": "#newsct_article",
    "www.hankyung.com": "#articletxt",
    "www.mk.co.kr": "#article_body",
    "biz.chosun.com": "#news_body_id",
    "www.sedaily.com": ".article_view",
    "www.edaily.co.kr": ".news_body",
}

REMOVE_TAGS = ["script", "style", "iframe", "nav", "header", "footer", "aside", "figure", "figcaption"]

FALLBACK_SELECTORS = [
    "article",
    '[itemprop="articleBody"]',
    ".article-body",
    ".article_body",
    ".news_body",
    ".article-content",
    "#article-body",
    "#content",
    "main",
]

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) StockNews/1.0"


@dataclass
class ScrapeResult:
    """스크래핑 결과."""
    url: str
    body: str | None
    error: str | None = None


class ArticleScraper:
    """비동기 기사 본문 스크래퍼."""

    def __init__(
        self,
        max_concurrent: int = MAX_CONCURRENT_REQUESTS,
        timeout: float = REQUEST_TIMEOUT,
        max_body_length: int = MAX_BODY_LENGTH,
    ):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.timeout = timeout
        self.max_body_length = max_body_length

    async def scrape_one(self, url: str, source: str = "") -> ScrapeResult:
        """단일 URL에서 기사 본문 추출."""
        base_source = source.split(":")[0]
        if base_source in SKIP_SOURCES:
            return ScrapeResult(url=url, body=None, error="skipped_source")

        if not url:
            return ScrapeResult(url=url, body=None, error="empty_url")

        async with self.semaphore:
            try:
                html = await self._fetch(url)
                body = self._extract_body(html, url)
                if body:
                    body = body[:self.max_body_length]
                return ScrapeResult(url=url, body=body)
            except httpx.TimeoutException:
                logger.warning("Scrape timeout: %s", url)
                return ScrapeResult(url=url, body=None, error="timeout")
            except httpx.HTTPStatusError as e:
                logger.warning("Scrape HTTP %d: %s", e.response.status_code, url)
                return ScrapeResult(url=url, body=None, error=f"http_{e.response.status_code}")
            except Exception as e:
                logger.warning("Scrape failed for %s: %s", url, e)
                return ScrapeResult(url=url, body=None, error=str(e))

    async def scrape_batch(self, items: list[dict]) -> dict[str, ScrapeResult]:
        """배치 스크래핑. items는 collector 출력 dict 리스트.

        Returns:
            {source_url: ScrapeResult} 매핑
        """
        tasks = []
        for item in items:
            url = item.get("source_url", "")
            source = item.get("source", "")
            tasks.append(self.scrape_one(url, source))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        mapping: dict[str, ScrapeResult] = {}
        for item, result in zip(items, results, strict=False):
            url = item.get("source_url", "")
            if isinstance(result, Exception):
                mapping[url] = ScrapeResult(url=url, body=None, error=str(result))
            else:
                mapping[url] = result

        return mapping

    async def _fetch(self, url: str) -> str:
        """URL에서 HTML 가져오기."""
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                raise ValueError(f"Non-HTML content: {content_type}")

            return resp.text

    def _extract_body(self, html: str, url: str) -> str | None:
        """HTML에서 본문 텍스트 추출."""
        soup = BeautifulSoup(html, "html.parser")

        for tag_name in REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        hostname = urlparse(url).hostname or ""
        if hostname in SITE_SELECTORS:
            element = soup.select_one(SITE_SELECTORS[hostname])
            if element:
                return self._clean_text(element.get_text())

        for selector in FALLBACK_SELECTORS:
            element = soup.select_one(selector)
            if element:
                text = self._clean_text(element.get_text())
                if len(text) > 100:
                    return text

        paragraphs = soup.find_all("p")
        if paragraphs:
            combined = "\n".join(
                self._clean_text(p.get_text()) for p in paragraphs
            )
            if len(combined) > 100:
                return combined

        return None

    @staticmethod
    def _clean_text(text: str) -> str:
        """텍스트 정리: 연속 공백/줄바꿈 제거."""
        text = re.sub(r"\s+", " ", text)
        return text.strip()
