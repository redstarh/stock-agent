"""정책 최적화기.

후보 정책 변형 생성 → 시뮬레이션 → 평가 → 최적 정책 승격.
Random search 기반, 향후 Bayesian/bandit 확장 가능.
"""

import json
import logging
import random
import time
from copy import deepcopy
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.advan.models import AdvanPolicy, AdvanSimulationRun

logger = logging.getLogger(__name__)

# 이벤트 유형 목록
EVENT_TYPES = [
    "실적", "가이던스", "수주", "증자", "소송", "규제",
    "경영권", "자사주", "배당", "공급계약", "기타",
]


def _mutate_priors(base_priors: dict, mutation_rate: float = 0.3) -> dict:
    """이벤트 priors를 랜덤 변형."""
    mutated = deepcopy(base_priors)
    for key in EVENT_TYPES:
        if key in mutated and random.random() < mutation_rate:
            delta = random.gauss(0, 0.15)
            mutated[key] = max(0.1, min(1.0, mutated[key] + delta))
            mutated[key] = round(mutated[key], 3)
    return mutated


def _mutate_thresholds(base_thresholds: dict, mutation_rate: float = 0.3) -> dict:
    """결정 임계값을 랜덤 변형."""
    mutated = deepcopy(base_thresholds)

    if random.random() < mutation_rate:
        mutated["buy_p"] = round(max(0.5, min(0.8, mutated.get("buy_p", 0.62) + random.gauss(0, 0.05))), 3)

    if random.random() < mutation_rate:
        mutated["sell_p"] = round(max(0.5, min(0.8, mutated.get("sell_p", 0.62) + random.gauss(0, 0.05))), 3)

    if random.random() < mutation_rate:
        mutated["abstain_low"] = round(
            max(0.2, min(0.5, mutated.get("abstain_low", 0.4) + random.gauss(0, 0.05))), 3
        )

    if random.random() < mutation_rate:
        mutated["abstain_high"] = round(
            max(0.5, min(0.8, mutated.get("abstain_high", 0.6) + random.gauss(0, 0.05))), 3
        )

    # abstain_low < abstain_high 보장
    if mutated.get("abstain_low", 0.4) >= mutated.get("abstain_high", 0.6):
        mutated["abstain_low"] = mutated["abstain_high"] - 0.1

    if random.random() < mutation_rate:
        mutated["label_threshold_pct"] = round(
            max(0.5, min(5.0, mutated.get("label_threshold_pct", 2.0) + random.gauss(0, 0.5))), 2
        )

    return mutated


def _mutate_retrieval(base_config: dict, mutation_rate: float = 0.2) -> dict:
    """Retrieval 설정 변형."""
    mutated = deepcopy(base_config)

    if random.random() < mutation_rate:
        mutated["max_results"] = random.choice([1, 2, 3, 5])

    if random.random() < mutation_rate:
        mutated["lookback_days"] = random.choice([180, 365, 730])

    if random.random() < mutation_rate:
        mutated["similarity_threshold"] = round(random.uniform(0.3, 0.7), 2)

    return mutated


def generate_candidate_policies(
    db: Session,
    base_policy: AdvanPolicy,
    num_candidates: int = 5,
) -> list[AdvanPolicy]:
    """기본 정책에서 N개의 후보 정책 변형 생성."""
    base_priors = json.loads(base_policy.event_priors) if base_policy.event_priors else {}
    base_thresholds = json.loads(base_policy.thresholds) if base_policy.thresholds else {}
    base_template = json.loads(base_policy.template_config) if base_policy.template_config else {}
    base_retrieval = json.loads(base_policy.retrieval_config) if base_policy.retrieval_config else {}

    candidates = []
    for i in range(num_candidates):
        mutated_priors = _mutate_priors(base_priors)
        mutated_thresholds = _mutate_thresholds(base_thresholds)
        mutated_retrieval = _mutate_retrieval(base_retrieval)

        # 버전 번호 증가
        base_ver = base_policy.version or "v1.0"
        new_ver = f"{base_ver}-opt{i+1}"

        candidate = AdvanPolicy(
            name=f"{base_policy.name}_candidate_{i+1}",
            version=new_ver,
            description=f"자동 생성된 후보 정책 (base: {base_policy.id}, variant {i+1})",
            is_active=False,
            event_priors=json.dumps(mutated_priors, ensure_ascii=False),
            thresholds=json.dumps(mutated_thresholds, ensure_ascii=False),
            template_config=json.dumps(base_template, ensure_ascii=False),
            retrieval_config=json.dumps(mutated_retrieval, ensure_ascii=False),
        )
        db.add(candidate)
        candidates.append(candidate)

    db.flush()  # ID 할당
    return candidates


def _run_simulation_for_policy(
    db: Session,
    policy: AdvanPolicy,
    market: str,
    date_from: date,
    date_to: date,
    horizon: int = 3,
    label_threshold: float = 2.0,
) -> AdvanSimulationRun:
    """특정 정책으로 시뮬레이션 실행 (동기)."""
    run = AdvanSimulationRun(
        name=f"opt_{policy.name}_{date_from}",
        policy_id=policy.id,
        market=market,
        horizon=horizon,
        label_threshold_pct=label_threshold,
        date_from=date_from,
        date_to=date_to,
        status="pending",
    )
    db.add(run)
    db.flush()

    from app.advan.simulator import run_simulation
    run_simulation(db, run.id)

    db.refresh(run)
    return run


