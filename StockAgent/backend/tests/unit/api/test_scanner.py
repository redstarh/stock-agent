"""T-B13: Scanner API 테스트"""
import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_top_stocks_default(client):
    """GET /api/v1/scanner/top with default params"""
    resp = client.get("/api/v1/scanner/top")
    assert resp.status_code == 200
    data = resp.json()
    assert "stocks" in data
    assert "count" in data
    assert isinstance(data["stocks"], list)
    assert isinstance(data["count"], int)
    assert data["count"] == len(data["stocks"])


def test_get_top_stocks_custom_top_n(client):
    """GET /api/v1/scanner/top?top_n=5"""
    resp = client.get("/api/v1/scanner/top?top_n=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "stocks" in data
    assert "count" in data
    assert isinstance(data["stocks"], list)
    assert isinstance(data["count"], int)
    # Since stocks list is empty in current implementation, count should be 0
    assert data["count"] == len(data["stocks"])


def test_get_top_stocks_invalid_top_n(client):
    """GET /api/v1/scanner/top?top_n=0 should return 422 (validation error)"""
    resp = client.get("/api/v1/scanner/top?top_n=0")
    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data


def test_get_top_stocks_exceeds_max(client):
    """GET /api/v1/scanner/top?top_n=101 should return 422"""
    resp = client.get("/api/v1/scanner/top?top_n=101")
    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data
