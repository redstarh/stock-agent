"""Redis Pub/Sub 메시지 스키마 테스트."""

import pytest
from pydantic import ValidationError

from app.schemas.pubsub import (
    BreakingNewsMessage,
    Market,
    MessageType,
    ScoreUpdateMessage,
    validate_message,
)


class TestBreakingNewsMessage:
    """BreakingNewsMessage 스키마 테스트."""

    def test_valid_message(self):
        msg = BreakingNewsMessage(
            stock_code="005930",
            title="삼성전자 실적 발표",
            news_score=85.5,
            market=Market.KR,
        )
        assert msg.type == MessageType.BREAKING_NEWS
        assert msg.schema_version == 1
        assert msg.stock_code == "005930"
        assert msg.news_score == 85.5

    def test_score_range_validation(self):
        with pytest.raises(ValidationError):
            BreakingNewsMessage(
                stock_code="005930",
                title="test",
                news_score=150.0,  # Over 100
                market=Market.KR,
            )

    def test_sentiment_range_validation(self):
        with pytest.raises(ValidationError):
            BreakingNewsMessage(
                stock_code="005930",
                title="test",
                news_score=50.0,
                market=Market.KR,
                sentiment=2.0,  # Over 1.0
            )

    def test_extra_fields_ignored(self):
        msg = BreakingNewsMessage(
            stock_code="005930",
            title="test",
            news_score=50.0,
            market=Market.KR,
            unknown_field="ignored",
        )
        assert not hasattr(msg, "unknown_field")

    def test_serialization_roundtrip(self):
        msg = BreakingNewsMessage(
            stock_code="AAPL",
            title="Apple earnings",
            news_score=90.0,
            market=Market.US,
            sentiment=0.8,
        )
        json_str = msg.model_dump_json()
        restored = BreakingNewsMessage.model_validate_json(json_str)
        assert restored.stock_code == "AAPL"
        assert restored.market == Market.US


class TestValidateMessage:
    """validate_message 함수 테스트."""

    def test_breaking_news_type(self):
        raw = {
            "type": "breaking_news",
            "stock_code": "005930",
            "title": "test",
            "news_score": 85.0,
            "market": "KR",
        }
        result = validate_message(raw)
        assert isinstance(result, BreakingNewsMessage)

    def test_score_update_type(self):
        raw = {
            "type": "score_update",
            "stock_code": "005930",
            "news_score": 75.0,
            "market": "KR",
        }
        result = validate_message(raw)
        assert isinstance(result, ScoreUpdateMessage)

    def test_unknown_type_returns_none(self):
        raw = {"type": "unknown", "data": "test"}
        result = validate_message(raw)
        assert result is None

    def test_invalid_data_raises(self):
        raw = {
            "type": "breaking_news",
            "stock_code": "005930",
            # missing required 'title' and 'news_score'
        }
        with pytest.raises(ValidationError):
            validate_message(raw)
