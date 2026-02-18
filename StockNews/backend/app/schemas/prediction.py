"""Prediction response schemas."""

from pydantic import BaseModel, field_validator


class PredictionResponse(BaseModel):
    """예측 점수 응답 스키마."""

    stock_code: str
    prediction_score: float | None = None  # 0-100 scale
    direction: str | None = None  # "up" | "down" | "neutral"
    confidence: float | None = None  # 0.0 ~ 1.0
    based_on_days: int = 30

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v):
        """Validate direction is one of allowed values."""
        if v is not None and v not in ("up", "down", "neutral"):
            raise ValueError("direction must be up, down, or neutral")
        return v
