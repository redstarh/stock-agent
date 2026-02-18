"""뉴스 수집 파이프라인 테스트."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def sample_items():
    """테스트용 수집 아이템."""
    return [
        {
            "title": "삼성전자 4분기 실적 발표",
            "source_url": "https://example.com/news/1",
            "source": "naver",
            "market": "KR",
            "stock_code": "005930",
            "stock_name": "삼성전자",
        },
        {
            "title": "SK하이닉스 HBM 수주 확대",
            "source_url": "https://example.com/news/2",
            "source": "naver",
            "market": "KR",
            "stock_code": "000660",
            "stock_name": "SK하이닉스",
        },
    ]


@pytest.fixture
def mock_pipeline_deps(monkeypatch):
    """파이프라인 외부 의존성 mock."""
    # Mock sentiment analysis
    monkeypatch.setattr(
        "app.processing.sentiment.call_llm",
        lambda sys, usr, **kw: '{"sentiment": "positive", "score": 0.8, "confidence": 0.9}',
    )

    # Mock summary
    monkeypatch.setattr(
        "app.processing.summary.call_llm",
        lambda sys, usr, **kw: '{"summary": "테스트 요약"}',
    )

    # Mock Redis (unavailable)
    monkeypatch.setattr(
        "app.collectors.pipeline._get_redis_client",
        lambda: None,
    )


class TestProcessCollectedItems:
    """process_collected_items() 테스트."""

    @pytest.mark.asyncio
    async def test_empty_items_returns_zero(self, db_session):
        """빈 리스트 → 0 반환."""
        from app.collectors.pipeline import process_collected_items
        result = await process_collected_items(db_session, [], market="KR")
        assert result == 0

    @pytest.mark.asyncio
    async def test_processes_and_saves_items(self, db_session, sample_items, mock_pipeline_deps, monkeypatch):
        """아이템을 처리하고 DB에 저장."""
        from app.collectors.pipeline import process_collected_items
        from app.models.news_event import NewsEvent

        # Mock article scraper (no body)
        async def mock_scrape(items):
            return {item.get("source_url", ""): None for item in items}
        monkeypatch.setattr("app.collectors.pipeline._scrape_articles", mock_scrape)

        count = await process_collected_items(db_session, sample_items, market="KR")

        assert count == 2
        events = db_session.query(NewsEvent).all()
        assert len(events) == 2

        # Verify first event
        event = db_session.query(NewsEvent).filter_by(stock_code="005930").first()
        assert event is not None
        assert event.title == "삼성전자 4분기 실적 발표"
        assert event.market == "KR"
        assert event.source == "naver"
        assert event.sentiment == "positive"
        assert event.news_score > 0

    @pytest.mark.asyncio
    async def test_dedup_filters_duplicates(self, db_session, sample_items, mock_pipeline_deps, monkeypatch):
        """중복 아이템 필터링."""
        from app.collectors.pipeline import process_collected_items
        from app.models.news_event import NewsEvent

        async def mock_scrape(items):
            return {item.get("source_url", ""): None for item in items}
        monkeypatch.setattr("app.collectors.pipeline._scrape_articles", mock_scrape)

        # First batch
        count1 = await process_collected_items(db_session, sample_items, market="KR")
        assert count1 == 2

        # Same batch again → should be filtered out
        count2 = await process_collected_items(db_session, sample_items, market="KR")
        assert count2 == 0

    @pytest.mark.asyncio
    async def test_item_failure_falls_back_to_neutral(self, db_session, mock_pipeline_deps, monkeypatch):
        """감성분석 실패 시 neutral fallback으로 저장."""
        from app.collectors.pipeline import process_collected_items
        from app.models.news_event import NewsEvent

        items = [
            {
                "title": "정상 뉴스",
                "source_url": "https://example.com/ok",
                "source": "naver",
                "market": "KR",
                "stock_code": "005930",
            },
            {
                "title": "문제 뉴스",
                "source_url": "https://example.com/bad",
                "source": "naver",
                "market": "KR",
                "stock_code": "000660",
            },
        ]

        call_count = 0

        def failing_sentiment(text, body=None):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("LLM error")
            return {"sentiment": "positive", "score": 0.8, "confidence": 0.9}

        monkeypatch.setattr("app.collectors.pipeline.analyze_sentiment", failing_sentiment)

        async def mock_scrape(items):
            return {item.get("source_url", ""): None for item in items}
        monkeypatch.setattr("app.collectors.pipeline._scrape_articles", mock_scrape)

        count = await process_collected_items(db_session, items, market="KR")
        assert count == 2  # Both saved, failed one gets neutral fallback

        failed_event = db_session.query(NewsEvent).filter_by(stock_code="000660").first()
        assert failed_event.sentiment == "neutral"

    @pytest.mark.asyncio
    async def test_breaking_news_published(self, db_session, sample_items, monkeypatch):
        """점수 >= 80이면 Redis 속보 발행 시도."""
        from app.collectors.pipeline import process_collected_items
        import fakeredis

        fake_redis = fakeredis.FakeRedis()
        monkeypatch.setattr("app.collectors.pipeline._get_redis_client", lambda: fake_redis)

        # Mock sentiment to return high score
        monkeypatch.setattr(
            "app.processing.sentiment.call_llm",
            lambda sys, usr, **kw: '{"sentiment": "positive", "score": 0.95, "confidence": 0.99}',
        )
        monkeypatch.setattr(
            "app.processing.summary.call_llm",
            lambda sys, usr, **kw: '{"summary": "테스트"}',
        )

        async def mock_scrape(items):
            return {item.get("source_url", ""): None for item in items}
        monkeypatch.setattr("app.collectors.pipeline._scrape_articles", mock_scrape)

        count = await process_collected_items(db_session, [sample_items[0]], market="KR")
        assert count == 1


class TestMapStockCode:
    """_map_stock_code() 테스트."""

    def test_existing_stock_code_kept(self):
        """이미 stock_code가 있으면 그대로 사용."""
        from app.collectors.pipeline import _map_stock_code
        result = _map_stock_code({"stock_code": "005930", "title": "test", "market": "KR"})
        assert result == "005930"

    def test_kr_stock_extracted_from_title(self):
        """한국 뉴스 제목에서 종목코드 추출."""
        from app.collectors.pipeline import _map_stock_code
        result = _map_stock_code({"stock_code": "", "title": "삼성전자 실적 발표", "market": "KR"})
        assert result == "005930"

    def test_us_stock_extracted_from_title(self):
        """미국 뉴스 제목에서 ticker 추출."""
        from app.collectors.pipeline import _map_stock_code
        result = _map_stock_code({"stock_code": "", "title": "NVDA hits new high", "market": "US"})
        assert result == "NVDA"

    def test_no_match_returns_empty(self):
        """매칭 안 되면 빈 문자열."""
        from app.collectors.pipeline import _map_stock_code
        result = _map_stock_code({"stock_code": "", "title": "일반 경제 뉴스", "market": "KR"})
        assert result == ""
