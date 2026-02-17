"""RED: 뉴스 수집기 통합 테스트."""

import pytest
import respx
from httpx import Response


class TestNaverCollector:
    @pytest.fixture
    def naver_html(self):
        """네이버 뉴스 검색 결과 mock HTML."""
        return """
        <html><body>
        <ul class="list_news">
            <li class="bx">
                <a class="news_tit" href="https://news.naver.com/article/1" title="삼성전자 4분기 실적 발표">삼성전자 4분기 실적 발표</a>
                <span class="info_group"><a class="info press">한국경제</a></span>
            </li>
            <li class="bx">
                <a class="news_tit" href="https://news.naver.com/article/2" title="SK하이닉스 HBM 수주 확대">SK하이닉스 HBM 수주 확대</a>
                <span class="info_group"><a class="info press">매일경제</a></span>
            </li>
            <li class="bx">
                <a class="news_tit" href="https://news.naver.com/article/3" title="카카오 신규 서비스 출시">카카오 신규 서비스 출시</a>
                <span class="info_group"><a class="info press">조선일보</a></span>
            </li>
        </ul>
        </body></html>
        """

    @respx.mock
    @pytest.mark.asyncio
    async def test_parse_news_list(self, naver_html):
        """네이버 뉴스 HTML 파싱 → 뉴스 리스트 반환."""
        from app.collectors.naver import NaverCollector

        respx.get("https://search.naver.com/search.naver").mock(
            return_value=Response(200, text=naver_html)
        )

        collector = NaverCollector()
        items = await collector.collect(query="삼성전자")

        assert len(items) >= 1
        assert all("title" in item for item in items)
        assert all("source_url" in item for item in items)
        assert all("source" in item for item in items)

    @respx.mock
    @pytest.mark.asyncio
    async def test_extract_stock_code_from_url(self, naver_html):
        """수집된 뉴스에 market='KR' 설정."""
        from app.collectors.naver import NaverCollector

        respx.get("https://search.naver.com/search.naver").mock(
            return_value=Response(200, text=naver_html)
        )

        collector = NaverCollector()
        items = await collector.collect(query="삼성전자", stock_code="005930")
        assert all(item.get("market") == "KR" for item in items)
        assert all(item.get("stock_code") == "005930" for item in items)

    @respx.mock
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """수집 실패 시 재시도 (최대 3회)."""
        from app.collectors.naver import NaverCollector

        route = respx.get("https://search.naver.com/search.naver")
        route.side_effect = [
            Response(500),
            Response(500),
            Response(200, text="<html><body><ul class='list_news'></ul></body></html>"),
        ]

        collector = NaverCollector(max_retries=3)
        items = await collector.collect(query="test")
        assert isinstance(items, list)


class TestDartCollector:
    @pytest.fixture
    def dart_json(self):
        """DART 공시 API mock 응답."""
        return {
            "status": "000",
            "message": "정상",
            "list": [
                {
                    "corp_name": "삼성전자",
                    "corp_code": "00126380",
                    "stock_code": "005930",
                    "report_nm": "[기재정정]사업보고서",
                    "rcept_no": "20240115000001",
                    "rcept_dt": "20240115",
                },
                {
                    "corp_name": "SK하이닉스",
                    "corp_code": "00164779",
                    "stock_code": "000660",
                    "report_nm": "분기보고서",
                    "rcept_no": "20240115000002",
                    "rcept_dt": "20240115",
                },
            ],
        }

    @respx.mock
    @pytest.mark.asyncio
    async def test_parse_disclosure_list(self, dart_json):
        """DART 공시 JSON 파싱."""
        from app.collectors.dart import DartCollector

        respx.get("https://opendart.fss.or.kr/api/list.json").mock(
            return_value=Response(200, json=dart_json)
        )

        collector = DartCollector(api_key="test_key")
        items = await collector.collect()

        assert len(items) == 2
        assert items[0]["title"] == "[기재정정]사업보고서"
        assert items[0]["stock_code"] == "005930"

    @respx.mock
    @pytest.mark.asyncio
    async def test_set_is_disclosure_true(self, dart_json):
        """DART 수집 뉴스의 is_disclosure=True."""
        from app.collectors.dart import DartCollector

        respx.get("https://opendart.fss.or.kr/api/list.json").mock(
            return_value=Response(200, json=dart_json)
        )

        collector = DartCollector(api_key="test_key")
        items = await collector.collect()

        assert all(item.get("is_disclosure") is True for item in items)

    @respx.mock
    @pytest.mark.asyncio
    async def test_invalid_api_key(self):
        """잘못된 API 키 → 빈 리스트 반환."""
        from app.collectors.dart import DartCollector

        respx.get("https://opendart.fss.or.kr/api/list.json").mock(
            return_value=Response(200, json={"status": "010", "message": "등록되지 않은 인증키"})
        )

        collector = DartCollector(api_key="invalid")
        items = await collector.collect()
        assert items == []


class TestRssCollector:
    @pytest.fixture
    def rss_xml(self):
        """RSS 피드 mock XML."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>뉴스 제목 1</title>
                    <link>https://example.com/news/1</link>
                    <pubDate>Mon, 15 Jan 2024 09:00:00 +0900</pubDate>
                    <description>뉴스 요약 1</description>
                </item>
                <item>
                    <title>뉴스 제목 2</title>
                    <link>https://example.com/news/2</link>
                    <pubDate>Mon, 15 Jan 2024 10:00:00 +0900</pubDate>
                    <description>뉴스 요약 2</description>
                </item>
            </channel>
        </rss>"""

    @respx.mock
    @pytest.mark.asyncio
    async def test_parse_rss_feed(self, rss_xml):
        """RSS XML 파싱 → 뉴스 리스트."""
        from app.collectors.rss import RssCollector

        respx.get("https://example.com/feed.xml").mock(
            return_value=Response(200, text=rss_xml)
        )

        collector = RssCollector()
        items = await collector.collect(feed_url="https://example.com/feed.xml")

        assert len(items) == 2
        assert items[0]["title"] == "뉴스 제목 1"
        assert items[0]["source_url"] == "https://example.com/news/1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_handle_malformed_xml(self):
        """잘못된 XML → 에러 없이 빈 리스트."""
        from app.collectors.rss import RssCollector

        respx.get("https://example.com/bad.xml").mock(
            return_value=Response(200, text="not xml at all {{{}}")
        )

        collector = RssCollector()
        items = await collector.collect(feed_url="https://example.com/bad.xml")
        assert items == []


class TestScheduler:
    def test_scheduler_creates_jobs(self):
        """스케줄러가 수집 job을 등록하는지 확인."""
        from app.collectors.scheduler import create_scheduler

        scheduler = create_scheduler()
        jobs = scheduler.get_jobs()
        assert len(jobs) >= 1

    def test_scheduler_interval(self):
        """기본 수집 주기가 5분."""
        from app.collectors.scheduler import COLLECTION_INTERVAL_MINUTES

        assert COLLECTION_INTERVAL_MINUTES == 5
