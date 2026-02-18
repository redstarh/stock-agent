"""LLM 기반 감성 분석.

AWS Bedrock Claude를 사용하여 뉴스의 감성(positive/neutral/negative)과
감성 점수(-1.0 ~ 1.0)를 분석.
"""

import json
import logging

from app.core.llm import call_llm

logger = logging.getLogger(__name__)


def _call_llm(text: str) -> dict:
    """Bedrock Claude 호출하여 감성 분석 결과 반환.

    Returns:
        {"sentiment": "positive"|"neutral"|"negative", "score": float, "confidence": float}
    """
    # 한국 금융 뉴스 특화 프롬프트 with few-shot examples
    system_prompt = """당신은 한국 금융 시장 전문 감성 분석가입니다.
뉴스 제목이나 본문의 주가 영향도를 분석하여 sentiment, score, confidence를 JSON으로 반환하세요.

## 감성 기준
- **positive**: 주가 상승 가능성이 높은 뉴스 (실적 개선, 수주 확대, 신제품 성공, 목표가 상향 등)
- **negative**: 주가 하락 가능성이 높은 뉴스 (실적 악화, 리콜, 소송 패소, 목표가 하향, 적자 지속 등)
- **neutral**: 주가에 중립적인 뉴스 (일상적 공시, 조직 개편, IR 행사 등)

## Score 범위
- positive: 0.3 ~ 1.0 (강도에 따라)
- neutral: -0.3 ~ 0.3
- negative: -1.0 ~ -0.3 (강도에 따라)

## Confidence (0.0 ~ 1.0)
- 명확한 실적/주가 키워드: 0.8 ~ 1.0
- 맥락상 유추 가능: 0.5 ~ 0.8
- 애매한 경우: 0.3 ~ 0.5

## Few-shot 예시

입력: "삼성전자 4분기 영업이익 10조원 돌파"
출력: {"sentiment": "positive", "score": 0.85, "confidence": 0.95}

입력: "SK하이닉스 메모리 반도체 가격 급락"
출력: {"sentiment": "negative", "score": -0.75, "confidence": 0.90}

입력: "현대차 CEO 교체 발표"
출력: {"sentiment": "neutral", "score": 0.0, "confidence": 0.70}

입력: "LG에너지솔루션 배터리 화재로 대규모 리콜"
출력: {"sentiment": "negative", "score": -0.95, "confidence": 0.98}

입력: "카카오 사명 변경 검토"
출력: {"sentiment": "neutral", "score": 0.05, "confidence": 0.60}

입력: "셀트리온 바이오시밀러 FDA 승인 획득"
출력: {"sentiment": "positive", "score": 0.80, "confidence": 0.92}

## 응답 형식
JSON만 반환하세요. 설명 없이 다음 형식으로:
{"sentiment": "positive"|"neutral"|"negative", "score": float, "confidence": float}"""

    response_text = call_llm(system_prompt, text)
    return json.loads(response_text)


def analyze_sentiment(text: str, body: str | None = None) -> dict:
    """뉴스 텍스트 감성 분석.

    Args:
        text: 뉴스 제목
        body: 뉴스 본문 (optional, 분석 정확도 향상)

    Returns:
        {"sentiment": str, "score": float, "confidence": float}
    """
    combined = text
    if body:
        combined = f"제목: {text}\n본문: {body[:2000]}"

    try:
        result = _call_llm(combined)

        # 결과 검증
        sentiment = result.get("sentiment", "neutral")
        if sentiment not in ("positive", "neutral", "negative"):
            sentiment = "neutral"

        score = float(result.get("score", 0.0))
        score = max(-1.0, min(1.0, score))  # clamp

        confidence = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))  # clamp

        return {"sentiment": sentiment, "score": score, "confidence": confidence}

    except Exception as e:
        logger.warning("Sentiment analysis failed, fallback to neutral: %s", e)
        return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
