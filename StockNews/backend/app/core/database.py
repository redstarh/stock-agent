"""DB 엔진 + 세션 팩토리."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Sync engine for MVP (SQLite)
engine = create_engine(
    settings.database_url.replace("+aiosqlite", ""),
    echo=settings.debug,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """SQLite WAL 모드 + busy timeout 설정."""
    if "sqlite" in settings.database_url:
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
