"""뉴스 수집 파이프라인 — 수집 → 전처리 → 분석 → 저장 → 발행."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.news_event import NewsEvent
from app.processing.article_scraper import ArticleScraper
from app.processing.dedup import deduplicate
from app.processing.sentiment import analyze_sentiment
from app.processing.stock_mapper import extract_stock_codes
from app.processing.summary import summarize_news
from app.processing.theme_classifier import classify_theme
from app.processing.us_stock_mapper import extract_tickers_from_text
from app.scoring.engine import (
    calc_disclosure,
    calc_frequency,
    calc_news_score,
    calc_recency,
    calc_sentiment_score,
)

logger = logging.getLogger(__name__)


async def _scrape_articles(items: list[dict]) -> dict[str, str | None]:
    """기사 본문 스크래핑. URL → body 매핑 반환."""
    scraper = ArticleScraper()
    results = await scraper.scrape_batch(items)
    return {url: result.body for url, result in results.items()}


def _map_stock_code(item: dict) -> str:
    """아이템에서 종목코드 추출/매핑."""
    # 이미 stock_code가 있으면 그대로 사용
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

    # 3. Redis 클라이언트 (속보 발행용)
    redis_client = _get_redis_client()

    saved_count = 0

    for item in unique_items:
        try:
            title = item.get("title", "")
            source_url = item.get("source_url", "")
            source = item.get("source", "unknown")
            is_disclosure = item.get("is_disclosure", False)
            published_at = item.get("published_at")

            # published_at 파싱
            if isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at)
                except (ValueError, TypeError):
                    published_at = None
            if published_at is None:
                published_at = datetime.now(timezone.utc)

            # 종목코드 매핑
            stock_code = _map_stock_code(item)
            stock_name = item.get("stock_name", "")

            # 기사 본문
            body = body_map.get(source_url)

            # 감성 분석 (Bedrock key 없으면 fallback)
            sentiment_result = analyze_sentiment(title, body)
            sentiment = sentiment_result["sentiment"]
            sentiment_score = sentiment_result["score"]

            # 테마 분류
            combined_text = title
            if body:
                combined_text += " " + body[:500]
            themes = classify_theme(combined_text)
            theme = ",".join(themes) if themes else None

            # 뉴스 요약
            summary = ""
            if body:
                summary = summarize_news(title, body)

            # 스코어 계산
            recency = calc_recency(published_at)
            frequency = calc_frequency(1)  # 단건 처리이므로 1
            sent_score = calc_sentiment_score(sentiment, sentiment_score)
            disc_score = calc_disclosure(is_disclosure)
            news_score = calc_news_score(recency, frequency, sent_score, disc_score)

            # DB 저장
            event = NewsEvent(
                market=market,
                stock_code=stock_code,
                stock_name=stock_name,
                title=title,
                summary=summary or None,
                content=body,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                news_score=news_score,
                source=source,
                source_url=source_url or None,
                theme=theme,
                is_disclosure=is_disclosure,
                published_at=published_at,
            )
            db.add(event)
            db.flush()  # ID 할당

            # 속보 발행
            if redis_client:
                from app.core.pubsub import publish_news_event as pub_event
                pub_event(redis_client, event, news_score)

            saved_count += 1

        except Exception as e:
            logger.warning("Pipeline item failed, skipping: %s — %s", item.get("title", "?")[:50], e)
            continue

    db.commit()
    logger.info("Pipeline complete: %d/%d items saved", saved_count, len(unique_items))

    if redis_client:
        try:
            redis_client.close()
        except Exception:
            pass

    return saved_count
