"""예측 컨텍스트 빌더 — 검증 데이터에서 LLM 참고용 컨텍스트를 생성."""

import json
import logging
import os
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.training import StockTrainingData
from app.models.verification import DailyPredictionResult, ThemePredictionAccuracy

logger = logging.getLogger(__name__)

DEFAULT_CONTEXT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "prediction_context.json",
)


def _get_verified_results(
    db: Session, days: int, market: str | None = None
) -> list[DailyPredictionResult]:
    """Get verified prediction results within the date range."""
    cutoff = date.today() - timedelta(days=days)
    query = db.query(DailyPredictionResult).filter(
        DailyPredictionResult.prediction_date >= cutoff,
        DailyPredictionResult.is_correct.isnot(None),
    )
    if market:
        query = query.filter(DailyPredictionResult.market == market)
    return query.all()


def _analyze_direction_accuracy(results: list[DailyPredictionResult]) -> list[dict]:
    """방향별 정확도 분석."""
    direction_stats: dict[str, dict] = {}
    for r in results:
        d = r.predicted_direction
        if d not in direction_stats:
            direction_stats[d] = {"total": 0, "correct": 0, "change_pcts": []}
        direction_stats[d]["total"] += 1
        if r.is_correct:
            direction_stats[d]["correct"] += 1
        if r.actual_change_pct is not None:
            direction_stats[d]["change_pcts"].append(r.actual_change_pct)

    out = []
    for direction, stats in sorted(direction_stats.items()):
        total = stats["total"]
        correct = stats["correct"]
        accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0
        change_pcts = stats["change_pcts"]
        avg_change = round(sum(change_pcts) / len(change_pcts), 2) if change_pcts else None
        out.append({
            "direction": direction,
            "total": total,
            "correct": correct,
            "accuracy": accuracy,
            "avg_actual_change_pct": avg_change,
        })
    return out


def _analyze_theme_predictability(
    db: Session, days: int, market: str | None = None
) -> list[dict]:
    """테마별 예측 가능성 분석."""
    cutoff = date.today() - timedelta(days=days)
    query = db.query(
        ThemePredictionAccuracy.theme,
        func.sum(ThemePredictionAccuracy.total_stocks).label("total"),
        func.sum(ThemePredictionAccuracy.correct_count).label("correct"),
    ).filter(
        ThemePredictionAccuracy.prediction_date >= cutoff,
    ).group_by(ThemePredictionAccuracy.theme)

    if market:
        query = query.filter(ThemePredictionAccuracy.market == market)

    rows = query.all()
    out = []
    for row in rows:
        total = row.total or 0
        correct = row.correct or 0
        accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0
        if accuracy >= 60 and total >= 5:
            predictability = "high"
        elif accuracy >= 40 and total >= 3:
            predictability = "medium"
        else:
            predictability = "low"
        out.append({
            "theme": row.theme,
            "accuracy": accuracy,
            "total": total,
            "predictability": predictability,
        })
    return sorted(out, key=lambda x: x["accuracy"], reverse=True)


def _analyze_sentiment_ranges(
    db: Session, days: int, market: str | None = None
) -> list[dict]:
    """감성 점수 범위별 실제 방향 분포."""
    cutoff = date.today() - timedelta(days=days)
    query = db.query(StockTrainingData).filter(
        StockTrainingData.prediction_date >= cutoff,
        StockTrainingData.actual_direction.isnot(None),
    )
    if market:
        query = query.filter(StockTrainingData.market == market)

    rows = query.all()

    # Define buckets: [-1.0, -0.5), [-0.5, 0.0), [0.0, 0.5), [0.5, 1.0]
    buckets = [
        ("-1.0~-0.5", -1.0, -0.5),
        ("-0.5~0.0", -0.5, 0.0),
        ("0.0~0.5", 0.0, 0.5),
        ("0.5~1.0", 0.5, 1.01),  # inclusive upper bound
    ]

    out = []
    for label, low, high in buckets:
        bucket_rows = [r for r in rows if low <= r.sentiment_score < high]
        total = len(bucket_rows)
        up_count = sum(1 for r in bucket_rows if r.actual_direction == "up")
        down_count = sum(1 for r in bucket_rows if r.actual_direction == "down")
        neutral_count = sum(1 for r in bucket_rows if r.actual_direction == "neutral")
        out.append({
            "range_label": label,
            "total": total,
            "up_count": up_count,
            "down_count": down_count,
            "neutral_count": neutral_count,
            "up_ratio": round(up_count / total, 2) if total > 0 else 0.0,
            "down_ratio": round(down_count / total, 2) if total > 0 else 0.0,
        })
    return out


