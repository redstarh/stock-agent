"""APScheduler 기반 뉴스 수집 스케줄러."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

COLLECTION_INTERVAL_MINUTES = 5


def _collect_news_job():
    """뉴스 수집 작업 (스케줄러에서 호출)."""
    logger.info("Scheduled news collection started")
    # 실제 수집 로직은 collectors를 호출 (MVP에서는 placeholder)


def create_scheduler() -> BackgroundScheduler:
    """수집 스케줄러 생성 및 job 등록."""
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        _collect_news_job,
        trigger=IntervalTrigger(minutes=COLLECTION_INTERVAL_MINUTES),
        id="news_collection",
        name="News Collection Job",
        replace_existing=True,
    )

    return scheduler
