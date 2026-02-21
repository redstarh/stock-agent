"""Historical training data backfill — 과거 예측 결과로부터 학습 데이터 생성."""

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.training import StockTrainingData
from app.models.verification import DailyPredictionResult
from app.processing.training_data_builder import build_training_snapshot

logger = logging.getLogger(__name__)


def backfill_training_data(
    db: Session,
    market: str = "KR",
    days_back: int = 30,
    dry_run: bool = False,
) -> dict:
    """과거 DailyPredictionResult 기반으로 StockTrainingData를 역산 생성.

    Args:
        db: Database session
        market: 시장 (KR/US)
        days_back: 역산 일수 (기본 30일)
        dry_run: True면 실제 저장하지 않고 건수만 반환

    Returns:
        {"created": int, "skipped": int, "failed": int, "dates_processed": int}
    """
    created = 0
    skipped = 0
    failed = 0
    dates_processed = 0

    # 1. Get all unique prediction dates from DailyPredictionResult for the market
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)

    prediction_dates = (
        db.query(DailyPredictionResult.prediction_date)
        .filter(
            DailyPredictionResult.market == market,
            DailyPredictionResult.prediction_date >= start_date,
            DailyPredictionResult.prediction_date <= end_date,
        )
        .distinct()
        .order_by(DailyPredictionResult.prediction_date)
        .all()
    )

    unique_dates = [d[0] for d in prediction_dates]
    logger.info(f"Found {len(unique_dates)} unique prediction dates for market {market}")

    # 2. For each date, process all DailyPredictionResult records
    for target_date in unique_dates:
        dates_processed += 1
        logger.info(f"Processing date {target_date} ({dates_processed}/{len(unique_dates)})")

        # Get all prediction results for this date
        results = (
            db.query(DailyPredictionResult)
            .filter(
                DailyPredictionResult.prediction_date == target_date,
                DailyPredictionResult.market == market,
            )
            .all()
        )

        for result in results:
            try:
                # 3. Check if StockTrainingData already exists for that date+stock_code
                existing = (
                    db.query(StockTrainingData)
                    .filter(
                        StockTrainingData.prediction_date == target_date,
                        StockTrainingData.stock_code == result.stock_code,
                    )
                    .first()
                )

                if existing:
                    logger.debug(f"Skipping existing record for {result.stock_code} on {target_date}")
                    skipped += 1
                    continue

                # 4. Build prediction dict from DailyPredictionResult
                prediction = {
                    "direction": result.predicted_direction,
                    "score": result.predicted_score,
                    "confidence": result.confidence,
                }

                if dry_run:
                    logger.info(f"[DRY RUN] Would create training data for {result.stock_code} on {target_date}")
                    created += 1
                    continue

                # Create training snapshot
                training_record = build_training_snapshot(
                    db=db,
                    stock_code=result.stock_code,
                    stock_name=result.stock_name,
                    market=market,
                    target_date=target_date,
                    prediction=prediction,
                )

                # 5. If actual prices exist in DailyPredictionResult, update actuals
                if result.actual_close_price is not None and result.actual_change_pct is not None:

                    # Update the training record with actuals
                    training_record.actual_close = result.actual_close_price
                    training_record.actual_change_pct = result.actual_change_pct
                    training_record.actual_volume = result.actual_volume
                    training_record.actual_direction = result.actual_direction
                    training_record.is_correct = result.is_correct

                created += 1
                logger.debug(f"Created training data for {result.stock_code} on {target_date}")

            except Exception as e:
                logger.error(f"Failed to process {result.stock_code} on {target_date}: {e}")
                failed += 1
                continue

        # 6. Commit after each date to keep transactions small
        if not dry_run:
            try:
                db.commit()
                logger.info(f"Committed batch for {target_date}")
            except Exception as e:
                logger.error(f"Failed to commit batch for {target_date}: {e}")
                db.rollback()

    # 7. Log summary
    summary = {
        "created": created,
        "skipped": skipped,
        "failed": failed,
        "dates_processed": dates_processed,
    }

    logger.info(
        f"Backfill complete: {created} created, {skipped} skipped, "
        f"{failed} failed, {dates_processed} dates processed"
    )

    return summary


def run_backfill(market: str = "KR", days_back: int = 30, dry_run: bool = False) -> dict:
    """Standalone entry point for backfill (creates own DB session).

    Args:
        market: 시장 (KR/US)
        days_back: 역산 일수
        dry_run: True면 실제 저장하지 않음

    Returns:
        Summary dict with counts
    """
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        result = backfill_training_data(db, market, days_back, dry_run)
        return result
    finally:
        db.close()
