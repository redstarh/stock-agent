"""RED: 환경 설정 테스트 — Pydantic Settings 기반."""

import os
import pytest


class TestConfig:
    def test_default_database_url(self):
        """기본 DATABASE_URL이 sqlite."""
        from app.core.config import settings

        assert "sqlite" in settings.database_url

    def test_default_redis_url(self):
        """기본 REDIS_URL 설정."""
        from app.core.config import settings

        assert settings.redis_url.startswith("redis://")

    def test_default_app_env(self):
        """기본 APP_ENV가 development."""
        from app.core.config import settings

        assert settings.app_env == "development"

    def test_cors_origins_parsing(self):
        """CORS_ORIGINS가 리스트로 파싱."""
        from app.core.config import settings

        assert isinstance(settings.cors_origins, list)
        assert len(settings.cors_origins) >= 1

    def test_debug_default(self):
        """기본 DEBUG가 True."""
        from app.core.config import settings

        assert settings.debug is True
