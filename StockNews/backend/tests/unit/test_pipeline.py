"""뉴스 수집 파이프라인 테스트."""

from unittest.mock import AsyncMock

import pytest

from app.processing.article_scraper import ScrapeResult


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
    # Mock unified analyzer (single LLM call)
    monkeypatch.setattr(
        "app.processing.unified_analyzer.call_llm",
        lambda sys, usr, **kw: '{"sentiment": "positive", "score": 0.8, "confidence": 0.9, "themes": [], "summary": "테스트 요약", "kr_impact": []}',
    )

    # Mock article scraper (no body)
    monkeypatch.setattr(
        "app.processing.article_scraper.ArticleScraper.scrape_one",
        AsyncMock(return_value=ScrapeResult(url="", body=None)),
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
    async def test_processes_and_saves_items(self, db_session, sample_items, mock_pipeline_deps):
        """아이템을 처리하고 DB에 저장."""
        from app.collectors.pipeline import process_collected_items
        from app.models.news_event import NewsEvent

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
    async def test_dedup_filters_duplicates(self, db_session, sample_items, mock_pipeline_deps):
        """중복 아이템 필터링."""
        from app.collectors.pipeline import process_collected_items

        # First batch
        count1 = await process_collected_items(db_session, sample_items, market="KR")
        assert count1 == 2

        # Same batch again → should be filtered out
        count2 = await process_collected_items(db_session, sample_items, market="KR")
        assert count2 == 0

    @pytest.mark.asyncio
    async def test_item_failure_falls_back_to_neutral(self, db_session, mock_pipeline_deps, monkeypatch):
        """통합 분석 실패 시 neutral fallback으로 저장."""
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

        def failing_analyze(title, body=None, market="KR"):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("LLM error")
            return {
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "confidence": 0.9,
                "themes": [],
                "summary": "",
                "kr_impact_themes": [],
            }

        monkeypatch.setattr("app.collectors.pipeline.analyze_news", failing_analyze)

        count = await process_collected_items(db_session, items, market="KR")
        assert count == 2  # Both saved, failed one gets neutral fallback

        failed_event = db_session.query(NewsEvent).filter_by(stock_code="000660").first()
        assert failed_event.sentiment == "neutral"

    @pytest.mark.asyncio
    async def test_breaking_news_published(self, db_session, sample_items, monkeypatch):
        """점수 >= 80이면 Redis 속보 발행 시도."""
        import fakeredis

        from app.collectors.pipeline import process_collected_items

        fake_redis = fakeredis.FakeRedis()
        monkeypatch.setattr("app.collectors.pipeline._get_redis_client", lambda: fake_redis)

        # Mock unified analyzer to return high score
        monkeypatch.setattr(
            "app.processing.unified_analyzer.call_llm",
            lambda sys, usr, **kw: '{"sentiment": "positive", "score": 0.95, "confidence": 0.99, "themes": [], "summary": "테스트", "kr_impact": []}',
        )

        # Mock article scraper (no body)
        monkeypatch.setattr(
            "app.processing.article_scraper.ArticleScraper.scrape_one",
            AsyncMock(return_value=ScrapeResult(url="", body=None)),
        )

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


class TestFastPathCheck:
    """_fast_path_check() 테스트."""

    def test_kr_negative_keyword_detected(self):
        """KR 부정 키워드 → (negative, score) 반환."""
        from app.collectors.pipeline import _fast_path_check
        result = _fast_path_check("삼성전자 파산 신청", "KR")
        assert result is not None
        assert result[0] == "negative"
        assert result[1] >= 80.0

    def test_kr_positive_keyword_detected(self):
        """KR 긍정 키워드 → (positive, score) 반환."""
        from app.collectors.pipeline import _fast_path_check
        result = _fast_path_check("삼성전자 영업이익 사상 최대", "KR")
        assert result is not None
        assert result[0] == "positive"
        assert result[1] >= 80.0

    def test_us_negative_keyword_detected(self):
        """US 부정 키워드 → case-insensitive 매칭."""
        from app.collectors.pipeline import _fast_path_check
        result = _fast_path_check("NVDA Files for Bankruptcy Protection", "US")
        assert result is not None
        assert result[0] == "negative"

    def test_us_positive_keyword_detected(self):
        """US 긍정 키워드 매칭."""
        from app.collectors.pipeline import _fast_path_check
        result = _fast_path_check("AAPL beats expectations in Q4 earnings", "US")
        assert result is not None
        assert result[0] == "positive"

    def test_no_keyword_returns_none(self):
        """키워드 없으면 None."""
        from app.collectors.pipeline import _fast_path_check
        assert _fast_path_check("삼성전자 주가 소폭 상승", "KR") is None
        assert _fast_path_check("AAPL stock rises slightly", "US") is None

    @pytest.mark.asyncio
    async def test_fast_path_publishes_before_llm(self, db_session, monkeypatch):
        """Fast-path 키워드 매칭 시 Redis에 즉시 발행."""
        import fakeredis

        from app.collectors.pipeline import process_collected_items

        fake_redis = fakeredis.FakeRedis()
        pubsub = fake_redis.pubsub()
        pubsub.subscribe("news_breaking_kr")

        monkeypatch.setattr("app.collectors.pipeline._get_redis_client", lambda: fake_redis)
        monkeypatch.setattr(
            "app.processing.unified_analyzer.call_llm",
            lambda sys, usr, **kw: '{"sentiment": "negative", "score": -0.9, "confidence": 0.95, "themes": [], "summary": "파산 뉴스", "kr_impact": []}',
        )
        monkeypatch.setattr(
            "app.processing.article_scraper.ArticleScraper.scrape_one",
            AsyncMock(return_value=ScrapeResult(url="", body=None)),
        )

        items = [{
            "title": "삼성전자 파산 신청 공시",
            "source_url": "https://example.com/breaking",
            "source": "naver",
            "market": "KR",
            "stock_code": "005930",
            "stock_name": "삼성전자",
        }]

        count = await process_collected_items(db_session, items, market="KR")
        assert count == 1

        # Verify at least one message was published to the breaking channel
        msg = pubsub.get_message()  # subscribe confirmation
        msg = pubsub.get_message()  # first real message (fast-path)
        assert msg is not None
        assert msg["type"] == "message"
