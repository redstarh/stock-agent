"""스케줄러 job 함수 테스트."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCollectKrNewsJob:
    """_collect_kr_news_job() 테스트."""

    def test_collects_and_processes(self, monkeypatch, db_session):
        """NaverCollector 호출 후 pipeline 처리."""
        collected_items = [
            {"title": "삼성전자 뉴스", "source_url": "https://example.com/1", "source": "naver", "market": "KR", "stock_code": "005930"},
        ]

        mock_collector_instance = MagicMock()

        async def mock_collect(**kwargs):
            return collected_items
        mock_collector_instance.collect = mock_collect

        mock_collector_cls = MagicMock(return_value=mock_collector_instance)
        monkeypatch.setattr("app.collectors.naver.NaverCollector", mock_collector_cls)

        process_call_args = []

        async def mock_process(db, items, market="KR"):
            process_call_args.append((len(items), market))
            return len(items)

        monkeypatch.setattr("app.collectors.pipeline.process_collected_items", mock_process)
        monkeypatch.setattr("app.core.database.SessionLocal", lambda: db_session)

        from app.collectors.scheduler import _collect_kr_news_job
        _collect_kr_news_job()

        assert len(process_call_args) == 1
        assert process_call_args[0][1] == "KR"

    def test_handles_collector_failure(self, monkeypatch, db_session):
        """수집기 실패 시에도 크래시하지 않음."""
        mock_collector_instance = MagicMock()

        async def mock_collect(**kwargs):
            raise ConnectionError("Network error")
        mock_collector_instance.collect = mock_collect

        mock_collector_cls = MagicMock(return_value=mock_collector_instance)
        monkeypatch.setattr("app.collectors.naver.NaverCollector", mock_collector_cls)

        from app.collectors.scheduler import _collect_kr_news_job
        # Should not raise
        _collect_kr_news_job()


class TestCollectDartDisclosureJob:
    """_collect_dart_disclosure_job() 테스트."""

    def test_skips_without_api_key(self, monkeypatch):
        """API key 없으면 스킵."""
        monkeypatch.setattr("app.collectors.scheduler.settings.dart_api_key", "")

        from app.collectors.scheduler import _collect_dart_disclosure_job
        # Should return immediately without error
        _collect_dart_disclosure_job()

    def test_collects_with_api_key(self, monkeypatch, db_session):
        """API key 있으면 수집 실행."""
        monkeypatch.setattr("app.collectors.scheduler.settings.dart_api_key", "test-key")

        collected_items = [
            {"title": "공시", "source_url": "https://dart.fss.or.kr/1", "source": "dart", "market": "KR", "stock_code": "005930", "is_disclosure": True},
        ]

        mock_collector_instance = MagicMock()

        async def mock_collect(**kwargs):
            return collected_items
        mock_collector_instance.collect = mock_collect

        mock_collector_cls = MagicMock(return_value=mock_collector_instance)
        monkeypatch.setattr("app.collectors.dart.DartCollector", mock_collector_cls)

        process_call_args = []

        async def mock_process(db, items, market="KR"):
            process_call_args.append((len(items), market))
            return len(items)

        monkeypatch.setattr("app.collectors.pipeline.process_collected_items", mock_process)
        monkeypatch.setattr("app.core.database.SessionLocal", lambda: db_session)

        from app.collectors.scheduler import _collect_dart_disclosure_job
        _collect_dart_disclosure_job()

        assert len(process_call_args) == 1


class TestCollectUsNewsJob:
    """_collect_us_news_job() 테스트."""

    def test_skips_without_api_key(self, monkeypatch):
        """API key 없으면 스킵."""
        monkeypatch.setattr("app.collectors.scheduler.settings.finnhub_api_key", "")

        from app.collectors.scheduler import _collect_us_news_job
        _collect_us_news_job()

    def test_collects_with_api_key(self, monkeypatch, db_session):
        """API key 있으면 수집 실행."""
        monkeypatch.setattr("app.collectors.scheduler.settings.finnhub_api_key", "test-key")

        collected_items = [
            {"title": "NVDA news", "source_url": "https://example.com/us/1", "source": "finnhub:reuters", "market": "US", "stock_code": "NVDA"},
        ]

        mock_collector_instance = MagicMock()

        async def mock_collect(**kwargs):
            return collected_items
        mock_collector_instance.collect = mock_collect

        mock_collector_cls = MagicMock(return_value=mock_collector_instance)
        monkeypatch.setattr("app.collectors.finnhub.FinnhubCollector", mock_collector_cls)

        process_call_args = []

        async def mock_process(db, items, market="US"):
            process_call_args.append((len(items), market))
            return len(items)

        monkeypatch.setattr("app.collectors.pipeline.process_collected_items", mock_process)
        monkeypatch.setattr("app.core.database.SessionLocal", lambda: db_session)

        from app.collectors.scheduler import _collect_us_news_job
        _collect_us_news_job()

        assert len(process_call_args) == 1
        assert process_call_args[0][1] == "US"


class TestCreateScheduler:
    """create_scheduler() 테스트."""

    def test_creates_scheduler_with_three_jobs(self):
        """3개 job이 등록된 스케줄러 생성."""
        from app.collectors.scheduler import create_scheduler
        scheduler = create_scheduler()

        jobs = scheduler.get_jobs()
        job_ids = [job.id for job in jobs]

        assert "kr_news_collection" in job_ids
        assert "dart_disclosure_collection" in job_ids
        assert "us_news_collection" in job_ids
        assert len(jobs) == 3
