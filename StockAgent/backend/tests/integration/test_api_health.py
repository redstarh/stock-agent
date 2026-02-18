"""T-B9: Health API 통합 테스트"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    """헬스체크 엔드포인트"""
    resp = await async_client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_contains_version(async_client):
    """헬스체크에 버전 정보 포함"""
    resp = await async_client.get("/api/v1/health")
    data = resp.json()
    assert "version" in data
