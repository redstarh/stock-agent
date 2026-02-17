"""공통 테스트 fixture 정의."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base  # noqa: F401 — also imports NewsEvent, ThemeStrength
import app.models  # ensure models are registered with Base.metadata


@pytest.fixture(scope="session")
def db_engine():
    """SQLite in-memory 엔진 (세션 전체 공유)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """트랜잭션 격리된 DB 세션 (각 테스트 후 rollback)."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def sample_news_events(db_session):
    """테스트용 뉴스 이벤트 5건 (다양한 종목/테마/감성)."""
    # Will be populated when NewsEvent model is implemented
    return []


@pytest.fixture
def sample_theme_strength(db_session):
    """테스트용 테마 강도 데이터."""
    # Will be populated when ThemeStrength model is implemented
    return []


@pytest.fixture
def mock_naver_response():
    """네이버 뉴스 크롤링 mock HTML 응답."""
    return "<html><body><div class='news'>테스트 뉴스</div></body></html>"


@pytest.fixture
def mock_dart_response():
    """DART API mock JSON 응답."""
    return {
        "status": "000",
        "list": [
            {
                "corp_name": "삼성전자",
                "report_nm": "테스트 공시",
                "rcept_dt": "20240115",
            }
        ],
    }


@pytest.fixture
def mock_rss_feed():
    """RSS 피드 mock XML 응답."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>테스트 뉴스</title>
                <link>https://example.com/news/1</link>
                <pubDate>Mon, 15 Jan 2024 09:00:00 +0900</pubDate>
            </item>
        </channel>
    </rss>"""


@pytest.fixture
def fake_redis():
    """fakeredis 인스턴스."""
    import fakeredis

    return fakeredis.FakeRedis()


@pytest.fixture
def mock_openai(monkeypatch):
    """OpenAI API mock (감성 분석 응답)."""

    class MockCompletion:
        class Choice:
            class Message:
                content = '{"sentiment": "positive", "score": 0.8}'

            message = Message()

        choices = [Choice()]

    class MockClient:
        class Chat:
            class Completions:
                @staticmethod
                def create(**kwargs):
                    return MockCompletion()

            completions = Completions()

        chat = Chat()

    monkeypatch.setattr("openai.OpenAI", lambda **kwargs: MockClient())
    return MockClient()
