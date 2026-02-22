"""뉴스 중복 제거 로직."""

from sqlalchemy.orm import Session

from app.models.news_event import NewsEvent


def is_duplicate(
    db: Session,
    source_url: str | None = None,
    title: str | None = None,
) -> bool:
    """뉴스 중복 여부 판별.

    1순위: source_url 동일 → 중복
    2순위: title 동일 → 중복 (다른 출처에서 같은 뉴스)
    """
    if source_url:
        exists = db.query(NewsEvent).filter(NewsEvent.source_url == source_url).first()
        if exists:
            return True

    if title:
        exists = db.query(NewsEvent).filter(NewsEvent.title == title).first()
        if exists:
            return True

    return False


def deduplicate(db: Session, items: list[dict]) -> list[dict]:
    """뉴스 배치에서 중복 제거 후 신규 뉴스만 반환.

    배치 내 URL + 제목 중복과 DB 기존 데이터 중복을 모두 제거합니다.
    여러 수집기 결과를 병합한 후 호출하면 교차 수집기 중복도 제거됩니다.
    """
    unique = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()

    for item in items:
        url = item.get("source_url")
        title = item.get("title")

        # 배치 내 URL 중복 체크
        if url and url in seen_urls:
            continue

        # 배치 내 제목 중복 체크 (다른 출처에서 같은 뉴스)
        if title and title in seen_titles:
            continue

        # DB 기존 데이터 중복 체크
        if is_duplicate(db, source_url=url, title=title):
            continue

        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)
        unique.append(item)

    return unique
