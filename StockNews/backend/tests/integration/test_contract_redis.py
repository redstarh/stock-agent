"""Contract tests: verify Redis Pub/Sub messages match shared/contracts/redis-messages.json.

These tests ensure StockAgent can correctly parse breaking news messages
published by StockNews.

NOTE: Known discrepancy — contract says field `score`, code publishes `news_score`.
      StockAgent must handle both field names. Tests document the actual behavior.
"""

import json
from pathlib import Path

import fakeredis
import pytest

from app.core.pubsub import (
    BREAKING_THRESHOLD,
    get_channel_name,
    publish_breaking_news,
    publish_news_event,
    should_publish_breaking,
)

# Load contract
CONTRACT_PATH = Path(__file__).resolve().parents[4] / "shared" / "contracts" / "redis-messages.json"


@pytest.fixture()
def redis_client():
    """FakeRedis client for testing."""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture()
def contract():
    """Load Redis message contract."""
    return json.loads(CONTRACT_PATH.read_text())


class TestContractExists:
    """Verify contract file is available."""

    def test_contract_file_exists(self):
        assert CONTRACT_PATH.exists(), f"Contract file not found: {CONTRACT_PATH}"

    def test_contract_is_valid_json(self):
        data = json.loads(CONTRACT_PATH.read_text())
        assert data["contract_version"] == "1.1"
        assert data["publisher"] == "StockNews (app/core/pubsub.py)"


class TestBreakingThreshold:
    """Verify breaking news threshold matches contract."""

    def test_threshold_matches_contract(self, contract):
        """Code threshold matches contract threshold."""
        expected = contract["channels"]["breaking_news"]["trigger_threshold"]
        assert expected == BREAKING_THRESHOLD

    def test_below_threshold_not_published(self):
        assert should_publish_breaking(79.9) is False

    def test_at_threshold_published(self):
        assert should_publish_breaking(80.0) is True

    def test_above_threshold_published(self):
        assert should_publish_breaking(95.0) is True


class TestChannelNaming:
    """Verify channel naming convention."""

    def test_kr_channel(self):
        """Korean market channel name."""
        assert get_channel_name("KR") == "news_breaking_kr"

    def test_us_channel(self):
        """US market channel name."""
        assert get_channel_name("US") == "news_breaking_us"

    def test_channel_documented_discrepancy(self, contract):
        """Document: contract says 'breaking_news' but code uses 'news_breaking_{market}'.

        StockAgent subscribes to the actual channel names, not the contract name.
        This discrepancy is documented here for awareness.
        """
        contract_channel = list(contract["channels"].keys())[0]
        actual_kr = get_channel_name("KR")
        # The contract says "breaking_news" but actual channels are "news_breaking_kr" / "news_breaking_us"
        assert contract_channel == "breaking_news"
        assert actual_kr == "news_breaking_kr"
        # This is a known discrepancy — StockAgent uses actual channel names


