"""StockNews_Advan Pydantic 스키마.

이벤트 기반 구조화 예측 시스템의 요청/응답 스키마.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


# ─── 이벤트 타입 상수 ───

EVENT_TYPES = [
    "실적", "가이던스", "수주", "증자", "소송", "규제",
    "경영권", "자사주", "배당", "M&A", "리콜", "공급계약",
    "인수합병", "분할", "상장폐지", "기타",
]

DIRECTIONS = ["positive", "negative", "mixed", "unknown"]
PREDICTIONS = ["Up", "Down", "Flat", "Abstain"]
TRADE_ACTIONS = ["buy", "sell", "hold", "skip"]


# ─── Event 스키마 ───

class AdvanEventResponse(BaseModel):
    """이벤트 응답."""
    id: int
    source_news_id: int | None
    ticker: str
    stock_name: str | None
    market: str
    event_type: str
    direction: str
    magnitude: float
    magnitude_detail: str | None
    novelty: float
    credibility: float
    is_disclosure: bool
    title: str
    summary: str | None
    source: str
    confounders: str | None
    event_timestamp: datetime
    is_after_market: bool
    created_at: datetime


class AdvanEventListResponse(BaseModel):
    """이벤트 목록 응답."""
    events: list[AdvanEventResponse]
    total: int


class EventExtractRequest(BaseModel):
    """이벤트 추출 요청."""
    market: str = Field(default="KR", description="KR or US")
    date_from: date | None = None
    date_to: date | None = None
    force_rebuild: bool = False


class EventExtractResponse(BaseModel):
    """이벤트 추출 결과."""
    extracted_count: int
    skipped_count: int
    error_count: int
    message: str


# ─── Policy 스키마 ───

class EventPriors(BaseModel):
    """이벤트 유형별 가중치."""
    실적: float = 0.8
    가이던스: float = 0.7
    수주: float = 0.6
    증자: float = 0.5
    소송: float = 0.5
    규제: float = 0.6
    경영권: float = 0.7
    자사주: float = 0.5
    배당: float = 0.4
    공급계약: float = 0.6
    기타: float = 0.3


class PolicyThresholds(BaseModel):
    """결정 임계값."""
    buy_p: float = Field(default=0.62, ge=0.5, le=1.0, description="매수 확률 임계값")
    sell_p: float = Field(default=0.62, ge=0.5, le=1.0, description="매도 확률 임계값")
    abstain_low: float = Field(default=0.4, ge=0.0, le=1.0, description="유보 하한")
    abstain_high: float = Field(default=0.6, ge=0.0, le=1.0, description="유보 상한")
    label_threshold_pct: float = Field(default=2.0, ge=0.5, le=10.0, description="라벨 임계값 (%)")
    stop_loss_pct: float = Field(default=5.0, ge=1.0, le=20.0, description="손절 기준 (%)")


class TemplateConfig(BaseModel):
    """LLM 입력 템플릿 설정."""
    include_features: bool = True
    include_similar_events: bool = True
    include_confounders: bool = True
    max_events_per_stock: int = Field(default=5, ge=1, le=20)
    use_v2_heuristic: bool = False


class RetrievalConfig(BaseModel):
    """유사 이벤트 검색 설정."""
    max_results: int = Field(default=3, ge=1, le=10)
    lookback_days: int = Field(default=365, ge=30, le=1095)
    same_sector_only: bool = False
    similarity_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class AdvanPolicyCreate(BaseModel):
    """정책 생성 요청."""
    name: str = Field(max_length=200)
    version: str = Field(max_length=50, default="v1.0")
    description: str | None = None
    event_priors: EventPriors = Field(default_factory=EventPriors)
    thresholds: PolicyThresholds = Field(default_factory=PolicyThresholds)
    template_config: TemplateConfig = Field(default_factory=TemplateConfig)
    retrieval_config: RetrievalConfig = Field(default_factory=RetrievalConfig)


class AdvanPolicyUpdate(BaseModel):
    """정책 수정 요청."""
    name: str | None = Field(None, max_length=200)
    version: str | None = Field(None, max_length=50)
    description: str | None = None
    is_active: bool | None = None
    event_priors: EventPriors | None = None
    thresholds: PolicyThresholds | None = None
    template_config: TemplateConfig | None = None
    retrieval_config: RetrievalConfig | None = None


class AdvanPolicyResponse(BaseModel):
    """정책 상세 응답."""
    id: int
    name: str
    version: str
    description: str | None
    is_active: bool
    event_priors: EventPriors
    thresholds: PolicyThresholds
    template_config: TemplateConfig
    retrieval_config: RetrievalConfig
    latest_brier: float | None
    latest_accuracy: float | None
    latest_calibration: float | None
    created_at: datetime
    updated_at: datetime


class AdvanPolicyListItem(BaseModel):
    """정책 목록 아이템."""
    id: int
    name: str
    version: str
    description: str | None
    is_active: bool
    latest_brier: float | None
    latest_accuracy: float | None
    latest_calibration: float | None
    created_at: datetime


# ─── Prediction 스키마 ───

class PredictionDriver(BaseModel):
    """예측 근거."""
    feature: str
    sign: str  # + / -
    weight: float
    evidence: str


class AdvanPredictionResponse(BaseModel):
    """개별 예측 응답."""
    id: int
    run_id: int
    event_id: int | None
    policy_id: int
    ticker: str
    prediction_date: date
    horizon: int
    prediction: str  # Up/Down/Flat/Abstain
    p_up: float
    p_down: float
    p_flat: float
    trade_action: str
    position_size: float
    top_drivers: list[PredictionDriver] | None = None
    invalidators: list[str] | None = None
    reasoning: str | None


# ─── Label 스키마 ───

class AdvanLabelResponse(BaseModel):
    """라벨 응답."""
    id: int
    prediction_id: int
    ticker: str
    prediction_date: date
    horizon: int
    realized_ret: float | None
    excess_ret: float | None
    label: str | None
    is_correct: bool | None
    label_date: date | None


# ─── Simulation Run 스키마 ───

class AdvanSimulationRunCreate(BaseModel):
    """시뮬레이션 실행 생성 요청."""
    name: str = Field(max_length=200)
    policy_id: int
    market: str = Field(default="KR", description="KR or US")
    horizon: int = Field(default=3, ge=1, le=20, description="예측 horizon (T+N 거래일)")
    label_threshold_pct: float = Field(default=2.0, ge=0.5, le=10.0, description="라벨 임계값 (%)")
    date_from: date
    date_to: date


class AdvanSimulationRunResponse(BaseModel):
    """시뮬레이션 실행 응답."""
    id: int
    name: str
    policy_id: int
    market: str
    horizon: int
    label_threshold_pct: float
    date_from: date
    date_to: date
    status: str
    total_predictions: int
    correct_count: int
    abstain_count: int
    accuracy_rate: float
    brier_score: float | None
    calibration_error: float | None
    auc_score: float | None
    f1_score: float | None
    avg_excess_return: float | None
    by_event_type_metrics: dict | None = None
    duration_seconds: float
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class AdvanSimulationRunDetail(BaseModel):
    """시뮬레이션 실행 상세 (결과 포함)."""
    run: AdvanSimulationRunResponse
    predictions: list[AdvanPredictionResponse]
    labels: list[AdvanLabelResponse]
    direction_stats: dict[str, dict]


# ─── Compare 스키마 ───

class AdvanCompareItem(BaseModel):
    """비교 대상 실행 정보."""
    id: int
    name: str
    policy_id: int
    policy_name: str | None = None
    market: str
    horizon: int
    date_from: date
    date_to: date
    total_predictions: int
    correct_count: int
    abstain_count: int
    accuracy_rate: float
    brier_score: float | None
    calibration_error: float | None
    auc_score: float | None
    f1_score: float | None
    avg_excess_return: float | None
    by_event_type_metrics: dict | None = None


class AdvanCompareResponse(BaseModel):
    """다중 실행 비교 응답."""
    runs: list[AdvanCompareItem]


# ─── Eval 스키마 ───

class AdvanEvalMetrics(BaseModel):
    """평가 메트릭."""
    accuracy: float
    f1: float
    brier: float
    calibration_error: float
    auc: float | None
    avg_excess_return: float | None
    total_predictions: int
    abstain_rate: float
    by_event_type: dict | None = None
    by_direction: dict | None = None
    robustness_metrics: dict | None = None


class AdvanEvalRunResponse(BaseModel):
    """평가 실행 응답."""
    id: int
    policy_id: int
    simulation_run_id: int | None
    eval_period_from: date
    eval_period_to: date
    split_type: str
    metrics: AdvanEvalMetrics
    created_at: datetime


# ─── Optimizer 스키마 ───

class OptimizeRequest(BaseModel):
    """최적화 실행 요청."""
    base_policy_id: int
    market: str = Field(default="KR")
    date_from: date
    date_to: date
    num_candidates: int = Field(default=5, ge=2, le=20, description="후보 정책 수")
    val_split_ratio: float = Field(default=0.2, ge=0.1, le=0.5, description="검증 비율")
    target_metric: str = Field(default="brier", description="최적화 대상: brier/accuracy/calibration")


class OptimizeResponse(BaseModel):
    """최적화 결과 응답."""
    best_policy_id: int
    best_policy_name: str
    candidates_evaluated: int
    best_metrics: AdvanEvalMetrics
    improvement_pct: float  # 기존 대비 개선율 (%)
    message: str
