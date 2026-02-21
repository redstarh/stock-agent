"""StockNews_Advan SQLAlchemy 모델.

이벤트 기반 구조화 예측 시스템의 핵심 데이터 모델.
기존 simulation 모델과 독립적으로 운영됨.
"""

from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AdvanEvent(Base):
    """정규화된 이벤트 레코드.

    뉴스/DART 원문에서 추출한 구조화 이벤트.
    """

    __tablename__ = "advan_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_news_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NewsEvent.id 참조
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    stock_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False, index=True)  # KR / US

    # 이벤트 분류
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # 실적/가이던스/수주/증자/소송/규제/경영권/자사주/배당/M&A/리콜/기타
    direction: Mapped[str] = mapped_column(String(20), nullable=False)  # positive/negative/mixed/unknown
    magnitude: Mapped[float] = mapped_column(Float, default=0.0)  # 정규화된 규모 (0~1)
    magnitude_detail: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: 세부 규모 피처

    # 메타
    novelty: Mapped[float] = mapped_column(Float, default=0.5)  # 새로움 (0~1)
    credibility: Mapped[float] = mapped_column(Float, default=0.5)  # 신뢰도 (0~1, DART=0.9, 루머=0.2)
    is_disclosure: Mapped[bool] = mapped_column(Boolean, default=False)  # DART 공시 여부

    # 원본 정보
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)

    # 컨파운더 (동시 발생 시장 이슈)
    confounders: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array

    # 시간
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_after_market: Mapped[bool] = mapped_column(Boolean, default=False)  # 장마감 후 발표 여부
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("idx_advan_event_ticker_ts", "ticker", "event_timestamp"),
        Index("idx_advan_event_type_dir", "event_type", "direction"),
        Index("idx_advan_event_market_ts", "market", "event_timestamp"),
    )

    def __repr__(self) -> str:
        return f"<AdvanEvent(id={self.id}, ticker={self.ticker}, type={self.event_type}, dir={self.direction})>"


class AdvanFeatureDaily(Base):
    """일별 시장 피처.

    종목별 가격/수익률/변동성/거래량 등 일별 피처 저장.
    """

    __tablename__ = "advan_feature_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    market: Mapped[str] = mapped_column(String(5), nullable=False)

    # 수익률
    ret_1d: Mapped[float | None] = mapped_column(Float, nullable=True)
    ret_3d: Mapped[float | None] = mapped_column(Float, nullable=True)
    ret_5d: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 변동성/거래량
    volatility_20d: Mapped[float | None] = mapped_column(Float, nullable=True)
    dollar_volume: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 시장 대비
    beta: Mapped[float | None] = mapped_column(Float, nullable=True)
    sector_ret: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_ret: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 가격
    close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("idx_advan_feature_ticker_date", "ticker", "trade_date", unique=True),
        Index("idx_advan_feature_market_date", "market", "trade_date"),
    )

    def __repr__(self) -> str:
        return f"<AdvanFeatureDaily(ticker={self.ticker}, date={self.trade_date})>"


