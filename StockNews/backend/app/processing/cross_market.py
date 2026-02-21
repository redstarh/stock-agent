"""US 뉴스의 한국 시장 영향 분석 (Bedrock Claude)."""

import json
import logging

from app.core.llm import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 글로벌 금융시장 분석 전문가입니다.
미국 뉴스가 한국 주식시장의 특정 테마/섹터에 미치는 영향을 분석합니다.

한국 주식시장 테마 목록:
AI, 반도체, 2차전지, 바이오, 자동차, 조선, 방산, 로봇, 금융, 엔터, 게임, 에너지, 부동산, 통신, 철강, 항공

분석 결과를 JSON 배열로 반환하세요. 영향이 없으면 빈 배열 []을 반환하세요.
각 항목: {"theme": "테마명", "impact": 0.0~1.0, "direction": "up"|"down"|"neutral"}
- impact: 영향 강도 (0.0: 무영향, 1.0: 매우 강한 영향)
- direction: 한국 해당 테마에 대한 방향성

중요: JSON 배열만 반환하세요. 다른 텍스트는 포함하지 마세요."""


def analyze_kr_impact(title: str, body: str | None = None) -> list[dict]:
    """US 뉴스의 한국 시장 영향 분석."""
    content = title
    if body:
        content += "\n\n" + body[:1000]

    user_message = f"다음 미국 뉴스가 한국 주식시장 테마에 미치는 영향을 분석하세요:\n\n{content}"

    try:
        result = call_llm(SYSTEM_PROMPT, user_message)
        impacts = json.loads(result)

        validated = []
        for item in impacts:
            if not isinstance(item, dict):
                continue
            theme = item.get("theme", "")
            impact = float(item.get("impact", 0))
            direction = item.get("direction", "neutral")
            if theme and 0 <= impact <= 1 and direction in ("up", "down", "neutral"):
                validated.append({
                    "theme": theme,
                    "impact": round(impact, 2),
                    "direction": direction,
                })

        return validated
    except Exception as e:
        logger.warning("Cross-market analysis failed: %s", e)
        return []
