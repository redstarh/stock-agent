"""Tests for training_backfill module."""

from datetime import date, datetime, timedelta

import pandas as pd
import pytest

from app.models.training import StockTrainingData
from app.models.verification import DailyPredictionResult
from app.processing.training_backfill import backfill_training_data


def _insert_prediction_result(
    db_session,
    stock_code="005930",
    stock_name="삼성전자",
    market="KR",
    target_date=None,
    predicted_direction="up",
    predicted_score=75.0,
    confidence=0.8,
    actual_close_price=None,
    actual_change_pct=None,
    actual_direction=None,
    is_correct=None,
):
    """테스트용 DailyPredictionResult 삽입 헬퍼."""
    if target_date is None:
        target_date = date(2026, 2, 19)

    result = DailyPredictionResult(
        prediction_date=target_date,
        stock_code=stock_code,
        stock_name=stock_name,
        market=market,
        predicted_direction=predicted_direction,
        predicted_score=predicted_score,
        confidence=confidence,
        news_count=5,
        actual_close_price=actual_close_price,
        actual_change_pct=actual_change_pct,
        actual_direction=actual_direction,
        is_correct=is_correct,
    )
    db_session.add(result)
    db_session.commit()
    return result


def test_backfill_creates_training_data(db_session, monkeypatch):
    """DailyPredictionResult로부터 StockTrainingData 생성 테스트."""
    target_date = date(2026, 2, 19)

    # Create DailyPredictionResult records
    _insert_prediction_result(
        db_session,
        stock_code="005930",
        stock_name="삼성전자",
        market="KR",
        target_date=target_date,
        predicted_direction="up",
        predicted_score=75.0,
        confidence=0.8,
    )

    # Mock yfinance to avoid network calls
    def mock_download(*args, **kwargs):
        return pd.DataFrame()

    monkeypatch.setattr("yfinance.download", mock_download)
    monkeypatch.setattr("app.processing.technical_indicators.yf.download", mock_download)

    # Run backfill
    result = backfill_training_data(db_session, market="KR", days_back=30)

    # Verify summary
    assert result["created"] == 1
    assert result["skipped"] == 0
    assert result["failed"] == 0
    assert result["dates_processed"] == 1

    # Verify training data was created
    training = (
        db_session.query(StockTrainingData)
        .filter_by(prediction_date=target_date, stock_code="005930")
        .first()
    )
    assert training is not None
    assert training.stock_code == "005930"
    assert training.stock_name == "삼성전자"
    assert training.market == "KR"
    assert training.predicted_direction == "up"
    assert training.predicted_score == 75.0
    assert training.confidence == 0.8


def test_backfill_skips_existing(db_session, monkeypatch):
    """이미 존재하는 레코드는 스킵하는지 테스트."""
    target_date = date(2026, 2, 19)

    # Pre-create a StockTrainingData record
    existing = StockTrainingData(
        prediction_date=target_date,
        stock_code="005930",
        stock_name="삼성전자",
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
    )
    db_session.add(existing)
    db_session.commit()

    # Create DailyPredictionResult for same stock/date
    _insert_prediction_result(
        db_session,
        stock_code="005930",
        stock_name="삼성전자",
        market="KR",
        target_date=target_date,
    )

    # Mock yfinance
    def mock_download(*args, **kwargs):
        return pd.DataFrame()

    monkeypatch.setattr("yfinance.download", mock_download)

    # Run backfill
    result = backfill_training_data(db_session, market="KR", days_back=30)

    # Verify it was skipped
    assert result["created"] == 0
    assert result["skipped"] == 1
    assert result["failed"] == 0

    # Verify no duplicate was created
    count = (
        db_session.query(StockTrainingData)
        .filter_by(prediction_date=target_date, stock_code="005930")
        .count()
    )
    assert count == 1


def test_backfill_dry_run(db_session, monkeypatch):
    """dry_run=True면 레코드 생성하지 않고 카운트만 반환."""
    target_date = date(2026, 2, 19)

    # Create DailyPredictionResult
    _insert_prediction_result(
        db_session,
        stock_code="005930",
        target_date=target_date,
    )

    # Mock yfinance
    def mock_download(*args, **kwargs):
        return pd.DataFrame()

    monkeypatch.setattr("yfinance.download", mock_download)

    # Run backfill with dry_run=True
    result = backfill_training_data(db_session, market="KR", days_back=30, dry_run=True)

    # Verify counts but no actual records created
    assert result["created"] == 1
    assert result["skipped"] == 0
    assert result["failed"] == 0

    # Verify no training data was actually created
    count = db_session.query(StockTrainingData).count()
    assert count == 0


