"""애플리케이션 설정 (pydantic-settings 기반)"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """환경 변수 기반 설정"""

    # App
    APP_NAME: str = "StockAgent"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://stockagent:stockagent@localhost:5432/stockagent"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Kiwoom API
    KIWOOM_APP_KEY: str = ""
    KIWOOM_APP_SECRET: str = ""
    KIWOOM_BASE_URL: str = "https://openapi.koreainvestment.com:9443"
    KIWOOM_ACCOUNT_NO: str = ""

    # StockNews
    STOCKNEWS_BASE_URL: str = "http://localhost:8001"

    # Trading
    MAX_POSITION_PCT: float = 0.10
    STOP_LOSS_PCT: float = 0.03
    DAILY_LOSS_LIMIT: int = 500000
    MAX_POSITIONS: int = 5

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }
