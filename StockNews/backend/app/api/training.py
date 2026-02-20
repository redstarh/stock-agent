"""학습 데이터 조회/내보내기 API."""

import json
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.core.limiter import limiter
from app.models.ml_model import MLModel
from app.models.training import StockTrainingData
from app.processing.feature_config import get_features_for_tier, get_min_samples_for_tier
from app.processing.ml_evaluator import MLEvaluator
from app.processing.ml_trainer import MLTrainer
from app.processing.model_registry import ModelRegistry
from app.processing.training_data_builder import export_training_csv
from app.schemas.training import (
    TrainingDataItem,
    TrainingDataResponse,
    TrainingStatsMarket,
    TrainingStatsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/training",
    tags=["training"],
    dependencies=[Depends(verify_api_key)],
)


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
            market_return=r.market_return,
            vix_change=r.vix_change,
            usd_krw_change=r.usd_krw_change,
            has_earnings_disclosure=r.has_earnings_disclosure,
            cross_theme_score=r.cross_theme_score,
            foreign_net_ratio=r.foreign_net_ratio,
            sector_index_change=r.sector_index_change,
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


@router.post("/backfill")
@limiter.limit("5/minute")
async def trigger_backfill(
    request: Request,
    response: Response,
    market: str = Query("KR", description="KR or US"),
    days_back: int = Query(30, ge=1, le=90, description="Days to backfill"),
    dry_run: bool = Query(False, description="Preview without creating records"),
    db: Session = Depends(get_db),
):
    """Historical training data backfill 실행."""
    from app.processing.training_backfill import backfill_training_data

    result = backfill_training_data(db, market=market, days_back=days_back, dry_run=dry_run)

    return {
        "status": "dry_run" if dry_run else "completed",
        "market": market,
        "days_back": days_back,
        **result,
    }


@router.post("/train")
@limiter.limit("5/minute")
async def train_model(
    request: Request,
    response: Response,
    market: str = Query("KR", description="KR or US"),
    model_type: str = Query("lightgbm", description="lightgbm or random_forest"),
    feature_tier: int = Query(1, ge=1, le=3, description="Feature tier"),
    db: Session = Depends(get_db),
):
    """모델 학습 실행."""
    features = get_features_for_tier(feature_tier)
    min_samples = get_min_samples_for_tier(feature_tier)

    trainer = MLTrainer(market=market, tier=feature_tier)

    try:
        X, y = trainer.load_training_data(db)
    except ValueError as e:
        # Insufficient samples
        return {
            "status": "insufficient_data",
            "samples": 0,
            "required": min_samples,
            "feature_tier": feature_tier,
        }

    if len(X) < min_samples:
        return {
            "status": "insufficient_data",
            "samples": len(X),
            "required": min_samples,
            "feature_tier": feature_tier,
        }

    if model_type == "lightgbm":
        result = trainer.train_lightgbm(X, y)
    else:
        result = trainer.train_random_forest(X, y)

    # Save to registry
    registry = ModelRegistry()
    model_id = registry.save(
        model=result["model"],
        metadata={
            "model_name": f"{model_type}_{market}_t{feature_tier}",
            "model_version": "1.0",
            "model_type": model_type,
            "market": market,
            "feature_tier": feature_tier,
            "feature_list": features,
            "train_accuracy": result["accuracy"],
            "test_accuracy": None,
            "cv_accuracy": result["cv_accuracy"],
            "cv_std": result["cv_std"],
            "train_samples": len(X),
            "test_samples": None,
            "hyperparameters": {},
            "feature_importances": result.get("feature_importances"),
        },
        db=db,
    )

    return {
        "status": "trained",
        "model_id": model_id,
        "model_type": model_type,
        "market": market,
        "feature_tier": feature_tier,
        "train_accuracy": round(result["accuracy"], 4),
        "test_accuracy": None,
        "cv_accuracy": round(result["cv_accuracy"], 4),
        "cv_std": round(result["cv_std"], 4),
        "samples": len(X),
        "features": len(features),
    }


