"""Verification API 엔드포인트 테스트."""

import asyncio
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.verification import (
    DailyPredictionResult,
    ThemePredictionAccuracy,
    VerificationRunLog,
)


@pytest.fixture
def client(db_session, monkeypatch):
    """Test client with overridden DB dependency."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_daily_results(db_session):
    """Sample daily prediction results."""
    today = date.today()
    results = [
        DailyPredictionResult(
            prediction_date=today,
            stock_code="005930",
            stock_name="삼성전자",
            market="KR",
            predicted_direction="up",
            predicted_score=75.0,
            confidence=0.8,
            news_count=10,
            previous_close_price=70000,
            actual_close_price=72000,
            actual_change_pct=2.86,
            actual_direction="up",
            is_correct=True,
            verified_at=datetime.now(timezone.utc),
        ),
        DailyPredictionResult(
            prediction_date=today,
            stock_code="000660",
            stock_name="SK하이닉스",
            market="KR",
            predicted_direction="down",
            predicted_score=35.0,
            confidence=0.6,
            news_count=5,
            previous_close_price=120000,
            actual_close_price=118000,
            actual_change_pct=-1.67,
            actual_direction="down",
            is_correct=True,
            verified_at=datetime.now(timezone.utc),
        ),
        DailyPredictionResult(
            prediction_date=today,
            stock_code="AAPL",
            stock_name="Apple Inc",
            market="US",
            predicted_direction="up",
            predicted_score=65.0,
            confidence=0.7,
            news_count=8,
            previous_close_price=150.0,
            actual_close_price=148.0,
            actual_change_pct=-1.33,
            actual_direction="down",
            is_correct=False,
            verified_at=datetime.now(timezone.utc),
        ),
        DailyPredictionResult(
            prediction_date=today,
            stock_code="TSLA",
            stock_name="Tesla Inc",
            market="US",
            predicted_direction="neutral",
            predicted_score=50.0,
            confidence=0.5,
            news_count=3,
            error_message="Price data unavailable",
        ),
    ]
    for r in results:
        db_session.add(r)
    db_session.commit()
    return results


@pytest.fixture
def sample_theme_accuracy(db_session):
    """Sample theme accuracy data."""
    today = date.today()
    themes = [
        ThemePredictionAccuracy(
            prediction_date=today,
            theme="반도체",
            market="KR",
            total_stocks=5,
            correct_count=4,
            accuracy_rate=0.8,
            avg_predicted_score=72.0,
            avg_actual_change_pct=1.5,
        ),
        ThemePredictionAccuracy(
            prediction_date=today,
            theme="자동차",
            market="KR",
            total_stocks=3,
            correct_count=2,
            accuracy_rate=0.6667,
            avg_predicted_score=68.0,
            avg_actual_change_pct=0.8,
        ),
    ]
    for t in themes:
        db_session.add(t)
    db_session.commit()
    return themes


@pytest.fixture
def sample_run_logs(db_session):
    """Sample verification run logs."""
    today = date.today()
    logs = [
        VerificationRunLog(
            run_date=today,
            market="KR",
            status="success",
            stocks_verified=10,
            stocks_failed=0,
            duration_seconds=15.5,
            created_at=datetime.now(timezone.utc),
        ),
        VerificationRunLog(
            run_date=today,
            market="US",
            status="partial",
            stocks_verified=8,
            stocks_failed=2,
            duration_seconds=20.3,
            created_at=datetime.now(timezone.utc),
        ),
    ]
    for log in logs:
        db_session.add(log)
    db_session.commit()
    return logs


def test_get_daily_results(client, sample_daily_results):
    """Test GET /verification/daily endpoint."""
    today = date.today()
    response = client.get(f"/api/v1/verification/daily?date={today}")

    assert response.status_code == 200
    data = response.json()
    assert data["date"] == str(today)
    assert data["market"] == "ALL"
    assert data["total"] == 4
    assert data["correct"] == 2  # 삼성전자 + SK하이닉스
    assert data["accuracy"] == 50.0  # 2/4 * 100
    assert len(data["results"]) == 4


def test_get_daily_results_market_filter(client, sample_daily_results):
    """Test GET /verification/daily with market filter."""
    today = date.today()
    response = client.get(f"/api/v1/verification/daily?date={today}&market=KR")

    assert response.status_code == 200
    data = response.json()
    assert data["market"] == "KR"
    assert data["total"] == 2
    assert len(data["results"]) == 2
    assert all(r["stock_code"] in ["005930", "000660"] for r in data["results"])


def test_get_daily_results_empty(client):
    """Test GET /verification/daily with no data."""
    yesterday = date.today() - timedelta(days=1)
    response = client.get(f"/api/v1/verification/daily?date={yesterday}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["correct"] == 0
    assert data["accuracy"] == 0.0
    assert data["results"] == []


def test_get_accuracy(client, sample_daily_results):
    """Test GET /verification/accuracy endpoint."""
    response = client.get("/api/v1/verification/accuracy?days=30")

    assert response.status_code == 200
    data = response.json()
    assert data["period_days"] == 30
    assert data["market"] == "ALL"
    assert data["total_predictions"] == 3  # Only verified results
    assert data["correct_predictions"] == 2
    assert data["overall_accuracy"] == pytest.approx(66.7, abs=0.1)
    assert "by_direction" in data
    assert "daily_trend" in data


def test_get_accuracy_by_direction(client, sample_daily_results):
    """Test accuracy breakdown by direction."""
    response = client.get("/api/v1/verification/accuracy?days=30")

    assert response.status_code == 200
    data = response.json()
    by_dir = data["by_direction"]
    assert "up" in by_dir
    assert "down" in by_dir
    assert "neutral" in by_dir
    # up: 1 correct out of 2 predictions
    assert by_dir["up"]["total"] == 2
    assert by_dir["up"]["correct"] == 1
    assert by_dir["up"]["accuracy"] == 50.0
    # down: 1 correct out of 1 prediction
    assert by_dir["down"]["total"] == 1
    assert by_dir["down"]["correct"] == 1
    assert by_dir["down"]["accuracy"] == 100.0


def test_get_accuracy_market_filter(client, sample_daily_results):
    """Test GET /verification/accuracy with market filter."""
    response = client.get("/api/v1/verification/accuracy?days=30&market=KR")

    assert response.status_code == 200
    data = response.json()
    assert data["market"] == "KR"
    assert data["total_predictions"] == 2
    assert data["correct_predictions"] == 2
    assert data["overall_accuracy"] == 100.0


def test_get_themes(client, sample_theme_accuracy):
    """Test GET /verification/themes endpoint."""
    today = date.today()
    response = client.get(f"/api/v1/verification/themes?date={today}")

    assert response.status_code == 200
    data = response.json()
    assert data["date"] == str(today)
    assert data["market"] == "ALL"
    assert len(data["themes"]) == 2
    # Should be sorted by accuracy_rate desc
    assert data["themes"][0]["theme"] == "반도체"
    assert data["themes"][0]["accuracy_rate"] == 80.0


def test_get_themes_market_filter(client, sample_theme_accuracy):
    """Test GET /verification/themes with market filter."""
    today = date.today()
    response = client.get(f"/api/v1/verification/themes?date={today}&market=KR")

    assert response.status_code == 200
    data = response.json()
    assert data["market"] == "KR"
    assert len(data["themes"]) == 2


def test_get_themes_trend(client, db_session):
    """Test GET /verification/themes/trend endpoint."""
    # Insert multi-day data
    dates = [date.today() - timedelta(days=i) for i in range(5)]
    for d in dates:
        theme = ThemePredictionAccuracy(
            prediction_date=d,
            theme="반도체",
            market="KR",
            total_stocks=5,
            correct_count=4,
            accuracy_rate=0.8,
            avg_predicted_score=70.0,
        )
        db_session.add(theme)
    db_session.commit()

    response = client.get("/api/v1/verification/themes/trend?theme=반도체&days=30")

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "반도체"
    assert data["market"] == "ALL"
    assert len(data["trend"]) == 5


def test_get_stock_history(client, db_session):
    """Test GET /verification/stocks/{code}/history endpoint."""
    # Insert multi-day data for a stock
    stock_code = "005930"
    dates = [date.today() - timedelta(days=i) for i in range(3)]
    for d in dates:
        result = DailyPredictionResult(
            prediction_date=d,
            stock_code=stock_code,
            stock_name="삼성전자",
            market="KR",
            predicted_direction="up",
            predicted_score=75.0,
            confidence=0.8,
            news_count=10,
            actual_direction="up",
            actual_change_pct=2.0,
            is_correct=True,
        )
        db_session.add(result)
    db_session.commit()

    response = client.get(f"/api/v1/verification/stocks/{stock_code}/history?days=30")

    assert response.status_code == 200
    data = response.json()
    assert data["stock_code"] == stock_code
    assert data["stock_name"] == "삼성전자"
    assert data["market"] == "KR"
    assert data["total_predictions"] == 3
    assert data["correct_predictions"] == 3
    assert data["accuracy_rate"] == 1.0
    assert len(data["history"]) == 3


def test_get_stock_history_empty(client):
    """Test GET /verification/stocks/{code}/history with no data."""
    response = client.get("/api/v1/verification/stocks/UNKNOWN/history?days=30")

    assert response.status_code == 200
    data = response.json()
    assert data["stock_code"] == "UNKNOWN"
    assert data["total_predictions"] == 0
    assert data["history"] == []


@patch("app.api.verification.run_verification", new_callable=AsyncMock)
@patch("app.api.verification.aggregate_theme_accuracy")
def test_post_run_trigger(mock_aggregate, mock_verify, client, db_session):
    """Test POST /verification/run endpoint."""
    # Mock the verification engine
    mock_log = VerificationRunLog(
        run_date=date.today(),
        market="KR",
        status="success",
        stocks_verified=10,
        stocks_failed=0,
        duration_seconds=15.0,
    )
    mock_verify.return_value = mock_log

    today_str = date.today().isoformat()
    response = client.post(f"/api/v1/verification/run?date={today_str}&market=KR")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "triggered"
    assert data["market"] == "KR"
    assert data["run_date"] == today_str


def test_get_status(client, sample_run_logs):
    """Test GET /verification/status endpoint."""
    response = client.get("/api/v1/verification/status")

    assert response.status_code == 200
    data = response.json()
    assert "current_date" in data
    assert len(data["markets"]) == 2

    kr_market = next(m for m in data["markets"] if m["market"] == "KR")
    assert kr_market["status"] == "success"
    assert kr_market["stocks_verified"] == 10

    us_market = next(m for m in data["markets"] if m["market"] == "US")
    assert us_market["status"] == "partial"
    assert us_market["stocks_verified"] == 8


def test_get_status_no_logs(client):
    """Test GET /verification/status with no run logs."""
    response = client.get("/api/v1/verification/status")

    assert response.status_code == 200
    data = response.json()
    assert len(data["markets"]) == 2
    # Both markets should have None for last_run_date
    assert all(m["last_run_date"] is None for m in data["markets"])


def test_daily_many_results(client, db_session):
    """Test daily results endpoint with many results."""
    today = date.today()
    # Insert 100 results
    for i in range(100):
        result = DailyPredictionResult(
            prediction_date=today,
            stock_code=f"{i:06d}",
            stock_name=f"Stock {i}",
            market="KR",
            predicted_direction="up",
            predicted_score=70.0,
            confidence=0.7,
            news_count=5,
            is_correct=True,
        )
        db_session.add(result)
    db_session.commit()

    response = client.get(f"/api/v1/verification/daily?date={today}&market=KR")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 100
    assert len(data["results"]) == 100
    assert data["correct"] == 100
