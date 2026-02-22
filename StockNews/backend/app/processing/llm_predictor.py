"""LLM 기반 주가 예측 — 예측 컨텍스트를 참고하여 예측."""

import json
import logging
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.llm import call_llm
from app.models.news_event import NewsEvent
from app.processing.prediction_context_builder import DEFAULT_CONTEXT_PATH
from app.processing.verification_engine import calculate_prediction_for_stock
from app.schemas.prediction_context import LLMPredictionResponse

logger = logging.getLogger(__name__)


def _load_context(context_path: str | None = None) -> dict | None:
    """예측 컨텍스트 JSON 파일 로드."""
    path = context_path or DEFAULT_CONTEXT_PATH
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Failed to load prediction context from %s: %s", path, e)
        return None


def _build_system_prompt(context: dict) -> str:
    """시스템 프롬프트 생성."""
    days = context.get("analysis_days", 30)
    overall = context.get("overall_accuracy", 0)
    total = context.get("total_predictions", 0)

    # Theme table
    themes = context.get("theme_predictability", [])
    theme_lines = []
    for t in themes[:10]:  # Top 10
        theme_lines.append(
            f"  - {t['theme']}: 정확도 {t['accuracy']}%, "
            f"예측 가능성 {t['predictability']} ({t['total']}건)"
        )
    theme_table = "\n".join(theme_lines) if theme_lines else "  (데이터 없음)"

    # Sentiment ranges
    sentiments = context.get("sentiment_ranges", [])
    sentiment_lines = []
    for s in sentiments:
        sentiment_lines.append(
            f"  - {s['range_label']}: 상승 {s['up_ratio']*100:.0f}%, "
            f"하락 {s['down_ratio']*100:.0f}% ({s['total']}건)"
        )
    sentiment_text = "\n".join(sentiment_lines) if sentiment_lines else "  (데이터 없음)"

    # News count effect
    news_effects = context.get("news_count_effect", [])
    news_lines = []
    for n in news_effects:
        news_lines.append(
            f"  - {n['range_label']}건: 정확도 {n['accuracy']}% ({n['total']}건)"
        )
    news_text = "\n".join(news_lines) if news_lines else "  (데이터 없음)"

    # Failure patterns
    failures = context.get("failure_patterns", [])
    failure_lines = []
    for f in failures:
        failure_lines.append(f"  - {f['description']}")
    failure_text = "\n".join(failure_lines) if failure_lines else "  (특이 패턴 없음)"

    return f"""당신은 한국 금융 시장 주가 방향 예측 전문가입니다.
뉴스 데이터와 과거 예측 정확도 분석 결과를 바탕으로 종목의 단기(1일) 주가 방향을 예측합니다.

## 예측 컨텍스트 (과거 {days}일 분석 결과)
### 전체 정확도: {overall}% ({total}건)
### 테마별 예측 정확도:
{theme_table}
### 감성 점수별 실제 방향 분포:
{sentiment_text}
### 뉴스 건수별 정확도:
{news_text}
### 주의해야 할 실패 패턴:
{failure_text}

## 예측 규칙
1. 과거 정확도가 낮은 방향의 예측은 신뢰도를 낮추세요
2. 테마별 예측 가능성을 고려하세요
3. 감성 점수의 실제 방향 분포를 참고하여 보정하세요
4. 뉴스 건수가 적으면 신뢰도를 낮추세요
5. 자주 틀리는 패턴에 해당하면 반대 방향도 고려하세요

## 응답 형식 (반드시 JSON)
{{"direction": "up|down|neutral", "score": 0-100, "confidence": 0.0-1.0, "reasoning": "한국어 예측 근거"}}"""


