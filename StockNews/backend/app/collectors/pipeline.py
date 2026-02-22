"""뉴스 수집 파이프라인 — 수집 → 전처리 → 분석 → 저장 → 발행."""

import contextlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.news_event import NewsEvent
from app.processing.article_scraper import ArticleScraper
from app.processing.dedup import deduplicate
from app.processing.stock_mapper import code_to_name, extract_stock_codes
from app.processing.unified_analyzer import analyze_news
from app.processing.us_stock_mapper import extract_tickers_from_text
from app.scoring.engine import (
    calc_disclosure,
    calc_frequency,
    calc_news_score,
    calc_recency,
    calc_sentiment_score,
)

logger = logging.getLogger(__name__)

# LLM 병렬 호출 워커 수
LLM_MAX_WORKERS = 10


async def _scrape_articles(items: list[dict]) -> dict[str, str | None]:
    """기사 본문 스크래핑. URL → body 매핑 반환."""
    scraper = ArticleScraper()
    results = await scraper.scrape_batch(items)
    return {url: result.body for url, result in results.items()}


def _map_stock_code(item: dict) -> str:
    """아이템에서 종목코드 추출/매핑."""
    if item.get("stock_code"):
        return item["stock_code"]

    title = item.get("title", "")
    market = item.get("market", "KR")

    if market == "US":
        tickers = extract_tickers_from_text(title)
        return tickers[0] if tickers else ""
    else:
        codes = extract_stock_codes(title)
        return codes[0] if codes else ""


def _get_news_frequency(db: Session, stock_code: str) -> int:
    """해당 종목의 최근 24시간 뉴스 건수 조회."""
    if not stock_code:
        return 1
    try:
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        count = db.query(sa_func.count(NewsEvent.id)).filter(
            NewsEvent.stock_code == stock_code,
            NewsEvent.published_at >= cutoff,
        ).scalar()
        return max(1, count or 1)
    except Exception as e:
        logger.warning("Frequency query failed: %s", e)
        return 1


def _get_redis_client():
    """Redis 클라이언트 생성. 연결 실패 시 None 반환."""
    try:
        import redis
        client = redis.from_url(settings.redis_url)
        client.ping()
        return client
    except Exception as e:
        logger.warning("Redis unavailable, skipping pub/sub: %s", e)
        return None


def _analyze_single(title: str, body: str | None, market: str = "KR") -> dict:
    """단일 아이템의 통합 LLM 분석 (1회 호출). Thread-safe."""
    return analyze_news(title, body, market)


async def process_collected_items(
    db: Session,
    items: list[dict],
    market: str = "KR",
) -> int:
    """수집된 뉴스 아이템을 파이프라인 처리.

    Args:
        db: SQLAlchemy 세션
        items: 수집기 출력 딕셔너리 리스트
        market: 시장 구분 (KR/US)

    Returns:
        저장된 뉴스 건수
    """
    if not items:
        return 0

    logger.info("Pipeline start: %d items (market=%s)", len(items), market)

    # 1. 중복 제거
    unique_items = deduplicate(db, items)
    logger.info("After dedup: %d items", len(unique_items))
    if not unique_items:
        return 0

    # 2. 기사 본문 스크래핑
    body_map = await _scrape_articles(unique_items)

    # 3. 전처리 (종목코드, 본문, 날짜 등)
    prepared = []
    for item in unique_items:
        title = item.get("title", "")
        source_url = item.get("source_url", "")
        source = item.get("source", "unknown")
        is_disclosure = item.get("is_disclosure", False)
        published_at = item.get("published_at")

        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at)
            except (ValueError, TypeError):
                published_at = None
        if published_at is None:
            published_at = datetime.now(UTC)

        stock_code = _map_stock_code(item)
        stock_name = item.get("stock_name", "")
        if not stock_name and stock_code:
            market_val = item.get("market", market)
            if market_val == "US":
                from app.processing.us_stock_mapper import ticker_to_name
                stock_name = ticker_to_name(stock_code) or ""
            else:
                stock_name = code_to_name(stock_code)

        body = body_map.get(source_url)

        prepared.append({
            "title": title,
            "source_url": source_url,
            "source": source,
            "is_disclosure": is_disclosure,
            "published_at": published_at,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "body": body,
        })

    # 4. LLM 분석 (병렬)
    logger.info("Starting parallel LLM analysis (%d workers)...", LLM_MAX_WORKERS)
    analysis_results: list[dict | None] = [None] * len(prepared)

    with ThreadPoolExecutor(max_workers=LLM_MAX_WORKERS) as executor:
        future_to_idx = {}
        for idx, p in enumerate(prepared):
            future = executor.submit(_analyze_single, p["title"], p["body"], market)
            future_to_idx[future] = idx

        for done_count, future in enumerate(as_completed(future_to_idx), 1):
            idx = future_to_idx[future]
            try:
                analysis_results[idx] = future.result()
            except Exception as e:
                logger.warning("LLM analysis failed for item %d: %s", idx, e)
                analysis_results[idx] = {
                    "sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "themes": [],
                    "summary": "",
                    "kr_impact_themes": [],
                }
            if done_count % 50 == 0:
                logger.info("LLM progress: %d/%d", done_count, len(prepared))

    logger.info("LLM analysis complete.")

    # 5. DB 저장 + 속보 발행
    redis_client = _get_redis_client()
    saved_count = 0

    for p, analysis in zip(prepared, analysis_results, strict=False):
        try:
            sentiment = analysis["sentiment"]
            sentiment_score = analysis["sentiment_score"]
            themes = analysis["themes"]
            theme = ",".join(themes) if themes else None
            summary = analysis["summary"]
            kr_impact_json = json.dumps(analysis.get("kr_impact_themes", []), ensure_ascii=False) if analysis.get("kr_impact_themes") else None

            recency = calc_recency(p["published_at"])
            news_count = _get_news_frequency(db, p["stock_code"])
            frequency = calc_frequency(news_count)
            sent_score = calc_sentiment_score(sentiment, sentiment_score)
            disc_score = calc_disclosure(p["is_disclosure"])
            news_score = calc_news_score(recency, frequency, sent_score, disc_score)

            event = NewsEvent(
                market=market,
                stock_code=p["stock_code"],
                stock_name=p["stock_name"],
                title=p["title"],
                summary=summary or None,
                content=p["body"],
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                news_score=news_score,
                source=p["source"],
                source_url=p["source_url"] or None,
                theme=theme,
                kr_impact_themes=kr_impact_json,
                is_disclosure=p["is_disclosure"],
                published_at=p["published_at"],
            )
            db.add(event)
            db.flush()

            if redis_client:
                from app.core.pubsub import publish_news_event as pub_event
                pub_event(redis_client, event, news_score)

            saved_count += 1

        except Exception as e:
            logger.warning("Pipeline save failed: %s — %s", p["title"][:50], e)
            continue

    db.commit()
    logger.info("Pipeline complete: %d/%d items saved", saved_count, len(unique_items))

    if redis_client:
        with contextlib.suppress(Exception):
            redis_client.close()

    return saved_count