@router.get("/models")
@limiter.limit("60/minute")
async def list_models(
    request: Request,
    response: Response,
    market: str | None = Query(None, description="Filter by market"),
    db: Session = Depends(get_db),
):
    """등록된 ML 모델 목록."""
    registry = ModelRegistry()
    models = registry.list_models(market=market, db=db)

    return [
        {
            "id": m.id,
            "model_name": m.model_name,
            "model_version": m.model_version,
            "model_type": m.model_type,
            "market": m.market,
            "feature_tier": m.feature_tier,
            "feature_list": json.loads(m.feature_list) if m.feature_list else [],
            "train_accuracy": m.train_accuracy,
            "test_accuracy": m.test_accuracy,
            "cv_accuracy": m.cv_accuracy,
            "cv_std": m.cv_std,
            "train_samples": m.train_samples,
            "test_samples": m.test_samples,
            "is_active": m.is_active,
            "feature_importances": json.loads(m.feature_importances) if m.feature_importances else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in models
    ]


@router.post("/models/{model_id}/activate")
@limiter.limit("10/minute")
async def activate_model(
    request: Request,
    response: Response,
    model_id: int,
    db: Session = Depends(get_db),
):
    """모델 활성화."""
    registry = ModelRegistry()
    try:
        registry.activate(model_id, db)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(e))

    return {"status": "activated", "model_id": model_id}


@router.post("/evaluate")
@limiter.limit("10/minute")
async def evaluate_model(
    request: Request,
    response: Response,
    market: str = Query("KR", description="KR or US"),
    db: Session = Depends(get_db),
):
    """활성 모델 평가."""
    registry = ModelRegistry()
    active = registry.get_active(market, db)

    if not active:
        return {"status": "no_active_model", "market": market}

    feature_list = json.loads(active.feature_list) if active.feature_list else []

    trainer = MLTrainer(market=market, tier=active.feature_tier)
    X, y = trainer.load_training_data(db)

    if X.empty:
        return {"status": "no_data", "market": market}

    model = registry.load(active.id, db)
    evaluator = MLEvaluator()
    result = evaluator.evaluate(model, X, y)

    return {
        "status": "evaluated",
        "model_id": active.id,
        "model_name": active.model_name,
        "market": market,
        **result,
    }


@router.get("/monitor")
@limiter.limit("30/minute")
async def monitor_models(
    request: Request,
    response: Response,
    market: str = Query("KR", description="KR or US"),
    min_accuracy: float = Query(0.55, description="Minimum acceptable accuracy"),
    db: Session = Depends(get_db),
):
    """모델 정확도 모니터링 + 자동 롤백 체크."""
    from app.processing.feature_validator import FeatureValidator

    registry = ModelRegistry()

    # Check accuracy and potentially rollback
    rollback_result = registry.check_accuracy_and_rollback(
        market, db, min_accuracy=min_accuracy
    )

    # Get accuracy history
    history = registry.get_accuracy_history(market, db, limit=10)

    # Check feature null rates
    validator = FeatureValidator()
    null_report = validator.null_rate_report(db, market)

    # Build alerts
    alerts = []

    if rollback_result["action"] == "rollback":
        alerts.append({
            "level": "warning",
            "type": "accuracy_rollback",
            "message": rollback_result["reason"],
        })
    elif rollback_result["action"] == "no_fallback":
        alerts.append({
            "level": "critical",
            "type": "accuracy_low_no_fallback",
            "message": rollback_result["reason"],
        })

    # Check for high null rate features
    for fname, fdata in null_report.get("features", {}).items():
        if fdata.get("alert"):
            alerts.append({
                "level": "warning",
                "type": "feature_null_rate",
                "message": f"Feature '{fname}' null rate {fdata['null_rate']:.1%} exceeds threshold",
            })

    return {
        "market": market,
        "rollback_check": rollback_result,
        "accuracy_history": history,
        "null_rate_report": null_report,
        "alerts": alerts,
        "alert_count": len(alerts),
    }


@router.get("/features")
@limiter.limit("60/minute")
async def get_feature_info(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """피처 Tier 정보 + 현재 샘플 수."""
    from app.processing.feature_config import REMOVED_FEATURES

    # Count current labeled samples per market
    sample_counts = {}
    for market in ["KR", "US"]:
        count = (
            db.query(func.count(StockTrainingData.id))
            .filter(
                StockTrainingData.market == market,
                StockTrainingData.actual_direction.isnot(None),
            )
            .scalar()
            or 0
        )
        sample_counts[market] = count

    # Build tier info
    tiers = {}
    for tier in [1, 2, 3]:
        features = get_features_for_tier(tier)
        min_samples = get_min_samples_for_tier(tier)

        tiers[str(tier)] = {
            "features": features,
            "feature_count": len(features),
            "min_samples": min_samples,
            "status": {
                market: (
                    "active" if count >= min_samples
                    else f"{count}/{min_samples}"
                )
                for market, count in sample_counts.items()
            },
        }

    return {
        "tiers": tiers,
        "removed_features": REMOVED_FEATURES,
        "current_samples": sample_counts,
    }
