"""학습 데이터 API 스키마."""

from datetime import date

from pydantic import BaseModel


class TrainingDataItem(BaseModel):
    """개별 학습 데이터 레코드."""

    prediction_date: date
    stock_code: str
    stock_name: str | None
    market: str

    # 뉴스 피처
    news_score: float
    sentiment_score: float
    news_count: int
    news_count_3d: int
    avg_score_3d: float
    disclosure_ratio: float
    sentiment_trend: float
    theme: str | None

    # 주가 피처
    prev_close: float | None
    prev_change_pct: float | None
    prev_volume: int | None
    price_change_5d: float | None
    volume_change_5d: float | None
    ma5_ratio: float | None
    ma20_ratio: float | None
    volatility_5d: float | None
    rsi_14: float | None
    bb_position: float | None

    # 시장 피처
    market_index_change: float | None
    day_of_week: int

    # 예측
    predicted_direction: str
    predicted_score: float
    confidence: float

    # 실제 결과
    actual_close: float | None
    actual_change_pct: float | None
    actual_direction: str | None
    actual_volume: int | None
    is_correct: bool | None


class TrainingDataResponse(BaseModel):
    """학습 데이터 목록 응답."""

    market: str
    start_date: date
    end_date: date
    total: int
    data: list[TrainingDataItem]


class TrainingStatsMarket(BaseModel):
    """시장별 통계."""

    market: str
    total_records: int
    labeled_records: int
    accuracy: float | None
    date_range_start: date | None
    date_range_end: date | None


class TrainingStatsResponse(BaseModel):
    """학습 데이터 통계 응답."""

    total_records: int
    labeled_records: int
    markets: list[TrainingStatsMarket]
