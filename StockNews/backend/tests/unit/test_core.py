"""Core 모듈 기본 테스트 — database, redis, logger import 및 기본 동작."""

import pytest


class TestDatabase:
    def test_engine_created(self):
        """DB 엔진이 생성되는지 확인."""
        from app.core.database import engine
        assert engine is not None

    def test_session_factory(self):
        """세션 팩토리가 동작하는지 확인."""
        from app.core.database import SessionLocal
        session = SessionLocal()
        assert session is not None
        session.close()

    def test_get_db_generator(self):
        """get_db가 generator로 동작."""
        from app.core.database import get_db
        gen = get_db()
        db = next(gen)
        assert db is not None
        try:
            next(gen)
        except StopIteration:
            pass


class TestRedis:
    def test_redis_client_created(self):
        """Redis 클라이언트가 생성되는지 확인 (연결 실패해도 객체는 생성)."""
        from app.core.redis import redis_client
        assert redis_client is not None

    def test_get_redis(self):
        """get_redis가 클라이언트를 반환."""
        from app.core.redis import get_redis
        client = get_redis()
        assert client is not None


class TestLogger:
    def test_logger_import(self):
        """structured logging import 확인."""
        import logging
        logger = logging.getLogger(__name__)
        assert logger is not None

    def test_logger_can_log(self):
        """logger가 에러 없이 로그를 출력."""
        import logging
        logger = logging.getLogger("test.core")
        # 에러 없이 실행되면 성공
        logger.info("Test log message")
