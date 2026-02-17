"""NewsEvent SQLAlchemy 모델."""

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Float, Index, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SentimentEnum(str, PyEnum):
    """감성 분석 결과 Enum."""

    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class NewsEvent(Base):
    """뉴스 이벤트 테이블."""

    __tablename__ = "news_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    stock_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    sentiment: Mapped[str] = mapped_column(
        String(10), nullable=False, default=SentimentEnum.neutral.value
    )
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    news_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True, unique=True)
    theme: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_disclosure: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_news_event_market_stock", "market", "stock_code"),
        Index("ix_news_event_published", "published_at"),
    )

    def __repr__(self) -> str:
        return f"<NewsEvent(id={self.id}, market={self.market}, stock={self.stock_code}, title={self.title[:30]})>"
