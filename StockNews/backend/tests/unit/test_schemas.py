"""RED: Pydantic 스키마 테스트 — SentimentEnum, NewsItem, ErrorResponse."""

import pytest
from pydantic import ValidationError


class TestSentimentEnum:
    def test_valid_values(self):
        """positive, neutral, negative만 허용."""
        from app.schemas.common import SentimentEnum

        assert SentimentEnum.positive == "positive"
        assert SentimentEnum.neutral == "neutral"
        assert SentimentEnum.negative == "negative"

    def test_invalid_value_raises(self):
        """'unknown' → ValidationError."""
        from app.schemas.common import SentimentEnum

        with pytest.raises(ValueError):
            SentimentEnum("unknown")


class TestNewsItemSchema:
    def test_has_market_field(self):
        """NewsItem에 market 필드 존재."""
        from app.schemas.news import NewsItem

        item = NewsItem(
            id=1, title="test", stock_code="005930", sentiment="positive",
            news_score=80.0, source="naver", market="KR",
            published_at="2024-01-15T09:00:00",
        )
        assert item.market == "KR"

    def test_has_source_url_field(self):
        """NewsItem에 source_url 필드 존재."""
        from app.schemas.news import NewsItem

        item = NewsItem(
            id=1, title="test", stock_code="005930", sentiment="positive",
            news_score=80.0, source="naver", market="KR",
            published_at="2024-01-15T09:00:00",
            source_url="https://news.naver.com/1",
        )
        assert item.source_url == "https://news.naver.com/1"

    def test_has_published_at_field(self):
        """NewsItem에 published_at 필드 존재 (timestamp 아님)."""
        from app.schemas.news import NewsItem

        item = NewsItem(
            id=1, title="test", stock_code="005930", sentiment="positive",
            news_score=80.0, source="naver", market="KR",
            published_at="2024-01-15T09:00:00",
        )
        assert item.published_at is not None
        assert not hasattr(item, "timestamp")


class TestNewsScoreResponse:
    def test_score_fields(self):
        """NewsScoreResponse에 4요소 + 최종 점수."""
        from app.schemas.news import NewsScoreResponse

        resp = NewsScoreResponse(
            stock_code="005930", stock_name="삼성전자",
            news_score=85.5, recency=90, frequency=80,
            sentiment_score=85, disclosure=100, news_count=12,
        )
        assert resp.news_score == 85.5
        assert resp.recency == 90


class TestTimelinePoint:
    def test_timeline_fields(self):
        """TimelinePoint에 date + score."""
        from app.schemas.common import TimelinePoint

        point = TimelinePoint(date="2024-01-15", score=85.5)
        assert point.date == "2024-01-15"
        assert point.score == 85.5


class TestThemeItem:
    def test_theme_fields(self):
        """ThemeItem 필드 확인."""
        from app.schemas.theme import ThemeItem

        item = ThemeItem(
            theme="AI", strength_score=92.5, news_count=45,
            sentiment_avg=0.7, date="2024-01-15", market="KR",
        )
        assert item.theme == "AI"
        assert item.strength_score == 92.5
