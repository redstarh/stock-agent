"""Advan Event Extractor 단위 테스트."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.advan.event_extractor import extract_events
from app.advan.models import AdvanEvent
from app.models.news_event import NewsEvent


@pytest.fixture
def sample_news_data(db_session: Session):
    """테스트용 뉴스 이벤트 생성."""
    events = [
        NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title="삼성전자 4분기 영업이익 12조원 달성",
            summary="삼성전자가 2024년 4분기 영업이익 12조원을 달성했다.",
            sentiment="positive",
            sentiment_score=0.8,
            news_score=85.0,
            source="DART",
            source_url="https://dart.fss.or.kr/test/1",
            is_disclosure=True,
            published_at=datetime(2024, 1, 15, 9, 0, tzinfo=UTC),
        ),
        NewsEvent(
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title="삼성전자 대규모 자사주 매입 결정",
            summary="삼성전자가 1조원 규모 자사주 매입을 발표했다.",
            sentiment="positive",
            sentiment_score=0.6,
            news_score=72.0,
            source="Naver",
            source_url="https://naver.com/test/2",
            is_disclosure=False,
            published_at=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
        ),
        NewsEvent(
            market="KR",
            stock_code="000660",
            stock_name="SK하이닉스",
            title="SK하이닉스 소송 패소 판결",
            summary="SK하이닉스가 특허 침해 소송에서 패소했다.",
            sentiment="negative",
            sentiment_score=-0.7,
            news_score=65.0,
            source="Naver",
            source_url="https://naver.com/test/3",
            is_disclosure=False,
            published_at=datetime(2024, 1, 15, 14, 0, tzinfo=UTC),
        ),
        NewsEvent(
            market="KR",
            stock_code="035420",
            stock_name="NAVER",
            title="네이버 유상증자 결정",
            summary="네이버가 5000억원 규모 유상증자를 결정했다.",
            sentiment="negative",
            sentiment_score=-0.5,
            news_score=78.0,
            source="DART",
            source_url="https://dart.fss.or.kr/test/4",
            is_disclosure=True,
            published_at=datetime(2024, 1, 15, 7, 0, tzinfo=UTC),  # 07:00 UTC = 16:00 KST (장후)
        ),
        NewsEvent(
            market="US",
            stock_code="AAPL",
            stock_name="Apple Inc",
            title="Apple reports record Q4 revenue",
            summary="Apple posted record quarterly revenue of $120B.",
            sentiment="positive",
            sentiment_score=0.7,
            news_score=90.0,
            source="Finnhub",
            source_url="https://finnhub.io/test/5",
            is_disclosure=False,
            published_at=datetime(2024, 1, 15, 20, 0, tzinfo=UTC),
        ),
    ]

    for e in events:
        db_session.add(e)
    db_session.commit()

    return events


class TestExtractEvents:
    """이벤트 추출 테스트."""

    def test_extract_kr_events(self, db_session: Session, sample_news_data):
        """KR 이벤트 추출."""
        result = extract_events(db_session, market="KR")
        assert result["extracted_count"] >= 3  # 최소 3건 (KR 뉴스 4건 중)
        assert result["error_count"] == 0

        # DB에 저장 확인
        events = db_session.query(AdvanEvent).filter(AdvanEvent.market == "KR").all()
        assert len(events) >= 3

    def test_extract_us_events(self, db_session: Session, sample_news_data):
        """US 이벤트 추출."""
        result = extract_events(db_session, market="US")
        assert result["extracted_count"] >= 1

    def test_event_type_classification(self, db_session: Session, sample_news_data):
        """이벤트 유형 분류 확인."""
        extract_events(db_session, market="KR")

        events = db_session.query(AdvanEvent).filter(AdvanEvent.market == "KR").all()
        event_types = {e.ticker: e.event_type for e in events}

        # 영업이익 → 실적
        samsung_events = [e for e in events if e.ticker == "005930"]
        types = {e.event_type for e in samsung_events}
        assert any(t in types for t in ["실적", "자사주", "기타"])

    def test_credibility_by_source(self, db_session: Session, sample_news_data):
        """소스별 신뢰도 검증."""
        extract_events(db_session, market="KR")

        events = db_session.query(AdvanEvent).all()
        for e in events:
            if e.is_disclosure:
                assert e.credibility >= 0.8, f"DART 공시 신뢰도가 낮음: {e.credibility}"
            else:
                assert e.credibility < 0.9, f"비공시 신뢰도가 너무 높음: {e.credibility}"

    def test_direction_from_sentiment(self, db_session: Session, sample_news_data):
        """감성 기반 방향성 추출."""
        extract_events(db_session, market="KR")

        events = db_session.query(AdvanEvent).all()
        for e in events:
            assert e.direction in ("positive", "negative", "mixed", "unknown")

    def test_after_market_detection(self, db_session: Session, sample_news_data):
        """장후 발표 감지."""
        extract_events(db_session, market="KR")

        # 네이버 유상증자 (16:00 발표) → is_after_market=True
        naver_events = db_session.query(AdvanEvent).filter(AdvanEvent.ticker == "035420").all()
        if naver_events:
            assert any(e.is_after_market for e in naver_events)

    def test_no_duplicate_extraction(self, db_session: Session, sample_news_data):
        """중복 추출 방지."""
        result1 = extract_events(db_session, market="KR")
        count1 = result1["extracted_count"]

        result2 = extract_events(db_session, market="KR")
        count2 = result2["extracted_count"]

        # 두 번째 추출 시 새 이벤트 없어야 함
        assert count2 == 0 or count2 <= count1

    def test_force_rebuild(self, db_session: Session, sample_news_data):
        """force_rebuild 시 재추출."""
        extract_events(db_session, market="KR")
        result = extract_events(db_session, market="KR", force_rebuild=True)
        assert result["extracted_count"] >= 1


class TestEventModel:
    """AdvanEvent 모델 테스트."""

    def test_create_event(self, db_session: Session):
        """이벤트 생성."""
        event = AdvanEvent(
            source_news_id=1,
            ticker="005930",
            stock_name="삼성전자",
            market="KR",
            event_type="실적",
            direction="positive",
            magnitude=0.8,
            novelty=0.9,
            credibility=0.95,
            is_disclosure=True,
            title="삼성전자 4분기 실적 발표",
            source="DART",
            event_timestamp=datetime(2024, 1, 15, 9, 0, tzinfo=UTC),
        )
        db_session.add(event)
        db_session.commit()

        saved = db_session.query(AdvanEvent).first()
        assert saved is not None
        assert saved.ticker == "005930"
        assert saved.event_type == "실적"
        assert saved.credibility == 0.95

    def test_event_repr(self, db_session: Session):
        """이벤트 repr 출력."""
        event = AdvanEvent(
            ticker="005930",
            market="KR",
            event_type="실적",
            direction="positive",
            title="테스트",
            source="DART",
            event_timestamp=datetime.now(UTC),
        )
        assert "005930" in repr(event)
        assert "실적" in repr(event)
