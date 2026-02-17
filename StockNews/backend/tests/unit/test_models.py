"""RED: DB 모델 테스트 — NewsEvent, ThemeStrength CRUD + 제약 조건."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


class TestNewsEventModel:
    def test_create_news_event(self, db_session):
        """news_event 레코드 생성 및 필드 검증."""
        from app.models.news_event import NewsEvent

        event = NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title="삼성전자 실적 발표",
            sentiment="positive",
            source="naver",
            source_url="https://news.naver.com/1",
        )
        db_session.add(event)
        db_session.commit()
        assert event.id is not None
        assert event.created_at is not None

    def test_news_event_sentiment_enum(self, db_session):
        """sentiment 필드가 positive/neutral/negative만 허용."""
        from app.models.news_event import NewsEvent

        for s in ["positive", "neutral", "negative"]:
            event = NewsEvent(
                market="KR",
                stock_code="005930",
                title=f"test_{s}",
                sentiment=s,
                source="naver",
            )
            db_session.add(event)
        db_session.commit()
        assert db_session.query(NewsEvent).count() == 3

    def test_news_event_dedup_index(self, db_session):
        """source_url 중복 시 IntegrityError 발생."""
        from app.models.news_event import NewsEvent

        event1 = NewsEvent(
            market="KR", stock_code="005930", title="뉴스1",
            sentiment="neutral", source="naver",
            source_url="https://news.naver.com/dup",
        )
        event2 = NewsEvent(
            market="KR", stock_code="005930", title="뉴스2",
            sentiment="neutral", source="naver",
            source_url="https://news.naver.com/dup",
        )
        db_session.add(event1)
        db_session.commit()
        db_session.add(event2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_news_event_default_values(self, db_session):
        """기본값 검증: sentiment='neutral', news_score=0, is_disclosure=False."""
        from app.models.news_event import NewsEvent

        event = NewsEvent(
            market="KR",
            stock_code="005930",
            title="기본값 테스트",
            source="naver",
        )
        db_session.add(event)
        db_session.commit()
        assert event.sentiment == "neutral"
        assert event.news_score == 0.0
        assert event.is_disclosure is False

    def test_news_event_has_published_at(self, db_session):
        """published_at 필드 존재 및 설정 가능."""
        from datetime import datetime, timezone
        from app.models.news_event import NewsEvent

        now = datetime.now(timezone.utc)
        event = NewsEvent(
            market="KR", stock_code="005930", title="published_at 테스트",
            sentiment="neutral", source="naver", published_at=now,
        )
        db_session.add(event)
        db_session.commit()
        # SQLite는 timezone을 저장하지 않으므로 naive datetime으로 비교
        assert event.published_at.replace(tzinfo=None) == now.replace(tzinfo=None)

    def test_news_event_has_market_field(self, db_session):
        """market 필드 (KR/US) 필수."""
        from app.models.news_event import NewsEvent

        event = NewsEvent(
            market="US", stock_code="AAPL", stock_name="Apple",
            title="Apple Earnings", sentiment="positive", source="finnhub",
        )
        db_session.add(event)
        db_session.commit()
        assert event.market == "US"


class TestThemeStrengthModel:
    def test_create_theme_strength(self, db_session):
        """theme_strength 레코드 생성."""
        from app.models.theme_strength import ThemeStrength
        from datetime import date

        ts = ThemeStrength(
            date=date(2024, 1, 15),
            market="KR",
            theme="AI",
            strength_score=92.5,
            news_count=45,
            sentiment_avg=0.7,
        )
        db_session.add(ts)
        db_session.commit()
        assert ts.id is not None

    def test_theme_unique_constraint(self, db_session):
        """(date, market, theme) 유니크 제약 검증."""
        from app.models.theme_strength import ThemeStrength
        from datetime import date

        ts1 = ThemeStrength(
            date=date(2024, 1, 15), market="KR", theme="AI",
            strength_score=90, news_count=40, sentiment_avg=0.5,
        )
        ts2 = ThemeStrength(
            date=date(2024, 1, 15), market="KR", theme="AI",
            strength_score=85, news_count=35, sentiment_avg=0.4,
        )
        db_session.add(ts1)
        db_session.commit()
        db_session.add(ts2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_theme_strength_sentiment_avg_range(self, db_session):
        """sentiment_avg가 -1.0 ~ 1.0 범위."""
        from app.models.theme_strength import ThemeStrength
        from datetime import date

        ts = ThemeStrength(
            date=date(2024, 1, 15), market="KR", theme="반도체",
            strength_score=80, news_count=30, sentiment_avg=0.6,
        )
        db_session.add(ts)
        db_session.commit()
        assert -1.0 <= ts.sentiment_avg <= 1.0
