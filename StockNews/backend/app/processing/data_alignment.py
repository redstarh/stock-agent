"""뉴스↔주가 데이터 정렬 및 피처 엔지니어링."""

from datetime import date, timedelta
from collections import defaultdict


def _classify_direction(change_pct: float) -> str:
    """주가 변동률 → 방향 분류."""
    if change_pct > 0.5:
        return "up"
    elif change_pct < -0.5:
        return "down"
    return "neutral"


def _find_next_trading_day(
    news_date: date,
    price_lookup: dict[tuple[str, date], dict],
    stock_code: str,
    max_days: int = 5,
) -> dict | None:
    """뉴스 날짜 다음 거래일(주가 데이터 존재일) 찾기."""
    for offset in range(1, max_days + 1):
        candidate = news_date + timedelta(days=offset)
        key = (stock_code, candidate)
        if key in price_lookup:
            return price_lookup[key]
    return None


def align_news_and_prices(
    news_events: list[dict], stock_prices: list[dict]
) -> list[dict]:
    """뉴스 이벤트를 다음 거래일 주가 변동과 정렬.

    각 뉴스에 대해 다음 거래일 주가를 찾아 매칭합니다.
    Returns: stock_code, news_date, news_score, sentiment_score,
             price_date, change_pct, direction
    """
    # 주가 데이터를 (stock_code, date) → dict 로 인덱싱
    price_lookup: dict[tuple[str, date], dict] = {}
    for p in stock_prices:
        key = (p["stock_code"], p["date"])
        price_lookup[key] = p

    aligned = []
    for news in news_events:
        stock_code = news["stock_code"]
        news_date = news["news_date"]

        price = _find_next_trading_day(news_date, price_lookup, stock_code)
        if price is None:
            continue

        aligned.append(
            {
                "stock_code": stock_code,
                "news_date": news_date,
                "news_score": news["news_score"],
                "sentiment_score": news["sentiment_score"],
                "price_date": price["date"],
                "change_pct": price["change_pct"],
                "direction": _classify_direction(price["change_pct"]),
            }
        )

    return aligned


def build_feature_dataset(
    aligned_data: list[dict],
) -> tuple[list[list[float]], list[str]]:
    """정렬된 데이터를 피처 벡터 + 라벨로 변환.

    Features (4차원): [news_score, sentiment_score, news_count_same_day, avg_score_3d]
    Labels: "up" / "down" / "neutral"
    """
    if not aligned_data:
        return [], []

    # 같은 종목+날짜별 뉴스 수 계산
    day_counts: dict[tuple[str, date], int] = defaultdict(int)
    day_scores: dict[tuple[str, date], list[float]] = defaultdict(list)
    for item in aligned_data:
        key = (item["stock_code"], item["news_date"])
        day_counts[key] += 1
        day_scores[key].append(item["news_score"])

    # 종목별 날짜 순서로 정렬하여 3일 이동평균 계산
    by_stock: dict[str, list[dict]] = defaultdict(list)
    for item in aligned_data:
        by_stock[item["stock_code"]].append(item)

    for stock_items in by_stock.values():
        stock_items.sort(key=lambda x: x["news_date"])

    features = []
    labels = []

    for item in aligned_data:
        stock_code = item["stock_code"]
        news_date = item["news_date"]

        # 피처 1: news_score
        news_score = item["news_score"]

        # 피처 2: sentiment_score
        sentiment_score = item["sentiment_score"]

        # 피처 3: 같은 날 같은 종목 뉴스 수
        news_count = day_counts[(stock_code, news_date)]

        # 피처 4: 최근 3일 평균 스코어
        recent_scores = []
        for d_offset in range(4):  # 오늘 포함 3일 전까지
            d = news_date - timedelta(days=d_offset)
            key = (stock_code, d)
            if key in day_scores:
                recent_scores.extend(day_scores[key])
        avg_score_3d = sum(recent_scores) / len(recent_scores) if recent_scores else news_score

        features.append([news_score, sentiment_score, float(news_count), avg_score_3d])
        labels.append(item["direction"])

    return features, labels
