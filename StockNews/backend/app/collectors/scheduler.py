"""APScheduler 기반 뉴스 수집 스케줄러."""

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.scope_loader import load_scope

logger = logging.getLogger(__name__)

COLLECTION_INTERVAL_MINUTES = 1

# 기본값 (scope 파일 미존재 시 fallback)
_DEFAULT_KR_SEARCH_QUERIES = [
    ("삼성전자", "005930"),
    ("SK하이닉스", "000660"),
    ("현대차", "005380"),
    ("NAVER", "035420"),
    ("카카오", "035720"),
    ("LG에너지솔루션", "373220"),
    ("셀트리온", "068270"),
    ("삼성바이오로직스", "207940"),
    ("기아", "000270"),
    ("POSCO홀딩스", "005490"),
]


def _load_kr_search_queries() -> list[tuple[str, str]]:
    """Scope 파일에서 검색 쿼리 로드. 실패 시 기본값 사용."""
    scope = load_scope()
    queries = scope.get("korean_market", {}).get("search_queries", [])
    if queries:
        return [(q["query"], q["stock_code"]) for q in queries]
    return _DEFAULT_KR_SEARCH_QUERIES


KR_SEARCH_QUERIES = _load_kr_search_queries()


def _collect_kr_news_job():
    """한국 뉴스 통합 수집 작업 (Naver + RSS 병합 후 단일 파이프라인).

    여러 수집기 결과를 병합하여 교차 수집기 URL/제목 중복을 제거합니다.
    """
    logger.info("Korean news collection started (merged)")

    async def _run():
        from app.collectors.naver import NaverCollector
        from app.collectors.pipeline import process_collected_items
        from app.core.database import SessionLocal

        all_items: list[dict] = []

        # 1. Naver 수집
        naver = NaverCollector()
        for query, stock_code in KR_SEARCH_QUERIES:
            try:
                items = await naver.collect(query=query, stock_code=stock_code, market="KR")
                all_items.extend(items)
            except Exception as e:
                logger.warning("Naver collect failed for %s: %s", query, e)

        # 2. KR RSS 수집 (설정된 경우)
        feeds = _load_rss_feeds("korean")
        if feeds:
            from app.collectors.rss import RssCollector
            rss = RssCollector()
            for feed in feeds:
                try:
                    items = await rss.collect(
                        feed_url=feed["url"],
                        source_name=feed.get("source_name", "rss"),
                        market=feed.get("market", "KR"),
                    )
                    all_items.extend(items)
                except Exception as e:
                    logger.warning("RSS collect failed for %s: %s", feed["url"], e)

        # 3. 병합된 아이템을 단일 파이프라인으로 처리
        if all_items:
            logger.info("Korean merged: %d items from all sources", len(all_items))
            db = SessionLocal()
            try:
                count = await process_collected_items(db, all_items, market="KR")
                logger.info("Korean news: %d items saved", count)
            finally:
                db.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error("Korean news collection failed: %s", e)


def _collect_dart_disclosure_job():
    """DART 공시 수집 작업."""
    if not settings.dart_api_key:
        logger.debug("DART API key not set, skipping")
        return

    logger.info("DART disclosure collection started")

    async def _run():
        from app.collectors.dart import DartCollector
        from app.collectors.pipeline import process_collected_items
        from app.core.database import SessionLocal

        collector = DartCollector(api_key=settings.dart_api_key)
        items = await collector.collect()

        if items:
            db = SessionLocal()
            try:
                count = await process_collected_items(db, items, market="KR")
                logger.info("DART disclosures: %d items saved", count)
            finally:
                db.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error("DART disclosure collection failed: %s", e)


def _collect_us_news_job():
    """미국 뉴스 수집 작업 (Finnhub)."""
    if not settings.finnhub_api_key:
        logger.debug("Finnhub API key not set, skipping US news collection")
        return

    logger.info("US news collection started")

    async def _run():
        from app.collectors.finnhub import FinnhubCollector
        from app.collectors.pipeline import process_collected_items
        from app.core.database import SessionLocal

        collector = FinnhubCollector()
        items = await collector.collect()

        if items:
            db = SessionLocal()
            try:
                count = await process_collected_items(db, items, market="US")
                logger.info("US news: %d items saved", count)
            finally:
                db.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error("US news collection failed: %s", e)


def _load_rss_feeds(market_key: str) -> list[dict]:
    """Scope 파일에서 RSS 피드 목록 로드."""
    scope = load_scope()
    return scope.get("rss_feeds", {}).get(market_key, [])


def _collect_rss_job(market_key: str):
    """RSS 피드 수집 작업."""
    feeds = _load_rss_feeds(market_key)
    if not feeds:
        logger.debug("No RSS feeds configured for %s, skipping", market_key)
        return

    market = "KR" if market_key == "korean" else "US"
    logger.info("RSS collection started: %s (%d feeds)", market_key, len(feeds))

    async def _run():
        from app.collectors.pipeline import process_collected_items
        from app.collectors.rss import RssCollector
        from app.core.database import SessionLocal

        collector = RssCollector()
        all_items = []

        for feed in feeds:
            try:
                items = await collector.collect(
                    feed_url=feed["url"],
                    source_name=feed.get("source_name", "rss"),
                    market=feed.get("market", market),
                )
                all_items.extend(items)
            except Exception as e:
                logger.warning("RSS collect failed for %s: %s", feed["url"], e)

        if all_items:
            db = SessionLocal()
            try:
                count = await process_collected_items(db, all_items, market=market)
                logger.info("RSS %s: %d items saved", market_key, count)
            finally:
                db.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error("RSS %s collection failed: %s", market_key, e)


def create_scheduler() -> BackgroundScheduler:
    """수집 스케줄러 생성 및 job 등록."""
    scheduler = BackgroundScheduler()

    # Korean news collection job (Naver + RSS 통합)
    scheduler.add_job(
        _collect_kr_news_job,
        trigger=IntervalTrigger(minutes=settings.collection_interval_kr),
        id="kr_news_collection",
        name="Korean News Collection Job (Merged)",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=30,
    )

    # DART disclosure collection job
    scheduler.add_job(
        _collect_dart_disclosure_job,
        trigger=IntervalTrigger(minutes=settings.collection_interval_dart),
        id="dart_disclosure_collection",
        name="DART Disclosure Collection Job",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=30,
    )

    # US news collection job
    scheduler.add_job(
        _collect_us_news_job,
        trigger=IntervalTrigger(minutes=settings.collection_interval_us),
        id="us_news_collection",
        name="US News Collection Job",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=30,
    )

    return scheduler
