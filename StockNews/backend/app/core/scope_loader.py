"""NewsCollectionScope.md YAML front matter loader.

docs/NewsCollectionScope.md의 YAML front matter를 파싱하여
수집 기준 데이터를 제공합니다. 파일이 없으면 빈 dict를 반환하며,
각 모듈은 자체 기본값을 fallback으로 사용합니다.
"""

import logging
from functools import lru_cache
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_reload_callbacks: list[callable] = []


def _find_scope_file() -> Path | None:
    """프로젝트 루트 기준 NewsCollectionScope.md 경로 탐색."""
    # backend/app/core/scope_loader.py → backend/ → project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    candidate = project_root / "docs" / "NewsCollectionScope.md"
    if candidate.exists():
        return candidate
    return None


@lru_cache(maxsize=1)
def load_scope() -> dict:
    """YAML front matter를 로드하고 캐싱.

    Returns:
        파싱된 YAML dict. 파일 미존재 또는 파싱 실패 시 빈 dict.
    """
    path = _find_scope_file()
    if not path:
        logger.debug("NewsCollectionScope.md not found, modules will use defaults")
        return {}

    try:
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")
        delimiters = [i for i, line in enumerate(lines) if line.strip() == "---"]
        if len(delimiters) >= 2:
            yaml_text = "\n".join(lines[delimiters[0] + 1 : delimiters[1]])
            data = yaml.safe_load(yaml_text)
            if isinstance(data, dict):
                logger.info("Loaded collection scope from %s", path)
                return data
    except Exception as e:
        logger.warning("Failed to load scope file: %s", e)

    return {}


def register_reload_callback(fn: callable) -> None:
    """reload_scope() 호출 시 실행될 콜백 등록."""
    _reload_callbacks.append(fn)


def reload_scope() -> dict:
    """캐시를 무효화하고 다시 로드. 등록된 콜백 실행."""
    load_scope.cache_clear()
    data = load_scope()
    for cb in _reload_callbacks:
        try:
            cb(data)
        except Exception as e:
            logger.warning("Reload callback failed: %s", e)
    return data