def _build_user_message(
    db: Session, stock_code: str, market: str, heuristic: dict,
    target_date: date | None = None,
) -> str:
    """유저 메시지 생성 — 종목 뉴스 데이터 + Heuristic 결과."""
    target_date = target_date or date.today()
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
        return f"종목 {stock_code}에 대한 뉴스가 없습니다."

    stock_name = news[0].stock_name or stock_code
    news_count = len(news)
    avg_score = sum(n.news_score for n in news) / news_count
    avg_sentiment = sum(n.sentiment_score for n in news) / news_count

    # 3-day trend
    three_days_ago = target_date - timedelta(days=3)
    cutoff_3d = datetime.combine(three_days_ago, datetime.min.time())
    recent = [n for n in news if n.created_at >= cutoff_3d]
    older = [n for n in news if n.created_at < cutoff_3d]
    if recent and older:
        recent_avg = sum(n.sentiment_score for n in recent) / len(recent)
        older_avg = sum(n.sentiment_score for n in older) / len(older)
        trend = round(recent_avg - older_avg, 3)
    else:
        trend = 0.0

    # Theme distribution
    themes = {}
    for n in news:
        if n.theme:
            themes[n.theme] = themes.get(n.theme, 0) + 1
    theme_text = ", ".join(f"{t}({c}건)" for t, c in sorted(themes.items(), key=lambda x: -x[1])[:5])

    # Disclosure ratio
    disclosure_count = sum(1 for n in news if n.is_disclosure)
    disclosure_ratio = round(disclosure_count / news_count, 2) if news_count > 0 else 0.0

    # Recent titles (top 5)
    recent_titles = [n.title for n in news[:5]]
    titles_text = "\n".join(f"  - {t}" for t in recent_titles)

    return f"""## 종목 정보
- 종목코드: {stock_code}
- 종목명: {stock_name}
- 시장: {market}

## 뉴스 데이터
- 뉴스 건수: {news_count}건
- 평균 뉴스 스코어: {avg_score:.1f}
- 평균 감성 점수: {avg_sentiment:.3f}
- 3일 감성 추세: {trend:+.3f}
- 주요 테마: {theme_text or '없음'}
- 공시 비율: {disclosure_ratio:.0%}

## 최근 뉴스 제목
{titles_text}

## Heuristic 예측 결과 (참고용)
- 방향: {heuristic['direction']}
- 점수: {heuristic['score']}
- 신뢰도: {heuristic['confidence']}

위 데이터를 기반으로 해당 종목의 단기(1일) 주가 방향을 예측해주세요."""


def _parse_llm_response(text: str) -> dict:
    """LLM 응답 텍스트를 파싱."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from the response text
        import re
        match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise ValueError(f"Cannot parse LLM response: {text[:200]}") from None

    direction = data.get("direction", "neutral")
    if direction not in ("up", "down", "neutral"):
        direction = "neutral"

    score = float(data.get("score", 50.0))
    score = max(0.0, min(100.0, score))

    confidence = float(data.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))

    reasoning = data.get("reasoning", "")

    return {
        "direction": direction,
        "score": round(score, 1),
        "confidence": round(confidence, 2),
        "reasoning": reasoning,
    }


def predict_with_llm(
    db: Session,
    stock_code: str,
    market: str = "KR",
    context_path: str | None = None,
    target_date: date | None = None,
    context_dict: dict | None = None,
) -> LLMPredictionResponse:
    """LLM을 사용한 주가 예측.

    Args:
        db: SQLAlchemy session
        stock_code: 종목 코드
        market: 시장 (KR/US)
        context_path: 컨텍스트 JSON 파일 경로
        target_date: 예측 대상 날짜 (기본값: 오늘)
        context_dict: 컨텍스트 딕셔너리 (context_path보다 우선)

    Returns:
        LLMPredictionResponse
    """
    # Step 1: Get heuristic prediction as baseline
    target_date = target_date or date.today()
    heuristic = calculate_prediction_for_stock(db, stock_code, market, target_date)

    # Step 2: Load context (context_dict takes priority over file)
    context = context_dict if context_dict is not None else _load_context(context_path)

    # Step 3: If no context, fallback to heuristic
    if context is None:
        logger.info(
            "No prediction context available, falling back to heuristic for %s",
            stock_code,
        )
        return LLMPredictionResponse(
            stock_code=stock_code,
            stock_name=heuristic.get("stock_name"),
            method="heuristic_fallback",
            direction=heuristic["direction"],
            prediction_score=heuristic["score"],
            confidence=heuristic["confidence"],
            reasoning="예측 컨텍스트 파일 없음 — Heuristic 결과 사용",
            heuristic_direction=heuristic["direction"],
            heuristic_score=heuristic["score"],
        )

    # Step 4: Build prompts
    system_prompt = _build_system_prompt(context)
    user_message = _build_user_message(db, stock_code, market, heuristic, target_date=target_date)

    # Step 5: Call LLM
    try:
        llm_text = call_llm(system_prompt, user_message)
        parsed = _parse_llm_response(llm_text)

        return LLMPredictionResponse(
            stock_code=stock_code,
            stock_name=heuristic.get("stock_name"),
            method="llm",
            direction=parsed["direction"],
            prediction_score=parsed["score"],
            confidence=parsed["confidence"],
            reasoning=parsed["reasoning"],
            heuristic_direction=heuristic["direction"],
            heuristic_score=heuristic["score"],
            context_version=context.get("version"),
            based_on_days=context.get("analysis_days"),
        )

    except Exception as e:
        logger.error("LLM prediction failed for %s: %s", stock_code, e)
        return LLMPredictionResponse(
            stock_code=stock_code,
            stock_name=heuristic.get("stock_name"),
            method="heuristic_fallback",
            direction=heuristic["direction"],
            prediction_score=heuristic["score"],
            confidence=heuristic["confidence"],
            reasoning=f"LLM 호출 실패 — Heuristic 결과 사용 ({e})",
            heuristic_direction=heuristic["direction"],
            heuristic_score=heuristic["score"],
        )
