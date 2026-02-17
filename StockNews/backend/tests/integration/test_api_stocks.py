"""RED: /stocks/* 엔드포인트 통합 테스트."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestStockTimelineEndpoint:
    @pytest.mark.asyncio
    async def test_get_timeline(self, async_client):
        """GET /api/v1/stocks/005930/timeline → 200 + 타임라인."""
        resp = await async_client.get("/api/v1/stocks/005930/timeline")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_timeline_days_param(self, async_client):
        """GET /api/v1/stocks/005930/timeline?days=3 → 200."""
        resp = await async_client.get("/api/v1/stocks/005930/timeline", params={"days": 3})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_timeline_unknown_stock(self, async_client):
        """GET /api/v1/stocks/999999/timeline → 200 + 빈 타임라인."""
        resp = await async_client.get("/api/v1/stocks/999999/timeline")
        assert resp.status_code == 200
        assert resp.json() == []
