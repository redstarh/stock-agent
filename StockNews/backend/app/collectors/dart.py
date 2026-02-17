"""DART 공시 API 수집기."""

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

DART_API_URL = "https://opendart.fss.or.kr/api/list.json"


class DartCollector:
    """DART 전자공시 수집기."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def collect(self, begin_date: str | None = None) -> list[dict]:
        """최근 공시 목록 수집."""
        if not begin_date:
            begin_date = datetime.now(timezone.utc).strftime("%Y%m%d")

        params = {
            "crtfc_key": self.api_key,
            "bgn_de": begin_date,
            "page_count": "100",
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(DART_API_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error("DART API request failed: %s", e)
            return []

        if data.get("status") != "000":
            logger.warning("DART API error: %s", data.get("message", "unknown"))
            return []

        items = []
        for entry in data.get("list", []):
            rcept_dt = entry.get("rcept_dt", "")

            item = {
                "title": entry.get("report_nm", ""),
                "stock_code": entry.get("stock_code", ""),
                "stock_name": entry.get("corp_name", ""),
                "source": "dart",
                "source_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={entry.get('rcept_no', '')}",
                "market": "KR",
                "is_disclosure": True,
                "published_at": _parse_dart_date(rcept_dt),
            }
            items.append(item)

        return items


def _parse_dart_date(date_str: str) -> datetime | None:
    """DART 날짜 문자열 → datetime 변환."""
    if not date_str or len(date_str) != 8:
        return None
    try:
        return datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
