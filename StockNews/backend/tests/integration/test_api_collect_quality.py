"""수집 품질 모니터링 API 통합 테스트."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# API key for testing (matches test_contract_api.py pattern)
API_KEY_HEADER = {"X-API-Key": "dev-api-key-change-in-production"}


@pytest.fixture
async def async_client():
    """비동기 테스트 클라이언트."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def _disable_rate_limit():
    """Rate limiting 비활성화."""
    app.state.limiter.enabled = False
    yield
    app.state.limiter.enabled = True


class TestCollectionQualityAPI:
    """GET /api/v1/collect/quality 통합 테스트."""

    async def test_quality_endpoint_returns_200(self, async_client):
        """엔드포인트 정상 응답 확인."""
        resp = await async_client.get(
            "/api/v1/collect/quality",
            headers=API_KEY_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "sources" in data

    async def test_quality_response_structure(self, async_client):
        """응답 구조 검증."""
        resp = await async_client.get(
            "/api/v1/collect/quality",
            headers=API_KEY_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()

        # Summary fields
        assert "total_sources" in data["summary"]
        assert "total_items_tracked" in data["summary"]
        assert "overall_scrape_success_rate" in data["summary"]
        assert "overall_avg_confidence" in data["summary"]

        # Sources dict
        assert isinstance(data["sources"], dict)

    async def test_quality_empty_initially(self, async_client):
        """초기 상태 또는 빈 트래커."""
        # Reset tracker for clean test
        from app.collectors.quality_tracker import tracker
        tracker._results.clear()

        resp = await async_client.get(
            "/api/v1/collect/quality",
            headers=API_KEY_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["total_sources"] == 0
        assert data["summary"]["total_items_tracked"] == 0
        assert data["sources"] == {}

    async def test_quality_with_tracked_items(self, async_client):
        """트래킹된 항목이 있는 경우."""
        from datetime import UTC, datetime

        from app.collectors.quality_tracker import ItemResult, tracker

        # Reset and add test data
        tracker._results.clear()
        tracker.record(
            ItemResult(
                source="naver",
                market="KR",
                scrape_ok=True,
                llm_confidence=0.85,
                sentiment="positive",
                news_score=75.0,
                timestamp=datetime.now(UTC),
            )
        )
        tracker.record(
            ItemResult(
                source="finnhub",
                market="US",
                scrape_ok=True,
                llm_confidence=0.90,
                sentiment="neutral",
                news_score=65.0,
                timestamp=datetime.now(UTC),
            )
        )

        resp = await async_client.get(
            "/api/v1/collect/quality",
            headers=API_KEY_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()

        # Verify summary
        assert data["summary"]["total_sources"] == 2
        assert data["summary"]["total_items_tracked"] == 2
        assert data["summary"]["overall_scrape_success_rate"] == 1.0

        # Verify source stats
        assert "naver" in data["sources"]
        assert "finnhub" in data["sources"]
        assert data["sources"]["naver"]["total_items"] == 1
        assert data["sources"]["finnhub"]["total_items"] == 1

    async def test_quality_requires_auth(self, async_client, monkeypatch):
        """인증 필요 여부 확인."""
        from app.core.config import settings

        # Force auth requirement
        monkeypatch.setattr(settings, "require_auth", True)
        monkeypatch.setattr(settings, "app_env", "production")

        # Without API key should fail
        resp = await async_client.get("/api/v1/collect/quality")
        assert resp.status_code in [401, 403]

        # With API key should succeed
        resp = await async_client.get(
            "/api/v1/collect/quality",
            headers=API_KEY_HEADER,
        )
        assert resp.status_code == 200

    async def test_quality_source_stats_fields(self, async_client):
        """소스별 통계 필드 검증."""
        from datetime import UTC, datetime

        from app.collectors.quality_tracker import ItemResult, tracker

        tracker._results.clear()
        tracker.record(
            ItemResult(
                source="naver",
                market="KR",
                scrape_ok=True,
                llm_confidence=0.8,
                sentiment="positive",
                news_score=70.0,
                timestamp=datetime.now(UTC),
            )
        )

        resp = await async_client.get(
            "/api/v1/collect/quality",
            headers=API_KEY_HEADER,
        )
        data = resp.json()

        naver_stats = data["sources"]["naver"]
        assert "total_items" in naver_stats
        assert "scrape_success_rate" in naver_stats
        assert "avg_confidence" in naver_stats
        assert "neutral_ratio" in naver_stats
        assert "avg_news_score" in naver_stats
        assert "high_score_ratio" in naver_stats
        assert "last_updated" in naver_stats

    async def test_quality_field_types(self, async_client):
        """응답 필드 타입 검증."""
        from datetime import UTC, datetime

        from app.collectors.quality_tracker import ItemResult, tracker

        tracker._results.clear()
        tracker.record(
            ItemResult(
                source="test",
                market="KR",
                scrape_ok=True,
                llm_confidence=0.75,
                sentiment="neutral",
                news_score=60.0,
                timestamp=datetime.now(UTC),
            )
        )

        resp = await async_client.get(
            "/api/v1/collect/quality",
            headers=API_KEY_HEADER,
        )
        data = resp.json()

        # Summary types
        assert isinstance(data["summary"]["total_sources"], int)
        assert isinstance(data["summary"]["total_items_tracked"], int)
        assert isinstance(data["summary"]["overall_scrape_success_rate"], float)
        assert isinstance(data["summary"]["overall_avg_confidence"], float)

        # Source stats types
        stats = data["sources"]["test"]
        assert isinstance(stats["total_items"], int)
        assert isinstance(stats["scrape_success_rate"], float)
        assert isinstance(stats["avg_confidence"], float)
        assert isinstance(stats["neutral_ratio"], float)
        assert isinstance(stats["avg_news_score"], float)
        assert isinstance(stats["high_score_ratio"], float)
        assert stats["last_updated"] is None or isinstance(stats["last_updated"], str)