class AdvanPolicy(Base):
    """예측 정책 (버전 관리).

    이벤트 priors, 결정 임계값, 템플릿, retrieval 설정을 포함.
    """

    __tablename__ = "advan_policy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)  # 현재 활성 정책

    # 정책 파라미터 (JSON)
    event_priors: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON: {"실적": 0.8, "수주": 0.6, "증자": 0.5, ...}

    thresholds: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON: {"buy_p": 0.62, "sell_p": 0.62, "abstain_low": 0.4, "abstain_high": 0.6,
    #         "label_threshold_pct": 2.0, "stop_loss_pct": 5.0}

    template_config: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON: {"include_features": true, "include_similar_events": true,
    #         "max_similar": 3, "similarity_threshold": 0.5}

    retrieval_config: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON: {"max_results": 3, "lookback_days": 365, "same_sector_only": false}

    # 성과 추적
    latest_brier: Mapped[float | None] = mapped_column(Float, nullable=True)
    latest_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    latest_calibration: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("idx_advan_policy_active", "is_active"),
        Index("idx_advan_policy_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<AdvanPolicy(id={self.id}, name={self.name}, v={self.version}, active={self.is_active})>"


class AdvanPrediction(Base):
    """개별 예측 레코드.

    이벤트 기반 LLM 예측 결과.
    """

    __tablename__ = "advan_prediction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # AdvanSimulationRun.id
    event_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # AdvanEvent.id
    policy_id: Mapped[int] = mapped_column(Integer, nullable=False)  # AdvanPolicy.id

    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False)
    horizon: Mapped[int] = mapped_column(Integer, nullable=False, default=3)  # T+N 거래일

    # 확률 예측
    prediction: Mapped[str] = mapped_column(String(10), nullable=False)  # Up/Down/Flat/Abstain
    p_up: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    p_down: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    p_flat: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # 액션
    trade_action: Mapped[str] = mapped_column(String(10), nullable=False, default="skip")  # buy/sell/hold/skip
    position_size: Mapped[float] = mapped_column(Float, default=0.0)  # 0~1

    # 근거
    top_drivers: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    invalidators: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("idx_advan_pred_run_date", "run_id", "prediction_date"),
        Index("idx_advan_pred_ticker_date", "ticker", "prediction_date"),
        Index("idx_advan_pred_policy", "policy_id"),
    )

    def __repr__(self) -> str:
        return f"<AdvanPrediction(run={self.run_id}, ticker={self.ticker}, pred={self.prediction})>"


class AdvanLabel(Base):
    """실현 수익률 라벨.

    예측 후 실제 주가 변동 결과.
    """

    __tablename__ = "advan_label"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # AdvanPrediction.id
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False)
    horizon: Mapped[int] = mapped_column(Integer, nullable=False)

    # 실현 결과
    realized_ret: Mapped[float | None] = mapped_column(Float, nullable=True)  # 실현 수익률 (%)
    excess_ret: Mapped[float | None] = mapped_column(Float, nullable=True)  # 초과수익률 (시장 제거)
    label: Mapped[str | None] = mapped_column(String(10), nullable=True)  # Up/Down/Flat (임계값 기반)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    label_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # 실제 라벨 산출일
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("idx_advan_label_pred", "prediction_id", unique=True),
        Index("idx_advan_label_ticker_date", "ticker", "prediction_date"),
    )

    def __repr__(self) -> str:
        return f"<AdvanLabel(pred={self.prediction_id}, label={self.label}, correct={self.is_correct})>"


class AdvanSimulationRun(Base):
    """Advan 시뮬레이션 실행 기록."""

    __tablename__ = "advan_simulation_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    policy_id: Mapped[int] = mapped_column(Integer, nullable=False)  # AdvanPolicy.id
    market: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    horizon: Mapped[int] = mapped_column(Integer, nullable=False, default=3)  # T+N
    label_threshold_pct: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)

    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending/running/completed/failed

    # 집계 결과
    total_predictions: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    abstain_count: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # 고급 메트릭
    brier_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    calibration_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    auc_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    f1_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_excess_return: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 이벤트 유형별 성과 (JSON)
    by_event_type_metrics: Mapped[str | None] = mapped_column(Text, nullable=True)

    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_advan_run_market_status", "market", "status"),
        Index("idx_advan_run_policy", "policy_id"),
    )

    def __repr__(self) -> str:
        return f"<AdvanSimulationRun(id={self.id}, name={self.name}, status={self.status})>"


class AdvanEvalRun(Base):
    """정책 평가 실행 기록."""

    __tablename__ = "advan_eval_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    policy_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    simulation_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # AdvanSimulationRun.id

    # 평가 기간
    eval_period_from: Mapped[date] = mapped_column(Date, nullable=False)
    eval_period_to: Mapped[date] = mapped_column(Date, nullable=False)
    split_type: Mapped[str] = mapped_column(String(20), nullable=False, default="test")
    # train/val/test

    # 메트릭
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    f1: Mapped[float] = mapped_column(Float, default=0.0)
    brier: Mapped[float] = mapped_column(Float, default=0.0)
    calibration_error: Mapped[float] = mapped_column(Float, default=0.0)
    auc: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_excess_return: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 상세 분석 (JSON)
    by_event_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    by_direction: Mapped[str | None] = mapped_column(Text, nullable=True)
    robustness_metrics: Mapped[str | None] = mapped_column(Text, nullable=True)

    total_predictions: Mapped[int] = mapped_column(Integer, default=0)
    abstain_rate: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("idx_advan_eval_policy_period", "policy_id", "eval_period_from"),
    )

    def __repr__(self) -> str:
        return f"<AdvanEvalRun(policy={self.policy_id}, brier={self.brier}, acc={self.accuracy})>"
