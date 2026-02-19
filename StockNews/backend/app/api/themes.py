"""테마 관련 REST 엔드포인트."""

import json
from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.limiter import limiter

from app.core.database import get_db
from app.models.news_event import NewsEvent
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
    """테마 강도 순위 조회 (news_event에서 실시간 집계, 복합 테마 분리).

    rise_index는 국내(KR)+국외(US) 뉴스를 모두 고려하여 0-100으로 산출.
    """
    # 1) 전체 뉴스 조회 (market 무관) — rise_index 계산용
    all_rows = db.query(
        NewsEvent.theme,
        NewsEvent.sentiment_score,
        NewsEvent.news_score,
        NewsEvent.market,
    ).filter(
        NewsEvent.theme.isnot(None),
        NewsEvent.theme != "",
    ).all()

    # 전체 데이터에서 테마별 KR/US 분리 집계
    global_data: dict[str, dict[str, list[tuple[float, float]]]] = {}
    for theme_str, sentiment_score, news_score, mkt in all_rows:
        for t in theme_str.split(","):
            t = t.strip()
            if not t:
                continue
            if t not in global_data:
                global_data[t] = {"KR": [], "US": []}
            key = mkt if mkt in ("KR", "US") else "KR"
            global_data[t][key].append((sentiment_score, news_score))

    # Also query US news with cross-market impact data
    us_impact_rows = db.query(
        NewsEvent.kr_impact_themes,
        NewsEvent.news_score,
    ).filter(
        NewsEvent.market == "US",
        NewsEvent.kr_impact_themes.isnot(None),
    ).all()

    # Incorporate US cross-market impacts into global data
    for kr_impact_json, news_score in us_impact_rows:
        try:
            impacts = json.loads(kr_impact_json)
            for imp in impacts:
                theme_name = imp.get("theme", "")
                impact_val = imp.get("impact", 0)
                direction = imp.get("direction", "neutral")
                if not theme_name:
                    continue
                if direction == "up":
                    sentiment = impact_val
                elif direction == "down":
                    sentiment = -impact_val
                else:
                    sentiment = 0.0
                if theme_name not in global_data:
                    global_data[theme_name] = {"KR": [], "US": []}
                global_data[theme_name]["US"].append((sentiment, news_score * impact_val))
        except (json.JSONDecodeError, TypeError):
            continue

    # rise_index 계산: KR 60% + US 40% 가중 (뉴스 없는 마켓은 0)
    def calc_rise_index(theme_key: str) -> float:
        d = global_data.get(theme_key, {"KR": [], "US": []})
        kr, us = d["KR"], d["US"]

        def market_score(items: list[tuple[float, float]]) -> float:
            if not items:
                return 0.0
            avg_sent = sum(s for s, _ in items) / len(items)
            avg_news = sum(n for _, n in items) / len(items)
            return avg_news * 0.6 + (avg_sent + 1) * 20

        kr_score = market_score(kr)
        us_score = market_score(us)

        # 가중 배합 (두 마켓 모두 데이터 있으면 KR 60% + US 40%)
        if kr and us:
            combined = kr_score * 0.6 + us_score * 0.4
        elif kr:
            combined = kr_score
        else:
            combined = us_score

        return round(min(100, max(0, combined)), 1)

    # 2) 마켓 필터 적용된 데이터로 표시 항목 구성
    theme_data: dict[str, list[tuple[float, float]]] = {}
    for theme_str, sentiment_score, news_score, mkt in all_rows:
        if market and mkt != market:
            continue
        for t in theme_str.split(","):
            t = t.strip()
            if not t:
                continue
            if t not in theme_data:
                theme_data[t] = []
            theme_data[t].append((sentiment_score, news_score))

    today = str(date.today())

    items = []
    for theme, scores in theme_data.items():
        news_count = len(scores)
        avg_sentiment = sum(s for s, _ in scores) / news_count
        avg_news_score = sum(n for _, n in scores) / news_count
        items.append(ThemeItem(
            theme=theme,
            strength_score=round(avg_news_score, 2),
            news_count=news_count,
            sentiment_avg=round(avg_sentiment, 3),
            rise_index=calc_rise_index(theme),
            date=today,
            market=market or "ALL",
        ))

    items.sort(key=lambda x: x.rise_index, reverse=True)
    return items[:limit]


@router.get("/news", response_model=dict)
@limiter.limit("60/minute")
async def get_theme_news(
    request: Request,
    response: Response,
    theme: str = Query(..., description="테마명"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """테마 관련 국내 뉴스 + 국외 영향 뉴스 조회."""
    from app.schemas.news import NewsItem

    # 1) 국내 뉴스: theme 컬럼에 해당 테마 포함
    kr_rows = (
        db.query(NewsEvent)
        .filter(NewsEvent.theme.ilike(f"%{theme}%"))
        .order_by(NewsEvent.published_at.desc())
        .limit(limit)
        .all()
    )

    kr_items = [
        NewsItem(
            id=r.id, title=r.title, stock_code=r.stock_code,
            stock_name=r.stock_name, sentiment=r.sentiment,
            sentiment_score=r.sentiment_score, news_score=r.news_score,
            source=r.source, source_url=r.source_url, market=r.market,
            theme=r.theme, summary=r.summary, published_at=r.published_at,
        )
        for r in kr_rows
    ]

    # 2) 국외 영향 뉴스: kr_impact_themes JSON에 해당 테마 포함
    us_rows = (
        db.query(NewsEvent)
        .filter(
            NewsEvent.market == "US",
            NewsEvent.kr_impact_themes.isnot(None),
            NewsEvent.kr_impact_themes.ilike(f"%{theme}%"),
        )
        .order_by(NewsEvent.published_at.desc())
        .limit(limit)
        .all()
    )

    us_items = []
    for r in us_rows:
        # 해당 테마의 impact 정보 추출
        impact_info = None
        try:
            impacts = json.loads(r.kr_impact_themes)
            for imp in impacts:
                if imp.get("theme") == theme:
                    impact_info = imp
                    break
        except (json.JSONDecodeError, TypeError):
            pass

        us_items.append({
            "id": r.id,
            "title": r.title,
            "stock_code": r.stock_code,
            "stock_name": r.stock_name,
            "sentiment": r.sentiment,
            "news_score": r.news_score,
            "source": r.source,
            "source_url": r.source_url,
            "market": r.market,
            "published_at": r.published_at,
            "impact": impact_info.get("impact", 0) if impact_info else 0,
            "direction": impact_info.get("direction", "neutral") if impact_info else "neutral",
        })

    return {
        "kr_news": kr_items,
        "kr_total": len(kr_items),
        "us_news": us_items,
        "us_total": len(us_items),
    }
