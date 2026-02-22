"""RED: 중복 제거 로직 단위 테스트."""

import pytest


class TestDedup:
    def test_same_url_is_duplicate(self, db_session):
        """동일 URL → 중복 판정."""
        from app.processing.dedup import is_duplicate

        # 첫 번째 뉴스는 중복 아님
        assert is_duplicate(db_session, source_url="https://news.naver.com/1") is False

        # DB에 같은 URL 저장
        from app.models.news_event import NewsEvent

        db_session.add(
            NewsEvent(
                market="KR", stock_code="005930", title="삼성전자 실적",
                source="naver", source_url="https://news.naver.com/1",
            )
        )
        db_session.flush()

        # 같은 URL은 중복
        assert is_duplicate(db_session, source_url="https://news.naver.com/1") is True

    def test_different_url_is_not_duplicate(self, db_session):
        """다른 URL → 비중복."""
        from app.processing.dedup import is_duplicate
        from app.models.news_event import NewsEvent

        db_session.add(
            NewsEvent(
                market="KR", stock_code="005930", title="삼성전자 실적",
                source="naver", source_url="https://news.naver.com/1",
            )
        )
        db_session.flush()

        assert is_duplicate(db_session, source_url="https://news.naver.com/2") is False

    def test_same_title_different_source(self, db_session):
        """동일 제목 + 다른 출처 → 중복 판정 (유사도 기반)."""
        from app.processing.dedup import is_duplicate
        from app.models.news_event import NewsEvent

        db_session.add(
            NewsEvent(
                market="KR", stock_code="005930", title="삼성전자 4분기 실적 발표",
                source="naver", source_url="https://news.naver.com/1",
            )
        )
        db_session.flush()

        # 동일 제목, 다른 URL/소스 → 중복
        assert is_duplicate(
            db_session,
            source_url="https://daum.net/news/1",
            title="삼성전자 4분기 실적 발표",
        ) is True

    def test_empty_url_handling(self, db_session):
        """URL 없는 뉴스 → URL 중복 체크 skip, 제목 기반으로만 판별."""
        from app.processing.dedup import is_duplicate

        # URL 없으면 URL 중복은 아님
        assert is_duplicate(db_session, source_url=None, title="새로운 뉴스") is False

    def test_deduplicate_batch(self, db_session):
        """뉴스 리스트에서 중복 제거 후 반환."""
        from app.processing.dedup import deduplicate
        from app.models.news_event import NewsEvent

        # 기존 DB에 뉴스 1건
        db_session.add(
            NewsEvent(
                market="KR", stock_code="005930", title="기존 뉴스",
                source="naver", source_url="https://news.naver.com/existing",
            )
        )
        db_session.flush()

        # 새 뉴스 배치: 1건 중복 + 2건 신규
        batch = [
            {"title": "기존 뉴스", "source_url": "https://news.naver.com/existing",
             "market": "KR", "stock_code": "005930", "source": "naver"},
            {"title": "새 뉴스 1", "source_url": "https://news.naver.com/new1",
             "market": "KR", "stock_code": "005930", "source": "naver"},
            {"title": "새 뉴스 2", "source_url": "https://news.naver.com/new2",
             "market": "KR", "stock_code": "035420", "source": "naver"},
        ]

        result = deduplicate(db_session, batch)
        assert len(result) == 2
        assert all(item["source_url"] != "https://news.naver.com/existing" for item in result)

    def test_deduplicate_same_title_different_url_in_batch(self, db_session):
        """배치 내 같은 제목 + 다른 URL → 두 번째 제거 (교차 수집기 중복)."""
        from app.processing.dedup import deduplicate

        batch = [
            {"title": "삼성전자 실적 발표", "source_url": "https://naver.com/1",
             "market": "KR", "stock_code": "005930", "source": "naver"},
            {"title": "삼성전자 실적 발표", "source_url": "https://rss.com/1",
             "market": "KR", "stock_code": "005930", "source": "rss"},
        ]

        result = deduplicate(db_session, batch)
        assert len(result) == 1
        assert result[0]["source_url"] == "https://naver.com/1"

    def test_deduplicate_same_url_in_batch(self, db_session):
        """배치 내 같은 URL → 두 번째 제거."""
        from app.processing.dedup import deduplicate

        batch = [
            {"title": "뉴스 A", "source_url": "https://naver.com/same",
             "market": "KR", "stock_code": "005930", "source": "naver"},
            {"title": "뉴스 B", "source_url": "https://naver.com/same",
             "market": "KR", "stock_code": "005930", "source": "naver"},
        ]

        result = deduplicate(db_session, batch)
        assert len(result) == 1
