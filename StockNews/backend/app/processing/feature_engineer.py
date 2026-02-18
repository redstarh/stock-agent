"""뉴스 + 주가 데이터 기반 ML 피처 엔지니어링."""

from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.collectors.price_collector import PriceCollector, fetch_recent_price_change
from app.models.news_event import NewsEvent


def extract_news_features(
    stock_code: str, db: Session, days: int = 30
) -> dict[str, float]:
    """뉴스 피처 추출.

    Args:
        stock_code: 종목 코드
        db: Database session
        days: 조회 기간 (일)

    Returns:
        {
            "news_score": float,
            "sentiment_score": float,
            "news_count": int,
            "avg_score_3d": float,
            "disclosure_ratio": float,
        }
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # 전체 기간 뉴스
    news = (
        db.query(NewsEvent)
        .filter(
            NewsEvent.stock_code == stock_code, NewsEvent.created_at >= cutoff_date
        )
        .order_by(NewsEvent.created_at.desc())
        .all()
    )

    if not news:
        return {
            "news_score": 0.0,
            "sentiment_score": 0.0,
            "news_count": 0,
            "avg_score_3d": 0.0,
            "disclosure_ratio": 0.0,
        }

    # 전체 평균
    avg_score = sum(n.news_score for n in news) / len(news)
    avg_sentiment = sum(n.sentiment_score for n in news) / len(news)

    # 최근 3일 평균
    recent_3d = datetime.now(timezone.utc) - timedelta(days=3)
    recent_news = [n for n in news if n.created_at >= recent_3d]
    avg_score_3d = (
        sum(n.news_score for n in recent_news) / len(recent_news)
        if recent_news
        else avg_score
    )

    # 공시 비율
    disclosure_count = sum(1 for n in news if n.is_disclosure)
    disclosure_ratio = disclosure_count / len(news) if news else 0.0

    return {
        "news_score": round(avg_score, 2),
        "sentiment_score": round(avg_sentiment, 2),
        "news_count": len(news),
        "avg_score_3d": round(avg_score_3d, 2),
        "disclosure_ratio": round(disclosure_ratio, 2),
    }


def extract_price_features(
    stock_code: str, collector: Optional[PriceCollector] = None
) -> dict[str, float]:
    """주가 피처 추출.

    Args:
        stock_code: 종목 코드
        collector: PriceCollector 인스턴스

    Returns:
        {
            "price_change_pct": float,
            "volume_change_pct": float,
            "moving_average_ratio": float,
        }
    """
    price_data = fetch_recent_price_change(stock_code, days=5, collector=collector)

    return {
        "price_change_pct": price_data.get("change_pct", 0.0),
        "volume_change_pct": price_data.get("volume_change_pct", 0.0),
        "moving_average_ratio": price_data.get("ma_ratio", 1.0),
    }


def build_feature_vector(
    stock_code: str, db: Session, collector: Optional[PriceCollector] = None
) -> dict[str, float]:
    """종목의 전체 피처 벡터 생성.

    Args:
        stock_code: 종목 코드
        db: Database session
        collector: PriceCollector 인스턴스

    Returns:
        Combined feature dictionary with all ML features
    """
    logger.info(f"Building feature vector for {stock_code}")

    news_features = extract_news_features(stock_code, db, days=30)
    price_features = extract_price_features(stock_code, collector)

    features = {**news_features, **price_features}
    logger.debug(f"Features for {stock_code}: {features}")

    return features


def prepare_training_data(
    stock_codes: list[str],
    db: Session,
    collector: Optional[PriceCollector] = None,
) -> tuple[list[list[float]], list[str], list[str]]:
    """여러 종목의 학습 데이터 준비.

    Args:
        stock_codes: 종목 코드 리스트
        db: Database session
        collector: PriceCollector 인스턴스

    Returns:
        (features, labels, stock_codes) tuple
        - features: [[news_score, sentiment, count, score_3d, disclosure_ratio,
                      price_change, volume_change, ma_ratio], ...]
        - labels: ["up", "down", ...] based on price_change_pct
        - stock_codes: corresponding stock codes
    """
    features_list = []
    labels = []
    valid_codes = []

    for code in stock_codes:
        features = build_feature_vector(code, db, collector)

        # Feature vector 생성
        feature_vec = [
            features["news_score"],
            features["sentiment_score"],
            float(features["news_count"]),
            features["avg_score_3d"],
            features["disclosure_ratio"],
            features["price_change_pct"],
            features["volume_change_pct"],
            features["moving_average_ratio"],
        ]

        # Label: price_change_pct 기반
        # > 2% → up, < -2% → down, else → neutral
        price_change = features["price_change_pct"]
        if price_change > 2.0:
            label = "up"
        elif price_change < -2.0:
            label = "down"
        else:
            label = "neutral"

        features_list.append(feature_vec)
        labels.append(label)
        valid_codes.append(code)

    logger.info(f"Prepared training data for {len(valid_codes)} stocks")
    return features_list, labels, valid_codes
