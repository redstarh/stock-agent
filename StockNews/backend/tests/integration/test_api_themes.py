"""RED: /theme/* 엔드포인트 통합 테스트."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestThemeStrengthEndpoint:
    @pytest.mark.asyncio
    async def test_get_theme_strength(self, async_client):
        """GET /api/v1/theme/strength → 200 + 테마 리스트."""
        resp = await async_client.get("/api/v1/theme/strength")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_theme_strength_market_filter(self, async_client):
        """GET /api/v1/theme/strength?market=KR → 200."""
        resp = await async_client.get("/api/v1/theme/strength", params={"market": "KR"})
        assert resp.status_code == 200
