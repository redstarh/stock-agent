"""종목명 ↔ 종목코드 매핑.

KOSPI/KOSDAQ 주요 종목 사전 기반 매핑.
MVP에서는 하드코딩 사전 사용; 추후 KRX API 또는 CSV 연동 가능.
"""

# 종목 사전: {종목명: 종목코드}
STOCK_DICT: dict[str, str] = {
    # KOSPI 대형주 Top 50
    "삼성전자": "005930",
    "삼성전자우": "005935",
    "SK하이닉스": "000660",
    "LG에너지솔루션": "373220",
    "삼성바이오로직스": "207940",
    "현대차": "005380",
    "현대자동차": "005380",
    "기아": "000270",
    "셀트리온": "068270",
    "KB금융": "105560",
    "POSCO홀딩스": "005490",
    "포스코홀딩스": "005490",
    "신한지주": "055550",
    "NAVER": "035420",
    "네이버": "035420",
    "삼성SDI": "006400",
    "LG화학": "051910",
    "하나금융지주": "086790",
    "삼성물산": "028260",
    "카카오": "035720",
    "우리금융지주": "316140",
    "HD현대중공업": "329180",
    "HMM": "011200",
    "삼성생명": "032830",
    "LG전자": "066570",
    "크래프톤": "259960",
    "SK이노베이션": "096770",
    "SK텔레콤": "017670",
    "KT&G": "033780",
    "한국전력": "015760",
    "현대모비스": "012330",
    "SK": "034730",
    "한화오션": "042660",
    "삼성화재": "000810",
    "NH투자증권": "005940",
    "두산에너빌리티": "034020",
    "KT": "030200",
    "LG": "003550",
    "한화에어로스페이스": "012450",
    "HD한국조선해양": "009540",
    "한국가스공사": "036460",
    "대한항공": "003490",
    "에코프로비엠": "247540",
    "에코프로": "086520",
    "포스코퓨처엠": "003670",
    "삼성전기": "009150",
    "LG이노텍": "011070",
    "SK바이오팜": "326030",
    "카카오뱅크": "323410",
    "카카오페이": "377300",
    # KOSDAQ 주요 종목
    "에코프로에이치엔": "383310",
    "알테오젠": "196170",
    "HLB": "028300",
    "리가켐바이오": "141080",
    "레인보우로보틱스": "277810",
    "엘앤에프": "066970",
    "포스코DX": "022100",
    "JYP Ent.": "035900",
    "JYP엔터": "035900",
    "HYBE": "352820",
    "하이브": "352820",
    "SM": "041510",
    "펄어비스": "263750",
    "CJ ENM": "035760",
}

# 영문명 → 코드 (대소문자 무시 매핑용)
_ENGLISH_MAP: dict[str, str] = {
    name.upper(): code for name, code in STOCK_DICT.items()
    if any(c.isascii() and c.isalpha() for c in name)
}

# 역매핑: {종목코드: 종목명} (첫 번째 매칭만 사용)
_CODE_TO_NAME: dict[str, str] = {}
for _name, _code in STOCK_DICT.items():
    if _code not in _CODE_TO_NAME:
        _CODE_TO_NAME[_code] = _name


def code_to_name(code: str) -> str:
    """종목코드 → 종목명. 미등록 시 빈 문자열."""
    return _CODE_TO_NAME.get(code, "")


def map_stock_name(name: str) -> str | None:
    """종목명 → 종목코드 매핑. 미등록 시 None 반환."""
    # 1. 정확 매칭
    if name in STOCK_DICT:
        return STOCK_DICT[name]

    # 2. 영문 대소문자 무시
    upper = name.upper()
    if upper in _ENGLISH_MAP:
        return _ENGLISH_MAP[upper]

    # 3. 부분 매칭 (종목명이 키에 포함)
    for stock_name, code in STOCK_DICT.items():
        if name == stock_name:
            return code

    return None


def extract_stock_codes(text: str) -> list[str]:
    """텍스트에서 종목명을 찾아 종목코드 리스트 반환.

    긴 이름부터 매칭하여 부분 매칭 오류 방지.
    """
    codes = []
    seen: set[str] = set()

    # 긴 이름부터 매칭 (e.g., "삼성전자우" > "삼성전자" > "삼성")
    sorted_names = sorted(STOCK_DICT.keys(), key=len, reverse=True)

    for name in sorted_names:
        if name in text:
            code = STOCK_DICT[name]
            if code not in seen:
                codes.append(code)
                seen.add(code)

    return codes


def find_matching_stocks(query: str) -> list[dict]:
    """쿼리와 부분 매칭되는 종목 리스트 반환.

    모호한 검색(e.g., "삼성")에 대해 관련 종목 목록 제공.
    """
    results = []
    seen_codes: set[str] = set()

    for name, code in STOCK_DICT.items():
        if query in name and code not in seen_codes:
            results.append({"name": name, "code": code})
            seen_codes.add(code)

    return results
