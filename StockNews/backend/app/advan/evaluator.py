"""예측 평가 모듈.

Brier Score, Calibration Error, AUC, Accuracy/F1 등 평가 메트릭 계산.
이벤트 유형별 성능 분해 및 robustness 분석.
"""

import json
import logging
import math
from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.advan.models import (
    AdvanEvalRun,
    AdvanLabel,
    AdvanPrediction,
)

logger = logging.getLogger(__name__)


def _brier_score(predictions: list[dict]) -> float:
    """Brier Score 계산.

    BS = (1/N) * Σ (p_predicted - actual)²
    actual: 1 if event occurred, 0 otherwise
    낮을수록 좋음 (0 = 완벽, 1 = 최악).

    3-class 확장: BS = (1/N) * Σ Σ_k (p_k - o_k)²
    """
    if not predictions:
        return 1.0

    total = 0.0
    count = 0

    for pred in predictions:
        actual_label = pred.get("actual_label")
        if actual_label is None:
            continue

        p_up = pred.get("p_up", 0.33)
        p_down = pred.get("p_down", 0.33)
        p_flat = pred.get("p_flat", 0.34)

        # One-hot actual
        o_up = 1.0 if actual_label == "Up" else 0.0
        o_down = 1.0 if actual_label == "Down" else 0.0
        o_flat = 1.0 if actual_label == "Flat" else 0.0

        bs = (p_up - o_up) ** 2 + (p_down - o_down) ** 2 + (p_flat - o_flat) ** 2
        total += bs
        count += 1

    return total / count if count > 0 else 1.0


def _calibration_error(predictions: list[dict], n_bins: int = 10) -> float:
    """Expected Calibration Error (ECE).

    확률 예측의 신뢰도 보정 오차.
    낮을수록 좋음.
    """
    if not predictions:
        return 1.0

    bins = defaultdict(lambda: {"correct": 0, "total": 0, "confidence_sum": 0.0})

    for pred in predictions:
        actual_label = pred.get("actual_label")
        if actual_label is None:
            continue

        predicted = pred.get("prediction")
        if predicted == "Abstain":
            continue

        # 해당 예측의 확률
        p_map = {"Up": pred.get("p_up", 0), "Down": pred.get("p_down", 0), "Flat": pred.get("p_flat", 0)}
        confidence = p_map.get(predicted, 0.33)

        bin_idx = min(int(confidence * n_bins), n_bins - 1)
        bins[bin_idx]["total"] += 1
        bins[bin_idx]["confidence_sum"] += confidence
        if predicted == actual_label:
            bins[bin_idx]["correct"] += 1

    total_samples = sum(b["total"] for b in bins.values())
    if total_samples == 0:
        return 1.0

    ece = 0.0
    for b in bins.values():
        if b["total"] == 0:
            continue
        avg_confidence = b["confidence_sum"] / b["total"]
        accuracy = b["correct"] / b["total"]
        ece += (b["total"] / total_samples) * abs(accuracy - avg_confidence)

    return ece


def _accuracy_f1(predictions: list[dict]) -> dict:
    """정확도 및 F1 스코어 계산."""
    if not predictions:
        return {"accuracy": 0.0, "f1": 0.0}

    correct = 0
    total = 0
    # Per-class TP, FP, FN
    classes = ["Up", "Down", "Flat"]
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)

    for pred in predictions:
        actual = pred.get("actual_label")
        predicted = pred.get("prediction")
        if actual is None or predicted == "Abstain":
            continue

        total += 1
        if predicted == actual:
            correct += 1
            tp[predicted] += 1
        else:
            fp[predicted] += 1
            fn[actual] += 1

    accuracy = correct / total if total > 0 else 0.0

    # Macro F1
    f1_scores = []
    for cls in classes:
        precision = tp[cls] / (tp[cls] + fp[cls]) if (tp[cls] + fp[cls]) > 0 else 0.0
        recall = tp[cls] / (tp[cls] + fn[cls]) if (tp[cls] + fn[cls]) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        f1_scores.append(f1)

    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0

    return {"accuracy": round(accuracy, 4), "f1": round(macro_f1, 4)}


