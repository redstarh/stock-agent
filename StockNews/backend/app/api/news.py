"""뉴스 관련 REST 엔드포인트."""

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.limiter import limiter

from app.core.database import get_db
from app.models.news_event import NewsEvent
from app.schemas.news import NewsItem, NewsListResponse, NewsScoreResponse, NewsTopItem

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/score", response_model=NewsScoreResponse)
@limiter.limit("60/minute")
async def get_news_score(
    request: Request,
    response: Response,
    stock: str = Query(..., description="종목 코드"),
    db: Session = Depends(get_db),
):
    """종목별 뉴스 스코어 조회."""
    rows = db.query(NewsEvent).filter(NewsEvent.stock_code == stock).all()

    if not rows:
        return NewsScoreResponse(stock_code=stock)

    total_score = sum(r.news_score for r in rows)
    avg_score = total_score / len(rows) if rows else 0.0
    avg_sentiment = sum(r.sentiment_score for r in rows) / len(rows) if rows else 0.0

    # 최신성: 최근 뉴스일수록 높은 점수 (MVP: 단순 평균)
    recency = avg_score
    frequency = float(len(rows))
    disclosure = sum(1.0 for r in rows if r.is_disclosure)

    stock_name = rows[0].stock_name if rows else None

    return NewsScoreResponse(
        stock_code=stock,
        stock_name=stock_name,
        news_score=round(avg_score, 2),
        recency=round(recency, 2),
        frequency=frequency,
        sentiment_score=round(avg_sentiment, 2),
        disclosure=disclosure,
        news_count=len(rows),
    )


@router.get("/top", response_model=list[NewsTopItem])
@limiter.limit("60/minute")
async def get_top_news(
    request: Request,
    response: Response,
    market: str = Query(..., description="마켓 (KR/US)"),
    limit: int = Query(10, ge=1, le=50, description="최대 건수"),
    db: Session = Depends(get_db),
):
    """마켓별 Top 종목 뉴스 조회."""
    results = (
        db.query(
            NewsEvent.stock_code,
            NewsEvent.stock_name,
            func.avg(NewsEvent.news_score).label("avg_score"),
            func.max(NewsEvent.sentiment).label("sentiment"),
            func.count(NewsEvent.id).label("cnt"),
            NewsEvent.market,
        )
        .filter(NewsEvent.market == market)
        .group_by(NewsEvent.stock_code, NewsEvent.stock_name, NewsEvent.market)
        .order_by(func.avg(NewsEvent.news_score).desc())
        .limit(limit)
        .all()
    )

    return [
        NewsTopItem(
            stock_code=r.stock_code,
            stock_name=r.stock_name,
            news_score=round(r.avg_score, 2),
            sentiment=r.sentiment,
            news_count=r.cnt,
            market=r.market,
        )
        for r in results
    ]


@router.get("/latest", response_model=NewsListResponse)
@limiter.limit("60/minute")
async def get_latest_news(
    request: Request,
    response: Response,
    market: str | None = Query(None, description="마켓 필터 (KR/US)"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """최신 뉴스 리스트 (페이지네이션)."""
    query = db.query(NewsEvent)

    if market:
        query = query.filter(NewsEvent.market == market)

    total = query.count()
    items = (
        query.order_by(NewsEvent.published_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return NewsListResponse(
        items=[
            NewsItem(
                id=row.id,
                title=row.title,
                stock_code=row.stock_code,
                stock_name=row.stock_name,
                sentiment=row.sentiment,
                news_score=row.news_score,
                source=row.source,
                source_url=row.source_url,
                market=row.market,
                theme=row.theme,
                content=row.content,
                published_at=row.published_at,
            )
            for row in items
        ],
        total=total,
        offset=offset,
        limit=limit,
    )
