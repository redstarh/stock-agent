"""LLM 기반 뉴스 요약.

뉴스 제목과 본문을 요약하여 핵심 정보를 추출.
"""

import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_SUMMARY_LENGTH = 200  # 최대 요약 글자 수


def _call_llm_summary(title: str, body: str | None = None) -> str:
    """OpenAI API로 뉴스 요약 생성."""
    import openai

    client = openai.OpenAI(api_key=settings.openai_api_key)

    content = f"제목: {title}"
    if body:
        content += f"\n본문: {body[:1000]}"  # 본문 1000자 제한

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Korean financial news summarizer. "
                    "Summarize the given news into 1-2 sentences in Korean. "
                    "Focus on: what happened, which company/stock, and potential market impact. "
                    f"Keep under {MAX_SUMMARY_LENGTH} characters. "
                    'Return JSON: {"summary": "요약 텍스트"}'
                ),
            },
            {"role": "user", "content": content},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    summary = result.get("summary", "")
    return summary[:MAX_SUMMARY_LENGTH]


def summarize_news(title: str, body: str | None = None) -> str:
    """뉴스 요약 생성.

    Args:
        title: 뉴스 제목
        body: 뉴스 본문 (optional)

    Returns:
        요약 문자열 (최대 200자). 실패 시 빈 문자열.
    """
    try:
        return _call_llm_summary(title, body)
    except Exception as e:
        logger.warning("Summary generation failed, returning empty: %s", e)
        return ""
