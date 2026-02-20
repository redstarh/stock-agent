"""학습 데이터 스냅샷 SQLAlchemy 모델."""

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StockTrainingData(Base):
    """예측 시점의 모든 피처를 스냅샷으로 저장. ML 학습 데이터로 활용."""

    __tablename__ = "stock_training_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    stock_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False, index=True)

    # === 뉴스 피처 (예측 시점 스냅샷) ===
    news_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    news_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    news_count_3d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_score_3d: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    disclosure_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sentiment_trend: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    theme: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # === 주가 피처 (예측 시점 스냅샷) ===
    prev_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    prev_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    prev_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_change_5d: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_change_5d: Mapped[float | None] = mapped_column(Float, nullable=True)
    ma5_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    ma20_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    volatility_5d: Mapped[float | None] = mapped_column(Float, nullable=True)
    rsi_14: Mapped[float | None] = mapped_column(Float, nullable=True)
    bb_position: Mapped[float | None] = mapped_column(Float, nullable=True)

    # === 시장 피처 ===
    market_index_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    vix_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    # === Tier 2 시장/공시 피처 ===
    usd_krw_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    has_earnings_disclosure: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    cross_theme_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # === 예측 결과 ===
    predicted_direction: Mapped[str] = mapped_column(String(10), nullable=False)
    predicted_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # === 실제 결과 (라벨) — 검증 후 업데이트 ===
    actual_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_direction: Mapped[str | None] = mapped_column(String(10), nullable=True)
    actual_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_training_date_stock", "prediction_date", "stock_code", unique=True),
        Index("idx_training_market_date", "market", "prediction_date"),
        Index("idx_training_labels", "market", "prediction_date", "actual_direction"),
    )

    def __repr__(self) -> str:
        return f"<StockTrainingData(date={self.prediction_date}, stock={self.stock_code}, direction={self.predicted_direction})>"
