"""Integration tests for Verification API endpoints."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.verification import (
    DailyPredictionResult,
    ThemePredictionAccuracy,
    VerificationRunLog,
)


@pytest.fixture
async def async_client():
    """FastAPI 비동기 테스트 클라이언트."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def clean_verification_tables(integration_session_factory):
    """각 테스트 전에 검증 테이블 정리."""
    session = integration_session_factory()
    try:
        session.query(DailyPredictionResult).delete()
        session.query(ThemePredictionAccuracy).delete()
        session.query(VerificationRunLog).delete()
        session.commit()
    finally:
        session.close()
    yield


class TestDailyVerificationEndpoint:
    """GET /api/v1/verification/daily 테스트."""

    @pytest.mark.asyncio
    async def test_get_daily_results_all_markets(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """일별 검증 결과 조회 (전체 시장)."""
        session = integration_session_factory()
        today = date.today()

        # Insert test data
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
        ]
        session.add_all(results)
        session.commit()
        session.close()

        response = await async_client.get(f"/api/v1/verification/daily?date={today}")

        assert response.status_code == 200
        data = response.json()
        assert data["date"] == str(today)
        assert data["market"] == "ALL"
        assert data["total"] == 3
        assert data["correct"] == 2  # 삼성전자 + SK하이닉스
        assert data["accuracy"] == pytest.approx(66.7, abs=0.1)
        assert len(data["results"]) == 3

        # Check first result structure
        first = data["results"][0]
        assert "stock_code" in first
        assert "stock_name" in first
        assert "predicted_direction" in first
        assert "predicted_score" in first
        assert "confidence" in first
        assert "actual_direction" in first
        assert "actual_change_pct" in first
        assert "is_correct" in first
        assert "news_count" in first

    @pytest.mark.asyncio
    async def test_get_daily_results_kr_market_filter(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """일별 검증 결과 조회 (KR 시장 필터)."""
        session = integration_session_factory()
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
                is_correct=True,
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
                is_correct=False,
            ),
        ]
        session.add_all(results)
        session.commit()
        session.close()

        response = await async_client.get(
            f"/api/v1/verification/daily?date={today}&market=KR"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["market"] == "KR"
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["stock_code"] == "005930"

    @pytest.mark.asyncio
    async def test_get_daily_results_with_failed_stocks(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """일별 검증 결과 조회 (실패 포함)."""
        session = integration_session_factory()
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
                is_correct=True,
            ),
            DailyPredictionResult(
                prediction_date=today,
                stock_code="000660",
                stock_name="SK하이닉스",
                market="KR",
                predicted_direction="up",
                predicted_score=70.0,
                confidence=0.7,
                news_count=5,
                is_correct=None,  # Failed verification
                error_message="Price data unavailable",
            ),
        ]
        session.add_all(results)
        session.commit()
        session.close()

        response = await async_client.get(f"/api/v1/verification/daily?date={today}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["correct"] == 1
        assert data["accuracy"] == 50.0

        # Check failed stock has error message
        failed = next(r for r in data["results"] if r["stock_code"] == "000660")
        assert failed["is_correct"] is None
        assert failed["error_message"] == "Price data unavailable"

    @pytest.mark.asyncio
    async def test_get_daily_results_empty(self, async_client: AsyncClient):
        """일별 검증 결과 조회 (데이터 없음)."""
        yesterday = date.today() - timedelta(days=1)
        response = await async_client.get(
            f"/api/v1/verification/daily?date={yesterday}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["correct"] == 0
        assert data["accuracy"] == 0.0
        assert data["results"] == []


class TestAccuracySummaryEndpoint:
    """GET /api/v1/verification/accuracy 테스트."""

    @pytest.mark.asyncio
    async def test_get_accuracy_summary(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """전체 정확도 요약 조회."""
        session = integration_session_factory()
        today = date.today()

        # Insert results for last 5 days
        for i in range(5):
            d = today - timedelta(days=i)
            results = [
                DailyPredictionResult(
                    prediction_date=d,
                    stock_code=f"00593{i}",
                    stock_name=f"Stock {i}",
                    market="KR",
                    predicted_direction="up",
                    predicted_score=75.0,
                    confidence=0.8,
                    news_count=10,
                    is_correct=True,
                ),
                DailyPredictionResult(
                    prediction_date=d,
                    stock_code=f"00066{i}",
                    stock_name=f"Stock {i}",
                    market="KR",
                    predicted_direction="down",
                    predicted_score=35.0,
                    confidence=0.6,
                    news_count=5,
                    is_correct=False,
                ),
            ]
            session.add_all(results)
        session.commit()
        session.close()

        response = await async_client.get("/api/v1/verification/accuracy?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 30
        assert data["market"] == "ALL"
        assert data["total_predictions"] == 10
        assert data["correct_predictions"] == 5
        assert data["overall_accuracy"] == 50.0
        assert "by_direction" in data
        assert "daily_trend" in data
        assert len(data["daily_trend"]) == 5

    @pytest.mark.asyncio
    async def test_get_accuracy_by_direction(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """방향별 정확도 분석."""
        session = integration_session_factory()
        today = date.today()

        results = [
            # 2 correct up predictions
            DailyPredictionResult(
                prediction_date=today,
                stock_code="001",
                stock_name="Stock 1",
                market="KR",
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
                news_count=10,
                is_correct=True,
            ),
            DailyPredictionResult(
                prediction_date=today,
                stock_code="002",
                stock_name="Stock 2",
                market="KR",
                predicted_direction="up",
                predicted_score=70.0,
                confidence=0.7,
                news_count=8,
                is_correct=True,
            ),
            # 1 incorrect up prediction
            DailyPredictionResult(
                prediction_date=today,
                stock_code="003",
                stock_name="Stock 3",
                market="KR",
                predicted_direction="up",
                predicted_score=65.0,
                confidence=0.6,
                news_count=5,
                is_correct=False,
            ),
            # 1 correct down prediction
            DailyPredictionResult(
                prediction_date=today,
                stock_code="004",
                stock_name="Stock 4",
                market="KR",
                predicted_direction="down",
                predicted_score=30.0,
                confidence=0.7,
                news_count=5,
                is_correct=True,
            ),
            # 1 correct neutral prediction
            DailyPredictionResult(
                prediction_date=today,
                stock_code="005",
                stock_name="Stock 5",
                market="KR",
                predicted_direction="neutral",
                predicted_score=50.0,
                confidence=0.5,
                news_count=3,
                is_correct=True,
            ),
        ]
        session.add_all(results)
        session.commit()
        session.close()

        response = await async_client.get("/api/v1/verification/accuracy?days=30")

        assert response.status_code == 200
        data = response.json()
        by_dir = data["by_direction"]
        # up: 2 correct out of 3
        assert by_dir["up"]["total"] == 3
        assert by_dir["up"]["correct"] == 2
        assert by_dir["up"]["accuracy"] == pytest.approx(66.7, abs=0.1)
        # down: 1 correct out of 1
        assert by_dir["down"]["total"] == 1
        assert by_dir["down"]["correct"] == 1
        assert by_dir["down"]["accuracy"] == 100.0
        # neutral: 1 correct out of 1
        assert by_dir["neutral"]["total"] == 1
        assert by_dir["neutral"]["correct"] == 1
        assert by_dir["neutral"]["accuracy"] == 100.0

    @pytest.mark.asyncio
    async def test_get_accuracy_market_filter(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """정확도 요약 (시장 필터)."""
        session = integration_session_factory()
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
                is_correct=True,
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
                is_correct=False,
            ),
        ]
        session.add_all(results)
        session.commit()
        session.close()

        response = await async_client.get(
            "/api/v1/verification/accuracy?days=30&market=KR"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["market"] == "KR"
        assert data["total_predictions"] == 1
        assert data["correct_predictions"] == 1
        assert data["overall_accuracy"] == 100.0

    @pytest.mark.asyncio
    async def test_get_accuracy_daily_trend(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """일별 정확도 추이."""
        session = integration_session_factory()
        today = date.today()

        # Day 1: 100% accuracy (2/2)
        day1 = [
            DailyPredictionResult(
                prediction_date=today - timedelta(days=2),
                stock_code="001",
                stock_name="Stock 1",
                market="KR",
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
                news_count=10,
                is_correct=True,
            ),
            DailyPredictionResult(
                prediction_date=today - timedelta(days=2),
                stock_code="002",
                stock_name="Stock 2",
                market="KR",
                predicted_direction="down",
                predicted_score=30.0,
                confidence=0.7,
                news_count=5,
                is_correct=True,
            ),
        ]

        # Day 2: 50% accuracy (1/2)
        day2 = [
            DailyPredictionResult(
                prediction_date=today - timedelta(days=1),
                stock_code="003",
                stock_name="Stock 3",
                market="KR",
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
                news_count=10,
                is_correct=True,
            ),
            DailyPredictionResult(
                prediction_date=today - timedelta(days=1),
                stock_code="004",
                stock_name="Stock 4",
                market="KR",
                predicted_direction="up",
                predicted_score=70.0,
                confidence=0.7,
                news_count=8,
                is_correct=False,
            ),
        ]

        session.add_all(day1 + day2)
        session.commit()
        session.close()

        response = await async_client.get("/api/v1/verification/accuracy?days=30")

        assert response.status_code == 200
        data = response.json()
        assert len(data["daily_trend"]) == 2

        # Verify trend data
        trend = sorted(data["daily_trend"], key=lambda x: x["date"])
        assert trend[0]["accuracy"] == 100.0
        assert trend[0]["total"] == 2
        assert trend[1]["accuracy"] == 50.0
        assert trend[1]["total"] == 2

    @pytest.mark.asyncio
    async def test_get_accuracy_empty(self, async_client: AsyncClient):
        """정확도 요약 (데이터 없음)."""
        response = await async_client.get("/api/v1/verification/accuracy?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["overall_accuracy"] is None
        assert data["total_predictions"] == 0
        assert data["correct_predictions"] == 0
        assert data["daily_trend"] == []


class TestThemeAccuracyEndpoint:
    """GET /api/v1/verification/themes 테스트."""

    @pytest.mark.asyncio
    async def test_get_theme_accuracy(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """테마별 정확도 조회."""
        session = integration_session_factory()
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
            ThemePredictionAccuracy(
                prediction_date=today,
                theme="바이오",
                market="KR",
                total_stocks=4,
                correct_count=1,
                accuracy_rate=0.25,
                avg_predicted_score=55.0,
                avg_actual_change_pct=-0.5,
            ),
        ]
        session.add_all(themes)
        session.commit()
        session.close()

        response = await async_client.get(
            f"/api/v1/verification/themes?date={today}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["date"] == str(today)
        assert data["market"] == "ALL"
        assert len(data["themes"]) == 3

        # Check structure
        first = data["themes"][0]
        assert "theme" in first
        assert "market" in first
        assert "total_stocks" in first
        assert "correct_count" in first
        assert "accuracy_rate" in first
        assert "avg_predicted_score" in first
        assert "avg_actual_change_pct" in first
        assert "rise_index" in first

    @pytest.mark.asyncio
    async def test_get_theme_accuracy_market_filter(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """테마별 정확도 조회 (시장 필터)."""
        session = integration_session_factory()
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
            ),
            ThemePredictionAccuracy(
                prediction_date=today,
                theme="Tech",
                market="US",
                total_stocks=3,
                correct_count=2,
                accuracy_rate=0.6667,
                avg_predicted_score=68.0,
            ),
        ]
        session.add_all(themes)
        session.commit()
        session.close()

        response = await async_client.get(
            f"/api/v1/verification/themes?date={today}&market=KR"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["market"] == "KR"
        assert len(data["themes"]) == 1
        assert data["themes"][0]["theme"] == "반도체"

    @pytest.mark.asyncio
    async def test_get_theme_accuracy_empty(self, async_client: AsyncClient):
        """테마별 정확도 조회 (데이터 없음)."""
        yesterday = date.today() - timedelta(days=1)
        response = await async_client.get(
            f"/api/v1/verification/themes?date={yesterday}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["themes"] == []


class TestThemeTrendEndpoint:
    """GET /api/v1/verification/themes/trend 테스트."""

    @pytest.mark.asyncio
    async def test_get_theme_trend(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """특정 테마의 정확도 추이."""
        session = integration_session_factory()
        today = date.today()

        # Insert 5 days of data
        for i in range(5):
            d = today - timedelta(days=i)
            theme = ThemePredictionAccuracy(
                prediction_date=d,
                theme="반도체",
                market="KR",
                total_stocks=5,
                correct_count=4 - i,  # Decreasing accuracy
                accuracy_rate=(4 - i) / 5,
                avg_predicted_score=70.0,
            )
            session.add(theme)
        session.commit()
        session.close()

        response = await async_client.get(
            "/api/v1/verification/themes/trend?theme=반도체&days=30"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "반도체"
        assert data["market"] == "ALL"
        assert len(data["trend"]) == 5

        # Verify trend data is sorted by date
        dates = [point["date"] for point in data["trend"]]
        assert dates == sorted(dates)

        # Check structure
        first = data["trend"][0]
        assert "date" in first
        assert "accuracy_rate" in first
        assert "total_stocks" in first

    @pytest.mark.asyncio
    async def test_get_theme_trend_market_filter(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """특정 테마의 정확도 추이 (시장 필터)."""
        session = integration_session_factory()
        today = date.today()

        # Insert data for both markets
        for market in ["KR", "US"]:
            for i in range(3):
                d = today - timedelta(days=i)
                theme = ThemePredictionAccuracy(
                    prediction_date=d,
                    theme="반도체",
                    market=market,
                    total_stocks=5,
                    correct_count=4,
                    accuracy_rate=0.8,
                    avg_predicted_score=70.0,
                )
                session.add(theme)
        session.commit()
        session.close()

        response = await async_client.get(
            "/api/v1/verification/themes/trend?theme=반도체&market=KR&days=30"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["market"] == "KR"
        assert len(data["trend"]) == 3

    @pytest.mark.asyncio
    async def test_get_theme_trend_empty(self, async_client: AsyncClient):
        """특정 테마의 정확도 추이 (데이터 없음)."""
        response = await async_client.get(
            "/api/v1/verification/themes/trend?theme=UNKNOWN&days=30"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "UNKNOWN"
        assert data["trend"] == []


class TestStockHistoryEndpoint:
    """GET /api/v1/verification/stocks/{code}/history 테스트."""

    @pytest.mark.asyncio
    async def test_get_stock_history(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """특정 종목의 예측 이력."""
        session = integration_session_factory()
        stock_code = "005930"
        today = date.today()

        # Insert 7 days of data
        for i in range(7):
            d = today - timedelta(days=i)
            result = DailyPredictionResult(
                prediction_date=d,
                stock_code=stock_code,
                stock_name="삼성전자",
                market="KR",
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
                news_count=10,
                actual_direction="up" if i % 2 == 0 else "down",
                actual_change_pct=2.0 if i % 2 == 0 else -1.0,
                is_correct=i % 2 == 0,  # Alternating correct/incorrect
            )
            session.add(result)
        session.commit()
        session.close()

        response = await async_client.get(
            f"/api/v1/verification/stocks/{stock_code}/history?days=30"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["stock_code"] == stock_code
        assert data["stock_name"] == "삼성전자"
        assert data["market"] == "KR"
        assert data["total_predictions"] == 7
        assert data["correct_predictions"] == 4  # 4 correct out of 7
        assert data["accuracy_rate"] == pytest.approx(0.5714, abs=0.01)
        assert len(data["history"]) == 7

        # Check structure
        first = data["history"][0]
        assert "date" in first
        assert "predicted_direction" in first
        assert "predicted_score" in first
        assert "actual_direction" in first
        assert "actual_change_pct" in first
        assert "is_correct" in first

        # Verify history is sorted by date
        dates = [point["date"] for point in data["history"]]
        assert dates == sorted(dates)

    @pytest.mark.asyncio
    async def test_get_stock_history_market_filter(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """특정 종목의 예측 이력 (시장 필터)."""
        session = integration_session_factory()
        today = date.today()

        # Insert data for same code in different markets (edge case)
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
                is_correct=True,
            ),
        ]
        session.add_all(results)
        session.commit()
        session.close()

        response = await async_client.get(
            "/api/v1/verification/stocks/005930/history?days=30&market=KR"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["market"] == "KR"
        assert len(data["history"]) == 1

    @pytest.mark.asyncio
    async def test_get_stock_history_with_unverified(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """특정 종목의 예측 이력 (미검증 포함)."""
        session = integration_session_factory()
        stock_code = "005930"
        today = date.today()

        results = [
            # Verified
            DailyPredictionResult(
                prediction_date=today - timedelta(days=1),
                stock_code=stock_code,
                stock_name="삼성전자",
                market="KR",
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
                news_count=10,
                is_correct=True,
            ),
            # Unverified (is_correct=None)
            DailyPredictionResult(
                prediction_date=today,
                stock_code=stock_code,
                stock_name="삼성전자",
                market="KR",
                predicted_direction="up",
                predicted_score=70.0,
                confidence=0.7,
                news_count=8,
                is_correct=None,
            ),
        ]
        session.add_all(results)
        session.commit()
        session.close()

        response = await async_client.get(
            f"/api/v1/verification/stocks/{stock_code}/history?days=30"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) == 2
        # Only verified predictions count for accuracy
        assert data["total_predictions"] == 1
        assert data["correct_predictions"] == 1
        assert data["accuracy_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_get_stock_history_empty(self, async_client: AsyncClient):
        """특정 종목의 예측 이력 (데이터 없음)."""
        response = await async_client.get(
            "/api/v1/verification/stocks/UNKNOWN/history?days=30"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["stock_code"] == "UNKNOWN"
        assert data["stock_name"] is None
        assert data["total_predictions"] == 0
        assert data["accuracy_rate"] == 0.0
        assert data["history"] == []


class TestVerificationRunEndpoint:
    """POST /api/v1/verification/run 테스트."""

    @pytest.mark.asyncio
    @patch("app.api.verification.run_verification", new_callable=AsyncMock)
    @patch("app.api.verification.aggregate_theme_accuracy")
    async def test_trigger_verification_run(
        self, mock_aggregate, mock_verify, async_client: AsyncClient
    ):
        """검증 실행 트리거."""
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
        response = await async_client.post(
            f"/api/v1/verification/run?date={today_str}&market=KR"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "triggered"
        assert data["market"] == "KR"
        assert data["run_date"] == today_str
        assert data["stocks_verified"] == 0  # Not yet run (background task)
        assert data["stocks_failed"] == 0
        assert data["duration_seconds"] == 0.0

    @pytest.mark.asyncio
    @patch("app.api.verification.run_verification", new_callable=AsyncMock)
    @patch("app.api.verification.aggregate_theme_accuracy")
    async def test_trigger_verification_run_us_market(
        self, mock_aggregate, mock_verify, async_client: AsyncClient
    ):
        """검증 실행 트리거 (US 시장)."""
        mock_log = VerificationRunLog(
            run_date=date.today(),
            market="US",
            status="success",
            stocks_verified=8,
            stocks_failed=0,
            duration_seconds=12.0,
        )
        mock_verify.return_value = mock_log

        today_str = date.today().isoformat()
        response = await async_client.post(
            f"/api/v1/verification/run?date={today_str}&market=US"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "triggered"
        assert data["market"] == "US"

    @pytest.mark.asyncio
    @patch("app.api.verification.run_verification", new_callable=AsyncMock)
    @patch("app.api.verification.aggregate_theme_accuracy")
    async def test_trigger_verification_run_failed(
        self, mock_aggregate, mock_verify, async_client: AsyncClient
    ):
        """검증 실행 트리거 (실패 케이스 mock)."""
        # Even if verification fails, the trigger should return 200
        mock_log = VerificationRunLog(
            run_date=date.today(),
            market="KR",
            status="failed",
            stocks_verified=0,
            stocks_failed=10,
            duration_seconds=5.0,
            error_details="Price API unavailable",
        )
        mock_verify.return_value = mock_log

        today_str = date.today().isoformat()
        response = await async_client.post(
            f"/api/v1/verification/run?date={today_str}&market=KR"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "triggered"


class TestVerificationStatusEndpoint:
    """GET /api/v1/verification/status 테스트."""

    @pytest.mark.asyncio
    async def test_get_verification_status(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """전체 검증 상태 조회."""
        session = integration_session_factory()
        today = date.today()

        logs = [
            VerificationRunLog(
                run_date=today,
                market="KR",
                status="success",
                stocks_verified=10,
                stocks_failed=0,
                duration_seconds=15.5,
            ),
            VerificationRunLog(
                run_date=today - timedelta(days=1),
                market="KR",
                status="success",
                stocks_verified=8,
                stocks_failed=0,
                duration_seconds=12.0,
            ),
            VerificationRunLog(
                run_date=today,
                market="US",
                status="partial",
                stocks_verified=8,
                stocks_failed=2,
                duration_seconds=20.3,
            ),
        ]
        session.add_all(logs)
        session.commit()
        session.close()

        response = await async_client.get("/api/v1/verification/status")

        assert response.status_code == 200
        data = response.json()
        assert data["current_date"] == str(today)
        assert len(data["markets"]) == 2
        assert data["total_stocks_verified_today"] == 18  # 10 + 8

        # Check KR market
        kr_market = next(m for m in data["markets"] if m["market"] == "KR")
        assert kr_market["last_run_date"] == str(today)
        assert kr_market["status"] == "success"
        assert kr_market["stocks_verified"] == 10

        # Check US market
        us_market = next(m for m in data["markets"] if m["market"] == "US")
        assert us_market["last_run_date"] == str(today)
        assert us_market["status"] == "partial"
        assert us_market["stocks_verified"] == 8

    @pytest.mark.asyncio
    async def test_get_verification_status_no_logs(self, async_client: AsyncClient):
        """전체 검증 상태 조회 (로그 없음)."""
        response = await async_client.get("/api/v1/verification/status")

        assert response.status_code == 200
        data = response.json()
        assert len(data["markets"]) == 2
        assert data["total_stocks_verified_today"] == 0

        # Both markets should have None for last_run_date
        assert all(m["last_run_date"] is None for m in data["markets"])
        assert all(m["status"] is None for m in data["markets"])
        assert all(m["stocks_verified"] == 0 for m in data["markets"])

    @pytest.mark.asyncio
    async def test_get_verification_status_partial_logs(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """전체 검증 상태 조회 (부분 로그)."""
        session = integration_session_factory()
        today = date.today()

        # Only KR market has logs
        log = VerificationRunLog(
            run_date=today,
            market="KR",
            status="success",
            stocks_verified=10,
            stocks_failed=0,
            duration_seconds=15.5,
        )
        session.add(log)
        session.commit()
        session.close()

        response = await async_client.get("/api/v1/verification/status")

        assert response.status_code == 200
        data = response.json()
        assert len(data["markets"]) == 2

        kr_market = next(m for m in data["markets"] if m["market"] == "KR")
        assert kr_market["last_run_date"] == str(today)
        assert kr_market["status"] == "success"

        us_market = next(m for m in data["markets"] if m["market"] == "US")
        assert us_market["last_run_date"] is None
        assert us_market["status"] is None
