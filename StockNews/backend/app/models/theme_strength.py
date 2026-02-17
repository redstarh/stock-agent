"""ThemeStrength SQLAlchemy 모델."""

from datetime import date

from sqlalchemy import Date, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ThemeStrength(Base):
    """테마 강도 집계 테이블 (일별)."""

    __tablename__ = "theme_strength"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    theme: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    strength_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    news_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sentiment_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    __table_args__ = (
        UniqueConstraint("date", "market", "theme", name="uq_theme_date_market"),
    )

    def __repr__(self) -> str:
        return f"<ThemeStrength(date={self.date}, market={self.market}, theme={self.theme}, score={self.strength_score})>"
