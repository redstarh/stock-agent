"""테마별 예측 정확도 집계."""

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models.news_event import NewsEvent
from app.models.verification import DailyPredictionResult, ThemePredictionAccuracy

logger = logging.getLogger(__name__)


def aggregate_theme_accuracy(
    db: Session, target_date: date, market: str
) -> list[ThemePredictionAccuracy]:
    """Aggregate theme-level accuracy from daily results."""
    # Get daily results for this date+market
    results = (
        db.query(DailyPredictionResult)
        .filter(
            DailyPredictionResult.prediction_date == target_date,
            DailyPredictionResult.market == market,
            DailyPredictionResult.is_correct.isnot(None),
        )
        .all()
    )

    if not results:
        return []

    # Map stock_code to themes from news_event
    stock_codes = list({r.stock_code for r in results})
    theme_map: dict[str, set[str]] = {}  # theme -> set of stock_codes

    for code in stock_codes:
        themes_row = (
            db.query(NewsEvent.theme)
            .filter(
                NewsEvent.stock_code == code,
                NewsEvent.market == market,
                NewsEvent.theme.isnot(None),
                NewsEvent.theme != "",
            )
            .distinct()
            .all()
        )
        for (theme_str,) in themes_row:
            for t in theme_str.split(","):
                t = t.strip()
                if t:
                    theme_map.setdefault(t, set()).add(code)

    # Aggregate per theme
    aggregated = []
    for theme, codes in theme_map.items():
        theme_results = [r for r in results if r.stock_code in codes]
        if not theme_results:
            continue

        total = len(theme_results)
        correct = sum(1 for r in theme_results if r.is_correct)
        accuracy = correct / total if total > 0 else 0.0
        avg_score = sum(r.predicted_score for r in theme_results) / total

        actual_changes = [r.actual_change_pct for r in theme_results if r.actual_change_pct is not None]
        avg_change = sum(actual_changes) / len(actual_changes) if actual_changes else None

        entry = ThemePredictionAccuracy(
            prediction_date=target_date,
            theme=theme,
            market=market,
            total_stocks=total,
            correct_count=correct,
            accuracy_rate=round(accuracy, 4),
            avg_predicted_score=round(avg_score, 2),
            avg_actual_change_pct=round(avg_change, 4) if avg_change is not None else None,
        )
        db.add(entry)
        aggregated.append(entry)

    db.commit()
    return aggregated
