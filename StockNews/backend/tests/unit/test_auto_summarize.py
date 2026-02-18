"""RED: 자동 요약 처리 테스트."""

import pytest
from datetime import datetime, timezone


class TestAutoSummarize:
    def test_auto_summarize_event_with_content(self, db_session, monkeypatch):
        """콘텐츠가 있는 이벤트는 자동 요약 생성."""
        # Mock call_llm before importing
        def mock_call_llm(system_prompt: str, user_message: str) -> str:
            return '{"summary": "삼성전자가 4분기 사상 최대 실적을 기록했다."}'

        monkeypatch.setattr("app.processing.summary.call_llm", mock_call_llm)

        from app.models.news_event import NewsEvent
        from app.processing.summary import auto_summarize_event

        event = NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title="삼성전자 4분기 실적 사상 최대",
            content="삼성전자가 4분기 매출 80조원을 기록하며 사상 최대 실적을 달성했다.",
            sentiment="positive",
            sentiment_score=0.8,
            news_score=85.0,
            source="naver",
            published_at=datetime.now(timezone.utc),
        )

        summary = auto_summarize_event(event)
        assert summary is not None
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_auto_summarize_event_no_content(self, db_session):
        """콘텐츠가 없으면 None 반환."""
        from app.models.news_event import NewsEvent
        from app.processing.summary import auto_summarize_event

        event = NewsEvent(
            market="KR",
            stock_code="005930",
            title="삼성전자 뉴스",
            content=None,
            sentiment="neutral",
            sentiment_score=0.0,
            news_score=50.0,
            source="naver",
            published_at=datetime.now(timezone.utc),
        )

        summary = auto_summarize_event(event)
        assert summary is None

    def test_auto_summarize_event_empty_content(self, db_session):
        """빈 콘텐츠는 None 반환."""
        from app.models.news_event import NewsEvent
        from app.processing.summary import auto_summarize_event

        event = NewsEvent(
            market="KR",
            stock_code="005930",
            title="삼성전자 뉴스",
            content="",
            sentiment="neutral",
            sentiment_score=0.0,
            news_score=50.0,
            source="naver",
            published_at=datetime.now(timezone.utc),
        )

        summary = auto_summarize_event(event)
        assert summary is None

    def test_auto_summarize_event_updates_event(self, db_session, monkeypatch):
        """auto_summarize_event가 event.summary를 업데이트."""
        # Mock call_llm before importing
        def mock_call_llm(system_prompt: str, user_message: str) -> str:
            return '{"summary": "삼성전자가 4분기 사상 최대 실적을 기록했다."}'

        monkeypatch.setattr("app.processing.summary.call_llm", mock_call_llm)

        from app.models.news_event import NewsEvent
        from app.processing.summary import auto_summarize_event

        event = NewsEvent(
            market="KR",
            stock_code="005930",
            title="삼성전자 4분기 실적 사상 최대",
            content="삼성전자가 4분기 매출 80조원을 기록하며 사상 최대 실적을 달성했다.",
            sentiment="positive",
            sentiment_score=0.8,
            news_score=85.0,
            source="naver",
            published_at=datetime.now(timezone.utc),
        )
        db_session.add(event)
        db_session.commit()

        summary = auto_summarize_event(event)
        assert event.summary == summary
        assert event.summary is not None

    def test_auto_summarize_on_api_failure(self, db_session, monkeypatch):
        """LLM 실패 시 빈 문자열 반환하고 event.summary는 빈 문자열."""
        from app.models.news_event import NewsEvent
        from app.processing.summary import auto_summarize_event

        def _raise(*args, **kwargs):
            raise ConnectionError("API unavailable")

        monkeypatch.setattr("app.processing.summary.summarize_news", _raise)

        event = NewsEvent(
            market="KR",
            stock_code="005930",
            title="삼성전자 뉴스",
            content="테스트 콘텐츠",
            sentiment="neutral",
            sentiment_score=0.0,
            news_score=50.0,
            source="naver",
            published_at=datetime.now(timezone.utc),
        )
        db_session.add(event)
        db_session.commit()

        summary = auto_summarize_event(event)
        assert summary == ""
        assert event.summary == ""
