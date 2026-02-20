"""학습 데이터 조회/내보내기 API."""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limiter import limiter
from app.models.training import StockTrainingData
from app.processing.training_data_builder import export_training_csv
from app.schemas.training import (
    TrainingDataItem,
    TrainingDataResponse,
    TrainingStatsMarket,
    TrainingStatsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/training", tags=["training"])


@router.get("/data", response_model=TrainingDataResponse)
@limiter.limit("30/minute")
async def get_training_data(
    request: Request,
    response: Response,
    market: str = Query("KR", description="KR or US"),
    start_date: str | None = Query(None, description="YYYY-MM-DD (default: 30 days ago)"),
    end_date: str | None = Query(None, description="YYYY-MM-DD (default: today)"),
    limit: int = Query(1000, ge=1, le=10000, description="Max records"),
    db: Session = Depends(get_db),
):
    """학습 데이터 조회."""
    ed = date.fromisoformat(end_date) if end_date else date.today()
    sd = date.fromisoformat(start_date) if start_date else ed - timedelta(days=30)

    records = (
        db.query(StockTrainingData)
        .filter(
            StockTrainingData.market == market,
            StockTrainingData.prediction_date >= sd,
            StockTrainingData.prediction_date <= ed,
        )
        .order_by(
            StockTrainingData.prediction_date.desc(),
            StockTrainingData.stock_code,
        )
        .limit(limit)
        .all()
    )

    data = [
        TrainingDataItem(
            prediction_date=r.prediction_date,
            stock_code=r.stock_code,
            stock_name=r.stock_name,
            market=r.market,
            news_score=r.news_score,
            sentiment_score=r.sentiment_score,
            news_count=r.news_count,
            news_count_3d=r.news_count_3d,
            avg_score_3d=r.avg_score_3d,
            disclosure_ratio=r.disclosure_ratio,
            sentiment_trend=r.sentiment_trend,
            theme=r.theme,
            prev_close=r.prev_close,
            prev_change_pct=r.prev_change_pct,
            prev_volume=r.prev_volume,
            price_change_5d=r.price_change_5d,
            volume_change_5d=r.volume_change_5d,
            ma5_ratio=r.ma5_ratio,
            ma20_ratio=r.ma20_ratio,
            volatility_5d=r.volatility_5d,
            rsi_14=r.rsi_14,
            bb_position=r.bb_position,
            market_index_change=r.market_index_change,
            day_of_week=r.day_of_week,
            predicted_direction=r.predicted_direction,
            predicted_score=r.predicted_score,
            confidence=r.confidence,
            actual_close=r.actual_close,
            actual_change_pct=r.actual_change_pct,
            actual_direction=r.actual_direction,
            actual_volume=r.actual_volume,
            is_correct=r.is_correct,
        )
        for r in records
    ]

    return TrainingDataResponse(
        market=market,
        start_date=sd,
        end_date=ed,
        total=len(data),
        data=data,
    )


@router.get("/export")
@limiter.limit("10/minute")
async def export_training(
    request: Request,
    response: Response,
    market: str = Query("KR", description="KR or US"),
    start_date: str | None = Query(None, description="YYYY-MM-DD"),
    end_date: str | None = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """학습 데이터 CSV 내보내기."""
    ed = date.fromisoformat(end_date) if end_date else date.today()
    sd = date.fromisoformat(start_date) if start_date else ed - timedelta(days=30)

    csv_content = export_training_csv(db, market, sd, ed)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=training_{market}_{sd}_{ed}.csv"
        },
    )


@router.get("/stats", response_model=TrainingStatsResponse)
@limiter.limit("60/minute")
async def get_training_stats(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """학습 데이터 통계."""
    markets_data = []
    total_all = 0
    labeled_all = 0

    for market in ["KR", "US"]:
        total = (
            db.query(func.count(StockTrainingData.id))
            .filter(StockTrainingData.market == market)
            .scalar()
            or 0
        )
        labeled = (
            db.query(func.count(StockTrainingData.id))
            .filter(
                StockTrainingData.market == market,
                StockTrainingData.is_correct.isnot(None),
            )
            .scalar()
            or 0
        )

        correct = (
            db.query(func.count(StockTrainingData.id))
            .filter(
                StockTrainingData.market == market,
                StockTrainingData.is_correct == True,  # noqa: E712
            )
            .scalar()
            or 0
        )
        accuracy = round((correct / labeled) * 100, 1) if labeled > 0 else None

        date_range = (
            db.query(
                func.min(StockTrainingData.prediction_date),
                func.max(StockTrainingData.prediction_date),
            )
            .filter(StockTrainingData.market == market)
            .first()
        )

        markets_data.append(
            TrainingStatsMarket(
                market=market,
                total_records=total,
                labeled_records=labeled,
                accuracy=accuracy,
                date_range_start=date_range[0] if date_range else None,
                date_range_end=date_range[1] if date_range else None,
            )
        )

        total_all += total
        labeled_all += labeled

    return TrainingStatsResponse(
        total_records=total_all,
        labeled_records=labeled_all,
        markets=markets_data,
    )
