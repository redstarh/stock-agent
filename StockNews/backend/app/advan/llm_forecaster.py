"""LLM 기반 확률적 예측기.

구조화된 이벤트 입력 → 확률 출력(P(up), P(down), P(flat)) + 근거 + 조건.
기존 core.llm.call_llm()을 활용하여 Bedrock Claude 호출.
"""

import json
import logging
import math
import re
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.advan.models import AdvanEvent, AdvanFeatureDaily, AdvanPrediction
from app.core.llm import call_llm

logger = logging.getLogger(__name__)

# 기본 시스템 프롬프트 (고정 규칙)
SYSTEM_PROMPT_TEMPLATE = """당신은 한국/미국 주식시장의 뉴스·공시 이벤트를 분석하여 주가 방향을 확률로 예측하는 금융 AI입니다.

## 절대 규칙
1. **시간 누수 금지**: 입력된 이벤트 timestamp 이후의 정보는 절대 사용하지 마세요.
2. **근거 의무**: 예측 근거는 반드시 입력 필드를 참조해야 합니다.
3. **확률 합 = 1**: p_up + p_down + p_flat = 1.0 (소수점 2자리)
4. **유사사례**: 과거 사례만 참조 가능합니다.
5. **ABSTAIN 허용**: 불확실하면 Abstain(유보)을 선택하세요. 무리한 예측보다 낫습니다.

## 이벤트 유형별 사전 가중치 (Priors)
{event_priors}

## 결정 규칙
- 매수(buy): p_up >= {buy_p}
- 매도(sell): p_down >= {sell_p}
- 유보(skip): max(p_up, p_down) < {abstain_high} 이거나 |p_up - p_down| < {abstain_band}
- 그 외: hold

## 예측 기간
- Horizon: T+{horizon} 거래일
- 라벨 기준: 수익률 > +{label_threshold}% → Up, < -{label_threshold}% → Down, 그 외 → Flat

## 출력 형식 (반드시 JSON)
```json
{{
  "prediction": "Up|Down|Flat|Abstain",
  "p_up": 0.00,
  "p_down": 0.00,
  "p_flat": 0.00,
  "trade_action": "buy|sell|hold|skip",
  "position_size": 0.0,
  "top_drivers": [
    {{"feature": "이벤트/지표명", "sign": "+|-", "weight": 0.0, "evidence": "근거 설명"}}
  ],
  "invalidators": ["이 조건이면 예측 무효"],
  "reasoning": "종합 판단 근거 (2-3문장)"
}}
```"""


def _build_system_prompt(policy_params: dict, horizon: int) -> str:
    """정책 파라미터로 시스템 프롬프트 구성."""
    priors = policy_params.get("event_priors", {})
    thresholds = policy_params.get("thresholds", {})

    priors_text = "\n".join(
        f"- {k}: 영향력 가중치 {v}" for k, v in priors.items()
    )

    abstain_band = thresholds.get("abstain_high", 0.6) - thresholds.get("abstain_low", 0.4)

    return SYSTEM_PROMPT_TEMPLATE.format(
        event_priors=priors_text or "- 기본값 적용",
        buy_p=thresholds.get("buy_p", 0.62),
        sell_p=thresholds.get("sell_p", 0.62),
        abstain_high=thresholds.get("abstain_high", 0.6),
        abstain_band=f"{abstain_band:.2f}",
        horizon=horizon,
        label_threshold=thresholds.get("label_threshold_pct", 2.0),
    )


