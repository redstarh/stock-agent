"""뉴스 스코어링 엔진.

최종 점수 = Recency * W_R + Frequency * W_F + Sentiment * W_S + Disclosure * W_D

각 요소는 0-100 범위로 정규화.
가중치 및 파라미터는 docs/NewsCollectionScope.md에서 로드.
"""

import math
from datetime import UTC, datetime

from app.core.scope_loader import load_scope

# Scope에서 스코어링 설정 로드
_scope = load_scope()
_scoring_cfg = _scope.get("scoring", {})
_weights = _scoring_cfg.get("weights", {})

# 가중치
W_RECENCY = _weights.get("recency", 0.4)
W_FREQUENCY = _weights.get("frequency", 0.3)
W_SENTIMENT = _weights.get("sentiment", 0.2)
W_DISCLOSURE = _weights.get("disclosure", 0.1)

# Recency 반감기 (시간)
RECENCY_HALF_LIFE_HOURS = _scoring_cfg.get("recency_half_life_hours", 24.0)

# Frequency 상한 뉴스 건수
FREQUENCY_MAX_COUNT = _scoring_cfg.get("frequency_max_count", 50)


def calc_recency(
    published_at: datetime,
    reference: datetime | None = None,
) -> float:
    """뉴스 최신성 점수 (0-100).

    지수 감쇠 모델: score = 100 * 2^(-hours / half_life)
    """
    if reference is None:
        reference = datetime.now(UTC)

    # timezone-aware 변환
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=UTC)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)

    delta_hours = (reference - published_at).total_seconds() / 3600.0

    # 미래 시각 → 100으로 클램프
    if delta_hours < 0:
        return 100.0

    score = 100.0 * math.pow(2, -delta_hours / RECENCY_HALF_LIFE_HOURS)
    return round(max(0.0, min(100.0, score)), 2)


def calc_frequency(news_count: int) -> float:
    """뉴스 빈도 점수 (0-100).

    선형 스케일링: score = min(100, count / max_count * 100)
    """
    if news_count <= 0:
        return 0.0
    score = (news_count / FREQUENCY_MAX_COUNT) * 100.0
    return round(min(100.0, score), 2)


def calc_sentiment_score(sentiment: str, score: float) -> float:
    """감성 분석 점수 → 0-100 범위 변환.

    score(-1.0 ~ 1.0)를 0-100으로 선형 변환: result = (score + 1) * 50
    """
    normalized = (score + 1.0) * 50.0
    return round(max(0.0, min(100.0, normalized)), 2)


def calc_disclosure(is_disclosure: bool) -> float:
    """공시 보너스 (0 or 100)."""
    return 100.0 if is_disclosure else 0.0


def calc_news_score(
    recency: float,
    frequency: float,
    sentiment: float,
    disclosure: float,
) -> float:
    """최종 뉴스 스코어 (가중합, 0-100)."""
    score = (
        recency * W_RECENCY
        + frequency * W_FREQUENCY
        + sentiment * W_SENTIMENT
        + disclosure * W_DISCLOSURE
    )
    return round(max(0.0, min(100.0, score)), 2)
