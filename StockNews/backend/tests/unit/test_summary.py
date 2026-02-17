"""RED: 뉴스 요약 기능 단위 테스트."""

import pytest


class TestNewsSummary:
    def test_summary_returns_string(self, mock_openai_summary):
        """요약 결과가 문자열."""
        from app.processing.summary import summarize_news

        result = summarize_news("삼성전자 4분기 실적 사상 최대")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_summary_max_length(self, mock_openai_summary):
        """요약 200자 이하."""
        from app.processing.summary import summarize_news

        result = summarize_news("삼성전자 4분기 실적 사상 최대치 경신, 매출 80조원 돌파")
        assert len(result) <= 200

    def test_summary_with_body(self, mock_openai_summary):
        """본문 포함 시에도 정상 동작."""
        from app.processing.summary import summarize_news

        result = summarize_news(
            "삼성전자 실적 발표",
            body="삼성전자가 4분기 매출 80조원을 기록하며 사상 최대 실적을 달성했다.",
        )
        assert isinstance(result, str)

    def test_summary_api_failure_returns_empty(self, monkeypatch):
        """LLM 실패 시 빈 문자열."""
        from app.processing.summary import summarize_news

        def _raise(*args, **kwargs):
            raise ConnectionError("API unavailable")

        monkeypatch.setattr("app.processing.summary._call_llm_summary", _raise)
        result = summarize_news("테스트 뉴스")
        assert result == ""

    def test_summary_title_only(self, mock_openai_summary):
        """제목만으로도 요약 가능."""
        from app.processing.summary import summarize_news

        result = summarize_news("SK하이닉스 HBM3E 양산 개시")
        assert isinstance(result, str)
        assert len(result) > 0
