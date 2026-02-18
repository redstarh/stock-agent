"""뉴스 관련 Pydantic 스키마."""

from datetime import datetime

from pydantic import BaseModel


class NewsItem(BaseModel):
    """뉴스 개별 항목 응답."""

    id: int
    title: str
    stock_code: str
    stock_name: str | None = None
    sentiment: str
    sentiment_score: float = 0.0
    news_score: float
    source: str
    source_url: str | None = None
    market: str
    theme: str | None = None
    content: str | None = None
    summary: str | None = None
    published_at: datetime | None = None

    model_config = {"from_attributes": True}


class NewsScoreResponse(BaseModel):
    """종목별 뉴스 스코어 응답."""

    stock_code: str
    stock_name: str | None = None
    news_score: float = 0.0
    recency: float = 0.0
    frequency: float = 0.0
    sentiment_score: float = 0.0
    disclosure: float = 0.0
    news_count: int = 0
    top_themes: list[str] = []
    updated_at: datetime | None = None


class NewsListResponse(BaseModel):
    """뉴스 리스트 페이지네이션 응답."""

    items: list[NewsItem]
    total: int
    offset: int = 0
    limit: int = 20


class NewsTopItem(BaseModel):
    """Top 종목 뉴스 요약."""

    stock_code: str
    stock_name: str | None = None
    news_score: float
    sentiment: str
    news_count: int
    market: str
