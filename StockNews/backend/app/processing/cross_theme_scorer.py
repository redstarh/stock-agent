"""Cross-Theme Scorer — 동일 테마 타 종목 평균 뉴스 스코어.

종목의 테마 내 상대적 위치를 파악하여 ML 피처로 활용.
"""

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.news_event import NewsEvent

logger = logging.getLogger(__name__)


def calc_cross_theme_score(
    db: Session,
    theme: str | None,
    stock_code: str,
    market: str,
    target_date: date,
    lookback_days: int = 7,
) -> float:
    """동일 테마 타 종목 평균 뉴스 스코어 (자기 자신 제외).

    Args:
        db: Database session
        theme: 종목의 테마 (None이면 0.0 반환)
        stock_code: 제외할 종목 코드 (자기 자신)
        market: 시장 (KR/US)
        target_date: 대상 날짜
        lookback_days: 뉴스 조회 기간 (기본 7일)

    Returns:
        동일 테마 타 종목 평균 뉴스 스코어 (0-100). 데이터 없으면 0.0.
    """
    if not theme:
        return 0.0

    cutoff_start = datetime.combine(target_date - timedelta(days=lookback_days), datetime.min.time())
    cutoff_end = datetime.combine(target_date, datetime.max.time())

    result = (
        db.query(func.avg(NewsEvent.news_score))
        .filter(
            NewsEvent.theme == theme,
            NewsEvent.market == market,
            NewsEvent.stock_code != stock_code,
            NewsEvent.created_at >= cutoff_start,
            NewsEvent.created_at <= cutoff_end,
        )
        .scalar()
    )

    if result is None:
        return 0.0

    return round(float(result), 2)


def calc_cross_theme_scores_batch(
    db: Session,
    market: str,
    target_date: date,
    lookback_days: int = 7,
) -> dict[str, float]:
    """시장 전체 종목에 대한 cross_theme_score 일괄 계산.

    Returns:
        {stock_code: cross_theme_score, ...}
    """
    cutoff_start = datetime.combine(target_date - timedelta(days=lookback_days), datetime.min.time())
    cutoff_end = datetime.combine(target_date, datetime.max.time())

    # Get all distinct stock_code + theme pairs for target date range
    stocks = (
        db.query(
            NewsEvent.stock_code,
            NewsEvent.theme,
        )
        .filter(
            NewsEvent.market == market,
            NewsEvent.created_at >= cutoff_start,
            NewsEvent.created_at <= cutoff_end,
            NewsEvent.theme.isnot(None),
        )
        .distinct()
        .all()
    )

    result = {}
    for stock_code, theme in stocks:
        score = calc_cross_theme_score(db, theme, stock_code, market, target_date, lookback_days)
        result[stock_code] = score

    return result
