"""통합 LLM 분석기 테스트."""

from datetime import UTC


class TestAnalyzeNews:
    """analyze_news() 테스트."""

    def test_returns_structured_result(self, monkeypatch):
        """정상 LLM 응답 → 구조화된 결과 반환."""
        llm_response = '{"sentiment": "positive", "score": 0.85, "confidence": 0.9, "themes": ["반도체"], "summary": "삼성전자 실적 호조", "kr_impact": []}'
        monkeypatch.setattr(
            "app.processing.unified_analyzer.call_llm",
            lambda sys, usr, **kw: llm_response,
        )

        from app.processing.unified_analyzer import analyze_news
        result = analyze_news("삼성전자 4분기 실적 사상 최대", market="KR")

        assert result["sentiment"] == "positive"
        assert result["sentiment_score"] == 0.85
        assert result["confidence"] == 0.9
        assert result["themes"] == ["반도체"]
        assert result["summary"] == "삼성전자 실적 호조"
        assert result["kr_impact_themes"] == []

    def test_us_news_returns_kr_impact(self, monkeypatch):
        """US 뉴스 → kr_impact 포함."""
        llm_response = '{"sentiment": "positive", "score": 0.8, "confidence": 0.9, "themes": ["AI", "반도체"], "summary": "NVIDIA AI chip revenue record", "kr_impact": [{"theme": "반도체", "impact": 0.8, "direction": "up"}]}'
        monkeypatch.setattr(
            "app.processing.unified_analyzer.call_llm",
            lambda sys, usr, **kw: llm_response,
        )

        from app.processing.unified_analyzer import analyze_news
        result = analyze_news("NVIDIA reports record AI chip revenue", market="US")

        assert len(result["kr_impact_themes"]) == 1
        assert result["kr_impact_themes"][0]["theme"] == "반도체"
        assert result["kr_impact_themes"][0]["direction"] == "up"

    def test_kr_news_ignores_kr_impact(self, monkeypatch):
        """KR 뉴스 → kr_impact 무시 (빈 배열)."""
        llm_response = '{"sentiment": "positive", "score": 0.5, "confidence": 0.7, "themes": [], "summary": "요약", "kr_impact": [{"theme": "AI", "impact": 0.5, "direction": "up"}]}'
        monkeypatch.setattr(
            "app.processing.unified_analyzer.call_llm",
            lambda sys, usr, **kw: llm_response,
        )

        from app.processing.unified_analyzer import analyze_news
        result = analyze_news("테스트 뉴스", market="KR")

        assert result["kr_impact_themes"] == []

    def test_invalid_sentiment_defaults_to_neutral(self, monkeypatch):
        """잘못된 sentiment → neutral로 보정."""
        llm_response = '{"sentiment": "unknown", "score": 0.5, "confidence": 0.5, "themes": [], "summary": "", "kr_impact": []}'
        monkeypatch.setattr(
            "app.processing.unified_analyzer.call_llm",
            lambda sys, usr, **kw: llm_response,
        )

        from app.processing.unified_analyzer import analyze_news
        result = analyze_news("테스트 뉴스")

        assert result["sentiment"] == "neutral"

    def test_score_clamped_to_range(self, monkeypatch):
        """score가 범위 밖이면 클램프."""
        llm_response = '{"sentiment": "positive", "score": 2.5, "confidence": 1.5, "themes": [], "summary": "", "kr_impact": []}'
        monkeypatch.setattr(
            "app.processing.unified_analyzer.call_llm",
            lambda sys, usr, **kw: llm_response,
        )

        from app.processing.unified_analyzer import analyze_news
        result = analyze_news("테스트")

        assert result["sentiment_score"] == 1.0
        assert result["confidence"] == 1.0

    def test_invalid_theme_filtered(self, monkeypatch):
        """유효하지 않은 테마는 필터링."""
        llm_response = '{"sentiment": "neutral", "score": 0.0, "confidence": 0.5, "themes": ["반도체", "없는테마", "AI"], "summary": "", "kr_impact": []}'
        monkeypatch.setattr(
            "app.processing.unified_analyzer.call_llm",
            lambda sys, usr, **kw: llm_response,
        )

        from app.processing.unified_analyzer import analyze_news
        result = analyze_news("테스트")

        assert result["themes"] == ["반도체", "AI"]

    def test_max_two_themes(self, monkeypatch):
        """테마 최대 2개."""
        llm_response = '{"sentiment": "neutral", "score": 0.0, "confidence": 0.5, "themes": ["AI", "반도체", "로봇"], "summary": "", "kr_impact": []}'
        monkeypatch.setattr(
            "app.processing.unified_analyzer.call_llm",
            lambda sys, usr, **kw: llm_response,
        )

        from app.processing.unified_analyzer import analyze_news
        result = analyze_news("테스트")

        assert len(result["themes"]) == 2

    def test_llm_failure_returns_defaults(self, monkeypatch):
        """LLM 실패 시 기본값 반환."""
        def raise_error(sys, usr, **kw):
            raise RuntimeError("Bedrock error")

        monkeypatch.setattr(
            "app.processing.unified_analyzer.call_llm",
            raise_error,
        )

        from app.processing.unified_analyzer import analyze_news
        result = analyze_news("테스트 뉴스")

        assert result["sentiment"] == "neutral"
        assert result["sentiment_score"] == 0.0
        assert result["themes"] == []
        assert result["summary"] == ""
        assert result["kr_impact_themes"] == []

    def test_summary_truncated_to_200_chars(self, monkeypatch):
        """요약 200자 초과 시 잘라냄."""
        long_summary = "가" * 300
        llm_response = f'{{"sentiment": "neutral", "score": 0.0, "confidence": 0.5, "themes": [], "summary": "{long_summary}", "kr_impact": []}}'
        monkeypatch.setattr(
            "app.processing.unified_analyzer.call_llm",
            lambda sys, usr, **kw: llm_response,
        )

        from app.processing.unified_analyzer import analyze_news
        result = analyze_news("테스트")

        assert len(result["summary"]) == 200

    def test_body_included_in_prompt(self, monkeypatch):
        """본문이 있으면 프롬프트에 포함."""
        captured_messages = []

        def capture_llm(sys, usr, **kw):
            captured_messages.append(usr)
            return '{"sentiment": "neutral", "score": 0.0, "confidence": 0.5, "themes": [], "summary": "", "kr_impact": []}'

        monkeypatch.setattr(
            "app.processing.unified_analyzer.call_llm",
            capture_llm,
        )

        from app.processing.unified_analyzer import analyze_news
        analyze_news("제목", body="본문 내용입니다")

        assert "본문: 본문 내용입니다" in captured_messages[0]


class TestGetNewsFrequency:
    """_get_news_frequency() 테스트."""

    def test_returns_count_from_db(self, db_session):
        """DB에 뉴스가 있으면 건수 반환."""
        from datetime import datetime

        from app.collectors.pipeline import _get_news_frequency
        from app.models.news_event import NewsEvent

        # 뉴스 2건 추가
        for i in range(2):
            event = NewsEvent(
                market="KR",
                stock_code="005930",
                title=f"테스트 뉴스 {i}",
                source="test",
                published_at=datetime.now(UTC),
            )
            db_session.add(event)
        db_session.commit()

        count = _get_news_frequency(db_session, "005930")
        assert count == 2

    def test_empty_stock_code_returns_one(self, db_session):
        """빈 종목코드 → 1 반환."""
        from app.collectors.pipeline import _get_news_frequency
        assert _get_news_frequency(db_session, "") == 1

    def test_no_news_returns_one(self, db_session):
        """뉴스 없는 종목 → 1 반환."""
        from app.collectors.pipeline import _get_news_frequency
        assert _get_news_frequency(db_session, "999999") == 1
