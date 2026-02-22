"""NewsCollectionScope.md YAML front matter writer.

docs/NewsCollectionScope.md의 YAML front matter를 프로그래밍 방식으로
수정하는 기능을 제공합니다. Markdown 문서는 보존됩니다.
"""

import logging
import threading
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_write_lock = threading.Lock()


def _find_scope_file() -> Path | None:
    """프로젝트 루트 기준 NewsCollectionScope.md 경로 탐색."""
    # backend/app/core/scope_writer.py → backend/ → project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    candidate = project_root / "docs" / "NewsCollectionScope.md"
    if candidate.exists():
        return candidate
    return None


def read_scope_yaml() -> dict:
    """Parse and return YAML front matter as dict.

    Returns:
        파싱된 YAML dict. 파일 미존재 또는 파싱 실패 시 빈 dict.
    """
    path = _find_scope_file()
    if not path:
        logger.warning("NewsCollectionScope.md not found")
        return {}

    try:
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")
        delimiters = [i for i, line in enumerate(lines) if line.strip() == "---"]
        if len(delimiters) >= 2:
            yaml_text = "\n".join(lines[delimiters[0] + 1 : delimiters[1]])
            data = yaml.safe_load(yaml_text)
            if isinstance(data, dict):
                return data
    except Exception as e:
        logger.error("Failed to read scope YAML: %s", e)

    return {}


def write_scope_yaml(data: dict) -> None:
    """Serialize dict to YAML and replace ONLY the front matter section.

    Preserve the Markdown documentation below the second --- delimiter.

    NOTE: This function does NOT acquire _write_lock. Callers must hold the lock.

    Args:
        data: YAML front matter를 대체할 dict
    """
    path = _find_scope_file()
    if not path:
        logger.error("NewsCollectionScope.md not found, cannot write")
        return

    try:
        # Read current file
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Find delimiters
        delimiters = [i for i, line in enumerate(lines) if line.strip() == "---"]
        if len(delimiters) < 2:
            logger.error("Invalid format: less than 2 --- delimiters found")
            return

        # Preserve markdown after second delimiter
        markdown_content = "\n".join(lines[delimiters[1] + 1 :])

        # Generate new YAML with header comment
        yaml_header = (
            "# News Collection Scope Configuration (Machine-Readable YAML Front Matter)\n"
            "# 이 YAML 블록은 뉴스 수집기가 런타임에 파싱하여 사용합니다.\n"
            "# 수정 시 YAML 문법을 준수하고, 하단 문서와 일관성을 유지하세요.\n"
        )
        yaml_content = yaml.dump(
            data,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=120,
        )

        # Reconstruct file
        new_content = f"---\n{yaml_header}\n{yaml_content}---\n{markdown_content}"

        # Write atomically
        path.write_text(new_content, encoding="utf-8")
        logger.info("Successfully updated NewsCollectionScope.md YAML front matter")

    except Exception as e:
        logger.error("Failed to write scope YAML: %s", e)


def add_kr_search_query(query: str, stock_code: str) -> bool:
    """Add a new entry to korean_market.search_queries if not already present.

    Args:
        query: 검색 쿼리 (예: "삼성전자")
        stock_code: 종목 코드 (예: "005930")

    Returns:
        True if added, False if already exists (duplicate check by stock_code).
    """
    with _write_lock:
        data = read_scope_yaml()

        # Ensure structure exists
        if "korean_market" not in data:
            data["korean_market"] = {}
        if "search_queries" not in data["korean_market"]:
            data["korean_market"]["search_queries"] = []

        queries = data["korean_market"]["search_queries"]

        # Check if stock_code already exists
        for entry in queries:
            if entry.get("stock_code") == stock_code:
                logger.info("Search query for %s already exists", stock_code)
                return False

        # Add new entry
        queries.append({"query": query, "stock_code": stock_code})
        write_scope_yaml(data)
        logger.info("Added search query: %s (%s)", query, stock_code)
        return True


def add_korean_stock(name: str, code: str) -> bool:
    """Add a new entry to korean_stocks dict.

    Args:
        name: 종목명 (예: "삼성전자")
        code: 종목 코드 (예: "005930")

    Returns:
        True if added, False if already exists.
    """
    with _write_lock:
        data = read_scope_yaml()

        # Ensure structure exists
        if "korean_stocks" not in data:
            data["korean_stocks"] = {}

        stocks = data["korean_stocks"]

        # Check if name already exists
        if name in stocks:
            logger.info("Korean stock %s already exists", name)
            return False

        # Add new entry
        stocks[name] = code
        write_scope_yaml(data)
        logger.info("Added Korean stock: %s (%s)", name, code)
        return True


def add_us_stock(ticker: str, name: str) -> bool:
    """Add a new entry to us_stocks dict.

    Args:
        ticker: 티커 심볼 (예: "AAPL")
        name: 회사명 (예: "Apple Inc.")

    Returns:
        True if added, False if already exists.
    """
    with _write_lock:
        data = read_scope_yaml()

        # Ensure structure exists
        if "us_stocks" not in data:
            data["us_stocks"] = {}

        stocks = data["us_stocks"]

        # Check if ticker already exists
        if ticker in stocks:
            logger.info("US stock %s already exists", ticker)
            return False

        # Add new entry
        stocks[ticker] = name
        write_scope_yaml(data)
        logger.info("Added US stock: %s (%s)", ticker, name)
        return True
