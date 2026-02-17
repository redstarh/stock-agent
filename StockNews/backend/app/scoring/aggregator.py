"""종목별/테마별 뉴스 집계."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.news_event import NewsEvent


def aggregate_by_stock(db: Session, market: str) -> list[dict]:
    """종목별 뉴스 집계 — 평균 스코어, 뉴스 수, 감성 평균."""
    results = (
        db.query(
            NewsEvent.stock_code,
            NewsEvent.stock_name,
            func.avg(NewsEvent.news_score).label("avg_score"),
            func.count(NewsEvent.id).label("news_count"),
            func.avg(NewsEvent.sentiment_score).label("sentiment_avg"),
        )
        .filter(NewsEvent.market == market)
        .group_by(NewsEvent.stock_code, NewsEvent.stock_name)
        .order_by(func.avg(NewsEvent.news_score).desc())
        .all()
    )

    return [
        {
            "stock_code": r.stock_code,
            "stock_name": r.stock_name,
            "avg_score": round(r.avg_score, 2),
            "news_count": r.news_count,
            "sentiment_avg": round(r.sentiment_avg, 2),
        }
        for r in results
    ]


def aggregate_by_theme(db: Session, market: str) -> list[dict]:
    """테마별 뉴스 집계 — 강도 점수, 뉴스 수, 감성 평균."""
    results = (
        db.query(
            NewsEvent.theme,
            func.avg(NewsEvent.news_score).label("strength_score"),
            func.count(NewsEvent.id).label("news_count"),
            func.avg(NewsEvent.sentiment_score).label("sentiment_avg"),
        )
        .filter(NewsEvent.market == market)
        .filter(NewsEvent.theme.isnot(None))
        .filter(NewsEvent.theme != "")
        .group_by(NewsEvent.theme)
        .order_by(func.avg(NewsEvent.news_score).desc())
        .all()
    )

    return [
        {
            "theme": r.theme,
            "strength_score": round(r.strength_score, 2),
            "news_count": r.news_count,
            "sentiment_avg": round(r.sentiment_avg, 2),
        }
        for r in results
    ]
