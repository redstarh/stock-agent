"""예측 검증 엔진 — 예측 vs 실제 주가 비교."""

import logging
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.news_event import NewsEvent
from app.models.verification import (
    DailyPredictionResult,
    VerificationRunLog,
)
from app.processing.price_fetcher import (
    fetch_prices_batch,
    get_direction_from_change,
)
from app.processing.training_data_builder import (
    build_training_snapshot,
    update_training_actuals,
)

logger = logging.getLogger(__name__)


def get_stocks_with_news(
    db: Session, target_date: date, market: str, min_news_count: int = 3
) -> list[dict]:
    """Get stocks that have sufficient recent news for prediction."""
    cutoff = target_date - timedelta(days=30)
    rows = (
        db.query(
            NewsEvent.stock_code,
            NewsEvent.stock_name,
            func.count(NewsEvent.id).label("news_count"),
        )
        .filter(
            NewsEvent.market == market,
            NewsEvent.created_at >= datetime.combine(cutoff, datetime.min.time()),
            NewsEvent.created_at <= datetime.combine(target_date, datetime.max.time()),
        )
        .group_by(NewsEvent.stock_code, NewsEvent.stock_name)
        .having(func.count(NewsEvent.id) >= min_news_count)
        .all()
    )
    return [
        {"stock_code": r.stock_code, "stock_name": r.stock_name, "news_count": r.news_count}
        for r in rows
    ]


def calculate_prediction_for_stock(
    db: Session, stock_code: str, market: str, target_date: date
) -> dict:
    """Calculate prediction for a stock (replicates prediction.py logic)."""
    cutoff = datetime.combine(target_date, datetime.max.time())
    news = (
        db.query(NewsEvent)
        .filter(
            NewsEvent.stock_code == stock_code,
            NewsEvent.market == market,
            NewsEvent.created_at <= cutoff,
        )
        .order_by(NewsEvent.created_at.desc())
        .limit(100)
        .all()
    )

    if not news:
        return {
            "stock_code": stock_code,
            "stock_name": None,
            "direction": "neutral",
            "score": 50.0,
            "confidence": 0.0,
            "news_count": 0,
        }

    avg_score = sum(n.news_score for n in news) / len(news)
    avg_sentiment = sum(n.sentiment_score for n in news) / len(news)
    prediction_score = min(100, max(0, avg_score * 0.6 + (avg_sentiment + 1) * 20))

    if prediction_score > 60:
        direction = "up"
    elif prediction_score < 40:
        direction = "down"
    else:
        direction = "neutral"

    volume_conf = min(1.0, len(news) / 20) * 0.5
    extremity_conf = abs(prediction_score - 50) / 100
    confidence = min(1.0, volume_conf + extremity_conf)

    return {
        "stock_code": stock_code,
        "stock_name": news[0].stock_name,
        "direction": direction,
        "score": round(prediction_score, 1),
        "confidence": round(confidence, 2),
        "news_count": len(news),
    }


async def run_verification(
    db: Session, target_date: date, market: str
) -> VerificationRunLog:
    """Main verification workflow."""
    start_time = datetime.now(UTC)
    run_log = VerificationRunLog(
        run_date=target_date, market=market, status="running"
    )
    db.add(run_log)
    db.commit()

    try:
        # Step 1: Get stocks with news
        stocks = get_stocks_with_news(db, target_date, market)
        if not stocks:
            run_log.status = "success"
            run_log.stocks_verified = 0
            run_log.duration_seconds = (datetime.now(UTC) - start_time).total_seconds()
            db.commit()
            return run_log

        # Step 2: Calculate predictions
        predictions = []
        for stock in stocks:
            pred = calculate_prediction_for_stock(
                db, stock["stock_code"], market, target_date
            )
            pred["stock_name"] = stock.get("stock_name")
            predictions.append(pred)

        # Step 3: Fetch actual prices
        stock_codes = [p["stock_code"] for p in predictions]
        actual_prices = await fetch_prices_batch(stock_codes, market, target_date)

        # Step 4: Save results + training snapshots
        verified = 0
        failed = 0
        for pred in predictions:
            price_data = actual_prices.get(pred["stock_code"])
            result = DailyPredictionResult(
                prediction_date=target_date,
                stock_code=pred["stock_code"],
                stock_name=pred["stock_name"],
                market=market,
                predicted_direction=pred["direction"],
                predicted_score=pred["score"],
                confidence=pred["confidence"],
                news_count=pred["news_count"],
            )
            if price_data:
                result.previous_close_price = price_data["previous_close"]
                result.actual_close_price = price_data["current_close"]
                result.actual_change_pct = price_data["change_pct"]
                result.actual_direction = get_direction_from_change(price_data["change_pct"])
                result.is_correct = pred["direction"] == result.actual_direction
                # OHLCV 확장 데이터
                result.actual_open_price = price_data.get("open")
                result.actual_high_price = price_data.get("high")
                result.actual_low_price = price_data.get("low")
                result.actual_volume = price_data.get("volume")
                result.previous_volume = price_data.get("previous_volume")
                if price_data.get("volume") and price_data.get("current_close"):
                    result.actual_trading_value = price_data["current_close"] * price_data["volume"]
                verified += 1
            else:
                result.error_message = "Price data unavailable"
                failed += 1
            db.add(result)

            # 학습 데이터 스냅샷 생성
            try:
                build_training_snapshot(
                    db=db,
                    stock_code=pred["stock_code"],
                    stock_name=pred["stock_name"],
                    market=market,
                    target_date=target_date,
                    prediction={
                        "direction": pred["direction"],
                        "score": pred["score"],
                        "confidence": pred["confidence"],
                    },
                )
            except Exception as e:
                logger.warning(
                    "Failed to build training snapshot for %s: %s",
                    pred["stock_code"],
                    e,
                )

        db.commit()

        # 학습 데이터 실제 결과 업데이트
        try:
            updated_count = update_training_actuals(db, target_date, market, actual_prices)
            db.commit()
            logger.info("Updated %d training data records with actuals", updated_count)
        except Exception as e:
            logger.warning("Failed to update training actuals: %s", e)

        # Step 5: Update run log
        duration = (datetime.now(UTC) - start_time).total_seconds()
        run_log.status = "success" if failed == 0 else "partial"
        run_log.stocks_verified = verified
        run_log.stocks_failed = failed
        run_log.duration_seconds = duration
        db.commit()
        return run_log

    except Exception as e:
        run_log.status = "failed"
        run_log.error_details = str(e)
        run_log.duration_seconds = (datetime.now(UTC) - start_time).total_seconds()
        db.commit()
        raise
