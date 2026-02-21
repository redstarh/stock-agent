"""StockNews_Advan API 엔드포인트.

이벤트 추출, 정책 관리, 시뮬레이션, 평가, 최적화 API.
기존 /api/v1/simulation 과 독립적으로 /api/v1/advan 에서 운영.
"""

import json
import logging
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.advan.models import (
    AdvanEvalRun,
    AdvanEvent,
    AdvanLabel,
    AdvanPolicy,
    AdvanPrediction,
    AdvanSimulationRun,
)
from app.advan.schemas import (
    AdvanCompareItem,
    AdvanCompareResponse,
    AdvanEventListResponse,
    AdvanEventResponse,
    AdvanEvalRunResponse,
    AdvanLabelResponse,
    AdvanPolicyCreate,
    AdvanPolicyListItem,
    AdvanPolicyResponse,
    AdvanPolicyUpdate,
    AdvanPredictionResponse,
    AdvanSimulationRunCreate,
    AdvanSimulationRunDetail,
    AdvanSimulationRunResponse,
    EventExtractRequest,
    EventExtractResponse,
    EventPriors,
    OptimizeRequest,
    OptimizeResponse,
    PolicyThresholds,
    RetrievalConfig,
    TemplateConfig,
)
from app.core.database import get_db
from app.models.news_event import NewsEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advan", tags=["advan"])


# ─── Event 엔드포인트 ───

