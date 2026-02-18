"""StockNews REST + Redis 클라이언트"""

import logging
import time
from typing import Optional

import httpx

logger = logging.getLogger("stockagent.core.news")


class NewsClient:
    """StockNews REST API 뉴스 점수 조회 (캐싱 지원)"""

    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        cache_ttl: int = 0,
    ):
        self._base_url = base_url
        self._cache_ttl = cache_ttl
        self._cache: dict[str, tuple[int, float]] = {}  # code -> (score, timestamp)

    async def get_score(self, stock_code: str) -> int:
        """종목 뉴스 점수 조회 (0~100). 서비스 다운 시 0 반환."""
        # 캐시 확인
        if self._cache_ttl > 0 and stock_code in self._cache:
            score, cached_at = self._cache[stock_code]
            if time.time() - cached_at < self._cache_ttl:
                return score

        try:
            async with httpx.AsyncClient(base_url=self._base_url) as client:
                resp = await client.get(
                    "/api/v1/news/score",
                    params={"stock": stock_code},
                )

            if resp.status_code != 200:
                logger.warning(
                    "뉴스 점수 조회 실패: code=%s, status=%d",
                    stock_code, resp.status_code,
                )
                return 0

            data = resp.json()
            score = data.get("news_score", 0)

            # 캐시 저장
            if self._cache_ttl > 0:
                self._cache[stock_code] = (score, time.time())

            return score

        except (httpx.HTTPError, Exception) as e:
            logger.error("뉴스 서비스 연결 실패: %s", e)
            return 0
