"""AdvanEvent 추출 — NewsEvent를 정규화된 이벤트로 변환."""

import logging
from datetime import date, datetime

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.advan.models import AdvanEvent
from app.models.news_event import NewsEvent

logger = logging.getLogger(__name__)

# 이벤트 타입 분류 키워드 매핑
EVENT_TYPE_KEYWORDS = {
    "실적": ["영업이익", "매출", "순이익", "실적", "분기", "반기", "연간", "어닝"],
    "가이던스": ["가이던스", "전망", "목표", "예상"],
    "수주": ["수주", "계약", "납품", "공급"],
    "증자": ["증자", "유상증자", "무상증자", "신주"],
    "소송": ["소송", "제소", "재판", "법원"],
    "규제": ["규제", "제재", "과징금", "벌금", "승인"],
    "경영권": ["경영권", "인수", "경영진", "대표이사", "CEO"],
    "자사주": ["자사주", "자기주식", "소각"],
    "배당": ["배당", "배당금", "주당"],
    "M&A": ["인수합병", "M&A", "합병", "인수"],
    "공급계약": ["공급계약", "납품계약"],
    "리콜": ["리콜", "회수"],
}


def _classify_event_type(title: str, summary: str | None) -> str:
    """뉴스 제목/요약에서 이벤트 타입 분류."""
    text = title.lower()
    if summary:
        text += " " + summary.lower()

    for event_type, keywords in EVENT_TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return event_type

    return "기타"


def _determine_direction(sentiment_score: float, is_disclosure: bool) -> str:
    """방향 결정 (positive/negative/mixed/unknown)."""
    # sentiment_score: -1.0 ~ 1.0
    if abs(sentiment_score) < 0.1:
        return "unknown"
    elif sentiment_score > 0.5:
        return "positive"
    elif sentiment_score < -0.5:
        return "negative"
    else:
        return "mixed"


def _calculate_magnitude(news_score: float) -> float:
    """규모 계산 (0~1 정규화). news_score는 0~100."""
    return min(max(news_score / 100.0, 0.0), 1.0)


def _calculate_credibility(is_disclosure: bool, source: str) -> float:
    """신뢰도 계산."""
    if is_disclosure:
        return 0.9
    elif source in ["naver", "rss"]:
        return 0.6
    else:
        return 0.4


def _is_after_market(published_at: datetime | None) -> bool:
    """장마감 후 발표 여부 (15:30 KST 이후).

    KST = UTC+9. 15:30 KST = 06:30 UTC.
    """
    if not published_at:
        return False
    # KST 기준으로 변환 (UTC+9)
    kst_hour = (published_at.hour + 9) % 24
    kst_minutes = kst_hour * 60 + published_at.minute
    return kst_minutes >= 15 * 60 + 30  # 15:30 KST = 930분


def _calculate_novelty(
    db: Session,
    ticker: str,
    event_type: str,
    event_timestamp: datetime,
) -> float:
    """Calculate novelty based on prior events for same ticker+event_type in last 7 days.

    First report → 0.9, second → 0.6, third+ → 0.3
    """
    from datetime import timedelta
    lookback = event_timestamp - timedelta(days=7)

    prior_count = (
        db.query(func.count(AdvanEvent.id))
        .filter(
            AdvanEvent.ticker == ticker,
            AdvanEvent.event_type == event_type,
            AdvanEvent.event_timestamp >= lookback,
            AdvanEvent.event_timestamp < event_timestamp,
        )
        .scalar()
    ) or 0

    if prior_count == 0:
        return 0.9
    elif prior_count == 1:
        return 0.6
    else:
        return 0.3


def _deduplicate_key(news: NewsEvent) -> str:
    """중복 제거 키 생성 (source_url 우선, 없으면 ticker+title 일부)."""
    if news.source_url:
        return news.source_url
    # 제목 앞 50자 + 종목 코드
    return f"{news.stock_code}:{news.title[:50]}"


def extract_events(
    db: Session,
    market: str,
    date_from: date | None = None,
    date_to: date | None = None,
    force_rebuild: bool = False,
) -> dict:
    """NewsEvent를 AdvanEvent로 추출.

    Args:
        db: DB 세션
        market: 시장 (KR/US)
        date_from: 시작일 (None이면 전체)
        date_to: 종료일 (None이면 전체)
        force_rebuild: True이면 기존 AdvanEvent 삭제 후 재생성

    Returns:
        {extracted_count, skipped_count, error_count}
    """
    if force_rebuild:
        # 기존 데이터 삭제
        conditions = [AdvanEvent.market == market]
        if date_from:
            conditions.append(AdvanEvent.event_timestamp >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            conditions.append(AdvanEvent.event_timestamp <= datetime.combine(date_to, datetime.max.time()))
        db.query(AdvanEvent).filter(and_(*conditions)).delete()
        db.commit()
        logger.info(f"force_rebuild: deleted existing AdvanEvent for market={market}")

    # NewsEvent 조회
    query = db.query(NewsEvent).filter(NewsEvent.market == market)
    if date_from:
        query = query.filter(NewsEvent.published_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(NewsEvent.published_at <= datetime.combine(date_to, datetime.max.time()))

    news_events = query.all()
    logger.info(f"Found {len(news_events)} NewsEvent records for market={market}")

    extracted_count = 0
    skipped_count = 0
    error_count = 0

    # 중복 제거 추적
    seen_keys = set()

    for news in news_events:
        try:
            # 중복 체크
            dedup_key = _deduplicate_key(news)
            if dedup_key in seen_keys:
                skipped_count += 1
                continue
            seen_keys.add(dedup_key)

            # 이미 추출된 이벤트 체크 (source_news_id)
            if not force_rebuild:
                existing = db.query(AdvanEvent).filter(AdvanEvent.source_news_id == news.id).first()
                if existing:
                    skipped_count += 1
                    continue

            # 이벤트 타입 분류
            event_type = _classify_event_type(news.title, news.summary)

            # 방향 결정
            direction = _determine_direction(news.sentiment_score, news.is_disclosure)

            # 규모 계산
            magnitude = _calculate_magnitude(news.news_score)

            # 신뢰도 계산
            credibility = _calculate_credibility(news.is_disclosure, news.source)

            # 장마감 후 여부
            is_after_market = _is_after_market(news.published_at)

            # AdvanEvent 생성
            advan_event = AdvanEvent(
                source_news_id=news.id,
                ticker=news.stock_code,
                stock_name=news.stock_name,
                market=news.market,
                event_type=event_type,
                direction=direction,
                magnitude=magnitude,
                magnitude_detail=None,  # 추후 확장 가능
                novelty=_calculate_novelty(db, news.stock_code, event_type, news.published_at or news.created_at),
                credibility=credibility,
                is_disclosure=news.is_disclosure,
                title=news.title,
                summary=news.summary,
                source=news.source,
                confounders=None,  # 추후 확장
                event_timestamp=news.published_at or news.created_at,
                is_after_market=is_after_market,
            )

            db.add(advan_event)
            extracted_count += 1

            # 배치 커밋 (100개마다)
            if extracted_count % 100 == 0:
                db.commit()
                logger.debug(f"Committed {extracted_count} events")

        except Exception as e:
            logger.error(f"Failed to extract event from NewsEvent.id={news.id}: {e}")
            error_count += 1

    # 최종 커밋
    db.commit()

    logger.info(
        f"Event extraction completed: extracted={extracted_count}, skipped={skipped_count}, errors={error_count}"
    )

    return {
        "extracted_count": extracted_count,
        "skipped_count": skipped_count,
        "error_count": error_count,
    }
