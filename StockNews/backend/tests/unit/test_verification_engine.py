"""Tests for verification_engine.py"""

import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock

from app.models.news_event import NewsEvent
from app.models.verification import DailyPredictionResult, VerificationRunLog
from app.processing.verification_engine import (
    get_stocks_with_news,
    calculate_prediction_for_stock,
    run_verification,
)


def test_get_stocks_with_news_returns_stocks(db_session):
    """Test that get_stocks_with_news returns stocks with sufficient news."""
    target_date = date(2026, 2, 19)

    # Insert 5 news for stock A
    for i in range(5):
        news = NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title=f"삼성 뉴스 {i}",
            sentiment="positive",
            sentiment_score=0.5,
            news_score=70.0,
            source="test",
            created_at=datetime.combine(target_date - timedelta(days=i), datetime.min.time()),
        )
        db_session.add(news)

    # Insert 1 news for stock B (below threshold)
    news_b = NewsEvent(
        market="KR",
        stock_code="000660",
        stock_name="SK하이닉스",
        title="SK 뉴스",
        sentiment="neutral",
        sentiment_score=0.0,
        news_score=50.0,
        source="test",
        created_at=datetime.combine(target_date, datetime.min.time()),
    )
    db_session.add(news_b)
    db_session.commit()

    # Get stocks with min_news_count=3
    stocks = get_stocks_with_news(db_session, target_date, "KR", min_news_count=3)

    assert len(stocks) == 1
    assert stocks[0]["stock_code"] == "005930"
    assert stocks[0]["stock_name"] == "삼성전자"
    assert stocks[0]["news_count"] >= 3


def test_get_stocks_with_news_empty(db_session):
    """Test that get_stocks_with_news returns empty list when no news."""
    target_date = date(2026, 2, 19)
    stocks = get_stocks_with_news(db_session, target_date, "KR")
    assert stocks == []


def test_calculate_prediction_up(db_session):
    """Test prediction returns 'up' direction for high scores."""
    target_date = date(2026, 2, 19)

    # Insert news with high scores
    for i in range(10):
        news = NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title=f"긍정 뉴스 {i}",
            sentiment="positive",
            sentiment_score=0.7,
            news_score=80.0,
            source="test",
            created_at=datetime.combine(target_date - timedelta(days=i), datetime.min.time()),
        )
        db_session.add(news)
    db_session.commit()

    pred = calculate_prediction_for_stock(db_session, "005930", "KR", target_date)

    assert pred["stock_code"] == "005930"
    assert pred["stock_name"] == "삼성전자"
    assert pred["direction"] == "up"
    assert pred["score"] > 60
    assert pred["confidence"] > 0
    assert pred["news_count"] == 10


def test_calculate_prediction_down(db_session):
    """Test prediction returns 'down' direction for low scores."""
    target_date = date(2026, 2, 19)

    # Insert news with low scores
    for i in range(10):
        news = NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title=f"부정 뉴스 {i}",
            sentiment="negative",
            sentiment_score=-0.7,
            news_score=20.0,
            source="test",
            created_at=datetime.combine(target_date - timedelta(days=i), datetime.min.time()),
        )
        db_session.add(news)
    db_session.commit()

    pred = calculate_prediction_for_stock(db_session, "005930", "KR", target_date)

    assert pred["direction"] == "down"
    assert pred["score"] < 40


def test_calculate_prediction_neutral(db_session):
    """Test prediction returns 'neutral' direction for medium scores."""
    target_date = date(2026, 2, 19)

    # Insert news with neutral scores
    for i in range(10):
        news = NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title=f"중립 뉴스 {i}",
            sentiment="neutral",
            sentiment_score=0.0,
            news_score=50.0,
            source="test",
            created_at=datetime.combine(target_date - timedelta(days=i), datetime.min.time()),
        )
        db_session.add(news)
    db_session.commit()

    pred = calculate_prediction_for_stock(db_session, "005930", "KR", target_date)

    assert pred["direction"] == "neutral"
    assert 40 <= pred["score"] <= 60


