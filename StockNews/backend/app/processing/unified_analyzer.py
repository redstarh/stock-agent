"""통합 LLM 뉴스 분석기.

감성 분석 + 테마 분류 + 요약 + 크로스마켓 영향을 1회 LLM 호출로 처리.
개별 분석기 대비 비용 66~75% 절감, 지연 66% 단축.
"""

import json
import logging

from app.core.llm import call_llm
from app.core.scope_loader import load_scope

logger = logging.getLogger(__name__)

# Scope에서 테마 목록 로드 (fallback: 기본 16개)
_DEFAULT_THEME_LIST = [
    "AI", "반도체", "2차전지", "바이오", "자동차", "조선", "방산",
    "로봇", "금융", "엔터", "게임", "에너지", "부동산", "통신", "철강", "항공",
]


def _load_theme_list() -> list[str]:
    """Scope 파일에서 테마 목록 로드."""
    scope = load_scope()
    themes = scope.get("themes", {})
    if themes:
        return list(themes.keys())
    return _DEFAULT_THEME_LIST


THEME_LIST = _load_theme_list()

_SYSTEM_PROMPT_KR = """당신은 한국 금융 시장 뉴스 분석 전문가입니다.
뉴스를 읽고 아래 4가지를 분석하여 **JSON 하나**로 반환하세요.

## 1. 감성 분석
- sentiment: "positive" | "neutral" | "negative"
- score: -1.0 ~ 1.0 (주가 영향도)
  - positive: 0.3 ~ 1.0 (실적 개선, 수주 확대, 목표가 상향)
  - neutral: -0.3 ~ 0.3 (일상적 공시, 조직 개편)
  - negative: -1.0 ~ -0.3 (실적 악화, 리콜, 소송)
- confidence: 0.0 ~ 1.0
  - 명확한 실적/주가 키워드: 0.8 ~ 1.0
  - 맥락상 유추: 0.5 ~ 0.8
  - 애매한 경우: 0.3 ~ 0.5

## 2. 테마 분류
사용 가능한 테마: {themes}
- 뉴스 내용과 직접 관련된 테마만 선택 (최대 2개)
- 종목명만으로 테마를 유추하지 마세요
- 관련 테마 없으면 빈 배열 []

## 3. 뉴스 요약
- 한국어로 1~2문장, 200자 이내
- 핵심: 무슨 일이, 어떤 기업에, 시장 영향은?
- 본문이 없으면 빈 문자열 ""

## 4. 크로스마켓 영향 (US 뉴스인 경우만)
- 미국 뉴스가 한국 시장 테마에 미치는 영향
- KR 뉴스이면 빈 배열 []

## 응답 형식 (JSON만, 설명 없이)
{{"sentiment": "positive", "score": 0.85, "confidence": 0.9, "themes": ["반도체"], "summary": "요약 텍스트", "kr_impact": []}}"""

_EXAMPLES = """
## 예시

입력: [KR] "삼성전자 4분기 영업이익 10조원 돌파"
출력: {"sentiment": "positive", "score": 0.85, "confidence": 0.95, "themes": ["반도체"], "summary": "삼성전자가 4분기 영업이익 10조원을 돌파하며 반도체 업황 회복 기대감을 높였다.", "kr_impact": []}

입력: [US] "NVIDIA reports record AI chip revenue, surpassing expectations"
출력: {"sentiment": "positive", "score": 0.80, "confidence": 0.90, "themes": ["AI", "반도체"], "summary": "엔비디아가 AI 칩 매출 신기록을 달성하며 시장 기대를 상회했다.", "kr_impact": [{"theme": "반도체", "impact": 0.8, "direction": "up"}, {"theme": "AI", "impact": 0.7, "direction": "up"}]}

입력: [KR] "삼성전자 주가 19만원 넘었다"
출력: {"sentiment": "neutral", "score": 0.1, "confidence": 0.6, "themes": [], "summary": "삼성전자 주가가 19만원을 돌파했다.", "kr_impact": []}"""


def analyze_news(
    title: str,
    body: str | None = None,
    market: str = "KR",
    *,
    model_id: str = "",
) -> dict:
    """뉴스 통합 분석 (1회 LLM 호출).

    Args:
        title: 뉴스 제목
        body: 뉴스 본문 (optional)
        market: 시장 구분 (KR/US)
        model_id: 사용할 모델 ID (빈 문자열이면 기본 모델)

    Returns:
        {
            "sentiment": str,
            "sentiment_score": float,
            "confidence": float,
            "themes": list[str],
            "summary": str,
            "kr_impact_themes": list[dict],
        }
    """
    themes_str = ", ".join(THEME_LIST)
    system_prompt = _SYSTEM_PROMPT_KR.format(themes=themes_str) + _EXAMPLES

    # 사용자 메시지 구성
    content = f"[{market}] 제목: {title}"
    if body:
        content += f"\n본문: {body[:2000]}"

    try:
        result_text = call_llm(system_prompt, content, model_id=model_id)
        result = json.loads(result_text)

        # 감성 검증
        sentiment = result.get("sentiment", "neutral")
        if sentiment not in ("positive", "neutral", "negative"):
            sentiment = "neutral"

        score = float(result.get("score", 0.0))
        score = max(-1.0, min(1.0, score))

        confidence = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        # 테마 검증
        raw_themes = result.get("themes", [])
        if not isinstance(raw_themes, list):
            raw_themes = []
        themes = [t for t in raw_themes if isinstance(t, str) and t in THEME_LIST][:2]

        # 요약 검증
        summary = str(result.get("summary", ""))[:200]

        # 크로스마켓 검증
        kr_impact = []
        if market == "US":
            raw_impact = result.get("kr_impact", [])
            if isinstance(raw_impact, list):
                for item in raw_impact:
                    if not isinstance(item, dict):
                        continue
                    theme = item.get("theme", "")
                    impact = float(item.get("impact", 0))
                    direction = item.get("direction", "neutral")
                    if theme and 0 <= impact <= 1 and direction in ("up", "down", "neutral"):
                        kr_impact.append({
                            "theme": theme,
                            "impact": round(impact, 2),
                            "direction": direction,
                        })

        return {
            "sentiment": sentiment,
            "sentiment_score": score,
            "confidence": confidence,
            "themes": themes,
            "summary": summary,
            "kr_impact_themes": kr_impact,
        }

    except Exception as e:
        logger.warning("Unified analysis failed, returning defaults: %s", e)
        return _default_result()


def _default_result() -> dict:
    """분석 실패 시 기본값."""
    return {
        "sentiment": "neutral",
        "sentiment_score": 0.0,
        "confidence": 0.0,
        "themes": [],
        "summary": "",
        "kr_impact_themes": [],
    }
