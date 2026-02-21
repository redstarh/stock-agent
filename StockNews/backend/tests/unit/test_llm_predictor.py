"""LLM Predictor 단위 테스트."""

import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.models.news_event import NewsEvent
from app.processing.llm_predictor import (
    _build_system_prompt,
    _build_user_message,
    _parse_llm_response,
    predict_with_llm,
)


MOCK_HEURISTIC = {
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "direction": "up",
    "score": 72.5,
    "confidence": 0.7,
    "news_count": 10,
}

MOCK_CONTEXT = {
    "version": "20240101_120000",
    "generated_at": "2024-01-01T12:00:00+00:00",
    "analysis_days": 30,
    "total_predictions": 100,
    "overall_accuracy": 62.0,
    "direction_accuracy": [
        {"direction": "up", "total": 50, "correct": 35, "accuracy": 70.0, "avg_actual_change_pct": 1.5},
        {"direction": "down", "total": 30, "correct": 15, "accuracy": 50.0, "avg_actual_change_pct": -1.2},
    ],
    "theme_predictability": [
        {"theme": "반도체", "accuracy": 72.0, "total": 20, "predictability": "high"},
    ],
    "sentiment_ranges": [
        {"range_label": "0.5~1.0", "total": 30, "up_count": 20, "down_count": 8, "neutral_count": 2, "up_ratio": 0.67, "down_ratio": 0.27},
    ],
    "news_count_effect": [
        {"range_label": "6-15", "total": 60, "accuracy": 70.0},
    ],
    "confidence_calibration": [],
    "score_ranges": [],
    "failure_patterns": [
        {"pattern": "high_score_down", "count": 5, "description": "높은 점수(>=70)에도 하락한 경우 5건"},
    ],
    "market_conditions": [],
}


@pytest.fixture
def sample_news(db_session):
    """테스트용 뉴스 이벤트."""
    now = datetime.now()  # naive datetime to match llm_predictor's cutoff logic
    events = []
    for i in range(5):
        event = NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title=f"삼성전자 관련 뉴스 {i+1}",
            sentiment="positive",
            sentiment_score=0.6 + i * 0.05,
            news_score=70.0 + i * 2,
            source="naver",
            source_url=f"https://example.com/news/{i+1000}",
            theme="반도체",
            is_disclosure=i == 0,
            created_at=now,
        )
        db_session.add(event)
        events.append(event)
    db_session.flush()
    return events


class TestBuildSystemPrompt:
    """시스템 프롬프트 생성 테스트."""

    def test_prompt_contains_context(self):
        """프롬프트에 컨텍스트 정보 포함."""
        prompt = _build_system_prompt(MOCK_CONTEXT)
        assert "62.0%" in prompt
        assert "100건" in prompt
        assert "반도체" in prompt
        assert "높은 점수" in prompt
        assert "30일" in prompt

    def test_prompt_with_empty_context(self):
        """빈 컨텍스트로 프롬프트 생성."""
        empty = {
            "analysis_days": 30,
            "overall_accuracy": 0,
            "total_predictions": 0,
            "theme_predictability": [],
            "sentiment_ranges": [],
            "news_count_effect": [],
            "failure_patterns": [],
        }
        prompt = _build_system_prompt(empty)
        assert "0%" in prompt
        assert "데이터 없음" in prompt


class TestBuildUserMessage:
    """유저 메시지 생성 테스트."""

    def test_message_with_news(self, db_session, sample_news):
        """뉴스가 있을 때 메시지 생성."""
        msg = _build_user_message(db_session, "005930", "KR", MOCK_HEURISTIC)
        assert "005930" in msg
        assert "삼성전자" in msg
        assert "반도체" in msg
        assert "Heuristic" in msg
        assert "up" in msg

    def test_message_without_news(self, db_session):
        """뉴스가 없을 때 메시지."""
        msg = _build_user_message(db_session, "999999", "KR", MOCK_HEURISTIC)
        assert "뉴스가 없습니다" in msg