def _build_user_message(
    ticker: str,
    events: list[AdvanEvent],
    features: AdvanFeatureDaily | None,
    similar_events: list[dict] | None,
) -> str:
    """사용자 메시지 구성: 이벤트 + 피처 + 유사사례."""
    parts = []

    # 1. 종목 이벤트
    parts.append(f"## 종목: {ticker}")
    if events:
        parts.append(f"### 관련 이벤트 ({len(events)}건)")
        for i, evt in enumerate(events, 1):
            parts.append(
                f"{i}. [{evt.event_type}] {evt.title}\n"
                f"   - 방향: {evt.direction} | 규모: {evt.magnitude:.2f} | "
                f"신뢰도: {evt.credibility:.2f}\n"
                f"   - 시각: {evt.event_timestamp.isoformat()} | "
                f"장후: {'예' if evt.is_after_market else '아니오'}\n"
                f"   - 출처: {evt.source} | 공시: {'예' if evt.is_disclosure else '아니오'}"
            )
            if evt.summary:
                parts.append(f"   - 요약: {evt.summary[:200]}")
    else:
        parts.append("### 관련 이벤트: 없음")

    # 2. 시장 피처
    if features:
        parts.append("\n### 시장 피처")
        parts.append(
            f"- 1일 수익률: {features.ret_1d:.2f}%" if features.ret_1d is not None else "- 1일 수익률: N/A"
        )
        parts.append(
            f"- 3일 수익률: {features.ret_3d:.2f}%" if features.ret_3d is not None else "- 3일 수익률: N/A"
        )
        parts.append(
            f"- 5일 수익률: {features.ret_5d:.2f}%" if features.ret_5d is not None else "- 5일 수익률: N/A"
        )
        parts.append(
            f"- 20일 변동성: {features.volatility_20d:.2f}%"
            if features.volatility_20d is not None
            else "- 20일 변동성: N/A"
        )
        if features.market_ret is not None:
            parts.append(f"- 시장 수익률: {features.market_ret:.2f}%")

    # 3. 유사 과거 사례
    if similar_events:
        parts.append(f"\n### 유사 과거 사례 ({len(similar_events)}건)")
        for i, sim in enumerate(similar_events, 1):
            evt_data = sim.get("event", {})
            parts.append(
                f"{i}. [{evt_data.get('event_type', '?')}] {evt_data.get('title', '?')[:80]}\n"
                f"   - 유사도: {sim.get('similarity', 0):.2f} | "
                f"실현 수익률: {sim.get('realized_ret', 'N/A')}% | "
                f"결과: {sim.get('label', 'N/A')}"
            )

    parts.append("\n위 정보를 바탕으로 JSON 형식으로 예측해 주세요.")
    return "\n".join(parts)


