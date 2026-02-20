"""
P0-5: Phase 0 Gate Test — Training Data Readiness Validation

Gate criteria for ML model training:
- 200+ labeled samples
- Balanced label distribution (no class > 70%)
- Tier 1 feature null rate <= 30%
- Feature validator working correctly
- Labeled vs unlabeled ratio >= 50%

Uses synthetic test data to validate checking logic (not production data).
"""

import pytest
from datetime import date, datetime, timezone, timedelta
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.training import StockTrainingData
from app.processing.feature_validator import FeatureValidator


@pytest.fixture
def db():
    """In-memory SQLite session with StockTrainingData table."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _make_training_record(
    stock_code: str, pred_date: date, market: str = "KR", **overrides
) -> StockTrainingData:
    """Helper to create a StockTrainingData record with sensible defaults."""
    defaults = {
        "prediction_date": pred_date,
        "stock_code": stock_code,
        "stock_name": f"Test Stock {stock_code}",
        "market": market,
        "news_score": 55.0,
        "sentiment_score": 0.3,
        "news_count": 5,
        "news_count_3d": 2,
        "avg_score_3d": 50.0,
        "disclosure_ratio": 0.1,
        "sentiment_trend": 0.05,
        "prev_close": 50000.0,
        "prev_change_pct": 1.2,
        "prev_volume": 100000,
        "price_change_5d": 3.5,
        "volume_change_5d": 10.0,
        "ma5_ratio": 1.02,
        "ma20_ratio": 0.98,
        "volatility_5d": 2.5,
        "rsi_14": 55.0,
        "bb_position": 0.6,
        "market_index_change": 0.5,
        "day_of_week": pred_date.weekday(),
        "predicted_direction": "up",
        "predicted_score": 65.0,
        "confidence": 0.7,
        "actual_close": 51000.0,
        "actual_change_pct": 2.0,
        "actual_direction": "up",
        "actual_volume": 120000,
        "is_correct": True,
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    return StockTrainingData(**defaults)


def test_sample_count_gate_pass(db):
    """Gate test: 200+ labeled samples required for training."""
    # Insert 250 labeled records with unique (date, stock_code) combinations
    base_date = date(2026, 1, 1)
    records = []
    for i in range(250):
        # Use different stock codes to avoid UNIQUE constraint violations
        pred_date = base_date + timedelta(days=i // 10)  # 10 stocks per day
        stock_code = f"{i % 10:06d}"
        records.append(
            _make_training_record(
                stock_code=stock_code,
                pred_date=pred_date,
                actual_direction="up" if i % 2 == 0 else "down",
            )
        )
    db.add_all(records)
    db.commit()

    # Query labeled count
    labeled_count = db.scalar(
        select(func.count()).where(StockTrainingData.actual_direction.isnot(None))
    )

    assert labeled_count >= 200, f"Expected >= 200 labeled samples, got {labeled_count}"


def test_sample_count_gate_fail(db):
    """Gate test should fail with insufficient samples."""
    # Insert only 50 records with unique (date, stock_code) combinations
    base_date = date(2026, 1, 1)
    records = []
    for i in range(50):
        pred_date = base_date + timedelta(days=i // 5)  # 5 stocks per day
        stock_code = f"{1000 + i:06d}"
        records.append(
            _make_training_record(
                stock_code=stock_code,
                pred_date=pred_date,
                actual_direction="up",
            )
        )
    db.add_all(records)
    db.commit()

    labeled_count = db.scalar(
        select(func.count()).where(StockTrainingData.actual_direction.isnot(None))
    )

    assert labeled_count < 200, f"Expected < 200 samples, got {labeled_count}"


def test_label_distribution_balanced(db):
    """Balanced label distribution — no class exceeds 70%."""
    # Insert 300 records: 120 up, 120 down, 60 neutral (40%, 40%, 20%)
    base_date = date(2026, 1, 1)
    records = []
    record_idx = 0

    for i in range(120):
        pred_date = base_date + timedelta(days=record_idx // 10)  # 10 stocks per day
        stock_code = f"{2000 + record_idx:06d}"
        records.append(
            _make_training_record(
                stock_code=stock_code,
                pred_date=pred_date,
                actual_direction="up",
            )
        )
        record_idx += 1

    for i in range(120):
        pred_date = base_date + timedelta(days=record_idx // 10)
        stock_code = f"{2000 + record_idx:06d}"
        records.append(
            _make_training_record(
                stock_code=stock_code,
                pred_date=pred_date,
                actual_direction="down",
            )
        )
        record_idx += 1

    for i in range(60):
        pred_date = base_date + timedelta(days=record_idx // 10)
        stock_code = f"{2000 + record_idx:06d}"
        records.append(
            _make_training_record(
                stock_code=stock_code,
                pred_date=pred_date,
                actual_direction="neutral",
            )
        )
        record_idx += 1

    db.add_all(records)
    db.commit()

    # Check distribution
    total = db.scalar(
        select(func.count()).where(StockTrainingData.actual_direction.isnot(None))
    )

    for label in ["up", "down", "neutral"]:
        count = db.scalar(
            select(func.count()).where(StockTrainingData.actual_direction == label)
        )
        ratio = count / total
        assert (
            ratio <= 0.7
        ), f"Label '{label}' exceeds 70% threshold: {ratio:.2%} ({count}/{total})"


def test_label_distribution_skewed(db):
    """Skewed label distribution — majority class > 70%."""
    # Insert 200 records: 180 up, 20 down (90%, 10%)
    base_date = date(2026, 1, 1)
    records = []
    record_idx = 0

    for i in range(180):
        pred_date = base_date + timedelta(days=record_idx // 10)  # 10 stocks per day
        stock_code = f"{3000 + record_idx:06d}"
        records.append(
            _make_training_record(
                stock_code=stock_code,
                pred_date=pred_date,
                actual_direction="up",
            )
        )
        record_idx += 1

    for i in range(20):
        pred_date = base_date + timedelta(days=record_idx // 10)
        stock_code = f"{3000 + record_idx:06d}"
        records.append(
            _make_training_record(
                stock_code=stock_code,
                pred_date=pred_date,
                actual_direction="down",
            )
        )
        record_idx += 1

    db.add_all(records)
    db.commit()

    # Verify majority class exceeds 70%
    total = db.scalar(
        select(func.count()).where(StockTrainingData.actual_direction.isnot(None))
    )
    up_count = db.scalar(
        select(func.count()).where(StockTrainingData.actual_direction == "up")
    )
    up_ratio = up_count / total

    assert (
        up_ratio > 0.7
    ), f"Expected majority class > 70%, got {up_ratio:.2%} ({up_count}/{total})"


def test_null_rate_within_threshold(db):
    """Tier 1 features all populated — null rate <= 30%."""
    # Insert 100 records with all Tier 1 features populated
    # Use recent dates to fall within the 30-day window
    base_date = date.today() - timedelta(days=15)  # Within last 30 days
    records = []

    for i in range(100):
        pred_date = base_date + timedelta(days=i % 10)  # Spread over 10 days
        stock_code = f"{4000 + i:06d}"
        records.append(
            _make_training_record(
                stock_code=stock_code,
                pred_date=pred_date,
                news_score=55.0 + i % 20,
                sentiment_score=0.3,
                rsi_14=50.0 + i % 30,
                prev_change_pct=1.0 + i % 10,
                price_change_5d=2.0 + i % 15,
                volume_change_5d=5.0 + i % 20,
                market_index_change=0.5,
            )
        )

    db.add_all(records)
    db.commit()

    # Check null rates
    validator = FeatureValidator()
    report = validator.null_rate_report(db, "KR")

    # Note: vix_change is not a column in StockTrainingData, it's mapped to market_index_change
    tier1_features = [
        "rsi_14",
        "prev_change_pct",
        "price_change_5d",
        "volume_change_5d",
        "market_index_change",
    ]

    for feature in tier1_features:
        feature_report = report["features"].get(feature)
        assert feature_report is not None, f"Feature '{feature}' not in report"
        assert (
            feature_report["null_rate"] <= 0.3
        ), f"Feature '{feature}' null rate {feature_report['null_rate']:.2%} exceeds 30%"
        assert (
            not feature_report["alert"]
        ), f"Feature '{feature}' triggered alert when it shouldn't"


def test_null_rate_exceeds_threshold(db):
    """Null rate > 30% triggers alert."""
    # Insert 100 records where 50 have rsi_14=None
    # Use recent dates to fall within the 30-day window
    base_date = date.today() - timedelta(days=15)  # Within last 30 days
    records = []

    for i in range(100):
        rsi_value = None if i < 50 else 55.0
        pred_date = base_date + timedelta(days=i % 10)  # Spread over 10 days
        stock_code = f"{5000 + i:06d}"
        records.append(
            _make_training_record(
                stock_code=stock_code,
                pred_date=pred_date,
                rsi_14=rsi_value,
            )
        )

    db.add_all(records)
    db.commit()

    # Check null rate report
    validator = FeatureValidator()
    report = validator.null_rate_report(db, "KR")

    rsi_report = report["features"].get("rsi_14")
    assert rsi_report is not None, "rsi_14 not in report"
    assert (
        rsi_report["null_rate"] >= 0.5
    ), f"Expected rsi_14 null rate >= 0.5, got {rsi_report['null_rate']:.2%}"
    assert rsi_report["alert"], "Expected alert=True for rsi_14 with high null rate"


def test_feature_validator_integration(db):
    """Feature validator clipping and imputation work correctly."""
    validator = FeatureValidator()

    # Test validation (clipping)
    features_out_of_bounds = {
        "news_score": 150.0,  # Should clip to 100
        "sentiment_score": -2.0,  # Should clip to -1.0
        "rsi_14": 200.0,  # Should clip to 100
        "prev_change_pct": 1.5,  # Within bounds
        "market_index_change": 0.3,  # Within bounds
    }

    validated = validator.validate(features_out_of_bounds)

    assert validated["news_score"] == 100.0, "news_score should be clipped to 100"
    assert (
        validated["sentiment_score"] == -1.0
    ), "sentiment_score should be clipped to -1.0"
    assert validated["rsi_14"] == 100.0, "rsi_14 should be clipped to 100"
    assert validated["prev_change_pct"] == 1.5, "prev_change_pct should be unchanged"
    assert (
        validated["market_index_change"] == 0.3
    ), "market_index_change should be unchanged"

    # Test imputation (using DEFAULT_VALUES from feature_validator.py)
    features_with_nulls = {
        "news_score": None,
        "sentiment_score": None,
        "rsi_14": None,
        "prev_change_pct": 1.2,
        "market_index_change": 0.5,
    }

    imputed = validator.impute_missing(features_with_nulls)

    assert imputed["news_score"] == 0.0, "news_score default should be 0.0"
    assert imputed["sentiment_score"] == 0.0, "sentiment_score default should be 0.0"
    assert imputed["rsi_14"] == 50.0, "rsi_14 default should be 50.0"
    assert imputed["prev_change_pct"] == 1.2, "prev_change_pct should be unchanged"
    assert imputed["market_index_change"] == 0.5, "market_index_change should be unchanged"


def test_labeled_vs_unlabeled_ratio(db):
    """Labeled ratio >= 50% required for useful training."""
    # Insert 200 records: 150 labeled, 50 unlabeled (75%, 25%)
    base_date = date(2026, 1, 1)
    records = []
    record_idx = 0

    # 150 labeled
    for i in range(150):
        pred_date = base_date + timedelta(days=record_idx // 10)  # 10 stocks per day
        stock_code = f"{6000 + record_idx:06d}"
        records.append(
            _make_training_record(
                stock_code=stock_code,
                pred_date=pred_date,
                actual_direction="up" if i % 2 == 0 else "down",
            )
        )
        record_idx += 1

    # 50 unlabeled (actual_direction=None)
    for i in range(50):
        pred_date = base_date + timedelta(days=record_idx // 10)
        stock_code = f"{6000 + record_idx:06d}"
        records.append(
            _make_training_record(
                stock_code=stock_code,
                pred_date=pred_date,
                actual_direction=None,
                actual_close=None,
                actual_change_pct=None,
                actual_volume=None,
                is_correct=None,
            )
        )
        record_idx += 1

    db.add_all(records)
    db.commit()

    # Count labeled and total
    total = db.scalar(select(func.count(StockTrainingData.id)))
    labeled = db.scalar(
        select(func.count()).where(StockTrainingData.actual_direction.isnot(None))
    )
    labeled_ratio = labeled / total

    assert (
        labeled_ratio >= 0.5
    ), f"Expected labeled ratio >= 50%, got {labeled_ratio:.2%} ({labeled}/{total})"
