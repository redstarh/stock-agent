"""RSS 피드 수집기."""

import contextlib
import logging
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import httpx

logger = logging.getLogger(__name__)


class RssCollector:
    """RSS 피드 파서."""

    async def collect(
        self,
        feed_url: str,
        source_name: str = "rss",
        market: str = "KR",
    ) -> list[dict]:
        """RSS 피드 수집 후 뉴스 리스트 반환."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(feed_url)
                resp.raise_for_status()

            return self._parse_feed(resp.text, source_name, market)

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error("RSS fetch failed for %s: %s", feed_url, e)
            return []

    def _parse_feed(self, xml_text: str, source_name: str, market: str) -> list[dict]:
        """RSS XML → 뉴스 항목 리스트."""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning("Malformed RSS XML, returning empty list")
            return []

        items = []
        for item_el in root.iter("item"):
            title = item_el.findtext("title", "")
            link = item_el.findtext("link", "")
            pub_date = item_el.findtext("pubDate", "")
            description = item_el.findtext("description", "")

            published_at = None
            if pub_date:
                with contextlib.suppress(ValueError, TypeError):
                    published_at = parsedate_to_datetime(pub_date)

            items.append({
                "title": title,
                "source_url": link,
                "source": source_name,
                "market": market,
                "stock_code": "",
                "summary": description,
                "published_at": published_at,
            })

        return items
