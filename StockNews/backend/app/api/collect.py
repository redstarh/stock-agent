"""수동 뉴스 수집 트리거 API."""

import asyncio
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collect", tags=["collect"])


@router.post("/kr")
async def collect_kr_news(db: Session = Depends(get_db)):
    """한국 뉴스 즉시 수집."""
    from app.collectors.naver import NaverCollector
    from app.collectors.pipeline import process_collected_items

    KR_QUERIES = [
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

    collector = NaverCollector()
    all_items = []

    for query, stock_code in KR_QUERIES:
        try:
            items = await collector.collect(query=query, stock_code=stock_code, market="KR")
            all_items.extend(items)
        except Exception as e:
            logger.warning("Naver collect failed for %s: %s", query, e)

    saved = 0
    if all_items:
        saved = await process_collected_items(db, all_items, market="KR")

    return {"status": "ok", "collected": len(all_items), "saved": saved}


@router.post("/us")
async def collect_us_news(db: Session = Depends(get_db)):
    """미국 뉴스 즉시 수집."""
    from app.collectors.finnhub import FinnhubCollector
    from app.collectors.pipeline import process_collected_items

    if not settings.finnhub_api_key:
        return {"status": "skipped", "reason": "FINNHUB_API_KEY not configured"}

    collector = FinnhubCollector()
    items = await collector.collect()

    saved = 0
    if items:
        saved = await process_collected_items(db, items, market="US")

    return {"status": "ok", "collected": len(items), "saved": saved}


@router.get("/status")
async def get_collect_status():
    """스케줄러 상태 조회."""
    try:
        from app.collectors.scheduler import create_scheduler
        from apscheduler.schedulers.background import BackgroundScheduler

        # Note: This returns the scheduler config, not running state
        # Running state would require access to the app's scheduler instance
        return {
            "status": "ok",
            "jobs": [
                {
                    "id": "kr_news_collection",
                    "name": "Korean News Collection",
                    "interval_minutes": settings.collection_interval_kr,
                },
                {
                    "id": "dart_disclosure_collection",
                    "name": "DART Disclosure Collection",
                    "interval_minutes": settings.collection_interval_dart,
                },
                {
                    "id": "us_news_collection",
                    "name": "US News Collection",
                    "interval_minutes": settings.collection_interval_us,
                },
            ],
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
