"""테마 관련 REST 엔드포인트."""

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session
from app.core.limiter import limiter

from app.core.database import get_db
from app.models.theme_strength import ThemeStrength
from app.schemas.theme import ThemeItem

router = APIRouter(prefix="/theme", tags=["theme"])


@router.get("/strength", response_model=list[ThemeItem])
@limiter.limit("60/minute")
async def get_theme_strength(
    request: Request,
    response: Response,
    market: str | None = Query(None, description="마켓 필터 (KR/US)"),
    limit: int = Query(20, ge=1, le=100, description="최대 건수"),
    db: Session = Depends(get_db),
):
    """테마 강도 순위 조회."""
    query = db.query(ThemeStrength)

    if market:
        query = query.filter(ThemeStrength.market == market)

    results = (
        query.order_by(ThemeStrength.strength_score.desc())
        .limit(limit)
        .all()
    )

    return [
        ThemeItem(
            theme=r.theme,
            strength_score=r.strength_score,
            news_count=r.news_count,
            sentiment_avg=r.sentiment_avg,
            date=str(r.date),
            market=r.market,
        )
        for r in results
    ]
