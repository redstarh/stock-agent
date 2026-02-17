"""통합 테스트용 conftest — 테스트 DB 오버라이드."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app as fastapi_app
from app.models.base import Base
import app.models  # noqa: F401


@pytest.fixture(scope="session")
def integration_engine():
    """통합 테스트용 SQLite in-memory 엔진."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def integration_session_factory(integration_engine):
    """세션 팩토리."""
    return sessionmaker(bind=integration_engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def override_get_db(integration_session_factory):
    """모든 통합 테스트에서 get_db를 테스트 DB로 오버라이드."""

    def _get_test_db():
        db = integration_session_factory()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _get_test_db
    yield
    fastapi_app.dependency_overrides.clear()