def _analyze_news_count_effect(results: list[DailyPredictionResult]) -> list[dict]:
    """뉴스 건수별 정확도."""
    ranges = [
        ("1-5", 1, 5),
        ("6-15", 6, 15),
        ("16+", 16, 9999),
    ]
    out = []
    for label, low, high in ranges:
        bucket = [r for r in results if low <= r.news_count <= high]
        total = len(bucket)
        correct = sum(1 for r in bucket if r.is_correct)
        accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0
        out.append({"range_label": label, "total": total, "accuracy": accuracy})
    return out


def _analyze_confidence_calibration(results: list[DailyPredictionResult]) -> list[dict]:
    """Confidence 보정 분석."""
    ranges = [
        ("0.0-0.3", 0.0, 0.3),
        ("0.3-0.6", 0.3, 0.6),
        ("0.6-1.0", 0.6, 1.01),
    ]
    out = []
    for label, low, high in ranges:
        bucket = [r for r in results if low <= r.confidence < high]
        total = len(bucket)
        correct = sum(1 for r in bucket if r.is_correct)
        accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0
        out.append({"range_label": label, "total": total, "accuracy": accuracy})
    return out


def _analyze_score_ranges(results: list[DailyPredictionResult]) -> list[dict]:
    """예측 점수 구간별 실제 방향 분포."""
    ranges = [
        ("0-30", 0, 30),
        ("30-50", 30, 50),
        ("50-70", 50, 70),
        ("70-100", 70, 100.01),
    ]
    out = []
    for label, low, high in ranges:
        bucket = [r for r in results if low <= r.predicted_score < high]
        total = len(bucket)
        up_count = sum(1 for r in bucket if r.actual_direction == "up")
        down_count = sum(1 for r in bucket if r.actual_direction == "down")
        neutral_count = sum(1 for r in bucket if r.actual_direction == "neutral")
        out.append({
            "range_label": label,
            "total": total,
            "up_count": up_count,
            "down_count": down_count,
            "neutral_count": neutral_count,
        })
    return out


def _analyze_failure_patterns(results: list[DailyPredictionResult]) -> list[dict]:
    """실패 패턴 감지."""
    patterns = []

    # Pattern 1: High score but down
    high_score_down = [
        r for r in results
        if r.predicted_score >= 70 and r.actual_direction == "down"
    ]
    if high_score_down:
        patterns.append({
            "pattern": "high_score_down",
            "count": len(high_score_down),
            "description": f"높은 점수(>=70)에도 하락한 경우 {len(high_score_down)}건",
        })

    # Pattern 2: Low score but up
    low_score_up = [
        r for r in results
        if r.predicted_score <= 30 and r.actual_direction == "up"
    ]
    if low_score_up:
        patterns.append({
            "pattern": "low_score_up",
            "count": len(low_score_up),
            "description": f"낮은 점수(<=30)에도 상승한 경우 {len(low_score_up)}건",
        })

    # Pattern 3: High confidence but wrong
    high_conf_wrong = [
        r for r in results
        if r.confidence >= 0.7 and not r.is_correct
    ]
    if high_conf_wrong:
        patterns.append({
            "pattern": "high_confidence_wrong",
            "count": len(high_conf_wrong),
            "description": f"높은 신뢰도(>=0.7)에도 틀린 경우 {len(high_conf_wrong)}건",
        })

    # Pattern 4: Neutral prediction but big move
    neutral_big_move = [
        r for r in results
        if r.predicted_direction == "neutral"
        and r.actual_change_pct is not None
        and abs(r.actual_change_pct) >= 3.0
    ]
    if neutral_big_move:
        patterns.append({
            "pattern": "neutral_big_move",
            "count": len(neutral_big_move),
            "description": f"중립 예측이나 3%이상 변동 {len(neutral_big_move)}건",
        })

    return patterns


