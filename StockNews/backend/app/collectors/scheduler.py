"""APScheduler 기반 뉴스 수집 스케줄러."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_INTERVAL_MINUTES = 1


def _collect_kr_news_job():
    """한국 뉴스 수집 작업 (Naver/RSS)."""
    logger.info("kr_news_collection: Korean news collection started")
    # 실제 수집 로직은 collectors를 호출 (MVP에서는 placeholder)


def _collect_dart_disclosure_job():
    """DART 공시 수집 작업."""
    logger.info("dart_disclosure_collection: DART disclosure collection started")
    # 실제 수집 로직은 collectors를 호출 (MVP에서는 placeholder)


def _collect_us_news_job():
    """미국 뉴스 수집 작업 (Finnhub/NewsAPI)."""
    logger.info("us_news_collection: US news collection started")
    # 실제 수집 로직은 collectors를 호출 (MVP에서는 placeholder)


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
