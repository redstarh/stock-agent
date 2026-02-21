#!/usr/bin/env python3
"""Historical data backfill script.

Collects historical news (DART, Finnhub), stock prices (yfinance),
runs verification pipeline for each business day, and generates
training data + theme strength.

Usage:
    cd backend
    .venv/bin/python scripts/historical_backfill.py --start-date 2026-02-01
    .venv/bin/python scripts/historical_backfill.py --start-date 2026-02-01 --end-date 2026-02-20
"""

import argparse
import asyncio
import logging
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.news_event import NewsEvent
from app.models.stock_price import StockPrice
from app.models.theme_strength import ThemeStrength
from app.models.training import StockTrainingData
from app.models.verification import (
    DailyPredictionResult,
    ThemePredictionAccuracy,
)
from app.processing.theme_aggregator import aggregate_theme_accuracy
from app.processing.verification_engine import run_verification
from app.scoring.engine import (
    calc_disclosure,
    calc_frequency,
    calc_news_score,
    calc_recency,
    calc_sentiment_score,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backfill")

# ============================================================
# Stock Lists
# ============================================================

KR_STOCKS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("005380", "현대차"),
    ("035420", "NAVER"),
    ("035720", "카카오"),
    ("373220", "LG에너지솔루션"),
    ("068270", "셀트리온"),
    ("207940", "삼성바이오로직스"),
    ("000270", "기아"),
    ("005490", "POSCO홀딩스"),
]

US_STOCKS = [
    ("AAPL", "Apple"),
    ("MSFT", "Microsoft"),
    ("GOOGL", "Alphabet"),
    ("AMZN", "Amazon"),
    ("NVDA", "NVIDIA"),
    ("TSLA", "Tesla"),
    ("META", "Meta Platforms"),
    ("JPM", "JPMorgan Chase"),
    ("V", "Visa"),
    ("JNJ", "Johnson & Johnson"),
]

# ============================================================
# Keyword-based Sentiment Analysis (no LLM)
# ============================================================

_POS_KR = ["상승", "호재", "급등", "신고가", "호실적", "수주", "흑자", "증가", "개선", "사상최대", "상향"]
_NEG_KR = ["하락", "악재", "급락", "적자", "리콜", "소송", "감소", "부진", "철회", "폭락", "하향"]
_POS_EN = ["surge", "rally", "beat", "record", "growth", "profit", "gain", "rise", "upgrade", "strong", "soar"]
_NEG_EN = ["crash", "decline", "miss", "loss", "drop", "fall", "downgrade", "weak", "cut", "plunge", "slump"]


def _simple_sentiment(title: str, market: str) -> tuple[str, float]:
    """Keyword-based sentiment for backfill (no LLM cost)."""
    if market == "KR":
        pos = sum(1 for k in _POS_KR if k in title)
        neg = sum(1 for k in _NEG_KR if k in title)
    else:
        t = title.lower()
        pos = sum(1 for k in _POS_EN if k in t)
        neg = sum(1 for k in _NEG_EN if k in t)

    if pos > neg:
        return "positive", min(0.8, 0.3 + pos * 0.15)
    if neg > pos:
        return "negative", max(-0.8, -0.3 - neg * 0.15)
    return "neutral", 0.0


# ============================================================
# Phase 1: News Collection
# ============================================================

async def collect_dart_news(start_date: date, end_date: date) -> list[dict]:
    """Collect DART disclosures day by day."""
    from app.collectors.dart import DartCollector

    if not settings.dart_api_key:
        logger.warning("DART API key not set — skipping DART collection")
        return []

    collector = DartCollector(api_key=settings.dart_api_key)
    all_items: list[dict] = []
    current = start_date

    while current <= end_date:
        # Skip weekends (DART doesn't publish)
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        date_str = current.strftime("%Y%m%d")
        logger.info("DART: collecting %s", date_str)
        try:
            items = await collector.collect(begin_date=date_str)
            all_items.extend(items)
            logger.info("  -> %d disclosures", len(items))
        except Exception as e:
            logger.warning("  DART failed for %s: %s", date_str, e)

        current += timedelta(days=1)
        await asyncio.sleep(0.5)  # Rate-limit courtesy

    logger.info("DART total: %d items", len(all_items))
    return all_items


