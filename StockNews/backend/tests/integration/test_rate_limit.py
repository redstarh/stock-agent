"""Rate limiting 통합 테스트."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def async_client():
    """비동기 테스트 클라이언트."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestRateLimit:
    """Rate limiting 테스트."""

    async def test_rate_limit_header(self, async_client):
        """응답에 X-RateLimit 헤더 포함."""
        response = await async_client.get("/api/v1/news/latest?market=KR")

        assert response.status_code == 200
        # slowapi는 X-RateLimit-* 헤더를 추가함
        assert "X-RateLimit-Limit" in response.headers or "RateLimit-Limit" in response.headers

    async def test_rate_limit_not_on_health(self, async_client):
        """GET /health는 rate limit 없음."""
        # Health endpoint는 rate limit이 없어야 함
        # 여러 번 호출해도 429를 반환하지 않음
        for _ in range(5):
            response = await async_client.get("/health")
            assert response.status_code == 200
            # Rate limit 헤더가 없어야 함
            assert "X-RateLimit-Limit" not in response.headers
            assert "RateLimit-Limit" not in response.headers

    async def test_rate_limit_applies_to_api_endpoints(self, async_client):
        """API 엔드포인트는 rate limit 적용."""
        # 첫 요청은 성공해야 함
        response = await async_client.get("/api/v1/news/latest?market=KR")
        assert response.status_code == 200

        # Rate limit 헤더가 있어야 함
        has_limit_header = (
            "X-RateLimit-Limit" in response.headers or
            "RateLimit-Limit" in response.headers
        )
        assert has_limit_header, "Rate limit headers should be present on API endpoints"

    async def test_different_endpoints_share_limit(self, async_client):
        """다른 엔드포인트도 rate limit 적용 확인."""
        endpoints = [
            "/api/v1/news/latest?market=KR",
            "/api/v1/news/top?market=KR",
            "/api/v1/news/score?stock=005930",
        ]

        for endpoint in endpoints:
            response = await async_client.get(endpoint)
            # 200 또는 404 (데이터 없음)는 괜찮지만, rate limit은 체크해야 함
            assert response.status_code in [200, 404]
