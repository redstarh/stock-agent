"""T-B11: StockNews REST 연동 테스트"""

import pytest
import respx
import httpx

from src.core.news_client import NewsClient


@pytest.fixture
def mock_stocknews():
    with respx.mock(base_url="http://localhost:8001", assert_all_called=False) as mock:
        mock.get("/api/v1/news/score", params={"code": "005930"}).respond(json={
            "code": "005930",
            "score": 75,
            "articles": 5,
        })
        yield mock


@pytest.mark.asyncio
async def test_get_news_score(mock_stocknews):
    """뉴스 점수 조회"""
    client = NewsClient(base_url="http://localhost:8001")
    score = await client.get_score("005930")
    assert 0 <= score <= 100
    assert score == 75


@pytest.mark.asyncio
async def test_news_score_caching(mock_stocknews):
    """점수 캐싱: TTL 내 재요청 없음"""
    client = NewsClient(base_url="http://localhost:8001", cache_ttl=60)
    score1 = await client.get_score("005930")
    score2 = await client.get_score("005930")
    assert score1 == score2
    assert mock_stocknews.calls.call_count == 1


@pytest.mark.asyncio
async def test_news_service_unavailable():
    """뉴스 서비스 다운 시 기본값 반환"""
    with respx.mock(base_url="http://localhost:8001") as mock:
        mock.get("/api/v1/news/score").respond(status_code=503)
        client = NewsClient(base_url="http://localhost:8001")
        score = await client.get_score("000660")
        assert score == 0


@pytest.mark.asyncio
async def test_news_score_different_stocks(mock_stocknews):
    """서로 다른 종목은 별도 캐시"""
    mock_stocknews.get("/api/v1/news/score", params={"code": "000660"}).respond(json={
        "code": "000660",
        "score": 45,
        "articles": 2,
    })
    client = NewsClient(base_url="http://localhost:8001", cache_ttl=60)
    score1 = await client.get_score("005930")
    score2 = await client.get_score("000660")
    assert score1 == 75
    assert score2 == 45