async def collect_finnhub_news(start_date: date, end_date: date) -> list[dict]:
    """Collect Finnhub company news for top US stocks."""
    from app.collectors.finnhub import FinnhubCollector

    if not settings.finnhub_api_key:
        logger.warning("Finnhub API key not set — skipping Finnhub collection")
        return []

    collector = FinnhubCollector()
    all_items: list[dict] = []
    from_str = start_date.strftime("%Y-%m-%d")
    to_str = end_date.strftime("%Y-%m-%d")

    for symbol, name in US_STOCKS:
        logger.info("Finnhub: %s (%s ~ %s)", symbol, from_str, to_str)
        try:
            items = await collector.collect_company_news(symbol, from_str, to_str)
            for item in items:
                item["stock_name"] = name
            all_items.extend(items)
            logger.info("  -> %d articles", len(items))
        except Exception as e:
            logger.warning("  Finnhub failed for %s: %s", symbol, e)
        await asyncio.sleep(1.2)  # Finnhub free tier: 60 calls/min

    logger.info("Finnhub total: %d items", len(all_items))
    return all_items


# ============================================================
# Phase 2: News Storage (simplified pipeline, no LLM)
# ============================================================

def store_news_items(db: Session, items: list[dict], market: str) -> int:
    """Store collected news with keyword-based analysis."""
    from app.processing.stock_mapper import code_to_name
    from app.processing.theme_classifier import classify_theme

    saved = 0
    skipped = 0

    for item in items:
        source_url = item.get("source_url", "")
        if not source_url:
            continue

        # Duplicate check
        exists = (
            db.query(NewsEvent.id)
            .filter(NewsEvent.source_url == source_url)
            .first()
        )
        if exists:
            skipped += 1
            continue

        title = item.get("title", "")
        stock_code = item.get("stock_code", "")
        stock_name = item.get("stock_name", "")

        if not stock_name and stock_code:
            if market == "KR":
                stock_name = code_to_name(stock_code)
            else:
                stock_name = dict(US_STOCKS).get(stock_code, "")

        # Parse published_at
        published_at = item.get("published_at")
        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at)
            except (ValueError, TypeError):
                published_at = None
        if published_at is None:
            published_at = datetime.now(UTC)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=UTC)

        # Keyword-based analysis
        sentiment, sentiment_score = _simple_sentiment(title, market)
        themes = classify_theme(title)
        theme = ",".join(themes) if themes else None
        is_disclosure = item.get("is_disclosure", False)

        # Score calculation (reference = same day + 12h for fair recency)
        reference_time = published_at + timedelta(hours=12)
        recency = calc_recency(published_at, reference=reference_time)
        frequency = calc_frequency(1)
        sent_score = calc_sentiment_score(sentiment, sentiment_score)
        disc_score = calc_disclosure(is_disclosure)
        news_score = calc_news_score(recency, frequency, sent_score, disc_score)

        event = NewsEvent(
            market=market,
            stock_code=stock_code,
            stock_name=stock_name,
            title=title,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            news_score=news_score,
            source=item.get("source", "backfill"),
            source_url=source_url,
            theme=theme,
            is_disclosure=is_disclosure,
            published_at=published_at,
            # CRITICAL: set created_at = published_at
            # so verification engine's date-based queries work correctly
            created_at=published_at,
        )

        try:
            db.add(event)
            db.flush()
            saved += 1
        except Exception as e:
            db.rollback()
            logger.debug("Duplicate or error: %s", e)

    db.commit()
    logger.info(
        "News stored: %d saved, %d skipped (market=%s)", saved, skipped, market
    )
    return saved


# ============================================================
# Phase 3: Stock Price Collection
# ============================================================

