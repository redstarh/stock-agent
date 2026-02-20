"""Tests for feature_validator module."""

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base
from app.models.training import StockTrainingData
from app.processing.feature_validator import (
    DEFAULT_VALUES,
    FEATURE_BOUNDS,
    FeatureValidator,
)


@pytest.fixture
def db_session():
    """In-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def validator():
    """Feature validator instance."""
    return FeatureValidator()


class TestValidate:
    """validate 메서드 테스트."""

    def test_validate_within_bounds(self, validator):
        """정상 범위 내 값은 그대로 통과."""
        features = {
            "rsi_14": 50.0,
            "bb_position": 0.5,
            "sentiment_score": 0.3,
            "news_score": 70.0,
            "confidence": 0.8,
            "volatility_5d": 10.0,
            "ma5_ratio": 1.2,
            "disclosure_ratio": 0.25,
        }

        result = validator.validate(features)

        assert result == features
        assert result["rsi_14"] == 50.0
        assert result["sentiment_score"] == 0.3

    def test_validate_clips_high(self, validator):
        """상한 초과 시 클리핑."""
        features = {
            "rsi_14": 150.0,  # > 100
            "bb_position": 1.5,  # > 1
            "sentiment_score": 2.0,  # > 1
        }

        result = validator.validate(features)

        assert result["rsi_14"] == 100.0
        assert result["bb_position"] == 1.0
        assert result["sentiment_score"] == 1.0

    def test_validate_clips_low(self, validator):
        """하한 미만 시 클리핑."""
        features = {
            "rsi_14": -10.0,  # < 0
            "bb_position": -0.5,  # < 0
            "sentiment_score": -2.0,  # < -1
            "volatility_5d": -5.0,  # < 0
        }

        result = validator.validate(features)

        assert result["rsi_14"] == 0.0
        assert result["bb_position"] == 0.0
        assert result["sentiment_score"] == -1.0
        assert result["volatility_5d"] == 0.0

    def test_validate_preserves_none(self, validator):
        """None 값은 클리핑 없이 보존."""
        features = {
            "rsi_14": None,
            "bb_position": 0.5,
            "sentiment_score": None,
            "news_score": 70.0,
        }

        result = validator.validate(features)

        assert result["rsi_14"] is None
        assert result["sentiment_score"] is None
        assert result["bb_position"] == 0.5
        assert result["news_score"] == 70.0

    def test_validate_unknown_feature(self, validator):
        """FEATURE_BOUNDS에 없는 피처는 그대로 통과."""
        features = {
            "rsi_14": 50.0,
            "unknown_feature": 999.0,  # Not in FEATURE_BOUNDS
            "custom_metric": -100.0,  # Not in FEATURE_BOUNDS
        }

        result = validator.validate(features)

        assert result["rsi_14"] == 50.0
        assert result["unknown_feature"] == 999.0
        assert result["custom_metric"] == -100.0


class TestImputeMissing:
    """impute_missing 메서드 테스트."""

    def test_impute_replaces_none(self, validator):
        """None 값을 기본값으로 대체."""
        features = {
            "news_score": None,
            "sentiment_score": None,
            "rsi_14": None,
            "ma5_ratio": None,
        }

        result = validator.impute_missing(features)

        assert result["news_score"] == DEFAULT_VALUES["news_score"]
        assert result["sentiment_score"] == DEFAULT_VALUES["sentiment_score"]
        assert result["rsi_14"] == DEFAULT_VALUES["rsi_14"]
        assert result["ma5_ratio"] == DEFAULT_VALUES["ma5_ratio"]

    def test_impute_keeps_existing(self, validator):
        """Non-None 값은 변경하지 않음."""
        features = {
            "news_score": 75.0,
            "sentiment_score": 0.5,
            "rsi_14": 65.0,
            "ma5_ratio": 1.3,
        }

        result = validator.impute_missing(features)

        assert result["news_score"] == 75.0
        assert result["sentiment_score"] == 0.5
        assert result["rsi_14"] == 65.0
        assert result["ma5_ratio"] == 1.3

    def test_impute_custom_defaults(self, validator):
        """커스텀 기본값이 DEFAULT_VALUES를 오버라이드."""
        features = {
            "news_score": None,
            "sentiment_score": None,
            "rsi_14": None,
        }

        custom_defaults = {
            "news_score": 50.0,  # Override default 0.0
            "rsi_14": 70.0,  # Override default 50.0
        }

        result = validator.impute_missing(features, defaults=custom_defaults)

        assert result["news_score"] == 50.0
        assert result["rsi_14"] == 70.0
        # sentiment_score uses DEFAULT_VALUES (not in custom_defaults)
        assert result["sentiment_score"] == DEFAULT_VALUES["sentiment_score"]


class TestNullRateReport:
    """null_rate_report 메서드 테스트."""

    def test_null_rate_report_empty_db(self, validator, db_session):
        """빈 DB는 total_records=0 반환."""
        report = validator.null_rate_report(db_session, "KR", days=30)

        assert report["total_records"] == 0
        assert report["features"] == {}

    def test_null_rate_report_with_data(self, validator, db_session):
        """StockTrainingData 레코드로 null 비율 계산."""
        target_date = date.today() - timedelta(days=5)

        # Create 10 records with varying null patterns
        for i in range(10):
            record = StockTrainingData(
                prediction_date=target_date - timedelta(days=i % 3),
                stock_code=f"00{i:04d}",
                stock_name=f"Stock {i}",
                market="KR",
                news_score=70.0,
                sentiment_score=0.5,
                news_count=5,
                news_count_3d=3,
                avg_score_3d=72.0,
                disclosure_ratio=0.0,
                sentiment_trend=0.1,
                day_of_week=2,
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
                # Technical indicators: 40% null (4 out of 10)
                rsi_14=65.0 if i >= 4 else None,
                bb_position=0.5 if i >= 4 else None,
                volatility_5d=10.0 if i >= 4 else None,
                ma5_ratio=1.1 if i >= 4 else None,
                # Price features: 20% null (2 out of 10)
                prev_change_pct=2.5 if i >= 2 else None,
                price_change_5d=5.0 if i >= 2 else None,
                volume_change_5d=10.0 if i >= 2 else None,
                # Market index: 0% null
                market_index_change=1.5,
            )
            db_session.add(record)

        db_session.commit()

        report = validator.null_rate_report(db_session, "KR", days=30)

        assert report["total_records"] == 10

        features = report["features"]

        # Technical indicators: 40% null → alert=True
        assert features["rsi_14"]["null_count"] == 4
        assert features["rsi_14"]["null_rate"] == 0.4
        assert features["rsi_14"]["alert"] is True

        assert features["bb_position"]["null_count"] == 4
        assert features["bb_position"]["null_rate"] == 0.4
        assert features["bb_position"]["alert"] is True

        assert features["volatility_5d"]["null_count"] == 4
        assert features["volatility_5d"]["alert"] is True

        assert features["ma5_ratio"]["null_count"] == 4
        assert features["ma5_ratio"]["alert"] is True

        # Price features: 20% null → alert=False
        assert features["prev_change_pct"]["null_count"] == 2
        assert features["prev_change_pct"]["null_rate"] == 0.2
        assert features["prev_change_pct"]["alert"] is False

        assert features["price_change_5d"]["null_count"] == 2
        assert features["price_change_5d"]["alert"] is False

        assert features["volume_change_5d"]["null_count"] == 2
        assert features["volume_change_5d"]["alert"] is False

        # Market index: 0% null → alert=False
        assert features["market_index_change"]["null_count"] == 0
        assert features["market_index_change"]["null_rate"] == 0.0
        assert features["market_index_change"]["alert"] is False

    def test_null_rate_report_filters_by_market(self, validator, db_session):
        """Market 필터링 확인 — KR 레코드만 집계."""
        target_date = date.today() - timedelta(days=5)

        # Add KR records
        for i in range(5):
            record = StockTrainingData(
                prediction_date=target_date,
                stock_code=f"KR{i:04d}",
                stock_name=f"KR Stock {i}",
                market="KR",
                news_score=70.0,
                sentiment_score=0.5,
                news_count=5,
                news_count_3d=3,
                avg_score_3d=72.0,
                disclosure_ratio=0.0,
                sentiment_trend=0.1,
                day_of_week=2,
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
                rsi_14=None,  # All null
            )
            db_session.add(record)

        # Add US records (should not be counted)
        for i in range(3):
            record = StockTrainingData(
                prediction_date=target_date,
                stock_code=f"US{i:04d}",
                stock_name=f"US Stock {i}",
                market="US",
                news_score=70.0,
                sentiment_score=0.5,
                news_count=5,
                news_count_3d=3,
                avg_score_3d=72.0,
                disclosure_ratio=0.0,
                sentiment_trend=0.1,
                day_of_week=2,
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
                rsi_14=65.0,  # Not null
            )
            db_session.add(record)

        db_session.commit()

        report = validator.null_rate_report(db_session, "KR", days=30)

        # Only KR records counted (5 total, 5 null)
        assert report["total_records"] == 5
        assert report["features"]["rsi_14"]["null_count"] == 5
        assert report["features"]["rsi_14"]["null_rate"] == 1.0
        assert report["features"]["rsi_14"]["alert"] is True

    def test_null_rate_report_filters_by_date(self, validator, db_session):
        """Date 필터링 확인 — days 파라미터 준수."""
        today = date.today()

        # Recent record (within 30 days)
        recent = StockTrainingData(
            prediction_date=today - timedelta(days=10),
            stock_code="RECENT",
            stock_name="Recent Stock",
            market="KR",
            news_score=70.0,
            sentiment_score=0.5,
            news_count=5,
            news_count_3d=3,
            avg_score_3d=72.0,
            disclosure_ratio=0.0,
            sentiment_trend=0.1,
            day_of_week=2,
            predicted_direction="up",
            predicted_score=75.0,
            confidence=0.8,
            rsi_14=None,
        )
        db_session.add(recent)

        # Old record (outside 30 days)
        old = StockTrainingData(
            prediction_date=today - timedelta(days=60),
            stock_code="OLD",
            stock_name="Old Stock",
            market="KR",
            news_score=70.0,
            sentiment_score=0.5,
            news_count=5,
            news_count_3d=3,
            avg_score_3d=72.0,
            disclosure_ratio=0.0,
            sentiment_trend=0.1,
            day_of_week=2,
            predicted_direction="up",
            predicted_score=75.0,
            confidence=0.8,
            rsi_14=65.0,
        )
        db_session.add(old)

        db_session.commit()

        report = validator.null_rate_report(db_session, "KR", days=30)

        # Only recent record counted
        assert report["total_records"] == 1
        assert report["features"]["rsi_14"]["null_count"] == 1
        assert report["features"]["rsi_14"]["null_rate"] == 1.0
