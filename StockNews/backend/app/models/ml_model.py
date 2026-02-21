"""ML Model Registry SQLAlchemy 모델."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MLModel(Base):
    """ML 모델 메타데이터 저장. 모델 버전 관리 및 활성화."""

    __tablename__ = "ml_model"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "lightgbm" or "random_forest"
    market: Mapped[str] = mapped_column(String(5), nullable=False)
    feature_tier: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, or 3
    feature_list: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array

    train_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    test_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    cv_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    cv_std: Mapped[float | None] = mapped_column(Float, nullable=True)

    train_samples: Mapped[int | None] = mapped_column(Integer, nullable=True)
    test_samples: Mapped[int | None] = mapped_column(Integer, nullable=True)
    train_start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    train_end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    model_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256

    hyperparameters: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    feature_importances: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        Index("ix_ml_model_active", "is_active", "market"),
        Index("ix_ml_model_name_version", "model_name", "model_version", "market", unique=True),
    )

    def __repr__(self) -> str:
        return f"<MLModel(name={self.model_name}, version={self.model_version}, market={self.market}, active={self.is_active})>"