def test_calculate_prediction_no_news(db_session):
    """Test prediction returns neutral with zero confidence when no news."""
    target_date = date(2026, 2, 19)

    pred = calculate_prediction_for_stock(db_session, "999999", "KR", target_date)

    assert pred["stock_code"] == "999999"
    assert pred["stock_name"] is None
    assert pred["direction"] == "neutral"
    assert pred["score"] == 50.0
    assert pred["confidence"] == 0.0
    assert pred["news_count"] == 0


def test_calculate_prediction_confidence(db_session):
    """Test that confidence increases with more news."""
    target_date = date(2026, 2, 19)

    # Insert 20 news items
    for i in range(20):
        news = NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title=f"뉴스 {i}",
            sentiment="positive",
            sentiment_score=0.5,
            news_score=80.0,
            source="test",
            created_at=datetime.combine(target_date - timedelta(days=i), datetime.min.time()),
        )
        db_session.add(news)
    db_session.commit()

    pred = calculate_prediction_for_stock(db_session, "005930", "KR", target_date)

    # volume_conf = min(1.0, 20 / 20) * 0.5 = 0.5
    # extremity_conf = abs(score - 50) / 100
    # With high score (>60), confidence should be significant
    assert pred["confidence"] >= 0.5


@pytest.mark.asyncio
async def test_run_verification_success(db_session, monkeypatch):
    """Test successful verification run."""
    target_date = date(2026, 2, 19)

    # Insert news for stocks
    for i in range(5):
        news = NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title=f"뉴스 {i}",
            sentiment="positive",
            sentiment_score=0.5,
            news_score=70.0,
            source="test",
            created_at=datetime.combine(target_date - timedelta(days=i), datetime.min.time()),
        )
        db_session.add(news)
    db_session.commit()

    # Mock fetch_prices_batch
    async def mock_fetch(stock_codes, market, target_date):
        return {
            "005930": {
                "previous_close": 70000.0,
                "current_close": 71600.0,
                "change_pct": 2.29,
            }
        }

    monkeypatch.setattr(
        "app.processing.verification_engine.fetch_prices_batch",
        mock_fetch
    )

    run_log = await run_verification(db_session, target_date, "KR")

    assert run_log.status == "success"
    assert run_log.stocks_verified == 1
    assert run_log.stocks_failed == 0
    assert run_log.duration_seconds > 0

    # Check result was saved
    result = db_session.query(DailyPredictionResult).filter_by(
        prediction_date=target_date,
        stock_code="005930"
    ).first()

    assert result is not None
    assert result.predicted_direction == "up"
    assert result.actual_direction == "up"
    assert result.is_correct is True


@pytest.mark.asyncio
async def test_run_verification_no_stocks(db_session, monkeypatch):
    """Test verification with no stocks (no news)."""
    target_date = date(2026, 2, 19)

    run_log = await run_verification(db_session, target_date, "KR")

    assert run_log.status == "success"
    assert run_log.stocks_verified == 0
    assert run_log.stocks_failed == 0


@pytest.mark.asyncio
async def test_run_verification_price_failure(db_session, monkeypatch):
    """Test verification when price data is unavailable."""
    target_date = date(2026, 2, 19)

    # Insert news
    for i in range(5):
        news = NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title=f"뉴스 {i}",
            sentiment="positive",
            sentiment_score=0.5,
            news_score=70.0,
            source="test",
            created_at=datetime.combine(target_date - timedelta(days=i), datetime.min.time()),
        )
        db_session.add(news)
    db_session.commit()

    # Mock fetch_prices_batch to return None
    async def mock_fetch(stock_codes, market, target_date):
        return {"005930": None}

    monkeypatch.setattr(
        "app.processing.verification_engine.fetch_prices_batch",
        mock_fetch
    )

    run_log = await run_verification(db_session, target_date, "KR")

    assert run_log.status == "partial"
    assert run_log.stocks_verified == 0
    assert run_log.stocks_failed == 1

    # Check result has error
    result = db_session.query(DailyPredictionResult).filter_by(
        prediction_date=target_date,
        stock_code="005930"
    ).first()

    assert result is not None
    assert result.error_message == "Price data unavailable"
    assert result.is_correct is None
