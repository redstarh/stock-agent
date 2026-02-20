"""뉴스 관련 REST 엔드포인트."""

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.core.limiter import limiter
from app.models.news_event import NewsEvent
from app.schemas.news import NewsItem, NewsListResponse, NewsScoreResponse, NewsTopItem

router = APIRouter(
    prefix="/news",
    tags=["news"],
    dependencies=[Depends(verify_api_key)],
)


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

    # Top 3 themes
    themes = [r.theme for r in rows if r.theme]
    theme_counts = {}
    for theme in themes:
        theme_counts[theme] = theme_counts.get(theme, 0) + 1
    top_themes = sorted(theme_counts.keys(), key=lambda t: theme_counts[t], reverse=True)[:3]

    # Updated at: max published_at
    updated_at = max((r.published_at for r in rows if r.published_at), default=None)

    # 감성별 건수
    positive_count = sum(1 for r in rows if r.sentiment == "positive")
    negative_count = sum(1 for r in rows if r.sentiment == "negative")
    neutral_count = len(rows) - positive_count - negative_count

    return NewsScoreResponse(
        stock_code=stock,
        stock_name=stock_name,
        news_score=round(avg_score, 2),
        recency=round(recency, 2),
        frequency=frequency,
        sentiment_score=round(avg_sentiment, 2),
        disclosure=disclosure,
        news_count=len(rows),
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
        top_themes=top_themes,
        updated_at=updated_at,
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
            func.avg(NewsEvent.sentiment_score).label("avg_sentiment"),
            func.max(NewsEvent.sentiment).label("sentiment"),
            func.count(NewsEvent.id).label("cnt"),
            NewsEvent.market,
        )
        .filter(NewsEvent.market == market)
        .group_by(NewsEvent.stock_code, NewsEvent.stock_name, NewsEvent.market)
        .all()
    )

    # Calculate prediction scores and sort by them
    items = []
    for r in results:
        avg_score = r.avg_score or 0.0
        avg_sentiment = r.avg_sentiment or 0.0

        # Same heuristic as prediction.py
        prediction_score = min(100, max(0, avg_score * 0.6 + (avg_sentiment + 1) * 20))

        if prediction_score > 60:
            direction = "up"
        elif prediction_score < 40:
            direction = "down"
        else:
            direction = "neutral"

        items.append(
            NewsTopItem(
                stock_code=r.stock_code,
                stock_name=r.stock_name,
                news_score=round(avg_score, 2),
                sentiment=r.sentiment,
                news_count=r.cnt,
                market=r.market,
                prediction_score=round(prediction_score, 1),
                direction=direction,
            )
        )

    # Sort by prediction_score descending and limit
    items.sort(key=lambda x: x.prediction_score or 0, reverse=True)
    return items[:limit]


@router.get("/latest", response_model=NewsListResponse)
@limiter.limit("60/minute")
async def get_latest_news(
    request: Request,
    response: Response,
    market: str | None = Query(None, description="마켓 필터 (KR/US)"),
    stock: str | None = Query(None, description="종목 코드/이름 검색"),
    sentiment: str | None = Query(None, description="감성 필터 (positive/neutral/negative)"),
    theme: str | None = Query(None, description="테마 필터"),
    date_from: str | None = Query(None, description="시작일 (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="종료일 (YYYY-MM-DD)"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """최신 뉴스 리스트 (페이지네이션)."""
    query = db.query(NewsEvent)

    if market:
        query = query.filter(NewsEvent.market == market)

    if stock:
        search_term = f"%{stock}%"
        query = query.filter(
            (NewsEvent.stock_code.ilike(search_term))
            | (NewsEvent.stock_name.ilike(search_term))
        )

    if sentiment:
        query = query.filter(NewsEvent.sentiment == sentiment)

    if theme:
        theme_term = f"%{theme}%"
        query = query.filter(NewsEvent.theme.ilike(theme_term))

    if date_from:
        from datetime import datetime

        date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        query = query.filter(func.date(NewsEvent.published_at) >= date_from_obj)

    if date_to:
        from datetime import datetime

        date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        query = query.filter(func.date(NewsEvent.published_at) <= date_to_obj)

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
                summary=row.summary,
                published_at=row.published_at,
            )
            for row in items
        ],
        total=total,
        offset=offset,
        limit=limit,
    )
