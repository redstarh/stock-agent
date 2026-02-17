"""RED: 종목/테마별 집계 로직 단위 테스트."""

import pytest
from datetime import datetime, timezone


class TestAggregator:
    def test_aggregate_by_stock(self, db_session):
        """종목별 집계 결과 확인."""
        from app.scoring.aggregator import aggregate_by_stock
        from app.models.news_event import NewsEvent

        # 삼성전자 뉴스 2건
        db_session.add_all([
            NewsEvent(
                market="KR", stock_code="005930", stock_name="삼성전자",
                title="삼성 뉴스 1", source="naver", news_score=80.0,
                sentiment="positive", sentiment_score=0.8,
                published_at=datetime.now(timezone.utc),
            ),
            NewsEvent(
                market="KR", stock_code="005930", stock_name="삼성전자",
                title="삼성 뉴스 2", source="naver", news_score=60.0,
                sentiment="neutral", sentiment_score=0.0,
                published_at=datetime.now(timezone.utc),
            ),
        ])
        db_session.flush()

        result = aggregate_by_stock(db_session, market="KR")
        assert len(result) >= 1
        samsung = [r for r in result if r["stock_code"] == "005930"]
        assert len(samsung) == 1
        assert samsung[0]["news_count"] == 2

    def test_theme_strength_calculation(self, db_session):
        """테마 강도 점수 계산."""
        from app.scoring.aggregator import aggregate_by_theme
        from app.models.news_event import NewsEvent

        db_session.add_all([
            NewsEvent(
                market="KR", stock_code="005930", title="AI 반도체",
                source="naver", news_score=90.0, theme="AI",
                sentiment="positive", sentiment_score=0.9,
                published_at=datetime.now(timezone.utc),
            ),
            NewsEvent(
                market="KR", stock_code="000660", title="AI 메모리",
                source="naver", news_score=85.0, theme="AI",
                sentiment="positive", sentiment_score=0.7,
                published_at=datetime.now(timezone.utc),
            ),
        ])
        db_session.flush()

        result = aggregate_by_theme(db_session, market="KR")
        ai_themes = [r for r in result if r["theme"] == "AI"]
        assert len(ai_themes) == 1
        assert ai_themes[0]["news_count"] == 2
        assert ai_themes[0]["strength_score"] > 0

    def test_sentiment_avg_calculation(self, db_session):
        """sentiment_avg = 종목별 감성 점수 평균값 (-1.0 ~ 1.0)."""
        from app.scoring.aggregator import aggregate_by_stock
        from app.models.news_event import NewsEvent

        db_session.add_all([
            NewsEvent(
                market="KR", stock_code="035420", stock_name="NAVER",
                title="네이버 호실적", source="naver", news_score=70.0,
                sentiment="positive", sentiment_score=0.6,
                published_at=datetime.now(timezone.utc),
            ),
            NewsEvent(
                market="KR", stock_code="035420", stock_name="NAVER",
                title="네이버 비용 증가", source="naver", news_score=40.0,
                sentiment="negative", sentiment_score=-0.4,
                published_at=datetime.now(timezone.utc),
            ),
        ])
        db_session.flush()

        result = aggregate_by_stock(db_session, market="KR")
        naver = [r for r in result if r["stock_code"] == "035420"]
        assert len(naver) == 1
        assert -1.0 <= naver[0]["sentiment_avg"] <= 1.0

    def test_empty_db_returns_empty(self, db_session):
        """DB 비어있으면 빈 리스트."""
        from app.scoring.aggregator import aggregate_by_stock

        result = aggregate_by_stock(db_session, market="KR")
        assert result == []
