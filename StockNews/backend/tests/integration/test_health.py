"""Health check endpoint 통합 테스트."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def async_client():
    """비동기 테스트 클라이언트."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestHealthEndpoint:
    """Health check 엔드포인트 테스트."""

    async def test_health_returns_ok(self, async_client):
        """GET /health → 200 + status ok."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "degraded"]
        assert data["version"] == "0.1.0"

    async def test_health_includes_services(self, async_client):
        """응답에 services.database 포함."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "database" in data["services"]
        assert "redis" in data["services"]

    async def test_health_database_check(self, async_client):
        """DB 연결 상태 확인."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        # DB는 SQLite in-memory이므로 항상 ok여야 함
        assert data["services"]["database"] == "ok"
        # Redis는 optional이므로 ok 또는 unavailable
        assert data["services"]["redis"] in ["ok", "unavailable"]