def _auc_binary(predictions: list[dict]) -> float | None:
    """이진 분류 AUC 근사 (Up vs Not-Up).

    간단한 Mann-Whitney U 통계량 기반.
    """
    positives = []  # p_up for actual Up
    negatives = []  # p_up for actual Not-Up

    for pred in predictions:
        actual = pred.get("actual_label")
        if actual is None or pred.get("prediction") == "Abstain":
            continue

        p_up = pred.get("p_up", 0.33)
        if actual == "Up":
            positives.append(p_up)
        else:
            negatives.append(p_up)

    if not positives or not negatives:
        return None

    # Mann-Whitney U
    concordant = 0
    tied = 0
    total_pairs = len(positives) * len(negatives)

    for p in positives:
        for n in negatives:
            if p > n:
                concordant += 1
            elif p == n:
                tied += 0.5

    auc = (concordant + tied) / total_pairs if total_pairs > 0 else 0.5
    return round(auc, 4)


def _by_event_type_metrics(predictions: list[dict]) -> dict:
    """이벤트 유형별 성능 분해."""
    by_type = defaultdict(list)

    for pred in predictions:
        event_type = pred.get("event_type", "기타")
        by_type[event_type].append(pred)

    result = {}
    for evt_type, preds in by_type.items():
        acc_f1 = _accuracy_f1(preds)
        brier = _brier_score(preds)
        total = len(preds)
        abstain = sum(1 for p in preds if p.get("prediction") == "Abstain")

        result[evt_type] = {
            "total": total,
            "accuracy": acc_f1["accuracy"],
            "f1": acc_f1["f1"],
            "brier": round(brier, 4),
            "abstain_count": abstain,
        }

    return result


def _by_direction_metrics(predictions: list[dict]) -> dict:
    """예측 방향별 성능 분해."""
    by_dir = defaultdict(lambda: {"total": 0, "correct": 0})

    for pred in predictions:
        actual = pred.get("actual_label")
        predicted = pred.get("prediction")
        if actual is None or predicted == "Abstain":
            continue

        by_dir[predicted]["total"] += 1
        if predicted == actual:
            by_dir[predicted]["correct"] += 1

    result = {}
    for direction, stats in by_dir.items():
        result[direction] = {
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": round(stats["correct"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
        }

    return result


def _robustness_metrics(predictions: list[dict]) -> dict:
    """구간별 안정성 분석.

    날짜를 4분할하여 각 구간의 성능 분산을 계산.
    """
    if len(predictions) < 8:
        return {"variance": None, "min_accuracy": None, "max_accuracy": None}

    # 날짜 기준 정렬
    sorted_preds = sorted(predictions, key=lambda p: p.get("prediction_date", ""))
    quarter = len(sorted_preds) // 4

    splits = [
        sorted_preds[:quarter],
        sorted_preds[quarter:2*quarter],
        sorted_preds[2*quarter:3*quarter],
        sorted_preds[3*quarter:],
    ]

    accuracies = []
    for split in splits:
        if not split:
            continue
        acc = _accuracy_f1(split)["accuracy"]
        accuracies.append(acc)

    if len(accuracies) < 2:
        return {"variance": None, "min_accuracy": None, "max_accuracy": None}

    mean_acc = sum(accuracies) / len(accuracies)
    variance = sum((a - mean_acc) ** 2 for a in accuracies) / len(accuracies)

    return {
        "variance": round(variance, 6),
        "std_dev": round(math.sqrt(variance), 4),
        "min_accuracy": round(min(accuracies), 4),
        "max_accuracy": round(max(accuracies), 4),
        "split_accuracies": [round(a, 4) for a in accuracies],
    }


