"""뉴스 수집 파이프라인 — 수집 → 전처리 → 분석 → 저장 → 발행.

스트리밍 방식: 건별로 스크래핑→분석→저장을 동시 처리하여
첫 번째 결과가 빠르게 나오고, 전체 대기 시간을 줄입니다.
"""

import asyncio
import contextlib
import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.collectors.quality_tracker import ItemResult, tracker
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

# 동시 처리 상한 (스크래핑 + LLM 합산)
PIPELINE_CONCURRENCY = 10

# ── Fast-path 키워드: 제목만으로 속보 판단 (LLM 이전) ──────────────
# {keyword: (sentiment, estimated_news_score)}
# 점수는 breaking threshold(80) 이상으로 설정하여 즉시 발행.
_FAST_PATH_KR: dict[str, tuple[str, float]] = {
    "파산": ("negative", 90.0),
    "상장폐지": ("negative", 90.0),
    "분식회계": ("negative", 88.0),
    "횡령": ("negative", 85.0),
    "적자전환": ("negative", 82.0),
    "사상 최대": ("positive", 85.0),
    "흑자전환": ("positive", 82.0),
    "액면분할": ("positive", 80.0),
}

_FAST_PATH_US: dict[str, tuple[str, float]] = {
    "bankruptcy": ("negative", 90.0),
    "fraud": ("negative", 88.0),
    "delisting": ("negative", 88.0),
    "record revenue": ("positive", 85.0),
    "all-time high": ("positive", 82.0),
    "beats expectations": ("positive", 80.0),
}


def _fast_path_check(title: str, market: str) -> tuple[str, float] | None:
    """제목 키워드로 속보 여부를 빠르게 판단 (LLM 호출 전).

    강한 시그널 키워드가 제목에 포함되면 즉시 속보 발행을 위해
    추정 sentiment와 news_score를 반환합니다.

    Returns:
        (sentiment, estimated_score) 또는 None (매칭 없음)
    """
    keywords = _FAST_PATH_US if market == "US" else _FAST_PATH_KR
    title_search = title.lower() if market == "US" else title

    for keyword, (sentiment, score) in keywords.items():
        if keyword in title_search:
            return (sentiment, score)
    return None


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


def _prepare_item(item: dict, market: str) -> dict:
    """수집 아이템을 파이프라인용 dict로 전처리."""
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

    return {
        "title": title,
        "source_url": source_url,
        "source": source,
        "is_disclosure": is_disclosure,
        "published_at": published_at,
        "stock_code": stock_code,
        "stock_name": stock_name,
    }


async def _process_single_item(
    item: dict,
    market: str,
    db: Session,
    scraper: ArticleScraper,
    redis_client,
    semaphore: asyncio.Semaphore,
) -> bool:
    """단일 아이템의 전체 파이프라인 (스크래핑→분석→저장→발행).

    Returns:
        저장 성공 시 True
    """
    async with semaphore:
        p = _prepare_item(item, market)

        # 0. Fast-path: 키워드 기반 속보 즉시 발행 (스크래핑/LLM 이전)
        if redis_client and p["stock_code"]:
            fast = _fast_path_check(p["title"], market)
            if fast:
                sentiment_est, score_est = fast
                from app.core.pubsub import publish_breaking_news
                publish_breaking_news(
                    redis_client=redis_client,
                    stock_code=p["stock_code"],
                    title=p["title"],
                    score=score_est,
                    market=market,
                    stock_name=p["stock_name"],
                    sentiment_score=0.7 if sentiment_est == "positive" else -0.7,
                )
                logger.info(
                    "Fast-path breaking: %s (score=%.0f)",
                    p["title"][:50], score_est,
                )

        # 1. 스크래핑
        try:
            scrape_result = await scraper.scrape_one(
                p["source_url"], item.get("source", ""),
            )
            body = scrape_result.body
        except Exception as e:
            logger.warning("Scrape failed for %s: %s", p["source_url"][:60], e)
            body = None

        # 2. LLM 분석 (sync → async via to_thread)
        try:
            analysis = await asyncio.to_thread(analyze_news, p["title"], body, market)
        except Exception as e:
            logger.warning("LLM analysis failed: %s", e)
            analysis = {
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "themes": [],
                "summary": "",
                "kr_impact_themes": [],
            }

        # 3. 스코어링 + 저장 + 발행
        try:
            sentiment = analysis["sentiment"]
            sentiment_score = analysis["sentiment_score"]
            themes = analysis["themes"]
            theme = ",".join(themes) if themes else None
            summary = analysis["summary"]
            kr_impact_json = (
                json.dumps(analysis.get("kr_impact_themes", []), ensure_ascii=False)
                if analysis.get("kr_impact_themes")
                else None
            )

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
                content=body,
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

            # Quality tracking
            tracker.record(ItemResult(
                source=p["source"],
                market=market,
                scrape_ok=body is not None,
                llm_confidence=analysis.get("confidence", 0.0),
                sentiment=sentiment,
                news_score=news_score,
                timestamp=datetime.now(UTC),
            ))

            if redis_client:
                from app.core.pubsub import publish_news_event as pub_event
                pub_event(redis_client, event, news_score)

            return True

        except Exception as e:
            logger.warning("Pipeline save failed: %s — %s", p["title"][:50], e)
            tracker.record(ItemResult(
                source=p["source"],
                market=market,
                scrape_ok=body is not None,
                llm_confidence=analysis.get("confidence", 0.0),
                sentiment=analysis.get("sentiment", "neutral"),
                news_score=0.0,
                timestamp=datetime.now(UTC),
            ))
            return False


async def process_collected_items(
    db: Session,
    items: list[dict],
    market: str = "KR",
) -> int:
    """수집된 뉴스 아이템을 스트리밍 파이프라인 처리.

    건별로 스크래핑→분석→저장을 동시 처리합니다.
    Semaphore로 동시 처리 수를 제한합니다.

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

    # 2. 스트리밍 처리 (건별 동시: 스크래핑→분석→저장)
    scraper = ArticleScraper()
    redis_client = _get_redis_client()
    semaphore = asyncio.Semaphore(PIPELINE_CONCURRENCY)

    tasks = [
        _process_single_item(item, market, db, scraper, redis_client, semaphore)
        for item in unique_items
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    saved_count = sum(1 for r in results if r is True)

    db.commit()
    logger.info("Pipeline complete: %d/%d items saved", saved_count, len(unique_items))

    if redis_client:
        with contextlib.suppress(Exception):
            redis_client.close()

    return saved_count
