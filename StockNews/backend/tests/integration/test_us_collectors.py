"""통합 테스트: 미국 뉴스 수집기 (Finnhub + NewsAPI)."""

import pytest
import httpx
import respx

from app.collectors.finnhub import FinnhubCollector
from app.collectors.newsapi import NewsAPICollector


class TestFinnhubCollector:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.finnhub_api_key", "test-key")

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_general_news(self):
        respx.get("https://finnhub.io/api/v1/news").mock(
            return_value=httpx.Response(200, json=[
                {
                    "headline": "NVIDIA beats earnings expectations",
                    "url": "https://example.com/1",
                    "source": "Reuters",
                    "datetime": 1708300800,
                    "category": "general",
                },
                {
                    "headline": "Apple launches new product",
                    "url": "https://example.com/2",
                    "source": "Bloomberg",
                    "datetime": 1708300900,
                    "category": "general",
                },
            ])
        )

        collector = FinnhubCollector()
        items = await collector.collect()
        assert len(items) == 2
        assert items[0]["market"] == "US"
        assert items[0]["stock_code"] == "NVDA"
        assert items[1]["stock_code"] == "AAPL"

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_company_news(self, monkeypatch):
        respx.get("https://finnhub.io/api/v1/company-news").mock(
            return_value=httpx.Response(200, json=[
                {
                    "headline": "Tesla Q4 results",
                    "url": "https://example.com/3",
                    "source": "CNBC",
                    "datetime": 1708300800,
                },
            ])
        )

        collector = FinnhubCollector()
        items = await collector.collect_company_news("TSLA")
        assert len(items) == 1
        assert items[0]["stock_code"] == "TSLA"

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_no_api_key(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.finnhub_api_key", "")
        collector = FinnhubCollector()
        items = await collector.collect()
        assert items == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_retry_on_failure(self):
        route = respx.get("https://finnhub.io/api/v1/news")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(200, json=[{"headline": "Test", "url": "http://x.com", "source": "T", "datetime": 0}]),
        ]

        collector = FinnhubCollector(max_retries=2, base_delay=0.01)
        items = await collector.collect()
        assert len(items) == 1


class TestNewsAPICollector:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.newsapi_api_key", "test-key")

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_news(self):
        respx.get("https://newsapi.org/v2/everything").mock(
            return_value=httpx.Response(200, json={
                "status": "ok",
                "totalResults": 2,
                "articles": [
                    {
                        "title": "Microsoft Azure growth accelerates",
                        "url": "https://example.com/4",
                        "source": {"name": "Reuters"},
                        "publishedAt": "2026-02-18T10:00:00Z",
                    },
                    {
                        "title": "AMD launches new AI chip",
                        "url": "https://example.com/5",
                        "source": {"name": "Bloomberg"},
                        "publishedAt": "2026-02-18T09:00:00Z",
                    },
                ],
            })
        )

        collector = NewsAPICollector()
        items = await collector.collect(query="tech stocks")
        assert len(items) == 2
        assert items[0]["market"] == "US"
        assert items[0]["stock_code"] == "MSFT"
        assert items[1]["stock_code"] == "AMD"

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_no_api_key(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.newsapi_api_key", "")
        collector = NewsAPICollector()
        items = await collector.collect()
        assert items == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_collect_empty_response(self):
        respx.get("https://newsapi.org/v2/everything").mock(
            return_value=httpx.Response(200, json={"status": "ok", "totalResults": 0, "articles": []})
        )
        collector = NewsAPICollector()
        items = await collector.collect()
        assert items == []
