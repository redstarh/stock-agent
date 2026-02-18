"""Unit tests for prediction schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.prediction import PredictionResponse


class TestPredictionSchema:
    def test_prediction_response_fields(self):
        """PredictionResponse에 필수 필드 존재."""
        data = {
            "stock_code": "005930",
            "prediction_score": 75.5,
            "direction": "up",
            "confidence": 0.85,
            "based_on_days": 30,
        }
        response = PredictionResponse(**data)

        assert response.stock_code == "005930"
        assert response.prediction_score == 75.5
        assert response.direction == "up"
        assert response.confidence == 0.85
        assert response.based_on_days == 30

    def test_null_prediction(self):
        """예측 데이터 없는 경우 None 필드."""
        response = PredictionResponse(stock_code="000000")

        assert response.stock_code == "000000"
        assert response.prediction_score is None
        assert response.direction is None
        assert response.confidence is None
        assert response.based_on_days == 30  # default value

    def test_invalid_direction_raises(self):
        """잘못된 direction 값 → ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PredictionResponse(
                stock_code="005930",
                prediction_score=50.0,
                direction="invalid",
                confidence=0.5,
            )

        assert "direction must be up, down, or neutral" in str(exc_info.value)

    def test_prediction_score_type(self):
        """prediction_score가 float 타입."""
        response = PredictionResponse(
            stock_code="005930",
            prediction_score=75.5,
            direction="up",
            confidence=0.8,
        )

        assert isinstance(response.prediction_score, float)

        # Integer input should be accepted and converted to float
        response2 = PredictionResponse(
            stock_code="005930",
            prediction_score=75,
            direction="up",
            confidence=0.8,
        )

        assert isinstance(response2.prediction_score, (int, float))
