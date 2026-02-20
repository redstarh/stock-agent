"""DB 엔진 + 세션 팩토리."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def _get_engine_url(url: str) -> str:
    """Convert config URL to sync engine URL."""
    if "sqlite" in url:
        return url.replace("+aiosqlite", "")
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg2")
    return url


# Sync engine for MVP (SQLite) and production (PostgreSQL)
engine = create_engine(
    _get_engine_url(settings.database_url),
    echo=settings.debug,
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """SQLite WAL 모드 + busy timeout 설정."""
    if engine.url.get_backend_name() == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """FastAPI dependency — DB 세션 제공."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