@router.get("/events", response_model=AdvanEventListResponse)
def list_events(
    market: str = Query(default="KR"),
    event_type: str | None = Query(default=None),
    ticker: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """이벤트 목록 조회."""
    query = db.query(AdvanEvent).filter(AdvanEvent.market == market)

    if event_type:
        query = query.filter(AdvanEvent.event_type == event_type)
    if ticker:
        query = query.filter(AdvanEvent.ticker == ticker)

    total = query.count()
    events = query.order_by(AdvanEvent.event_timestamp.desc()).offset(offset).limit(limit).all()

    return AdvanEventListResponse(
        events=[_event_to_response(e) for e in events],
        total=total,
    )


@router.get("/events/summary")
def event_type_summary(
    market: str = Query(default="KR"),
    db: Session = Depends(get_db),
):
    """이벤트 타입별 요약 통계."""
    results = (
        db.query(
            AdvanEvent.event_type,
            func.count(AdvanEvent.id).label("count"),
            func.avg(AdvanEvent.magnitude).label("avg_magnitude"),
            func.avg(AdvanEvent.credibility).label("avg_credibility"),
            func.avg(AdvanEvent.novelty).label("avg_novelty"),
        )
        .filter(AdvanEvent.market == market)
        .group_by(AdvanEvent.event_type)
        .order_by(func.count(AdvanEvent.id).desc())
        .all()
    )

    total_events = sum(r.count for r in results)
    return [
        {
            "event_type": r.event_type,
            "count": r.count,
            "ratio": round(r.count / total_events * 100, 1) if total_events > 0 else 0,
            "avg_magnitude": round(float(r.avg_magnitude or 0), 4),
            "avg_credibility": round(float(r.avg_credibility or 0), 4),
            "avg_novelty": round(float(r.avg_novelty or 0), 4),
        }
        for r in results
    ]


@router.post("/events/extract", response_model=EventExtractResponse)
def extract_events(
    request: EventExtractRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """뉴스에서 이벤트 추출."""
    from app.advan.event_extractor import extract_events as do_extract

    result = do_extract(
        db=db,
        market=request.market,
        date_from=request.date_from,
        date_to=request.date_to,
        force_rebuild=request.force_rebuild,
    )

    return EventExtractResponse(
        extracted_count=result.get("extracted_count", 0),
        skipped_count=result.get("skipped_count", 0),
        error_count=result.get("error_count", 0),
        message=f"이벤트 추출 완료: {result.get('extracted_count', 0)}건 생성",
    )


# ─── Policy 엔드포인트 ───

@router.get("/policies", response_model=list[AdvanPolicyListItem])
def list_policies(db: Session = Depends(get_db)):
    """정책 목록 조회."""
    policies = db.query(AdvanPolicy).order_by(AdvanPolicy.created_at.desc()).all()
    return [
        AdvanPolicyListItem(
            id=p.id,
            name=p.name,
            version=p.version,
            description=p.description,
            is_active=p.is_active,
            latest_brier=p.latest_brier,
            latest_accuracy=p.latest_accuracy,
            latest_calibration=p.latest_calibration,
            created_at=p.created_at,
        )
        for p in policies
    ]


@router.post("/policies", response_model=AdvanPolicyResponse)
def create_policy(request: AdvanPolicyCreate, db: Session = Depends(get_db)):
    """정책 생성."""
    policy = AdvanPolicy(
        name=request.name,
        version=request.version,
        description=request.description,
        is_active=False,
        event_priors=request.event_priors.model_dump_json(),
        thresholds=request.thresholds.model_dump_json(),
        template_config=request.template_config.model_dump_json(),
        retrieval_config=request.retrieval_config.model_dump_json(),
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return _policy_to_response(policy)


@router.get("/policies/{policy_id}", response_model=AdvanPolicyResponse)
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    """정책 상세 조회."""
    policy = db.query(AdvanPolicy).filter(AdvanPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return _policy_to_response(policy)


@router.put("/policies/{policy_id}", response_model=AdvanPolicyResponse)
def update_policy(policy_id: int, request: AdvanPolicyUpdate, db: Session = Depends(get_db)):
    """정책 수정."""
    policy = db.query(AdvanPolicy).filter(AdvanPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    if request.name is not None:
        policy.name = request.name
    if request.version is not None:
        policy.version = request.version
    if request.description is not None:
        policy.description = request.description
    if request.is_active is not None:
        if request.is_active:
            # 다른 정책 비활성화
            db.query(AdvanPolicy).filter(AdvanPolicy.id != policy_id).update({"is_active": False})
        policy.is_active = request.is_active
    if request.event_priors is not None:
        policy.event_priors = request.event_priors.model_dump_json()
    if request.thresholds is not None:
        policy.thresholds = request.thresholds.model_dump_json()
    if request.template_config is not None:
        policy.template_config = request.template_config.model_dump_json()
    if request.retrieval_config is not None:
        policy.retrieval_config = request.retrieval_config.model_dump_json()

    from datetime import UTC, datetime
    policy.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(policy)
    return _policy_to_response(policy)


@router.delete("/policies/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    """정책 삭제."""
    policy = db.query(AdvanPolicy).filter(AdvanPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # 활성 정책은 삭제 불가
    if policy.is_active:
        raise HTTPException(status_code=400, detail="Cannot delete active policy")

    db.delete(policy)
    db.commit()
    return {"message": f"Policy {policy_id} deleted"}


@router.post("/policies/default", response_model=AdvanPolicyResponse)
def create_default_policy(db: Session = Depends(get_db)):
    """기본 정책 생성."""
    from app.advan.policy import create_default_policy as do_create
    policy = do_create(db)
    return _policy_to_response(policy)


# ─── Simulation 엔드포인트 ───

@router.get("/runs", response_model=list[AdvanSimulationRunResponse])
def list_runs(
    market: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """시뮬레이션 실행 목록."""
    query = db.query(AdvanSimulationRun)
    if market:
        query = query.filter(AdvanSimulationRun.market == market)
    if status:
        query = query.filter(AdvanSimulationRun.status == status)

    runs = query.order_by(AdvanSimulationRun.created_at.desc()).limit(limit).all()
    return [_run_to_response(r) for r in runs]


@router.post("/runs", response_model=AdvanSimulationRunResponse)
def create_run(
    request: AdvanSimulationRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """시뮬레이션 실행 생성 (백그라운드)."""
    # 정책 존재 확인
    policy = db.query(AdvanPolicy).filter(AdvanPolicy.id == request.policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    run = AdvanSimulationRun(
        name=request.name,
        policy_id=request.policy_id,
        market=request.market,
        horizon=request.horizon,
        label_threshold_pct=request.label_threshold_pct,
        date_from=request.date_from,
        date_to=request.date_to,
        status="pending",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    from app.advan.simulator import run_simulation
    background_tasks.add_task(run_simulation, db, run.id)

    return _run_to_response(run)


@router.get("/runs/{run_id}", response_model=AdvanSimulationRunDetail)
def get_run(run_id: int, db: Session = Depends(get_db)):
    """시뮬레이션 실행 상세."""
    run = db.query(AdvanSimulationRun).filter(AdvanSimulationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    predictions = (
        db.query(AdvanPrediction)
        .filter(AdvanPrediction.run_id == run_id)
        .order_by(AdvanPrediction.prediction_date.desc())
        .all()
    )

    labels = (
        db.query(AdvanLabel)
        .join(AdvanPrediction, AdvanPrediction.id == AdvanLabel.prediction_id)
        .filter(AdvanPrediction.run_id == run_id)
        .all()
    )

    # Direction stats
    direction_stats = _calc_direction_stats(predictions, labels)

    return AdvanSimulationRunDetail(
        run=_run_to_response(run),
        predictions=[_prediction_to_response(p) for p in predictions],
        labels=[_label_to_response(l) for l in labels],
        direction_stats=direction_stats,
    )


@router.get("/runs/{run_id}/by-stock")
def run_by_stock(run_id: int, db: Session = Depends(get_db)):
    """종목별 예측 결과 (방향별 상세 포함)."""
    run = db.query(AdvanSimulationRun).filter(AdvanSimulationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    predictions = (
        db.query(AdvanPrediction)
        .filter(AdvanPrediction.run_id == run_id)
        .order_by(AdvanPrediction.prediction_date.desc())
        .all()
    )
    pred_ids = [p.id for p in predictions]
    labels = db.query(AdvanLabel).filter(AdvanLabel.prediction_id.in_(pred_ids)).all() if pred_ids else []
    label_map = {l.prediction_id: l for l in labels}

    # Group by ticker
    by_stock: dict[str, dict] = {}
    for pred in predictions:
        if pred.ticker not in by_stock:
            by_stock[pred.ticker] = {
                "total": 0, "correct": 0,
                "latest_prediction": pred.prediction,
                "latest_label": None,
                "latest_realized_ret": None,
                "by_direction": {},
            }
        by_stock[pred.ticker]["total"] += 1
        label = label_map.get(pred.id)
        if label and label.is_correct:
            by_stock[pred.ticker]["correct"] += 1

        # Per-direction stats
        d = pred.prediction
        if d not in by_stock[pred.ticker]["by_direction"]:
            by_stock[pred.ticker]["by_direction"][d] = {"total": 0, "correct": 0}
        by_stock[pred.ticker]["by_direction"][d]["total"] += 1
        if label and label.is_correct:
            by_stock[pred.ticker]["by_direction"][d]["correct"] += 1

        # Latest label info (predictions ordered desc, so first is latest)
        if by_stock[pred.ticker]["latest_label"] is None and label:
            by_stock[pred.ticker]["latest_label"] = label.label
            by_stock[pred.ticker]["latest_realized_ret"] = label.realized_ret

    # Get stock names
    tickers = list(by_stock.keys())
    name_rows = (
        db.query(AdvanEvent.ticker, AdvanEvent.stock_name)
        .filter(AdvanEvent.ticker.in_(tickers))
        .distinct()
        .all()
    ) if tickers else []
    name_map = {r.ticker: r.stock_name for r in name_rows}

    result = []
    for ticker, stats in by_stock.items():
        accuracy = round(stats["correct"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        result.append({
            "stock_code": ticker,
            "stock_name": name_map.get(ticker),
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": accuracy,
            "latest_prediction": stats["latest_prediction"],
            "latest_label": stats["latest_label"],
            "latest_realized_ret": round(stats["latest_realized_ret"], 2) if stats["latest_realized_ret"] is not None else None,
            "by_direction": stats["by_direction"],
        })

    return sorted(result, key=lambda x: x["total"], reverse=True)


@router.get("/runs/{run_id}/by-theme")
def run_by_theme(run_id: int, db: Session = Depends(get_db)):
    """테마별 예측 결과 (NewsEvent.theme 기준)."""
    run = db.query(AdvanSimulationRun).filter(AdvanSimulationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Join: Prediction → Event → NewsEvent (for theme)
    results = (
        db.query(
            NewsEvent.theme,
            func.count(AdvanPrediction.id).label("total"),
            func.sum(case((AdvanLabel.is_correct == True, 1), else_=0)).label("correct"),  # noqa: E712
        )
        .join(AdvanEvent, AdvanPrediction.event_id == AdvanEvent.id)
        .join(NewsEvent, AdvanEvent.source_news_id == NewsEvent.id)
        .outerjoin(AdvanLabel, AdvanLabel.prediction_id == AdvanPrediction.id)
        .filter(
            AdvanPrediction.run_id == run_id,
            NewsEvent.theme.isnot(None),
            NewsEvent.theme != "",
        )
        .group_by(NewsEvent.theme)
        .order_by(func.count(AdvanPrediction.id).desc())
        .all()
    )

    return [
        {
            "theme": r.theme,
            "total_stocks": r.total,
            "correct_count": int(r.correct or 0),
            "accuracy_rate": round(int(r.correct or 0) / r.total * 100, 1) if r.total > 0 else 0,
        }
        for r in results
    ]


@router.delete("/runs/{run_id}")
def delete_run(run_id: int, db: Session = Depends(get_db)):
    """시뮬레이션 실행 삭제."""
    run = db.query(AdvanSimulationRun).filter(AdvanSimulationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # 관련 라벨 삭제
    pred_ids = [p.id for p in db.query(AdvanPrediction.id).filter(AdvanPrediction.run_id == run_id).all()]
    if pred_ids:
        db.query(AdvanLabel).filter(AdvanLabel.prediction_id.in_(pred_ids)).delete(synchronize_session=False)
    # 관련 예측 삭제
    db.query(AdvanPrediction).filter(AdvanPrediction.run_id == run_id).delete()
    db.delete(run)
    db.commit()
    return {"message": f"Run {run_id} deleted"}


@router.get("/compare", response_model=AdvanCompareResponse)
def compare_runs(
    run_ids: str = Query(description="Comma-separated run IDs"),
    db: Session = Depends(get_db),
):
    """다중 실행 비교."""
    ids = [int(x.strip()) for x in run_ids.split(",") if x.strip()]
    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 run IDs required")

    runs = db.query(AdvanSimulationRun).filter(AdvanSimulationRun.id.in_(ids)).all()
    if len(runs) < 2:
        raise HTTPException(status_code=404, detail="Not enough runs found")

    items = []
    for r in runs:
        policy = db.query(AdvanPolicy).filter(AdvanPolicy.id == r.policy_id).first()
        items.append(AdvanCompareItem(
            id=r.id,
            name=r.name,
            policy_id=r.policy_id,
            policy_name=policy.name if policy else None,
            market=r.market,
            horizon=r.horizon,
            date_from=r.date_from,
            date_to=r.date_to,
            total_predictions=r.total_predictions,
            correct_count=r.correct_count,
            abstain_count=r.abstain_count,
            accuracy_rate=r.accuracy_rate,
            brier_score=r.brier_score,
            calibration_error=r.calibration_error,
            auc_score=r.auc_score,
            f1_score=r.f1_score,
            avg_excess_return=r.avg_excess_return,
            by_event_type_metrics=json.loads(r.by_event_type_metrics) if r.by_event_type_metrics else None,
        ))

    return AdvanCompareResponse(runs=items)


# ─── Evaluate 엔드포인트 ───

@router.get("/evaluate/{run_id}")
def evaluate_run_endpoint(run_id: int, db: Session = Depends(get_db)):
    """시뮬레이션 결과 상세 평가."""
    run = db.query(AdvanSimulationRun).filter(AdvanSimulationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    from app.advan.evaluator import evaluate_run
    metrics = evaluate_run(db, run_id)

    return {
        "run_id": run_id,
        "run_name": run.name,
        "policy_id": run.policy_id,
        "metrics": metrics,
    }


@router.get("/guardrails/{run_id}")
def check_guardrails(run_id: int, db: Session = Depends(get_db)):
    """안전장치 검사 실행."""
    run = db.query(AdvanSimulationRun).filter(AdvanSimulationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    from app.advan.guardrails import run_all_checks
    violations = run_all_checks(
        db=db,
        run_id=run_id,
        policy_id=run.policy_id,
        market=run.market,
        date_from=run.date_from,
        date_to=run.date_to,
    )

    return {
        "run_id": run_id,
        "violations": violations,
        "total_violations": len(violations),
        "has_errors": any(v["level"] == "error" for v in violations),
    }


# ─── Optimize 엔드포인트 ───

@router.post("/optimize", response_model=OptimizeResponse)
def run_optimization(
    request: OptimizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """정책 최적화 실행."""
    policy = db.query(AdvanPolicy).filter(AdvanPolicy.id == request.base_policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Base policy not found")

    from app.advan.optimizer import run_optimization as do_optimize

    result = do_optimize(
        db=db,
        base_policy_id=request.base_policy_id,
        market=request.market,
        date_from=request.date_from,
        date_to=request.date_to,
        num_candidates=request.num_candidates,
        val_split_ratio=request.val_split_ratio,
        target_metric=request.target_metric,
    )

    return OptimizeResponse(
        best_policy_id=result["best_policy_id"],
        best_policy_name=result["best_policy_name"],
        candidates_evaluated=result["candidates_evaluated"],
        best_metrics=result["best_metrics"],
        improvement_pct=result["improvement_pct"],
        message=result["message"],
    )


# ─── Helper 함수 ───

def _event_to_response(e: AdvanEvent) -> AdvanEventResponse:
    return AdvanEventResponse(
        id=e.id,
        source_news_id=e.source_news_id,
        ticker=e.ticker,
        stock_name=e.stock_name,
        market=e.market,
        event_type=e.event_type,
        direction=e.direction,
        magnitude=e.magnitude,
        magnitude_detail=e.magnitude_detail,
        novelty=e.novelty,
        credibility=e.credibility,
        is_disclosure=e.is_disclosure,
        title=e.title,
        summary=e.summary,
        source=e.source,
        confounders=e.confounders,
        event_timestamp=e.event_timestamp,
        is_after_market=e.is_after_market,
        created_at=e.created_at,
    )


def _policy_to_response(p: AdvanPolicy) -> AdvanPolicyResponse:
    return AdvanPolicyResponse(
        id=p.id,
        name=p.name,
        version=p.version,
        description=p.description,
        is_active=p.is_active,
        event_priors=EventPriors(**json.loads(p.event_priors)) if p.event_priors else EventPriors(),
        thresholds=PolicyThresholds(**json.loads(p.thresholds)) if p.thresholds else PolicyThresholds(),
        template_config=TemplateConfig(**json.loads(p.template_config)) if p.template_config else TemplateConfig(),
        retrieval_config=RetrievalConfig(**json.loads(p.retrieval_config)) if p.retrieval_config else RetrievalConfig(),
        latest_brier=p.latest_brier,
        latest_accuracy=p.latest_accuracy,
        latest_calibration=p.latest_calibration,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _run_to_response(r: AdvanSimulationRun) -> AdvanSimulationRunResponse:
    return AdvanSimulationRunResponse(
        id=r.id,
        name=r.name,
        policy_id=r.policy_id,
        market=r.market,
        horizon=r.horizon,
        label_threshold_pct=r.label_threshold_pct,
        date_from=r.date_from,
        date_to=r.date_to,
        status=r.status,
        total_predictions=r.total_predictions,
        correct_count=r.correct_count,
        abstain_count=r.abstain_count,
        accuracy_rate=r.accuracy_rate,
        brier_score=r.brier_score,
        calibration_error=r.calibration_error,
        auc_score=r.auc_score,
        f1_score=r.f1_score,
        avg_excess_return=r.avg_excess_return,
        by_event_type_metrics=json.loads(r.by_event_type_metrics) if r.by_event_type_metrics else None,
        duration_seconds=r.duration_seconds,
        error_message=r.error_message,
        created_at=r.created_at,
        completed_at=r.completed_at,
    )


def _prediction_to_response(p: AdvanPrediction) -> AdvanPredictionResponse:
    drivers = None
    if p.top_drivers:
        try:
            drivers = json.loads(p.top_drivers)
        except json.JSONDecodeError:
            drivers = None

    invalidators = None
    if p.invalidators:
        try:
            invalidators = json.loads(p.invalidators)
        except json.JSONDecodeError:
            invalidators = None

    return AdvanPredictionResponse(
        id=p.id,
        run_id=p.run_id,
        event_id=p.event_id,
        policy_id=p.policy_id,
        ticker=p.ticker,
        prediction_date=p.prediction_date,
        horizon=p.horizon,
        prediction=p.prediction,
        p_up=p.p_up,
        p_down=p.p_down,
        p_flat=p.p_flat,
        trade_action=p.trade_action,
        position_size=p.position_size,
        top_drivers=drivers,
        invalidators=invalidators,
        reasoning=p.reasoning,
    )


def _label_to_response(l: AdvanLabel) -> AdvanLabelResponse:
    return AdvanLabelResponse(
        id=l.id,
        prediction_id=l.prediction_id,
        ticker=l.ticker,
        prediction_date=l.prediction_date,
        horizon=l.horizon,
        realized_ret=l.realized_ret,
        excess_ret=l.excess_ret,
        label=l.label,
        is_correct=l.is_correct,
        label_date=l.label_date,
    )


def _calc_direction_stats(
    predictions: list[AdvanPrediction],
    labels: list[AdvanLabel],
) -> dict:
    """방향별 통계 계산."""
    label_map = {l.prediction_id: l for l in labels}
    stats: dict[str, dict] = {}

    for pred in predictions:
        direction = pred.prediction
        if direction not in stats:
            stats[direction] = {"total": 0, "correct": 0, "accuracy": 0.0}

        stats[direction]["total"] += 1
        label = label_map.get(pred.id)
        if label and label.is_correct:
            stats[direction]["correct"] += 1

    for direction, s in stats.items():
        s["accuracy"] = round(s["correct"] / s["total"], 4) if s["total"] > 0 else 0.0

    return stats
