"""StockPrice SQLAlchemy 모델."""

from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StockPrice(Base):
    """주가 데이터 테이블."""

    __tablename__ = "stock_price"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)
    change_pct: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )  # daily % change
    volume: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    __table_args__ = (Index("ix_stock_price_code_date", "stock_code", "date", unique=True),)

    def __repr__(self) -> str:
        return f"<StockPrice(stock_code={self.stock_code}, date={self.date}, change_pct={self.change_pct:.2f}%)>"