def test_backfill_updates_actuals(db_session, monkeypatch):
    """DailyPredictionResult에 실제 데이터가 있으면 업데이트하는지 테스트."""
    target_date = date(2026, 2, 19)

    # Create DailyPredictionResult with actual data
    _insert_prediction_result(
        db_session,
        stock_code="005930",
        stock_name="삼성전자",
        market="KR",
        target_date=target_date,
        predicted_direction="up",
        predicted_score=75.0,
        confidence=0.8,
        actual_close_price=71500.0,
        actual_change_pct=2.29,
        actual_direction="up",
        is_correct=True,
    )

    # Mock yfinance
    def mock_download(*args, **kwargs):
        return pd.DataFrame()

    monkeypatch.setattr("yfinance.download", mock_download)
    monkeypatch.setattr("app.processing.technical_indicators.yf.download", mock_download)

    # Run backfill
    result = backfill_training_data(db_session, market="KR", days_back=30)

    # Verify training data was created
    assert result["created"] == 1

    # Verify actuals were populated
    training = (
        db_session.query(StockTrainingData)
        .filter_by(prediction_date=target_date, stock_code="005930")
        .first()
    )
    assert training is not None
    assert training.actual_close == 71500.0
    assert training.actual_change_pct == 2.29
    assert training.actual_direction == "up"
    assert training.is_correct is True


def test_backfill_multiple_dates(db_session, monkeypatch):
    """여러 날짜의 데이터를 처리하는지 테스트."""
    dates = [
        date(2026, 2, 17),
        date(2026, 2, 18),
        date(2026, 2, 19),
    ]

    # Create prediction results for multiple dates
    for d in dates:
        _insert_prediction_result(
            db_session,
            stock_code="005930",
            target_date=d,
        )
        _insert_prediction_result(
            db_session,
            stock_code="000660",
            stock_name="SK하이닉스",
            target_date=d,
        )

    # Mock yfinance
    def mock_download(*args, **kwargs):
        return pd.DataFrame()

    monkeypatch.setattr("yfinance.download", mock_download)

    # Run backfill
    result = backfill_training_data(db_session, market="KR", days_back=30)

    # Verify all records were created
    assert result["created"] == 6  # 3 dates × 2 stocks
    assert result["dates_processed"] == 3

    # Verify training data exists for all combinations
    for d in dates:
        for code in ["005930", "000660"]:
            training = (
                db_session.query(StockTrainingData)
                .filter_by(prediction_date=d, stock_code=code)
                .first()
            )
            assert training is not None


def test_backfill_handles_errors(db_session, monkeypatch):
    """개별 종목 처리 실패 시 계속 진행하는지 테스트."""
    target_date = date(2026, 2, 19)

    # Create prediction results
    _insert_prediction_result(
        db_session,
        stock_code="005930",
        target_date=target_date,
    )
    _insert_prediction_result(
        db_session,
        stock_code="000660",
        target_date=target_date,
    )

    # Mock yfinance
    def mock_download(*args, **kwargs):
        return pd.DataFrame()

    monkeypatch.setattr("yfinance.download", mock_download)

    # Mock build_training_snapshot to fail for one stock
    original_build = None
    call_count = [0]

    def mock_build(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise Exception("Simulated error")
        return original_build(*args, **kwargs)

    from app.processing import training_data_builder
    original_build = training_data_builder.build_training_snapshot
    monkeypatch.setattr("app.processing.training_backfill.build_training_snapshot", mock_build)

    # Run backfill
    result = backfill_training_data(db_session, market="KR", days_back=30)

    # Verify one failed, one succeeded
    assert result["created"] == 1
    assert result["failed"] == 1
    assert result["dates_processed"] == 1


def test_backfill_empty_results(db_session):
    """DailyPredictionResult가 없으면 처리할 것이 없음."""
    result = backfill_training_data(db_session, market="KR", days_back=30)

    assert result["created"] == 0
    assert result["skipped"] == 0
    assert result["failed"] == 0
    assert result["dates_processed"] == 0


def test_backfill_market_filter(db_session, monkeypatch):
    """시장 필터가 정확히 작동하는지 테스트."""
    target_date = date(2026, 2, 19)

    # Create prediction results for different markets
    _insert_prediction_result(
        db_session,
        stock_code="005930",
        market="KR",
        target_date=target_date,
    )
    _insert_prediction_result(
        db_session,
        stock_code="AAPL",
        stock_name="Apple",
        market="US",
        target_date=target_date,
    )

    # Mock yfinance
    def mock_download(*args, **kwargs):
        return pd.DataFrame()

    monkeypatch.setattr("yfinance.download", mock_download)

    # Run backfill for KR market only
    result = backfill_training_data(db_session, market="KR", days_back=30)

    # Verify only KR market was processed
    assert result["created"] == 1

    # Verify KR training data exists
    kr_training = (
        db_session.query(StockTrainingData)
        .filter_by(prediction_date=target_date, stock_code="005930")
        .first()
    )
    assert kr_training is not None

    # Verify US training data does not exist
    us_training = (
        db_session.query(StockTrainingData)
        .filter_by(prediction_date=target_date, stock_code="AAPL")
        .first()
    )
    assert us_training is None
