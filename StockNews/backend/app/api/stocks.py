"""종목 관련 REST 엔드포인트."""

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import cast, func, Date
from sqlalchemy.orm import Session
from app.core.limiter import limiter

from app.core.database import get_db
from app.models.news_event import NewsEvent
from app.schemas.common import TimelinePoint

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/{stock_code}/timeline", response_model=list[TimelinePoint])
@limiter.limit("60/minute")
async def get_stock_timeline(
    request: Request,
    response: Response,
    stock_code: str,
    days: int = Query(7, ge=1, le=90, description="조회 일수"),
    db: Session = Depends(get_db),
):
    """종목별 뉴스 스코어 타임라인."""
    results = (
        db.query(
            cast(NewsEvent.published_at, Date).label("date"),
            func.avg(NewsEvent.news_score).label("score"),
        )
        .filter(NewsEvent.stock_code == stock_code)
        .filter(NewsEvent.published_at.isnot(None))
        .group_by(cast(NewsEvent.published_at, Date))
        .order_by(cast(NewsEvent.published_at, Date).desc())
        .limit(days)
        .all()
    )

    return [
        TimelinePoint(date=str(r.date), score=round(r.score, 2))
        for r in results
    ]