def _analyze_market_conditions(
    db: Session, results: list[DailyPredictionResult], days: int
) -> list[dict]:
    """시장별 조건 분석."""
    markets: dict[str, list[DailyPredictionResult]] = {}
    for r in results:
        markets.setdefault(r.market, []).append(r)

    cutoff = date.today() - timedelta(days=days)
    out = []
    for market, market_results in sorted(markets.items()):
        total = len(market_results)
        correct = sum(1 for r in market_results if r.is_correct)
        accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0

        # Find best/worst theme for this market
        theme_query = db.query(
            ThemePredictionAccuracy.theme,
            func.sum(ThemePredictionAccuracy.total_stocks).label("total"),
            func.sum(ThemePredictionAccuracy.correct_count).label("correct"),
        ).filter(
            ThemePredictionAccuracy.prediction_date >= cutoff,
            ThemePredictionAccuracy.market == market,
        ).group_by(ThemePredictionAccuracy.theme).having(
            func.sum(ThemePredictionAccuracy.total_stocks) >= 3
        ).all()

        best_theme = None
        worst_theme = None
        if theme_query:
            theme_accs = []
            for t in theme_query:
                t_total = t.total or 0
                t_correct = t.correct or 0
                t_acc = (t_correct / t_total * 100) if t_total > 0 else 0
                theme_accs.append((t.theme, t_acc))
            theme_accs.sort(key=lambda x: x[1], reverse=True)
            best_theme = theme_accs[0][0] if theme_accs else None
            worst_theme = theme_accs[-1][0] if len(theme_accs) > 1 else None

        out.append({
            "market": market,
            "accuracy": accuracy,
            "total": total,
            "best_theme": best_theme,
            "worst_theme": worst_theme,
        })
    return out


def build_prediction_context(
    db: Session, days: int = 30, market: str | None = None
) -> dict:
    """검증 데이터로부터 예측 컨텍스트를 생성.

    Args:
        db: SQLAlchemy session
        days: 분석 기간 (일)
        market: 시장 필터 (None=전체)

    Returns:
        예측 컨텍스트 딕셔너리
    """
    results = _get_verified_results(db, days, market)

    total = len(results)
    correct = sum(1 for r in results if r.is_correct)
    overall_accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0

    version = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    context = {
        "version": version,
        "generated_at": datetime.now(UTC).isoformat(),
        "analysis_days": days,
        "total_predictions": total,
        "overall_accuracy": overall_accuracy,
        "direction_accuracy": _analyze_direction_accuracy(results),
        "theme_predictability": _analyze_theme_predictability(db, days, market),
        "sentiment_ranges": _analyze_sentiment_ranges(db, days, market),
        "news_count_effect": _analyze_news_count_effect(results),
        "confidence_calibration": _analyze_confidence_calibration(results),
        "score_ranges": _analyze_score_ranges(results),
        "failure_patterns": _analyze_failure_patterns(results),
        "market_conditions": _analyze_market_conditions(db, results, days),
    }

    logger.info(
        "Built prediction context: %d predictions, %.1f%% accuracy (days=%d, market=%s)",
        total,
        overall_accuracy,
        days,
        market or "ALL",
    )
    return context


def build_and_save_prediction_context(
    db: Session, days: int = 30, output_path: str | None = None
) -> dict:
    """컨텍스트를 생성하고 JSON 파일로 저장.

    Args:
        db: SQLAlchemy session
        days: 분석 기간
        output_path: 저장 경로 (None=기본 경로)

    Returns:
        생성된 컨텍스트 딕셔너리
    """
    context = build_prediction_context(db, days)
    path = output_path or DEFAULT_CONTEXT_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)

    logger.info("Saved prediction context to %s", path)
    return context