class TestParseLLMResponse:
    """LLM 응답 파싱 테스트."""

    def test_valid_json(self):
        """유효한 JSON 응답 파싱."""
        text = json.dumps({
            "direction": "up",
            "score": 75.5,
            "confidence": 0.82,
            "reasoning": "반도체 테마 긍정적",
        })
        result = _parse_llm_response(text)
        assert result["direction"] == "up"
        assert result["score"] == 75.5
        assert result["confidence"] == 0.82
        assert "반도체" in result["reasoning"]

    def test_score_clamping(self):
        """점수 범위 클램핑."""
        text = json.dumps({"direction": "up", "score": 150, "confidence": 2.0})
        result = _parse_llm_response(text)
        assert result["score"] == 100.0
        assert result["confidence"] == 1.0

    def test_invalid_direction_defaults_neutral(self):
        """잘못된 방향은 neutral로 기본값."""
        text = json.dumps({"direction": "sideways", "score": 50, "confidence": 0.5})
        result = _parse_llm_response(text)
        assert result["direction"] == "neutral"

    def test_json_in_markdown(self):
        """마크다운 코드 블록 안의 JSON 파싱."""
        text = 'Some explanation here\n{"direction": "down", "score": 30, "confidence": 0.6, "reasoning": "하락 예상"}\nmore text'
        result = _parse_llm_response(text)
        assert result["direction"] == "down"

    def test_unparseable_raises(self):
        """파싱 불가능한 응답은 예외."""
        with pytest.raises(ValueError, match="Cannot parse"):
            _parse_llm_response("This is not JSON at all")


class TestPredictWithLLM:
    """predict_with_llm 통합 테스트."""

    @patch("app.processing.llm_predictor.calculate_prediction_for_stock")
    @patch("app.processing.llm_predictor._load_context")
    @patch("app.processing.llm_predictor.call_llm")
    def test_successful_llm_prediction(
        self, mock_llm, mock_ctx, mock_heuristic, db_session, sample_news
    ):
        """LLM 예측 성공."""
        mock_heuristic.return_value = MOCK_HEURISTIC
        mock_ctx.return_value = MOCK_CONTEXT
        mock_llm.return_value = json.dumps({
            "direction": "up",
            "score": 78.0,
            "confidence": 0.85,
            "reasoning": "반도체 테마 강세 지속",
        })

        result = predict_with_llm(db_session, "005930", "KR")
        assert result.method == "llm"
        assert result.direction == "up"
        assert result.prediction_score == 78.0
        assert result.confidence == 0.85
        assert result.heuristic_direction == "up"
        assert result.context_version == "20240101_120000"

    @patch("app.processing.llm_predictor.calculate_prediction_for_stock")
    @patch("app.processing.llm_predictor._load_context")
    def test_no_context_fallback(self, mock_ctx, mock_heuristic, db_session):
        """컨텍스트 없을 때 Heuristic fallback."""
        mock_heuristic.return_value = MOCK_HEURISTIC
        mock_ctx.return_value = None

        result = predict_with_llm(db_session, "005930", "KR")
        assert result.method == "heuristic_fallback"
        assert result.direction == "up"
        assert result.prediction_score == 72.5
        assert "컨텍스트 파일 없음" in result.reasoning

    @patch("app.processing.llm_predictor.calculate_prediction_for_stock")
    @patch("app.processing.llm_predictor._load_context")
    @patch("app.processing.llm_predictor.call_llm")
    def test_llm_failure_fallback(
        self, mock_llm, mock_ctx, mock_heuristic, db_session, sample_news
    ):
        """LLM 호출 실패 시 Heuristic fallback."""
        mock_heuristic.return_value = MOCK_HEURISTIC
        mock_ctx.return_value = MOCK_CONTEXT
        mock_llm.side_effect = RuntimeError("Bedrock error")

        result = predict_with_llm(db_session, "005930", "KR")
        assert result.method == "heuristic_fallback"
        assert result.direction == "up"
        assert "LLM 호출 실패" in result.reasoning
