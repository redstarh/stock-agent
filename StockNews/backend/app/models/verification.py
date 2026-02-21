"""Prediction Verification SQLAlchemy 모델."""

from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DailyPredictionResult(Base):
    """일별 개별 종목 예측 검증 결과."""

    __tablename__ = "daily_prediction_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    stock_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False, index=True)

    # Prediction data
    predicted_direction: Mapped[str] = mapped_column(String(10), nullable=False)
    predicted_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    news_count: Mapped[int] = mapped_column(Integer, default=0)

    # Actual data
    previous_close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 확장 실제 주가 데이터 (OHLCV)
    actual_open_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_high_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_low_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    previous_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_trading_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_direction: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Verification result
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_prediction_date_stock", "prediction_date", "stock_code"),
        Index("idx_market_date", "market", "prediction_date"),
    )

    def __repr__(self) -> str:
        return f"<DailyPredictionResult(date={self.prediction_date}, stock={self.stock_code}, correct={self.is_correct})>"


class ThemePredictionAccuracy(Base):
    """테마별 예측 정확도 집계."""

    __tablename__ = "theme_prediction_accuracy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    theme: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False, index=True)

    # Aggregated metrics
    total_stocks: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Score metrics
    avg_predicted_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_actual_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    rise_index_at_prediction: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (Index("idx_theme_date", "prediction_date", "theme"),)

    def __repr__(self) -> str:
        return f"<ThemePredictionAccuracy(date={self.prediction_date}, theme={self.theme}, accuracy={self.accuracy_rate})>"


class VerificationRunLog(Base):
    """검증 실행 로그."""

    __tablename__ = "verification_run_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Metrics
    stocks_verified: Mapped[int] = mapped_column(Integer, default=0)
    stocks_failed: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # Error tracking
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<VerificationRunLog(date={self.run_date}, market={self.market}, status={self.status})>"
