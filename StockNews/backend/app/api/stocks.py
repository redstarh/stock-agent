"""종목 관련 REST 엔드포인트."""

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.core.limiter import limiter
from app.models.news_event import NewsEvent
from app.schemas.common import TimelinePoint

router = APIRouter(
    prefix="/stocks",
    tags=["stocks"],
    dependencies=[Depends(verify_api_key)],
)


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
    date_col = func.date(NewsEvent.published_at)
    results = (
        db.query(
            date_col.label("date"),
            func.avg(NewsEvent.news_score).label("score"),
        )
        .filter(NewsEvent.stock_code == stock_code)
        .filter(NewsEvent.published_at.isnot(None))
        .group_by(date_col)
        .order_by(date_col.desc())
        .limit(days)
        .all()
    )

    return [
        TimelinePoint(date=str(r.date), score=round(r.score, 2))
        for r in results
    ]
