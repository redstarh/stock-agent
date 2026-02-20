"""학습 데이터 스냅샷 생성/업데이트/내보내기."""

import csv
import io
import logging
from datetime import date, datetime, timedelta, timezone

import pandas as pd
from sqlalchemy.orm import Session

from app.collectors.market_indicator_collector import MarketIndicatorCollector
from app.collectors.yfinance_middleware import download_with_retry
from app.models.news_event import NewsEvent
from app.models.training import StockTrainingData
from app.processing.price_fetcher import format_ticker
from app.processing.technical_indicators import (
    calc_market_index_change,
    compute_all_technical_indicators,
)

logger = logging.getLogger(__name__)

_market_collector = MarketIndicatorCollector()


def _fetch_news_features(
    db: Session,
    stock_code: str,
    market: str,
    target_date: date,
) -> dict:
    """예측 시점의 뉴스 피처 수집."""
    cutoff = datetime.combine(target_date, datetime.max.time())
    cutoff_30d = datetime.combine(target_date - timedelta(days=30), datetime.min.time())

    news = (
        db.query(NewsEvent)
        .filter(
            NewsEvent.stock_code == stock_code,
            NewsEvent.market == market,
            NewsEvent.created_at >= cutoff_30d,
            NewsEvent.created_at <= cutoff,
        )
        .order_by(NewsEvent.created_at.desc())
        .all()
    )

    if not news:
        return {
            "news_score": 0.0,
            "sentiment_score": 0.0,
            "news_count": 0,
            "news_count_3d": 0,
            "avg_score_3d": 0.0,
            "disclosure_ratio": 0.0,
            "sentiment_trend": 0.0,
            "theme": None,
        }

    avg_score = sum(n.news_score for n in news) / len(news)
    avg_sentiment = sum(n.sentiment_score for n in news) / len(news)

    # 최근 3일 vs 7일 뉴스
    cutoff_3d = datetime.combine(target_date - timedelta(days=3), datetime.min.time())
    cutoff_7d = datetime.combine(target_date - timedelta(days=7), datetime.min.time())

    news_3d = [n for n in news if n.created_at >= cutoff_3d]
    news_7d = [n for n in news if n.created_at >= cutoff_7d]

    avg_score_3d = sum(n.news_score for n in news_3d) / len(news_3d) if news_3d else avg_score
    avg_sentiment_3d = sum(n.sentiment_score for n in news_3d) / len(news_3d) if news_3d else avg_sentiment
    avg_sentiment_7d = sum(n.sentiment_score for n in news_7d) / len(news_7d) if news_7d else avg_sentiment

    # 공시 비율
    disclosure_count = sum(1 for n in news if getattr(n, "is_disclosure", False))
    disclosure_ratio = disclosure_count / len(news)

    # 주요 테마 (최빈)
    themes = [n.theme for n in news if getattr(n, "theme", None)]
    top_theme = max(set(themes), key=themes.count) if themes else None

    return {
        "news_score": round(avg_score, 2),
        "sentiment_score": round(avg_sentiment, 2),
        "news_count": len(news),
        "news_count_3d": len(news_3d),
        "avg_score_3d": round(avg_score_3d, 2),
        "disclosure_ratio": round(disclosure_ratio, 4),
        "sentiment_trend": round(avg_sentiment_3d - avg_sentiment_7d, 4),
        "theme": top_theme,
    }


def _fetch_price_features(
    stock_code: str,
    market: str,
    target_date: date,
) -> dict:
    """예측 시점의 주가 피처 수집 (yfinance)."""
    ticker = format_ticker(stock_code, market)
    start = target_date - timedelta(days=60)
    end = target_date + timedelta(days=1)

    try:
        df = download_with_retry(ticker, start=str(start), end=str(end))
        if df.empty or len(df) < 2:
            return {}

        closes = df["Close"]
        if isinstance(closes, pd.DataFrame):
            closes = closes.iloc[:, 0]
        closes = closes.dropna()

        volumes = df["Volume"]
        if isinstance(volumes, pd.DataFrame):
            volumes = volumes.iloc[:, 0]
        volumes = volumes.dropna()

        # 기본 주가 정보
        prev_close = float(closes.iloc[-1]) if len(closes) >= 1 else None
        prev_change_pct = None
        if len(closes) >= 2:
            p1, p2 = float(closes.iloc[-2]), float(closes.iloc[-1])
            prev_change_pct = round(((p2 - p1) / p1) * 100, 4) if p1 != 0 else None

        prev_volume = int(volumes.iloc[-1]) if len(volumes) >= 1 else None

        # 기술적 지표
        indicators = compute_all_technical_indicators(closes, volumes)

        return {
            "prev_close": prev_close,
            "prev_change_pct": prev_change_pct,
            "prev_volume": prev_volume,
            **indicators,
        }
    except Exception as e:
        logger.warning("Failed to fetch price features for %s: %s", stock_code, e)
        return {}


