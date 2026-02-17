"""Pydantic Settings 기반 환경 설정."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./stocknews.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str = ""

    # DART
    dart_api_key: str = ""

    # App
    app_env: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
