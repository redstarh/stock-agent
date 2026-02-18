"""ArticleScraper 단위 테스트."""

import pytest
import respx
from httpx import Response

from app.processing.article_scraper import ArticleScraper, ScrapeResult


@respx.mock
@pytest.mark.asyncio
async def test_scrape_naver_article():
    """네이버 뉴스 #dic_area 선택자로 본문 추출."""
    html = """
    <html>
        <body>
            <div id="dic_area">
                네이버 뉴스 본문입니다.
                여러 줄로 작성되어 있습니다.
            </div>
        </body>
    </html>
    """
    respx.get("https://news.naver.com/article/1").mock(
        return_value=Response(200, text=html, headers={"content-type": "text/html"})
    )

    scraper = ArticleScraper()
    result = await scraper.scrape_one("https://news.naver.com/article/1")

    assert result.url == "https://news.naver.com/article/1"
    assert result.body is not None
    assert "네이버 뉴스 본문" in result.body
    assert result.error is None


@respx.mock
@pytest.mark.asyncio
async def test_scrape_fallback_article_tag():
    """<article> fallback 동작 (100자 이상 본문)."""
    html = """
    <html>
        <body>
            <article>
                This is a long article body that contains more than one hundred characters.
                It should be extracted successfully using the article tag fallback selector.
            </article>
        </body>
    </html>
    """
    respx.get("https://example.com/news/1").mock(
        return_value=Response(200, text=html, headers={"content-type": "text/html"})
    )

    scraper = ArticleScraper()
    result = await scraper.scrape_one("https://example.com/news/1")

    assert result.body is not None
    assert len(result.body) > 100
    assert "long article body" in result.body
    assert result.error is None


@respx.mock
@pytest.mark.asyncio
async def test_scrape_fallback_paragraphs():
    """<p> 태그 결합 fallback (100자 이상)."""
    html = """
    <html>
        <body>
            <p>First paragraph with some content.</p>
            <p>Second paragraph with more content to make it longer.</p>
            <p>Third paragraph to ensure we exceed one hundred characters in total length.</p>
        </body>
    </html>
    """
    respx.get("https://example.com/news/2").mock(
        return_value=Response(200, text=html, headers={"content-type": "text/html"})
    )

    scraper = ArticleScraper()
    result = await scraper.scrape_one("https://example.com/news/2")

    assert result.body is not None
    assert len(result.body) > 100
    assert "First paragraph" in result.body
    assert "Third paragraph" in result.body
    assert result.error is None


@respx.mock
@pytest.mark.asyncio
async def test_scrape_timeout():
    """httpx.TimeoutException 시 error='timeout'."""
    import httpx

    respx.get("https://example.com/slow").mock(side_effect=httpx.TimeoutException("timeout"))

    scraper = ArticleScraper()
    result = await scraper.scrape_one("https://example.com/slow")

    assert result.url == "https://example.com/slow"
    assert result.body is None
    assert result.error == "timeout"


@respx.mock
@pytest.mark.asyncio
async def test_scrape_http_error():
    """HTTP 403 시 error='http_403'."""
    respx.get("https://example.com/forbidden").mock(
        return_value=Response(403, text="Forbidden")
    )

    scraper = ArticleScraper()
    result = await scraper.scrape_one("https://example.com/forbidden")

    assert result.url == "https://example.com/forbidden"
    assert result.body is None
    assert result.error == "http_403"


@pytest.mark.asyncio
async def test_skip_dart_source():
    """source='dart'는 건너뜀, error='skipped_source'."""
    scraper = ArticleScraper()
    result = await scraper.scrape_one("https://dart.fss.or.kr/article/1", source="dart")

    assert result.url == "https://dart.fss.or.kr/article/1"
    assert result.body is None
    assert result.error == "skipped_source"


@pytest.mark.asyncio
async def test_skip_empty_url():
    """빈 URL 시 error='empty_url'."""
    scraper = ArticleScraper()
    result = await scraper.scrape_one("", source="some_source")

    assert result.url == ""
    assert result.body is None
    assert result.error == "empty_url"


@respx.mock
@pytest.mark.asyncio
async def test_non_html_rejected():
    """content-type이 PDF 등이면 에러."""
    respx.get("https://example.com/document.pdf").mock(
        return_value=Response(200, text="PDF content", headers={"content-type": "application/pdf"})
    )

    scraper = ArticleScraper()
    result = await scraper.scrape_one("https://example.com/document.pdf")

    assert result.url == "https://example.com/document.pdf"
    assert result.body is None
    assert result.error is not None
    assert "Non-HTML content" in result.error


@respx.mock
@pytest.mark.asyncio
async def test_body_length_truncation():
    """max_body_length=3000 초과 시 잘림."""
    long_text = "A" * 5000
    html = f"<html><body><article>{long_text}</article></body></html>"

    respx.get("https://example.com/long").mock(
        return_value=Response(200, text=html, headers={"content-type": "text/html"})
    )

    scraper = ArticleScraper(max_body_length=3000)
    result = await scraper.scrape_one("https://example.com/long")

    assert result.body is not None
    assert len(result.body) == 3000
    assert result.error is None


@respx.mock
@pytest.mark.asyncio
async def test_scrape_batch():
    """2개 URL 배치 동시 스크래핑."""
    html1 = "<html><body><article>First article with enough content to pass the length check. Adding more text to ensure we exceed one hundred characters minimum requirement.</article></body></html>"
    html2 = "<html><body><article>Second article with enough content to pass the length check. Adding more text to ensure we exceed one hundred characters minimum requirement.</article></body></html>"

    respx.get("https://example.com/article1").mock(
        return_value=Response(200, text=html1, headers={"content-type": "text/html"})
    )
    respx.get("https://example.com/article2").mock(
        return_value=Response(200, text=html2, headers={"content-type": "text/html"})
    )

    scraper = ArticleScraper()
    items = [
        {"source_url": "https://example.com/article1", "source": "test"},
        {"source_url": "https://example.com/article2", "source": "test"},
    ]

    results = await scraper.scrape_batch(items)

    assert len(results) == 2
    assert "https://example.com/article1" in results
    assert "https://example.com/article2" in results
    assert results["https://example.com/article1"].body is not None
    assert "First article" in results["https://example.com/article1"].body
    assert results["https://example.com/article2"].body is not None
    assert "Second article" in results["https://example.com/article2"].body


@respx.mock
@pytest.mark.asyncio
async def test_removes_script_tags():
    """script 태그가 본문에서 제거됨."""
    html = """
    <html>
        <body>
            <article>
                Article content here with enough text to pass the minimum length requirement.
                <script>alert('should be removed');</script>
                More article content to ensure we exceed one hundred characters in total.
            </article>
        </body>
    </html>
    """
    respx.get("https://example.com/with-script").mock(
        return_value=Response(200, text=html, headers={"content-type": "text/html"})
    )

    scraper = ArticleScraper()
    result = await scraper.scrape_one("https://example.com/with-script")

    assert result.body is not None
    assert "Article content" in result.body
    assert "script" not in result.body.lower()
    assert "alert" not in result.body
    assert result.error is None


@pytest.mark.asyncio
async def test_clean_text():
    """연속 공백/줄바꿈이 단일 공백으로 정리됨."""
    from app.processing.article_scraper import ArticleScraper

    text = "This   has    multiple     spaces\n\n\nand\n\nmany\nnewlines\t\tand\ttabs"
    cleaned = ArticleScraper._clean_text(text)

    assert "  " not in cleaned
    assert "\n" not in cleaned
    assert "\t" not in cleaned
    assert cleaned == "This has multiple spaces and many newlines and tabs"
