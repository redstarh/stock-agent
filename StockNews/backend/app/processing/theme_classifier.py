"""키워드 기반 테마 분류기.

뉴스 제목/본문에서 투자 테마를 추출.
키워드 사전은 docs/NewsCollectionScope.md에서 로드하며, LLM 분류 fallback으로 사용.
"""

from app.core.scope_loader import load_scope

# 기본값 (scope 파일 미존재 시 fallback)
_DEFAULT_THEME_KEYWORDS: dict[str, list[str]] = {
    "AI": ["AI", "인공지능", "딥러닝", "머신러닝", "GPT", "LLM", "생성형"],
    "반도체": ["반도체", "HBM", "파운드리", "메모리", "D램", "DRAM", "낸드", "NAND"],
    "2차전지": ["2차전지", "배터리", "양극재", "음극재", "전해질", "리튬", "전고체"],
    "바이오": ["바이오", "신약", "임상", "제약", "항체", "세포치료"],
    "자동차": ["자동차", "전기차", "EV", "자율주행", "완성차"],
    "조선": ["조선", "LNG선", "컨테이너선", "해운", "수주"],
    "방산": ["방산", "방위산업", "국방", "무기", "K방산"],
    "로봇": ["로봇", "로보틱스", "자동화", "휴머노이드"],
    "금융": ["금융", "은행", "보험", "증권", "핀테크", "금리"],
    "엔터": ["엔터", "K-POP", "한류", "콘텐츠", "OTT"],
    "게임": ["게임", "MMORPG", "모바일게임"],
    "에너지": ["에너지", "태양광", "풍력", "수소", "원전", "신재생"],
    "부동산": ["부동산", "건설", "분양", "PF", "주택"],
    "통신": ["통신", "5G", "6G", "데이터센터", "클라우드"],
    "철강": ["철강", "포스코", "고로", "전기로"],
    "항공": ["항공", "여행", "관광", "면세"],
}


def _load_theme_keywords() -> dict[str, list[str]]:
    """Scope 파일에서 테마 키워드 로드. 실패 시 기본값 사용."""
    scope = load_scope()
    themes = scope.get("themes", {})
    if themes:
        return themes
    return _DEFAULT_THEME_KEYWORDS


# 테마 키워드 사전: {테마명: [키워드 리스트]}
THEME_KEYWORDS: dict[str, list[str]] = _load_theme_keywords()


def classify_theme(text: str) -> list[str]:
    """텍스트에서 매칭되는 테마 리스트 반환.

    키워드가 텍스트에 포함되면 해당 테마로 분류.
    """
    matched_themes: list[str] = []

    for theme, keywords in THEME_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                matched_themes.append(theme)
                break  # 한 테마에 여러 키워드 매칭해도 1회만

    return matched_themes
