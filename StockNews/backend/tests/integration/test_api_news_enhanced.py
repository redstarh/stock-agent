"""RED: 향상된 /news/* 엔드포인트 통합 테스트."""

import pytest
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.news_event import NewsEvent


@pytest.fixture
async def async_client():
    """FastAPI 비동기 테스트 클라이언트."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def seed_news_with_themes(integration_session_factory):
    """테마가 포함된 뉴스 데이터 시드."""
    session = integration_session_factory()

    events = [
        NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title="삼성전자 AI 반도체 개발",
            content="삼성전자가 차세대 AI 반도체 개발에 성공했다.",
            summary="삼성전자가 AI 반도체 개발에 성공했다.",
            sentiment="positive",
            sentiment_score=0.8,
            news_score=85.0,
            source="naver",
            theme="AI",
            published_at=datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
        ),
        NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title="삼성전자 반도체 공장 증설",
            content="삼성전자가 반도체 공장을 증설한다.",
            summary="삼성전자가 반도체 공장을 증설한다.",
            sentiment="positive",
            sentiment_score=0.7,
            news_score=80.0,
            source="naver",
            theme="반도체",
            published_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        ),
        NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title="삼성전자 4분기 실적 발표",
            content="삼성전자가 4분기 사상 최대 실적을 기록했다.",
            summary="삼성전자가 4분기 사상 최대 실적을 기록했다.",
            sentiment="positive",
            sentiment_score=0.9,
            news_score=90.0,
            source="dart",
            theme="실적",
            is_disclosure=True,
            published_at=datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
        ),
    ]

    for event in events:
        session.add(event)
    session.commit()
    session.close()


class TestNewsScoreEnhanced:
    @pytest.mark.asyncio
    async def test_news_score_includes_top_themes(self, async_client, seed_news_with_themes):
        """GET /api/v1/news/score?stock=005930 → top_themes 포함."""
        resp = await async_client.get("/api/v1/news/score", params={"stock": "005930"})
        assert resp.status_code == 200
        data = resp.json()
        assert "top_themes" in data
        assert isinstance(data["top_themes"], list)
        assert len(data["top_themes"]) <= 3
        # 005930에는 AI, 반도체, 실적 테마가 있음
        assert "AI" in data["top_themes"] or "반도체" in data["top_themes"] or "실적" in data["top_themes"]

    @pytest.mark.asyncio
    async def test_news_score_includes_updated_at(self, async_client, seed_news_with_themes):
        """GET /api/v1/news/score?stock=005930 → updated_at 포함."""
        resp = await async_client.get("/api/v1/news/score", params={"stock": "005930"})
        assert resp.status_code == 200
        data = resp.json()
        assert "updated_at" in data
        # updated_at은 최신 뉴스의 published_at
        assert data["updated_at"] is not None

    @pytest.mark.asyncio
    async def test_news_score_no_news_returns_null_updated_at(self, async_client):
        """뉴스가 없는 종목은 updated_at이 null."""
        resp = await async_client.get("/api/v1/news/score", params={"stock": "999999"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["updated_at"] is None


class TestNewsLatestEnhanced:
    @pytest.mark.asyncio
    async def test_latest_news_includes_summary(self, async_client, seed_news_with_themes):
        """GET /api/v1/news/latest → items에 summary 포함."""
        resp = await async_client.get("/api/v1/news/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        if data["items"]:
            item = data["items"][0]
            assert "summary" in item
