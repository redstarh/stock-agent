"""T-B1: 프로젝트 초기 셋업 테스트"""


def test_pytest_runs():
    """pytest가 정상 실행되는지 확인"""
    assert True


def test_project_imports():
    """핵심 패키지 import 가능 확인"""
    import httpx  # noqa: F401
    import fastapi  # noqa: F401
    import sqlalchemy  # noqa: F401
    import redis  # noqa: F401
    import pydantic  # noqa: F401


def test_config_loads():
    """설정 파일 로딩 확인"""
    from src.config import Settings

    settings = Settings()
    assert settings.APP_NAME == "StockAgent"
    assert settings.DATABASE_URL is not None
    assert settings.REDIS_URL is not None


def test_config_kiwoom_defaults():
    """키움 API 기본 설정 확인"""
    from src.config import Settings

    settings = Settings()
    assert settings.KIWOOM_BASE_URL != ""
    assert settings.MAX_POSITION_PCT == 0.10
    assert settings.STOP_LOSS_PCT == 0.03


def test_logging_configured():
    """로깅 설정 확인"""
    import logging

    logger = logging.getLogger("stockagent")
    assert logger is not None
    assert logger.level != logging.NOTSET
