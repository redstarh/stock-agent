"""LLM 기반 뉴스 요약.

뉴스 제목과 본문을 요약하여 핵심 정보를 추출.
"""

import json
import logging

from app.core.llm import call_llm

logger = logging.getLogger(__name__)

MAX_SUMMARY_LENGTH = 200  # 최대 요약 글자 수


def _call_llm_summary(title: str, body: str | None = None) -> str:
    """Bedrock Claude로 뉴스 요약 생성."""
    content = f"제목: {title}"
    if body:
        content += f"\n본문: {body[:1000]}"  # 본문 1000자 제한

    system_prompt = (
        "You are a Korean financial news summarizer. "
        "Summarize the given news into 1-2 sentences in Korean. "
        "Focus on: what happened, which company/stock, and potential market impact. "
        f"Keep under {MAX_SUMMARY_LENGTH} characters. "
        'Return JSON: {"summary": "요약 텍스트"}'
    )

    response_text = call_llm(system_prompt, content)
    result = json.loads(response_text)
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


def auto_summarize_event(event) -> str | None:
    """NewsEvent에 대해 자동 요약 생성 및 저장.

    Args:
        event: NewsEvent 인스턴스

    Returns:
        생성된 요약 문자열. 콘텐츠가 없으면 None. 실패 시 빈 문자열.
    """
    if not event.content or not event.content.strip():
        return None

    try:
        summary = summarize_news(event.title, event.content)
        event.summary = summary
        return summary
    except Exception as e:
        logger.warning("Auto-summarize failed for event %s: %s", event.id, e)
        event.summary = ""
        return ""
