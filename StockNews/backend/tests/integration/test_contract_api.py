"""Contract tests: verify API responses match shared/contracts/news-api.json.

These tests ensure backward compatibility with StockAgent (consumer).
If any test fails, it means a breaking change was introduced that could
break StockAgent's integration.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.news_event import NewsEvent

# Load contract
CONTRACT_PATH = Path(__file__).resolve().parents[4] / "shared" / "contracts" / "news-api.json"

API_KEY_HEADER = {"X-API-Key": "dev-api-key-change-in-production"}


@pytest.fixture(autouse=True)
def _disable_rate_limit():
    """Disable rate limiting for contract tests."""
    app.state.limiter.enabled = False
    yield
    app.state.limiter.enabled = True


@pytest.fixture()
def seed_data(integration_session_factory):
    """Seed test data for contract tests."""
    session = integration_session_factory()

    # Seed data matching contract expectations
    events = [
        NewsEvent(
            title="삼성전자 실적 발표",
            stock_code="005930",
            stock_name="삼성전자",
            sentiment="positive",
            sentiment_score=0.8,
            news_score=85.0,
            source="naver",
            market="KR",
            theme="반도체",
            is_disclosure=True,
            published_at=datetime.now(timezone.utc),
        ),
        NewsEvent(
            title="삼성전자 특허 소송",
            stock_code="005930",
            stock_name="삼성전자",
            sentiment="negative",
            sentiment_score=-0.3,
            news_score=60.0,
            source="naver",
            market="KR",
            theme="법률",
            is_disclosure=False,
            published_at=datetime.now(timezone.utc),
        ),
        NewsEvent(
            title="AAPL Earnings Beat",
            stock_code="AAPL",
            stock_name="Apple Inc.",
            sentiment="positive",
            sentiment_score=0.9,
            news_score=90.0,
            source="finnhub",
            market="US",
            theme="Earnings",
            is_disclosure=False,
            published_at=datetime.now(timezone.utc),
        ),
    ]
    session.add_all(events)
    session.commit()
    session.close()


@pytest.fixture()
def client():
    """TestClient — DB override handled by conftest.py autouse fixture."""
    return TestClient(app, raise_server_exceptions=False)


class TestContractExists:
    """Verify contract file is available."""

    def test_contract_file_exists(self):
        assert CONTRACT_PATH.exists(), f"Contract file not found: {CONTRACT_PATH}"

    def test_contract_is_valid_json(self):
        data = json.loads(CONTRACT_PATH.read_text())
        assert data["contract_version"] == "1.1"
        assert data["provider"] == "StockNews"
        assert data["consumer"] == "StockAgent"


class TestNewsScoreContract:
    """GET /api/v1/news/score — contract compliance."""

    def test_required_fields_present(self, client, seed_data):
        """All fields required by StockAgent are present."""
        resp = client.get("/api/v1/news/score?stock=005930", headers=API_KEY_HEADER)
        assert resp.status_code == 200
        data = resp.json()

        # Required by contract
        assert "stock_code" in data
        assert "news_score" in data
        assert "recency" in data
        assert "frequency" in data
        assert "sentiment_score" in data
        assert "disclosure" in data
        assert "news_count" in data

    def test_field_types(self, client, seed_data):
        """Field types match contract specification."""
        resp = client.get("/api/v1/news/score?stock=005930", headers=API_KEY_HEADER)
        data = resp.json()

        assert isinstance(data["stock_code"], str)
        assert isinstance(data["news_score"], (int, float))
        assert isinstance(data["recency"], (int, float))
        assert isinstance(data["frequency"], (int, float))
        assert isinstance(data["sentiment_score"], (int, float))
        assert isinstance(data["disclosure"], (int, float))
        assert isinstance(data["news_count"], int)
        assert data["stock_name"] is None or isinstance(data["stock_name"], str)

    def test_score_ranges(self, client, seed_data):
        """Scores are within contracted ranges."""
        resp = client.get("/api/v1/news/score?stock=005930", headers=API_KEY_HEADER)
        data = resp.json()

        assert 0 <= data["news_score"] <= 100
        assert -1.0 <= data["sentiment_score"] <= 1.0
        assert data["news_count"] >= 0

    def test_empty_stock_returns_defaults(self, client, seed_data):
        """Unknown stock returns zero defaults (not 404)."""
        resp = client.get("/api/v1/news/score?stock=UNKNOWN", headers=API_KEY_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data["stock_code"] == "UNKNOWN"
        assert data["news_score"] == 0.0
        assert data["news_count"] == 0

    def test_additional_fields_allowed(self, client, seed_data):
        """Contract allows additional fields beyond required ones."""
        resp = client.get("/api/v1/news/score?stock=005930", headers=API_KEY_HEADER)
        data = resp.json()
        # These are StockNews extensions beyond the contract — allowed
        # Just verify they don't break the required fields
        required = {"stock_code", "news_score", "recency", "frequency",
                    "sentiment_score", "disclosure", "news_count"}
        assert required.issubset(set(data.keys()))


class TestNewsTopContract:
    """GET /api/v1/news/top — contract compliance."""

    def test_returns_list(self, client, seed_data):
        resp = client.get("/api/v1/news/top?market=KR", headers=API_KEY_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_item_required_fields(self, client, seed_data):
        """Each item has all contract-required fields."""
        resp = client.get("/api/v1/news/top?market=KR", headers=API_KEY_HEADER)
        data = resp.json()
        assert len(data) > 0

        for item in data:
            assert "stock_code" in item
            assert "news_score" in item
            assert "sentiment" in item
            assert "news_count" in item
            assert "market" in item

    def test_item_field_types(self, client, seed_data):
        resp = client.get("/api/v1/news/top?market=KR", headers=API_KEY_HEADER)
        for item in resp.json():
            assert isinstance(item["stock_code"], str)
            assert isinstance(item["news_score"], (int, float))
            assert isinstance(item["sentiment"], str)
            assert item["sentiment"] in ("positive", "neutral", "negative")
            assert isinstance(item["news_count"], int)
            assert item["market"] in ("KR", "US")

    def test_market_filter(self, client, seed_data):
        """Market filter returns only matching items."""
        resp = client.get("/api/v1/news/top?market=US", headers=API_KEY_HEADER)
        for item in resp.json():
            assert item["market"] == "US"

    def test_limit_parameter(self, client, seed_data):
        resp = client.get("/api/v1/news/top?market=KR&limit=1", headers=API_KEY_HEADER)
        assert len(resp.json()) <= 1


class TestPredictionContract:
    """GET /api/v1/stocks/{code}/prediction — contract compliance."""

    def test_required_fields(self, client, seed_data):
        resp = client.get("/api/v1/stocks/005930/prediction", headers=API_KEY_HEADER)
        assert resp.status_code == 200
        data = resp.json()

        assert "stock_code" in data
        assert "prediction_score" in data
        assert "direction" in data
        assert "confidence" in data
        assert "based_on_days" in data

    def test_field_types(self, client, seed_data):
        resp = client.get("/api/v1/stocks/005930/prediction", headers=API_KEY_HEADER)
        data = resp.json()

        assert isinstance(data["stock_code"], str)
        assert data["prediction_score"] is None or isinstance(data["prediction_score"], (int, float))
        assert data["direction"] is None or data["direction"] in ("up", "down", "neutral")
        assert data["confidence"] is None or isinstance(data["confidence"], (int, float))
        assert isinstance(data["based_on_days"], int)

    def test_unknown_stock_returns_nulls(self, client, seed_data):
        """Unknown stock returns null prediction (not 404)."""
        resp = client.get("/api/v1/stocks/UNKNOWN/prediction", headers=API_KEY_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data["stock_code"] == "UNKNOWN"
        assert data["prediction_score"] is None


class TestHealthContract:
    """GET /health — contract compliance."""

    def test_health_fields(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()

        assert "status" in data
        assert data["status"] in ("ok", "degraded", "error")
        assert "version" in data

    def test_health_no_auth_required(self, client):
        """Health endpoint does not require authentication."""
        resp = client.get("/health")
        assert resp.status_code == 200


class TestBackwardCompatibility:
    """Verify no breaking changes to contracted fields."""

    def test_contract_endpoints_reachable(self, client, seed_data):
        """All contract endpoints return 200 (not 404)."""
        endpoints = [
            "/api/v1/news/score?stock=005930",
            "/api/v1/news/top?market=KR",
            "/api/v1/stocks/005930/prediction",
            "/health",
        ]
        for ep in endpoints:
            headers = API_KEY_HEADER if "/api/" in ep else {}
            resp = client.get(ep, headers=headers)
            assert resp.status_code == 200, f"{ep} returned {resp.status_code}"

    def test_score_endpoint_query_param_name(self, client, seed_data):
        """Contract specifies ?stock= parameter (not ?code= or ?symbol=)."""
        resp = client.get("/api/v1/news/score?stock=005930", headers=API_KEY_HEADER)
        assert resp.status_code == 200

    def test_top_endpoint_query_param_names(self, client, seed_data):
        """Contract specifies ?market= and ?limit= parameters."""
        resp = client.get("/api/v1/news/top?market=KR&limit=5", headers=API_KEY_HEADER)
        assert resp.status_code == 200
