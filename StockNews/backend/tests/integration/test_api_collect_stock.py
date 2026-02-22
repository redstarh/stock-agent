"""POST /collect/stock API 통합 테스트."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """TestClient fixture."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers():
    """인증 헤더."""
    return {"X-API-Key": "test-api-key"}


class TestCollectStock:
    """POST /api/v1/collect/stock 테스트."""

    @patch("app.collectors.pipeline.process_collected_items", new_callable=AsyncMock, return_value=5)
    @patch("app.collectors.naver.NaverCollector.collect", new_callable=AsyncMock)
    def test_collect_kr_stock(self, mock_collect, mock_process, client, auth_headers):
        """KR 종목 수집이 정상 동작한다."""
        mock_collect.return_value = [{"title": "test"} for _ in range(10)]

        response = client.post(
            "/api/v1/collect/stock",
            json={
                "query": "삼성전자",
                "stock_code": "005930",
                "market": "KR",
                "add_to_scope": False,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["collected"] == 10
        assert data["saved"] == 5
        assert data["added_to_scope"] is False

    @patch("app.collectors.pipeline.process_collected_items", new_callable=AsyncMock, return_value=3)
    @patch("app.collectors.finnhub.FinnhubCollector.collect_company_news", new_callable=AsyncMock)
    def test_collect_us_stock(self, mock_collect, mock_process, client, auth_headers):
        """US 종목 수집이 정상 동작한다."""
        mock_collect.return_value = [{"title": "test"} for _ in range(8)]

        with patch("app.api.collect.settings") as mock_settings:
            mock_settings.finnhub_api_key = "test_key"
            response = client.post(
                "/api/v1/collect/stock",
                json={
                    "query": "Apple",
                    "stock_code": "AAPL",
                    "market": "US",
                    "add_to_scope": False,
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["stock_code"] == "AAPL"

    def test_invalid_market_returns_400(self, client, auth_headers):
        """지원하지 않는 market은 400 에러를 반환한다."""
        response = client.post(
            "/api/v1/collect/stock",
            json={
                "query": "Test",
                "stock_code": "TEST",
                "market": "JP",
                "add_to_scope": False,
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("app.collectors.pipeline.process_collected_items", new_callable=AsyncMock, return_value=0)
    @patch("app.collectors.naver.NaverCollector.collect", new_callable=AsyncMock, return_value=[])
    @patch("app.core.scope_writer.add_kr_search_query", return_value=True)
    @patch("app.core.scope_writer.add_korean_stock", return_value=True)
    @patch("app.core.scope_loader.reload_scope", return_value={})
    def test_add_to_scope_kr(
        self,
        mock_reload,
        mock_add_stock,
        mock_add_query,
        mock_collect,
        mock_process,
        client,
        auth_headers,
    ):
        """add_to_scope=true 시 scope에 종목이 추가된다."""
        response = client.post(
            "/api/v1/collect/stock",
            json={
                "query": "한화에어로스페이스",
                "stock_code": "012450",
                "market": "KR",
                "add_to_scope": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["added_to_scope"] is True
        mock_add_query.assert_called_once_with("한화에어로스페이스", "012450")
        mock_add_stock.assert_called_once_with("한화에어로스페이스", "012450")
        mock_reload.assert_called_once()

    @patch("app.collectors.pipeline.process_collected_items", new_callable=AsyncMock, return_value=0)
    @patch("app.collectors.naver.NaverCollector.collect", new_callable=AsyncMock, return_value=[])
    def test_unauthorized_without_api_key(self, mock_collect, mock_process, client):
        """API 키 없이 호출 시 인증 에러를 반환한다 (production 모드)."""
        from app.core.config import settings

        # Configure production mode with auth required
        original_env = settings.app_env
        original_auth = settings.require_auth

        try:
            settings.app_env = "production"
            settings.require_auth = True

            response = client.post(
                "/api/v1/collect/stock",
                json={
                    "query": "삼성전자",
                    "stock_code": "005930",
                    "market": "KR",
                    "add_to_scope": False,
                },
            )
            # In production with require_auth=True and no API key, should return 401
            assert response.status_code == 401
        finally:
            # Restore original settings
            settings.app_env = original_env
            settings.require_auth = original_auth
