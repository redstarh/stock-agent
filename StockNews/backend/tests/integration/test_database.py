"""RED: DB 연결 + CRUD 통합 테스트."""

import pytest
from sqlalchemy import inspect


class TestDatabaseConnection:
    def test_create_tables(self, db_engine):
        """모든 테이블 생성 확인."""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        assert "news_event" in tables
        assert "theme_strength" in tables

    def test_crud_news_event(self, db_session):
        """news_event CRUD 동작."""
        from app.models.news_event import NewsEvent

        # Create
        event = NewsEvent(
            market="KR", stock_code="005930", stock_name="삼성전자",
            title="CRUD 테스트", sentiment="positive", source="naver",
        )
        db_session.add(event)
        db_session.commit()
        event_id = event.id

        # Read
        found = db_session.get(NewsEvent, event_id)
        assert found is not None
        assert found.title == "CRUD 테스트"

        # Update
        found.news_score = 85.0
        db_session.commit()
        updated = db_session.get(NewsEvent, event_id)
        assert updated.news_score == 85.0

        # Delete
        db_session.delete(updated)
        db_session.commit()
        deleted = db_session.get(NewsEvent, event_id)
        assert deleted is None

    def test_crud_theme_strength(self, db_session):
        """theme_strength CRUD 동작."""
        from app.models.theme_strength import ThemeStrength
        from datetime import date

        # Create
        ts = ThemeStrength(
            date=date(2024, 1, 15), market="KR", theme="AI",
            strength_score=90, news_count=40, sentiment_avg=0.6,
        )
        db_session.add(ts)
        db_session.commit()
        ts_id = ts.id

        # Read
        found = db_session.get(ThemeStrength, ts_id)
        assert found is not None
        assert found.theme == "AI"

        # Update
        found.strength_score = 95.0
        db_session.commit()
        updated = db_session.get(ThemeStrength, ts_id)
        assert updated.strength_score == 95.0

        # Delete
        db_session.delete(updated)
        db_session.commit()
        deleted = db_session.get(ThemeStrength, ts_id)
        assert deleted is None
