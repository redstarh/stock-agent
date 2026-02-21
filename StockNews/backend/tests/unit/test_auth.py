"""API 인증 테스트."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.auth import is_public_endpoint
from app.core.config import settings
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


class TestPublicEndpoints:
    """Public 엔드포인트 테스트."""

    def test_is_public_endpoint(self):
        """Public 엔드포인트 확인."""
        assert is_public_endpoint("/health") is True
        assert is_public_endpoint("/docs") is True
        assert is_public_endpoint("/openapi.json") is True
        assert is_public_endpoint("/redoc") is True
        assert is_public_endpoint("/metrics") is True
        assert is_public_endpoint("/api/v1/news/score") is False

    def test_health_endpoint_no_auth(self):
        """Health 엔드포인트는 인증 불필요."""
        response = client.get("/health")
        assert response.status_code == 200


class TestApiKeyValidation:
    """API Key 검증 테스트."""

    @pytest.fixture(autouse=True)
    def setup_auth(self, monkeypatch):
        """인증 활성화."""
        monkeypatch.setattr(settings, "require_auth", True)
        monkeypatch.setattr(settings, "app_env", "production")
        monkeypatch.setattr(settings, "api_key", "test-api-key-12345")

    def test_valid_api_key(self):
        """유효한 API Key로 요청 성공."""
        response = client.get(
            "/api/v1/news/latest?market=KR",
            headers={"X-API-Key": "test-api-key-12345"},
        )
        # 200 or 500 (DB connection issues in test env), but not 401/403
        assert response.status_code not in [401, 403]

    def test_invalid_api_key(self):
        """잘못된 API Key로 요청 실패."""
        response = client.get(
            "/api/v1/news/latest?market=KR",
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid API Key" in response.json()["detail"]

    def test_missing_api_key(self):
        """API Key 없이 요청 실패."""
        response = client.get("/api/v1/news/latest?market=KR")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Missing API Key" in response.json()["detail"]


class TestDevelopmentMode:
    """Development 모드 테스트."""

    @pytest.fixture(autouse=True)
    def setup_dev_mode(self, monkeypatch):
        """Development 모드 설정."""
        monkeypatch.setattr(settings, "app_env", "development")
        monkeypatch.setattr(settings, "require_auth", True)

    def test_skip_auth_in_development(self):
        """Development 모드에서는 인증 스킵."""
        response = client.get("/api/v1/news/latest?market=KR")
        # Should not return 401/403 in development mode
        assert response.status_code not in [401, 403]


class TestAuthDisabled:
    """인증 비활성화 테스트."""

    @pytest.fixture(autouse=True)
    def setup_no_auth(self, monkeypatch):
        """인증 비활성화."""
        monkeypatch.setattr(settings, "require_auth", False)
        monkeypatch.setattr(settings, "app_env", "production")

    def test_skip_auth_when_disabled(self):
        """require_auth=False일 때 인증 스킵."""
        response = client.get("/api/v1/news/latest?market=KR")
        # Should not return 401/403 when auth is disabled
        assert response.status_code not in [401, 403]


class TestPublicEndpointsNoAuth:
    """Public 엔드포인트는 항상 인증 불필요."""

    @pytest.fixture(autouse=True)
    def setup_strict_auth(self, monkeypatch):
        """엄격한 인증 모드 설정."""
        monkeypatch.setattr(settings, "require_auth", True)
        monkeypatch.setattr(settings, "app_env", "production")

    def test_health_no_auth_required(self):
        """Health 엔드포인트는 항상 인증 불필요."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_docs_no_auth_required(self):
        """Docs 엔드포인트는 항상 인증 불필요."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_no_auth_required(self):
        """OpenAPI 스키마는 항상 인증 불필요."""
        response = client.get("/openapi.json")
        assert response.status_code == 200


class TestApiKeyRotation:
    """API Key 회전 테스트."""

    @pytest.fixture(autouse=True)
    def setup_rotation(self, monkeypatch):
        """회전 키 설정."""
        monkeypatch.setattr(settings, "require_auth", True)
        monkeypatch.setattr(settings, "app_env", "production")
        monkeypatch.setattr(settings, "api_key", "current-key-12345")
        monkeypatch.setattr(settings, "api_key_next", "next-key-67890")

    def test_current_key_accepted(self):
        """현재 키로 요청 성공."""
        response = client.get(
            "/api/v1/news/latest?market=KR",
            headers={"X-API-Key": "current-key-12345"},
        )
        assert response.status_code not in [401, 403]

    def test_next_key_accepted(self):
        """회전 키로 요청 성공."""
        response = client.get(
            "/api/v1/news/latest?market=KR",
            headers={"X-API-Key": "next-key-67890"},
        )
        assert response.status_code not in [401, 403]

    def test_old_key_rejected(self):
        """무효한 키 거부."""
        response = client.get(
            "/api/v1/news/latest?market=KR",
            headers={"X-API-Key": "old-expired-key"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_rotation_without_next_key(self, monkeypatch):
        """next 키 미설정 시 current 키만 유효."""
        monkeypatch.setattr(settings, "api_key_next", "")
        response = client.get(
            "/api/v1/news/latest?market=KR",
            headers={"X-API-Key": "next-key-67890"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
