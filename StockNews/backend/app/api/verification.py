"""예측 검증 API 엔드포인트."""

import asyncio
import logging
from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.core.limiter import limiter
from app.models.verification import (
    DailyPredictionResult,
    ThemePredictionAccuracy,
    VerificationRunLog,
)
from app.processing.theme_aggregator import aggregate_theme_accuracy
from app.processing.verification_engine import run_verification
from app.schemas.verification import (
    AccuracyResponse,
    DailyResultItem,
    DailyTrend,
    DailyVerificationResponse,
    DirectionDetail,
    DirectionStats,
    MarketStatus,
    StockHistoryPoint,
    StockHistoryResponse,
    ThemeAccuracyItem,
    ThemeAccuracyResponse,
    ThemeTrendPoint,
    ThemeTrendResponse,
    VerificationRunResponse,
    VerificationStatusResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/verification",
    tags=["verification"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("/daily", response_model=DailyVerificationResponse)
@limiter.limit("60/minute")
async def get_daily_results(
    request: Request,
    response: Response,
    target_date: str = Query(..., alias="date", description="YYYY-MM-DD"),
    market: str | None = Query(None, description="KR or US (optional, default=ALL)"),
    db: Session = Depends(get_db),
):
    """일별 검증 결과 조회."""
    d = date.fromisoformat(target_date)
    query = db.query(DailyPredictionResult).filter(DailyPredictionResult.prediction_date == d)

    if market:
        query = query.filter(DailyPredictionResult.market == market)

    rows = query.all()
    results = [
        DailyResultItem(
            stock_code=r.stock_code,
            stock_name=r.stock_name,
            predicted_direction=r.predicted_direction,
            predicted_score=r.predicted_score,
            confidence=r.confidence,
            actual_direction=r.actual_direction,
            actual_change_pct=r.actual_change_pct,
            is_correct=r.is_correct,
            news_count=r.news_count,
            error_message=r.error_message,
        )
        for r in rows
    ]
    total = len(rows)
    correct = sum(1 for r in rows if r.is_correct is True)
    accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0
    return DailyVerificationResponse(
        date=d,
        market=market or "ALL",
        total=total,
        correct=correct,
        accuracy=accuracy,
        results=results,
    )


@router.get("/accuracy", response_model=AccuracyResponse)
@limiter.limit("60/minute")
async def get_accuracy_summary(
    request: Request,
    response: Response,
    market: str | None = Query(None, description="KR or US (optional, default=ALL)"),
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
):
    """전체 정확도 요약 조회."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    query = db.query(DailyPredictionResult).filter(
        DailyPredictionResult.prediction_date >= start_date,
        DailyPredictionResult.prediction_date <= end_date,
        DailyPredictionResult.is_correct.isnot(None),
    )

    if market:
        query = query.filter(DailyPredictionResult.market == market)

    rows = query.all()

    empty_detail = DirectionDetail(total=0, correct=0, accuracy=0.0)

    if not rows:
        return AccuracyResponse(
            period_days=days,
            market=market or "ALL",
            overall_accuracy=None,
            total_predictions=0,
            correct_predictions=0,
            by_direction=DirectionStats(
                up=empty_detail, down=empty_detail, neutral=empty_detail
            ),
            daily_trend=[],
        )

    total_predictions = len(rows)
    correct_predictions = sum(1 for r in rows if r.is_correct)
    overall_accuracy = (correct_predictions / total_predictions) * 100 if total_predictions > 0 else 0.0

    up_rows = [r for r in rows if r.predicted_direction == "up"]
    down_rows = [r for r in rows if r.predicted_direction == "down"]
    neutral_rows = [r for r in rows if r.predicted_direction == "neutral"]

    def _direction_detail(direction_rows: list) -> DirectionDetail:
        total = len(direction_rows)
        correct = sum(1 for r in direction_rows if r.is_correct)
        accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0
        return DirectionDetail(total=total, correct=correct, accuracy=accuracy)

    daily_map: dict[date, list[DailyPredictionResult]] = {}
    for r in rows:
        daily_map.setdefault(r.prediction_date, []).append(r)

    daily_trend = []
    for d in sorted(daily_map.keys()):
        day_rows = daily_map[d]
        day_correct = sum(1 for r in day_rows if r.is_correct)
        day_accuracy = round((day_correct / len(day_rows)) * 100, 1) if day_rows else 0.0
        daily_trend.append(
            DailyTrend(
                date=d,
                accuracy=day_accuracy,
                total=len(day_rows),
            )
        )

    return AccuracyResponse(
        period_days=days,
        market=market or "ALL",
        overall_accuracy=round(overall_accuracy, 1),
        total_predictions=total_predictions,
        correct_predictions=correct_predictions,
        by_direction=DirectionStats(
            up=_direction_detail(up_rows),
            down=_direction_detail(down_rows),
            neutral=_direction_detail(neutral_rows),
        ),
        daily_trend=daily_trend,
    )


@router.get("/themes", response_model=ThemeAccuracyResponse)
@limiter.limit("60/minute")
async def get_theme_accuracy(
    request: Request,
    response: Response,
    target_date: str = Query(..., alias="date", description="YYYY-MM-DD"),
    market: str | None = Query(None, description="KR or US (optional, default=ALL)"),
    db: Session = Depends(get_db),
):
    """테마별 정확도 조회."""
    d = date.fromisoformat(target_date)
    query = db.query(ThemePredictionAccuracy).filter(
        ThemePredictionAccuracy.prediction_date == d
    )

    if market:
        query = query.filter(ThemePredictionAccuracy.market == market)

    rows = query.all()

    themes = [
        ThemeAccuracyItem(
            theme=r.theme,
            market=r.market,
            total_stocks=r.total_stocks,
            correct_count=r.correct_count,
            accuracy_rate=round(r.accuracy_rate * 100, 1),
            avg_predicted_score=r.avg_predicted_score,
            avg_actual_change_pct=r.avg_actual_change_pct,
            rise_index=r.rise_index_at_prediction,
        )
        for r in rows
    ]

    return ThemeAccuracyResponse(
        market=market or "ALL",
        date=d,
        themes=themes,
    )


@router.get("/themes/trend", response_model=ThemeTrendResponse)
@limiter.limit("60/minute")
async def get_theme_trend(
    request: Request,
    response: Response,
    theme: str = Query(..., description="Theme name"),
    market: str | None = Query(None, description="KR or US (optional, default=ALL)"),
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
):
    """특정 테마의 정확도 추이 조회."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    query = db.query(ThemePredictionAccuracy).filter(
        ThemePredictionAccuracy.theme == theme,
        ThemePredictionAccuracy.prediction_date >= start_date,
        ThemePredictionAccuracy.prediction_date <= end_date,
    )

    if market:
        query = query.filter(ThemePredictionAccuracy.market == market)

    rows = query.order_by(ThemePredictionAccuracy.prediction_date).all()

    trend = [
        ThemeTrendPoint(
            date=r.prediction_date,
            accuracy_rate=r.accuracy_rate,
            total_stocks=r.total_stocks,
        )
        for r in rows
    ]

    return ThemeTrendResponse(
        theme=theme,
        market=market or "ALL",
        start_date=start_date,
        end_date=end_date,
        trend=trend,
    )


@router.get("/stocks/{code}/history", response_model=StockHistoryResponse)
@limiter.limit("60/minute")
async def get_stock_history(
    request: Request,
    response: Response,
    code: str,
    market: str | None = Query(None, description="KR or US (optional, auto-detect)"),
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
):
    """특정 종목의 예측 이력 조회."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    query = db.query(DailyPredictionResult).filter(
        DailyPredictionResult.stock_code == code,
        DailyPredictionResult.prediction_date >= start_date,
        DailyPredictionResult.prediction_date <= end_date,
    )

    if market:
        query = query.filter(DailyPredictionResult.market == market)

    rows = query.order_by(DailyPredictionResult.prediction_date).all()

    if not rows:
        return StockHistoryResponse(
            stock_code=code,
            stock_name=None,
            market=market or "UNKNOWN",
            start_date=start_date,
            end_date=end_date,
            total_predictions=0,
            correct_predictions=0,
            accuracy_rate=0.0,
            history=[],
        )

    history = [
        StockHistoryPoint(
            date=r.prediction_date,
            predicted_direction=r.predicted_direction,
            predicted_score=r.predicted_score,
            actual_direction=r.actual_direction,
            actual_change_pct=r.actual_change_pct,
            is_correct=r.is_correct,
        )
        for r in rows
    ]

    verified_rows = [r for r in rows if r.is_correct is not None]
    total_predictions = len(verified_rows)
    correct_predictions = sum(1 for r in verified_rows if r.is_correct)
    accuracy_rate = correct_predictions / total_predictions if total_predictions > 0 else 0.0

    return StockHistoryResponse(
        stock_code=code,
        stock_name=rows[0].stock_name,
        market=rows[0].market,
        start_date=start_date,
        end_date=end_date,
        total_predictions=total_predictions,
        correct_predictions=correct_predictions,
        accuracy_rate=round(accuracy_rate, 4),
        history=history,
    )


@router.post("/run", response_model=VerificationRunResponse)
@limiter.limit("10/minute")
async def trigger_verification_run(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    target_date: str = Query(..., alias="date", description="YYYY-MM-DD"),
    market: str = Query("KR", description="KR or US"),
    db: Session = Depends(get_db),
):
    """검증 실행 트리거 (백그라운드)."""
    d = date.fromisoformat(target_date)

    async def run_verification_task():
        """Background task wrapper."""
        from app.core.database import SessionLocal

        db_bg = SessionLocal()
        try:
            run_log = await run_verification(db_bg, d, market)
            if run_log.status != "failed":
                aggregate_theme_accuracy(db_bg, d, market)
            return run_log
        finally:
            db_bg.close()

    background_tasks.add_task(run_verification_task)

    return VerificationRunResponse(
        run_date=d,
        market=market,
        status="triggered",
        stocks_verified=0,
        stocks_failed=0,
        duration_seconds=0.0,
        error_details=None,
    )


@router.get("/status", response_model=VerificationStatusResponse)
@limiter.limit("60/minute")
async def get_verification_status(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """전체 검증 상태 조회."""
    current_date = date.today()

    markets_data = []
    for market in ["KR", "US"]:
        latest = (
            db.query(VerificationRunLog)
            .filter(VerificationRunLog.market == market)
            .order_by(VerificationRunLog.run_date.desc())
            .first()
        )

        if latest:
            markets_data.append(
                MarketStatus(
                    market=market,
                    last_run_date=latest.run_date,
                    status=latest.status,
                    stocks_verified=latest.stocks_verified,
                )
            )
        else:
            markets_data.append(
                MarketStatus(
                    market=market,
                    last_run_date=None,
                    status=None,
                    stocks_verified=0,
                )
            )

    today_count = (
        db.query(func.sum(VerificationRunLog.stocks_verified))
        .filter(VerificationRunLog.run_date == current_date)
        .scalar()
        or 0
    )

    return VerificationStatusResponse(
        current_date=current_date,
        markets=markets_data,
        total_stocks_verified_today=today_count,
    )