def _parse_llm_response(raw: str) -> dict:
    """LLM 응답을 JSON으로 파싱. 실패 시 기본값 반환."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # JSON 블록 추출 시도
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    logger.warning("Failed to parse LLM response, returning Abstain")
    return {
        "prediction": "Abstain",
        "p_up": 0.33,
        "p_down": 0.33,
        "p_flat": 0.34,
        "trade_action": "skip",
        "position_size": 0.0,
        "top_drivers": [],
        "invalidators": ["LLM 응답 파싱 실패"],
        "reasoning": "LLM 응답을 파싱할 수 없어 유보 처리",
    }


def _validate_probabilities(result: dict) -> dict:
    """확률 합 = 1.0 검증 및 보정."""
    p_up = float(result.get("p_up", 0.33))
    p_down = float(result.get("p_down", 0.33))
    p_flat = float(result.get("p_flat", 0.34))

    total = p_up + p_down + p_flat
    if total > 0 and abs(total - 1.0) > 0.01:
        p_up /= total
        p_down /= total
        p_flat /= total

    result["p_up"] = round(p_up, 4)
    result["p_down"] = round(p_down, 4)
    result["p_flat"] = round(1.0 - round(p_up, 4) - round(p_down, 4), 4)

    # prediction 유효성 검증
    valid_predictions = {"Up", "Down", "Flat", "Abstain"}
    if result.get("prediction") not in valid_predictions:
        # 확률 기반으로 결정
        max_p = max(p_up, p_down, p_flat)
        if max_p == p_up:
            result["prediction"] = "Up"
        elif max_p == p_down:
            result["prediction"] = "Down"
        else:
            result["prediction"] = "Flat"

    # trade_action 유효성 검증
    valid_actions = {"buy", "sell", "hold", "skip"}
    if result.get("trade_action") not in valid_actions:
        result["trade_action"] = "skip"

    # position_size 범위 제한
    result["position_size"] = max(0.0, min(1.0, float(result.get("position_size", 0.0))))

    return result


def predict_stock(
    db: Session,
    ticker: str,
    events: list[AdvanEvent],
    features: AdvanFeatureDaily | None,
    similar_events: list[dict] | None,
    policy_params: dict,
    horizon: int = 3,
) -> dict:
    """단일 종목에 대한 LLM 확률 예측.

    Args:
        db: DB 세션
        ticker: 종목코드
        events: 해당 종목의 이벤트 목록
        features: 시장 피처 (없으면 None)
        similar_events: 유사 과거 사례
        policy_params: 정책 파라미터 dict
        horizon: 예측 기간 (T+N)

    Returns:
        예측 결과 dict (prediction, p_up, p_down, p_flat, ...)
    """
    system_prompt = _build_system_prompt(policy_params, horizon)
    user_message = _build_user_message(ticker, events, features, similar_events)

    try:
        raw_response = call_llm(system_prompt, user_message)
        result = _parse_llm_response(raw_response)
        result = _validate_probabilities(result)

        # Abstain 결정: 정책 임계값 기반
        thresholds = policy_params.get("thresholds", {})
        abstain_high = thresholds.get("abstain_high", 0.6)
        max_directional = max(result["p_up"], result["p_down"])
        if max_directional < abstain_high and result["prediction"] != "Abstain":
            result["prediction"] = "Abstain"
            result["trade_action"] = "skip"
            result["position_size"] = 0.0

        return result

    except Exception as e:
        logger.error("LLM prediction failed for %s: %s", ticker, e)
        return {
            "prediction": "Abstain",
            "p_up": 0.33,
            "p_down": 0.33,
            "p_flat": 0.34,
            "trade_action": "skip",
            "position_size": 0.0,
            "top_drivers": [],
            "invalidators": [f"LLM 호출 실패: {str(e)[:100]}"],
            "reasoning": f"LLM 호출 중 오류 발생: {str(e)[:200]}",
        }


def predict_stock_heuristic(
    events: list[AdvanEvent],
    features: AdvanFeatureDaily | None,
    policy_params: dict,
) -> dict:
    """LLM 없이 규칙 기반 예측 (폴백/비교 기준).

    이벤트 방향성과 규모, 신뢰도를 기반으로 단순 확률 추정.
    """
    if not events:
        return {
            "prediction": "Flat",
            "p_up": 0.25,
            "p_down": 0.25,
            "p_flat": 0.50,
            "trade_action": "skip",
            "position_size": 0.0,
            "top_drivers": [],
            "invalidators": ["이벤트 없음"],
            "reasoning": "관련 이벤트가 없어 Flat 추정",
        }

    priors = policy_params.get("event_priors", {})

    # 방향별 가중 점수 합산
    positive_score = 0.0
    negative_score = 0.0
    total_weight = 0.0

    for evt in events:
        weight = priors.get(evt.event_type, 0.3) * evt.credibility * evt.magnitude
        total_weight += weight
        if evt.direction == "positive":
            positive_score += weight
        elif evt.direction == "negative":
            negative_score += weight
        else:  # mixed/unknown
            positive_score += weight * 0.3
            negative_score += weight * 0.3

    if total_weight == 0:
        total_weight = 1.0

    # 확률 변환 (sigmoid-like)
    net_score = (positive_score - negative_score) / total_weight
    # net_score: -1 ~ +1 범위

    base_flat = 0.35
    if net_score > 0:
        p_up = base_flat + (1 - base_flat) * min(net_score, 1.0) * 0.6
        p_down = (1 - base_flat - p_up + base_flat) * 0.3
        p_flat = 1.0 - p_up - p_down
    elif net_score < 0:
        p_down = base_flat + (1 - base_flat) * min(-net_score, 1.0) * 0.6
        p_up = (1 - base_flat - p_down + base_flat) * 0.3
        p_flat = 1.0 - p_up - p_down
    else:
        p_up = 0.30
        p_down = 0.30
        p_flat = 0.40

    # 범위 보정
    p_up = max(0.05, min(0.90, p_up))
    p_down = max(0.05, min(0.90, p_down))
    p_flat = max(0.05, 1.0 - p_up - p_down)
    total = p_up + p_down + p_flat
    p_up /= total
    p_down /= total
    p_flat /= total

    # 결정
    thresholds = policy_params.get("thresholds", {})
    buy_p = thresholds.get("buy_p", 0.62)
    sell_p = thresholds.get("sell_p", 0.62)

    if p_up >= buy_p:
        prediction = "Up"
        action = "buy"
        size = min(1.0, (p_up - 0.5) * 2)
    elif p_down >= sell_p:
        prediction = "Down"
        action = "sell"
        size = min(1.0, (p_down - 0.5) * 2)
    elif max(p_up, p_down) < thresholds.get("abstain_high", 0.6):
        prediction = "Abstain"
        action = "skip"
        size = 0.0
    else:
        prediction = "Flat"
        action = "hold"
        size = 0.0

    drivers = []
    for evt in events[:3]:
        drivers.append({
            "feature": f"{evt.event_type}: {evt.title[:50]}",
            "sign": "+" if evt.direction == "positive" else "-" if evt.direction == "negative" else "?",
            "weight": round(priors.get(evt.event_type, 0.3) * evt.credibility, 2),
            "evidence": f"방향={evt.direction}, 규모={evt.magnitude:.2f}, 신뢰도={evt.credibility:.2f}",
        })

    return {
        "prediction": prediction,
        "p_up": round(p_up, 4),
        "p_down": round(p_down, 4),
        "p_flat": round(p_flat, 4),
        "trade_action": action,
        "position_size": round(size, 4),
        "top_drivers": drivers,
        "invalidators": [],
        "reasoning": f"규칙 기반 예측: 순점수={net_score:.2f}, 이벤트 {len(events)}건 분석",
    }


def predict_stock_heuristic_v2(
    events: list[AdvanEvent],
    features: AdvanFeatureDaily | None,
    policy_params: dict,
    prediction_date: date | None = None,
) -> dict:
    """LLM 없이 규칙 기반 예측 v2 (향상된 폴백).

    v1 대비 개선사항:
    - Enhanced event-type priors with research-based multipliers
    - Novelty weighting
    - Time decay
    - Market session bonus
    - Credibility boost
    - Event deduplication at prediction time
    - Softmax-like probability transform
    """
    if not events:
        return {
            "prediction": "Flat",
            "p_up": 0.25,
            "p_down": 0.25,
            "p_flat": 0.50,
            "trade_action": "skip",
            "position_size": 0.0,
            "top_drivers": [],
            "invalidators": ["이벤트 없음"],
            "reasoning": "v2 규칙 기반 예측: 관련 이벤트가 없어 Flat 추정",
        }

    priors = policy_params.get("event_priors", {})

    # Event-type prior multipliers (research-based)
    type_multipliers = {
        "실적": 1.5,
        "M&A": 1.5,
        "경영권": 1.3,
        "가이던스": 1.3,
        "규제": 1.2,
        "수주": 1.1,
    }

    # Event deduplication: group by (ticker, event_type), keep highest magnitude
    dedup_map = {}
    for evt in events:
        key = (evt.ticker, evt.event_type)
        if key not in dedup_map or evt.magnitude > dedup_map[key].magnitude:
            dedup_map[key] = evt

    deduped_events = list(dedup_map.values())

    # 방향별 가중 점수 합산
    positive_score = 0.0
    negative_score = 0.0
    total_weight = 0.0

    # Use prediction_date for time decay in backtesting, fall back to now for live
    if prediction_date is not None:
        ref_dt = datetime.combine(prediction_date, datetime.min.time(), tzinfo=UTC)
    else:
        ref_dt = datetime.now(UTC)

    for evt in deduped_events:
        # Base weight from policy priors
        base_prior = priors.get(evt.event_type, 0.3)

        # Apply type multiplier
        multiplier = type_multipliers.get(evt.event_type, 1.0)
        prior = base_prior * multiplier

        weight = prior * evt.credibility * evt.magnitude

        # Novelty weighting
        weight *= (0.5 + evt.novelty)

        # Time decay (handle naive/aware datetime mismatch)
        evt_ts = evt.event_timestamp
        if evt_ts.tzinfo is None:
            evt_ts = evt_ts.replace(tzinfo=UTC)
        days_ago = max(0, (ref_dt - evt_ts).days)
        decay = math.exp(-0.5 * days_ago)
        weight *= decay

        # Market session bonus
        if evt.is_after_market:
            weight *= 1.2

        # Credibility boost
        if evt.credibility >= 0.8:
            weight *= 1.3

        total_weight += weight
        if evt.direction == "positive":
            positive_score += weight
        elif evt.direction == "negative":
            negative_score += weight
        else:  # mixed/unknown
            # Instead of adding equally to both sides (which cancels out),
            # add a small net contribution based on magnitude
            # High magnitude mixed events slightly lean positive (corporate action bias)
            if evt.magnitude > 0.5:
                positive_score += weight * 0.4
                negative_score += weight * 0.2
            else:
                positive_score += weight * 0.3
                negative_score += weight * 0.3

    # Feature-based momentum signal (mild, breaks ties for low-evidence cases)
    feature_signal = 0.0
    if features is not None:
        # Use available price features for momentum
        if features.ret_1d is not None:
            # ret_1d is already a return value, use it directly
            feature_signal = max(-0.3, min(0.3, features.ret_1d * 5))  # cap at ±0.3
        elif features.market_ret is not None:
            feature_signal = max(-0.2, min(0.2, features.market_ret * 3))

    # Add feature signal as weak evidence
    if abs(feature_signal) > 0.01:
        feature_weight = 0.3  # weak contribution
        if feature_signal > 0:
            positive_score += feature_weight * abs(feature_signal)
        else:
            negative_score += feature_weight * abs(feature_signal)
        total_weight += feature_weight * abs(feature_signal)

    if total_weight == 0:
        total_weight = 1.0

    # Direction from normalized score (-1 to 1)
    direction_score = (positive_score - negative_score) / total_weight

    # Evidence confidence: more events with higher total weight = more confident
    # Sigmoid saturation: total_weight=1 → 0.39, tw=2 → 0.63, tw=3 → 0.78
    evidence_confidence = 1 - math.exp(-total_weight * 0.5)

    # Net score combines direction and evidence strength
    net_score = direction_score * evidence_confidence

    # Softmax probability transform (scale=2.0 for better spread)
    scale = 2.0
    exp_up = math.exp(scale * net_score)
    exp_down = math.exp(-scale * net_score)
    exp_flat = math.exp(0)  # =1.0
    total_exp = exp_up + exp_down + exp_flat
    p_up = exp_up / total_exp
    p_down = exp_down / total_exp
    p_flat = exp_flat / total_exp

    # 결정
    thresholds = policy_params.get("thresholds", {})
    buy_p = thresholds.get("buy_p", 0.62)
    sell_p = thresholds.get("sell_p", 0.62)

    if p_up >= buy_p:
        prediction = "Up"
        action = "buy"
        size = min(1.0, (p_up - 0.5) * 2)
    elif p_down >= sell_p:
        prediction = "Down"
        action = "sell"
        size = min(1.0, (p_down - 0.5) * 2)
    elif max(p_up, p_down) < thresholds.get("abstain_high", 0.6):
        prediction = "Abstain"
        action = "skip"
        size = 0.0
    else:
        prediction = "Flat"
        action = "hold"
        size = 0.0

    drivers = []
    for evt in deduped_events[:3]:
        drivers.append({
            "feature": f"{evt.event_type}: {evt.title[:50]}",
            "sign": "+" if evt.direction == "positive" else "-" if evt.direction == "negative" else "?",
            "weight": round(priors.get(evt.event_type, 0.3) * evt.credibility, 2),
            "evidence": f"방향={evt.direction}, 규모={evt.magnitude:.2f}, 신뢰도={evt.credibility:.2f}, novelty={evt.novelty:.2f}",
        })

    return {
        "prediction": prediction,
        "p_up": round(p_up, 4),
        "p_down": round(p_down, 4),
        "p_flat": round(p_flat, 4),
        "trade_action": action,
        "position_size": round(size, 4),
        "top_drivers": drivers,
        "invalidators": [],
        "reasoning": f"v2 규칙 기반 예측: 순점수={net_score:.2f}, 증거강도={evidence_confidence:.2f}, 중복제거 후 이벤트 {len(deduped_events)}건 분석",
    }
