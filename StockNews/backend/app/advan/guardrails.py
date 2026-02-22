"""예측 시스템 안전장치.

미래 정보 누수 탐지, 데이터 품질 검증, 과최적화 감지.
"""

import logging
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.advan.models import (
    AdvanEvalRun,
    AdvanEvent,
    AdvanFeatureDaily,
    AdvanLabel,
    AdvanPrediction,
)

logger = logging.getLogger(__name__)


class GuardrailViolation:
    """안전장치 위반 레코드."""

    def __init__(self, level: str, category: str, message: str, details: dict | None = None):
        self.level = level  # error / warning / info
        self.category = category
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "category": self.category,
            "message": self.message,
            "details": self.details,
        }


def check_future_leakage(
    db: Session,
    run_id: int,
    prediction_date: date,
) -> list[GuardrailViolation]:
    """미래 정보 누수 검사.

    예측 시점 이후의 이벤트가 입력에 사용되었는지 확인.
    """
    violations = []

    predictions = (
        db.query(AdvanPrediction)
        .filter(AdvanPrediction.run_id == run_id)
        .filter(AdvanPrediction.prediction_date == prediction_date)
        .all()
    )

    for pred in predictions:
        if pred.event_id:
            event = db.query(AdvanEvent).filter(AdvanEvent.id == pred.event_id).first()
            if event and event.event_timestamp.date() > prediction_date:
                violations.append(GuardrailViolation(
                    level="error",
                    category="future_leakage",
                    message=f"이벤트 {event.id}의 시각({event.event_timestamp})이 "
                            f"예측일({prediction_date}) 이후입니다.",
                    details={"event_id": event.id, "ticker": pred.ticker},
                ))

    return violations


def check_data_quality(
    db: Session,
    market: str,
    date_from: date,
    date_to: date,
) -> list[GuardrailViolation]:
    """데이터 품질 검사.

    이벤트 수, 피처 누락, 라벨 결측 등.
    """
    violations = []

    # 이벤트 수 확인
    event_count = (
        db.query(func.count(AdvanEvent.id))
        .filter(
            AdvanEvent.market == market,
            func.date(AdvanEvent.event_timestamp) >= date_from,
            func.date(AdvanEvent.event_timestamp) <= date_to,
        )
        .scalar()
    )

    if event_count == 0:
        violations.append(GuardrailViolation(
            level="error",
            category="data_quality",
            message=f"기간 {date_from}~{date_to}에 이벤트가 없습니다.",
        ))
    elif event_count < 10:
        violations.append(GuardrailViolation(
            level="warning",
            category="data_quality",
            message=f"이벤트 수가 부족합니다: {event_count}건 (최소 10건 권장).",
        ))

    # 피처 데이터 확인
    feature_count = (
        db.query(func.count(AdvanFeatureDaily.id))
        .filter(
            AdvanFeatureDaily.market == market,
            AdvanFeatureDaily.trade_date >= date_from,
            AdvanFeatureDaily.trade_date <= date_to,
        )
        .scalar()
    )

    if feature_count == 0:
        violations.append(GuardrailViolation(
            level="warning",
            category="data_quality",
            message=f"기간 {date_from}~{date_to}에 시장 피처 데이터가 없습니다.",
        ))

    # 이벤트 유형 분포 확인 (편향 검사)
    type_counts = (
        db.query(AdvanEvent.event_type, func.count(AdvanEvent.id))
        .filter(
            AdvanEvent.market == market,
            func.date(AdvanEvent.event_timestamp) >= date_from,
            func.date(AdvanEvent.event_timestamp) <= date_to,
        )
        .group_by(AdvanEvent.event_type)
        .all()
    )

    if type_counts:
        total = sum(c for _, c in type_counts)
        for evt_type, count in type_counts:
            ratio = count / total
            if ratio > 0.7:
                violations.append(GuardrailViolation(
                    level="warning",
                    category="data_quality",
                    message=f"이벤트 유형 '{evt_type}'이 전체의 {ratio:.0%}를 차지합니다. 편향 주의.",
                    details={"event_type": evt_type, "ratio": round(ratio, 2)},
                ))

    return violations