class TestMessageFormat:
    """Verify published message format matches contract."""

    def test_required_fields_present(self, redis_client):
        """All contract-required fields are in the published message."""
        pubsub = redis_client.pubsub()
        pubsub.subscribe("news_breaking_kr")
        # Consume subscribe confirmation
        pubsub.get_message()

        publish_breaking_news(
            redis_client=redis_client,
            stock_code="005930",
            title="삼성전자 실적 발표",
            score=85.0,
            market="KR",
            stock_name="삼성전자",
            theme="반도체",
            sentiment_score=0.8,
            published_at="2024-01-15T09:00:00",
        )

        msg = pubsub.get_message()
        assert msg is not None
        assert msg["type"] == "message"

        data = json.loads(msg["data"])

        # Contract required fields
        assert data["type"] == "breaking_news"
        assert data["stock_code"] == "005930"
        assert data["title"] == "삼성전자 실적 발표"
        assert data["market"] == "KR"
        assert isinstance(data["sentiment"], (int, float))

    def test_message_field_types(self, redis_client):
        """Field types match contract specification."""
        pubsub = redis_client.pubsub()
        pubsub.subscribe("news_breaking_kr")
        pubsub.get_message()

        publish_breaking_news(
            redis_client=redis_client,
            stock_code="005930",
            title="테스트 뉴스",
            score=90.0,
            market="KR",
            sentiment_score=0.5,
        )

        msg = pubsub.get_message()
        data = json.loads(msg["data"])

        assert isinstance(data["type"], str)
        assert isinstance(data["stock_code"], str)
        assert isinstance(data["title"], str)
        assert isinstance(data["market"], str)
        assert isinstance(data["sentiment"], (int, float))
        assert -1.0 <= data["sentiment"] <= 1.0

    def test_score_field_name_discrepancy(self, redis_client):
        """Document: contract expects 'score' but code publishes 'news_score'.

        StockAgent should handle 'news_score' field (actual) not 'score' (contract).
        """
        pubsub = redis_client.pubsub()
        pubsub.subscribe("news_breaking_kr")
        pubsub.get_message()

        publish_breaking_news(
            redis_client=redis_client,
            stock_code="005930",
            title="테스트",
            score=85.0,
            market="KR",
        )

        msg = pubsub.get_message()
        data = json.loads(msg["data"])

        # Actual behavior: field is "news_score" not "score"
        assert "news_score" in data
        assert data["news_score"] == 85.0
        # Contract says "score" — this is a known discrepancy
        assert "score" not in data

    def test_market_enum_kr(self, redis_client):
        """KR market value is preserved."""
        pubsub = redis_client.pubsub()
        pubsub.subscribe("news_breaking_kr")
        pubsub.get_message()

        publish_breaking_news(
            redis_client=redis_client,
            stock_code="005930",
            title="KR test",
            score=80.0,
            market="KR",
        )

        msg = pubsub.get_message()
        data = json.loads(msg["data"])
        assert data["market"] == "KR"

    def test_market_enum_us(self, redis_client):
        """US market value is preserved."""
        pubsub = redis_client.pubsub()
        pubsub.subscribe("news_breaking_us")
        pubsub.get_message()

        publish_breaking_news(
            redis_client=redis_client,
            stock_code="AAPL",
            title="US test",
            score=80.0,
            market="US",
        )

        msg = pubsub.get_message()
        data = json.loads(msg["data"])
        assert data["market"] == "US"

    def test_optional_fields_included(self, redis_client):
        """Optional fields (stock_name, theme, published_at) are included when provided."""
        pubsub = redis_client.pubsub()
        pubsub.subscribe("news_breaking_kr")
        pubsub.get_message()

        publish_breaking_news(
            redis_client=redis_client,
            stock_code="005930",
            title="Full payload",
            score=85.0,
            market="KR",
            stock_name="삼성전자",
            theme="반도체",
            sentiment_score=0.7,
            published_at="2024-01-15T09:00:00",
        )

        msg = pubsub.get_message()
        data = json.loads(msg["data"])

        assert data["stock_name"] == "삼성전자"
        assert data["theme"] == "반도체"
        assert data["published_at"] == "2024-01-15T09:00:00"

    def test_optional_fields_null_when_omitted(self, redis_client):
        """Optional fields are null when not provided."""
        pubsub = redis_client.pubsub()
        pubsub.subscribe("news_breaking_kr")
        pubsub.get_message()

        publish_breaking_news(
            redis_client=redis_client,
            stock_code="005930",
            title="Minimal payload",
            score=80.0,
            market="KR",
        )

        msg = pubsub.get_message()
        data = json.loads(msg["data"])

        assert data["stock_name"] is None
        assert data["theme"] is None
        assert data["published_at"] is None


class TestPublishNewsEvent:
    """Test publish_news_event helper with threshold check."""

    def test_below_threshold_not_published(self, redis_client):
        """Events below threshold are not published."""
        from unittest.mock import MagicMock

        event = MagicMock()
        event.stock_code = "005930"
        event.title = "Low score news"
        event.market = "KR"
        event.stock_name = "삼성전자"
        event.theme = "반도체"
        event.sentiment_score = 0.5
        event.published_at = None

        result = publish_news_event(redis_client, event, score=50.0)
        assert result is False

    def test_above_threshold_published(self, redis_client):
        """Events at or above threshold are published."""
        from unittest.mock import MagicMock

        event = MagicMock()
        event.stock_code = "005930"
        event.title = "High score news"
        event.market = "KR"
        event.stock_name = "삼성전자"
        event.theme = "반도체"
        event.sentiment_score = 0.9
        event.published_at = None

        pubsub = redis_client.pubsub()
        pubsub.subscribe("news_breaking_kr")
        pubsub.get_message()

        result = publish_news_event(redis_client, event, score=85.0)
        assert result is True

        msg = pubsub.get_message()
        assert msg is not None
        data = json.loads(msg["data"])
        assert data["stock_code"] == "005930"