def evaluate_run(
    db: Session,
    run_id: int,
    split_type: str = "test",
) -> dict:
    """시뮬레이션 실행 결과를 종합 평가.

    Args:
        db: DB 세션
        run_id: AdvanSimulationRun.id
        split_type: 평가 구간 유형 (train/val/test)

    Returns:
        평가 메트릭 dict
    """
    # 예측 + 라벨 조인
    results = (
        db.query(AdvanPrediction, AdvanLabel)
        .outerjoin(AdvanLabel, AdvanPrediction.id == AdvanLabel.prediction_id)
        .filter(AdvanPrediction.run_id == run_id)
        .all()
    )

    if not results:
        logger.warning("No predictions found for run_id=%d", run_id)
        return _empty_metrics()

    # 평가용 데이터 구성
    predictions = []
    for pred, label in results:
        pred_dict = {
            "prediction": pred.prediction,
            "p_up": pred.p_up,
            "p_down": pred.p_down,
            "p_flat": pred.p_flat,
            "actual_label": label.label if label else None,
            "realized_ret": label.realized_ret if label else None,
            "excess_ret": label.excess_ret if label else None,
            "is_correct": label.is_correct if label else None,
            "prediction_date": str(pred.prediction_date),
            "event_type": "기타",  # 이벤트 타입은 별도 조인 필요
        }
        predictions.append(pred_dict)

    # 이벤트 타입 보강 (가능하면)
    from app.advan.models import AdvanEvent
    for pred_obj, _ in results:
        if pred_obj.event_id:
            event = db.query(AdvanEvent).filter(AdvanEvent.id == pred_obj.event_id).first()
            if event:
                # 해당 prediction dict 찾기
                for pd in predictions:
                    if pd["prediction_date"] == str(pred_obj.prediction_date):
                        pd["event_type"] = event.event_type
                        break

    # 라벨 있는 것만 필터
    labeled = [p for p in predictions if p["actual_label"] is not None]
    total = len(predictions)
    abstain_count = sum(1 for p in predictions if p["prediction"] == "Abstain")

    # 메트릭 계산
    acc_f1 = _accuracy_f1(labeled)
    brier = _brier_score(labeled)
    calibration = _calibration_error(labeled)
    auc = _auc_binary(labeled)
    by_type = _by_event_type_metrics(labeled)
    by_dir = _by_direction_metrics(labeled)
    robustness = _robustness_metrics(labeled)

    # 평균 초과수익률
    excess_returns = [p["excess_ret"] for p in labeled if p.get("excess_ret") is not None]
    avg_excess = sum(excess_returns) / len(excess_returns) if excess_returns else None

    metrics = {
        "accuracy": acc_f1["accuracy"],
        "f1": acc_f1["f1"],
        "brier": round(brier, 4),
        "calibration_error": round(calibration, 4),
        "auc": auc,
        "avg_excess_return": round(avg_excess, 4) if avg_excess is not None else None,
        "total_predictions": total,
        "labeled_predictions": len(labeled),
        "abstain_count": abstain_count,
        "abstain_rate": round(abstain_count / total, 4) if total > 0 else 0.0,
        "by_event_type": by_type,
        "by_direction": by_dir,
        "robustness_metrics": robustness,
    }

    return metrics


def save_eval_run(
    db: Session,
    policy_id: int,
    simulation_run_id: int | None,
    period_from: date,
    period_to: date,
    split_type: str,
    metrics: dict,
) -> AdvanEvalRun:
    """평가 결과를 DB에 저장."""
    eval_run = AdvanEvalRun(
        policy_id=policy_id,
        simulation_run_id=simulation_run_id,
        eval_period_from=period_from,
        eval_period_to=period_to,
        split_type=split_type,
        accuracy=metrics.get("accuracy", 0.0),
        f1=metrics.get("f1", 0.0),
        brier=metrics.get("brier", 1.0),
        calibration_error=metrics.get("calibration_error", 1.0),
        auc=metrics.get("auc"),
        avg_excess_return=metrics.get("avg_excess_return"),
        by_event_type=json.dumps(metrics.get("by_event_type", {}), ensure_ascii=False),
        by_direction=json.dumps(metrics.get("by_direction", {}), ensure_ascii=False),
        robustness_metrics=json.dumps(metrics.get("robustness_metrics", {}), ensure_ascii=False),
        total_predictions=metrics.get("total_predictions", 0),
        abstain_rate=metrics.get("abstain_rate", 0.0),
    )
    db.add(eval_run)
    db.commit()
    db.refresh(eval_run)
    return eval_run


def _empty_metrics() -> dict:
    """빈 메트릭 반환."""
    return {
        "accuracy": 0.0,
        "f1": 0.0,
        "brier": 1.0,
        "calibration_error": 1.0,
        "auc": None,
        "avg_excess_return": None,
        "total_predictions": 0,
        "labeled_predictions": 0,
        "abstain_count": 0,
        "abstain_rate": 0.0,
        "by_event_type": {},
        "by_direction": {},
        "robustness_metrics": {},
    }
