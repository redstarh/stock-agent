"""RED: /news/* 엔드포인트 통합 테스트."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def async_client():
    """FastAPI 비동기 테스트 클라이언트."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestNewsScoreEndpoint:
    @pytest.mark.asyncio
    async def test_get_news_score_success(self, async_client):
        """GET /api/v1/news/score?stock=005930 → 200."""
        resp = await async_client.get("/api/v1/news/score", params={"stock": "005930"})
        assert resp.status_code == 200
        data = resp.json()
        assert "news_score" in data
        assert "stock_code" in data

    @pytest.mark.asyncio
    async def test_get_news_score_missing_stock(self, async_client):
        """GET /api/v1/news/score → 422 (stock 파라미터 누락)."""
        resp = await async_client.get("/api/v1/news/score")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_get_news_score_unknown_stock(self, async_client):
        """GET /api/v1/news/score?stock=999999 → 200 + score=0."""
        resp = await async_client.get("/api/v1/news/score", params={"stock": "999999"})
        assert resp.status_code == 200
        assert resp.json()["news_score"] == 0


class TestNewsTopEndpoint:
    @pytest.mark.asyncio
    async def test_get_top_news(self, async_client):
        """GET /api/v1/news/top?market=KR → 200 + 리스트."""
        resp = await async_client.get("/api/v1/news/top", params={"market": "KR"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_top_news_limit(self, async_client):
        """GET /api/v1/news/top?market=KR&limit=5 → 최대 5건."""
        resp = await async_client.get("/api/v1/news/top", params={"market": "KR", "limit": 5})
        assert resp.status_code == 200
        assert len(resp.json()) <= 5

    @pytest.mark.asyncio
    async def test_top_news_missing_market(self, async_client):
        """GET /api/v1/news/top → 422."""
        resp = await async_client.get("/api/v1/news/top")
        assert resp.status_code == 422


class TestNewsLatestEndpoint:
    @pytest.mark.asyncio
    async def test_get_latest_news(self, async_client):
        """GET /api/v1/news/latest → 200 + 페이지네이션 응답."""
        resp = await async_client.get("/api/v1/news/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_latest_pagination(self, async_client):
        """GET /api/v1/news/latest?offset=0&limit=5 → 올바른 구조."""
        resp = await async_client.get("/api/v1/news/latest", params={"offset": 0, "limit": 5})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_latest_market_filter(self, async_client):
        """GET /api/v1/news/latest?market=KR → KR 뉴스만 반환."""
        resp = await async_client.get("/api/v1/news/latest", params={"market": "KR"})
        assert resp.status_code == 200


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """GET /health → 200 + status='ok'."""
        resp = await async_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_version(self, async_client):
        """version 포함."""
        resp = await async_client.get("/health")
        assert "version" in resp.json()
