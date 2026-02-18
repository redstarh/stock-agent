"""APScheduler 기반 뉴스 수집 스케줄러."""

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_INTERVAL_MINUTES = 1

# Top 10 Korean stocks for Naver search
KR_SEARCH_QUERIES = [
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


def _collect_kr_news_job():
    """한국 뉴스 수집 작업 (Naver)."""
    logger.info("Korean news collection started")

    async def _run():
        from app.collectors.naver import NaverCollector
        from app.collectors.pipeline import process_collected_items
        from app.core.database import SessionLocal

        collector = NaverCollector()
        all_items = []

        for query, stock_code in KR_SEARCH_QUERIES:
            try:
                items = await collector.collect(query=query, stock_code=stock_code, market="KR")
                all_items.extend(items)
            except Exception as e:
                logger.warning("Naver collect failed for %s: %s", query, e)

        if all_items:
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


def create_scheduler() -> BackgroundScheduler:
    """수집 스케줄러 생성 및 job 등록."""
    scheduler = BackgroundScheduler()

    # Korean news collection job
    scheduler.add_job(
        _collect_kr_news_job,
        trigger=IntervalTrigger(minutes=settings.collection_interval_kr),
        id="kr_news_collection",
        name="Korean News Collection Job",
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
