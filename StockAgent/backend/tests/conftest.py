"""공통 테스트 fixture"""

import pytest


@pytest.fixture
def test_settings():
    """테스트용 Settings 인스턴스"""
    from src.config import Settings

    return Settings(
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/stockagent_test",
        REDIS_URL="redis://localhost:6379/1",
        DEBUG=True,
    )
