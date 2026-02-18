"""Unit tests for enhanced pubsub functionality."""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.core.pubsub import publish_news_event, should_publish_breaking


class MockNewsEvent:
    """Mock NewsEvent for testing."""

    def __init__(
        self,
        stock_code: str = "005930",
        title: str = "Test news",
        market: str = "KR",
        stock_name: str | None = "삼성전자",
        theme: str | None = "반도체",
        sentiment: str = "positive",
        published_at: datetime | None = None,
    ):
        self.stock_code = stock_code
        self.title = title
        self.market = market
        self.stock_name = stock_name
        self.theme = theme
        self.sentiment = sentiment
        self.published_at = published_at or datetime.now(timezone.utc)


class TestPublishNewsEvent:
    """NewsEvent 기반 발행 테스트."""

    def test_publish_news_event_above_threshold(self):
        """점수 >= 80: NewsEvent 발행."""
        mock_redis = MagicMock()
        news = MockNewsEvent(
            stock_code="005930",
            title="삼성전자 급등",
            market="KR",
            stock_name="삼성전자",
            theme="반도체",
            sentiment="positive",
        )

        result = publish_news_event(mock_redis, news, score=85.0)

        assert result is True
        mock_redis.publish.assert_called_once()

        # 발행된 메시지 확인
        call_args = mock_redis.publish.call_args
        channel = call_args[0][0]
        payload = json.loads(call_args[0][1])

        assert channel == "news_breaking_kr"
        assert payload["type"] == "breaking_news"
        assert payload["stock_code"] == "005930"
        assert payload["stock_name"] == "삼성전자"
        assert payload["title"] == "삼성전자 급등"
        assert payload["theme"] == "반도체"
        assert payload["sentiment"] == "positive"
        assert payload["news_score"] == 85.0
        assert payload["market"] == "KR"
        assert payload["published_at"] is not None

    def test_publish_news_event_below_threshold(self):
        """점수 < 80: 발행 안 함."""
        mock_redis = MagicMock()
        news = MockNewsEvent()

        result = publish_news_event(mock_redis, news, score=75.0)

        assert result is False
        mock_redis.publish.assert_not_called()

    def test_publish_news_event_us_market(self):
        """US 마켓 채널 확인."""
        mock_redis = MagicMock()
        news = MockNewsEvent(
            stock_code="AAPL",
            title="Apple breaks record",
            market="US",
            stock_name="Apple Inc.",
        )

        result = publish_news_event(mock_redis, news, score=90.0)

        assert result is True
        call_args = mock_redis.publish.call_args
        channel = call_args[0][0]
        assert channel == "news_breaking_us"

    def test_publish_news_event_with_none_fields(self):
        """Optional 필드가 None인 경우."""
        mock_redis = MagicMock()
        news = MockNewsEvent(
            stock_code="000000",
            title="Unknown stock",
            market="KR",
            stock_name=None,
            theme=None,
        )

        result = publish_news_event(mock_redis, news, score=82.0)

        assert result is True
        call_args = mock_redis.publish.call_args
        payload = json.loads(call_args[0][1])

        assert payload["stock_name"] is None
        assert payload["theme"] is None

    def test_breaking_threshold_edge_cases(self):
        """경계값 테스트."""
        assert should_publish_breaking(79.99) is False
        assert should_publish_breaking(80.0) is True
        assert should_publish_breaking(80.01) is True
        assert should_publish_breaking(100.0) is True
