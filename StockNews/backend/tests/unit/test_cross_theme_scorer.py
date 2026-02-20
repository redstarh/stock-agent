"""Tests for cross_theme_scorer module."""

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.news_event import NewsEvent
from app.processing.cross_theme_scorer import calc_cross_theme_score, calc_cross_theme_scores_batch


@pytest.fixture
def db():
    """In-memory SQLite session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _insert_news(db, stock_code, theme, score, market="KR", days_ago=0):
    """Helper to insert a news event."""
    target_date = date.today() - timedelta(days=days_ago)
    news = NewsEvent(
        market=market,
        stock_code=stock_code,
        stock_name=f"Stock {stock_code}",
        title=f"News for {stock_code}",
        sentiment="positive",
        sentiment_score=0.5,
        news_score=score,
        source="test",
        theme=theme,
        created_at=datetime.combine(target_date, datetime.min.time()),
    )
    db.add(news)
    db.commit()
    return news


class TestCalcCrossThemeScore:
    def test_basic_cross_theme(self, db):
        """동일 테마 타 종목 평균 계산."""
        target = date.today()
        _insert_news(db, "005930", "반도체", 80.0, days_ago=0)
        _insert_news(db, "000660", "반도체", 60.0, days_ago=0)
        _insert_news(db, "034730", "반도체", 70.0, days_ago=0)

        # Score for 005930: average of 000660(60) + 034730(70) = 65.0
        score = calc_cross_theme_score(db, "반도체", "005930", "KR", target)
        assert score == 65.0

    def test_no_theme_returns_zero(self, db):
        """테마가 None이면 0.0 반환."""
        score = calc_cross_theme_score(db, None, "005930", "KR", date.today())
        assert score == 0.0

    def test_no_other_stocks(self, db):
        """같은 테마 타 종목이 없으면 0.0 반환."""
        target = date.today()
        _insert_news(db, "005930", "반도체", 80.0, days_ago=0)

        score = calc_cross_theme_score(db, "반도체", "005930", "KR", target)
        assert score == 0.0

    def test_market_filter(self, db):
        """시장 필터 적용."""
        target = date.today()
        _insert_news(db, "005930", "반도체", 80.0, market="KR", days_ago=0)
        _insert_news(db, "NVDA", "반도체", 90.0, market="US", days_ago=0)

        # KR market: only sees 005930, no other KR stocks
        score = calc_cross_theme_score(db, "반도체", "005930", "KR", target)
        assert score == 0.0

    def test_lookback_window(self, db):
        """lookback_days 밖의 뉴스는 제외."""
        target = date.today()
        _insert_news(db, "005930", "반도체", 80.0, days_ago=0)
        _insert_news(db, "000660", "반도체", 60.0, days_ago=0)
        _insert_news(db, "034730", "반도체", 90.0, days_ago=10)  # Outside 7-day window

        score = calc_cross_theme_score(db, "반도체", "005930", "KR", target, lookback_days=7)
        assert score == 60.0  # Only 000660 is within window

    def test_excludes_self(self, db):
        """자기 자신 제외 확인."""
        target = date.today()
        _insert_news(db, "005930", "반도체", 80.0, days_ago=0)
        _insert_news(db, "005930", "반도체", 90.0, days_ago=1)  # Same stock, different day
        _insert_news(db, "000660", "반도체", 50.0, days_ago=0)

        score = calc_cross_theme_score(db, "반도체", "005930", "KR", target)
        assert score == 50.0  # Only 000660


class TestCalcCrossThemeScoresBatch:
    def test_batch_calculation(self, db):
        """일괄 계산."""
        target = date.today()
        _insert_news(db, "005930", "반도체", 80.0, days_ago=0)
        _insert_news(db, "000660", "반도체", 60.0, days_ago=0)

        scores = calc_cross_theme_scores_batch(db, "KR", target)
        assert "005930" in scores
        assert "000660" in scores
        assert scores["005930"] == 60.0  # 000660's score
        assert scores["000660"] == 80.0  # 005930's score

    def test_empty_market(self, db):
        """빈 시장."""
        scores = calc_cross_theme_scores_batch(db, "KR", date.today())
        assert scores == {}
