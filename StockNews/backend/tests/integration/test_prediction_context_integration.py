"""예측 컨텍스트 통합 테스트 — 전체 플로우 검증."""

import json
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest

from app.models.news_event import NewsEvent
from app.models.training import StockTrainingData
from app.models.verification import DailyPredictionResult, ThemePredictionAccuracy
from app.processing.prediction_context_builder import build_and_save_prediction_context
from app.processing.llm_predictor import predict_with_llm


@pytest.fixture
def seed_verification_data(db_session):
    """검증 데이터 시딩 — 뉴스 + 예측 결과 + 테마 + 학습 데이터."""
    today = date.today()
    now = datetime.now(timezone.utc)

    # NewsEvent 시딩
    for i in range(5):
        db_session.add(NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title=f"삼성전자 뉴스 {i+1}",
            sentiment="positive",
            sentiment_score=0.6 + i * 0.05,
            news_score=70.0 + i * 2,
            source="naver",
            source_url=f"https://example.com/integration/{i+2000}",
            theme="반도체",
            is_disclosure=False,
            created_at=now,
        ))

    # DailyPredictionResult 시딩
    db_session.add(DailyPredictionResult(
        prediction_date=today,
        stock_code="005930",
        stock_name="삼성전자",
        market="KR",
        predicted_direction="up",
        predicted_score=75.0,
        confidence=0.8,
        news_count=10,
        actual_direction="up",
        actual_change_pct=2.0,
        is_correct=True,
        verified_at=now,
    ))

    # ThemePredictionAccuracy 시딩
    db_session.add(ThemePredictionAccuracy(
        prediction_date=today,
        theme="반도체",
        market="KR",
        total_stocks=10,
        correct_count=7,
        accuracy_rate=0.7,
        created_at=now,
    ))

    # StockTrainingData 시딩
    db_session.add(StockTrainingData(
        prediction_date=today,
        stock_code="005930",
        stock_name="삼성전자",
        market="KR",
        sentiment_score=0.7,
        news_count=10,
        theme="반도체",
        predicted_direction="up",
        predicted_score=75.0,
        confidence=0.8,
        actual_direction="up",
        is_correct=True,
        news_score=75.0,
        news_count_3d=25,
        avg_score_3d=73.0,
        disclosure_ratio=0.0,
        sentiment_trend=0.05,
        day_of_week=today.weekday(),
        created_at=now,
    ))

    db_session.flush()
    return db_session


class TestFullFlow:
    """전체 플로우 통합 테스트."""

    def test_build_context_then_predict(self, seed_verification_data, tmp_path):
        """컨텍스트 빌드 → LLM 예측 (mock) → 응답 검증."""
        db = seed_verification_data
        output_path = str(tmp_path / "ctx.json")

        # Step 1: Build and save context
        context = build_and_save_prediction_context(db, days=30, output_path=output_path)
        assert context["total_predictions"] == 1
        assert context["overall_accuracy"] == 100.0

        # Verify file was created
        with open(output_path) as f:
            saved = json.load(f)
        assert saved["version"] == context["version"]

        # Step 2: Use context for LLM prediction (mock LLM call)
        mock_llm_response = json.dumps({
            "direction": "up",
            "score": 80.0,
            "confidence": 0.9,
            "reasoning": "반도체 테마 강세 지속, 과거 정확도 100%",
        })

        with patch("app.processing.llm_predictor.call_llm", return_value=mock_llm_response):
            result = predict_with_llm(db, "005930", "KR", context_path=output_path)

        assert result.method == "llm"
        assert result.direction == "up"
        assert result.prediction_score == 80.0
        assert result.confidence == 0.9
        assert result.heuristic_direction is not None
        assert result.context_version == context["version"]

    def test_fallback_without_context(self, seed_verification_data):
        """컨텍스트 없이 LLM 예측 → Heuristic fallback."""
        db = seed_verification_data
        result = predict_with_llm(db, "005930", "KR", context_path="/nonexistent.json")
        assert result.method == "heuristic_fallback"
        assert result.stock_code == "005930"
        assert result.direction in ("up", "down", "neutral")
