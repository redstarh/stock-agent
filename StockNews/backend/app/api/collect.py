"""수동 뉴스 수집 트리거 API."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.schemas.collect import (
    CollectionQualityResponse,
    QualitySummary,
    SourceQualityStats,
    StockCollectRequest,
    StockCollectResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/collect",
    tags=["collect"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/kr")
@limiter.limit("30/minute")
async def collect_kr_news(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
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


@router.post("/stock", response_model=StockCollectResponse)
@limiter.limit("10/minute")
async def collect_stock_news(
    request: Request,
    response: Response,
    body: StockCollectRequest,
    db: Session = Depends(get_db),
):
    """종목별 수동 뉴스 수집.

    특정 종목에 대해 즉시 뉴스를 수집합니다.
    add_to_scope=true이면 일일 수집 대상에도 추가합니다.
    """
    from app.collectors.pipeline import process_collected_items

    all_items = []

    if body.market == "KR":
        from app.collectors.naver import NaverCollector

        collector = NaverCollector()
        try:
            items = await collector.collect(
                query=body.query, stock_code=body.stock_code, market="KR"
            )
            all_items.extend(items)
        except Exception as e:
            logger.warning("Manual KR collect failed for %s: %s", body.query, e)
    elif body.market == "US":
        from app.collectors.finnhub import FinnhubCollector

        if not settings.finnhub_api_key:
            return StockCollectResponse(
                status="skipped",
                query=body.query,
                stock_code=body.stock_code,
                collected=0,
                saved=0,
                added_to_scope=False,
            )
        collector = FinnhubCollector()
        try:
            items = await collector.collect_company_news(symbol=body.stock_code)
            all_items.extend(items)
        except Exception as e:
            logger.warning("Manual US collect failed for %s: %s", body.stock_code, e)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported market: {body.market}")

    saved = 0
    if all_items:
        saved = await process_collected_items(db, all_items, market=body.market)

    added_to_scope = False
    if body.add_to_scope:
        from app.core.scope_loader import reload_scope
        from app.core.scope_writer import add_korean_stock, add_kr_search_query, add_us_stock

        if body.market == "KR":
            added_q = add_kr_search_query(body.query, body.stock_code)
            added_s = add_korean_stock(body.query, body.stock_code)
            added_to_scope = added_q or added_s
        elif body.market == "US":
            added_to_scope = add_us_stock(body.stock_code, body.query)

        if added_to_scope:
            reload_scope()

    return StockCollectResponse(
        status="ok",
        query=body.query,
        stock_code=body.stock_code,
        collected=len(all_items),
        saved=saved,
        added_to_scope=added_to_scope,
    )


@router.post("/us")
@limiter.limit("30/minute")
async def collect_us_news(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
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
@limiter.limit("30/minute")
async def get_collect_status(request: Request, response: Response):
    """스케줄러 상태 조회."""
    try:

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


@router.post("/analyze-cross-market")
@limiter.limit("30/minute")
async def analyze_cross_market(
    request: Request,
    response: Response,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """기존 US 뉴스의 한국 시장 영향 재분석 (Bedrock Claude)."""
    import json as _json
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from app.models.news_event import NewsEvent
    from app.processing.cross_market import analyze_kr_impact

    us_news = (
        db.query(NewsEvent)
        .filter(
            NewsEvent.market == "US",
            NewsEvent.kr_impact_themes.is_(None),
        )
        .limit(limit)
        .all()
    )

    if not us_news:
        return {"message": "No US news to analyze", "analyzed": 0}

    analyzed = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_news = {
            executor.submit(analyze_kr_impact, n.title, n.content): n
            for n in us_news
        }
        for future in as_completed(future_to_news):
            news = future_to_news[future]
            try:
                impacts = future.result()
                if impacts:
                    news.kr_impact_themes = _json.dumps(impacts, ensure_ascii=False)
                    analyzed += 1
            except Exception as e:
                logger.warning("Re-analysis failed for %s: %s", news.title[:30], e)

    db.commit()
    return {"message": f"Analyzed {analyzed}/{len(us_news)} US news", "analyzed": analyzed}


@router.post("/reclassify-themes")
@limiter.limit("30/minute")
async def reclassify_themes(
    request: Request,
    response: Response,
    limit: int = Query(500, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """기존 뉴스 테마를 LLM(Sonnet)으로 재분류 (병렬 처리)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from app.models.news_event import NewsEvent
    from app.processing.llm_theme_classifier import classify_theme_llm

    model_id = settings.bedrock_model_id  # Opus (분류 정확도 최고)

    news_list = (
        db.query(NewsEvent)
        .order_by(NewsEvent.created_at.desc())
        .limit(limit)
        .all()
    )

    if not news_list:
        return {"message": "No news to reclassify", "reclassified": 0}

    def _classify(news_item):
        themes = classify_theme_llm(news_item.title, news_item.content, model_id=model_id)
        return news_item, themes

    reclassified = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_classify, n) for n in news_list]
        for done, future in enumerate(as_completed(futures), 1):
            try:
                news, themes = future.result()
                new_theme = ",".join(themes) if themes else None
                if news.theme != new_theme:
                    news.theme = new_theme
                    reclassified += 1
            except Exception as e:
                logger.warning("Reclassify failed: %s", e)
            if done % 50 == 0:
                logger.info("Reclassify progress: %d/%d", done, len(news_list))

    db.commit()
    return {
        "message": f"Reclassified {reclassified}/{len(news_list)} news",
        "total": len(news_list),
        "changed": reclassified,
    }


@router.get("/quality", response_model=CollectionQualityResponse)
@limiter.limit("60/minute")
async def get_collection_quality(request: Request, response: Response):
    """소스별 수집 품질 메트릭 조회."""
    from app.collectors.quality_tracker import tracker

    summary = tracker.get_summary()
    sources = tracker.get_all_stats()

    return CollectionQualityResponse(
        summary=QualitySummary(**summary),
        sources={k: SourceQualityStats(**v) for k, v in sources.items()},
    )