def run_optimization(
    db: Session,
    base_policy_id: int,
    market: str,
    date_from: date,
    date_to: date,
    num_candidates: int = 5,
    val_split_ratio: float = 0.2,
    target_metric: str = "brier",
) -> dict:
    """정책 최적화 실행.

    1. 기간을 train/val로 분할
    2. 후보 정책 생성
    3. train 구간 시뮬레이션
    4. val 구간 평가
    5. 안정성 검증 후 최적 정책 승격

    Args:
        db: DB 세션
        base_policy_id: 기본 정책 ID
        market: 시장 (KR/US)
        date_from: 시작일
        date_to: 종료일
        num_candidates: 후보 수
        val_split_ratio: 검증 비율
        target_metric: 최적화 대상 (brier/accuracy/calibration)

    Returns:
        최적화 결과 dict
    """
    start_time = time.time()

    base_policy = db.query(AdvanPolicy).filter(AdvanPolicy.id == base_policy_id).first()
    if not base_policy:
        raise ValueError(f"Policy {base_policy_id} not found")

    # Train/Val 분할
    total_days = (date_to - date_from).days
    val_days = max(7, int(total_days * val_split_ratio))
    val_start = date_to - timedelta(days=val_days)
    train_end = val_start - timedelta(days=1)

    logger.info(
        "Optimization: train=%s~%s, val=%s~%s, candidates=%d",
        date_from, train_end, val_start, date_to, num_candidates,
    )

    # 후보 정책 생성
    candidates = generate_candidate_policies(db, base_policy, num_candidates)
    db.commit()

    # 각 후보에 대해 시뮬레이션 실행
    results = []

    # 기본 정책도 val에서 평가 (baseline)
    all_policies = [base_policy] + candidates

    for i, policy in enumerate(all_policies):
        logger.info("Evaluating policy %d/%d: %s", i + 1, len(all_policies), policy.name)
        try:
            run = _run_simulation_for_policy(
                db, policy, market, val_start, date_to,
                horizon=3,
                label_threshold=json.loads(policy.thresholds).get("label_threshold_pct", 2.0)
                if policy.thresholds else 2.0,
            )

            metric_value = _get_metric(run, target_metric)
            results.append({
                "policy_id": policy.id,
                "policy_name": policy.name,
                "run_id": run.id,
                "metric": metric_value,
                "accuracy": run.accuracy_rate,
                "brier": run.brier_score,
                "calibration": run.calibration_error,
                "total": run.total_predictions,
            })
        except Exception as e:
            logger.error("Policy %s evaluation failed: %s", policy.name, e)
            results.append({
                "policy_id": policy.id,
                "policy_name": policy.name,
                "run_id": None,
                "metric": float("inf") if target_metric == "brier" else 0.0,
                "accuracy": 0.0,
                "brier": 1.0,
                "calibration": 1.0,
                "total": 0,
            })

    # 최적 정책 선택
    if target_metric == "brier":
        # Brier는 낮을수록 좋음
        best = min(results, key=lambda r: r["metric"] if r["metric"] is not None else float("inf"))
    else:
        # accuracy, f1은 높을수록 좋음
        best = max(results, key=lambda r: r["metric"] if r["metric"] is not None else 0.0)

    # baseline(기본 정책)과 비교
    baseline = results[0]  # 첫 번째가 기본 정책

    improvement = 0.0
    if baseline["metric"] and baseline["metric"] != 0 and best["metric"] is not None:
        if target_metric == "brier":
            improvement = (baseline["metric"] - best["metric"]) / baseline["metric"] * 100
        else:
            improvement = (best["metric"] - baseline["metric"]) / max(baseline["metric"], 0.001) * 100

    # 안정성 검증: 기본보다 나아야 승격
    should_promote = improvement > 0

    if should_promote and best["policy_id"] != base_policy_id:
        # 최적 정책을 활성화 (기존 활성 해제)
        db.query(AdvanPolicy).filter(AdvanPolicy.is_active.is_(True)).update({"is_active": False})
        db.query(AdvanPolicy).filter(AdvanPolicy.id == best["policy_id"]).update({
            "is_active": True,
            "latest_brier": best.get("brier"),
            "latest_accuracy": best.get("accuracy"),
            "latest_calibration": best.get("calibration"),
        })
        db.commit()
        message = f"최적 정책 '{best['policy_name']}'으로 승격 (개선: {improvement:.1f}%)"
    else:
        message = f"기본 정책이 최선. 승격 없음 (개선: {improvement:.1f}%)"

    duration = round(time.time() - start_time, 2)

    return {
        "best_policy_id": best["policy_id"],
        "best_policy_name": best["policy_name"],
        "candidates_evaluated": len(results),
        "best_metrics": {
            "accuracy": best.get("accuracy", 0.0),
            "f1": 0.0,
            "brier": best.get("brier", 1.0),
            "calibration_error": best.get("calibration", 1.0),
            "auc": None,
            "avg_excess_return": None,
            "total_predictions": best.get("total", 0),
            "abstain_rate": 0.0,
        },
        "improvement_pct": round(improvement, 2),
        "message": message,
        "duration_seconds": duration,
        "all_results": results,
    }


def _get_metric(run: AdvanSimulationRun, metric_name: str) -> float | None:
    """시뮬레이션 결과에서 특정 메트릭 추출."""
    mapping = {
        "brier": run.brier_score,
        "accuracy": run.accuracy_rate,
        "calibration": run.calibration_error,
        "f1": run.f1_score,
        "auc": run.auc_score,
    }
    return mapping.get(metric_name)
