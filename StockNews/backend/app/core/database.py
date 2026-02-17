"""DB 엔진 + 세션 팩토리."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Sync engine for MVP (SQLite)
engine = create_engine(
    settings.database_url.replace("+aiosqlite", ""),
    echo=settings.debug,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """FastAPI dependency — DB 세션 제공."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
