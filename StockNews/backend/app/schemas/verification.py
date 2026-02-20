"""Verification response schemas."""

from datetime import date

from pydantic import BaseModel


# Daily verification response schemas
class DailyResultItem(BaseModel):
    """개별 종목의 일별 검증 결과."""

    stock_code: str
    stock_name: str | None
    predicted_direction: str
    predicted_score: float
    confidence: float
    actual_direction: str | None
    actual_change_pct: float | None
    is_correct: bool | None
    news_count: int = 0
    error_message: str | None


class DailyVerificationResponse(BaseModel):
    """일별 검증 결과 응답."""

    date: date
    market: str
    total: int
    correct: int
    accuracy: float
    results: list[DailyResultItem]


# Accuracy summary response schemas
class DirectionDetail(BaseModel):
    """방향별 상세 통계."""

    total: int
    correct: int
    accuracy: float


class DirectionStats(BaseModel):
    """방향별 정확도 통계."""

    up: DirectionDetail
    down: DirectionDetail
    neutral: DirectionDetail


class DailyTrend(BaseModel):
    """일별 정확도 추이."""

    date: date
    accuracy: float
    total: int


class AccuracyResponse(BaseModel):
    """전체 정확도 요약 응답."""

    period_days: int
    market: str
    overall_accuracy: float | None
    total_predictions: int
    correct_predictions: int
    by_direction: DirectionStats
    daily_trend: list[DailyTrend]


# Theme accuracy response schemas
class ThemeAccuracyItem(BaseModel):
    """개별 테마의 정확도 정보."""

    theme: str
    market: str
    total_stocks: int
    correct_count: int
    accuracy_rate: float
    avg_predicted_score: float
    avg_actual_change_pct: float | None
    rise_index: float | None = None


class ThemeAccuracyResponse(BaseModel):
    """테마별 정확도 응답."""

    market: str
    date: date
    themes: list[ThemeAccuracyItem]


# Theme trend response schemas
class ThemeTrendPoint(BaseModel):
    """테마 정확도 추이 데이터 포인트."""

    date: date
    accuracy_rate: float
    total_stocks: int


class ThemeTrendResponse(BaseModel):
    """특정 테마의 정확도 추이 응답."""

    theme: str
    market: str
    start_date: date
    end_date: date
    trend: list[ThemeTrendPoint]


# Stock history response schemas
class StockHistoryPoint(BaseModel):
    """개별 종목의 예측 이력."""

    date: date
    predicted_direction: str
    predicted_score: float
    actual_direction: str | None
    actual_change_pct: float | None
    is_correct: bool | None


class StockHistoryResponse(BaseModel):
    """특정 종목의 예측 이력 응답."""

    stock_code: str
    stock_name: str | None
    market: str
    start_date: date
    end_date: date
    total_predictions: int
    correct_predictions: int
    accuracy_rate: float
    history: list[StockHistoryPoint]


# Verification run response schemas
class VerificationRunResponse(BaseModel):
    """검증 실행 로그 응답."""

    run_date: date
    market: str
    status: str
    stocks_verified: int
    stocks_failed: int
    duration_seconds: float
    error_details: str | None


# Verification status response schemas
class MarketStatus(BaseModel):
    """시장별 검증 상태."""

    market: str
    last_run_date: date | None
    status: str | None
    stocks_verified: int


class VerificationStatusResponse(BaseModel):
    """전체 검증 상태 응답."""

    current_date: date
    markets: list[MarketStatus]
    total_stocks_verified_today: int
