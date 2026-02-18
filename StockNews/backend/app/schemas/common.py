"""공통 스키마 — SentimentEnum, TimelinePoint, HealthResponse."""

from enum import Enum

from pydantic import BaseModel


class SentimentEnum(str, Enum):
    """감성 분석 결과."""

    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class TimelinePoint(BaseModel):
    """스코어 타임라인 데이터 포인트."""

    date: str
    score: float


class HealthResponse(BaseModel):
    """서버 상태 응답."""

    status: str
    version: str | None = None
    services: dict[str, str] | None = None


class ErrorResponse(BaseModel):
    """표준 에러 응답."""

    detail: str
    status_code: int = 500
