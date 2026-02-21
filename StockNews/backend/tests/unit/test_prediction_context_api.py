"""Prediction Context API 엔드포인트 테스트."""

import json
import os
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.verification import DailyPredictionResult


@pytest.fixture
def client(db_session, monkeypatch):
    """Test client with overridden DB dependency."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_context_file(tmp_path):
    """임시 예측 컨텍스트 파일 생성."""
    context = {
        "version": "20240101_120000",
        "generated_at": "2024-01-01T12:00:00+00:00",
        "analysis_days": 30,
        "total_predictions": 50,
        "overall_accuracy": 62.0,
        "direction_accuracy": [
            {"direction": "up", "total": 30, "correct": 20, "accuracy": 66.7, "avg_actual_change_pct": 1.5},
        ],
        "theme_predictability": [
            {"theme": "반도체", "accuracy": 70.0, "total": 15, "predictability": "high"},
        ],
        "sentiment_ranges": [
            {"range_label": "0.5~1.0", "total": 20, "up_count": 14, "down_count": 5, "neutral_count": 1, "up_ratio": 0.7, "down_ratio": 0.25},
        ],
        "news_count_effect": [
            {"range_label": "6-15", "total": 30, "accuracy": 70.0},
        ],
        "confidence_calibration": [
            {"range_label": "0.6-1.0", "total": 25, "accuracy": 72.0},
        ],
        "score_ranges": [
            {"range_label": "50-70", "total": 20, "up_count": 12, "down_count": 6, "neutral_count": 2},
        ],
        "failure_patterns": [
            {"pattern": "high_score_down", "count": 3, "description": "높은 점수에도 하락 3건"},
        ],
        "market_conditions": [
            {"market": "KR", "accuracy": 65.0, "total": 35, "best_theme": "반도체", "worst_theme": "바이오"},
            {"market": "US", "accuracy": 58.0, "total": 15, "best_theme": "AI", "worst_theme": None},
        ],
    }
    filepath = tmp_path / "prediction_context.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False)
    return str(filepath)


class TestGetPredictionContext:
    """GET /prediction-context 테스트."""

    def test_get_context_success(self, client, sample_context_file):
        """컨텍스트 조회 성공."""
        with patch(
            "app.api.prediction_context.DEFAULT_CONTEXT_PATH",
            sample_context_file,
        ):
            resp = client.get("/api/v1/prediction-context")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "20240101_120000"
        assert data["total_predictions"] == 50
        assert data["overall_accuracy"] == 62.0

    def test_get_context_not_found(self, client):
        """컨텍스트 파일 없을 때 404."""
        with patch(
            "app.api.prediction_context.DEFAULT_CONTEXT_PATH",
            "/nonexistent/path.json",
        ):
            resp = client.get("/api/v1/prediction-context")
        assert resp.status_code == 404

    def test_get_context_market_filter(self, client, sample_context_file):
        """시장 필터 적용."""
        with patch(
            "app.api.prediction_context.DEFAULT_CONTEXT_PATH",
            sample_context_file,
        ):
            resp = client.get("/api/v1/prediction-context?market=KR")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["market_conditions"]) == 1
        assert data["market_conditions"][0]["market"] == "KR"


class TestRebuildPredictionContext:
    """POST /prediction-context/rebuild 테스트."""

    def test_rebuild_success(self, client, db_session, tmp_path):
        """리빌드 성공."""
        output_path = str(tmp_path / "ctx.json")
        with patch(
            "app.api.prediction_context.DEFAULT_CONTEXT_PATH",
            output_path,
        ):
            resp = client.post("/api/v1/prediction-context/rebuild?days=30")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["analysis_days"] == 30


class TestLLMPrediction:
    """GET /stocks/{code}/prediction/llm 테스트."""

    @patch("app.api.prediction_context.predict_with_llm")
    def test_llm_prediction(self, mock_predict, client):
        """LLM 예측 엔드포인트."""
        from app.schemas.prediction_context import LLMPredictionResponse

        mock_predict.return_value = LLMPredictionResponse(
            stock_code="005930",
            stock_name="삼성전자",
            method="llm",
            direction="up",
            prediction_score=78.0,
            confidence=0.85,
            reasoning="반도체 테마 강세",
            heuristic_direction="up",
            heuristic_score=72.5,
            context_version="20240101_120000",
            based_on_days=30,
        )
        resp = client.get("/api/v1/stocks/005930/prediction/llm?market=KR")
        assert resp.status_code == 200
        data = resp.json()
        assert data["method"] == "llm"
        assert data["direction"] == "up"
        assert data["prediction_score"] == 78.0
