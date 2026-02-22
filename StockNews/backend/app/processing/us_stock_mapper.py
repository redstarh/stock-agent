"""미국 종목 ticker ↔ 종목명 매핑.

종목 사전은 docs/NewsCollectionScope.md에서 로드하며, fallback으로 내장 사전 사용.
"""

from app.core.scope_loader import load_scope

# 기본값 (scope 파일 미존재 시 fallback)
_DEFAULT_US_STOCK_MAP: dict[str, str] = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "META": "Meta Platforms",
    "TSLA": "Tesla",
    "BRK.B": "Berkshire Hathaway",
    "JPM": "JPMorgan Chase",
    "V": "Visa",
    "UNH": "UnitedHealth",
    "JNJ": "Johnson & Johnson",
    "WMT": "Walmart",
    "MA": "Mastercard",
    "PG": "Procter & Gamble",
    "HD": "Home Depot",
    "XOM": "Exxon Mobil",
    "AVGO": "Broadcom",
    "LLY": "Eli Lilly",
    "COST": "Costco",
    "MRK": "Merck",
    "ABBV": "AbbVie",
    "PEP": "PepsiCo",
    "KO": "Coca-Cola",
    "ADBE": "Adobe",
    "CRM": "Salesforce",
    "TMO": "Thermo Fisher",
    "NFLX": "Netflix",
    "AMD": "AMD",
    "INTC": "Intel",
    "CSCO": "Cisco",
    "DIS": "Disney",
    "PFE": "Pfizer",
    "ABT": "Abbott",
    "NKE": "Nike",
    "ORCL": "Oracle",
    "QCOM": "Qualcomm",
    "TXN": "Texas Instruments",
    "IBM": "IBM",
    "AMAT": "Applied Materials",
    "BKNG": "Booking Holdings",
    "ISRG": "Intuitive Surgical",
    "NOW": "ServiceNow",
    "UBER": "Uber",
    "GS": "Goldman Sachs",
    "BA": "Boeing",
    "GE": "GE Aerospace",
    "CAT": "Caterpillar",
    "MMM": "3M",
    "PYPL": "PayPal",
}


def _load_us_stock_map() -> dict[str, str]:
    """Scope 파일에서 미국 종목 사전 로드. 실패 시 기본값 사용."""
    scope = load_scope()
    stocks = scope.get("us_stocks", {})
    if stocks:
        return stocks
    return _DEFAULT_US_STOCK_MAP


# Top 50 US stocks by market cap
US_STOCK_MAP: dict[str, str] = _load_us_stock_map()

_REVERSE_MAP = {v.lower(): k for k, v in US_STOCK_MAP.items()}


def ticker_to_name(ticker: str) -> str | None:
    """Ticker → 종목명."""
    return US_STOCK_MAP.get(ticker.upper())


def name_to_ticker(name: str) -> str | None:
    """종목명 → Ticker."""
    return _REVERSE_MAP.get(name.lower())


def extract_tickers_from_text(text: str) -> list[str]:
    """텍스트에서 ticker 추출 (word boundaries 사용)."""
    import re

    found = []
    text_upper = text.upper()

    # First try exact ticker matches with word boundaries
    for ticker in US_STOCK_MAP:
        # Escape special characters for regex (e.g., BRK.B)
        escaped_ticker = re.escape(ticker)
        pattern = r'\b' + escaped_ticker + r'\b'
        if re.search(pattern, text_upper):
            found.append(ticker)

    # If no tickers found, try company name matching
    if not found:
        text_lower = text.lower()
        for ticker, name in US_STOCK_MAP.items():
            if name.lower() in text_lower:
                found.append(ticker)

    return found
