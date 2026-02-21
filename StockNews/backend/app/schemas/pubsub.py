"""Redis Pub/Sub 메시지 스키마."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class MessageType(StrEnum):
    """메시지 타입."""
    BREAKING_NEWS = "breaking_news"
    SCORE_UPDATE = "score_update"


class Market(StrEnum):
    """시장 구분."""
    KR = "KR"
    US = "US"


class BreakingNewsMessage(BaseModel):
    """속보 메시지 스키마.

    Redis Pub/Sub로 발행되는 속보 메시지의 표준 형식.
    StockAgent consumer와의 계약 (contract).
    """
    schema_version: int = Field(default=1, description="스키마 버전")
    type: MessageType = MessageType.BREAKING_NEWS
    stock_code: str = Field(..., description="종목 코드")
    stock_name: str | None = Field(default=None, description="종목명")
    title: str = Field(..., description="뉴스 제목")
    theme: str | None = Field(default=None, description="테마 분류")
    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0, description="감성 점수")
    news_score: float = Field(..., ge=0.0, le=100.0, description="뉴스 점수")
    market: Market = Field(..., description="시장 구분")
    published_at: str | None = Field(default=None, description="발행 시각 ISO format")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="메시지 생성 시각")

    model_config = {"extra": "ignore"}


class ScoreUpdateMessage(BaseModel):
    """점수 업데이트 메시지 스키마."""
    schema_version: int = Field(default=1, description="스키마 버전")
    type: MessageType = MessageType.SCORE_UPDATE
    stock_code: str = Field(..., description="종목 코드")
    news_score: float = Field(..., ge=0.0, le=100.0, description="뉴스 점수")
    market: Market = Field(..., description="시장 구분")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="메시지 생성 시각")

    model_config = {"extra": "ignore"}


def validate_message(raw_data: dict) -> BreakingNewsMessage | ScoreUpdateMessage | None:
    """수신된 메시지를 타입에 따라 검증.

    Args:
        raw_data: JSON 파싱된 메시지 딕셔너리

    Returns:
        검증된 메시지 모델 또는 None (알 수 없는 타입)
    """
    msg_type = raw_data.get("type")
    if msg_type == MessageType.BREAKING_NEWS:
        return BreakingNewsMessage.model_validate(raw_data)
    elif msg_type == MessageType.SCORE_UPDATE:
        return ScoreUpdateMessage.model_validate(raw_data)
    return None