def collect_stock_prices(db: Session, start_date: date, end_date: date) -> int:
    """Bulk-download stock prices via yfinance and store in stock_price."""
    import yfinance as yf

    all_stocks = (
        [(code, "KR") for code, _ in KR_STOCKS]
        + [(code, "US") for code, _ in US_STOCKS]
    )
    saved = 0

    for stock_code, market in all_stocks:
        ticker = f"{stock_code}.KS" if market == "KR" else stock_code
        logger.info("Prices: %s (%s)", ticker, market)

        try:
            yf_ticker = yf.Ticker(ticker)
            hist = yf_ticker.history(
                start=str(start_date - timedelta(days=7)),
                end=str(end_date + timedelta(days=1)),
            )

            if hist.empty:
                logger.warning("  No price data for %s", ticker)
                continue

            for i, (idx, row) in enumerate(hist.iterrows()):
                price_date = idx.date() if hasattr(idx, "date") else idx

                # Skip if already exists
                exists = (
                    db.query(StockPrice.id)
                    .filter(
                        StockPrice.stock_code == stock_code,
                        StockPrice.date == price_date,
                    )
                    .first()
                )
                if exists:
                    continue

                # Calculate daily change %
                change_pct = 0.0
                if i > 0:
                    prev_close = float(hist.iloc[i - 1]["Close"])
                    curr_close = float(row["Close"])
                    if prev_close > 0:
                        change_pct = round(
                            ((curr_close - prev_close) / prev_close) * 100, 4
                        )

                price = StockPrice(
                    stock_code=stock_code,
                    market=market,
                    date=price_date,
                    close_price=float(row["Close"]),
                    change_pct=change_pct,
                    volume=int(row["Volume"]) if row["Volume"] > 0 else 0,
                )
                db.add(price)
                saved += 1

            db.commit()
            logger.info("  -> %d rows from %s", len(hist), ticker)

        except Exception as e:
            logger.warning("  Price failed for %s: %s", ticker, e)
            db.rollback()

    logger.info("Stock prices stored: %d records", saved)
    return saved


# ============================================================
# Phase 4: Verification & Training Data
# ============================================================

async def run_daily_verifications(
    db: Session, start_date: date, end_date: date
) -> dict:
    """Run verification for each business day × market."""
    results = {"success": 0, "failed": 0, "skipped": 0}
    current = start_date

    while current <= end_date:
        # Skip weekends
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        for market in ["KR", "US"]:
            # Ensure clean session state before each iteration
            try:
                db.rollback()
            except Exception:
                pass

            # Skip if already done
            try:
                exists = (
                    db.query(DailyPredictionResult.id)
                    .filter(
                        DailyPredictionResult.prediction_date == current,
                        DailyPredictionResult.market == market,
                    )
                    .first()
                )
                if exists:
                    logger.info("Skip: %s %s (already verified)", current, market)
                    results["skipped"] += 1
                    continue
            except Exception:
                db.rollback()

            logger.info("Verify: %s %s", current, market)
            try:
                run_log = await run_verification(db, current, market)
                status = run_log.status
                verified = run_log.stocks_verified or 0
                logger.info(
                    "  -> %s: %d stocks verified", status, verified
                )

                # Aggregate theme accuracy for this date
                try:
                    aggregate_theme_accuracy(db, current, market)
                except Exception as e:
                    logger.warning("  Theme agg failed: %s", e)
                    db.rollback()

                results["success"] += 1

            except Exception as e:
                logger.error("  Verification FAILED: %s", e)
                db.rollback()
                results["failed"] += 1

        current += timedelta(days=1)

    return results


# ============================================================
# Phase 5: Theme Strength Generation
# ============================================================

