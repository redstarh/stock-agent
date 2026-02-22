"""예측 검증 스케줄러."""

import asyncio
import logging
from datetime import date

from apscheduler.triggers.cron import CronTrigger

from app.core.database import SessionLocal
from app.processing.theme_aggregator import aggregate_theme_accuracy
from app.processing.verification_engine import run_verification

logger = logging.getLogger(__name__)


def _verify_kr_job():
    """한국 시장 검증 (15:35 KST)."""
    logger.info("KR market verification started")
    target = date.today()  # Verify today's close

    async def _run():
        db = SessionLocal()
        try:
            log = await run_verification(db, target, "KR")
            if log.status != "failed":
                aggregate_theme_accuracy(db, target, "KR")
                try:
                    from app.processing.prediction_context_builder import (
                        build_and_save_prediction_context,
                    )
                    build_and_save_prediction_context(db, days=30)
                    logger.info("KR prediction context rebuilt")
                except Exception as e:
                    logger.warning("Failed to rebuild prediction context after KR verification: %s", e)
            logger.info(
                "KR verification: %s (verified=%d, failed=%d)",
                log.status,
                log.stocks_verified,
                log.stocks_failed,
            )
        finally:
            db.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error("KR verification failed: %s", e)


def _verify_us_job():
    """미국 시장 검증 (16:30 EST)."""
    logger.info("US market verification started")
    target = date.today()

    async def _run():
        db = SessionLocal()
        try:
            log = await run_verification(db, target, "US")
            if log.status != "failed":
                aggregate_theme_accuracy(db, target, "US")
                try:
                    from app.processing.prediction_context_builder import (
                        build_and_save_prediction_context,
                    )
                    build_and_save_prediction_context(db, days=30)
                    logger.info("US prediction context rebuilt")
                except Exception as e:
                    logger.warning("Failed to rebuild prediction context after US verification: %s", e)
            logger.info(
                "US verification: %s (verified=%d, failed=%d)",
                log.status,
                log.stocks_verified,
                log.stocks_failed,
            )
        finally:
            db.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error("US verification failed: %s", e)


def register_verification_jobs(scheduler):
    """Register verification jobs with existing scheduler."""
    # KR: 15:35 KST (06:35 UTC)
    scheduler.add_job(
        _verify_kr_job,
        trigger=CronTrigger(day_of_week="mon-fri", hour=6, minute=35),
        id="kr_verification",
        name="KR Market Verification",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    # US: 16:30 EST (21:30 UTC)
    scheduler.add_job(
        _verify_us_job,
        trigger=CronTrigger(day_of_week="mon-fri", hour=21, minute=30),
        id="us_verification",
        name="US Market Verification",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    logger.info("Verification scheduler jobs registered")
