"""T-B17: Strategy 관리 API 테스트"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def async_client():
    """httpx AsyncClient fixture"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_get_strategy_config(async_client):
    """전략 설정 조회"""
    resp = await async_client.get("/api/v1/strategy/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "top_n" in data
    assert "news_threshold" in data


@pytest.mark.asyncio
async def test_update_strategy_config(async_client):
    """전략 설정 업데이트"""
    resp = await async_client.put(
        "/api/v1/strategy/config", json={"top_n": 10, "news_threshold": 60}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["top_n"] == 10
    assert data["news_threshold"] == 60


@pytest.mark.asyncio
async def test_toggle_strategy(async_client):
    """전략 활성화/비활성화"""
    resp = await async_client.post("/api/v1/strategy/toggle", json={"enabled": False})
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False

    resp = await async_client.post("/api/v1/strategy/toggle", json={"enabled": True})
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True
