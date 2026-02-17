"""LLM 기반 감성 분석.

OpenAI API를 사용하여 뉴스의 감성(positive/neutral/negative)과
감성 점수(-1.0 ~ 1.0)를 분석.
"""

import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def _call_llm(text: str) -> dict:
    """OpenAI API 호출하여 감성 분석 결과 반환.

    Returns:
        {"sentiment": "positive"|"neutral"|"negative", "score": float}
    """
    import openai

    client = openai.OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial news sentiment analyzer. "
                    "Analyze the sentiment of the given news text. "
                    "Return JSON: {\"sentiment\": \"positive\"|\"neutral\"|\"negative\", \"score\": float(-1.0 to 1.0)}"
                ),
            },
            {"role": "user", "content": text},
        ],
        temperature=0,
    )

    content = response.choices[0].message.content
    return json.loads(content)


def analyze_sentiment(text: str) -> dict:
    """뉴스 텍스트 감성 분석.

    Returns:
        {"sentiment": str, "score": float}
    """
    try:
        result = _call_llm(text)

        # 결과 검증
        sentiment = result.get("sentiment", "neutral")
        if sentiment not in ("positive", "neutral", "negative"):
            sentiment = "neutral"

        score = float(result.get("score", 0.0))
        score = max(-1.0, min(1.0, score))  # clamp

        return {"sentiment": sentiment, "score": score}

    except Exception as e:
        logger.warning("Sentiment analysis failed, fallback to neutral: %s", e)
        return {"sentiment": "neutral", "score": 0.0}
