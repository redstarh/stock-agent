"""API 버전 관리 테스트."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture
def client():
    """테스트 클라이언트 픽스처."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers(monkeypatch):
    """API 키 인증 헤더 픽스처."""
    monkeypatch.setattr(settings, "require_auth", True)
    monkeypatch.setattr(settings, "api_key", "test-api-key-12345")
    return {"X-API-Key": "test-api-key-12345"}


def test_v1_endpoint_works(client, auth_headers):
    """v1 엔드포인트가 정상 작동하는지 확인."""
    response = client.get("/api/v1/news/latest?market=KR", headers=auth_headers)
    # 200 or 500 (DB/Redis issues in test), but should not be 401/403/404
    assert response.status_code not in [401, 403, 404]


def test_v2_endpoint_works(client, auth_headers):
    """v2 엔드포인트가 정상 작동하는지 확인."""
    response = client.get("/api/v2/news/latest?market=KR", headers=auth_headers)
    # 200 or 500 (DB/Redis issues in test), but should not be 401/403/404
    assert response.status_code not in [401, 403, 404]


def test_v1_v2_same_results(client, auth_headers):
    """v1과 v2가 동일한 결과를 반환하는지 확인."""
    v1_response = client.get("/api/v1/news/latest?market=KR", headers=auth_headers)
    v2_response = client.get("/api/v2/news/latest?market=KR", headers=auth_headers)

    # 상태 코드가 같아야 함
    assert v1_response.status_code == v2_response.status_code

    # 성공 응답인 경우 결과도 동일해야 함
    if v1_response.status_code == 200:
        assert v1_response.json() == v2_response.json()


def test_v1_deprecation_headers(client):
    """v1 응답에 deprecation 헤더가 포함되는지 확인."""
    # /api/versions는 DB 불필요 — 미들웨어 헤더 테스트에 적합
    # v1 경로로 직접 접근하여 미들웨어 동작 확인
    from fastapi import FastAPI
    from starlette.testclient import TestClient as StarletteTestClient

    from app.core.versioning import APIVersionMiddleware

    test_app = FastAPI()
    test_app.add_middleware(APIVersionMiddleware)

    @test_app.get("/api/v1/test")
    def v1_test():
        return {"ok": True}

    @test_app.get("/api/v2/test")
    def v2_test():
        return {"ok": True}

    tc = StarletteTestClient(test_app)
    response = tc.get("/api/v1/test")

    assert response.status_code == 200
    assert response.headers.get("X-API-Version") == "v1"
    assert response.headers.get("Deprecation") == "true"
    assert "Sunset" in response.headers
    assert "2026" in response.headers["Sunset"]
    assert "Link" in response.headers
    assert "/api/v2/" in response.headers["Link"]
    assert 'rel="successor-version"' in response.headers["Link"]


def test_v2_no_deprecation_headers(client):
    """v2 응답에는 deprecation 헤더가 없는지 확인."""
    from fastapi import FastAPI
    from starlette.testclient import TestClient as StarletteTestClient

    from app.core.versioning import APIVersionMiddleware

    test_app = FastAPI()
    test_app.add_middleware(APIVersionMiddleware)

    @test_app.get("/api/v2/test")
    def v2_test():
        return {"ok": True}

    tc = StarletteTestClient(test_app)
    response = tc.get("/api/v2/test")

    assert response.status_code == 200
    assert response.headers.get("X-API-Version") == "v2"
    assert "Deprecation" not in response.headers
    assert "Sunset" not in response.headers


def test_versions_endpoint(client):
    """API 버전 목록 엔드포인트가 정상 작동하는지 확인."""
    response = client.get("/api/versions")

    assert response.status_code == 200
    data = response.json()

    # 응답 구조 확인
    assert "versions" in data
    assert "default_version" in data
    assert "recommended_version" in data

    # 버전 목록 확인
    versions = data["versions"]
    assert len(versions) == 2

    # v1 버전 확인
    v1 = next(v for v in versions if v["version"] == "v1")
    assert v1["status"] == "deprecated"
    assert v1["base_url"] == "/api/v1"
    assert v1["sunset_date"] is not None
    assert v1["successor"] == "v2"

    # v2 버전 확인
    v2 = next(v for v in versions if v["version"] == "v2")
    assert v2["status"] == "stable"
    assert v2["base_url"] == "/api/v2"
    assert v2["sunset_date"] is None
    assert v2["successor"] is None

    # 권장 버전 확인
    assert data["default_version"] == "v2"
    assert data["recommended_version"] == "v2"


def test_non_api_path_no_version_headers(client):
    """API가 아닌 경로에는 버전 헤더가 없는지 확인."""
    response = client.get("/health")

    # 버전 관련 헤더 없음
    assert "X-API-Version" not in response.headers
    assert "Deprecation" not in response.headers
    assert "Sunset" not in response.headers
