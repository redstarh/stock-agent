"""ML Feature Configuration — Tier 정의 및 피처 메타데이터.

Metadata-only module. 피처 계산 로직 없음. 이름과 그룹 정의만.
"""

TIER_1_FEATURES = [
    "news_score", "sentiment_score", "rsi_14",
    "prev_change_pct", "price_change_5d", "volume_change_5d",
    "market_return", "vix_change",
]

TIER_2_FEATURES = TIER_1_FEATURES + [
    "news_count_3d", "avg_score_3d", "sentiment_trend",
    "ma5_ratio", "volatility_5d",
    "usd_krw_change", "has_earnings_disclosure", "cross_theme_score",
]

TIER_3_FEATURES = TIER_2_FEATURES + [
    "foreign_net_ratio", "sector_index_change",
    "disclosure_ratio", "bb_position",
]

# Features removed with documented rationale
REMOVED_FEATURES = {
    "prev_close": "절대값, 방향 무관 (Fama & French 1993)",
    "prev_volume": "절대값, 종목 크기만 반영",
    "individual_net_buy": "선형 종속 (= -(foreign+institution))",
    "stochastic_k": "RSI와 중복 (r~0.6)",
    "stochastic_d": "RSI와 중복",
    "nasdaq_change": "S&P500과 r~0.9",
    "news_acceleration": "2차 도함수 = 노이즈 증폭",
    "news_velocity_1h": "1h 윈도우 극단적 노이즈",
    "days_to_month_end": "방향 무관 연속값",
    "day_of_week": "정수 인코딩 오류, is_monday가 나음",
    "market_index_change": "market_return으로 대체",
    "atr_14": "volatility_5d와 중복 (r~0.7)",
    "ma60_ratio": "1일 예측에 너무 느림",
    "is_friday": "효과 미입증",
    "is_month_end": "효과 < 0.3%",
    "is_quarter_end": "연 4회, 학습 불가",
    "gold_change": "주식과 불안정 관계",
    "crude_oil_change": "에너지 섹터만 유효",
}


def get_features_for_tier(tier: int) -> list[str]:
    """주어진 Tier의 피처 목록 반환."""
    if tier == 1:
        return list(TIER_1_FEATURES)
    elif tier == 2:
        return list(TIER_2_FEATURES)
    elif tier == 3:
        return list(TIER_3_FEATURES)
    raise ValueError(f"Invalid tier: {tier}")


def get_min_samples_for_tier(tier: int) -> int:
    """Tier별 최소 필요 샘플 수.

    N/10 이론 최소값보다 높은 실전 임계값 적용.
    TimeSeriesSplit CV 안정성 + 과적합 방지 목적.
    """
    thresholds = {1: 200, 2: 500, 3: 1000}
    if tier not in thresholds:
        raise ValueError(f"Invalid tier: {tier}")
    return thresholds[tier]


def get_feature_count_for_tier(tier: int) -> int:
    """Tier별 피처 수."""
    return len(get_features_for_tier(tier))