def generate_theme_strength(
    db: Session, start_date: date, end_date: date
) -> int:
    """Aggregate daily theme strength from news_event."""
    saved = 0
    current = start_date

    while current <= end_date:
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        for market in ["KR", "US"]:
            day_start = datetime.combine(current, datetime.min.time(), tzinfo=UTC)
            day_end = datetime.combine(current, datetime.max.time(), tzinfo=UTC)

            news = (
                db.query(NewsEvent)
                .filter(
                    NewsEvent.market == market,
                    NewsEvent.published_at >= day_start,
                    NewsEvent.published_at <= day_end,
                )
                .all()
            )

            if not news:
                continue

            # Aggregate by theme
            theme_data: dict[str, dict] = {}
            for n in news:
                if not n.theme:
                    continue
                for t in n.theme.split(","):
                    t = t.strip()
                    if not t:
                        continue
                    if t not in theme_data:
                        theme_data[t] = {"scores": [], "sentiments": []}
                    theme_data[t]["scores"].append(n.news_score)
                    theme_data[t]["sentiments"].append(n.sentiment_score)

            for theme, data in theme_data.items():
                # Skip if already exists
                exists = (
                    db.query(ThemeStrength.id)
                    .filter(
                        ThemeStrength.date == current,
                        ThemeStrength.market == market,
                        ThemeStrength.theme == theme,
                    )
                    .first()
                )
                if exists:
                    continue

                scores = data["scores"]
                sentiments = data["sentiments"]
                strength = ThemeStrength(
                    date=current,
                    market=market,
                    theme=theme,
                    strength_score=round(sum(scores) / len(scores), 2),
                    news_count=len(scores),
                    sentiment_avg=round(
                        sum(sentiments) / len(sentiments), 4
                    ),
                )
                db.add(strength)
                saved += 1

            db.commit()

        current += timedelta(days=1)

    logger.info("Theme strength: %d records generated", saved)
    return saved


# ============================================================
# Main
# ============================================================

async def main(start_date: date, end_date: date):
    logger.info("=" * 60)
    logger.info("HISTORICAL BACKFILL: %s ~ %s", start_date, end_date)
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        # ---- Phase 1: Collect News ----
        logger.info("\n=== Phase 1: Collecting historical news ===")
        dart_items = await collect_dart_news(start_date, end_date)
        finnhub_items = await collect_finnhub_news(start_date, end_date)

        # ---- Phase 2: Store News ----
        logger.info("\n=== Phase 2: Storing news items ===")
        kr_saved = store_news_items(db, dart_items, "KR")
        us_saved = store_news_items(db, finnhub_items, "US")

        # ---- Phase 3: Stock Prices ----
        logger.info("\n=== Phase 3: Collecting stock prices ===")
        prices_saved = collect_stock_prices(db, start_date, end_date)

        # ---- Phase 4: Verification + Training Data ----
        logger.info("\n=== Phase 4: Running daily verification ===")
        verify = await run_daily_verifications(db, start_date, end_date)

        # ---- Phase 5: Theme Strength ----
        logger.info("\n=== Phase 5: Generating theme strength ===")
        theme_count = generate_theme_strength(db, start_date, end_date)

        # ---- Summary ----
        total_news = db.query(func.count(NewsEvent.id)).scalar()
        total_prices = db.query(func.count(StockPrice.id)).scalar()
        total_pred = db.query(func.count(DailyPredictionResult.id)).scalar()
        total_train = db.query(func.count(StockTrainingData.id)).scalar()
        total_theme = db.query(func.count(ThemeStrength.id)).scalar()
        total_theme_acc = db.query(func.count(ThemePredictionAccuracy.id)).scalar()

        logger.info("\n" + "=" * 60)
        logger.info("BACKFILL COMPLETE")
        logger.info("=" * 60)
        logger.info("New records this run:")
        logger.info("  KR news stored   : %d", kr_saved)
        logger.info("  US news stored   : %d", us_saved)
        logger.info("  Stock prices     : %d", prices_saved)
        logger.info("  Verification     : success=%d, failed=%d, skipped=%d",
                     verify["success"], verify["failed"], verify["skipped"])
        logger.info("  Theme strength   : %d", theme_count)
        logger.info("")
        logger.info("Total DB state:")
        logger.info("  news_event              : %d", total_news)
        logger.info("  stock_price             : %d", total_prices)
        logger.info("  daily_prediction_result : %d", total_pred)
        logger.info("  stock_training_data     : %d", total_train)
        logger.info("  theme_strength          : %d", total_theme)
        logger.info("  theme_prediction_acc    : %d", total_theme_acc)

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Historical data backfill")
    parser.add_argument(
        "--start-date",
        default="2026-02-01",
        help="Start date (YYYY-MM-DD), default: 2026-02-01",
    )
    parser.add_argument(
        "--end-date",
        default="2026-02-20",
        help="End date (YYYY-MM-DD), default: 2026-02-20",
    )
    args = parser.parse_args()

    asyncio.run(
        main(
            date.fromisoformat(args.start_date),
            date.fromisoformat(args.end_date),
        )
    )
