"""LLM 기반 테마 분류기 (Bedrock Claude).

키워드 매칭 대신 Claude를 사용하여 정확한 테마 분류.
"""

import json
import logging

from app.core.llm import call_llm

logger = logging.getLogger(__name__)

THEME_LIST = [
    "AI", "반도체", "2차전지", "바이오", "자동차", "조선", "방산",
    "로봇", "금융", "엔터", "게임", "에너지", "부동산", "통신", "철강", "항공",
]

SYSTEM_PROMPT = f"""당신은 한국 주식시장 뉴스 테마 분류 전문가입니다.
뉴스 제목과 본문을 읽고 관련된 투자 테마를 분류합니다.

사용 가능한 테마 목록:
{", ".join(THEME_LIST)}

규칙:
1. 뉴스 내용과 직접적으로 관련된 테마만 선택하세요.
2. 단순히 키워드가 포함되었다고 선택하지 마세요. 뉴스의 핵심 주제를 파악하세요.
3. 종목명이나 회사명만으로 테마를 유추하지 마세요. 뉴스 내용 기반으로 판단하세요.
4. 관련 테마가 없으면 빈 배열 []을 반환하세요.
5. 최대 2개까지만 선택하세요.
6. JSON 배열만 반환하세요. 예: ["반도체", "AI"] 또는 []

예시:
- "삼성전자, HBM3E 양산 시작" → ["반도체"]
- "현대차 전기차 신모델 출시" → ["자동차"]
- "삼성전자주가 19만원 넘었다" → []  (주가 변동 자체는 특정 테마 아님)
- "카카오, 신작 게임 매출 급증" → ["게임"]
- "SK하이닉스 AI 반도체 수주 확대" → ["AI", "반도체"]"""


def classify_theme_llm(
    title: str,
    body: str | None = None,
    *,
    model_id: str = "",
) -> list[str]:
    """LLM으로 뉴스 테마 분류.

    Args:
        title: 뉴스 제목
        body: 뉴스 본문 (선택)
        model_id: 사용할 모델 ID (빈 문자열이면 기본 모델)

    Returns:
        테마 문자열 리스트 (예: ["반도체", "AI"])
    """
    content = title
    if body:
        content += "\n\n" + body[:500]

    user_message = f"다음 뉴스의 테마를 분류하세요:\n\n{content}"

    try:
        # model_id가 지정되지 않으면 Opus (기본값) 사용
        result = call_llm(SYSTEM_PROMPT, user_message, model_id=model_id)
        themes = json.loads(result)

        if not isinstance(themes, list):
            return []

        # 유효한 테마만 필터링
        valid = [t for t in themes if isinstance(t, str) and t in THEME_LIST]
        return valid[:2]

    except Exception as e:
        logger.warning("LLM theme classification failed: %s", e)
        return []
