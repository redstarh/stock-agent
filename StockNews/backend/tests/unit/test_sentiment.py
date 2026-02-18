"""RED: 감성 분석 로직 단위 테스트."""

import pytest


class TestSentimentAnalyzer:
    def test_positive_sentiment(self, mock_openai):
        """긍정 뉴스 → 'positive'."""
        from app.processing.sentiment import analyze_sentiment

        result = analyze_sentiment("삼성전자 실적 사상 최대치 경신")
        assert result["sentiment"] == "positive"

    def test_sentiment_score_range(self, mock_openai):
        """감성 점수가 -1.0 ~ 1.0 범위."""
        from app.processing.sentiment import analyze_sentiment

        result = analyze_sentiment("삼성전자 실적 발표")
        assert -1.0 <= result["score"] <= 1.0

    def test_api_failure_fallback(self, monkeypatch):
        """OpenAI API 실패 시 neutral 기본값."""
        from app.processing.sentiment import analyze_sentiment

        # OpenAI 호출 실패 mock
        def _raise(*args, **kwargs):
            raise ConnectionError("API unavailable")

        monkeypatch.setattr(
            "app.processing.sentiment._call_llm",
            _raise,
        )

        result = analyze_sentiment("테스트 뉴스")
        assert result["sentiment"] == "neutral"
        assert result["score"] == 0.0

    def test_returns_dict_format(self, mock_openai):
        """반환값에 sentiment, score 키 존재."""
        from app.processing.sentiment import analyze_sentiment

        result = analyze_sentiment("테스트")
        assert "sentiment" in result
        assert "score" in result

    def test_sentiment_with_body(self, mock_openai):
        """본문 포함 시 감성 분석 정상 동작."""
        from app.processing.sentiment import analyze_sentiment

        result = analyze_sentiment(
            "삼성전자 실적 발표",
            body="삼성전자가 4분기 매출 80조원을 기록하며 사상 최대 실적을 달성했다."
        )
        assert result["sentiment"] in ("positive", "neutral", "negative")
        assert -1.0 <= result["score"] <= 1.0
        assert "confidence" in result

    def test_sentiment_body_none_backward_compatible(self, mock_openai):
        """body=None 시 기존과 동일하게 동작 (하위 호환)."""
        from app.processing.sentiment import analyze_sentiment

        result = analyze_sentiment("테스트 뉴스")
        assert "sentiment" in result
        assert "score" in result