def check_overfitting(
    db: Session,
    policy_id: int,
    min_eval_runs: int = 3,
) -> list[GuardrailViolation]:
    """과최적화 감지.

    최근 구간에서만 성능이 좋고 이전 구간에서 나쁜 경우 경고.
    """
    violations = []

    eval_runs = (
        db.query(AdvanEvalRun)
        .filter(AdvanEvalRun.policy_id == policy_id)
        .order_by(AdvanEvalRun.eval_period_from.asc())
        .all()
    )

    if len(eval_runs) < min_eval_runs:
        violations.append(GuardrailViolation(
            level="info",
            category="overfitting",
            message=f"평가 실행이 {len(eval_runs)}회로 과최적화 검사 불충분 (최소 {min_eval_runs}회).",
        ))
        return violations

    # 시간 순서대로 Brier 점수 비교
    briers = [r.brier for r in eval_runs if r.brier is not None]
    if len(briers) >= 3:
        # 전반부 vs 후반부 비교
        mid = len(briers) // 2
        early_avg = sum(briers[:mid]) / mid
        late_avg = sum(briers[mid:]) / (len(briers) - mid)

        # 최근 구간이 과도하게 좋으면 (Brier 50% 이상 개선) 경고
        if early_avg > 0 and (early_avg - late_avg) / early_avg > 0.5:
            violations.append(GuardrailViolation(
                level="warning",
                category="overfitting",
                message=f"최근 구간의 Brier({late_avg:.3f})가 이전({early_avg:.3f}) 대비 "
                        f"과도하게 개선되었습니다. 과최적화 가능성.",
                details={
                    "early_brier": round(early_avg, 4),
                    "late_brier": round(late_avg, 4),
                    "improvement_pct": round((early_avg - late_avg) / early_avg * 100, 1),
                },
            ))

    # Accuracy 안정성 검사
    accuracies = [r.accuracy for r in eval_runs if r.accuracy is not None]
    if len(accuracies) >= 3:
        mean_acc = sum(accuracies) / len(accuracies)
        variance = sum((a - mean_acc) ** 2 for a in accuracies) / len(accuracies)
        if variance > 0.05:  # 분산 > 5%
            violations.append(GuardrailViolation(
                level="warning",
                category="overfitting",
                message=f"정확도 분산이 높습니다({variance:.4f}). 구간별 성능이 불안정합니다.",
                details={"variance": round(variance, 4), "accuracies": [round(a, 4) for a in accuracies]},
            ))

    return violations


def check_label_integrity(
    db: Session,
    run_id: int,
) -> list[GuardrailViolation]:
    """라벨 무결성 검사.

    예측에 대한 라벨이 올바르게 생성되었는지 확인.
    """
    violations = []

    total_preds = (
        db.query(func.count(AdvanPrediction.id))
        .filter(AdvanPrediction.run_id == run_id)
        .scalar()
    )

    labeled_count = (
        db.query(func.count(AdvanLabel.id))
        .join(AdvanPrediction, AdvanPrediction.id == AdvanLabel.prediction_id)
        .filter(AdvanPrediction.run_id == run_id)
        .scalar()
    )

    if total_preds > 0 and labeled_count == 0:
        violations.append(GuardrailViolation(
            level="warning",
            category="label_integrity",
            message=f"실행 {run_id}에 {total_preds}개 예측이 있으나 라벨이 없습니다.",
        ))
    elif total_preds > 0:
        label_rate = labeled_count / total_preds
        if label_rate < 0.5:
            violations.append(GuardrailViolation(
                level="warning",
                category="label_integrity",
                message=f"라벨 비율이 낮습니다: {label_rate:.0%} ({labeled_count}/{total_preds}).",
            ))

    return violations


def run_all_checks(
    db: Session,
    run_id: int | None = None,
    policy_id: int | None = None,
    market: str = "KR",
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    """모든 안전장치 검사 실행."""
    all_violations = []

    if date_from and date_to:
        all_violations.extend(check_data_quality(db, market, date_from, date_to))

    if run_id:
        all_violations.extend(check_label_integrity(db, run_id))
        if date_from:
            all_violations.extend(check_future_leakage(db, run_id, date_from))

    if policy_id:
        all_violations.extend(check_overfitting(db, policy_id))

    return [v.to_dict() for v in all_violations]
