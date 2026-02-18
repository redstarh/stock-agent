"""RED: NewsItem and NewsScoreResponse schema 테스트."""

import pytest
from datetime import datetime, timezone


class TestNewsItemSchema:
    def test_news_item_includes_summary(self):
        """NewsItem에 summary 필드 포함."""
        from app.schemas.news import NewsItem

        data = {
            "id": 1,
            "title": "삼성전자 실적 발표",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "sentiment": "positive",
            "news_score": 85.0,
            "source": "naver",
            "source_url": "https://example.com",
            "market": "KR",
            "theme": "AI",
            "published_at": "2024-01-15T09:00:00Z",
            "summary": "삼성전자가 4분기 사상 최대 실적을 기록했다.",
        }

        item = NewsItem(**data)
        assert item.summary == "삼성전자가 4분기 사상 최대 실적을 기록했다."

    def test_news_item_summary_nullable(self):
        """summary는 None 허용."""
        from app.schemas.news import NewsItem

        data = {
            "id": 1,
            "title": "뉴스",
            "stock_code": "005930",
            "sentiment": "neutral",
            "news_score": 50.0,
            "source": "naver",
            "market": "KR",
            "summary": None,
        }

        item = NewsItem(**data)
        assert item.summary is None

    def test_news_item_summary_optional(self):
        """summary 필드 생략 가능."""
        from app.schemas.news import NewsItem

        data = {
            "id": 1,
            "title": "뉴스",
            "stock_code": "005930",
            "sentiment": "neutral",
            "news_score": 50.0,
            "source": "naver",
            "market": "KR",
        }

        item = NewsItem(**data)
        assert hasattr(item, "summary")


class TestNewsScoreResponseSchema:
    def test_news_score_includes_top_themes(self):
        """NewsScoreResponse에 top_themes 필드 포함."""
        from app.schemas.news import NewsScoreResponse

        data = {
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "news_score": 85.0,
            "recency": 80.0,
            "frequency": 10.0,
            "sentiment_score": 0.7,
            "disclosure": 2.0,
            "news_count": 15,
            "top_themes": ["AI", "반도체", "실적"],
        }

        response = NewsScoreResponse(**data)
        assert response.top_themes == ["AI", "반도체", "실적"]

    def test_news_score_top_themes_default_empty(self):
        """top_themes 기본값은 빈 리스트."""
        from app.schemas.news import NewsScoreResponse

        data = {
            "stock_code": "005930",
            "news_score": 85.0,
        }

        response = NewsScoreResponse(**data)
        assert response.top_themes == []

    def test_news_score_includes_updated_at(self):
        """NewsScoreResponse에 updated_at 필드 포함."""
        from app.schemas.news import NewsScoreResponse

        now = datetime.now(timezone.utc)
        data = {
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "news_score": 85.0,
            "updated_at": now,
        }

        response = NewsScoreResponse(**data)
        assert response.updated_at == now

    def test_news_score_updated_at_nullable(self):
        """updated_at은 None 허용."""
        from app.schemas.news import NewsScoreResponse

        data = {
            "stock_code": "005930",
            "news_score": 85.0,
            "updated_at": None,
        }

        response = NewsScoreResponse(**data)
        assert response.updated_at is None
