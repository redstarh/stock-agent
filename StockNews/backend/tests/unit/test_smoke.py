"""스모크 테스트 — 기본 import 및 DB 연결 확인."""

import pytest


def test_import_app():
    """FastAPI 앱 import가 에러 없이 성공하는지 확인."""
    from app.main import app

    assert app is not None


def test_app_has_health_route():
    """FastAPI 앱에 /health 라우트가 등록되어 있는지 확인."""
    from app.main import app

    routes = [route.path for route in app.routes]
    assert "/health" in routes


def test_db_engine(db_engine):
    """DB 엔진이 정상 생성되는지 확인."""
    assert db_engine is not None


def test_db_session(db_session):
    """DB 세션이 정상 생성되는지 확인."""
    assert db_session is not None
    # 간단한 쿼리 실행 가능 여부
    result = db_session.execute(
        __import__("sqlalchemy").text("SELECT 1")
    )
    assert result.scalar() == 1
