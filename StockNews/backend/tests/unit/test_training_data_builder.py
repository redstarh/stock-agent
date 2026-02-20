"""Tests for training_data_builder module."""

from datetime import date, datetime, timedelta

import pandas as pd
import pytest

from app.models.news_event import NewsEvent
from app.models.training import StockTrainingData
from app.processing.training_data_builder import (
    build_training_snapshot,
    export_training_csv,
    update_training_actuals,
)


def _insert_news(db_session, stock_code="005930", market="KR", count=5, target_date=None):
    """테스트용 뉴스 삽입 헬퍼."""
    if target_date is None:
        target_date = date(2026, 2, 19)
    for i in range(count):
        news = NewsEvent(
            market=market,
            stock_code=stock_code,
            stock_name="삼성전자",
            title=f"뉴스 {i}",
            sentiment="positive",
            sentiment_score=0.5,
            news_score=70.0,
            source="test",
            theme="반도체",
            created_at=datetime.combine(target_date - timedelta(days=i), datetime.min.time()),
        )
        db_session.add(news)
    db_session.commit()


def test_build_training_snapshot_basic(db_session, monkeypatch):
    """기본 스냅샷 생성 테스트."""
    target_date = date(2026, 2, 19)
    _insert_news(db_session, target_date=target_date)

    # Mock yfinance to avoid network calls
    mock_df = pd.DataFrame({
        "Close": [69000 + i * 500 for i in range(30)],
        "Open": [68500 + i * 500 for i in range(30)],
        "High": [69500 + i * 500 for i in range(30)],
        "Low": [68000 + i * 500 for i in range(30)],
        "Volume": [1000000 + i * 10000 for i in range(30)],
    }, index=pd.date_range("2026-01-15", periods=30))

    def mock_download(*args, **kwargs):
        return mock_df

    monkeypatch.setattr("yfinance.download", mock_download)
    monkeypatch.setattr(
        "app.processing.technical_indicators.yf.download",
        mock_download,
    )
    monkeypatch.setattr(
        "app.processing.training_data_builder.calc_cross_theme_score",
        lambda db, theme, stock_code, market, target_date: 0.0,
    )

    record = build_training_snapshot(
        db=db_session,
        stock_code="005930",
        stock_name="삼성전자",
        market="KR",
        target_date=target_date,
        prediction={"direction": "up", "score": 75.0, "confidence": 0.8},
    )

    assert record is not None
    assert record.stock_code == "005930"
    assert record.market == "KR"
    assert record.predicted_direction == "up"
    assert record.predicted_score == 75.0
    assert record.confidence == 0.8
    assert record.news_score > 0
    assert record.news_count == 5
    assert record.theme == "반도체"
    assert record.day_of_week == target_date.weekday()
    # Actuals should be None initially
    assert record.actual_close is None
    assert record.is_correct is None


def test_build_training_snapshot_no_news(db_session, monkeypatch):
    """뉴스 없는 종목 스냅샷."""
    # Mock yfinance
    def mock_download(*args, **kwargs):
        return pd.DataFrame()

    monkeypatch.setattr("yfinance.download", mock_download)
    monkeypatch.setattr(
        "app.processing.technical_indicators.yf.download",
        mock_download,
    )
    monkeypatch.setattr(
        "app.processing.training_data_builder.calc_cross_theme_score",
        lambda db, theme, stock_code, market, target_date: 0.0,
    )

    record = build_training_snapshot(
        db=db_session,
        stock_code="999999",
        stock_name="Unknown",
        market="KR",
        target_date=date(2026, 2, 19),
        prediction={"direction": "neutral", "score": 50.0, "confidence": 0.0},
    )

    assert record.news_score == 0.0
    assert record.news_count == 0
    assert record.predicted_direction == "neutral"


def test_update_training_actuals(db_session):
    """실제 결과 업데이트 테스트."""
    target_date = date(2026, 2, 19)

    # Insert training record directly
    record = StockTrainingData(
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
    db_session.add(record)
    db_session.commit()

    # Update with actual data
    price_data = {
        "005930": {
            "current_close": 71500.0,
            "change_pct": 2.29,
            "volume": 5000000,
        }
    }

    updated = update_training_actuals(db_session, target_date, "KR", price_data)
    db_session.commit()

    assert updated == 1

    # Verify record was updated
    r = db_session.query(StockTrainingData).filter_by(
        prediction_date=target_date, stock_code="005930"
    ).first()
    assert r.actual_close == 71500.0
    assert r.actual_change_pct == 2.29
    assert r.actual_direction == "up"
    assert r.actual_volume == 5000000
    assert r.is_correct is True


def test_update_training_actuals_down(db_session):
    """하락 예측 vs 하락 실제 → correct."""
    target_date = date(2026, 2, 18)

    record = StockTrainingData(
        prediction_date=target_date,
        stock_code="000660",
        stock_name="SK하이닉스",
        market="KR",
        news_score=30.0,
        sentiment_score=-0.5,
        news_count=3,
        news_count_3d=1,
        avg_score_3d=25.0,
        disclosure_ratio=0.0,
        sentiment_trend=-0.1,
        day_of_week=1,
        predicted_direction="down",
        predicted_score=35.0,
        confidence=0.6,
    )
    db_session.add(record)
    db_session.commit()

    price_data = {
        "000660": {
            "current_close": 125000.0,
            "change_pct": -3.5,
            "volume": 2000000,
        }
    }

    updated = update_training_actuals(db_session, target_date, "KR", price_data)
    db_session.commit()

    assert updated == 1
    r = db_session.query(StockTrainingData).filter_by(
        prediction_date=target_date, stock_code="000660"
    ).first()
    assert r.actual_direction == "down"
    assert r.is_correct is True


def test_update_training_actuals_no_match(db_session):
    """매칭 레코드 없을 때 0 반환."""
    updated = update_training_actuals(
        db_session, date(2099, 1, 1), "KR", {"005930": {"current_close": 100.0}}
    )
    assert updated == 0


def test_export_training_csv(db_session):
    """CSV 내보내기 테스트."""
    target_date = date(2026, 2, 19)

    record = StockTrainingData(
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
        actual_close=71500.0,
        actual_change_pct=2.29,
        actual_direction="up",
        is_correct=True,
    )
    db_session.add(record)
    db_session.commit()

    csv_str = export_training_csv(db_session, "KR", target_date - timedelta(days=1), target_date)

    assert csv_str is not None
    lines = csv_str.strip().split("\n")
    assert len(lines) == 2  # header + 1 data row

    header = lines[0]
    assert "prediction_date" in header
    assert "stock_code" in header
    assert "news_score" in header
    assert "actual_close" in header
    assert "is_correct" in header

    data = lines[1]
    assert "005930" in data
    assert "삼성전자" in data
    assert "up" in data


def test_export_training_csv_empty(db_session):
    """빈 데이터 CSV."""
    csv_str = export_training_csv(db_session, "KR", date(2099, 1, 1), date(2099, 1, 31))
    lines = csv_str.strip().split("\n")
    assert len(lines) == 1  # header only
