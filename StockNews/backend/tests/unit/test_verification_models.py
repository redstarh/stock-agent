"""Tests for verification SQLAlchemy models."""

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import inspect

from app.models.verification import (
    DailyPredictionResult,
    ThemePredictionAccuracy,
    VerificationRunLog,
)


def test_create_daily_prediction_result(db_session):
    """Test creating a DailyPredictionResult record."""
    result = DailyPredictionResult(
        prediction_date=date(2026, 2, 19),
        stock_code="005930",
        stock_name="삼성전자",
        market="KR",
        predicted_direction="up",
        predicted_score=75.5,
        confidence=0.85,
        news_count=12,
        previous_close_price=70000.0,
        actual_close_price=71500.0,
        actual_change_pct=2.14,
        actual_direction="up",
        is_correct=True,
    )
    db_session.add(result)
    db_session.commit()

    assert result.id is not None
    assert result.stock_code == "005930"
    assert result.predicted_direction == "up"
    assert result.is_correct is True
    assert result.verified_at is not None


def test_create_theme_prediction_accuracy(db_session):
    """Test creating a ThemePredictionAccuracy record."""
    accuracy = ThemePredictionAccuracy(
        prediction_date=date(2026, 2, 19),
        theme="반도체",
        market="KR",
        total_stocks=20,
        correct_count=15,
        accuracy_rate=0.75,
        avg_predicted_score=68.5,
        avg_actual_change_pct=1.85,
        rise_index_at_prediction=72.3,
    )
    db_session.add(accuracy)
    db_session.commit()

    assert accuracy.id is not None
    assert accuracy.theme == "반도체"
    assert accuracy.accuracy_rate == 0.75
    assert accuracy.created_at is not None


def test_create_verification_run_log(db_session):
    """Test creating a VerificationRunLog record."""
    log = VerificationRunLog(
        run_date=date(2026, 2, 19),
        market="KR",
        status="completed",
        stocks_verified=50,
        stocks_failed=2,
        duration_seconds=45.3,
    )
    db_session.add(log)
    db_session.commit()

    assert log.id is not None
    assert log.status == "completed"
    assert log.stocks_verified == 50
    assert log.created_at is not None


def test_daily_result_nullable_fields(db_session):
    """Test DailyPredictionResult with nullable fields."""
    result = DailyPredictionResult(
        prediction_date=date(2026, 2, 19),
        stock_code="AAPL",
        market="US",
        predicted_direction="neutral",
        predicted_score=50.0,
        confidence=0.6,
        news_count=5,
        # Nullable fields intentionally not set
        stock_name=None,
        previous_close_price=None,
        actual_close_price=None,
        actual_change_pct=None,
        actual_direction=None,
        is_correct=None,
        error_message=None,
    )
    db_session.add(result)
    db_session.commit()

    assert result.id is not None
    assert result.stock_name is None
    assert result.actual_close_price is None
    assert result.is_correct is None


def test_daily_result_indexes(db_session):
    """Test that DailyPredictionResult has correct indexes."""
    inspector = inspect(db_session.bind)
    indexes = inspector.get_indexes("daily_prediction_result")

    index_names = {idx["name"] for idx in indexes}

    # Check for key indexes
    assert "idx_prediction_date_stock" in index_names
    assert "idx_market_date" in index_names


def test_verification_log_status_values(db_session):
    """Test VerificationRunLog accepts various status values."""
    statuses = ["running", "completed", "failed", "partial"]

    for status in statuses:
        log = VerificationRunLog(
            run_date=date(2026, 2, 19),
            market="KR",
            status=status,
            stocks_verified=10,
            stocks_failed=0,
            duration_seconds=10.0,
        )
        db_session.add(log)

    db_session.commit()

    logs = db_session.query(VerificationRunLog).all()
    assert len(logs) == 4
    assert {log.status for log in logs} == set(statuses)


def test_daily_result_query_by_date_and_market(db_session):
    """Test querying DailyPredictionResult by date and market."""
    # Create results for different dates and markets
    results = [
        DailyPredictionResult(
            prediction_date=date(2026, 2, 18),
            stock_code="005930",
            market="KR",
            predicted_direction="up",
            predicted_score=80.0,
            confidence=0.9,
            news_count=10,
        ),
        DailyPredictionResult(
            prediction_date=date(2026, 2, 19),
            stock_code="000660",
            market="KR",
            predicted_direction="up",
            predicted_score=75.0,
            confidence=0.85,
            news_count=8,
        ),
        DailyPredictionResult(
            prediction_date=date(2026, 2, 19),
            stock_code="AAPL",
            market="US",
            predicted_direction="neutral",
            predicted_score=55.0,
            confidence=0.7,
            news_count=15,
        ),
    ]
    for result in results:
        db_session.add(result)
    db_session.commit()

    # Query by date and market
    kr_results = (
        db_session.query(DailyPredictionResult)
        .filter(
            DailyPredictionResult.prediction_date == date(2026, 2, 19),
            DailyPredictionResult.market == "KR",
        )
        .all()
    )

    assert len(kr_results) == 1
    assert kr_results[0].stock_code == "000660"
    assert kr_results[0].market == "KR"
