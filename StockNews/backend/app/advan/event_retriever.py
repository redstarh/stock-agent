"""유사 이벤트 검색 — 과거 이벤트 패턴 매칭."""

import logging
from datetime import date, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.advan.models import AdvanEvent, AdvanLabel, AdvanPrediction

logger = logging.getLogger(__name__)


def _calculate_similarity(event: AdvanEvent, candidate: AdvanEvent) -> float:
    """두 이벤트 간 유사도 계산 (0~1).

    Args:
        event: 기준 이벤트
        candidate: 비교 이벤트

    Returns:
        유사도 점수 (0~1)
    """
    score = 0.0

    # 1. 이벤트 타입 일치 (50%)
    if event.event_type == candidate.event_type:
        score += 0.5

    # 2. 방향 일치 (20%)
    if event.direction == candidate.direction:
        score += 0.2

    # 3. 규모 유사도 (20%)
    magnitude_diff = abs(event.magnitude - candidate.magnitude)
    magnitude_sim = max(0, 1.0 - magnitude_diff)
    score += 0.2 * magnitude_sim

    # 4. 신뢰도 유사도 (10%)
    credibility_diff = abs(event.credibility - candidate.credibility)
    credibility_sim = max(0, 1.0 - credibility_diff)
    score += 0.1 * credibility_sim

    return score


def retrieve_similar_events(
    db: Session,
    event: AdvanEvent,
    policy_retrieval_config: dict,
    prediction_date: date,
) -> list[dict]:
    """유사한 과거 이벤트 검색.

    Args:
        db: DB 세션
        event: 기준 이벤트
        policy_retrieval_config: 검색 설정 (max_results, lookback_days, same_sector_only, similarity_threshold)
        prediction_date: 예측 기준일 (이 날짜 이전 이벤트만 검색)

    Returns:
        [
            {
                "event": AdvanEventResponse dict,
                "similarity": 0.85,
                "realized_ret": 3.2,  # optional
                "label": "Up",  # optional
            },
            ...
        ]
    """
    max_results = policy_retrieval_config.get("max_results", 3)
    lookback_days = policy_retrieval_config.get("lookback_days", 365)
    same_sector_only = policy_retrieval_config.get("same_sector_only", False)
    similarity_threshold = policy_retrieval_config.get("similarity_threshold", 0.5)

    # 검색 기간 계산 (prediction_date 이전)
    lookback_start = prediction_date - timedelta(days=lookback_days)

    # 후보 이벤트 조회 (시간 제약 STRICT — no future leakage!)
    query = db.query(AdvanEvent).filter(
        and_(
            AdvanEvent.event_type == event.event_type,  # 같은 이벤트 타입
            AdvanEvent.event_timestamp < prediction_date,  # 예측일 이전
            AdvanEvent.event_timestamp >= lookback_start,  # lookback 범위 내
            AdvanEvent.id != event.id,  # 자기 자신 제외
        )
    )

    # 같은 시장 필터 (선택적)
    if policy_retrieval_config.get("same_market_only", True):
        query = query.filter(AdvanEvent.market == event.market)

    # 같은 섹터 필터 (현재는 구현 안 됨 — 추후 확장)
    if same_sector_only:
        # TODO: sector 필드 추가 시 구현
        pass

    candidates = query.all()

    if not candidates:
        logger.debug(f"No candidates found for event_id={event.id}")
        return []

    # 유사도 계산 및 필터링
    scored_candidates = []
    for candidate in candidates:
        similarity = _calculate_similarity(event, candidate)
        if similarity >= similarity_threshold:
            scored_candidates.append((candidate, similarity))

    # 유사도 기준 내림차순 정렬
    scored_candidates.sort(key=lambda x: x[1], reverse=True)

    # 상위 N개 선택
    top_candidates = scored_candidates[:max_results]

    # 결과 구성 (실현 결과 조회)
    results = []
    for candidate, similarity in top_candidates:
        result_dict = {
            "event": {
                "id": candidate.id,
                "ticker": candidate.ticker,
                "stock_name": candidate.stock_name,
                "market": candidate.market,
                "event_type": candidate.event_type,
                "direction": candidate.direction,
                "magnitude": candidate.magnitude,
                "credibility": candidate.credibility,
                "title": candidate.title,
                "summary": candidate.summary,
                "event_timestamp": candidate.event_timestamp.isoformat(),
            },
            "similarity": round(similarity, 3),
        }

        # 해당 이벤트의 실현 결과 조회 (AdvanLabel)
        # AdvanLabel은 prediction_id로 연결되므로, 해당 이벤트의 예측을 찾아야 함
        related_prediction = (
            db.query(AdvanPrediction)
            .filter(AdvanPrediction.event_id == candidate.id)
            .first()
        )

        if related_prediction:
            label = (
                db.query(AdvanLabel)
                .filter(AdvanLabel.prediction_id == related_prediction.id)
                .first()
            )
            if label:
                result_dict["realized_ret"] = label.realized_ret
                result_dict["label"] = label.label

        results.append(result_dict)

    logger.debug(f"Retrieved {len(results)} similar events for event_id={event.id}")
    return results
