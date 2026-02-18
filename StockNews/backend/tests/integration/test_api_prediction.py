"""Integration tests for prediction API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.news_event import NewsEvent


@pytest.fixture
async def async_client():
    """FastAPI 비동기 테스트 클라이언트."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestPredictionEndpoint:
    @pytest.mark.asyncio
    async def test_get_prediction(self, async_client: AsyncClient, integration_session_factory):
        """GET /api/v1/stocks/005930/prediction → 200 + PredictionResponse."""
        # Insert test news using integration session
        session = integration_session_factory()
        news_items = [
            NewsEvent(
                market="KR",
                stock_code="005930",
                title="삼성전자 신제품 출시",
                content="긍정적인 전망",
                news_score=75.0,
                sentiment_score=0.8,
                source="naver",
                source_url="http://example.com/pred1",
            ),
            NewsEvent(
                market="KR",
                stock_code="005930",
                title="실적 호조",
                content="매출 증가",
                news_score=80.0,
                sentiment_score=0.9,
                source="naver",
                source_url="http://example.com/pred2",
            ),
        ]
        session.add_all(news_items)
        session.commit()
        session.close()

        response = await async_client.get("/api/v1/stocks/005930/prediction")

        assert response.status_code == 200
        data = response.json()
        assert data["stock_code"] == "005930"
        assert data["prediction_score"] is not None
        assert isinstance(data["prediction_score"], (int, float))
        assert data["direction"] in ["up", "down", "neutral"]
        assert data["confidence"] is not None
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["based_on_days"] == 30

    @pytest.mark.asyncio
    async def test_prediction_unknown_stock(self, async_client: AsyncClient):
        """존재하지 않는 종목 → 200 + null prediction."""
        response = await async_client.get("/api/v1/stocks/UNKNOWN/prediction")

        assert response.status_code == 200
        data = response.json()
        assert data["stock_code"] == "UNKNOWN"
        assert data["prediction_score"] is None
        assert data["direction"] is None
        assert data["confidence"] is None

    @pytest.mark.asyncio
    async def test_prediction_confidence(self, async_client: AsyncClient, integration_session_factory):
        """응답에 confidence 필드 포함 (0.0 ~ 1.0)."""
        # Insert test news
        session = integration_session_factory()
        news = NewsEvent(
            market="KR",
            stock_code="000660",
            title="SK하이닉스 호재",
            content="긍정적 뉴스",
            news_score=70.0,
            sentiment_score=0.7,
            source="naver",
            source_url="http://example.com/pred3",
        )
        session.add(news)
        session.commit()
        session.close()

        response = await async_client.get("/api/v1/stocks/000660/prediction")

        assert response.status_code == 200
        data = response.json()
        assert "confidence" in data
        assert data["confidence"] is not None
        assert 0.0 <= data["confidence"] <= 1.0
        assert isinstance(data["confidence"], float)

    @pytest.mark.asyncio
    async def test_prediction_direction_valid(self, async_client: AsyncClient, integration_session_factory):
        """direction이 up/down/neutral 중 하나."""
        # Insert multiple test news with varying scores
        session = integration_session_factory()
        news_items = [
            NewsEvent(
                market="KR",
                stock_code="035720",
                title=f"카카오 뉴스 {i}",
                content="내용",
                news_score=60.0 + i * 5,
                sentiment_score=0.5,
                source="naver",
                source_url=f"http://example.com/pred_kakao{i}",
            )
            for i in range(5)
        ]
        session.add_all(news_items)
        session.commit()
        session.close()

        response = await async_client.get("/api/v1/stocks/035720/prediction")

        assert response.status_code == 200
        data = response.json()
        assert data["direction"] in ["up", "down", "neutral"]
