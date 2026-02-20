"""ML 피처 검증 — 범위 체크, 결측 대체, null 비율 분석."""

import logging
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.training import StockTrainingData

logger = logging.getLogger(__name__)

# Feature bounds: (min, max) — values outside are clipped
FEATURE_BOUNDS: dict[str, tuple[float, float]] = {
    "rsi_14": (0, 100),
    "bb_position": (0, 1),
    "sentiment_score": (-1, 1),
    "news_score": (0, 100),
    "confidence": (0, 1),
    "volatility_5d": (0, 50),
    "ma5_ratio": (0.5, 2.0),
    "disclosure_ratio": (0, 1),
    "prev_change_pct": (-30, 30),
    "price_change_5d": (-50, 50),
    "volume_change_5d": (-100, 1000),
}

# Default imputation values (used when feature is None)
DEFAULT_VALUES: dict[str, float] = {
    "news_score": 0.0,
    "sentiment_score": 0.0,
    "news_count": 0,
    "news_count_3d": 0,
    "avg_score_3d": 0.0,
    "disclosure_ratio": 0.0,
    "sentiment_trend": 0.0,
    "prev_change_pct": 0.0,
    "price_change_5d": 0.0,
    "volume_change_5d": 0.0,
    "ma5_ratio": 1.0,
    "volatility_5d": 0.0,
    "rsi_14": 50.0,
    "bb_position": 0.5,
    "market_return": 0.0,
    "vix_change": 0.0,
}


class FeatureValidator:
    """ML 피처 검증기."""

    def validate(self, features: dict) -> dict:
        """범위 체크 + 클리핑.

        Args:
            features: {feature_name: value} dict

        Returns:
            Validated features dict (out-of-bounds values clipped, issues logged)
        """
        result = {}
        for key, value in features.items():
            if value is None:
                result[key] = value
                continue

            if key in FEATURE_BOUNDS:
                lo, hi = FEATURE_BOUNDS[key]
                if isinstance(value, (int, float)):
                    if value < lo or value > hi:
                        logger.warning(
                            "Feature %s=%.4f out of bounds [%.1f, %.1f], clipping",
                            key, value, lo, hi,
                        )
                        value = max(lo, min(hi, value))
            result[key] = value
        return result

    def impute_missing(self, features: dict, defaults: dict | None = None) -> dict:
        """결측값(None)을 기본값으로 대체.

        Args:
            features: {feature_name: value} dict (may contain None)
            defaults: Custom defaults (overrides DEFAULT_VALUES)

        Returns:
            Features dict with None values replaced
        """
        effective_defaults = {**DEFAULT_VALUES}
        if defaults:
            effective_defaults.update(defaults)

        result = {}
        for key, value in features.items():
            if value is None and key in effective_defaults:
                result[key] = effective_defaults[key]
                logger.debug("Imputed %s with default %.4f", key, effective_defaults[key])
            else:
                result[key] = value
        return result

    def null_rate_report(self, db: Session, market: str, days: int = 30) -> dict:
        """피처별 null 비율 분석.

        Args:
            db: Database session
            market: "KR" or "US"
            days: Analysis period (default 30 days)

        Returns:
            {
                "total_records": int,
                "features": {
                    "feature_name": {"null_count": int, "null_rate": float, "alert": bool},
                    ...
                }
            }
        """
        cutoff = date.today() - timedelta(days=days)

        total = (
            db.query(func.count(StockTrainingData.id))
            .filter(
                StockTrainingData.market == market,
                StockTrainingData.prediction_date >= cutoff,
            )
            .scalar() or 0
        )

        if total == 0:
            return {"total_records": 0, "features": {}}

        # Check null rates for key feature columns
        feature_columns = {
            "rsi_14": StockTrainingData.rsi_14,
            "bb_position": StockTrainingData.bb_position,
            "volatility_5d": StockTrainingData.volatility_5d,
            "ma5_ratio": StockTrainingData.ma5_ratio,
            "prev_change_pct": StockTrainingData.prev_change_pct,
            "price_change_5d": StockTrainingData.price_change_5d,
            "volume_change_5d": StockTrainingData.volume_change_5d,
            "market_index_change": StockTrainingData.market_index_change,
            "news_score": StockTrainingData.news_score,
            "sentiment_score": StockTrainingData.sentiment_score,
        }

        report = {}
        for name, column in feature_columns.items():
            null_count = (
                db.query(func.count(StockTrainingData.id))
                .filter(
                    StockTrainingData.market == market,
                    StockTrainingData.prediction_date >= cutoff,
                    column.is_(None),
                )
                .scalar() or 0
            )
            null_rate = null_count / total
            report[name] = {
                "null_count": null_count,
                "null_rate": round(null_rate, 4),
                "alert": null_rate > 0.3,  # Alert if >30%
            }

        return {"total_records": total, "features": report}
