"""Prediction Context 스키마."""

from datetime import datetime

from pydantic import BaseModel, Field


class DirectionAccuracy(BaseModel):
    """방향별 정확도."""
    direction: str
    total: int
    correct: int
    accuracy: float
    avg_actual_change_pct: float | None = None


class ThemePredictability(BaseModel):
    """테마별 예측 가능성."""
    theme: str
    accuracy: float
    total: int
    predictability: str  # "high" | "medium" | "low"


class SentimentRangeBucket(BaseModel):
    """감성 점수 범위별 실제 방향 분포."""
    range_label: str  # e.g. "-1.0~-0.5"
    total: int
    up_count: int
    down_count: int
    neutral_count: int
    up_ratio: float
    down_ratio: float


class NewsCountEffect(BaseModel):
    """뉴스 건수 효과."""
    range_label: str  # e.g. "1-5", "6-15", "16+"
    total: int
    accuracy: float


class ConfidenceCalibration(BaseModel):
    """Confidence 보정."""
    range_label: str  # e.g. "0.0-0.3", "0.3-0.6", "0.6-1.0"
    total: int
    accuracy: float


class ScoreRangeBucket(BaseModel):
    """예측 점수 구간별 실제 방향 분포."""
    range_label: str  # e.g. "0-30", "30-50", "50-70", "70-100"
    total: int
    up_count: int
    down_count: int
    neutral_count: int


class FailurePattern(BaseModel):
    """실패 패턴."""
    pattern: str
    count: int
    description: str


class MarketCondition(BaseModel):
    """시장별 조건."""
    market: str
    accuracy: float
    total: int
    best_theme: str | None = None
    worst_theme: str | None = None


class PredictionContextResponse(BaseModel):
    """전체 예측 컨텍스트 문서."""
    version: str
    generated_at: datetime
    analysis_days: int
    total_predictions: int
    overall_accuracy: float
    direction_accuracy: list[DirectionAccuracy]
    theme_predictability: list[ThemePredictability]
    sentiment_ranges: list[SentimentRangeBucket]
    news_count_effect: list[NewsCountEffect]
    confidence_calibration: list[ConfidenceCalibration]
    score_ranges: list[ScoreRangeBucket]
    failure_patterns: list[FailurePattern]
    market_conditions: list[MarketCondition]


class LLMPredictionResponse(BaseModel):
    """LLM 예측 응답."""
    stock_code: str
    stock_name: str | None = None
    method: str = Field(description="'llm' or 'heuristic_fallback'")
    direction: str = Field(description="'up', 'down', or 'neutral'")
    prediction_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    reasoning: str = Field(default="", description="한국어 예측 근거")
    heuristic_direction: str | None = None
    heuristic_score: float | None = None
    context_version: str | None = None
    based_on_days: int | None = None


class ContextRebuildResponse(BaseModel):
    """컨텍스트 리빌드 결과."""
    success: bool
    version: str
    analysis_days: int
    total_predictions: int
    overall_accuracy: float
    file_path: str
    generated_at: datetime
