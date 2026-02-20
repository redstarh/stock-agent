"""Integration tests for Training API endpoints."""

from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.training import StockTrainingData


@pytest.fixture
async def async_client():
    """FastAPI 비동기 테스트 클라이언트."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def clean_training_tables(integration_session_factory):
    """각 테스트 전에 학습 데이터 테이블 정리."""
    session = integration_session_factory()
    try:
        session.query(StockTrainingData).delete()
        session.commit()
    finally:
        session.close()
    yield


class TestGetTrainingData:
    """GET /api/v1/training/data 테스트."""

    @pytest.mark.asyncio
    async def test_get_training_data(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """학습 데이터 조회."""
        session = integration_session_factory()

        # Insert sample data
        records = []
        for i in range(3):
            record = StockTrainingData(
                prediction_date=date(2026, 2, 17) + timedelta(days=i),
                stock_code="005930",
                stock_name="삼성전자",
                market="KR",
                news_score=70.0 + i,
                sentiment_score=0.5,
                news_count=5 + i,
                news_count_3d=3,
                avg_score_3d=72.0,
                disclosure_ratio=0.0,
                sentiment_trend=0.1,
                day_of_week=(0 + i) % 5,
                predicted_direction="up",
                predicted_score=75.0 + i,
                confidence=0.8,
                actual_close=71500.0 if i < 2 else None,
                actual_change_pct=2.29 if i < 2 else None,
                actual_direction="up" if i < 2 else None,
                is_correct=True if i < 2 else None,
            )
            records.append(record)
            session.add(record)

        session.commit()
        session.close()

        response = await async_client.get(
            "/api/v1/training/data",
            params={
                "market": "KR",
                "start_date": "2026-02-15",
                "end_date": "2026-02-20",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["market"] == "KR"
        assert data["total"] == 3
        assert len(data["data"]) == 3
        assert data["data"][0]["stock_code"] == "005930"

    @pytest.mark.asyncio
    async def test_get_training_data_empty(self, async_client: AsyncClient):
        """데이터 없을 때."""
        response = await async_client.get(
            "/api/v1/training/data",
            params={
                "market": "US",
                "start_date": "2026-02-15",
                "end_date": "2026-02-20",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_get_training_data_limit(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """limit 파라미터 테스트."""
        session = integration_session_factory()

        # Insert 3 records
        for i in range(3):
            record = StockTrainingData(
                prediction_date=date(2026, 2, 17) + timedelta(days=i),
                stock_code=f"00593{i}",
                stock_name=f"Stock {i}",
                market="KR",
                news_score=70.0,
                sentiment_score=0.5,
                news_count=5,
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
            )
            session.add(record)

        session.commit()
        session.close()

        response = await async_client.get(
            "/api/v1/training/data",
            params={"market": "KR", "limit": 1},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1

    @pytest.mark.asyncio
    async def test_get_training_data_date_range(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """날짜 범위 필터링."""
        session = integration_session_factory()

        # Insert records across different dates
        for i in range(5):
            record = StockTrainingData(
                prediction_date=date(2026, 2, 15) + timedelta(days=i),
                stock_code="005930",
                stock_name="삼성전자",
                market="KR",
                news_score=70.0,
                sentiment_score=0.5,
                news_count=5,
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
            )
            session.add(record)

        session.commit()
        session.close()

        response = await async_client.get(
            "/api/v1/training/data",
            params={
                "market": "KR",
                "start_date": "2026-02-16",
                "end_date": "2026-02-18",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3  # Only 2/16, 2/17, 2/18


class TestExportTrainingCSV:
    """GET /api/v1/training/export 테스트."""

    @pytest.mark.asyncio
    async def test_export_training_csv(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """CSV 내보내기."""
        session = integration_session_factory()

        # Insert sample data
        for i in range(3):
            record = StockTrainingData(
                prediction_date=date(2026, 2, 17) + timedelta(days=i),
                stock_code="005930",
                stock_name="삼성전자",
                market="KR",
                news_score=70.0 + i,
                sentiment_score=0.5,
                news_count=5 + i,
                predicted_direction="up",
                predicted_score=75.0 + i,
                confidence=0.8,
            )
            session.add(record)

        session.commit()
        session.close()

        response = await async_client.get(
            "/api/v1/training/export",
            params={
                "market": "KR",
                "start_date": "2026-02-15",
                "end_date": "2026-02-20",
            },
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]

        lines = response.text.strip().split("\n")
        assert len(lines) == 4  # header + 3 data rows
        assert "prediction_date" in lines[0]
        assert "005930" in lines[1]

    @pytest.mark.asyncio
    async def test_export_training_csv_empty(self, async_client: AsyncClient):
        """빈 CSV 내보내기."""
        response = await async_client.get(
            "/api/v1/training/export",
            params={"market": "US"},
        )

        assert response.status_code == 200
        lines = response.text.strip().split("\n")
        assert len(lines) == 1  # header only

    @pytest.mark.asyncio
    async def test_export_training_csv_filename(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """CSV 파일명 검증."""
        session = integration_session_factory()

        record = StockTrainingData(
            prediction_date=date(2026, 2, 17),
            stock_code="005930",
            stock_name="삼성전자",
            market="KR",
            news_score=70.0,
            sentiment_score=0.5,
            news_count=5,
            predicted_direction="up",
            predicted_score=75.0,
            confidence=0.8,
        )
        session.add(record)
        session.commit()
        session.close()

        response = await async_client.get(
            "/api/v1/training/export",
            params={
                "market": "KR",
                "start_date": "2026-02-15",
                "end_date": "2026-02-20",
            },
        )

        assert response.status_code == 200
        disposition = response.headers["content-disposition"]
        assert "training_KR_2026-02-15_2026-02-20.csv" in disposition


class TestGetTrainingStats:
    """GET /api/v1/training/stats 테스트."""

    @pytest.mark.asyncio
    async def test_get_training_stats(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """학습 데이터 통계."""
        session = integration_session_factory()

        # Insert KR market data
        for i in range(3):
            record = StockTrainingData(
                prediction_date=date(2026, 2, 17) + timedelta(days=i),
                stock_code=f"00593{i}",
                stock_name=f"Stock {i}",
                market="KR",
                news_score=70.0,
                sentiment_score=0.5,
                news_count=5,
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
                actual_close=71500.0 if i < 2 else None,
                actual_change_pct=2.29 if i < 2 else None,
                actual_direction="up" if i < 2 else None,
                is_correct=True if i < 2 else None,
            )
            session.add(record)

        session.commit()
        session.close()

        response = await async_client.get("/api/v1/training/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 3
        assert data["labeled_records"] == 2

        kr_market = next(m for m in data["markets"] if m["market"] == "KR")
        assert kr_market["total_records"] == 3
        assert kr_market["labeled_records"] == 2
        assert kr_market["accuracy"] == 100.0

    @pytest.mark.asyncio
    async def test_get_training_stats_empty(self, async_client: AsyncClient):
        """데이터 없을 때 통계."""
        response = await async_client.get("/api/v1/training/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 0
        assert data["labeled_records"] == 0

        # Both markets should exist but with zero counts
        assert len(data["markets"]) == 2
        for market in data["markets"]:
            assert market["total_records"] == 0
            assert market["labeled_records"] == 0
            assert market["accuracy"] is None

    @pytest.mark.asyncio
    async def test_get_training_stats_multi_market(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """다중 시장 통계."""
        session = integration_session_factory()

        # Insert KR market data
        for i in range(2):
            record = StockTrainingData(
                prediction_date=date(2026, 2, 17),
                stock_code=f"00593{i}",
                stock_name=f"Stock {i}",
                market="KR",
                news_score=70.0,
                sentiment_score=0.5,
                news_count=5,
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
                is_correct=True,
            )
            session.add(record)

        # Insert US market data
        for i in range(3):
            record = StockTrainingData(
                prediction_date=date(2026, 2, 17),
                stock_code=f"AAPL{i}",
                stock_name=f"Apple {i}",
                market="US",
                news_score=65.0,
                sentiment_score=0.6,
                news_count=4,
                predicted_direction="up",
                predicted_score=70.0,
                confidence=0.7,
                is_correct=False if i == 0 else None,
            )
            session.add(record)

        session.commit()
        session.close()

        response = await async_client.get("/api/v1/training/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 5
        assert data["labeled_records"] == 3  # 2 KR + 1 US

        kr_market = next(m for m in data["markets"] if m["market"] == "KR")
        assert kr_market["total_records"] == 2
        assert kr_market["labeled_records"] == 2
        assert kr_market["accuracy"] == 100.0

        us_market = next(m for m in data["markets"] if m["market"] == "US")
        assert us_market["total_records"] == 3
        assert us_market["labeled_records"] == 1
        assert us_market["accuracy"] == 0.0

    @pytest.mark.asyncio
    async def test_get_training_stats_date_range(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """통계에 날짜 범위 포함 확인."""
        session = integration_session_factory()

        # Insert records across different dates
        for i in range(5):
            record = StockTrainingData(
                prediction_date=date(2026, 2, 15) + timedelta(days=i),
                stock_code="005930",
                stock_name="삼성전자",
                market="KR",
                news_score=70.0,
                sentiment_score=0.5,
                news_count=5,
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
            )
            session.add(record)

        session.commit()
        session.close()

        response = await async_client.get("/api/v1/training/stats")

        assert response.status_code == 200
        data = response.json()

        kr_market = next(m for m in data["markets"] if m["market"] == "KR")
        assert kr_market["date_range_start"] == "2026-02-15"
        assert kr_market["date_range_end"] == "2026-02-19"

    @pytest.mark.asyncio
    async def test_get_training_stats_accuracy_calculation(
        self, async_client: AsyncClient, integration_session_factory
    ):
        """정확도 계산 로직."""
        session = integration_session_factory()

        # 5 total, 3 labeled, 2 correct
        for i in range(5):
            is_correct = None
            if i < 3:  # First 3 are labeled
                is_correct = True if i < 2 else False  # First 2 are correct

            record = StockTrainingData(
                prediction_date=date(2026, 2, 17),
                stock_code=f"00593{i}",
                stock_name=f"Stock {i}",
                market="KR",
                news_score=70.0,
                sentiment_score=0.5,
                news_count=5,
                predicted_direction="up",
                predicted_score=75.0,
                confidence=0.8,
                is_correct=is_correct,
            )
            session.add(record)

        session.commit()
        session.close()

        response = await async_client.get("/api/v1/training/stats")

        assert response.status_code == 200
        data = response.json()

        kr_market = next(m for m in data["markets"] if m["market"] == "KR")
        assert kr_market["total_records"] == 5
        assert kr_market["labeled_records"] == 3
        # Accuracy: 2 correct out of 3 labeled = 66.7%
        assert kr_market["accuracy"] == pytest.approx(66.7, abs=0.1)