def build_training_snapshot(
    db: Session,
    stock_code: str,
    stock_name: str | None,
    market: str,
    target_date: date,
    prediction: dict,
) -> StockTrainingData:
    """예측 시점의 모든 피처를 수집하여 StockTrainingData 레코드 생성.

    Args:
        db: Database session
        stock_code: 종목 코드
        stock_name: 종목명
        market: 시장 (KR/US)
        target_date: 예측 대상 날짜
        prediction: {"direction": str, "score": float, "confidence": float}

    Returns:
        StockTrainingData 인스턴스 (DB에 저장됨)
    """
    # 뉴스 피처
    news_feat = _fetch_news_features(db, stock_code, market, target_date)

    # 주가 피처
    price_feat = _fetch_price_features(stock_code, market, target_date)

    # 시장 지수
    market_index_change = calc_market_index_change(market, target_date)

    # Tier 1 시장 지표 (market_return, vix_change)
    market_indicators = _market_collector.fetch_daily_indicators(target_date, market)

    record = StockTrainingData(
        prediction_date=target_date,
        stock_code=stock_code,
        stock_name=stock_name,
        market=market,
        # 뉴스 피처
        news_score=news_feat["news_score"],
        sentiment_score=news_feat["sentiment_score"],
        news_count=news_feat["news_count"],
        news_count_3d=news_feat["news_count_3d"],
        avg_score_3d=news_feat["avg_score_3d"],
        disclosure_ratio=news_feat["disclosure_ratio"],
        sentiment_trend=news_feat["sentiment_trend"],
        theme=news_feat["theme"],
        # 주가 피처
        prev_close=price_feat.get("prev_close"),
        prev_change_pct=price_feat.get("prev_change_pct"),
        prev_volume=price_feat.get("prev_volume"),
        price_change_5d=price_feat.get("price_change_5d"),
        volume_change_5d=price_feat.get("volume_change_5d"),
        ma5_ratio=price_feat.get("ma5_ratio"),
        ma20_ratio=price_feat.get("ma20_ratio"),
        volatility_5d=price_feat.get("volatility_5d"),
        rsi_14=price_feat.get("rsi_14"),
        bb_position=price_feat.get("bb_position"),
        # 시장 피처
        market_index_change=market_index_change,
        market_return=market_indicators.get("market_return"),
        vix_change=market_indicators.get("vix_change"),
        day_of_week=target_date.weekday(),
        # 예측 결과
        predicted_direction=prediction["direction"],
        predicted_score=prediction["score"],
        confidence=prediction["confidence"],
    )

    db.add(record)
    return record


def update_training_actuals(
    db: Session,
    target_date: date,
    market: str,
    price_data: dict[str, dict],
) -> int:
    """검증 후 실제 결과(라벨)를 업데이트.

    Args:
        db: Database session
        target_date: 예측 대상 날짜
        market: 시장 (KR/US)
        price_data: {stock_code: {"current_close", "change_pct", "volume", ...}}

    Returns:
        업데이트 건수
    """
    records = (
        db.query(StockTrainingData)
        .filter(
            StockTrainingData.prediction_date == target_date,
            StockTrainingData.market == market,
        )
        .all()
    )

    updated = 0
    for record in records:
        data = price_data.get(record.stock_code)
        if not data:
            continue

        record.actual_close = data.get("current_close")
        record.actual_change_pct = data.get("change_pct")
        record.actual_volume = data.get("volume")

        if record.actual_change_pct is not None:
            if record.actual_change_pct > 1.0:
                record.actual_direction = "up"
            elif record.actual_change_pct < -1.0:
                record.actual_direction = "down"
            else:
                record.actual_direction = "neutral"

            record.is_correct = record.predicted_direction == record.actual_direction

        updated += 1

    return updated


def export_training_csv(
    db: Session,
    market: str,
    start_date: date,
    end_date: date,
) -> str:
    """학습 데이터를 CSV 문자열로 내보내기.

    Args:
        db: Database session
        market: 시장 (KR/US)
        start_date: 시작 날짜
        end_date: 종료 날짜

    Returns:
        CSV 문자열
    """
    records = (
        db.query(StockTrainingData)
        .filter(
            StockTrainingData.market == market,
            StockTrainingData.prediction_date >= start_date,
            StockTrainingData.prediction_date <= end_date,
        )
        .order_by(
            StockTrainingData.prediction_date,
            StockTrainingData.stock_code,
        )
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    columns = [
        "prediction_date", "stock_code", "stock_name", "market",
        "news_score", "sentiment_score", "news_count", "news_count_3d",
        "avg_score_3d", "disclosure_ratio", "sentiment_trend", "theme",
        "prev_close", "prev_change_pct", "prev_volume",
        "price_change_5d", "volume_change_5d",
        "ma5_ratio", "ma20_ratio", "volatility_5d", "rsi_14", "bb_position",
        "market_index_change", "market_return", "vix_change", "day_of_week",
        "predicted_direction", "predicted_score", "confidence",
        "actual_close", "actual_change_pct", "actual_direction",
        "actual_volume", "is_correct",
    ]
    writer.writerow(columns)

    for r in records:
        writer.writerow([
            str(r.prediction_date),
            r.stock_code,
            r.stock_name or "",
            r.market,
            r.news_score,
            r.sentiment_score,
            r.news_count,
            r.news_count_3d,
            r.avg_score_3d,
            r.disclosure_ratio,
            r.sentiment_trend,
            r.theme or "",
            r.prev_close or "",
            r.prev_change_pct or "",
            r.prev_volume or "",
            r.price_change_5d or "",
            r.volume_change_5d or "",
            r.ma5_ratio or "",
            r.ma20_ratio or "",
            r.volatility_5d or "",
            r.rsi_14 or "",
            r.bb_position or "",
            r.market_index_change or "",
            r.market_return or "",
            r.vix_change or "",
            r.day_of_week,
            r.predicted_direction,
            r.predicted_score,
            r.confidence,
            r.actual_close or "",
            r.actual_change_pct or "",
            r.actual_direction or "",
            r.actual_volume or "",
            r.is_correct if r.is_correct is not None else "",
        ])

    return output.getvalue()
